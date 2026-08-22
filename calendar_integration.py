
from __future__ import annotations

import datetime as dt
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

import database

GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID","").strip()
GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET","").strip()
GOOGLE_REDIRECT_URI=os.getenv(
    "GOOGLE_REDIRECT_URI","http://127.0.0.1:8000/me/calendar/google/callback"
).strip()

AUTH_URL="https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL="https://oauth2.googleapis.com/token"
CALENDAR_API="https://www.googleapis.com/calendar/v3"
SCOPES=[
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
]

def _is_real_setting(value: str) -> bool:
    value=(value or "").strip()
    if not value:
        return False
    upper=value.upper()
    return not (
        upper.startswith("PASTE_")
        or "YOUR_GOOGLE_" in upper
        or upper in {"CHANGE_ME","REPLACE_ME"}
    )

def configuration_status() -> dict:
    missing=[]
    if not _is_real_setting(GOOGLE_CLIENT_ID):
        missing.append("GOOGLE_CLIENT_ID")
    if not _is_real_setting(GOOGLE_CLIENT_SECRET):
        missing.append("GOOGLE_CLIENT_SECRET")
    if not _is_real_setting(GOOGLE_REDIRECT_URI):
        missing.append("GOOGLE_REDIRECT_URI")
    return {
        "configured":not missing,
        "missing":missing,
        "redirect_uri":GOOGLE_REDIRECT_URI,
    }

def configured() -> bool:
    return configuration_status()["configured"]

def _http_json(url: str, method="GET", data=None, token: str | None=None) -> dict:
    headers={"Accept":"application/json"}
    body=None
    if data is not None:
        body=json.dumps(data).encode("utf-8")
        headers["Content-Type"]="application/json"
    if token:
        headers["Authorization"]=f"Bearer {token}"
    req=urllib.request.Request(url,data=body,method=method,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            raw=r.read().decode("utf-8")
            return json.loads(raw or "{}")
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode("utf-8",errors="replace")
        raise RuntimeError(f"Google Calendar API error ({exc.code}): {detail[:500]}") from exc

def _form_post(url: str, values: dict) -> dict:
    data=urllib.parse.urlencode(values).encode("utf-8")
    req=urllib.request.Request(url,data=data,method="POST",
        headers={"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode("utf-8",errors="replace")
        raise RuntimeError(f"Google OAuth error ({exc.code}): {detail[:500]}") from exc

def begin_oauth(user_id: int, return_url: str | None, db_path: Path) -> str:
    if not configured():
        raise RuntimeError("Google Calendar OAuth is not configured on the backend")
    state=secrets.token_urlsafe(32)
    database.save_oauth_state(state,user_id,return_url,db_path)
    params={
        "client_id":GOOGLE_CLIENT_ID,
        "redirect_uri":GOOGLE_REDIRECT_URI,
        "response_type":"code",
        "scope":" ".join(SCOPES),
        "access_type":"offline",
        "prompt":"consent",
        "include_granted_scopes":"true",
        "state":state,
    }
    return AUTH_URL+"?"+urllib.parse.urlencode(params)

def finish_oauth(code: str, state: str, db_path: Path) -> tuple[int,str | None]:
    saved=database.consume_oauth_state(state,db_path)
    if not saved:
        raise RuntimeError("Google OAuth state is invalid or expired")
    token=_form_post(TOKEN_URL,{
        "code":code,
        "client_id":GOOGLE_CLIENT_ID,
        "client_secret":GOOGLE_CLIENT_SECRET,
        "redirect_uri":GOOGLE_REDIRECT_URI,
        "grant_type":"authorization_code",
    })
    expires=dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=int(token.get("expires_in",3600)))
    database.save_calendar_connection(
        saved["user_id"],token.get("access_token",""),token.get("refresh_token"),
        expires.isoformat(),token.get("scope"),None,"primary",db_path
    )
    return int(saved["user_id"]),saved.get("return_url")

def _token(user_id: int, db_path: Path) -> str:
    conn=database.get_calendar_connection(user_id,db_path)
    if not conn:
        raise RuntimeError("Google Calendar is not connected")
    expires=None
    if conn.get("token_expires_at"):
        try: expires=dt.datetime.fromisoformat(conn["token_expires_at"])
        except Exception: pass
    now=dt.datetime.now(dt.timezone.utc)
    if conn.get("access_token") and expires and expires>now+dt.timedelta(minutes=2):
        return conn["access_token"]
    if not conn.get("refresh_token"):
        if conn.get("access_token"): return conn["access_token"]
        raise RuntimeError("Google Calendar connection needs to be re-authorized")
    refreshed=_form_post(TOKEN_URL,{
        "client_id":GOOGLE_CLIENT_ID,
        "client_secret":GOOGLE_CLIENT_SECRET,
        "refresh_token":conn["refresh_token"],
        "grant_type":"refresh_token",
    })
    new_exp=now+dt.timedelta(seconds=int(refreshed.get("expires_in",3600)))
    database.save_calendar_connection(
        user_id,refreshed["access_token"],None,new_exp.isoformat(),
        refreshed.get("scope") or conn.get("scope"),conn.get("google_email"),
        conn.get("calendar_id","primary"),db_path
    )
    return refreshed["access_token"]

def _tz(user_id: int, db_path: Path) -> ZoneInfo:
    name=database.get_time_settings(user_id,db_path).get("timezone") or "UTC"
    try:return ZoneInfo(name)
    except Exception:return ZoneInfo("UTC")

def current_local_time(user_id: int, db_path: Path) -> dict:
    settings=database.get_time_settings(user_id,db_path)
    tz=_tz(user_id,db_path)
    now=dt.datetime.now(dt.timezone.utc).astimezone(tz)
    return {
        "timezone":settings["timezone"],
        "iso":now.isoformat(),
        "date":now.date().isoformat(),
        "time":now.strftime("%H:%M:%S"),
        "weekday":now.weekday(),
        "weekday_name":now.strftime("%A"),
        "utc_offset_minutes":int(now.utcoffset().total_seconds()/60) if now.utcoffset() else 0,
    }

def _date_for_weekday(user_id: int, weekday: int, db_path: Path) -> dt.date:
    today=dt.datetime.now(dt.timezone.utc).astimezone(_tz(user_id,db_path)).date()
    monday=today-dt.timedelta(days=today.weekday())
    return monday+dt.timedelta(days=int(weekday))

def workout_event_times(user_id: int, schedule_item: dict, duration_min: int, db_path: Path) -> tuple[dt.datetime,dt.datetime]:
    settings=database.get_time_settings(user_id,db_path)
    hhmm=schedule_item.get("scheduled_time") or settings.get("default_workout_time") or "17:00"
    hour,minute=[int(x) for x in hhmm.split(":")[:2]]
    date=_date_for_weekday(user_id,int(schedule_item["scheduled_day"]),db_path)
    start=dt.datetime.combine(date,dt.time(hour,minute),tzinfo=_tz(user_id,db_path))
    end=start+dt.timedelta(minutes=max(10,int(duration_min or 45)))
    return start,end

def _event_body(user_id: int, schedule_item: dict, workout: dict, db_path: Path) -> dict:
    start,end=workout_event_times(user_id,schedule_item,int(workout.get("estimated_minutes") or 45),db_path)
    tz=database.get_time_settings(user_id,db_path).get("timezone","UTC")
    return {
        "summary":f"Forge Fitness — {workout.get('name') or schedule_item.get('name')}",
        "description":"Synced by Forge Fitness. Move this event to reschedule the workout in Forge.",
        "start":{"dateTime":start.isoformat(),"timeZone":tz},
        "end":{"dateTime":end.isoformat(),"timeZone":tz},
        "extendedProperties":{"private":{
            "forge":"1","forge_workout_id":str(schedule_item["workout_id"])
        }},
        "reminders":{"useDefault":True},
    }

def _forge_signature(schedule_item: dict, workout: dict) -> str:
    return "|".join([
        str(schedule_item.get("scheduled_day")),
        str(schedule_item.get("scheduled_time") or ""),
        str(bool(schedule_item.get("is_skipped"))),
        str(workout.get("name") or ""),
        str(workout.get("estimated_minutes") or ""),
        str(workout.get("status") or schedule_item.get("status") or ""),
    ])

def get_event(user_id: int, event_id: str, db_path: Path, calendar_id="primary") -> dict:
    token=_token(user_id,db_path)
    url=f"{CALENDAR_API}/calendars/{urllib.parse.quote(calendar_id,safe='')}/events/{urllib.parse.quote(event_id,safe='')}"
    return _http_json(url,token=token)

def create_event(user_id: int, schedule_item: dict, workout: dict, db_path: Path, calendar_id="primary") -> dict:
    token=_token(user_id,db_path)
    body=_event_body(user_id,schedule_item,workout,db_path)
    url=f"{CALENDAR_API}/calendars/{urllib.parse.quote(calendar_id,safe='')}/events"
    return _http_json(url,"POST",body,token)

def update_event(user_id: int, event_id: str, schedule_item: dict, workout: dict,
                 db_path: Path, calendar_id="primary") -> dict:
    token=_token(user_id,db_path)
    body=_event_body(user_id,schedule_item,workout,db_path)
    url=f"{CALENDAR_API}/calendars/{urllib.parse.quote(calendar_id,safe='')}/events/{urllib.parse.quote(event_id,safe='')}"
    return _http_json(url,"PUT",body,token)

def delete_event(user_id: int, event_id: str, db_path: Path, calendar_id="primary") -> None:
    token=_token(user_id,db_path)
    url=f"{CALENDAR_API}/calendars/{urllib.parse.quote(calendar_id,safe='')}/events/{urllib.parse.quote(event_id,safe='')}"
    req=urllib.request.Request(url,method="DELETE",headers={"Authorization":f"Bearer {token}"})
    try:
        urllib.request.urlopen(req,timeout=15).read()
    except urllib.error.HTTPError as exc:
        if exc.code not in {404,410}:
            raise

def _event_local_start(user_id: int, event: dict, db_path: Path) -> dt.datetime | None:
    raw=(event.get("start") or {}).get("dateTime")
    if not raw:return None
    try:
        parsed=dt.datetime.fromisoformat(raw.replace("Z","+00:00"))
        return parsed.astimezone(_tz(user_id,db_path))
    except Exception:return None

def freebusy(user_id: int, start: dt.datetime, end: dt.datetime, db_path: Path, calendar_id="primary") -> list[dict]:
    token=_token(user_id,db_path)
    body={"timeMin":start.astimezone(dt.timezone.utc).isoformat(),
          "timeMax":end.astimezone(dt.timezone.utc).isoformat(),
          "items":[{"id":calendar_id}]}
    data=_http_json(f"{CALENDAR_API}/freeBusy","POST",body,token)
    return ((data.get("calendars") or {}).get(calendar_id) or {}).get("busy",[]) or []

def availability_for_workout(user_id: int, target_day: int, duration_min: int,
                             db_path: Path, target_time: str | None=None) -> dict:
    settings=database.get_time_settings(user_id,db_path)
    hhmm=target_time or settings.get("default_workout_time") or "17:00"
    schedule={"scheduled_day":target_day,"scheduled_time":hhmm}
    start,end=workout_event_times(user_id,schedule,duration_min,db_path)
    busy=freebusy(user_id,start,end,db_path)
    available=not busy
    # Search same day for a simple alternate starting on half-hour boundaries, 06:00-21:00.
    alternatives=[]
    if busy:
        # Prefer nearby alternatives rather than suggesting an arbitrary early-morning slot.
        offsets=[]
        for step in range(1,13):
            offsets.extend([step*30,-step*30])
        for minutes_offset in offsets:
            cand=start+dt.timedelta(minutes=minutes_offset)
            if cand.date()!=start.date() or cand.hour<6 or cand.hour>=22:
                continue
            cand_end=cand+dt.timedelta(minutes=duration_min)
            if not freebusy(user_id,cand,cand_end,db_path):
                alternatives.append(cand.strftime("%H:%M"))
                if len(alternatives)>=3:break
    return {
        "available":available,
        "start":start.isoformat(),
        "end":end.isoformat(),
        "busy":busy,
        "alternative_times":alternatives,
    }

def sync_workout(user_id: int, workout_id: int, db_path: Path) -> dict:
    conn=database.get_calendar_connection(user_id,db_path)
    if not conn:return {"status":"not_connected"}
    settings=database.get_time_settings(user_id,db_path)
    if not settings.get("calendar_sync_enabled"):return {"status":"sync_disabled"}

    schedule=database.get_workout_schedule_item(user_id,workout_id,db_path)
    with database.session(db_path) as con:
        row=con.execute(
            """SELECT w.id AS workout_id,w.name,w.estimated_minutes,w.status
               FROM workouts w JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE w.id=? AND p.user_id=?""",(workout_id,user_id)
        ).fetchone()
    workout=dict(row) if row else None
    if not workout:return {"status":"workout_missing"}
    link=database.get_calendar_link(workout_id,db_path)
    calendar_id=conn.get("calendar_id") or "primary"

    if schedule.get("is_skipped"):
        if link:
            delete_event(user_id,link["google_event_id"],db_path,calendar_id)
            with database.session(db_path) as con:
                con.execute("DELETE FROM workout_calendar_links WHERE workout_id=?",(workout_id,))
        return {"status":"removed_skipped"}

    signature=_forge_signature(schedule,workout)

    if link:
        try:event=get_event(user_id,link["google_event_id"],db_path,calendar_id)
        except Exception:
            event=None

        # Pull Google changes first.
        if event and event.get("status")!="cancelled":
            google_updated=event.get("updated")
            local_start=_event_local_start(user_id,event,db_path)
            if google_updated and google_updated!=link.get("last_google_updated") and local_start:
                day=local_start.weekday()
                hhmm=local_start.strftime("%H:%M")
                if day!=int(schedule["scheduled_day"]) or hhmm!=(schedule.get("scheduled_time") or settings["default_workout_time"]):
                    try:
                        schedule=database.set_workout_schedule_from_calendar(
                            user_id,workout_id,day,hhmm,db_path
                        )
                        signature=_forge_signature(schedule,workout)
                        database.update_calendar_link_sync(workout_id,google_updated,signature,db_path)
                        return {"status":"pulled_from_google","workout_id":workout_id,
                                "scheduled_day":day,"scheduled_time":hhmm}
                    except ValueError as exc:
                        return {"status":"google_change_conflict","error":str(exc),"workout_id":workout_id}

        # Push Forge changes if local schedule differs.
        if signature!=link.get("last_forge_signature"):
            event=update_event(user_id,link["google_event_id"],schedule,workout,db_path,calendar_id)
            database.update_calendar_link_sync(workout_id,event.get("updated"),signature,db_path)
            return {"status":"pushed_to_google","workout_id":workout_id}

        if event:
            database.update_calendar_link_sync(workout_id,event.get("updated"),signature,db_path)
        return {"status":"in_sync","workout_id":workout_id}

    event=create_event(user_id,schedule,workout,db_path,calendar_id)
    database.upsert_calendar_link(user_id,workout_id,event["id"],calendar_id,event.get("updated"),signature,db_path)
    return {"status":"created_google_event","workout_id":workout_id,"event_id":event["id"]}

def sync_all(user_id: int, db_path: Path) -> dict:
    schedule=database.get_workout_schedule(user_id,db_path)
    results=[]
    for item in schedule:
        try:results.append(sync_workout(user_id,item["workout_id"],db_path))
        except Exception as exc:
            results.append({"status":"error","workout_id":item["workout_id"],"error":str(exc)})
    return {
        "results":results,
        "created":sum(x.get("status")=="created_google_event" for x in results),
        "pushed":sum(x.get("status")=="pushed_to_google" for x in results),
        "pulled":sum(x.get("status")=="pulled_from_google" for x in results),
        "conflicts":sum(x.get("status")=="google_change_conflict" for x in results),
        "errors":sum(x.get("status")=="error" for x in results),
    }
