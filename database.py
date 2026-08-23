from __future__ import annotations

import json
import hashlib
import hmac
import secrets
import sqlite3
import os
import tempfile
import threading
import logging
from urllib.parse import urlsplit
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

DEFAULT_DB_PATH = Path(__file__).with_name("fitness_app_initial_database.sqlite")
SCHEMA_VERSION = 1

# v14.32 free persistence bridge:
# Forge keeps its mature SQLite data layer locally, while a consistent SQLite
# snapshot is persisted in Supabase Postgres after successful write transactions.
# On a fresh Render instance the snapshot is restored before the first DB access.
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "").strip()
PERSISTENCE_KEY = os.getenv("FORGE_PERSISTENCE_KEY", "forge-production").strip() or "forge-production"
_persist_lock = threading.RLock()
_persist_restore_attempted = False
_persist_syncing = False
_persist_available = None
_log = logging.getLogger("forge.persistence")

def _persistence_target() -> str:
    """Return a password-free persistence target for diagnostics."""
    if not SUPABASE_DB_URL:
        return "disabled"
    try:
        u = urlsplit(SUPABASE_DB_URL)
        return f"user={u.username or '?'} host={u.hostname or '?'} port={u.port or '?'} db={(u.path or '/').lstrip('/') or '?'}"
    except Exception:
        return "configured (URL could not be parsed)"

def _persistence_warning(action: str, exc: Exception) -> None:
    global _persist_available
    _persist_available = False
    _log.warning("Supabase persistence %s failed; continuing with local SQLite. %s; error=%s: %s",
                 action, _persistence_target(), type(exc).__name__, exc)


def _pg_connect():
    if not SUPABASE_DB_URL:
        return None
    import psycopg
    return psycopg.connect(SUPABASE_DB_URL, connect_timeout=10)

def _ensure_remote_store(pg) -> None:
    with pg.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS forge_persistence_snapshots (
                app_key TEXT PRIMARY KEY,
                sqlite_blob BYTEA NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        ''')
    pg.commit()

def restore_remote_snapshot(db_path=DEFAULT_DB_PATH) -> bool:
    """Restore the latest durable DB snapshot once per process, if configured."""
    global _persist_restore_attempted
    if not SUPABASE_DB_URL:
        return False
    with _persist_lock:
        if _persist_restore_attempted:
            return False
        _persist_restore_attempted = True
        pg = None
        try:
            pg = _pg_connect()
            if pg is None:
                return False
            _ensure_remote_store(pg)
            with pg.cursor() as cur:
                cur.execute("SELECT sqlite_blob FROM forge_persistence_snapshots WHERE app_key=%s", (PERSISTENCE_KEY,))
                row = cur.fetchone()
            global _persist_available
            _persist_available = True
            _log.info("Supabase persistence connected for restore: %s", _persistence_target())
            if not row:
                return False
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes(row[0]))
            for suffix in ("-wal", "-shm"):
                Path(str(path)+suffix).unlink(missing_ok=True)
            return True
        except Exception as exc:
            _persistence_warning("restore", exc)
            return False
        finally:
            if pg is not None:
                try:
                    pg.close()
                except Exception:
                    pass

def sync_remote_snapshot(db_path=DEFAULT_DB_PATH) -> bool:
    """Persist a transaction-consistent SQLite snapshot to Supabase Postgres."""
    global _persist_syncing
    if not SUPABASE_DB_URL or _persist_syncing:
        return False
    with _persist_lock:
        _persist_syncing = True
        tmp_name = None
        try:
            path = Path(db_path)
            if not path.exists():
                return False
            fd, tmp_name = tempfile.mkstemp(prefix="forge-snapshot-", suffix=".sqlite")
            os.close(fd)
            source = sqlite3.connect(path)
            target = sqlite3.connect(tmp_name)
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()
            payload = Path(tmp_name).read_bytes()
            pg = None
            try:
                pg = _pg_connect()
                if pg is None:
                    return False
                _ensure_remote_store(pg)
                with pg.cursor() as cur:
                    cur.execute('''
                        INSERT INTO forge_persistence_snapshots(app_key, sqlite_blob, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT(app_key) DO UPDATE
                        SET sqlite_blob=EXCLUDED.sqlite_blob, updated_at=NOW()
                    ''', (PERSISTENCE_KEY, payload))
                pg.commit()
                global _persist_available
                _persist_available = True
                return True
            except Exception as exc:
                _persistence_warning("sync", exc)
                return False
            finally:
                if pg is not None:
                    try:
                        pg.close()
                    except Exception:
                        pass
        finally:
            if tmp_name:
                Path(tmp_name).unlink(missing_ok=True)
            _persist_syncing = False



def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    restore_remote_snapshot(db_path)
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


@contextmanager
def session(db_path: str | Path = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    con = connect(db_path)
    start_changes = con.total_changes
    try:
        yield con
        con.commit()
        # Reads no longer upload a full database snapshot. Only transactions
        # that actually changed SQLite trigger the durable Supabase snapshot.
        if con.total_changes > start_changes:
            sync_remote_snapshot(db_path)
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def ensure_schema(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Create only application tables; never drops or rewrites exercise tables."""
    schema = Path(__file__).with_name("database_schema.sql").read_text(encoding="utf-8")
    with session(db_path) as con:
        con.executescript(schema)
        con.execute(
            "INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)",
            (SCHEMA_VERSION,),
        )

    ensure_performance_weight_column(db_path)
    with session(db_path) as con:
        cols={r["name"] for r in con.execute("PRAGMA table_info(user_profiles)").fetchall()}
        if "cardio_preference" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN cardio_preference TEXT NOT NULL DEFAULT 'moderate'")
        if "workout_split" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN workout_split TEXT NOT NULL DEFAULT 'auto'")
        if "sport" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN sport TEXT NOT NULL DEFAULT 'general'")
        if "core_workouts_per_week" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN core_workouts_per_week INTEGER NOT NULL DEFAULT 2")
        if "cardio_workouts_per_week" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN cardio_workouts_per_week INTEGER NOT NULL DEFAULT 2")
        ws_cols={r["name"] for r in con.execute("PRAGMA table_info(workout_schedule)").fetchall()}
        if ws_cols and "scheduled_time" not in ws_cols:
            con.execute("ALTER TABLE workout_schedule ADD COLUMN scheduled_time TEXT NOT NULL DEFAULT '17:00'")
        ne_cols={r["name"] for r in con.execute("PRAGMA table_info(nutrition_entries)").fetchall()}
        if ne_cols and "source" not in ne_cols:
            con.execute("ALTER TABLE nutrition_entries ADD COLUMN source TEXT")
        if ne_cols and "source_url" not in ne_cols:
            con.execute("ALTER TABLE nutrition_entries ADD COLUMN source_url TEXT")
    ensure_expanded_exercise_directory(db_path)

def create_user(db_path=DEFAULT_DB_PATH) -> int:
    with session(db_path) as con:
        cur = con.execute("INSERT INTO users DEFAULT VALUES")
        return int(cur.lastrowid)


def upsert_profile(user_id: int, profile: dict[str, Any], db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute(
            """INSERT INTO user_profiles
            (user_id, goal, experience, days_per_week, minutes_per_workout,
             equipment_json, preferred_exercises_json, excluded_exercises_json,
             priority_muscles_json, recovery_level, cardio_preference, workout_split, sport, core_workouts_per_week, cardio_workouts_per_week, seed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              goal=excluded.goal, experience=excluded.experience,
              days_per_week=excluded.days_per_week,
              minutes_per_workout=excluded.minutes_per_workout,
              equipment_json=excluded.equipment_json,
              preferred_exercises_json=excluded.preferred_exercises_json,
              excluded_exercises_json=excluded.excluded_exercises_json,
              priority_muscles_json=excluded.priority_muscles_json,
              recovery_level=excluded.recovery_level,
              cardio_preference=excluded.cardio_preference,
              workout_split=excluded.workout_split, sport=excluded.sport, core_workouts_per_week=excluded.core_workouts_per_week, cardio_workouts_per_week=excluded.cardio_workouts_per_week, seed=excluded.seed,
              updated_at=CURRENT_TIMESTAMP""",
            (
                user_id, profile["goal"], profile["experience"], profile["days_per_week"],
                profile["minutes_per_workout"], _json(profile.get("equipment", [])),
                _json(profile.get("preferred_exercises", [])), _json(profile.get("excluded_exercises", [])),
                _json(profile.get("priority_muscles", [])), profile.get("recovery_level", "normal"),
                profile.get("cardio_preference", "moderate"), profile.get("workout_split", "auto"), profile.get("sport", "general"),
                max(0, min(int(profile.get("core_workouts_per_week", 2)), int(profile["days_per_week"]))),
                max(0, min(int(profile.get("cardio_workouts_per_week", 2)), int(profile["days_per_week"]))),
                profile.get("seed"),
            ),
        )


def get_profile(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with session(db_path) as con:
        row = con.execute("SELECT * FROM user_profiles WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    for key in ("equipment", "preferred_exercises", "excluded_exercises", "priority_muscles"):
        d[key] = json.loads(d.pop(f"{key}_json"))
    return d


def save_training_state(user_id: int, state: dict[str, Any], db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute(
            """INSERT INTO training_state
            (user_id, week_number, consecutive_hard_weeks, missed_workouts,
             fatigue_score, completion_rate, exercise_history_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              week_number=excluded.week_number,
              consecutive_hard_weeks=excluded.consecutive_hard_weeks,
              missed_workouts=excluded.missed_workouts,
              fatigue_score=excluded.fatigue_score,
              completion_rate=excluded.completion_rate,
              exercise_history_json=excluded.exercise_history_json,
              updated_at=CURRENT_TIMESTAMP""",
            (user_id, state.get("week_number", 1), state.get("consecutive_hard_weeks", 0),
             state.get("missed_workouts", 0), state.get("fatigue_score", 0.0),
             state.get("last_week_completion_rate", 1.0), _json(state.get("exercise_history", {}))),
        )


def get_training_state(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        row = con.execute("SELECT * FROM training_state WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return {"week_number": 1, "consecutive_hard_weeks": 0, "missed_workouts": 0,
                "fatigue_score": 0.0, "last_week_completion_rate": 1.0, "exercise_history": {}}
    d = dict(row)
    d["exercise_history"] = json.loads(d.pop("exercise_history_json"))
    d.pop("updated_at", None)
    return d


def save_program(user_id: int, plan: dict[str, Any], db_path=DEFAULT_DB_PATH, replace_active: bool = False) -> int:
    with session(db_path) as con:
        if replace_active:
            # Keep the old program/workouts/sessions for history and PRs, but make
            # the rebuilt program the single active plan. This avoids the v14.34
            # duplicate "week 1" collision without deleting training history.
            con.execute(
                "UPDATE programs SET status='replaced', updated_at=CURRENT_TIMESTAMP "
                "WHERE user_id=? AND status='active'",
                (user_id,),
            )
            cur = con.execute("INSERT INTO programs(user_id, status) VALUES (?, 'active')", (user_id,))
            program_id = int(cur.lastrowid)
        else:
            program = con.execute(
                "SELECT id FROM programs WHERE user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if program:
                program_id = int(program["id"])
            else:
                cur = con.execute("INSERT INTO programs(user_id, status) VALUES (?, 'active')", (user_id,))
                program_id = int(cur.lastrowid)

        wc = plan.get("weekly_controller", {})
        week = int(wc.get("week_number", 1))
        existing = con.execute(
            "SELECT id FROM program_weeks WHERE program_id=? AND week_number=?",
            (program_id, week),
        ).fetchone()
        if existing:
            raise ValueError(f"Program week {week} already exists")

        week_cur = con.execute(
            """INSERT INTO program_weeks(program_id, week_number, recommendation,
               fatigue_score, completion_rate, consecutive_hard_weeks, missed_workouts, plan_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (program_id, week, wc.get("recommendation"), wc.get("fatigue_score", 0),
             wc.get("completion_rate", 1), wc.get("consecutive_hard_weeks", 0),
             wc.get("missed_workouts", 0), _json(plan)),
        )
        week_id = int(week_cur.lastrowid)
        for wi, workout in enumerate(plan.get("workouts", [])):
            wcur = con.execute(
                """INSERT INTO workouts(program_week_id, name, workout_index, estimated_minutes, status)
                   VALUES (?, ?, ?, ?, 'planned')""",
                (week_id, workout["name"], wi, workout.get("estimated_minutes", 0)),
            )
            workout_id = int(wcur.lastrowid)
            for ei, exercise in enumerate(workout.get("exercises", [])):
                con.execute(
                    """INSERT INTO workout_exercises
                    (workout_id, exercise_id, exercise_order, sets, min_reps, max_reps,
                     rest_seconds, progression_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (workout_id, exercise["exercise_id"], ei, exercise["sets"],
                     exercise["min_reps"], exercise["max_reps"], exercise["rest_seconds"],
                     exercise["progression_method"]),
                )
        con.execute("UPDATE programs SET current_week=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (week, program_id))
        return program_id


def get_current_plan(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with session(db_path) as con:
        row = con.execute(
            """SELECT pw.plan_json FROM programs p
               JOIN program_weeks pw ON pw.program_id=p.id
               WHERE p.user_id=? AND p.status='active'
               ORDER BY pw.week_number DESC, pw.id DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
    return json.loads(row["plan_json"]) if row else None


def start_workout(user_id: int, workout_id: int, db_path=DEFAULT_DB_PATH) -> int:
    with session(db_path) as con:
        row = con.execute(
            """SELECT w.id, w.status FROM workouts w
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE w.id=? AND p.user_id=?""", (workout_id, user_id)
        ).fetchone()
        if not row:
            raise ValueError("Workout not found for user")

        existing = con.execute(
            """SELECT ws.id FROM workout_sessions ws
               WHERE ws.workout_id=? AND ws.status='active'
               ORDER BY ws.started_at DESC LIMIT 1""",
            (workout_id,),
        ).fetchone()
        if existing:
            sid=int(existing["id"])
            con.execute("INSERT OR IGNORE INTO session_state(session_id,current_exercise_index,current_set_index) VALUES (?,0,0)",(sid,))
            return sid

        cur = con.execute(
            "INSERT INTO workout_sessions(workout_id, status, started_at) VALUES (?, 'active', CURRENT_TIMESTAMP)",
            (workout_id,),
        )
        con.execute(
            "UPDATE workouts SET status='active', started_at=COALESCE(started_at, CURRENT_TIMESTAMP) WHERE id=?",
            (workout_id,),
        )
        sid=int(cur.lastrowid)
        con.execute("INSERT OR IGNORE INTO session_state(session_id,current_exercise_index,current_set_index) VALUES (?,0,0)",(sid,))
        return sid



def record_performance(user_id: int, session_id: int, exercise_id: int, data: dict[str, Any], db_path=DEFAULT_DB_PATH) -> int:
    with session(db_path) as con:
        valid = con.execute(
            """SELECT ws.id FROM workout_sessions ws
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE ws.id=? AND p.user_id=?""", (session_id, user_id)
        ).fetchone()
        if not valid:
            raise ValueError("Workout session not found for user")
        cur = con.execute(
            """INSERT INTO exercise_performance
               (session_id, exercise_id, completed_sets, reps_json, difficulty, skipped,
                weight, duration_seconds, load_mode, recorded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (
                session_id,
                exercise_id,
                int(data.get("completed_sets", 0)),
                _json(data.get("reps", [])),
                data.get("difficulty"),
                int(bool(data.get("skipped", False))),
                data.get("weight") if data.get("weight") is not None else 0,
                data.get("duration_seconds"),
                data.get("load_mode") or "weight",
            ),
        )
        return int(cur.lastrowid)



def finish_workout(user_id: int, session_id: int, completed: bool, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        row = con.execute(
            """SELECT ws.workout_id FROM workout_sessions ws
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE ws.id=? AND p.user_id=?""", (session_id, user_id)
        ).fetchone()
        if not row:
            raise ValueError("Workout session not found for user")
        status = "completed" if completed else "skipped"
        con.execute("UPDATE workout_sessions SET status=?, completed_at=CURRENT_TIMESTAMP WHERE id=?", (status, session_id))
        con.execute("UPDATE workouts SET status=?, completed_at=CURRENT_TIMESTAMP WHERE id=?", (status, row["workout_id"]))


def database_stats(db_path=DEFAULT_DB_PATH) -> dict[str, int]:
    with session(db_path) as con:
        names = [r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return {name: int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]) for name in names}





def ensure_performance_weight_column(db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        cols = [r["name"] for r in con.execute("PRAGMA table_info(exercise_performance)").fetchall()]
        if "weight" not in cols:
            con.execute("ALTER TABLE exercise_performance ADD COLUMN weight REAL")
        if "duration_seconds" not in cols:
            con.execute("ALTER TABLE exercise_performance ADD COLUMN duration_seconds INTEGER")
        if "load_mode" not in cols:
            con.execute("ALTER TABLE exercise_performance ADD COLUMN load_mode TEXT NOT NULL DEFAULT 'weight'")


def get_active_session(user_id: int, db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        row = con.execute(
            """SELECT ws.*, w.workout_index, w.name AS workout_name
               FROM workout_sessions ws
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=? AND ws.status='active'
               ORDER BY ws.started_at DESC, ws.id DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def get_exercise_performance_for_session(session_id: int, exercise_id: int, db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        rows = con.execute(
            """SELECT * FROM exercise_performance
               WHERE session_id=? AND exercise_id=?
               ORDER BY recorded_at ASC, id ASC""",
            (session_id, exercise_id),
        ).fetchall()
        return [dict(r) for r in rows]


def aggregate_recent_exercise_history(user_id: int, db_path=DEFAULT_DB_PATH):
    """Build generator-friendly exercise history keyed by exercise name."""
    with session(db_path) as con:
        rows = con.execute(
            """SELECT e.name, ep.completed_sets, ep.reps_json, ep.difficulty,
                      ep.skipped, ep.weight, ep.recorded_at
               FROM exercise_performance ep
               JOIN exercises e ON e.id=ep.exercise_id
               JOIN workout_sessions ws ON ws.id=ep.session_id
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=?
               ORDER BY ep.recorded_at ASC, ep.id ASC""",
            (user_id,),
        ).fetchall()

    history = {}
    for row in rows:
        item = history.setdefault(
            row["name"],
            {"completed_sets": 0, "reps": [], "difficulty": None, "skipped": False, "weights": []},
        )
        item["completed_sets"] += int(row["completed_sets"] or 0)
        try:
            reps = json.loads(row["reps_json"]) if isinstance(row["reps_json"], str) else (row["reps_json"] or [])
        except Exception:
            reps = []
        if isinstance(reps, list):
            item["reps"].extend(int(x) for x in reps if isinstance(x, (int, float)))
        if row["difficulty"] is not None:
            item["difficulty"] = float(row["difficulty"])
        item["skipped"] = bool(row["skipped"])
        if row["weight"] is not None:
            item["weights"].append(float(row["weight"]))
    return history


AUTH_SESSION_DAYS = 30
PASSWORD_ITERATIONS = 240_000

def _normalize_email(email: str) -> str:
    return email.strip().lower()

def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    if salt_hex is None:
        salt = secrets.token_bytes(16)
        salt_hex = salt.hex()
    else:
        salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return digest.hex(), salt_hex

def create_account(email: str, password: str, display_name: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    email = _normalize_email(email)
    display_name = display_name.strip()
    if not email or "@" not in email:
        raise ValueError("Enter a valid email address")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not display_name:
        raise ValueError("Display name is required")
    password_hash, salt = _hash_password(password)
    with session(db_path) as con:
        if con.execute("SELECT 1 FROM user_accounts WHERE email=?", (email,)).fetchone():
            raise ValueError("An account with that email already exists")
        cur = con.execute("INSERT INTO users DEFAULT VALUES")
        user_id = int(cur.lastrowid)
        con.execute("""INSERT INTO user_accounts
            (user_id,email,display_name,password_hash,password_salt)
            VALUES (?,?,?,?,?)""",(user_id,email,display_name,password_hash,salt))
        con.execute("""INSERT INTO training_state
            (user_id,week_number,consecutive_hard_weeks,missed_workouts,fatigue_score,completion_rate,exercise_history_json)
            VALUES (?,1,0,0,0,1,'{}')""",(user_id,))
    return {"user_id":user_id,"email":email,"display_name":display_name}

def authenticate_account(email: str, password: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    email = _normalize_email(email)
    with session(db_path) as con:
        row = con.execute("""SELECT user_id,email,display_name,password_hash,password_salt
            FROM user_accounts WHERE email=?""",(email,)).fetchone()
    if not row:
        return None
    candidate,_ = _hash_password(password,row["password_salt"])
    if not hmac.compare_digest(candidate,row["password_hash"]):
        return None
    return {"user_id":int(row["user_id"]),"email":row["email"],"display_name":row["display_name"]}

def create_auth_session(user_id: int, db_path=DEFAULT_DB_PATH) -> str:
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=AUTH_SESSION_DAYS)
    with session(db_path) as con:
        con.execute("INSERT INTO auth_sessions(user_id,token_hash,expires_at) VALUES (?,?,?)",
                    (user_id,token_hash,expires.isoformat()))
    return raw

def get_user_from_token(raw_token: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    if not raw_token:
        return None
    token_hash=hashlib.sha256(raw_token.encode()).hexdigest()
    now=datetime.now(timezone.utc).isoformat()
    with session(db_path) as con:
        row=con.execute("""SELECT ua.user_id,ua.email,ua.display_name,s.expires_at
            FROM auth_sessions s JOIN user_accounts ua ON ua.user_id=s.user_id
            WHERE s.token_hash=? AND s.revoked_at IS NULL AND s.expires_at>?""",
            (token_hash,now)).fetchone()
    return dict(row) if row else None

def revoke_auth_session(raw_token: str, db_path=DEFAULT_DB_PATH) -> None:
    if not raw_token: return
    token_hash=hashlib.sha256(raw_token.encode()).hexdigest()
    with session(db_path) as con:
        con.execute("UPDATE auth_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE token_hash=?",(token_hash,))

def update_account_name(user_id: int, display_name: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    display_name=display_name.strip()
    if not display_name: raise ValueError("Display name is required")
    with session(db_path) as con:
        con.execute("UPDATE user_accounts SET display_name=?,updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
                    (display_name,user_id))
        row=con.execute("SELECT user_id,email,display_name FROM user_accounts WHERE user_id=?",(user_id,)).fetchone()
    if not row: raise ValueError("Account not found")
    return dict(row)



def get_workout_history(user_id: int, limit: int = 50, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with session(db_path) as con:
        rows = con.execute(
            """
            SELECT ws.id AS session_id, ws.workout_id, ws.status, ws.started_at, ws.completed_at,
                   w.name AS workout_name, w.workout_index, w.estimated_minutes,
                   pw.week_number
            FROM workout_sessions ws
            JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=?
            ORDER BY COALESCE(ws.completed_at, ws.started_at) DESC, ws.id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        out = []
        for row in rows:
            d = dict(row)
            perf = con.execute(
                """
                SELECT ep.*, e.name AS exercise_name
                FROM exercise_performance ep
                JOIN exercises e ON e.id=ep.exercise_id
                WHERE ep.session_id=?
                ORDER BY ep.id ASC
                """,
                (d["session_id"],),
            ).fetchall()
            exercise_map = {}
            total_volume = 0.0
            total_sets = 0
            for p in perf:
                pd = dict(p)
                ex = exercise_map.setdefault(
                    int(pd["exercise_id"]),
                    {
                        "exercise_id": int(pd["exercise_id"]),
                        "name": pd["exercise_name"],
                        "sets": [],
                    },
                )
                try:
                    reps_list = json.loads(pd["reps_json"]) if pd["reps_json"] else []
                except Exception:
                    reps_list = []
                weight = float(pd["weight"] or 0)
                for reps in reps_list or [0]:
                    reps = int(reps or 0)
                    ex["sets"].append({
                        "reps": reps,
                        "weight": weight,
                        "rpe": pd["difficulty"],
                        "skipped": bool(pd["skipped"]),
                    })
                    if not pd["skipped"]:
                        total_sets += 1
                        total_volume += weight * reps
            d["exercises"] = list(exercise_map.values())
            d["total_sets"] = total_sets
            d["total_volume"] = round(total_volume, 2)
            out.append(d)
        return out


def get_exercise_history(user_id: int, exercise_id: int, limit: int = 100, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        ex = con.execute("SELECT id, name FROM exercises WHERE id=?", (exercise_id,)).fetchone()
        if not ex:
            raise ValueError("Exercise not found")
        rows = con.execute(
            """
            SELECT ep.*, ws.started_at, ws.completed_at, w.name AS workout_name
            FROM exercise_performance ep
            JOIN workout_sessions ws ON ws.id=ep.session_id
            JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND ep.exercise_id=?
            ORDER BY ep.recorded_at ASC, ep.id ASC
            LIMIT ?
            """,
            (user_id, exercise_id, limit),
        ).fetchall()

    sets = []
    best_weight = 0.0
    best_e1rm = 0.0
    best_volume_set = 0.0
    best_reps = 0
    for row in rows:
        try:
            reps_list = json.loads(row["reps_json"]) if row["reps_json"] else []
        except Exception:
            reps_list = []
        weight = float(row["weight"] or 0) if row["weight"] is not None else None
        duration = int(row["duration_seconds"] or 0) if "duration_seconds" in row.keys() else 0
        load_mode = (row["load_mode"] if "load_mode" in row.keys() else "weight") or "weight"
        if duration > 0:
            best_reps = max(best_reps, duration)
            sets.append({
                "recorded_at": row["recorded_at"],
                "workout_name": row["workout_name"],
                "weight": weight,
                "load_mode": load_mode,
                "duration_seconds": duration,
                "reps": None,
                "rpe": row["difficulty"],
                "e1rm": 0,
                "volume": 0,
            })
            continue
        for reps in reps_list or [0]:
            reps = int(reps or 0)
            calc_weight = float(weight or 0)
            e1rm = calc_weight * (1 + reps / 30.0) if calc_weight > 0 and reps > 0 and load_mode != "bodyweight" else 0.0
            vol = calc_weight * reps if load_mode != "bodyweight" else 0.0
            if load_mode != "bodyweight":
                best_weight = max(best_weight, calc_weight)
                best_e1rm = max(best_e1rm, e1rm)
                best_volume_set = max(best_volume_set, vol)
            best_reps = max(best_reps, reps)
            sets.append({
                "recorded_at": row["recorded_at"],
                "workout_name": row["workout_name"],
                "weight": weight,
                "load_mode": load_mode,
                "duration_seconds": None,
                "reps": reps,
                "rpe": row["difficulty"],
                "e1rm": round(e1rm, 2),
                "volume": round(vol, 2),
            })

    return {
        "exercise_id": int(ex["id"]),
        "name": ex["name"],
        "sets": sets,
        "prs": {
            "max_weight": round(best_weight, 2),
            "best_e1rm": round(best_e1rm, 2),
            "best_volume_set": round(best_volume_set, 2),
            "best_reps": best_reps,
        },
    }


def get_personal_records(user_id: int, limit: int = 100, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with session(db_path) as con:
        rows = con.execute(
            """
            SELECT e.id AS exercise_id, e.name, e.movement_pattern, e.exercise_type,
                   e.primary_muscle, ep.weight, ep.reps_json, ep.difficulty,
                   ep.recorded_at, ws.id AS session_id
            FROM exercise_performance ep
            JOIN exercises e ON e.id=ep.exercise_id
            JOIN workout_sessions ws ON ws.id=ep.session_id
            JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND ep.skipped=0
            ORDER BY ep.recorded_at ASC, ep.id ASC
            """,
            (user_id,),
        ).fetchall()

    by_ex = {}
    for row in rows:
        try:
            reps_list = json.loads(row["reps_json"]) if row["reps_json"] else []
        except Exception:
            reps_list = []
        weight = float(row["weight"] or 0)
        for reps in reps_list or [0]:
            reps = int(reps or 0)
            e1rm = weight * (1 + reps / 30.0) if weight > 0 and reps > 0 else 0.0
            cur = by_ex.setdefault(
                int(row["exercise_id"]),
                {
                    "exercise_id": int(row["exercise_id"]),
                    "name": row["name"],
                    "movement_pattern": row["movement_pattern"],
                    "exercise_type": row["exercise_type"],
                    "primary_muscle": row["primary_muscle"],
                    "max_weight": 0.0,
                    "best_e1rm": 0.0,
                    "best_volume_set": 0.0,
                    "best_reps": 0,
                    "last_recorded_at": None,
                },
            )
            cur["max_weight"] = max(cur["max_weight"], weight)
            cur["best_e1rm"] = max(cur["best_e1rm"], e1rm)
            cur["best_volume_set"] = max(cur["best_volume_set"], weight * reps)
            cur["best_reps"] = max(cur["best_reps"], reps)
            cur["last_recorded_at"] = row["recorded_at"]
    records = list(by_ex.values())
    for r in records:
        r["max_weight"] = round(r["max_weight"], 2)
        r["best_e1rm"] = round(r["best_e1rm"], 2)
        r["best_volume_set"] = round(r["best_volume_set"], 2)
    records.sort(key=lambda x: (x["best_e1rm"], x["max_weight"]), reverse=True)
    return records[:limit]


def get_latest_exercise_targets(user_id: int, exercise_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    history = get_exercise_history(user_id, exercise_id, 100, db_path)
    sets = history["sets"]
    if not sets:
        return None
    latest = sets[-1]
    recent = sets[-3:]
    avg_rpe = sum(float(x["rpe"] or 0) for x in recent) / max(1, len(recent))
    max_reps = max(int(x["reps"]) for x in recent)
    weight = float(latest["weight"])
    if avg_rpe <= 7 and max_reps >= 8:
        suggestion = {"action": "increase_load", "suggested_weight": round(weight + 5, 2)}
    elif avg_rpe >= 9:
        suggestion = {"action": "repeat_or_reduce", "suggested_weight": weight}
    else:
        suggestion = {"action": "repeat_and_add_reps", "suggested_weight": weight}
    return {
        "exercise_id": exercise_id,
        "last_weight": weight,
        "recent_average_rpe": round(avg_rpe, 2),
        "recent_best_reps": max_reps,
        **suggestion,
    }



def _equipment_allowed(exercise_equipment: str, profile_equipment: list[str]) -> bool:
    if "full_gym" in profile_equipment:
        return True
    available = {x.lower().replace("_", " ").strip() for x in profile_equipment}
    required = {x.lower().strip() for x in (exercise_equipment or "").split(",") if x.strip()}
    aliases = {
        "dumbbells": {"dumbbell", "dumbbells"},
        "barbell": {"barbell"},
        "bench": {"bench"},
        "machine": {"machine", "machines"},
        "cable machine": {"cable", "cable machine"},
        "bodyweight": {"bodyweight"},
        "squat rack": {"squat rack"},
    }
    expanded = set(available)
    for item in list(available):
        expanded.update(aliases.get(item, set()))
    return all(any(req == a or req in a or a in req for a in expanded) for req in required)



def get_cardio_options_for_user(user_id: int, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    profile=get_profile(user_id,db_path) or {}
    equipment=profile.get("equipment",["full_gym"])
    with session(db_path) as con:
        rows=con.execute(
            """SELECT id,name,primary_muscle,secondary_muscles,movement_pattern,equipment,
                      difficulty,exercise_type,min_reps,max_reps,default_sets,
                      default_rest_seconds,progression_method,notes
               FROM exercises
               WHERE exercise_type='Cardio'
                  OR movement_pattern IN ('Steady-State Cardio','Interval Cardio')
               ORDER BY movement_pattern,name"""
        ).fetchall()
    out=[]
    for row in rows:
        item=dict(row)
        item["equipment_compatible"]=_equipment_allowed(item["equipment"],equipment)
        out.append(item)
    return out

def swap_workout_cardio(user_id: int, workout_id: int, new_exercise_id: int,
                        db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    options={int(x["id"]):x for x in get_cardio_options_for_user(user_id,db_path)}
    new=options.get(int(new_exercise_id))
    if not new:
        raise ValueError("That exercise is not a cardio option")
    if not new["equipment_compatible"]:
        raise ValueError("That cardio option does not match your equipment")

    with session(db_path) as con:
        row=con.execute(
            """SELECT w.id,w.workout_index,pw.id AS week_id,pw.plan_json
               FROM workouts w
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE w.id=? AND p.user_id=? AND p.status='active'""",(workout_id,user_id)
        ).fetchone()
        if not row:
            raise ValueError("Workout not found")

        plan=json.loads(row["plan_json"])
        idx=int(row["workout_index"])
        workouts=plan.get("workouts",[])
        if idx<0 or idx>=len(workouts):
            raise ValueError("Workout is missing from the active plan")
        workout=workouts[idx]
        module=workout.get("cardio_module")
        if not module:
            raise ValueError("This training day does not have a cardio module")

        old=module.get("name")
        module["name"]=new["name"]
        module["exercise_id"]=int(new["id"])
        module["movement_pattern"]=new["movement_pattern"]
        module["equipment"]=new["equipment"]

        # Keep top-level module list synchronized.
        for top in plan.get("cardio_modules",[]):
            if int(top.get("workout_index",-1))==idx:
                top.update(module)
                break

        con.execute(
            "UPDATE program_weeks SET plan_json=? WHERE id=?",
            (_json(plan),int(row["week_id"]))
        )
        con.execute(
            """INSERT INTO progression_events(user_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?)""",
            (user_id,workout_id,"cardio_swap",old,new["name"],"User swapped standalone cardio module")
        )
    return {
        "workout_id":int(workout_id),
        "old_cardio":old,
        "cardio_name":new["name"],
        "cardio_exercise_id":int(new["id"]),
        "cardio_movement_pattern":new["movement_pattern"],
        "cardio_equipment":new["equipment"],
    }


def get_substitutions_for_user(user_id: int, exercise_id: int, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    profile = get_profile(user_id, db_path) or {}
    equipment = profile.get("equipment", ["full_gym"])
    with session(db_path) as con:
        original=con.execute(
            """SELECT id,name,primary_muscle,secondary_muscles,movement_pattern,equipment,
                      difficulty,exercise_type,min_reps,max_reps,default_sets,
                      default_rest_seconds,progression_method
               FROM exercises WHERE id=?""",(exercise_id,)
        ).fetchone()
        if not original:
            raise ValueError("Exercise not found")
        rows = con.execute(
            """
            SELECT e.id, e.name, e.primary_muscle, e.secondary_muscles, e.movement_pattern,
                   e.equipment, e.difficulty, e.exercise_type, e.min_reps, e.max_reps,
                   e.default_sets, e.default_rest_seconds, e.progression_method,
                   s.reason
            FROM exercise_substitutions s
            JOIN exercises e ON e.id=s.substitute_exercise_id
            WHERE s.exercise_id=?
            """,
            (exercise_id,),
        ).fetchall()
        pref_rows=con.execute(
            "SELECT exercise_id,preference FROM user_exercise_preferences WHERE user_id=?",
            (user_id,),
        ).fetchall()
    prefs={int(r["exercise_id"]):r["preference"] for r in pref_rows}
    orig=dict(original); om=_exercise_intelligence_metadata(orig)
    out=[]
    for row in rows:
        d=dict(row)
        d["equipment_compatible"]=_equipment_allowed(d["equipment"],equipment)
        d.update(_exercise_intelligence_metadata(d))
        pref=prefs.get(int(d["id"]),"neutral")
        d["user_preference"]=pref
        score=0
        reasons=[]
        if d["movement_pattern"]==orig["movement_pattern"]:
            score+=40; reasons.append("same movement")
        if d["primary_muscle"]==orig["primary_muscle"]:
            score+=25; reasons.append("same primary muscle")
        elif d["primary_muscle"].split(",")[0].strip()==orig["primary_muscle"].split(",")[0].strip():
            score+=18; reasons.append("similar target")
        if d["exercise_type"]==orig["exercise_type"]:
            score+=10
        score-=abs(d["fatigue_cost"]-om["fatigue_cost"])*4
        score-=abs(d["skill_demand"]-om["skill_demand"])*2
        if d["equipment_compatible"]:
            score+=20; reasons.append("available equipment")
        else:
            score-=60
        if pref=="favorite":
            score+=30; reasons.append("favorite")
        elif pref=="avoid":
            score-=80
        elif pref=="painful":
            score-=200
        if profile.get("recovery_level")=="low":
            score+=(om["fatigue_cost"]-d["fatigue_cost"])*5
        d["substitution_score"]=score
        d["smart_reason"]=", ".join(reasons[:3]) or d.get("reason") or "similar exercise"
        out.append(d)
    out.sort(key=lambda x:(x["substitution_score"],x["equipment_compatible"]),reverse=True)
    return out


def swap_workout_exercise(user_id: int, workout_id: int, old_exercise_id: int,
                          new_exercise_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    allowed = {x["id"]: x for x in get_substitutions_for_user(user_id, old_exercise_id, db_path)}
    new = allowed.get(new_exercise_id)
    if not new:
        raise ValueError("That exercise is not an approved substitution")
    if not new["equipment_compatible"]:
        raise ValueError("That substitution does not match your available equipment")

    with session(db_path) as con:
        owned = con.execute(
            """SELECT we.id AS workout_exercise_id, we.exercise_order, pw.id AS week_id, pw.plan_json
               FROM workout_exercises we
               JOIN workouts w ON w.id=we.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=? AND we.workout_id=? AND we.exercise_id=?
               ORDER BY we.exercise_order LIMIT 1""",
            (user_id, workout_id, old_exercise_id),
        ).fetchone()
        if not owned:
            raise ValueError("Exercise is not part of this workout")

        con.execute(
            """UPDATE workout_exercises
               SET exercise_id=?, min_reps=?, max_reps=?, rest_seconds=?, progression_method=?
               WHERE id=?""",
            (new_exercise_id, new["min_reps"], new["max_reps"], new["default_rest_seconds"],
             new["progression_method"], owned["workout_exercise_id"]),
        )

        plan=json.loads(owned["plan_json"])
        workout_row=con.execute("SELECT workout_index FROM workouts WHERE id=?",(workout_id,)).fetchone()
        wi=int(workout_row["workout_index"])
        order=int(owned["exercise_order"])
        ex=plan["workouts"][wi]["exercises"][order]
        ex.update({
            "exercise_id":new_exercise_id,
            "name":new["name"],
            "primary_muscle":new["primary_muscle"],
            "secondary_muscles":new["secondary_muscles"],
            "movement_pattern":new["movement_pattern"],
            "equipment":new["equipment"],
            "difficulty":new["difficulty"],
            "exercise_type":new["exercise_type"],
            "min_reps":new["min_reps"],
            "max_reps":new["max_reps"],
            "rest_seconds":new["default_rest_seconds"],
            "progression_method":new["progression_method"],
        })
        con.execute("UPDATE program_weeks SET plan_json=? WHERE id=?",(_json(plan),owned["week_id"]))

        con.execute(
            """INSERT INTO progression_events(user_id,exercise_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?,?)""",
            (user_id,new_exercise_id,workout_id,"exercise_swap",str(old_exercise_id),str(new_exercise_id),
             new.get("reason") or "User-selected substitution"),
        )
    return new


def update_workout_exercise_sets(user_id: int, workout_id: int, exercise_id: int, sets: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    sets=max(1,min(12,int(sets)))
    with session(db_path) as con:
        row=con.execute("""SELECT we.id,we.exercise_order,w.workout_index,pw.id AS week_id,pw.plan_json
            FROM workout_exercises we JOIN workouts w ON w.id=we.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND w.id=? AND we.exercise_id=? LIMIT 1""",(user_id,workout_id,exercise_id)).fetchone()
        if not row: raise ValueError("Exercise is not part of this workout")
        con.execute("UPDATE workout_exercises SET sets=? WHERE id=?",(sets,row["id"]))
        plan=json.loads(row["plan_json"]); wi=int(row["workout_index"]); oi=int(row["exercise_order"])
        plan["workouts"][wi]["exercises"][oi]["sets"]=sets
        con.execute("UPDATE program_weeks SET plan_json=? WHERE id=?",(_json(plan),row["week_id"]))
    return {"workout_id":workout_id,"exercise_id":exercise_id,"sets":sets}


def apply_shortened_workout(user_id: int, workout_id: int, target_minutes: int,
                            db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        row=con.execute(
            """SELECT w.workout_index,w.estimated_minutes,pw.id AS week_id,pw.plan_json
               FROM workouts w
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE w.id=? AND p.user_id=?""",(workout_id,user_id)
        ).fetchone()
        if not row:
            raise ValueError("Workout not found for user")
        plan=json.loads(row["plan_json"])
        wi=int(row["workout_index"])
        workout=plan["workouts"][wi]
        exercises=workout.get("exercises",[])
        if not exercises:
            raise ValueError("Workout has no exercises")

        original_minutes=max(1,int(workout.get("estimated_minutes") or row["estimated_minutes"] or 45))
        ratio=max(.25,min(1.0,target_minutes/original_minutes))
        keep=max(1,min(len(exercises),round(len(exercises)*ratio)))
        kept=exercises[:keep]
        removed=exercises[keep:]
        workout["exercises"]=kept
        workout["estimated_minutes"]=target_minutes

        con.execute("DELETE FROM workout_exercises WHERE workout_id=? AND exercise_order>=?",(workout_id,keep))
        con.execute("UPDATE workouts SET estimated_minutes=? WHERE id=?",(target_minutes,workout_id))
        con.execute("UPDATE program_weeks SET plan_json=? WHERE id=?",(_json(plan),row["week_id"]))
        con.execute(
            """INSERT INTO progression_events(user_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?)""",
            (user_id,workout_id,"coach_shorten",str(original_minutes),str(target_minutes),
             f"Coach shortened workout to {target_minutes} minutes"),
        )
    return {"workout_id":workout_id,"target_minutes":target_minutes,
            "kept_exercises":len(kept),"removed_exercises":[x.get("name") for x in removed]}


def ensure_session_state(session_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("INSERT OR IGNORE INTO session_state(session_id,current_exercise_index,current_set_index) VALUES (?,0,0)", (session_id,))

def get_session_resume_state(user_id: int, session_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        row=con.execute(
            """SELECT ws.id AS session_id,ws.workout_id,ws.status,ws.started_at,ws.completed_at,
                      w.workout_index,w.name AS workout_name,
                      COALESCE(ss.current_exercise_index,0) AS current_exercise_index,
                      COALESCE(ss.current_set_index,0) AS current_set_index,
                      ss.rest_started_at,ss.rest_duration_seconds,ss.feedback,ss.abandoned_at
               FROM workout_sessions ws
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               LEFT JOIN session_state ss ON ss.session_id=ws.id
               WHERE ws.id=? AND p.user_id=?""",(session_id,user_id)).fetchone()
        if not row: raise ValueError("Workout session not found for user")
        d=dict(row)
        logged=con.execute("SELECT exercise_id,COUNT(*) AS logged_sets FROM exercise_performance WHERE session_id=? GROUP BY exercise_id",(session_id,)).fetchall()
        d["logged_sets_by_exercise"]={str(r["exercise_id"]):int(r["logged_sets"]) for r in logged}
        return d

def update_session_position(user_id: int, session_id: int, exercise_index: int, set_index: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        ok=con.execute("""SELECT 1 FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE ws.id=? AND p.user_id=?""",(session_id,user_id)).fetchone()
        if not ok: raise ValueError("Workout session not found for user")
        con.execute("""INSERT INTO session_state(session_id,current_exercise_index,current_set_index,updated_at)
            VALUES (?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET current_exercise_index=excluded.current_exercise_index,
            current_set_index=excluded.current_set_index,updated_at=CURRENT_TIMESTAMP""",
            (session_id,max(0,int(exercise_index)),max(0,int(set_index))))

def start_session_rest(user_id: int, session_id: int, duration_seconds: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        ok=con.execute("""SELECT 1 FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE ws.id=? AND p.user_id=?""",(session_id,user_id)).fetchone()
        if not ok: raise ValueError("Workout session not found for user")
        con.execute("""INSERT INTO session_state(session_id,rest_started_at,rest_duration_seconds,updated_at)
            VALUES (?,CURRENT_TIMESTAMP,?,CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET rest_started_at=CURRENT_TIMESTAMP,
            rest_duration_seconds=excluded.rest_duration_seconds,updated_at=CURRENT_TIMESTAMP""",
            (session_id,max(0,int(duration_seconds))))
        return dict(con.execute("SELECT rest_started_at,rest_duration_seconds FROM session_state WHERE session_id=?",(session_id,)).fetchone())

def clear_session_rest(user_id: int, session_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        ok=con.execute("""SELECT 1 FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE ws.id=? AND p.user_id=?""",(session_id,user_id)).fetchone()
        if not ok: raise ValueError("Workout session not found for user")
        con.execute("UPDATE session_state SET rest_started_at=NULL,rest_duration_seconds=NULL,updated_at=CURRENT_TIMESTAMP WHERE session_id=?",(session_id,))

def save_workout_feedback(user_id: int, session_id: int, feedback: str, db_path=DEFAULT_DB_PATH) -> None:
    allowed={"Too Hard","Hard","Just Right","Easy","Too Easy"}
    if feedback not in allowed: raise ValueError("Invalid workout feedback")
    with session(db_path) as con:
        ok=con.execute("""SELECT 1 FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE ws.id=? AND p.user_id=?""",(session_id,user_id)).fetchone()
        if not ok: raise ValueError("Workout session not found for user")
        con.execute("""INSERT INTO session_state(session_id,feedback,updated_at) VALUES (?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET feedback=excluded.feedback,updated_at=CURRENT_TIMESTAMP""",(session_id,feedback))
        delta={"Too Hard":2.0,"Hard":1.0,"Just Right":0.0,"Easy":-0.5,"Too Easy":-1.0}[feedback]
        con.execute("UPDATE training_state SET fatigue_score=MAX(0,fatigue_score+?),updated_at=CURRENT_TIMESTAMP WHERE user_id=?",(delta,user_id))

def abandon_workout(user_id: int, session_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        row=con.execute("""SELECT ws.workout_id FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE ws.id=? AND p.user_id=?""",(session_id,user_id)).fetchone()
        if not row: raise ValueError("Workout session not found for user")
        con.execute("UPDATE workout_sessions SET status='abandoned',completed_at=CURRENT_TIMESTAMP WHERE id=?",(session_id,))
        con.execute("UPDATE workouts SET status='planned' WHERE id=? AND status='active'",(row["workout_id"],))
        con.execute("""INSERT INTO session_state(session_id,abandoned_at,updated_at) VALUES (?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET abandoned_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP""",(session_id,))

def record_performance_idempotent(user_id: int, request_id: str, session_id: int, exercise_id: int, data: dict[str, Any], db_path=DEFAULT_DB_PATH) -> tuple[int,bool]:
    request_id=(request_id or "").strip()
    if not request_id: raise ValueError("request_id is required")
    with session(db_path) as con:
        row=con.execute("SELECT performance_id FROM set_log_requests WHERE request_id=? AND user_id=?",(request_id,user_id)).fetchone()
        if row: return int(row["performance_id"]),True
    pid=record_performance(user_id,session_id,exercise_id,data,db_path)
    try:
        with session(db_path) as con:
            con.execute("INSERT INTO set_log_requests(request_id,user_id,session_id,exercise_id,performance_id) VALUES (?,?,?,?,?)",
                        (request_id,user_id,session_id,exercise_id,pid))
    except sqlite3.IntegrityError:
        with session(db_path) as con:
            row=con.execute("SELECT performance_id FROM set_log_requests WHERE request_id=? AND user_id=?",(request_id,user_id)).fetchone()
            if row:
                con.execute("DELETE FROM exercise_performance WHERE id=?",(pid,))
                return int(row["performance_id"]),True
        raise
    return pid,False


def save_coach_message(user_id: int, role: str, message: str, action: dict[str, Any] | None = None,
                       db_path=DEFAULT_DB_PATH) -> int:
    if role not in {"user","assistant"}:
        raise ValueError("Invalid coach message role")
    message=(message or "").strip()
    if not message:
        raise ValueError("Coach message cannot be empty")
    with session(db_path) as con:
        cur=con.execute(
            "INSERT INTO coach_messages(user_id,role,message,action_json) VALUES (?,?,?,?)",
            (user_id,role,message,_json(action) if action else None),
        )
        return int(cur.lastrowid)

def get_coach_messages(user_id: int, limit: int = 30, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with session(db_path) as con:
        rows=con.execute(
            """SELECT id,role,message,action_json,created_at
               FROM coach_messages WHERE user_id=?
               ORDER BY id DESC LIMIT ?""",
            (user_id,max(1,min(int(limit),100))),
        ).fetchall()
    out=[]
    for row in reversed(rows):
        d=dict(row)
        raw=d.pop("action_json",None)
        try:d["action"]=json.loads(raw) if raw else None
        except Exception:d["action"]=None
        out.append(d)
    return out

def clear_coach_messages(user_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("DELETE FROM coach_messages WHERE user_id=?",(user_id,))

def get_exercise_by_message(user_id: int, message: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    text=(message or "").lower()
    with session(db_path) as con:
        rows=con.execute(
            """SELECT DISTINCT e.id,e.name
               FROM exercises e
               JOIN workout_exercises we ON we.exercise_id=e.id
               JOIN workouts w ON w.id=we.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=? ORDER BY LENGTH(e.name) DESC""",
            (user_id,),
        ).fetchall()
    for row in rows:
        if row["name"].lower() in text:
            return dict(row)
    return None


DAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

_DEFAULT_WEEK_DAYS = {
    2: [0,3],
    3: [0,2,4],
    4: [0,1,3,4],
    5: [0,1,2,4,5],
    6: [0,1,2,3,4,5],
}

def day_name(day_index: int) -> str:
    return DAY_NAMES[int(day_index) % 7]

def parse_day_name(value: str) -> int | None:
    text=(value or "").strip().lower()
    aliases={
        "mon":0,"monday":0,
        "tue":1,"tues":1,"tuesday":1,
        "wed":2,"wednesday":2,
        "thu":3,"thur":3,"thurs":3,"thursday":3,
        "fri":4,"friday":4,
        "sat":5,"saturday":5,
        "sun":6,"sunday":6,
    }
    return aliases.get(text)

def ensure_workout_schedule(user_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        rows=con.execute(
            """SELECT w.id,w.workout_index
               FROM workouts w
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=? AND p.status='active' AND pw.week_number=(
                 SELECT MAX(pw2.week_number)
                 FROM program_weeks pw2 JOIN programs p2 ON p2.id=pw2.program_id
                 WHERE p2.user_id=? AND p2.status='active'
               )
               ORDER BY w.workout_index""",
            (user_id,user_id),
        ).fetchall()
        count=len(rows)
        days=_DEFAULT_WEEK_DAYS.get(count, list(range(min(count,7))))
        for i,row in enumerate(rows):
            d=days[i] if i<len(days) else min(i,6)
            con.execute(
                """INSERT OR IGNORE INTO workout_schedule(workout_id,scheduled_day,original_day)
                   VALUES (?,?,?)""",
                (int(row["id"]),d,d),
            )

def get_workout_schedule(user_id: int, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    ensure_workout_schedule(user_id,db_path)
    with session(db_path) as con:
        rows=con.execute(
            """SELECT w.id AS workout_id,w.name,w.workout_index,w.status,
                      ws.scheduled_day,ws.original_day,ws.is_skipped,ws.scheduled_time
               FROM workouts w
               JOIN workout_schedule ws ON ws.workout_id=w.id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=? AND p.status='active' AND pw.week_number=(
                 SELECT MAX(pw2.week_number)
                 FROM program_weeks pw2 JOIN programs p2 ON p2.id=pw2.program_id
                 WHERE p2.user_id=? AND p2.status='active'
               )
               ORDER BY ws.scheduled_day,w.workout_index""",
            (user_id,user_id),
        ).fetchall()
    out=[]
    for row in rows:
        d=dict(row)
        d["scheduled_day_name"]=day_name(d["scheduled_day"])
        d["original_day_name"]=day_name(d["original_day"])
        d["is_skipped"]=bool(d["is_skipped"])
        out.append(d)
    return out

def get_workout_schedule_item(user_id: int, workout_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    schedule=get_workout_schedule(user_id,db_path)
    item=next((x for x in schedule if int(x["workout_id"])==int(workout_id)),None)
    if not item:
        raise ValueError("Workout not found in current schedule")
    return item

def find_scheduled_workout(user_id: int, *, workout_id: int | None = None,
                           workout_name: str | None = None, day_index: int | None = None,
                           db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    schedule=get_workout_schedule(user_id,db_path)
    if workout_id is not None:
        found=next((x for x in schedule if int(x["workout_id"])==int(workout_id)),None)
        if found:return found
    if workout_name:
        text=workout_name.lower()
        matches=[x for x in schedule if x["name"].lower() in text or text in x["name"].lower()]
        if matches:return sorted(matches,key=lambda x:len(x["name"]),reverse=True)[0]
    if day_index is not None:
        return next((x for x in schedule if int(x["scheduled_day"])==int(day_index) and not x["is_skipped"]),None)
    return None

def preview_move_workout(user_id: int, workout_id: int, target_day: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    item=get_workout_schedule_item(user_id,workout_id,db_path)
    target_day=int(target_day)
    if target_day<0 or target_day>6:
        raise ValueError("Invalid target day")
    if item["status"] in {"active","completed"}:
        return {
            "valid":False,
            "reason":f"{item['name']} cannot be moved because it is {item['status']}.",
            "workout":item,
            "target_day":target_day,
            "target_day_name":day_name(target_day),
        }
    if int(item["scheduled_day"])==target_day:
        return {
            "valid":False,
            "reason":f"{item['name']} is already scheduled for {day_name(target_day)}.",
            "workout":item,
            "target_day":target_day,
            "target_day_name":day_name(target_day),
        }

    schedule=get_workout_schedule(user_id,db_path)
    conflict=next((x for x in schedule if int(x["workout_id"])!=int(workout_id)
                   and int(x["scheduled_day"])==target_day and not x["is_skipped"]),None)
    warnings=[]
    if conflict:
        return {
            "valid":False,
            "reason":f"{day_name(target_day)} already has {conflict['name']}.",
            "conflict":conflict,
            "workout":item,
            "target_day":target_day,
            "target_day_name":day_name(target_day),
            "suggested_action":"swap_workouts",
        }

    other_days=[int(x["scheduled_day"]) for x in schedule
                if int(x["workout_id"])!=int(workout_id) and not x["is_skipped"]]
    if any(abs(target_day-d)==1 for d in other_days):
        warnings.append("This creates back-to-back training days.")
    return {
        "valid":True,
        "workout":item,
        "from_day":int(item["scheduled_day"]),
        "from_day_name":item["scheduled_day_name"],
        "target_day":target_day,
        "target_day_name":day_name(target_day),
        "warnings":warnings,
    }

def move_workout_day(user_id: int, workout_id: int, target_day: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    preview=preview_move_workout(user_id,workout_id,target_day,db_path)
    if not preview.get("valid"):
        raise ValueError(preview.get("reason","Workout move is not valid"))
    with session(db_path) as con:
        con.execute(
            "UPDATE workout_schedule SET scheduled_day=?,updated_at=CURRENT_TIMESTAMP WHERE workout_id=?",
            (int(target_day),int(workout_id)),
        )
        con.execute(
            """INSERT INTO progression_events(user_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?)""",
            (user_id,workout_id,"move_workout",
             preview["from_day_name"],preview["target_day_name"],
             "Coach-approved workout reschedule"),
        )
    return preview

def swap_workout_days(user_id: int, workout_id_a: int, workout_id_b: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    a=get_workout_schedule_item(user_id,workout_id_a,db_path)
    b=get_workout_schedule_item(user_id,workout_id_b,db_path)
    if a["status"] in {"active","completed"} or b["status"] in {"active","completed"}:
        raise ValueError("Active or completed workouts cannot be rescheduled")
    with session(db_path) as con:
        con.execute("UPDATE workout_schedule SET scheduled_day=?,updated_at=CURRENT_TIMESTAMP WHERE workout_id=?",
                    (b["scheduled_day"],a["workout_id"]))
        con.execute("UPDATE workout_schedule SET scheduled_day=?,updated_at=CURRENT_TIMESTAMP WHERE workout_id=?",
                    (a["scheduled_day"],b["workout_id"]))
        con.execute(
            """INSERT INTO progression_events(user_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?)""",
            (user_id,a["workout_id"],"swap_workout_day",a["scheduled_day_name"],b["scheduled_day_name"],
             f"Swapped with {b['name']}"),
        )
    return {
        "workout_a":a,
        "workout_b":b,
        "a_new_day":b["scheduled_day_name"],
        "b_new_day":a["scheduled_day_name"],
    }

def set_workout_skipped(user_id: int, workout_id: int, skipped: bool, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    item=get_workout_schedule_item(user_id,workout_id,db_path)
    if item["status"] in {"active","completed"}:
        raise ValueError("Active or completed workouts cannot be skipped/restored")
    with session(db_path) as con:
        con.execute("UPDATE workout_schedule SET is_skipped=?,updated_at=CURRENT_TIMESTAMP WHERE workout_id=?",
                    (1 if skipped else 0,workout_id))
        con.execute(
            """INSERT INTO progression_events(user_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?)""",
            (user_id,workout_id,"skip_workout","active" if not skipped else "skipped",
             "skipped" if skipped else "active","Coach-approved schedule change"),
        )
    item["is_skipped"]=bool(skipped)
    return item



def get_time_settings(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        con.execute(
            """INSERT OR IGNORE INTO user_time_settings
               (user_id,timezone,utc_offset_minutes,default_workout_time,calendar_sync_enabled)
               VALUES (?, 'UTC', 0, '17:00', 1)""",(user_id,)
        )
        row=con.execute("SELECT * FROM user_time_settings WHERE user_id=?",(user_id,)).fetchone()
    result=dict(row)
    result["calendar_sync_enabled"]=bool(result["calendar_sync_enabled"])
    return result

def update_time_settings(user_id: int, timezone: str | None = None,
                         utc_offset_minutes: int | None = None,
                         default_workout_time: str | None = None,
                         calendar_sync_enabled: bool | None = None,
                         db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    get_time_settings(user_id,db_path)
    fields=[]; values=[]
    if timezone is not None:
        fields.append("timezone=?");values.append(str(timezone))
    if utc_offset_minutes is not None:
        fields.append("utc_offset_minutes=?");values.append(int(utc_offset_minutes))
    if default_workout_time is not None:
        if not __import__("re").match(r"^(?:[01]\d|2[0-3]):[0-5]\d$",str(default_workout_time)):
            raise ValueError("default_workout_time must be HH:MM")
        fields.append("default_workout_time=?");values.append(str(default_workout_time))
    if calendar_sync_enabled is not None:
        fields.append("calendar_sync_enabled=?");values.append(1 if calendar_sync_enabled else 0)
    if fields:
        values.append(user_id)
        with session(db_path) as con:
            con.execute(f"UPDATE user_time_settings SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE user_id=?",tuple(values))
            if default_workout_time is not None:
                con.execute(
                    """UPDATE workout_schedule SET scheduled_time=?
                       WHERE workout_id IN (
                         SELECT w.id FROM workouts w JOIN program_weeks pw ON pw.id=w.program_week_id
                         JOIN programs p ON p.id=pw.program_id WHERE p.user_id=?
                       )""",(str(default_workout_time),user_id)
                )
    return get_time_settings(user_id,db_path)

def get_calendar_connection(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with session(db_path) as con:
        row=con.execute("SELECT * FROM google_calendar_connections WHERE user_id=?",(user_id,)).fetchone()
    return dict(row) if row else None

def save_calendar_connection(user_id: int, access_token: str, refresh_token: str | None,
                             token_expires_at: str | None, scope: str | None,
                             google_email: str | None = None, calendar_id: str="primary",
                             db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        existing=con.execute("SELECT refresh_token FROM google_calendar_connections WHERE user_id=?",(user_id,)).fetchone()
        refresh=refresh_token or (existing["refresh_token"] if existing else None)
        con.execute(
            """INSERT INTO google_calendar_connections
               (user_id,calendar_id,access_token,refresh_token,token_expires_at,scope,google_email)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
                 calendar_id=excluded.calendar_id,access_token=excluded.access_token,
                 refresh_token=COALESCE(excluded.refresh_token,google_calendar_connections.refresh_token),
                 token_expires_at=excluded.token_expires_at,scope=excluded.scope,
                 google_email=COALESCE(excluded.google_email,google_calendar_connections.google_email),
                 updated_at=CURRENT_TIMESTAMP""",
            (user_id,calendar_id,access_token,refresh,token_expires_at,scope,google_email)
        )

def disconnect_calendar(user_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("DELETE FROM workout_calendar_links WHERE user_id=?",(user_id,))
        con.execute("DELETE FROM google_calendar_connections WHERE user_id=?",(user_id,))

def save_oauth_state(state: str, user_id: int, return_url: str | None, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("DELETE FROM calendar_oauth_states WHERE datetime(created_at)<datetime('now','-20 minutes')")
        con.execute("INSERT OR REPLACE INTO calendar_oauth_states(state,user_id,return_url) VALUES (?,?,?)",
                    (state,user_id,return_url))

def consume_oauth_state(state: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with session(db_path) as con:
        row=con.execute(
            "SELECT * FROM calendar_oauth_states WHERE state=? AND datetime(created_at)>=datetime('now','-20 minutes')",
            (state,)
        ).fetchone()
        con.execute("DELETE FROM calendar_oauth_states WHERE state=?",(state,))
    return dict(row) if row else None

def get_calendar_link(workout_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with session(db_path) as con:
        row=con.execute("SELECT * FROM workout_calendar_links WHERE workout_id=?",(workout_id,)).fetchone()
    return dict(row) if row else None

def upsert_calendar_link(user_id: int, workout_id: int, event_id: str,
                         calendar_id: str="primary", google_updated: str | None=None,
                         forge_signature: str | None=None, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute(
            """INSERT INTO workout_calendar_links
               (workout_id,user_id,google_event_id,google_calendar_id,last_google_updated,last_forge_signature)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(workout_id) DO UPDATE SET
                 google_event_id=excluded.google_event_id,google_calendar_id=excluded.google_calendar_id,
                 last_google_updated=excluded.last_google_updated,last_forge_signature=excluded.last_forge_signature,
                 last_synced_at=CURRENT_TIMESTAMP""",
            (workout_id,user_id,event_id,calendar_id,google_updated,forge_signature)
        )

def update_calendar_link_sync(workout_id: int, google_updated: str | None,
                              forge_signature: str | None, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute(
            """UPDATE workout_calendar_links SET last_google_updated=?,last_forge_signature=?,
               last_synced_at=CURRENT_TIMESTAMP WHERE workout_id=?""",
            (google_updated,forge_signature,workout_id)
        )

def list_calendar_links(user_id: int, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with session(db_path) as con:
        rows=con.execute("SELECT * FROM workout_calendar_links WHERE user_id=?",(user_id,)).fetchall()
    return [dict(x) for x in rows]

def set_workout_schedule_from_calendar(user_id: int, workout_id: int, target_day: int,
                                       scheduled_time: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    item=get_workout_schedule_item(user_id,workout_id,db_path)
    if item["status"] in {"active","completed"}:
        raise ValueError("Active or completed workouts cannot be moved by calendar sync")
    schedule=get_workout_schedule(user_id,db_path)
    conflict=next((x for x in schedule if int(x["workout_id"])!=int(workout_id)
                   and int(x["scheduled_day"])==int(target_day) and not x["is_skipped"]),None)
    if conflict:
        raise ValueError(f"{day_name(target_day)} already has {conflict['name']}")
    with session(db_path) as con:
        con.execute(
            """UPDATE workout_schedule SET scheduled_day=?,scheduled_time=?,updated_at=CURRENT_TIMESTAMP
               WHERE workout_id=?""",(int(target_day),str(scheduled_time),int(workout_id))
        )
        con.execute(
            """INSERT INTO progression_events(user_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?)""",
            (user_id,workout_id,"calendar_reschedule",
             f"{item['scheduled_day_name']} {item.get('scheduled_time','')}",
             f"{day_name(target_day)} {scheduled_time}",
             "Synced from Google Calendar")
        )
    return get_workout_schedule_item(user_id,workout_id,db_path)



def get_notification_settings(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        con.execute("INSERT OR IGNORE INTO notification_settings(user_id) VALUES (?)",(user_id,))
        row=con.execute("SELECT * FROM notification_settings WHERE user_id=?",(user_id,)).fetchone()
    out=dict(row)
    for k in ("workout_reminders","nutrition_reminders","calendar_conflict_alerts","morning_brief"): out[k]=bool(out[k])
    return out

def update_notification_settings(user_id: int, values: dict[str, Any], db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    get_notification_settings(user_id,db_path); fields=[]; args=[]
    for k,v in values.items():
        if k not in {"workout_reminders","nutrition_reminders","calendar_conflict_alerts","morning_brief","reminder_minutes_before"}: continue
        if k=="reminder_minutes_before": v=max(15,min(360,int(v)))
        else: v=1 if bool(v) else 0
        fields.append(f"{k}=?"); args.append(v)
    if fields:
        args.append(user_id)
        with session(db_path) as con: con.execute(f"UPDATE notification_settings SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE user_id=?",tuple(args))
    return get_notification_settings(user_id,db_path)

def dismiss_notification(user_id: int, key: str, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con: con.execute("INSERT OR REPLACE INTO dismissed_notifications(user_id,notification_key,dismissed_at) VALUES (?,?,CURRENT_TIMESTAMP)",(user_id,key))

def is_notification_dismissed(user_id: int, key: str, db_path=DEFAULT_DB_PATH) -> bool:
    with session(db_path) as con: return bool(con.execute("SELECT 1 FROM dismissed_notifications WHERE user_id=? AND notification_key=?",(user_id,key)).fetchone())

def get_nutrition_targets(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        con.execute(
            """INSERT OR IGNORE INTO nutrition_targets
               (user_id,calories,protein_g,carbs_g,fat_g)
               VALUES (?,2200,150,250,70)""",(user_id,)
        )
        row=con.execute("SELECT * FROM nutrition_targets WHERE user_id=?",(user_id,)).fetchone()
    return dict(row)

def update_nutrition_targets(user_id: int, calories: int, protein_g: int,
                             carbs_g: int, fat_g: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    calories=max(0,int(calories));protein_g=max(0,int(protein_g))
    carbs_g=max(0,int(carbs_g));fat_g=max(0,int(fat_g))
    with session(db_path) as con:
        con.execute(
            """INSERT INTO nutrition_targets(user_id,calories,protein_g,carbs_g,fat_g)
               VALUES (?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
                 calories=excluded.calories,protein_g=excluded.protein_g,
                 carbs_g=excluded.carbs_g,fat_g=excluded.fat_g,
                 updated_at=CURRENT_TIMESTAMP""",
            (user_id,calories,protein_g,carbs_g,fat_g)
        )
    return get_nutrition_targets(user_id,db_path)

def add_nutrition_entry(user_id: int, entry_date: str, meal_type: str,
                        food_name: str, calories: int, protein_g: float,
                        carbs_g: float, fat_g: float, source: str | None = None,
                        source_url: str | None = None,
                        db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    import datetime as _dt
    try:_dt.date.fromisoformat(entry_date)
    except Exception:raise ValueError("entry_date must be YYYY-MM-DD")
    food_name=(food_name or "").strip()
    if not food_name:raise ValueError("Food name is required")
    meal_type=(meal_type or "Meal").strip() or "Meal"
    with session(db_path) as con:
        cur=con.execute(
            """INSERT INTO nutrition_entries
               (user_id,entry_date,meal_type,food_name,calories,protein_g,carbs_g,fat_g,source,source_url)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (user_id,entry_date,meal_type,food_name,max(0,int(calories)),
             max(0,float(protein_g)),max(0,float(carbs_g)),max(0,float(fat_g)),
             source,source_url)
        )
        row=con.execute("SELECT * FROM nutrition_entries WHERE id=?",(cur.lastrowid,)).fetchone()
    result=dict(row)
    remember_nutrition_food(user_id,result["food_name"],result["calories"],result["protein_g"],result["carbs_g"],result["fat_g"],result.get("source"),result.get("source_url"),db_path)
    return result

def delete_nutrition_entry(user_id: int, entry_id: int, db_path=DEFAULT_DB_PATH) -> bool:
    with session(db_path) as con:
        cur=con.execute("DELETE FROM nutrition_entries WHERE id=? AND user_id=?",(entry_id,user_id))
        return cur.rowcount>0

def get_nutrition_day(user_id: int, entry_date: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    targets=get_nutrition_targets(user_id,db_path)
    with session(db_path) as con:
        rows=con.execute(
            """SELECT id,entry_date,meal_type,food_name,calories,protein_g,carbs_g,fat_g,source,source_url,created_at
               FROM nutrition_entries WHERE user_id=? AND entry_date=?
               ORDER BY created_at,id""",(user_id,entry_date)
        ).fetchall()
    entries=[dict(x) for x in rows]
    totals={
        "calories":sum(int(x["calories"]) for x in entries),
        "protein_g":round(sum(float(x["protein_g"]) for x in entries),1),
        "carbs_g":round(sum(float(x["carbs_g"]) for x in entries),1),
        "fat_g":round(sum(float(x["fat_g"]) for x in entries),1),
    }
    remaining={
        "calories":max(0,int(targets["calories"])-totals["calories"]),
        "protein_g":max(0,round(float(targets["protein_g"])-totals["protein_g"],1)),
        "carbs_g":max(0,round(float(targets["carbs_g"])-totals["carbs_g"],1)),
        "fat_g":max(0,round(float(targets["fat_g"])-totals["fat_g"],1)),
    }
    return {"date":entry_date,"targets":targets,"totals":totals,"remaining":remaining,"entries":entries}

def _normalize_food_name(name: str) -> str:
    import re as _re
    value=(name or "").lower()
    value=_re.sub(r"\s+—\s+.*$","",value)
    value=_re.sub(r"[^a-z0-9]+"," ",value)
    return " ".join(value.split()).strip()

def remember_nutrition_food(user_id: int, food_name: str, calories: int,
                            protein_g: float, carbs_g: float, fat_g: float,
                            source: str | None=None, source_url: str | None=None,
                            db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    normalized=_normalize_food_name(food_name)
    if not normalized:
        raise ValueError("Food name is required")
    with session(db_path) as con:
        con.execute(
            """INSERT INTO nutrition_saved_foods
               (user_id,normalized_name,food_name,calories,protein_g,carbs_g,fat_g,source,source_url,use_count)
               VALUES (?,?,?,?,?,?,?,?,?,1)
               ON CONFLICT(user_id,normalized_name) DO UPDATE SET
                 food_name=excluded.food_name,calories=excluded.calories,
                 protein_g=excluded.protein_g,carbs_g=excluded.carbs_g,fat_g=excluded.fat_g,
                 source=COALESCE(excluded.source,nutrition_saved_foods.source),
                 source_url=COALESCE(excluded.source_url,nutrition_saved_foods.source_url),
                 use_count=nutrition_saved_foods.use_count+1,
                 last_used_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP""",
            (user_id,normalized,food_name,int(calories),float(protein_g),float(carbs_g),float(fat_g),source,source_url)
        )
        row=con.execute("SELECT * FROM nutrition_saved_foods WHERE user_id=? AND normalized_name=?",(user_id,normalized)).fetchone()
    result=dict(row);result["is_favorite"]=bool(result["is_favorite"]);return result

def get_saved_nutrition_foods(user_id: int, limit: int=12, favorites_only: bool=False,
                              db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    limit=max(1,min(int(limit),100))
    with session(db_path) as con:
        sql="SELECT * FROM nutrition_saved_foods WHERE user_id=?";args=[user_id]
        if favorites_only: sql+=" AND is_favorite=1"
        sql+=" ORDER BY is_favorite DESC, datetime(last_used_at) DESC, use_count DESC LIMIT ?";args.append(limit)
        rows=con.execute(sql,tuple(args)).fetchall()
    out=[]
    for row in rows:
        x=dict(row);x["is_favorite"]=bool(x["is_favorite"]);out.append(x)
    return out

def set_saved_food_favorite(user_id: int, saved_food_id: int, favorite: bool, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        cur=con.execute("UPDATE nutrition_saved_foods SET is_favorite=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",(1 if favorite else 0,int(saved_food_id),user_id))
        if cur.rowcount<1: raise ValueError("Saved food not found")
        row=con.execute("SELECT * FROM nutrition_saved_foods WHERE id=?",(int(saved_food_id),)).fetchone()
    x=dict(row);x["is_favorite"]=bool(x["is_favorite"]);return x

def find_saved_food_match(user_id: int, text: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any] | None:
    query=_normalize_food_name(text); qtokens=set(query.split())
    if not qtokens:return None
    stop={"log","add","track","record","enter","save","my","a","an","the","for","breakfast","lunch","dinner","snack","i","had","ate","drank"}
    qtokens={x for x in qtokens if x not in stop}
    best=None;best_score=0.0
    for food in get_saved_nutrition_foods(user_id,100,False,db_path):
        fn=_normalize_food_name(food["food_name"]);ftokens=set(fn.split())
        if not ftokens:continue
        score=len(qtokens & ftokens)/max(1,len(ftokens))
        if fn and fn in query:score=max(score,1.0)
        if score>best_score:best_score=score;best=food
    return best if best_score>=0.72 else None

def update_nutrition_entry(user_id: int, entry_id: int, meal_type: str, food_name: str,
                           calories: int, protein_g: float, carbs_g: float, fat_g: float,
                           source: str | None=None, source_url: str | None=None,
                           db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    food_name=(food_name or "").strip()
    if not food_name:raise ValueError("Food name is required")
    with session(db_path) as con:
        cur=con.execute("""UPDATE nutrition_entries SET meal_type=?,food_name=?,calories=?,protein_g=?,carbs_g=?,fat_g=?,source=?,source_url=? WHERE id=? AND user_id=?""",
            ((meal_type or "Meal").strip() or "Meal",food_name,max(0,int(calories)),max(0,float(protein_g)),max(0,float(carbs_g)),max(0,float(fat_g)),source,source_url,int(entry_id),user_id))
        if cur.rowcount<1:raise ValueError("Nutrition entry not found")
        row=con.execute("SELECT * FROM nutrition_entries WHERE id=?",(int(entry_id),)).fetchone()
    remember_nutrition_food(user_id,food_name,row["calories"],row["protein_g"],row["carbs_g"],row["fat_g"],row["source"],row["source_url"],db_path)
    return dict(row)

def quick_log_saved_food(user_id: int, saved_food_id: int, entry_date: str, meal_type: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        row=con.execute("SELECT * FROM nutrition_saved_foods WHERE id=? AND user_id=?",(int(saved_food_id),user_id)).fetchone()
    if not row:raise ValueError("Saved food not found")
    food=dict(row)
    return add_nutrition_entry(user_id,entry_date,meal_type,food["food_name"],food["calories"],food["protein_g"],food["carbs_g"],food["fat_g"],food.get("source"),food.get("source_url"),db_path)



def upsert_body_metrics(user_id: int, entry_date: str, values: dict[str, Any],
                        db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    allowed=("weight_lb","body_fat_pct","waist_in","chest_in","hips_in","arm_in","thigh_in","notes")
    clean={}
    for key in allowed:
        value=values.get(key)
        if key=="notes":
            clean[key]=(str(value).strip()[:500] if value is not None else None)
        elif value in (None,""):
            clean[key]=None
        else:
            num=float(value)
            if num<0: raise ValueError(f"{key} cannot be negative")
            clean[key]=num
    if not any(clean.get(k) is not None for k in allowed):
        raise ValueError("Enter at least one body metric")
    with session(db_path) as con:
        con.execute(
            """INSERT INTO body_metrics
               (user_id,entry_date,weight_lb,body_fat_pct,waist_in,chest_in,hips_in,arm_in,thigh_in,notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(user_id,entry_date) DO UPDATE SET
                 weight_lb=excluded.weight_lb,body_fat_pct=excluded.body_fat_pct,
                 waist_in=excluded.waist_in,chest_in=excluded.chest_in,hips_in=excluded.hips_in,
                 arm_in=excluded.arm_in,thigh_in=excluded.thigh_in,notes=excluded.notes,
                 updated_at=CURRENT_TIMESTAMP""",
            (user_id,entry_date,clean["weight_lb"],clean["body_fat_pct"],clean["waist_in"],
             clean["chest_in"],clean["hips_in"],clean["arm_in"],clean["thigh_in"],clean["notes"])
        )
        row=con.execute("SELECT * FROM body_metrics WHERE user_id=? AND entry_date=?",(user_id,entry_date)).fetchone()
    return dict(row)

def delete_body_metrics(user_id: int, entry_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        cur=con.execute("DELETE FROM body_metrics WHERE id=? AND user_id=?",(int(entry_id),user_id))
        if cur.rowcount<1: raise ValueError("Body metric entry not found")

def get_body_metrics(user_id: int, limit: int=180, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    limit=max(1,min(int(limit),500))
    with session(db_path) as con:
        rows=con.execute(
            """SELECT * FROM body_metrics WHERE user_id=?
               ORDER BY date(entry_date) DESC,id DESC LIMIT ?""",(user_id,limit)
        ).fetchall()
    return [dict(x) for x in rows]

def get_body_metrics_summary(user_id: int, range_days: int | None=90,
                             db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    rows=get_body_metrics(user_id,500,db_path)
    if range_days is not None:
        from datetime import date as _date, timedelta as _td
        cutoff=_date.today()-_td(days=int(range_days))
        rows=[x for x in rows if _date.fromisoformat(x["entry_date"])>=cutoff]
    rows=sorted(rows,key=lambda x:x["entry_date"])
    def trend(field: str):
        pts=[{"date":x["entry_date"],"value":float(x[field])} for x in rows if x.get(field) is not None]
        if not pts:return {"points":[],"current":None,"start":None,"change":None,"change_percent":None}
        start=float(pts[0]["value"]);current=float(pts[-1]["value"]);change=current-start
        pct=(change/start*100) if start else None
        return {"points":pts,"current":round(current,2),"start":round(start,2),
                "change":round(change,2),"change_percent":round(pct,1) if pct is not None else None}
    metrics={k:trend(k) for k in ("weight_lb","body_fat_pct","waist_in","chest_in","hips_in","arm_in","thigh_in")}
    return {"entries":list(reversed(rows)),"metrics":metrics,"range_days":range_days}

def get_progress_intelligence(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    """Combine adherence, strength, workload, effort, recovery, and nutrition consistency.

    This intentionally uses only data Forge already records. Nutrition consistency is
    compared with the user's CURRENT targets because historical target revisions are
    not versioned yet.
    """
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz

    now=_dt.now(_tz.utc)
    cutoff30=(now-_td(days=30)).date()
    cutoff14=(now-_td(days=14)).date()

    history=get_workout_history(user_id,80,db_path)
    recent30=[]
    for h in history:
        raw=h.get("completed_at") or h.get("started_at")
        try: day=_dt.fromisoformat(str(raw).replace("Z","+00:00")).date()
        except Exception: continue
        if day>=cutoff30: recent30.append(h)

    completed30=[x for x in recent30 if x.get("status")=="completed"]
    skipped30=[x for x in recent30 if x.get("status")=="skipped"]
    considered=len(completed30)+len(skipped30)
    adherence=round(len(completed30)/considered*100,1) if considered else None

    completed_all=[x for x in history if x.get("status")=="completed"]
    recent4=completed_all[:4]
    prior4=completed_all[4:8]
    avg_recent_volume=(sum(float(x.get("total_volume") or 0) for x in recent4)/len(recent4)) if recent4 else 0.0
    avg_prior_volume=(sum(float(x.get("total_volume") or 0) for x in prior4)/len(prior4)) if prior4 else 0.0
    volume_change=((avg_recent_volume-avg_prior_volume)/avg_prior_volume*100.0) if avg_prior_volume>0 else None

    rpes=[]
    for workout in recent4:
        for ex in workout.get("exercises") or []:
            for st in ex.get("sets") or []:
                if not st.get("skipped") and st.get("rpe") is not None:
                    try:rpes.append(float(st["rpe"]))
                    except Exception:pass
    avg_rpe=round(sum(rpes)/len(rpes),1) if rpes else None

    strength30=get_strength_trend(user_id,None,30,db_path)
    strength90=get_strength_trend(user_id,None,90,db_path)
    pts30=strength30.get("points") or []
    recent_strength_change=None
    if len(pts30)>=2:
        recent_strength_change=round(float(pts30[-1]["value"])-float(pts30[0]["value"]),1)

    state=get_training_state(user_id,db_path)
    fatigue=round(float(state.get("fatigue_score") or 0),1)

    targets=get_nutrition_targets(user_id,db_path)
    with session(db_path) as con:
        rows=con.execute(
            """SELECT entry_date,SUM(calories) calories,SUM(protein_g) protein_g
               FROM nutrition_entries
               WHERE user_id=? AND date(entry_date)>=date(?)
               GROUP BY entry_date ORDER BY entry_date""",
            (user_id,cutoff14.isoformat())
        ).fetchall()
    logged_days=len(rows)
    calorie_hits=0;protein_hits=0
    for row in rows:
        cal=float(row["calories"] or 0); protein=float(row["protein_g"] or 0)
        if float(targets["calories"])*.80 <= cal <= float(targets["calories"])*1.20: calorie_hits+=1
        if protein >= float(targets["protein_g"])*.80: protein_hits+=1
    nutrition_consistency=round(((calorie_hits+protein_hits)/(logged_days*2))*100,1) if logged_days else None

    body=get_body_metrics_summary(user_id,30,db_path)
    weight_trend=body["metrics"]["weight_lb"]
    weight_change=weight_trend.get("change")
    weight_change_pct=weight_trend.get("change_percent")

    signals=[]
    recommendations=[]

    if adherence is None:
        signals.append({"type":"adherence","status":"insufficient","label":"Workout adherence","value":"Not enough data"})
    elif adherence>=85:
        signals.append({"type":"adherence","status":"positive","label":"Workout adherence","value":f"{adherence:g}%"})
    elif adherence>=65:
        signals.append({"type":"adherence","status":"watch","label":"Workout adherence","value":f"{adherence:g}%"})
        recommendations.append("Improve weekly consistency before increasing training complexity.")
    else:
        signals.append({"type":"adherence","status":"negative","label":"Workout adherence","value":f"{adherence:g}%"})
        recommendations.append("Focus on completing the planned sessions consistently before adding more volume.")

    if recent_strength_change is None:
        signals.append({"type":"strength","status":"insufficient","label":"30-day strength trend","value":"Not enough data"})
    elif recent_strength_change>2:
        signals.append({"type":"strength","status":"positive","label":"30-day strength trend","value":f"+{recent_strength_change:g}%"})
    elif recent_strength_change>=-1:
        signals.append({"type":"strength","status":"watch","label":"30-day strength trend","value":f"{recent_strength_change:+g}%"})
        if len(pts30)>=3: recommendations.append("Strength has been mostly flat recently. Review exercise progression, recovery, and adherence.")
    else:
        signals.append({"type":"strength","status":"negative","label":"30-day strength trend","value":f"{recent_strength_change:+g}%"})
        recommendations.append("Recent estimated strength has declined. Avoid automatically adding volume until recovery and execution are reviewed.")

    if volume_change is not None:
        status="positive" if -5<=volume_change<=20 else "watch"
        signals.append({"type":"volume","status":status,"label":"Recent workload","value":f"{volume_change:+.1f}% vs prior 4"})
        if volume_change>25 and (avg_rpe is not None and avg_rpe>=8.5):
            recommendations.append("Workload and effort both rose quickly. Consider holding volume steady rather than increasing again.")

    profile=get_profile(user_id,db_path) or {}
    goal=profile.get("goal","general_fitness")
    if weight_trend.get("current") is not None and len(weight_trend.get("points") or [])>=2:
        direction="up" if (weight_change or 0)>0 else "down" if (weight_change or 0)<0 else "flat"
        desired=None
        if goal=="lose_fat": desired="down"
        elif goal=="build_muscle": desired="up"
        body_status="positive" if desired and direction==desired else "watch" if desired and direction=="flat" else "negative" if desired else "watch"
        signals.append({"type":"bodyweight","status":body_status,"label":"30-day bodyweight trend",
                        "value":f"{weight_change:+.1f} lb ({weight_change_pct:+.1f}%)"})
        if desired and direction not in {desired,"flat"}:
            recommendations.append("Your recent bodyweight direction does not match your current training goal. Review intake consistency and the pace of change before adjusting training.")
    else:
        signals.append({"type":"bodyweight","status":"insufficient","label":"Bodyweight trend","value":"Not enough weigh-ins"})

    recovery_status="positive"
    recovery_text=f"Fatigue {fatigue:g}/10"
    if fatigue>=7 or (avg_rpe is not None and avg_rpe>=9):
        recovery_status="negative"
        recommendations.append("Recovery indicators are high. A lighter session or recovery week may be more productive than pushing harder.")
    elif fatigue>=5 or (avg_rpe is not None and avg_rpe>=8.3):
        recovery_status="watch"
        recommendations.append("Recovery is becoming a constraint. Watch sleep, soreness, and session difficulty before progressing load.")
    signals.append({"type":"recovery","status":recovery_status,"label":"Recovery pressure",
                    "value":recovery_text + (f" • avg effort {avg_rpe:g}/10" if avg_rpe is not None else "")})

    if nutrition_consistency is not None:
        ns="positive" if nutrition_consistency>=80 else "watch" if nutrition_consistency>=55 else "negative"
        signals.append({"type":"nutrition","status":ns,"label":"Nutrition consistency",
                        "value":f"{nutrition_consistency:g}% across {logged_days} logged days"})
        if nutrition_consistency<60:
            recommendations.append("Nutrition logging/target consistency is low enough that it may be masking a training or recovery problem.")
    else:
        signals.append({"type":"nutrition","status":"insufficient","label":"Nutrition consistency","value":"No recent nutrition data"})

    plateau=bool(len(pts30)>=3 and recent_strength_change is not None and -1<=recent_strength_change<=1.5)
    recovery_needed=bool(fatigue>=7 or (avg_rpe is not None and avg_rpe>=9))
    declining=bool(recent_strength_change is not None and recent_strength_change<-1)

    if recovery_needed:
        status="recovery_needed"; headline="Recovery may be limiting progress"
    elif declining:
        status="declining"; headline="Recent strength is trending down"
    elif plateau:
        status="plateau"; headline="Progress has flattened recently"
    elif recent_strength_change is not None and recent_strength_change>2 and (adherence is None or adherence>=70):
        status="progressing"; headline="Training is moving in the right direction"
    elif considered<3 and len(pts30)<2:
        status="insufficient_data"; headline="Forge needs more completed training data"
    else:
        status="steady"; headline="Progress is steady"

    components=[]
    if adherence is not None:components.append(min(100,max(0,adherence)))
    if recent_strength_change is not None:components.append(min(100,max(0,50+recent_strength_change*5)))
    components.append(min(100,max(0,100-fatigue*8)))
    if nutrition_consistency is not None:components.append(nutrition_consistency)
    score=round(sum(components)/len(components)) if components else None

    if not recommendations:
        recommendations.append("Keep the current plan consistent and continue logging sets so Forge can detect meaningful changes.")

    return {
        "status":status,"headline":headline,"score":score,
        "signals":signals,"recommendations":recommendations[:4],
        "metrics":{
            "workouts_completed_30d":len(completed30),
            "workouts_skipped_30d":len(skipped30),
            "adherence_percent":adherence,
            "strength_change_30d_percent":recent_strength_change,
            "strength_all_time_percent":strength90.get("summary",{}).get("change_percent"),
            "recent_volume_change_percent":round(volume_change,1) if volume_change is not None else None,
            "recent_average_rpe":avg_rpe,
            "fatigue_score":fatigue,
            "nutrition_consistency_percent":nutrition_consistency,
            "nutrition_logged_days_14d":logged_days,
            "weight_current_lb":weight_trend.get("current"),
            "weight_change_30d_lb":weight_change,
            "weight_change_30d_percent":weight_change_pct,
        },
        "plateau_detected":plateau,
        "data_notes":[
            "Strength uses Forge's estimated-strength trend from logged weighted sets.",
            "Nutrition consistency uses the current calorie/protein targets because historical target changes are not versioned yet."
        ]
    }

def get_strength_trend(user_id: int, exercise_id: int | None = None,
                       days: int | None = 90, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    """Return chart-ready strength progress data from recorded sets.

    Exercise mode:
      - displays estimated 1RM in lb.
      - percentage change is relative to that exercise's first-ever valid logged set.

    Overall mode:
      - every exercise gets a permanent first-ever estimated-1RM baseline.
      - each later performance becomes percentage change from that baseline.
      - the daily overall value is the average percentage change across exercises
        represented on that date.
      - date range controls visibility only; it never resets the baseline.
    """
    with session(db_path) as con:
        # Always load ALL historical performances first so baselines never change
        # when the UI switches between 30D / 90D / 1Y / ALL.
        rows=con.execute(
            """
            SELECT ep.exercise_id,e.name AS exercise_name,ep.weight,ep.reps_json,
                   ep.recorded_at,ep.skipped
            FROM exercise_performance ep
            JOIN exercises e ON e.id=ep.exercise_id
            JOIN workout_sessions ws ON ws.id=ep.session_id
            JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND ep.skipped=0
            ORDER BY datetime(ep.recorded_at),ep.id
            """,
            (user_id,),
        ).fetchall()

        ex_rows=con.execute(
            """SELECT DISTINCT e.id,e.name
               FROM exercise_performance ep
               JOIN exercises e ON e.id=ep.exercise_id
               JOIN workout_sessions ws ON ws.id=ep.session_id
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=? AND ep.skipped=0
               ORDER BY e.name""",
            (user_id,),
        ).fetchall()

    exercises=[{"exercise_id":int(x["id"]),"name":x["name"]} for x in ex_rows]

    parsed=[]
    for row in rows:
        try:
            reps_list=json.loads(row["reps_json"]) if row["reps_json"] else []
        except Exception:
            reps_list=[]
        weight=float(row["weight"] or 0)
        for reps in reps_list:
            reps=int(reps or 0)
            if weight<=0 or reps<=0:
                continue
            e1rm=weight*(1+reps/30.0)
            parsed.append({
                "exercise_id":int(row["exercise_id"]),
                "exercise_name":row["exercise_name"],
                "recorded_at":row["recorded_at"],
                "date":str(row["recorded_at"])[:10],
                "weight":round(weight,2),
                "reps":reps,
                "e1rm":round(e1rm,2),
            })

    # Permanent first-ever e1RM baseline for every exercise.
    baseline_by_ex={}
    for x in parsed:
        if x["exercise_id"] not in baseline_by_ex:
            baseline_by_ex[x["exercise_id"]]=x["e1rm"]

    # Visibility cutoff only. Baselines above remain all-time.
    cutoff_date=None
    if days is not None:
        cutoff_date=(__import__("datetime").datetime.utcnow()-__import__("datetime").timedelta(days=int(days))).date()

    visible=[
        x for x in parsed
        if cutoff_date is None or __import__("datetime").date.fromisoformat(x["date"])>=cutoff_date
    ]

    if exercise_id is not None:
        all_ex=[x for x in parsed if x["exercise_id"]==int(exercise_id)]
        filtered=[x for x in visible if x["exercise_id"]==int(exercise_id)]
        baseline=baseline_by_ex.get(int(exercise_id),0)

        # One best estimated-1RM point per date.
        by_date={}
        for x in filtered:
            cur=by_date.get(x["date"])
            if cur is None or x["e1rm"]>cur["e1rm"]:
                by_date[x["date"]]=x

        points=[]
        for x in sorted(by_date.values(),key=lambda z:z["date"]):
            progress_pct=((x["e1rm"]-baseline)/baseline*100.0) if baseline else 0.0
            points.append({
                "date":x["date"],
                "value":x["e1rm"],
                "progress_percent":round(progress_pct,1),
                "weight":x["weight"],
                "reps":x["reps"],
                "exercise_name":x["exercise_name"],
                "label":f"{x['weight']} lb × {x['reps']}",
            })

        # Summary current/best is based on all time, while visible chart uses selected range.
        all_best=max((x["e1rm"] for x in all_ex),default=0)
        all_current=all_ex[-1]["e1rm"] if all_ex else 0
        overall_change=((all_current-baseline)/baseline*100.0) if baseline else 0.0

        mode="exercise"
        unit="lb"
        title=next((x["name"] for x in exercises if x["exercise_id"]==int(exercise_id)),"Exercise")
        summary={
            "current":round(all_current,2),
            "best":round(all_best,2),
            "change_percent":round(overall_change,1),
            "data_points":len(points),
            "baseline":round(baseline,2),
        }

    else:
        # For each date and exercise, keep the strongest normalized performance.
        daily={}
        for x in visible:
            baseline=baseline_by_ex.get(x["exercise_id"],0)
            if baseline<=0:
                continue
            pct=((x["e1rm"]-baseline)/baseline)*100.0
            key=(x["date"],x["exercise_id"])
            cur=daily.get(key)
            if cur is None or pct>cur["progress_percent"]:
                daily[key]={
                    "date":x["date"],
                    "exercise_id":x["exercise_id"],
                    "progress_percent":pct,
                }

        by_date={}
        for item in daily.values():
            by_date.setdefault(item["date"],[]).append(item["progress_percent"])

        points=[
            {
                "date":date,
                "value":round(sum(vals)/len(vals),2),
                "progress_percent":round(sum(vals)/len(vals),1),
                "label":f"{round(sum(vals)/len(vals),1):+g}% strength progress",
            }
            for date,vals in sorted(by_date.items())
        ]

        # Calculate all-time current progress using each exercise's latest performance.
        latest_by_ex={}
        best_pct_by_ex={}
        for x in parsed:
            baseline=baseline_by_ex.get(x["exercise_id"],0)
            if baseline<=0:
                continue
            pct=((x["e1rm"]-baseline)/baseline)*100.0
            latest_by_ex[x["exercise_id"]]=pct
            best_pct_by_ex[x["exercise_id"]]=max(best_pct_by_ex.get(x["exercise_id"],pct),pct)

        current=(sum(latest_by_ex.values())/len(latest_by_ex)) if latest_by_ex else 0.0
        best=(sum(best_pct_by_ex.values())/len(best_pct_by_ex)) if best_pct_by_ex else 0.0

        mode="overall"
        unit="percent"
        title="Overall Strength Progress"
        summary={
            "current":round(current,1),
            "best":round(best,1),
            "change_percent":round(current,1),
            "data_points":len(points),
            "baseline":0.0,
        }

    return {
        "mode":mode,
        "title":title,
        "unit":unit,
        "exercise_id":exercise_id,
        "points":points,
        "exercises":exercises,
        "summary":summary,
        "baseline_type":"all_time_first_valid_set",
    }



EQUIPMENT_CATALOG = [
    # Free weights
    {"key":"dumbbells","name":"Dumbbells","category":"Free Weights","icon":"🏋️","detail_schema":{"max_weight_lb":"number","adjustable":"boolean"}},
    {"key":"barbell","name":"Olympic Barbell","category":"Free Weights","icon":"🏋️","detail_schema":{"bar_weight_lb":"number"}},
    {"key":"ez_curl_bar","name":"EZ Curl Bar","category":"Free Weights","icon":"〰️","detail_schema":{"bar_weight_lb":"number"}},
    {"key":"trap_bar","name":"Trap / Hex Bar","category":"Free Weights","icon":"⬡","detail_schema":{"bar_weight_lb":"number"}},
    {"key":"weight_plates","name":"Weight Plates","category":"Free Weights","icon":"⚫","detail_schema":{"total_weight_lb":"number","smallest_plate_lb":"number"}},
    {"key":"kettlebells","name":"Kettlebells","category":"Free Weights","icon":"🔩","detail_schema":{"max_weight_lb":"number"}},
    {"key":"medicine_ball","name":"Medicine Ball","category":"Free Weights","icon":"⚽","detail_schema":{"max_weight_lb":"number"}},

    # Benches / racks / stations
    {"key":"bench","name":"Flat Bench","category":"Benches & Racks","icon":"🪑","detail_schema":{}},
    {"key":"adjustable_bench","name":"Adjustable Bench","category":"Benches & Racks","icon":"🪑","detail_schema":{"incline":"boolean","decline":"boolean"}},
    {"key":"squat_rack","name":"Squat Rack","category":"Benches & Racks","icon":"🏗️","detail_schema":{"safeties":"boolean"}},
    {"key":"power_rack","name":"Power Rack","category":"Benches & Racks","icon":"🏗️","detail_schema":{"pull_up_bar":"boolean","safeties":"boolean"}},
    {"key":"preacher_bench","name":"Preacher Curl Bench","category":"Benches & Racks","icon":"🪑","detail_schema":{}},
    {"key":"dip_station","name":"Dip Station","category":"Benches & Racks","icon":"↕️","detail_schema":{}},
    {"key":"pull_up_bar","name":"Pull-Up Bar","category":"Benches & Racks","icon":"➖","detail_schema":{}},

    # Cable / selectorized machines
    {"key":"cable_machine","name":"Cable Machine / Functional Trainer","category":"Cable & Machines","icon":"🧵","detail_schema":{"dual_stack":"boolean","max_stack_lb":"number"}},
    {"key":"lat_pulldown","name":"Lat Pulldown Machine","category":"Cable & Machines","icon":"⬇️","detail_schema":{"max_stack_lb":"number"}},
    {"key":"seated_row_machine","name":"Seated Row Machine","category":"Cable & Machines","icon":"↔️","detail_schema":{"max_stack_lb":"number"}},
    {"key":"chest_press_machine","name":"Chest Press Machine","category":"Cable & Machines","icon":"➡️","detail_schema":{"max_stack_lb":"number"}},
    {"key":"shoulder_press_machine","name":"Shoulder Press Machine","category":"Cable & Machines","icon":"⬆️","detail_schema":{"max_stack_lb":"number"}},
    {"key":"leg_press_machine","name":"Leg Press Machine","category":"Cable & Machines","icon":"🦵","detail_schema":{"plate_loaded":"boolean"}},
    {"key":"leg_extension_machine","name":"Leg Extension Machine","category":"Cable & Machines","icon":"🦵","detail_schema":{"max_stack_lb":"number"}},
    {"key":"leg_curl_machine","name":"Leg Curl Machine","category":"Cable & Machines","icon":"🦵","detail_schema":{"max_stack_lb":"number"}},
    {"key":"pec_deck","name":"Pec Deck / Rear Delt Machine","category":"Cable & Machines","icon":"🪽","detail_schema":{"max_stack_lb":"number"}},
    {"key":"calf_raise_machine","name":"Calf Raise Machine","category":"Cable & Machines","icon":"🦶","detail_schema":{}},
    {"key":"smith_machine","name":"Smith Machine","category":"Cable & Machines","icon":"▥","detail_schema":{"counterbalanced":"boolean"}},
    {"key":"machine","name":"Other Strength Machines","category":"Cable & Machines","icon":"⚙️","detail_schema":{}},

    # Cable attachments / accessories
    {"key":"rope_attachment","name":"Rope Attachment","category":"Attachments & Accessories","icon":"🪢","detail_schema":{}},
    {"key":"straight_bar_attachment","name":"Straight-Bar Cable Attachment","category":"Attachments & Accessories","icon":"➖","detail_schema":{}},
    {"key":"lat_bar_attachment","name":"Lat Bar Attachment","category":"Attachments & Accessories","icon":"〰️","detail_schema":{}},
    {"key":"ankle_strap","name":"Ankle Strap","category":"Attachments & Accessories","icon":"🦶","detail_schema":{}},
    {"key":"bands","name":"Resistance Bands","category":"Attachments & Accessories","icon":"➰","detail_schema":{"light":"boolean","medium":"boolean","heavy":"boolean"}},
    {"key":"ab_wheel","name":"Ab Wheel","category":"Attachments & Accessories","icon":"⭕","detail_schema":{}},
    {"key":"foam_roller","name":"Foam Roller","category":"Attachments & Accessories","icon":"🧻","detail_schema":{}},
    {"key":"yoga_mat","name":"Exercise / Yoga Mat","category":"Attachments & Accessories","icon":"▭","detail_schema":{}},
    {"key":"stability_ball","name":"Stability Ball","category":"Attachments & Accessories","icon":"⚪","detail_schema":{}},
    {"key":"landmine_attachment","name":"Landmine Attachment","category":"Attachments & Accessories","icon":"📍","detail_schema":{}},

    # Bodyweight
    {"key":"bodyweight","name":"Bodyweight / Floor Space","category":"Bodyweight","icon":"🧍","detail_schema":{}},
    {"key":"rings","name":"Gymnastic Rings","category":"Bodyweight","icon":"⭕","detail_schema":{}},
    {"key":"suspension_trainer","name":"Suspension Trainer / TRX","category":"Bodyweight","icon":"🔻","detail_schema":{}},

    # Cardio
    {"key":"treadmill","name":"Treadmill","category":"Cardio","icon":"🏃","detail_schema":{"max_speed_mph":"number","incline":"boolean"}},
    {"key":"bike","name":"Stationary Bike","category":"Cardio","icon":"🚲","detail_schema":{}},
    {"key":"rowing_machine","name":"Rowing Machine","category":"Cardio","icon":"🚣","detail_schema":{}},
    {"key":"elliptical","name":"Elliptical","category":"Cardio","icon":"🏃","detail_schema":{}},
    {"key":"stair_climber","name":"Stair Climber","category":"Cardio","icon":"🪜","detail_schema":{}},
    {"key":"jump_rope","name":"Jump Rope","category":"Cardio","icon":"➰","detail_schema":{}},
    {"key":"sled","name":"Push / Pull Sled","category":"Cardio","icon":"🛷","detail_schema":{}},
    {"key":'safety_squat_bar',"name":'Safety Squat Bar',"category":'Specialty Bars',"icon":'🏋️',"detail_schema":{'bar_weight_lb': 'number'}},
    {"key":'swiss_bar',"name":'Swiss / Multi-Grip Bar',"category":'Specialty Bars',"icon":'🏋️',"detail_schema":{'bar_weight_lb': 'number'}},
    {"key":'cambered_bar',"name":'Cambered Bar',"category":'Specialty Bars',"icon":'🏋️',"detail_schema":{'bar_weight_lb': 'number'}},
    {"key":'axle_bar',"name":'Axle / Fat Bar',"category":'Specialty Bars',"icon":'🏋️',"detail_schema":{'bar_weight_lb': 'number'}},
    {"key":'fixed_barbells',"name":'Fixed Barbells',"category":'Free Weights',"icon":'🏋️',"detail_schema":{'max_weight_lb': 'number'}},
    {"key":'sandbag',"name":'Training Sandbag',"category":'Free Weights',"icon":'🏋️',"detail_schema":{'max_weight_lb': 'number'}},
    {"key":'weighted_vest',"name":'Weighted Vest',"category":'Free Weights',"icon":'🏋️',"detail_schema":{'max_weight_lb': 'number'}},
    {"key":'clubs_maces',"name":'Clubs / Maces',"category":'Free Weights',"icon":'🏋️',"detail_schema":{'max_weight_lb': 'number'}},
    {"key":'deadlift_platform',"name":'Deadlift / Lifting Platform',"category":'Benches & Racks',"icon":'🏗️',"detail_schema":{}},
    {"key":'half_rack',"name":'Half Rack',"category":'Benches & Racks',"icon":'🏗️',"detail_schema":{'safeties': 'boolean', 'pull_up_bar': 'boolean'}},
    {"key":'wall_rack',"name":'Wall-Mounted Rack',"category":'Benches & Racks',"icon":'🏗️',"detail_schema":{'safeties': 'boolean'}},
    {"key":'glute_ham_developer',"name":'Glute Ham Developer (GHD)',"category":'Benches & Racks',"icon":'🏗️',"detail_schema":{}},
    {"key":'roman_chair',"name":'Roman Chair / Back Extension Bench',"category":'Benches & Racks',"icon":'🏗️',"detail_schema":{}},
    {"key":'hyperextension_bench',"name":'45° Hyperextension Bench',"category":'Benches & Racks',"icon":'🏗️',"detail_schema":{}},
    {"key":'decline_bench',"name":'Decline / Ab Bench',"category":'Benches & Racks',"icon":'🏗️',"detail_schema":{}},
    {"key":'hack_squat_machine',"name":'Hack Squat Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'plate_loaded': 'boolean'}},
    {"key":'pendulum_squat',"name":'Pendulum Squat Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'plate_loaded': 'boolean'}},
    {"key":'belt_squat_machine',"name":'Belt Squat Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'plate_loaded': 'boolean'}},
    {"key":'v_squat_machine',"name":'V-Squat / Leverage Squat',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'plate_loaded': 'boolean'}},
    {"key":'hip_thrust_machine',"name":'Hip Thrust / Glute Drive Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'hip_abductor_machine',"name":'Hip Abductor Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'hip_adductor_machine',"name":'Hip Adductor Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'standing_leg_curl',"name":'Standing Leg Curl Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'lying_leg_curl',"name":'Lying Leg Curl Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'seated_leg_curl',"name":'Seated Leg Curl Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'donkey_calf_machine',"name":'Donkey Calf Raise Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{}},
    {"key":'tibialis_machine',"name":'Tibialis Raise Machine',"category":'Lower Body Machines',"icon":'🦵',"detail_schema":{}},
    {"key":'incline_press_machine',"name":'Incline Chest Press Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'decline_press_machine',"name":'Decline Chest Press Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'chest_supported_row_machine',"name":'Chest-Supported Row Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'high_row_machine',"name":'High Row Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'pullover_machine',"name":'Pullover Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'lateral_raise_machine',"name":'Lateral Raise Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'rear_delt_machine',"name":'Rear Delt Fly Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'biceps_curl_machine',"name":'Biceps Curl Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'triceps_extension_machine',"name":'Triceps Extension Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_stack_lb': 'number'}},
    {"key":'assisted_dip_pullup',"name":'Assisted Dip / Pull-Up Machine',"category":'Upper Body Machines',"icon":'⚙️',"detail_schema":{'max_assistance_lb': 'number'}},
    {"key":'v_bar_attachment',"name":'V-Bar / Close-Grip Attachment',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'single_d_handle',"name":'Single D-Handle',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{'quantity': 'number'}},
    {"key":'triceps_v_bar',"name":'Triceps V-Bar',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'multi_grip_lat_bar',"name":'Multi-Grip Lat Pulldown Bar',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'lifting_belt',"name":'Lifting Belt',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'lifting_straps',"name":'Lifting Straps',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'wrist_wraps',"name":'Wrist Wraps',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'knee_sleeves',"name":'Knee Sleeves',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'dip_belt',"name":'Dip / Pull-Up Weight Belt',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'fractional_plates',"name":'Fractional / Micro Plates',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{'smallest_plate_lb': 'number'}},
    {"key":'barbell_collars',"name":'Barbell Collars',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'blocks',"name":'Pulling Blocks / Jerk Blocks',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{}},
    {"key":'plyo_box',"name":'Plyometric Box',"category":'Attachments & Accessories',"icon":'➰',"detail_schema":{'max_height_in': 'number'}},
    {"key":'battle_ropes',"name":'Battle Ropes',"category":'Conditioning',"icon":'🏃',"detail_schema":{}},
    {"key":'agility_ladder',"name":'Agility Ladder',"category":'Conditioning',"icon":'🏃',"detail_schema":{}},
    {"key":'cones',"name":'Training Cones',"category":'Conditioning',"icon":'🏃',"detail_schema":{}},
    {"key":'parallettes',"name":'Parallettes',"category":'Bodyweight',"icon":'🧍',"detail_schema":{}},
    {"key":'pushup_handles',"name":'Push-Up Handles',"category":'Bodyweight',"icon":'🧍',"detail_schema":{}},
    {"key":'climbing_rope',"name":'Climbing Rope',"category":'Bodyweight',"icon":'🧍',"detail_schema":{}},
    {"key":'monkey_bars',"name":'Monkey Bars',"category":'Bodyweight',"icon":'🧍',"detail_schema":{}},
    {"key":'air_bike',"name":'Air / Assault Bike',"category":'Cardio',"icon":'🚲',"detail_schema":{}},
    {"key":'spin_bike',"name":'Spin Bike',"category":'Cardio',"icon":'🚲',"detail_schema":{}},
    {"key":'recumbent_bike',"name":'Recumbent Bike',"category":'Cardio',"icon":'🚲',"detail_schema":{}},
    {"key":'ski_erg',"name":'SkiErg',"category":'Cardio',"icon":'🚲',"detail_schema":{}},
    {"key":'arc_trainer',"name":'Arc Trainer',"category":'Cardio',"icon":'🚲',"detail_schema":{}},
    {"key":'stepmill',"name":'Stepmill',"category":'Cardio',"icon":'🚲',"detail_schema":{}},
    {"key":'curved_treadmill',"name":'Curved Manual Treadmill',"category":'Cardio',"icon":'🚲',"detail_schema":{}},
    {"key":'massage_gun',"name":'Massage Gun',"category":'Recovery & Mobility',"icon":'🧘',"detail_schema":{}},
    {"key":'massage_ball',"name":'Massage / Lacrosse Ball',"category":'Recovery & Mobility',"icon":'🧘',"detail_schema":{}},
    {"key":'mobility_stick',"name":'Mobility Stick / Dowel',"category":'Recovery & Mobility',"icon":'🧘',"detail_schema":{}},
    {"key":'stretch_strap',"name":'Stretching Strap',"category":'Recovery & Mobility',"icon":'🧘',"detail_schema":{}},
    {"key":'slant_board',"name":'Slant Board / Calf Wedge',"category":'Recovery & Mobility',"icon":'🧘',"detail_schema":{}},
]

FULL_GYM_EQUIPMENT_KEYS = [
    "dumbbells","barbell","ez_curl_bar","trap_bar","weight_plates","kettlebells",
    "bench","adjustable_bench","squat_rack","power_rack","preacher_bench","dip_station","pull_up_bar",
    "cable_machine","lat_pulldown","seated_row_machine","chest_press_machine","shoulder_press_machine",
    "leg_press_machine","leg_extension_machine","leg_curl_machine","pec_deck","calf_raise_machine",
    "smith_machine","machine","rope_attachment","straight_bar_attachment","lat_bar_attachment","ankle_strap",
    "bands","ab_wheel","foam_roller","yoga_mat","stability_ball","landmine_attachment",
    "bodyweight","treadmill","bike","rowing_machine","elliptical","stair_climber","jump_rope","sled",
    'safety_squat_bar','swiss_bar','cambered_bar','axle_bar','fixed_barbells','sandbag','weighted_vest','clubs_maces','deadlift_platform','half_rack','wall_rack','glute_ham_developer','roman_chair','hyperextension_bench','decline_bench','hack_squat_machine','pendulum_squat','belt_squat_machine','v_squat_machine','hip_thrust_machine','hip_abductor_machine','hip_adductor_machine','standing_leg_curl','lying_leg_curl','seated_leg_curl','donkey_calf_machine','tibialis_machine','incline_press_machine','decline_press_machine','chest_supported_row_machine','high_row_machine','pullover_machine','lateral_raise_machine','rear_delt_machine','biceps_curl_machine','triceps_extension_machine','assisted_dip_pullup','v_bar_attachment','single_d_handle','triceps_v_bar','multi_grip_lat_bar','lifting_belt','lifting_straps','wrist_wraps','knee_sleeves','dip_belt','fractional_plates','barbell_collars','blocks','plyo_box','battle_ropes','agility_ladder','cones','parallettes','pushup_handles','climbing_rope','monkey_bars','air_bike','spin_bike','recumbent_bike','ski_erg','arc_trainer','stepmill','curved_treadmill'
]
HOME_GYM_EQUIPMENT_KEYS = [
    "dumbbells","barbell","weight_plates","kettlebells","adjustable_bench",
    "power_rack","pull_up_bar","bands","landmine_attachment","bodyweight","yoga_mat",
    'safety_squat_bar','swiss_bar','sandbag','weighted_vest','half_rack','deadlift_platform','lifting_belt','lifting_straps','wrist_wraps','knee_sleeves','dip_belt','fractional_plates','barbell_collars','plyo_box','battle_ropes','parallettes','pushup_handles','air_bike'
]
BODYWEIGHT_EQUIPMENT_KEYS = ["bodyweight","pull_up_bar","bands","yoga_mat","jump_rope",
    'parallettes','pushup_handles','climbing_rope','monkey_bars','weighted_vest','plyo_box'
]

REMOVED_EQUIPMENT_KEYS = {
    # Conditioning equipment removed from the Equipment Log UI.
    "battle_ropes","agility_ladder","cones",

    # Recovery & Mobility equipment removed from the Equipment Log UI.
    "massage_gun","massage_ball","mobility_stick","stretch_strap","slant_board",
}

REMOVED_EQUIPMENT_CATEGORIES = {"Conditioning","Recovery & Mobility"}

def equipment_catalog() -> list[dict[str, Any]]:
    return [
        dict(x) for x in EQUIPMENT_CATALOG
        if x.get("key") not in REMOVED_EQUIPMENT_KEYS
        and x.get("category") not in REMOVED_EQUIPMENT_CATEGORIES
    ]

def equipment_preset_keys(preset: str) -> list[str]:
    preset=(preset or "").strip().lower()
    if preset=="full_gym": keys=FULL_GYM_EQUIPMENT_KEYS
    elif preset=="home_gym": keys=HOME_GYM_EQUIPMENT_KEYS
    elif preset=="bodyweight": keys=BODYWEIGHT_EQUIPMENT_KEYS
    else: return []
    return [x for x in keys if x not in REMOVED_EQUIPMENT_KEYS]

def _legacy_equipment_from_log(items: list[dict[str, Any]]) -> list[str]:
    """Translate the richer Equipment Log into generator capability keys."""
    keys={str(item.get("key") or item.get("equipment_key") or "").strip().lower() for item in items}
    out=set()

    direct={
        "dumbbells":"dumbbells","barbell":"barbell","bench":"bench","squat_rack":"squat_rack",
        "cable_machine":"cable_machine","machine":"machine","pull_up_bar":"pull_up_bar",
        "bodyweight":"bodyweight","ab_wheel":"ab_wheel","treadmill":"treadmill",
        "bike":"bike","rowing_machine":"rowing_machine","kettlebells":"kettlebells","bands":"bands",
    }
    for key,legacy in direct.items():
        if key in keys: out.add(legacy)

    if {"adjustable_bench","preacher_bench"} & keys: out.add("bench")
    if {"power_rack"} & keys:
        out.add("squat_rack")
        out.add("pull_up_bar")
    if {"lat_pulldown","seated_row_machine","chest_press_machine","shoulder_press_machine",
        "leg_press_machine","leg_extension_machine","leg_curl_machine","pec_deck",
        "calf_raise_machine","smith_machine"} & keys:
        out.add("machine")
    if {"rope_attachment","straight_bar_attachment","lat_bar_attachment","ankle_strap"} & keys and "cable_machine" in keys:
        out.add("cable_machine")

    # Bar variations still give Forge a useful barbell capability for compatible movements.
    if {"ez_curl_bar","trap_bar"} & keys:
        out.add("barbell")

    return sorted(out)

def get_equipment_log(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        rows=con.execute(
            """SELECT equipment_key,display_name,category,details_json,is_custom
               FROM user_equipment_log WHERE user_id=?
               ORDER BY category,display_name""",(user_id,)
        ).fetchall()

    items=[]
    for row in rows:
        d=dict(row)
        try: details=json.loads(d.pop("details_json") or "{}")
        except Exception: details={}
        if d["equipment_key"] in REMOVED_EQUIPMENT_KEYS or d["category"] in REMOVED_EQUIPMENT_CATEGORIES:
            continue
        items.append({
            "key":d["equipment_key"],"name":d["display_name"],"category":d["category"],
            "details":details,"is_custom":bool(d["is_custom"]),
        })

    # Backward-compatible migration: old profile equipment becomes an equipment log
    # the first time the new screen is opened.
    if not items:
        profile=get_profile(user_id,db_path)
        old=list((profile or {}).get("equipment") or [])
        if old:
            if "full_gym" in [str(x).lower() for x in old]:
                keys=FULL_GYM_EQUIPMENT_KEYS
            else:
                keys=[str(x).strip().lower() for x in old]
            catalog={x["key"]:x for x in equipment_catalog()}
            migrated=[]
            for key in keys:
                if key in catalog:
                    c=catalog[key]
                    migrated.append({"key":key,"name":c["name"],"category":c["category"],"details":{},"is_custom":False})
            if migrated:
                return set_equipment_log(user_id,migrated,db_path)

    return {"items":items,"legacy_equipment":_legacy_equipment_from_log(items)}

def set_equipment_log(user_id: int, items: list[dict[str, Any]], db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    catalog={x["key"]:x for x in equipment_catalog()}
    clean=[]
    seen=set()
    for raw in items:
        key=str(raw.get("key") or "").strip().lower()
        name=str(raw.get("name") or "").strip()
        custom=bool(raw.get("is_custom",False))
        if not key and name:
            key="custom_"+__import__("re").sub(r"[^a-z0-9]+","_",name.lower()).strip("_")
        if not key or key in seen:
            continue
        if key in REMOVED_EQUIPMENT_KEYS:
            continue
        if key in catalog:
            c=catalog[key]
            name=c["name"]; category=c["category"]; custom=False
        else:
            if not name: continue
            category=str(raw.get("category") or "Other").strip() or "Other"
            custom=True
        details=raw.get("details") if isinstance(raw.get("details"),dict) else {}
        clean.append({"key":key,"name":name,"category":category,"details":details,"is_custom":custom})
        seen.add(key)

    with session(db_path) as con:
        con.execute("DELETE FROM user_equipment_log WHERE user_id=?",(user_id,))
        for item in clean:
            con.execute(
                """INSERT INTO user_equipment_log
                   (user_id,equipment_key,display_name,category,details_json,is_custom)
                   VALUES (?,?,?,?,?,?)""",
                (user_id,item["key"],item["name"],item["category"],_json(item["details"]),1 if item["is_custom"] else 0),
            )
        legacy=_legacy_equipment_from_log(clean)
        # Keep the legacy profile field synchronized for generator/substitution compatibility.
        con.execute(
            "UPDATE user_profiles SET equipment_json=?,updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
            (_json(legacy),user_id),
        )
    return {"items":clean,"legacy_equipment":_legacy_equipment_from_log(clean)}


EXPANDED_EXERCISE_LIBRARY = [('Dumbbell Floor Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Floor-based press with reduced shoulder extension.'), ('Close-Grip Bench Press', 'Triceps', 'Chest, Front Delts', 'Horizontal Push', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 6, 10, 3, 150, 'Double progression', 'Bench press variation emphasizing triceps.'), ('Paused Bench Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 4, 8, 3, 180, 'Double progression', 'Brief pause on the chest before pressing.'), ('Spoto Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Barbell, Bench', 'Advanced', 'Compound', 0, 5, 8, 3, 180, 'Double progression', 'Pause just above the chest.'), ('Decline Push-Up', 'Upper Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Bodyweight', 'Intermediate', 'Compound', 1, 8, 20, 3, 90, 'Rep progression', 'Feet elevated push-up.'), ('Incline Push-Up', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Bodyweight', 'Beginner', 'Compound', 1, 8, 20, 3, 75, 'Rep progression', 'Hands elevated to reduce loading.'), ('Dumbbell Squeeze Press', 'Chest', 'Triceps', 'Horizontal Push', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 10, 15, 3, 90, 'Double progression', 'Press dumbbells together throughout the rep.'), ('Dumbbell Pullover', 'Chest', 'Lats, Triceps', 'Horizontal Push', 'Dumbbells, Bench', 'Intermediate', 'Isolation', 0, 10, 15, 2, 90, 'Double progression', 'Shoulder-extension focused pullover.'), ('Low-to-High Cable Fly', 'Upper Chest', 'Front Delts', 'Horizontal Push', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 2, 75, 'Double progression', 'Cable fly finishing high.'), ('High-to-Low Cable Fly', 'Chest', 'Front Delts', 'Horizontal Push', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 2, 75, 'Double progression', 'Cable fly finishing low.'), ('Chest-Supported Dumbbell Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Bench-supported row to reduce lower-back fatigue.'), ('One-Arm Dumbbell Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Single-arm dumbbell row.'), ('Pendlay Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Barbell', 'Intermediate', 'Compound', 0, 5, 10, 3, 150, 'Double progression', 'Row from a dead stop on the floor.'), ('Meadows Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Barbell', 'Intermediate', 'Compound', 0, 8, 15, 3, 120, 'Double progression', 'Landmine-style one-arm row.'), ('Inverted Row', 'Upper Back', 'Lats, Biceps, Core', 'Horizontal Pull', 'Bodyweight', 'Beginner', 'Compound', 1, 6, 15, 3, 90, 'Rep progression', 'Bodyweight horizontal row.'), ('Wide-Grip Seated Cable Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Wide-grip cable row.'), ('Single-Arm Cable Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 10, 15, 3, 90, 'Double progression', 'Unilateral cable row.'), ('Machine High Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'High-angle machine row.'), ('Straight-Arm Pulldown', 'Lats', 'Triceps', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 2, 75, 'Double progression', 'Lat isolation with mostly straight elbows.'), ('Neutral-Grip Lat Pulldown', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Neutral-grip pulldown.'), ('Close-Grip Lat Pulldown', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Close neutral or supinated pulldown.'), ('Chin-Up', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Pull-Up Bar', 'Intermediate', 'Compound', 0, 5, 12, 3, 120, 'Rep progression', 'Supinated-grip vertical pull.'), ('Neutral-Grip Pull-Up', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Pull-Up Bar', 'Intermediate', 'Compound', 0, 5, 12, 3, 120, 'Rep progression', 'Neutral-grip pull-up.'), ('Scapular Pull-Up', 'Upper Back', 'Lats', 'Vertical Pull', 'Pull-Up Bar', 'Beginner', 'Isolation', 1, 8, 15, 2, 60, 'Rep progression', 'Scapular depression without elbow flexion.'), ('Arnold Press', 'Shoulders', 'Triceps, Front Delts', 'Vertical Push', 'Dumbbells', 'Intermediate', 'Compound', 0, 8, 12, 3, 120, 'Double progression', 'Rotating dumbbell shoulder press.'), ('Seated Dumbbell Shoulder Press', 'Shoulders', 'Triceps', 'Vertical Push', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 12, 3, 120, 'Double progression', 'Seated overhead dumbbell press.'), ('Machine Shoulder Press', 'Shoulders', 'Triceps', 'Vertical Push', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Selectorized shoulder press.'), ('Landmine Press', 'Shoulders', 'Upper Chest, Triceps', 'Vertical Push', 'Barbell', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Angled single-arm or two-arm press.'), ('Cable Lateral Raise', 'Side Delts', 'Shoulders', 'Shoulder Isolation', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Cable lateral raise.'), ('Lean-Away Cable Lateral Raise', 'Side Delts', 'Shoulders', 'Shoulder Isolation', 'Cable Machine', 'Intermediate', 'Isolation', 0, 10, 20, 2, 60, 'Double progression', 'Long-range cable lateral raise.'), ('Front Raise', 'Shoulders', 'Upper Chest', 'Shoulder Isolation', 'Dumbbells', 'Beginner', 'Isolation', 1, 10, 15, 2, 60, 'Double progression', 'Dumbbell front raise.'), ('Reverse Pec Deck', 'Rear Delts', 'Upper Back', 'Horizontal Pull', 'Machine', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Rear-delt fly on pec deck.'), ('Face Pull', 'Rear Delts', 'Upper Back, Rotator Cuff', 'Horizontal Pull', 'Cable Machine', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Cable face pull.'), ('Bent-Over Rear Delt Raise', 'Rear Delts', 'Upper Back', 'Horizontal Pull', 'Dumbbells', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Bent-over dumbbell rear-delt raise.'), ('Incline Dumbbell Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Dumbbells, Bench', 'Intermediate', 'Isolation', 0, 8, 15, 3, 75, 'Double progression', 'Curl from an incline bench.'), ('Hammer Curl', 'Biceps, Brachialis', 'Forearms', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 8, 15, 3, 75, 'Double progression', 'Neutral-grip dumbbell curl.'), ('Cross-Body Hammer Curl', 'Biceps, Brachialis', 'Forearms', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 10, 15, 2, 60, 'Double progression', 'Hammer curl toward opposite shoulder.'), ('Cable Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 15, 3, 60, 'Double progression', 'Standing cable curl.'), ('Bayesian Cable Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Cable Machine', 'Intermediate', 'Isolation', 0, 10, 15, 3, 60, 'Double progression', 'Cable curl with arm behind torso.'), ('Preacher Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 75, 'Double progression', 'Supported preacher curl.'), ('Reverse Curl', 'Biceps, Brachialis', 'Forearms', 'Elbow Flexion', 'Barbell', 'Intermediate', 'Isolation', 0, 10, 15, 2, 60, 'Double progression', 'Pronated-grip curl.'), ('Wrist Curl', 'Forearms', 'Grip', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 12, 20, 2, 45, 'Double progression', 'Forearm wrist flexion.'), ('Reverse Wrist Curl', 'Forearms', 'Grip', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 12, 20, 2, 45, 'Double progression', 'Forearm wrist extension.'), ('Overhead Dumbbell Triceps Extension', 'Triceps', 'Shoulders', 'Elbow Extension', 'Dumbbells', 'Beginner', 'Isolation', 1, 10, 15, 3, 75, 'Double progression', 'Overhead dumbbell extension.'), ('Single-Arm Cable Triceps Extension', 'Triceps', 'Shoulders', 'Elbow Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Single-arm cable extension.'), ('Cable Overhead Triceps Extension', 'Triceps', 'Shoulders', 'Elbow Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Overhead cable extension.'), ('Diamond Push-Up', 'Triceps', 'Chest, Front Delts', 'Horizontal Push', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 20, 3, 75, 'Rep progression', 'Close-hand push-up emphasizing triceps.'), ('Bench Dip', 'Triceps', 'Chest, Front Delts', 'Elbow Extension', 'Bench', 'Beginner', 'Compound', 1, 8, 20, 3, 75, 'Rep progression', 'Bodyweight dip using a bench.'), ('Machine Dip', 'Triceps', 'Chest, Front Delts', 'Elbow Extension', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Assisted or selectorized dip movement.'), ('Front Squat', 'Quads, Glutes', 'Core, Upper Back', 'Squat', 'Barbell, Squat Rack', 'Intermediate', 'Compound', 0, 5, 10, 3, 180, 'Double progression', 'Front-loaded barbell squat.'), ('Box Squat', 'Quads, Glutes', 'Hamstrings, Core', 'Squat', 'Barbell, Squat Rack', 'Intermediate', 'Compound', 0, 5, 10, 3, 180, 'Double progression', 'Squat to a box or bench.'), ('Goblet Squat', 'Quads, Glutes', 'Core', 'Squat', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Front-loaded goblet squat.'), ('Heel-Elevated Goblet Squat', 'Quads', 'Glutes, Core', 'Squat', 'Dumbbells', 'Beginner', 'Compound', 1, 10, 15, 3, 105, 'Double progression', 'Goblet squat with heels elevated.'), ('Smith Machine Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Fixed-path squat.'), ('Hack Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Machine hack squat.'), ('Belt Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Hip-loaded squat variation.'), ('Bulgarian Split Squat', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells, Bench', 'Intermediate', 'Compound', 0, 8, 15, 3, 120, 'Double progression', 'Rear-foot-elevated split squat.'), ('Reverse Lunge', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Step backward into lunge.'), ('Walking Lunge', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells', 'Intermediate', 'Compound', 0, 10, 20, 3, 105, 'Double progression', 'Alternating forward walking lunge.'), ('Step-Up', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Step onto elevated surface.'), ('Single-Leg Leg Press', 'Quads, Glutes', 'Hamstrings', 'Knee Extension', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Unilateral leg press.'), ('Sissy Squat', 'Quads', 'Core', 'Knee Extension', 'Bodyweight', 'Advanced', 'Isolation', 0, 8, 15, 2, 75, 'Rep progression', 'Bodyweight knee-extension dominant squat.'), ('Romanian Deadlift', 'Hamstrings, Glutes', 'Back, Core', 'Hinge', 'Barbell', 'Intermediate', 'Compound', 0, 6, 12, 3, 150, 'Double progression', 'Hip hinge emphasizing hamstrings.'), ('Dumbbell Romanian Deadlift', 'Hamstrings, Glutes', 'Back, Core', 'Hinge', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Dumbbell hip hinge.'), ('Sumo Deadlift', 'Glutes, Hamstrings, Back', 'Quads, Core', 'Hinge', 'Barbell', 'Intermediate', 'Compound', 0, 4, 8, 3, 180, 'Double progression', 'Wide-stance deadlift.'), ('Trap-Bar Deadlift', 'Glutes, Hamstrings, Back', 'Quads, Core', 'Hinge', 'Barbell', 'Beginner', 'Compound', 1, 5, 10, 3, 150, 'Double progression', 'Neutral-grip deadlift pattern.'), ('Good Morning', 'Hamstrings, Glutes', 'Back, Core', 'Hinge', 'Barbell', 'Advanced', 'Compound', 0, 8, 12, 3, 120, 'Double progression', 'Barbell hip hinge.'), ('Cable Pull-Through', 'Glutes, Hamstrings', 'Core', 'Hip Extension', 'Cable Machine', 'Beginner', 'Compound', 1, 10, 15, 3, 90, 'Double progression', 'Cable hip extension.'), ('Glute Bridge', 'Glutes', 'Hamstrings, Core', 'Hip Extension', 'Bodyweight', 'Beginner', 'Compound', 1, 10, 20, 3, 75, 'Rep progression', 'Floor glute bridge.'), ('Single-Leg Glute Bridge', 'Glutes', 'Hamstrings, Core', 'Hip Extension', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 15, 3, 75, 'Rep progression', 'Unilateral glute bridge.'), ('Dumbbell Hip Thrust', 'Glutes', 'Hamstrings', 'Hip Extension', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Hip thrust loaded with dumbbell.'), ('Cable Kickback', 'Glutes', 'Hamstrings', 'Hip Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Cable hip extension kickback.'), ('Standing Leg Curl', 'Hamstrings', 'Calves', 'Knee Flexion', 'Machine', 'Beginner', 'Isolation', 1, 10, 15, 3, 60, 'Double progression', 'Standing machine hamstring curl.'), ('Nordic Hamstring Curl', 'Hamstrings', 'Glutes', 'Knee Flexion', 'Bodyweight', 'Advanced', 'Compound', 0, 4, 10, 3, 120, 'Rep progression', 'Eccentric-focused bodyweight hamstring curl.'), ('Single-Leg Calf Raise', 'Calves', 'Foot Intrinsics', 'Calf Raise', 'Bodyweight', 'Beginner', 'Isolation', 1, 10, 25, 3, 45, 'Rep progression', 'Single-leg standing calf raise.'), ('Donkey Calf Raise', 'Calves', 'Foot Intrinsics', 'Calf Raise', 'Machine', 'Intermediate', 'Isolation', 0, 10, 20, 3, 60, 'Double progression', 'Hip-hinged calf raise.'), ('Tibialis Raise', 'Tibialis Anterior', 'Lower Leg', 'Calf Raise', 'Bodyweight', 'Beginner', 'Isolation', 1, 12, 25, 3, 45, 'Rep progression', 'Dorsiflexion-focused lower-leg exercise.'), ('Dead Bug', 'Core', 'Hip Flexors', 'Anti-Extension', 'Bodyweight', 'Beginner', 'Core', 1, 8, 16, 3, 45, 'Rep progression', 'Controlled anti-extension drill.'), ('Bird Dog', 'Core', 'Glutes, Back', 'Anti-Extension', 'Bodyweight', 'Beginner', 'Core', 1, 8, 16, 3, 45, 'Rep progression', 'Quadruped contralateral stability drill.'), ('Hollow Body Hold', 'Core', 'Hip Flexors', 'Anti-Extension', 'Bodyweight', 'Intermediate', 'Isometric', 0, 20, 60, 3, 45, 'Time progression', 'Anti-extension isometric hold.'), ('Cable Crunch', 'Abs', 'Hip Flexors', 'Spinal Flexion', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Weighted cable crunch.'), ('Reverse Crunch', 'Abs', 'Hip Flexors', 'Spinal Flexion', 'Bodyweight', 'Beginner', 'Core', 1, 10, 20, 3, 45, 'Rep progression', 'Posterior pelvic tilt crunch.'), ('Hanging Knee Raise', 'Abs', 'Hip Flexors', 'Hip Flexion', 'Pull-Up Bar', 'Intermediate', 'Core', 0, 8, 15, 3, 60, 'Rep progression', 'Hanging knee raise.'), ('Hanging Leg Raise', 'Abs', 'Hip Flexors', 'Hip Flexion', 'Pull-Up Bar', 'Advanced', 'Core', 0, 6, 15, 3, 75, 'Rep progression', 'Straight-leg hanging raise.'), ('Pallof Press', 'Core', 'Obliques', 'Anti-Rotation', 'Cable Machine', 'Beginner', 'Core', 1, 8, 15, 3, 45, 'Double progression', 'Cable anti-rotation press.'), ('Side Plank', 'Core', 'Obliques', 'Anti-Lateral Flexion', 'Bodyweight', 'Beginner', 'Isometric', 1, 20, 60, 3, 45, 'Time progression', 'Lateral core isometric.'), ('Suitcase Carry', 'Core', 'Grip, Obliques', 'Loaded Carry', 'Dumbbells', 'Beginner', 'Core', 1, 20, 60, 3, 60, 'Load/distance progression', 'One-sided loaded carry.'), ("Farmer's Carry", 'Grip', 'Core, Traps', 'Loaded Carry', 'Dumbbells', 'Beginner', 'Compound', 1, 20, 60, 3, 75, 'Load/distance progression', 'Two-handed loaded carry.'), ('Incline Treadmill Walk', 'Cardiovascular', 'Calves, Glutes', 'Steady-State Cardio', 'Treadmill', 'Beginner', 'Cardio', 1, 10, 30, 1, 0, 'Time progression', 'Low-impact incline walking.'), ('Treadmill Intervals', 'Cardiovascular', 'Quads, Calves', 'Interval Cardio', 'Treadmill', 'Intermediate', 'Cardio', 0, 10, 25, 1, 0, 'Interval progression', 'Alternating hard and easy treadmill intervals.'), ('Bike Intervals', 'Cardiovascular', 'Quads', 'Interval Cardio', 'Bike', 'Beginner', 'Cardio', 1, 10, 25, 1, 0, 'Interval progression', 'Stationary bike intervals.'), ('Rowing Intervals', 'Cardiovascular', 'Back, Legs', 'Interval Cardio', 'Rowing Machine', 'Intermediate', 'Cardio', 0, 10, 25, 1, 0, 'Interval progression', 'Rowing ergometer intervals.'), ('Jump Rope', 'Cardiovascular', 'Calves, Shoulders', 'Interval Cardio', 'Bodyweight', 'Intermediate', 'Cardio', 0, 5, 20, 1, 0, 'Time progression', 'Jump-rope conditioning.'), ('Mountain Climber', 'Cardiovascular', 'Core, Hip Flexors', 'Interval Cardio', 'Bodyweight', 'Beginner', 'Cardio', 1, 20, 60, 3, 30, 'Time progression', 'Bodyweight conditioning drill.'), ('Burpee', 'Cardiovascular', 'Chest, Quads, Core', 'Interval Cardio', 'Bodyweight', 'Intermediate', 'Cardio', 0, 6, 15, 3, 45, 'Rep progression', 'Full-body conditioning movement.'), ('Band Pull-Apart', 'Rear Delts', 'Upper Back', 'Horizontal Pull', 'Bodyweight', 'Beginner', 'Isolation', 1, 12, 25, 2, 30, 'Rep progression', 'Upper-back and rear-delt activation.'), ('Wall Slide', 'Shoulders', 'Upper Back', 'Shoulder Isolation', 'Bodyweight', 'Beginner', 'Mobility', 1, 8, 15, 2, 30, 'Rep progression', 'Scapular upward-rotation drill.'), ('Bodyweight Squat', 'Quads, Glutes', 'Core', 'Squat', 'Bodyweight', 'Beginner', 'Compound', 1, 10, 25, 3, 60, 'Rep progression', 'Unloaded squat pattern.'), ('Split Squat', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Bodyweight', 'Beginner', 'Compound', 1, 8, 15, 3, 75, 'Rep progression', 'Stationary split squat.'), ('Pike Push-Up', 'Shoulders', 'Triceps, Upper Chest', 'Vertical Push', 'Bodyweight', 'Intermediate', 'Compound', 0, 6, 15, 3, 90, 'Rep progression', 'Bodyweight vertical pressing progression.'), ('Assisted Pull-Up', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Machine', 'Beginner', 'Compound', 1, 6, 12, 3, 105, 'Double progression', 'Assisted vertical pull.'), ('Assisted Dip', 'Triceps', 'Chest, Front Delts', 'Elbow Extension', 'Machine', 'Beginner', 'Compound', 1, 6, 12, 3, 105, 'Double progression', 'Assisted dip.'), ('Cable Wood Chop', 'Core', 'Obliques, Shoulders', 'Rotation', 'Cable Machine', 'Beginner', 'Core', 1, 10, 15, 3, 60, 'Double progression', 'Rotational cable core exercise.'), ('Russian Twist', 'Core', 'Obliques', 'Rotation', 'Bodyweight', 'Beginner', 'Core', 1, 12, 24, 3, 45, 'Rep progression', 'Rotational seated core exercise.'), ('Back Extension', 'Glutes, Hamstrings', 'Back', 'Hip Extension', 'Machine', 'Beginner', 'Compound', 1, 10, 20, 3, 75, 'Double progression', '45-degree or machine back extension.')]

def ensure_expanded_exercise_directory(db_path=DEFAULT_DB_PATH) -> dict[str, int]:
    """Idempotently add the expanded directory without deleting existing exercises."""
    inserted=0
    substitutions=0
    with session(db_path) as con:
        existing={r["name"].lower():int(r["id"]) for r in con.execute("SELECT id,name FROM exercises")}
        for row in EXPANDED_EXERCISE_LIBRARY:
            name=row[0]
            if name.lower() in existing:
                continue
            cur=con.execute(
                """INSERT INTO exercises
                   (name,primary_muscle,secondary_muscles,movement_pattern,equipment,difficulty,
                    exercise_type,beginner_suitable,min_reps,max_reps,default_sets,
                    default_rest_seconds,progression_method,notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                row
            )
            existing[name.lower()]=int(cur.lastrowid)
            inserted+=1

        # Auto-build high-quality substitution links around the same movement pattern.
        rows=[dict(r) for r in con.execute(
            """SELECT id,name,primary_muscle,movement_pattern,exercise_type
               FROM exercises ORDER BY id"""
        )]
        for a in rows:
            candidates=[]
            for b in rows:
                if a["id"]==b["id"]: continue
                if a["movement_pattern"]!=b["movement_pattern"]: continue
                score=0
                if a["primary_muscle"]==b["primary_muscle"]: score+=3
                elif a["primary_muscle"].split(",")[0].strip()==b["primary_muscle"].split(",")[0].strip(): score+=2
                if a["exercise_type"]==b["exercise_type"]: score+=1
                if score>=2:
                    candidates.append((score,b))
            candidates.sort(key=lambda x:(-x[0],x[1]["name"]))
            for _,b in candidates[:8]:
                cur=con.execute(
                    """INSERT OR IGNORE INTO exercise_substitutions
                       (exercise_id,substitute_exercise_id,reason) VALUES (?,?,?)""",
                    (a["id"],b["id"],"Similar movement pattern and target muscles")
                )
                substitutions += max(cur.rowcount,0)
    return {"inserted":inserted,"substitutions_added":substitutions}


def _exercise_intelligence_metadata(exercise: dict[str, Any]) -> dict[str, Any]:
    """Derive stable exercise intelligence from the existing Forge directory."""
    name=str(exercise.get("name") or "")
    pattern=str(exercise.get("movement_pattern") or "")
    etype=str(exercise.get("exercise_type") or "")
    equipment=str(exercise.get("equipment") or "")
    difficulty=str(exercise.get("difficulty") or "Intermediate")
    primary=str(exercise.get("primary_muscle") or "")

    compound=etype=="Compound"
    machine=any(x in equipment.lower() for x in ("machine","cable"))
    bodyweight="bodyweight" in equipment.lower()
    unilateral=any(x in name.lower() for x in (
        "one-arm","single-arm","single-leg","split squat","lunge","bulgarian",
        "step-up","step up","pistol","single d"
    ))
    supported=any(x in name.lower() for x in ("chest-supported","seated","machine","supported"))
    free_weight=any(x in equipment.lower() for x in ("barbell","dumbbell","kettlebell"))

    fatigue=2
    if compound: fatigue+=1
    if free_weight and compound: fatigue+=1
    if pattern in {"Squat","Hinge","Deadlift","Loaded Carry"}: fatigue+=1
    if machine or supported: fatigue-=1
    fatigue=max(1,min(fatigue,5))

    stability=2
    if free_weight: stability+=1
    if unilateral: stability+=1
    if machine or supported: stability-=1
    stability=max(1,min(stability,5))

    joint_stress=2
    lname=name.lower()
    if any(x in lname for x in ("behind neck","upright row","dip","skull crusher")): joint_stress+=1
    if any(x in lname for x in ("machine","cable","supported","floor press")): joint_stress-=1
    joint_stress=max(1,min(joint_stress,5))

    skill={"Beginner":1,"Intermediate":3,"Advanced":5}.get(difficulty,3)
    hypertrophy=4 if etype in {"Isolation","Compound"} else 2
    strength=5 if compound and pattern in {"Horizontal Push","Vertical Push","Horizontal Pull","Vertical Pull","Squat","Hinge"} else (3 if compound else 1)
    conditioning=5 if etype=="Cardio" or "Cardio" in pattern else (3 if pattern=="Loaded Carry" else 1)

    if machine or supported:
        hypertrophy=min(5,hypertrophy+1)
    if bodyweight and difficulty=="Beginner":
        skill=max(1,skill-1)

    timed = etype=="Isometric" or any(x in name.lower() for x in ("plank","hold","wall sit"))
    bodyweight = "bodyweight" in equipment.lower()
    return {
        "tracking_mode":"timed" if timed else "reps",
        "bodyweight_default":bodyweight,
        "fatigue_cost":fatigue,
        "stability_demand":stability,
        "joint_stress":joint_stress,
        "skill_demand":skill,
        "hypertrophy_score":hypertrophy,
        "strength_score":strength,
        "conditioning_score":conditioning,
        "unilateral":unilateral,
        "supported":supported,
        "compound":compound,
        "primary_pattern":pattern,
        "selection_tags":[
            x for x,yes in (
                ("compound",compound),("unilateral",unilateral),("supported",supported),
                ("machine",machine),("bodyweight",bodyweight),("free_weight",free_weight)
            ) if yes
        ],
    }


def get_user_exercise_preference(user_id: int, exercise_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        row=con.execute(
            "SELECT preference,notes,updated_at FROM user_exercise_preferences WHERE user_id=? AND exercise_id=?",
            (user_id,exercise_id),
        ).fetchone()
    return dict(row) if row else {"preference":"neutral","notes":None,"updated_at":None}


def set_user_exercise_preference(user_id: int, exercise_id: int, preference: str,
                                 notes: str | None = None, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    preference=(preference or "neutral").strip().lower()
    if preference not in {"neutral","favorite","avoid","painful"}:
        raise ValueError("Preference must be neutral, favorite, avoid, or painful")
    with session(db_path) as con:
        ex=con.execute("SELECT id,name FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not ex:
            raise ValueError("Exercise not found")
        if preference=="neutral" and not notes:
            con.execute("DELETE FROM user_exercise_preferences WHERE user_id=? AND exercise_id=?",(user_id,exercise_id))
        else:
            con.execute(
                """INSERT INTO user_exercise_preferences(user_id,exercise_id,preference,notes)
                   VALUES (?,?,?,?)
                   ON CONFLICT(user_id,exercise_id) DO UPDATE SET
                     preference=excluded.preference,notes=excluded.notes,updated_at=CURRENT_TIMESTAMP""",
                (user_id,exercise_id,preference,notes),
            )

    # Keep the generator's existing preference fields synchronized so changes
    # immediately influence plan generation/rebuilds.
    profile=get_profile(user_id,db_path)
    if profile:
        preferred=list(profile.get("preferred_exercises",[]))
        excluded=list(profile.get("excluded_exercises",[]))
        name=str(ex["name"])
        preferred=[x for x in preferred if x.lower()!=name.lower()]
        excluded=[x for x in excluded if x.lower()!=name.lower()]
        if preference=="favorite":
            preferred.append(name)
        elif preference in {"avoid","painful"}:
            excluded.append(name)
        profile["preferred_exercises"]=preferred
        profile["excluded_exercises"]=excluded
        upsert_profile(user_id,profile,db_path)
    return get_user_exercise_preference(user_id,exercise_id,db_path)


def list_exercise_directory(user_id: int | None = None, search: str = "",
                            muscle: str | None = None, equipment: str | None = None,
                            difficulty: str | None = None, movement: str | None = None,
                            compatible_only: bool = False, limit: int = 300,
                            db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    ensure_expanded_exercise_directory(db_path)
    profile=get_profile(user_id,db_path) if user_id else None
    profile_equipment=(profile or {}).get("equipment",["full_gym"])

    with session(db_path) as con:
        rows=[dict(r) for r in con.execute(
            """SELECT id,name,primary_muscle,secondary_muscles,movement_pattern,equipment,
                      difficulty,exercise_type,beginner_suitable,min_reps,max_reps,
                      default_sets,default_rest_seconds,progression_method,notes
               FROM exercises ORDER BY primary_muscle,name"""
        )]

    prefs={}
    if user_id:
        with session(db_path) as con:
            prefs={int(r["exercise_id"]):dict(r) for r in con.execute(
                "SELECT exercise_id,preference,notes FROM user_exercise_preferences WHERE user_id=?",
                (user_id,),
            ).fetchall()}

    q=(search or "").strip().lower()
    out=[]
    for d in rows:
        d["beginner_suitable"]=bool(d["beginner_suitable"])
        d["equipment_compatible"]=_equipment_allowed(d["equipment"],profile_equipment) if user_id else True
        d.update(_exercise_intelligence_metadata(d))
        pref=prefs.get(int(d["id"]),{})
        d["user_preference"]=pref.get("preference","neutral")
        d["preference_notes"]=pref.get("notes")
        if q and q not in " ".join(str(d.get(k,"")) for k in
            ("name","primary_muscle","secondary_muscles","movement_pattern","equipment")).lower():
            continue
        if muscle and muscle!="All" and muscle.lower() not in d["primary_muscle"].lower():
            continue
        if equipment and equipment!="All" and equipment.lower() not in d["equipment"].lower():
            continue
        if difficulty and difficulty!="All" and d["difficulty"].lower()!=difficulty.lower():
            continue
        if movement and movement!="All" and d["movement_pattern"].lower()!=movement.lower():
            continue
        if compatible_only and not d["equipment_compatible"]:
            continue
        out.append(d)
        if len(out)>=max(1,min(int(limit),500)):
            break

    muscles=sorted({r["primary_muscle"] for r in rows})
    equipment_values=sorted({r["equipment"] for r in rows})
    difficulties=sorted({r["difficulty"] for r in rows})
    movements=sorted({r["movement_pattern"] for r in rows})
    return {
        "exercises":out,
        "total_matches":len(out),
        "directory_total":len(rows),
        "filters":{
            "muscles":muscles,
            "equipment":equipment_values,
            "difficulties":difficulties,
            "movements":movements,
        },
    }

def get_exercise_directory_item(exercise_id: int, user_id: int | None = None,
                                db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    directory=list_exercise_directory(user_id=user_id,limit=500,db_path=db_path)
    item=next((x for x in directory["exercises"] if int(x["id"])==int(exercise_id)),None)
    if item:return item
    # Item may have been filtered out only if limit; fetch directly.
    with session(db_path) as con:
        row=con.execute("SELECT * FROM exercises WHERE id=?",(exercise_id,)).fetchone()
    if not row: raise ValueError("Exercise not found")
    d=dict(row)
    d["beginner_suitable"]=bool(d["beginner_suitable"])
    profile=get_profile(user_id,db_path) if user_id else None
    d["equipment_compatible"]=_equipment_allowed(d["equipment"],(profile or {}).get("equipment",["full_gym"]))
    d.update(_exercise_intelligence_metadata(d))
    pref=get_user_exercise_preference(user_id,exercise_id,db_path) if user_id else {"preference":"neutral","notes":None}
    d["user_preference"]=pref.get("preference","neutral")
    d["preference_notes"]=pref.get("notes")
    return d
