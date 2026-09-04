from __future__ import annotations

import json
import hashlib
import hmac
import secrets
import shutil
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
    restored = restore_remote_snapshot(db_path)
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Cloud/container bootstrap: if this process has no restored snapshot yet and
    # the configured writable DB path does not exist, seed it from the bundled
    # baseline database so schema expansion always has the canonical exercises.
    if not restored and not path.exists():
        seed = Path(os.getenv(
            "FORGE_DB_SEED_PATH",
            str(Path(__file__).with_name("fitness_app_initial_database.sqlite"))
        )).expanduser()
        try:
            if seed.exists() and seed.resolve() != path.resolve():
                shutil.copy2(seed, path)
        except Exception as exc:
            _log.warning("Forge database seed copy failed; attempting schema bootstrap anyway: %s", exc)

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
        if "custom_split_json" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN custom_split_json TEXT NOT NULL DEFAULT '[]'")
        if "sport" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN sport TEXT NOT NULL DEFAULT 'general'")
        if "core_workouts_per_week" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN core_workouts_per_week INTEGER NOT NULL DEFAULT 2")
        if "cardio_workouts_per_week" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN cardio_workouts_per_week INTEGER NOT NULL DEFAULT 2")
        if "exercises_per_day" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN exercises_per_day INTEGER NOT NULL DEFAULT 6")
        if "exercises_per_workout_json" not in cols:
            con.execute("ALTER TABLE user_profiles ADD COLUMN exercises_per_workout_json TEXT NOT NULL DEFAULT '[]'")
        ws_cols={r["name"] for r in con.execute("PRAGMA table_info(workout_schedule)").fetchall()}
        if ws_cols and "scheduled_time" not in ws_cols:
            con.execute("ALTER TABLE workout_schedule ADD COLUMN scheduled_time TEXT NOT NULL DEFAULT '17:00'")
        ne_cols={r["name"] for r in con.execute("PRAGMA table_info(nutrition_entries)").fetchall()}
        if ne_cols and "source" not in ne_cols:
            con.execute("ALTER TABLE nutrition_entries ADD COLUMN source TEXT")
        if ne_cols and "source_url" not in ne_cols:
            con.execute("ALTER TABLE nutrition_entries ADD COLUMN source_url TEXT")
    ensure_expanded_exercise_directory(db_path)
    ensure_exercise_muscle_taxonomy(db_path)
    ensure_exercise_intelligence_v4(db_path)
    ensure_plan_exercise_locks(db_path)
    ensure_exercise_progression_state(db_path)
    ensure_programming_decisions(db_path)
    ensure_training_strategy_state(db_path)
    ensure_exercise_form_demo_metadata(db_path)
    ensure_bundled_exercise_demo_assets(db_path)


def ensure_exercise_muscle_taxonomy(db_path=DEFAULT_DB_PATH) -> None:
    """Maintain a normalized broad-muscle/sub-muscle map for every exercise."""
    from muscle_taxonomy import MUSCLE_TAXONOMY, exercise_links
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS muscle_taxonomy (
            muscle_group TEXT NOT NULL, sub_muscle TEXT NOT NULL,
            PRIMARY KEY(muscle_group, sub_muscle))""")
        con.execute("""CREATE TABLE IF NOT EXISTS exercise_muscles (
            exercise_id INTEGER NOT NULL, muscle_group TEXT NOT NULL, sub_muscle TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('primary','secondary')),
            PRIMARY KEY(exercise_id,muscle_group,sub_muscle,role),
            FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE)""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_exercise_muscles_group ON exercise_muscles(muscle_group,sub_muscle)")
        for group, subs in MUSCLE_TAXONOMY.items():
            for sub in subs:
                con.execute("INSERT OR IGNORE INTO muscle_taxonomy(muscle_group,sub_muscle) VALUES (?,?)",(group,sub))
        rows=con.execute("SELECT id,name,primary_muscle,secondary_muscles FROM exercises").fetchall()
        for row in rows:
            d=dict(row)
            con.execute("DELETE FROM exercise_muscles WHERE exercise_id=?",(d["id"],))
            for link in exercise_links(d):
                con.execute("INSERT OR IGNORE INTO exercise_muscles(exercise_id,muscle_group,sub_muscle,role) VALUES (?,?,?,?)",
                            (d["id"],link["muscle_group"],link["sub_muscle"],link["role"]))



def ensure_plan_exercise_locks(db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS plan_exercise_locks (
            user_id INTEGER NOT NULL, workout_index INTEGER NOT NULL, exercise_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id,workout_index,exercise_id))""")

def get_plan_exercise_locks(user_id:int, db_path=DEFAULT_DB_PATH) -> dict[int,list[int]]:
    with session(db_path) as con:
        rows=con.execute("SELECT workout_index,exercise_id FROM plan_exercise_locks WHERE user_id=? ORDER BY workout_index,created_at",(user_id,)).fetchall()
    out={}
    for r in rows: out.setdefault(int(r["workout_index"]),[]).append(int(r["exercise_id"]))
    return out

def set_plan_exercise_lock(user_id:int, workout_index:int, exercise_id:int, locked:bool, db_path=DEFAULT_DB_PATH) -> dict:
    with session(db_path) as con:
        if locked:
            con.execute("INSERT OR IGNORE INTO plan_exercise_locks(user_id,workout_index,exercise_id) VALUES (?,?,?)",(user_id,workout_index,exercise_id))
        else:
            con.execute("DELETE FROM plan_exercise_locks WHERE user_id=? AND workout_index=? AND exercise_id=?",(user_id,workout_index,exercise_id))
    return {"workout_index":workout_index,"exercise_id":exercise_id,"locked":bool(locked)}


def ensure_exercise_progression_state(db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS exercise_progression_state (
            user_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, method TEXT NOT NULL,
            status TEXT NOT NULL, exposure_count INTEGER NOT NULL DEFAULT 0,
            plateau_evidence INTEGER NOT NULL DEFAULT 0, retention_score INTEGER NOT NULL DEFAULT 50,
            next_threshold TEXT, last_exposures_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id,exercise_id))""")

def save_exercise_progression_state(user_id:int, exercise_id:int, state:dict, db_path=DEFAULT_DB_PATH) -> None:
    ensure_exercise_progression_state(db_path)
    with session(db_path) as con:
        con.execute("""INSERT INTO exercise_progression_state
            (user_id,exercise_id,method,status,exposure_count,plateau_evidence,retention_score,next_threshold,last_exposures_json,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(user_id,exercise_id) DO UPDATE SET method=excluded.method,status=excluded.status,
            exposure_count=excluded.exposure_count,plateau_evidence=excluded.plateau_evidence,retention_score=excluded.retention_score,
            next_threshold=excluded.next_threshold,last_exposures_json=excluded.last_exposures_json,updated_at=CURRENT_TIMESTAMP""",
            (user_id,exercise_id,state.get('method','double progression'),state.get('status','new'),int(state.get('sessions_analyzed',0)),
             int(state.get('plateau_evidence',0)),int(state.get('retention_score',50)),state.get('next_load_threshold'),
             _json(state.get('last_exposures') or [])))

def get_exercise_progression_state(user_id:int, exercise_id:int, db_path=DEFAULT_DB_PATH):
    ensure_exercise_progression_state(db_path)
    with session(db_path) as con:
        r=con.execute("SELECT * FROM exercise_progression_state WHERE user_id=? AND exercise_id=?",(user_id,exercise_id)).fetchone()
    if not r:return None
    d=dict(r)
    try:d['last_exposures']=json.loads(d.pop('last_exposures_json') or '[]')
    except Exception:d['last_exposures']=[]
    return d


def ensure_programming_decisions(db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS programming_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            decision_type TEXT NOT NULL, scope TEXT NOT NULL, duration TEXT NOT NULL,
            target_type TEXT NOT NULL, target_id TEXT, target_name TEXT,
            old_value_json TEXT, new_value_json TEXT, evidence TEXT NOT NULL,
            confidence TEXT NOT NULL DEFAULT 'medium', applied INTEGER NOT NULL DEFAULT 1,
            source TEXT NOT NULL DEFAULT 'forge_intelligence_core',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_programming_decisions_user_created ON programming_decisions(user_id,created_at DESC,id DESC)")

def record_programming_decision(user_id:int, *, decision_type:str, scope:str, duration:str, target_type:str,
                                target_id=None, target_name=None, old_value=None, new_value=None,
                                evidence:str, confidence:str='medium', applied:bool=True, source:str='forge_intelligence_core',
                                db_path=DEFAULT_DB_PATH) -> int:
    ensure_programming_decisions(db_path)
    confidence=confidence if confidence in {'low','medium','high'} else 'medium'
    with session(db_path) as con:
        cur=con.execute("""INSERT INTO programming_decisions
            (user_id,decision_type,scope,duration,target_type,target_id,target_name,old_value_json,new_value_json,evidence,confidence,applied,source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id,decision_type,scope,duration,target_type,str(target_id) if target_id is not None else None,target_name,
             _json(old_value) if old_value is not None else None,_json(new_value) if new_value is not None else None,
             evidence,confidence,int(bool(applied)),source))
        return int(cur.lastrowid)

def list_programming_decisions(user_id:int, limit:int=50, db_path=DEFAULT_DB_PATH):
    ensure_programming_decisions(db_path); limit=max(1,min(200,int(limit)))
    with session(db_path) as con:
        rows=con.execute("SELECT * FROM programming_decisions WHERE user_id=? ORDER BY id DESC LIMIT ?",(user_id,limit)).fetchall()
    out=[]
    for r in rows:
        d=dict(r)
        for src,dst in [('old_value_json','old_value'),('new_value_json','new_value')]:
            raw=d.pop(src,None)
            try:d[dst]=json.loads(raw) if raw else None
            except Exception:d[dst]=raw
        d['applied']=bool(d['applied']); out.append(d)
    return out

def ensure_exercise_intelligence_v4(db_path=DEFAULT_DB_PATH) -> None:
    """Exercise Database 4.0: normalized similarity, stress, stability and substitution metadata."""
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS exercise_intelligence (
            exercise_id INTEGER PRIMARY KEY, movement_family TEXT NOT NULL, similarity_family TEXT NOT NULL,
            joint_stress INTEGER NOT NULL DEFAULT 3, stability_demand INTEGER NOT NULL DEFAULT 3,
            skill_demand INTEGER NOT NULL DEFAULT 3, fatigue_cost INTEGER NOT NULL DEFAULT 3,
            FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE)""")
        rows=con.execute("SELECT id,name,movement_pattern,exercise_type,equipment,difficulty FROM exercises").fetchall()
        for r in rows:
            d=dict(r); name=str(d['name']).lower(); pattern=str(d.get('movement_pattern') or 'other').lower()
            family=pattern
            if 'press' in name or 'bench' in name: family += ':press'
            elif 'fly' in name: family += ':fly'
            elif 'row' in name: family += ':row'
            elif 'pulldown' in name or 'pull-up' in name or 'chin-up' in name: family += ':vertical_pull'
            elif 'curl' in name: family += ':curl'
            elif 'extension' in name and 'tricep' in name: family += ':triceps_extension'
            elif 'squat' in name: family += ':squat'
            elif 'lunge' in name or 'split squat' in name: family += ':lunge'
            elif 'deadlift' in name or 'rdl' in name: family += ':hinge'
            elif 'raise' in name: family += ':raise'
            equipment=str(d.get('equipment') or '').split(',')[0].strip().lower()
            similarity=f"{family}:{equipment}"
            compound=str(d.get('exercise_type'))=='Compound'
            joint=4 if compound else 2; fatigue=4 if compound else 2
            stability=4 if any(x in equipment for x in ('barbell','dumbbell','bodyweight')) else 2
            skill=4 if str(d.get('difficulty'))=='Advanced' else (3 if compound else 2)
            con.execute("""INSERT INTO exercise_intelligence(exercise_id,movement_family,similarity_family,joint_stress,stability_demand,skill_demand,fatigue_cost)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(exercise_id) DO UPDATE SET movement_family=excluded.movement_family,similarity_family=excluded.similarity_family,
                joint_stress=excluded.joint_stress,stability_demand=excluded.stability_demand,skill_demand=excluded.skill_demand,fatigue_cost=excluded.fatigue_cost""",
                (d['id'],family,similarity,joint,stability,skill,fatigue))

def get_exercise_intelligence(exercise_id:int, db_path=DEFAULT_DB_PATH) -> dict|None:
    with session(db_path) as con:
        r=con.execute("SELECT * FROM exercise_intelligence WHERE exercise_id=?",(exercise_id,)).fetchone()
    return dict(r) if r else None

def get_muscle_taxonomy(db_path=DEFAULT_DB_PATH) -> dict[str,list[str]]:
    with session(db_path) as con:
        rows=con.execute("SELECT muscle_group,sub_muscle FROM muscle_taxonomy ORDER BY muscle_group,sub_muscle").fetchall()
    out={}
    for row in rows: out.setdefault(row["muscle_group"],[]).append(row["sub_muscle"])
    return out

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
             priority_muscles_json, recovery_level, cardio_preference, workout_split, custom_split_json, sport, core_workouts_per_week, cardio_workouts_per_week, exercises_per_day, exercises_per_workout_json, seed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
              workout_split=excluded.workout_split, custom_split_json=excluded.custom_split_json, sport=excluded.sport, core_workouts_per_week=excluded.core_workouts_per_week, cardio_workouts_per_week=excluded.cardio_workouts_per_week, exercises_per_day=excluded.exercises_per_day, exercises_per_workout_json=excluded.exercises_per_workout_json, seed=excluded.seed,
              updated_at=CURRENT_TIMESTAMP""",
            (
                user_id, profile["goal"], profile["experience"], profile["days_per_week"],
                profile["minutes_per_workout"], _json(profile.get("equipment", [])),
                _json(profile.get("preferred_exercises", [])), _json(profile.get("excluded_exercises", [])),
                _json(profile.get("priority_muscles", [])), profile.get("recovery_level", "normal"),
                profile.get("cardio_preference", "moderate"), profile.get("workout_split", "auto"), _json(profile.get("custom_split", [])), profile.get("sport", "general"),
                max(0, min(int(profile.get("core_workouts_per_week", 2)), int(profile["days_per_week"]))),
                max(0, min(int(profile.get("cardio_workouts_per_week", 2)), int(profile["days_per_week"]))),
                max(3, min(int(profile.get("exercises_per_day", 6)), 10)),
                _json(profile.get("exercises_per_workout", [])),
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
    d["custom_split"] = json.loads(d.pop("custom_split_json", "[]") or "[]")
    d["exercises_per_workout"] = json.loads(d.pop("exercises_per_workout_json", "[]") or "[]")
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
               WHERE w.id=? AND p.user_id=? AND p.status='active'""", (workout_id, user_id)
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
            """SELECT ws.id,ws.workout_id FROM workout_sessions ws
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE ws.id=? AND p.user_id=? AND p.status='active' AND ws.status='active'""", (session_id, user_id)
        ).fetchone()
        if not valid:
            raise ValueError("Active workout session is stale. Resume or start the current workout.")
        belongs = con.execute(
            "SELECT 1 FROM workout_exercises WHERE workout_id=? AND exercise_id=? LIMIT 1",
            (valid["workout_id"], exercise_id),
        ).fetchone()
        if not belongs:
            raise ValueError("This exercise does not match the active workout session. Reopen the workout to resync it.")
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
               WHERE p.user_id=? AND p.status='active' AND ws.status='active'
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
            cur.setdefault("session_best", []).append({"e1rm":e1rm,"weight":weight,"reps":reps,"recorded_at":row["recorded_at"]})
    records = list(by_ex.values())
    for r in records:
        r["max_weight"] = round(r["max_weight"], 2)
        r["best_e1rm"] = round(r["best_e1rm"], 2)
        r["best_volume_set"] = round(r["best_volume_set"], 2)
        vals=[float(x.get("e1rm") or 0) for x in r.pop("session_best",[]) if float(x.get("e1rm") or 0)>0]
        r["record_categories"]={"weight_pr":r["max_weight"],"estimated_1rm_pr":r["best_e1rm"],"rep_pr":r["best_reps"],"set_volume_pr":r["best_volume_set"]}
        r["trend"]="improving" if len(vals)>=4 and sum(vals[-2:])/2>sum(vals[:2])/2*1.015 else "declining" if len(vals)>=4 and sum(vals[-2:])/2<sum(vals[:2])/2*.985 else "steady"
    records.sort(key=lambda x: (x["best_e1rm"], x["max_weight"]), reverse=True)
    return records[:limit]


def _calculate_latest_exercise_targets(user_id: int, exercise_id: int, db_path=DEFAULT_DB_PATH,
                                min_reps: int | None=None, max_reps: int | None=None,
                                load_mode: str | None=None) -> dict[str, Any] | None:
    """Build an adaptive next-set target from recent logged performance.

    v14.57 uses the programmed rep range plus recent RPE/performance instead of
    a fixed +5 lb rule. It also supports bodyweight and timed exercises.
    """
    history = get_exercise_history(user_id, exercise_id, 100, db_path)
    sets = [x for x in history["sets"] if x.get("reps") is not None or x.get("duration_seconds")]
    if not sets:
        return None
    latest = sets[-1]
    mode = (load_mode or latest.get("load_mode") or "weight").lower()
    recent = sets[-5:]
    valid_rpes=[float(x["rpe"]) for x in recent if x.get("rpe") is not None and float(x["rpe"])>0]
    avg_rpe = sum(valid_rpes)/len(valid_rpes) if valid_rpes else 8.0
    sample_count=len(recent)
    confidence="high" if sample_count>=4 else "medium" if sample_count>=2 else "low"

    if mode == "timed" or latest.get("duration_seconds"):
        durations=[int(x.get("duration_seconds") or 0) for x in recent if int(x.get("duration_seconds") or 0)>0]
        last_duration=int(latest.get("duration_seconds") or (durations[-1] if durations else 0))
        if avg_rpe <= 7.25:
            target=max(5,last_duration+10); action="increase_duration"
            reason="Recent holds are controlled, so add a small amount of time."
        elif avg_rpe >= 9.25:
            target=max(5,last_duration-5); action="reduce_duration"
            reason="Recent effort is very high, so trim the hold slightly and protect form."
        else:
            target=max(5,last_duration+5 if avg_rpe < 8.25 else last_duration); action="hold_duration" if target==last_duration else "increase_duration"
            reason="Build the hold gradually while keeping effort repeatable."
        return {"exercise_id":exercise_id,"load_mode":"timed","action":action,
                "suggested_duration_seconds":target,"last_duration_seconds":last_duration,
                "recent_average_rpe":round(avg_rpe,2),"confidence":confidence,
                "sample_count":sample_count,"reason":reason}

    lo=max(1,int(min_reps or 6)); hi=max(lo,int(max_reps or max(lo,12)))
    recent_reps=[int(x.get("reps") or 0) for x in recent if x.get("reps") is not None]
    last_reps=int(latest.get("reps") or lo)
    best_recent=max(recent_reps or [last_reps])

    if mode == "bodyweight":
        if avg_rpe <= 7.5:
            target=min(hi,max(lo,last_reps+1)); action="add_reps" if target>last_reps else "hold_reps"
            reason="Recent bodyweight sets are controlled, so progress by adding a rep before adding load."
        elif avg_rpe >= 9.25 or last_reps < lo:
            target=max(lo,min(last_reps,hi)); action="hold_reps"
            reason="Effort is high, so hold the rep target and prioritize clean repetitions."
        else:
            target=max(lo,min(hi,last_reps)); action="hold_reps"
            reason="Keep this rep target until it becomes consistently easier."
        return {"exercise_id":exercise_id,"load_mode":"bodyweight","action":action,
                "suggested_reps":target,"last_reps":last_reps,"recent_best_reps":best_recent,
                "recent_average_rpe":round(avg_rpe,2),"confidence":confidence,
                "sample_count":sample_count,"reason":reason}

    weight=float(latest.get("weight") or 0)
    # Small, gym-realistic increments; lower loads get finer jumps.
    increment=2.5 if weight < 80 else 5.0
    if avg_rpe >= 9.25 or last_reps < lo:
        suggested=max(0.0,round((weight*0.95)/2.5)*2.5)
        target_reps=lo; action="reduce_load"
        reason="Recent effort or reps suggest the current load is too aggressive for the programmed range."
    elif avg_rpe <= 7.5 and best_recent >= hi:
        suggested=round((weight+increment)*2)/2
        target_reps=lo; action="increase_load"
        reason="You reached the top of the programmed rep range with controlled effort, so add a small amount of load."
    elif last_reps < hi:
        suggested=weight
        target_reps=min(hi,max(lo,last_reps+1 if avg_rpe <= 8.5 else last_reps))
        action="add_reps" if target_reps>last_reps else "hold_load"
        reason="Keep the load steady and build reps inside the programmed range before increasing weight."
    else:
        suggested=weight; target_reps=max(lo,min(hi,last_reps)); action="hold_load"
        reason="Hold this load until the top of the rep range is repeatable at a manageable effort."
    return {"exercise_id":exercise_id,"load_mode":"weight","action":action,
            "suggested_weight":round(suggested,2),"suggested_reps":target_reps,
            "last_weight":weight,"last_reps":last_reps,"recent_best_reps":best_recent,
            "rep_range":{"min":lo,"max":hi},"recent_average_rpe":round(avg_rpe,2),
            "confidence":confidence,"sample_count":sample_count,"reason":reason}



def ensure_persistent_program_targets(db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS persistent_program_targets (
            user_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, evidence_key TEXT NOT NULL,
            load_mode TEXT NOT NULL DEFAULT 'weight', suggested_weight REAL, suggested_reps INTEGER,
            suggested_duration_seconds INTEGER, action TEXT NOT NULL, evidence TEXT NOT NULL,
            confidence TEXT NOT NULL DEFAULT 'medium', source TEXT NOT NULL DEFAULT 'forge_15_1',
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id,exercise_id), UNIQUE(user_id,evidence_key))""")

def get_persistent_program_target(user_id:int, exercise_id:int, db_path=DEFAULT_DB_PATH):
    ensure_persistent_program_targets(db_path)
    with session(db_path) as con:
        r=con.execute("SELECT * FROM persistent_program_targets WHERE user_id=? AND exercise_id=?",(user_id,exercise_id)).fetchone()
    return dict(r) if r else None

def save_persistent_program_target(user_id:int, exercise_id:int, target:dict, evidence_key:str, evidence:str, confidence:str='high', db_path=DEFAULT_DB_PATH):
    ensure_persistent_program_targets(db_path)
    with session(db_path) as con:
        prior=con.execute("SELECT * FROM persistent_program_targets WHERE user_id=? AND exercise_id=?",(user_id,exercise_id)).fetchone()
        if prior and prior['evidence_key']==evidence_key:
            return {'applied':False,'duplicate':True,'target':dict(prior)}
        con.execute("""INSERT INTO persistent_program_targets
            (user_id,exercise_id,evidence_key,load_mode,suggested_weight,suggested_reps,suggested_duration_seconds,action,evidence,confidence,applied_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(user_id,exercise_id) DO UPDATE SET evidence_key=excluded.evidence_key,load_mode=excluded.load_mode,
            suggested_weight=excluded.suggested_weight,suggested_reps=excluded.suggested_reps,suggested_duration_seconds=excluded.suggested_duration_seconds,
            action=excluded.action,evidence=excluded.evidence,confidence=excluded.confidence,applied_at=CURRENT_TIMESTAMP""",
            (user_id,exercise_id,evidence_key,target.get('load_mode') or 'weight',target.get('suggested_weight'),target.get('suggested_reps'),
             target.get('suggested_duration_seconds'),target.get('action') or 'hold',evidence,confidence))
        row=con.execute("SELECT * FROM persistent_program_targets WHERE user_id=? AND exercise_id=?",(user_id,exercise_id)).fetchone()
    return {'applied':True,'duplicate':False,'target':dict(row)}

def get_latest_exercise_targets(user_id: int, exercise_id: int, db_path=DEFAULT_DB_PATH, min_reps: int | None = None, max_reps: int | None = None, load_mode: str | None = None, use_persistent: bool = True) -> dict[str, Any] | None:
    calculated=_calculate_latest_exercise_targets(user_id,exercise_id,db_path,min_reps,max_reps,load_mode)
    if not use_persistent:
        return calculated
    persistent=get_persistent_program_target(user_id,exercise_id,db_path)
    if not persistent:
        return calculated
    out=dict(calculated or {})
    out.update({k:persistent.get(k) for k in ('load_mode','suggested_weight','suggested_reps','suggested_duration_seconds','action') if persistent.get(k) is not None})
    out['persistent_target']=True
    out['persistent_evidence']=persistent.get('evidence')
    out['persistent_applied_at']=persistent.get('applied_at')
    return out


def get_session_intelligence(user_id: int, session_id: int, exercise_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    """Return live, session-only coaching after a logged set.

    v14.58 combines within-session RPE, rep/duration decay and planned volume to
    recommend rest and whether to continue, trim, or optionally extend an exercise.
    It never rewrites the saved program; recommendations apply only to the active session.
    """
    with session(db_path) as con:
        plan = con.execute(
            """SELECT we.sets,we.min_reps,we.max_reps,we.rest_seconds,we.exercise_order,
                      e.name,e.exercise_type,e.movement_pattern,
                      ws.workout_id
               FROM workout_sessions ws
               JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               JOIN workout_exercises we ON we.workout_id=ws.workout_id AND we.exercise_id=?
               JOIN exercises e ON e.id=we.exercise_id
               WHERE ws.id=? AND p.user_id=?""",
            (exercise_id, session_id, user_id),
        ).fetchone()
        if not plan:
            raise ValueError("Exercise is not part of this active workout")
    rows = get_exercise_performance_for_session(session_id, exercise_id, db_path)
    valid = [r for r in rows if not bool(r.get("skipped"))]
    carried_completed = get_session_swap_carry(session_id, exercise_id, db_path)
    completed_current = len(valid)
    completed = carried_completed + completed_current
    planned = max(1, int(plan["sets"] or 1))
    base_rest = max(15, int(plan["rest_seconds"] or 60))
    rpes = [float(r["difficulty"]) for r in valid if r.get("difficulty") is not None]
    recent_rpe = rpes[-1] if rpes else 7.0
    avg_rpe = sum(rpes) / len(rpes) if rpes else 7.0
    mode = (valid[-1].get("load_mode") if valid else "weight") or "weight"

    def effort_value(row):
        if (row.get("load_mode") or mode) == "timed":
            return float(row.get("duration_seconds") or 0)
        try:
            reps = json.loads(row.get("reps_json") or "[]")
        except Exception:
            reps = []
        return float(reps[0] if reps else 0)

    values = [effort_value(r) for r in valid]
    first = next((v for v in values if v > 0), 0.0)
    last = values[-1] if values else 0.0
    decay = ((first-last)/first*100.0) if first > 0 and last > 0 else 0.0
    high_rpe_streak = 0
    for r in reversed(rpes):
        if r >= 9.0: high_rpe_streak += 1
        else: break

    fatigue = 0.0
    fatigue += max(0.0, (avg_rpe-7.0)*1.6)
    fatigue += max(0.0, decay/12.0)
    fatigue += max(0.0, high_rpe_streak-1)*1.2
    fatigue = round(max(0.0, min(10.0, fatigue)), 1)

    rest_mult = 1.0
    if recent_rpe >= 9.5: rest_mult += .50
    elif recent_rpe >= 9.0: rest_mult += .30
    elif recent_rpe >= 8.0: rest_mult += .15
    elif recent_rpe <= 6.5: rest_mult -= .15
    if decay >= 20: rest_mult += .20
    elif decay >= 12: rest_mult += .10
    if str(plan["movement_pattern"] or "").lower() in {"squat","hinge","horizontal push","vertical push","horizontal pull","vertical pull"}:
        rest_mult += .05
    suggested_rest = int(round(base_rest * rest_mult / 15.0) * 15)
    suggested_rest = max(30, min(300, suggested_rest))

    remaining = max(0, planned-completed)
    action = "continue"
    title = "Stay on plan"
    reason = "Performance is stable enough to continue the programmed sets."
    total_sets = planned
    stop = False
    optional = False

    severe = (recent_rpe >= 10 and decay >= 20) or (high_rpe_streak >= 2 and decay >= 25)
    high_fatigue = fatigue >= 7.0 or (high_rpe_streak >= 2 and decay >= 15)
    strong = completed >= planned and avg_rpe <= 6.5 and decay <= 5

    if severe and completed >= 2:
        action = "stop_exercise"
        title = "End this exercise here"
        reason = "Effort and performance drop suggest more sets are unlikely to be productive today. Move on while technique is still protected."
        total_sets = completed
        stop = True
    elif high_fatigue and remaining >= 2:
        action = "trim_volume"
        total_sets = max(completed + 1, planned - 1)
        title = "Trim one set today"
        reason = "Fatigue is accumulating faster than expected, so one fewer set should preserve useful work without adding low-quality volume."
    elif completed >= planned:
        if strong and planned < 8:
            action = "optional_set"
            total_sets = planned + 1
            title = "Optional bonus set"
            reason = "You finished the planned work with low effort and almost no performance drop. One extra clean set is reasonable, but not required."
            optional = True
        else:
            action = "move_on"
            title = "Exercise complete"
            reason = "You completed the planned sets. Move to the next exercise rather than adding unnecessary fatigue."
            total_sets = planned
            stop = True
    elif recent_rpe >= 9.5:
        action = "continue_cautiously"
        title = "Recover longer before the next set"
        reason = "That set was near your limit. Take the full recovery recommendation and keep the next set technically clean."
    elif recent_rpe <= 6.5 and decay <= 5:
        action = "continue_strong"
        title = "Performance is holding well"
        reason = "Effort is controlled and output is stable, so continue the planned volume."

    performance_drop_percent=round(max(0.0, decay),1)
    load_adjustment_percent=-5 if recent_rpe>=9.5 or decay>=25 else 2.5 if recent_rpe<=6.5 and decay<8 and completed<planned else 0
    effort_cap=8 if fatigue>=7 else 9 if fatigue>=4.5 else 10
    remaining_sets=max(0,total_sets-completed)
    estimated_remaining_minutes=max(1,round((remaining_sets*(suggested_rest+45))/60))
    why_changed=(
        "Performance dropped across working sets, so Forge is protecting quality." if decay>=15 else
        "Effort is running high, so the next set should be more conservative." if recent_rpe>=9 else
        "Performance is stable with room in reserve, so progression remains available." if recent_rpe<=7 and decay<10 else
        "The session is tracking close to the programmed target."
    )
    last_weight=float(valid[-1].get("weight") or 0) if valid else 0.0
    last_reps=int(last or 0) if mode != "timed" else 0
    planned_min=int(plan["min_reps"] or 1); planned_max=int(plan["max_reps"] or planned_min)
    target_gap=(last_reps-planned_min) if mode != "timed" else 0
    if mode == "weight" and last_weight > 0:
        next_weight=round(max(0.0,last_weight*(1+load_adjustment_percent/100.0))*2)/2
    else:
        next_weight=None
    if mode == "timed":
        next_reps=None
    elif recent_rpe>=9.5 or decay>=20:
        next_reps=max(planned_min,min(planned_max,last_reps))
    elif recent_rpe<=7 and last_reps>=planned_max:
        next_reps=planned_min
    else:
        next_reps=max(planned_min,min(planned_max,last_reps+1 if last_reps<planned_max else last_reps))
    auto_scope="session"
    auto_duration="next_set" if completed < total_sets else "exercise_complete"
    auto_action=(
        "reduce_load" if load_adjustment_percent<0 else
        "increase_load" if load_adjustment_percent>0 else
        "extend_rest" if suggested_rest>base_rest else
        "trim_volume" if total_sets<planned else
        "hold"
    )
    autoregulation={
        "version":"3.0",
        "scope":auto_scope,
        "duration":auto_duration,
        "action":auto_action,
        "planned":{"sets":planned,"min_reps":planned_min,"max_reps":planned_max,"rest_seconds":base_rest},
        "actual":{"completed_sets":completed,"last_reps":last_reps if mode!="timed" else None,"last_weight":round(last_weight,2) if last_weight else None,"recent_rpe":round(recent_rpe,1),"performance_drop_percent":performance_drop_percent},
        "recommended":{"total_sets":total_sets,"weight":next_weight,"reps":next_reps,"rest_seconds":suggested_rest,"effort_cap":effort_cap},
        "why":why_changed,
        "persistent_change":False,
    }
    next_set={"load_adjustment_percent":load_adjustment_percent,"effort_cap":effort_cap,"rest_seconds":suggested_rest,"estimated_remaining_minutes":estimated_remaining_minutes,"recommended_weight":next_weight,"recommended_reps":next_reps}

    return {
        "exercise_id": exercise_id,
        "exercise_name": plan["name"],
        "action": action,
        "title": title,
        "reason": reason,
        "fatigue_score": fatigue,
        "recent_rpe": round(recent_rpe, 1),
        "average_rpe": round(avg_rpe, 2),
        "performance_drop_percent": round(max(0.0, decay), 1),
        "completed_sets": completed,
        "completed_sets_on_replacement": completed_current,
        "carried_completed_sets": carried_completed,
        "planned_sets": planned,
        "recommended_total_sets": total_sets,
        "remaining_sets": max(0, total_sets-completed),
        "base_rest_seconds": base_rest,
        "recommended_rest_seconds": suggested_rest,
        "stop_exercise": stop,
        "optional_extra_set": optional,
        "load_mode": mode,
        "load_adjustment_percent": load_adjustment_percent,
        "effort_cap": effort_cap,
        "why_changed": why_changed,
        "estimated_remaining_minutes": estimated_remaining_minutes,
        "next_set": next_set,
        "autoregulation": autoregulation,
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

def move_training_module(user_id: int, source_workout_id: int, target_workout_id: int,
                         module_type: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    if module_type not in {"core","cardio"}:
        raise ValueError("Invalid module type")
    if int(source_workout_id)==int(target_workout_id):
        raise ValueError("Choose a different training day")
    with session(db_path) as con:
        rows=con.execute(
            """SELECT w.id,w.name,w.workout_index,pw.id AS week_id,pw.plan_json
               FROM workouts w
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE p.user_id=? AND p.status='active' AND w.id IN (?,?)
               ORDER BY w.id""",
            (user_id,source_workout_id,target_workout_id),
        ).fetchall()
        by_id={int(r["id"]):r for r in rows}
        if int(source_workout_id) not in by_id or int(target_workout_id) not in by_id:
            raise ValueError("Workout not found")
        src=by_id[int(source_workout_id)]; dst=by_id[int(target_workout_id)]
        if int(src["week_id"])!=int(dst["week_id"]):
            raise ValueError("Modules can only move within the current training week")

        completed=con.execute(
            """SELECT 1 FROM training_module_sessions
               WHERE user_id=? AND workout_id=? AND module_type=? AND status='completed' LIMIT 1""",
            (user_id,source_workout_id,module_type),
        ).fetchone()
        if completed:
            raise ValueError(f"Completed {module_type} sessions cannot be moved")

        plan=json.loads(src["plan_json"])
        workouts=plan.get("workouts",[])
        si=int(src["workout_index"]); ti=int(dst["workout_index"])
        if si>=len(workouts) or ti>=len(workouts):
            raise ValueError("Workout is missing from the active plan")
        source=workouts[si]; target=workouts[ti]
        key=f"{module_type}_module"
        module=source.get(key)
        if not module:
            raise ValueError(f"No {module_type} module is scheduled on the source day")
        target_module=target.get(key)

        # Any workout day is a valid destination. If it already contains the same
        # module type, swap the two modules so neither session is lost.
        source[key]=target_module
        target[key]=module
        module["workout_index"]=ti
        module["moved_by_user"]=True
        module["scheduled_with"]=target.get("name") or dst["name"]
        if target_module:
            target_module["workout_index"]=si
            target_module["moved_by_user"]=True
            target_module["scheduled_with"]=source.get("name") or src["name"]

        top_key=f"{module_type}_modules"
        for top in plan.get(top_key,[]):
            wi=int(top.get("workout_index",-1))
            if wi==si:
                top.update(module); top["workout_index"]=ti
            elif target_module and wi==ti:
                top.update(target_module); top["workout_index"]=si

        # Any still-active, uncompleted module session follows the module.
        if target_module:
            con.execute(
                """UPDATE training_module_sessions SET workout_id=-workout_id
                   WHERE user_id=? AND workout_id IN (?,?) AND module_type=? AND status='active'""",
                (user_id,source_workout_id,target_workout_id,module_type),
            )
            con.execute(
                """UPDATE training_module_sessions
                   SET workout_id=CASE WHEN workout_id=? THEN ? WHEN workout_id=? THEN ? ELSE workout_id END
                   WHERE user_id=? AND module_type=? AND status='active'""",
                (-int(source_workout_id),target_workout_id,-int(target_workout_id),source_workout_id,user_id,module_type),
            )
        else:
            con.execute(
                """UPDATE training_module_sessions SET workout_id=?
                   WHERE user_id=? AND workout_id=? AND module_type=? AND status='active'""",
                (target_workout_id,user_id,source_workout_id,module_type),
            )
        con.execute("UPDATE program_weeks SET plan_json=? WHERE id=?",(_json(plan),int(src["week_id"])))
        con.execute(
            """INSERT INTO progression_events(user_id,workout_id,event_type,old_value,new_value,reason)
               VALUES (?,?,?,?,?,?)""",
            (user_id,target_workout_id,f"{module_type}_day_move",
             source.get("name") or src["name"],target.get("name") or dst["name"],
             f"User moved {module_type} module to a different training day"),
        )
    return {
        "status":"moved","module_type":module_type,
        "source_workout_id":int(source_workout_id),
        "target_workout_id":int(target_workout_id),
        "target_workout_name":target.get("name") or dst["name"],
    }


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


def ensure_session_exercise_transitions(db_path=DEFAULT_DB_PATH) -> None:
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS session_exercise_transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL, workout_id INTEGER NOT NULL, exercise_order INTEGER NOT NULL,
            old_exercise_id INTEGER NOT NULL, new_exercise_id INTEGER NOT NULL, carried_completed_sets INTEGER NOT NULL DEFAULT 0,
            swapped_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_session_exercise_transitions_session_order ON session_exercise_transitions(session_id,exercise_order,id DESC)")

def get_session_swap_carry(session_id:int, exercise_id:int, db_path=DEFAULT_DB_PATH) -> int:
    ensure_session_exercise_transitions(db_path)
    with session(db_path) as con:
        r=con.execute("SELECT carried_completed_sets FROM session_exercise_transitions WHERE session_id=? AND new_exercise_id=? ORDER BY id DESC LIMIT 1",(session_id,exercise_id)).fetchone()
    return int(r['carried_completed_sets']) if r else 0


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

        # v15.2: if this is the currently active exercise, preserve the immutable session/workout
        # and carry the completed set position forward to the replacement. Historical rows are never rewritten.
        active=con.execute("""SELECT ws.id AS session_id,COALESCE(ss.current_exercise_index,0) AS current_exercise_index,
            COALESCE(ss.current_set_index,0) AS current_set_index FROM workout_sessions ws
            LEFT JOIN session_state ss ON ss.session_id=ws.id
            WHERE ws.workout_id=? AND ws.status='active' ORDER BY ws.started_at DESC,ws.id DESC LIMIT 1""",(workout_id,)).fetchone()
        transition=None
        if active and int(active['current_exercise_index'])==int(owned['exercise_order']):
            carried=int(con.execute("SELECT COUNT(*) FROM exercise_performance WHERE session_id=? AND exercise_id=? AND skipped=0",(active['session_id'],old_exercise_id)).fetchone()[0])
            carried=max(carried,int(active['current_set_index'] or 0))
            ensure_session_exercise_transitions(db_path)
            con.execute("""INSERT INTO session_exercise_transitions(session_id,workout_id,exercise_order,old_exercise_id,new_exercise_id,carried_completed_sets)
                VALUES(?,?,?,?,?,?)""",(active['session_id'],workout_id,owned['exercise_order'],old_exercise_id,new_exercise_id,carried))
            con.execute("UPDATE session_state SET current_set_index=?,updated_at=CURRENT_TIMESTAMP WHERE session_id=?",(carried,active['session_id']))
            transition={'session_id':int(active['session_id']),'exercise_order':int(owned['exercise_order']),'old_exercise_id':old_exercise_id,
                        'new_exercise_id':new_exercise_id,'carried_completed_sets':carried,'historical_rows_rewritten':False}

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
    result=dict(new)
    result['session_transition']=transition
    return result


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


def reconcile_active_session(user_id: int, session_id: int | None = None, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    """Reconcile persisted session state with the current active program."""
    with session(db_path) as con:
        stale=con.execute("""SELECT ws.id FROM workout_sessions ws
            JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND ws.status='active' AND p.status!='active'""",(user_id,)).fetchall()
        for r in stale:
            con.execute("UPDATE workout_sessions SET status='abandoned',completed_at=CURRENT_TIMESTAMP WHERE id=?",(r["id"],))
            con.execute("UPDATE session_state SET abandoned_at=COALESCE(abandoned_at,CURRENT_TIMESTAMP),updated_at=CURRENT_TIMESTAMP WHERE session_id=?",(r["id"],))
        params=[user_id]
        where="p.user_id=? AND p.status='active' AND ws.status='active'"
        if session_id is not None:
            where+=" AND ws.id=?"
            params.append(int(session_id))
        row=con.execute(f"""SELECT ws.id AS session_id,ws.workout_id,w.workout_index,w.name AS workout_name,
                    COALESCE(ss.current_exercise_index,0) AS current_exercise_index,
                    COALESCE(ss.current_set_index,0) AS current_set_index
               FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
               JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
               LEFT JOIN session_state ss ON ss.session_id=ws.id
               WHERE {where} ORDER BY ws.started_at DESC,ws.id DESC LIMIT 1""",tuple(params)).fetchone()
        if not row:
            return {"status":"none","stale_sessions_closed":len(stale)}
        d=dict(row)
        exercises=con.execute("""SELECT we.exercise_order,we.exercise_id,we.sets,e.name
            FROM workout_exercises we JOIN exercises e ON e.id=we.exercise_id
            WHERE we.workout_id=? ORDER BY we.exercise_order""",(d["workout_id"],)).fetchall()
        if not exercises:
            con.execute("UPDATE workout_sessions SET status='abandoned',completed_at=CURRENT_TIMESTAMP WHERE id=?",(d["session_id"],))
            return {"status":"recovered","action":"session_closed","reason":"Workout has no current exercises","stale_sessions_closed":len(stale)}
        ei=max(0,min(int(d["current_exercise_index"] or 0),len(exercises)-1))
        ex=exercises[ei]
        si=max(0,min(int(d["current_set_index"] or 0),max(0,int(ex["sets"] or 1)-1)))
        if ei!=int(d["current_exercise_index"] or 0) or si!=int(d["current_set_index"] or 0):
            con.execute("""INSERT INTO session_state(session_id,current_exercise_index,current_set_index,updated_at)
                VALUES (?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(session_id) DO UPDATE SET
                current_exercise_index=excluded.current_exercise_index,current_set_index=excluded.current_set_index,
                updated_at=CURRENT_TIMESTAMP""",(d["session_id"],ei,si))
        d.update({"status":"ok","current_exercise_index":ei,"current_set_index":si,
                  "current_exercise_id":int(ex["exercise_id"]),"current_exercise_name":ex["name"],
                  "exercise_count":len(exercises),"stale_sessions_closed":len(stale)})
        return d

def get_session_diagnostics(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    sync=reconcile_active_session(user_id,None,db_path)
    with session(db_path) as con:
        stale=int(con.execute("""SELECT COUNT(*) FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND ws.status='active' AND p.status!='active'""",(user_id,)).fetchone()[0])
        duplicates=int(con.execute("""SELECT COUNT(*) FROM (SELECT ws.workout_id,COUNT(*) c FROM workout_sessions ws
            JOIN workouts w ON w.id=ws.workout_id JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id WHERE p.user_id=? AND p.status='active' AND ws.status='active'
            GROUP BY ws.workout_id HAVING c>1)""",(user_id,)).fetchone()[0])
    return {"status":"ok" if stale==0 and duplicates==0 else "review","active_session":sync,
            "stale_active_sessions":stale,"duplicate_active_workouts":duplicates}

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


def get_current_module(user_id: int, workout_id: int, module_type: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    if module_type not in {"core","cardio"}:
        raise ValueError("Invalid module type")
    with session(db_path) as con:
        row=con.execute(
            """SELECT w.workout_index,pw.plan_json
               FROM workouts w
               JOIN program_weeks pw ON pw.id=w.program_week_id
               JOIN programs p ON p.id=pw.program_id
               WHERE w.id=? AND p.user_id=? AND p.status='active'
               ORDER BY pw.week_number DESC LIMIT 1""",
            (workout_id,user_id),
        ).fetchone()
    if not row:
        raise ValueError("Workout not found")
    plan=json.loads(row["plan_json"])
    idx=int(row["workout_index"])
    workouts=plan.get("workouts",[])
    if idx<0 or idx>=len(workouts):
        raise ValueError("Workout is not in the active plan")
    module=workouts[idx].get(f"{module_type}_module")
    if not module:
        raise ValueError(f"No {module_type} module is scheduled with this workout")
    return module


def start_training_module(user_id: int, workout_id: int, module_type: str, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    module=get_current_module(user_id,workout_id,module_type,db_path)
    with session(db_path) as con:
        existing=con.execute(
            """SELECT * FROM training_module_sessions
               WHERE user_id=? AND workout_id=? AND module_type=? AND status='active'
               ORDER BY id DESC LIMIT 1""",(user_id,workout_id,module_type)
        ).fetchone()
        if existing:
            return dict(existing)
        planned=int(module.get("estimated_minutes") or module.get("minutes") or 0)
        cur=con.execute(
            """INSERT INTO training_module_sessions
               (user_id,workout_id,module_type,module_name,status,planned_minutes)
               VALUES (?,?,?,?, 'active', ?)""",
            (user_id,workout_id,module_type,module.get("name") or module_type.title(),planned),
        )
        sid=int(cur.lastrowid)
        row=con.execute("SELECT * FROM training_module_sessions WHERE id=?",(sid,)).fetchone()
        return dict(row)


def get_training_module_logs(user_id: int, module_session_id: int, db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with session(db_path) as con:
        rows=con.execute(
            """SELECT l.*
               FROM training_module_exercise_logs l
               JOIN training_module_sessions s ON s.id=l.module_session_id
               WHERE l.module_session_id=? AND s.user_id=?
               ORDER BY l.id""",
            (module_session_id,user_id),
        ).fetchall()
    out=[]
    for row in rows:
        d=dict(row)
        d["reps"]=json.loads(d.pop("reps_json") or "[]")
        out.append(d)
    return out


def log_core_module_exercise(user_id: int, module_session_id: int, exercise_id: int,
                             sets_completed: int, reps: list[int] | None = None,
                             duration_seconds: int | None = None, weight: float | None = None,
                             load_mode: str = "bodyweight", rpe: float | None = None,
                             db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        ms=con.execute(
            """SELECT * FROM training_module_sessions
               WHERE id=? AND user_id=? AND module_type='core' AND status='active'""",
            (module_session_id,user_id),
        ).fetchone()
        if not ms: raise ValueError("Active core module session not found")
        cur=con.execute(
            """INSERT INTO training_module_exercise_logs
               (module_session_id,exercise_id,sets_completed,reps_json,duration_seconds,weight,load_mode,rpe)
               VALUES (?,?,?,?,?,?,?,?)""",
            (module_session_id,exercise_id,max(1,int(sets_completed)),_json(reps or []),
             duration_seconds,weight,load_mode,rpe),
        )
        return {"id":int(cur.lastrowid),"module_session_id":module_session_id,"exercise_id":exercise_id}


def complete_training_module(user_id: int, module_session_id: int,
                             completed_minutes: float | None = None, distance: float | None = None,
                             pace: str | None = None, rpe: float | None = None,
                             notes: str | None = None, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        row=con.execute(
            "SELECT * FROM training_module_sessions WHERE id=? AND user_id=?",
            (module_session_id,user_id),
        ).fetchone()
        if not row: raise ValueError("Module session not found")
        con.execute(
            """UPDATE training_module_sessions
               SET status='completed',completed_minutes=?,distance=?,pace=?,rpe=?,notes=?,
                   completed_at=CURRENT_TIMESTAMP WHERE id=?""",
            (completed_minutes,distance,pace,rpe,notes,module_session_id),
        )
        result=con.execute("SELECT * FROM training_module_sessions WHERE id=?",(module_session_id,)).fetchone()
        return dict(result)


def get_core_progression_history(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    """Summarize recent completed core work for progressive future targets."""
    with session(db_path) as con:
        rows=con.execute(
            """SELECT e.name,l.reps_json,l.duration_seconds,l.rpe,l.recorded_at
               FROM training_module_exercise_logs l
               JOIN training_module_sessions s ON s.id=l.module_session_id
               JOIN exercises e ON e.id=l.exercise_id
               WHERE s.user_id=? AND s.module_type='core' AND s.status='completed'
               ORDER BY l.recorded_at DESC,l.id DESC""",(user_id,)
        ).fetchall()
    grouped={}
    for row in rows:
        recent=grouped.setdefault(row["name"],[])
        if len(recent)>=8:
            continue
        reps=json.loads(row["reps_json"] or "[]")
        recent.append({
            "reps":int(reps[0]) if reps else None,
            "duration_seconds":int(row["duration_seconds"]) if row["duration_seconds"] else None,
            "rpe":float(row["rpe"]) if row["rpe"] is not None else None,
            "recorded_at":row["recorded_at"],
        })
    out={}
    for name,recent in grouped.items():
        reps=[x["reps"] for x in recent if x["reps"] is not None]
        holds=[x["duration_seconds"] for x in recent if x["duration_seconds"] is not None]
        rpes=[x["rpe"] for x in recent if x["rpe"] is not None]
        out[name]={
            "core_recent":recent,
            "core_last_reps":reps[0] if reps else None,
            "core_last_duration":holds[0] if holds else None,
            "core_best_reps":max(reps) if reps else None,
            "core_best_duration":max(holds) if holds else None,
            "core_avg_rpe":round(sum(rpes)/len(rpes),2) if rpes else None,
        }
    return out


def get_module_tracking_summary(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        sessions=[dict(r) for r in con.execute(
            """SELECT * FROM training_module_sessions WHERE user_id=?
               ORDER BY started_at DESC,id DESC""",(user_id,)
        ).fetchall()]
        logs=[dict(r) for r in con.execute(
            """SELECT l.*,e.name,e.movement_pattern
               FROM training_module_exercise_logs l
               JOIN training_module_sessions s ON s.id=l.module_session_id
               JOIN exercises e ON e.id=l.exercise_id
               WHERE s.user_id=? ORDER BY l.recorded_at DESC,l.id DESC""",(user_id,)
        ).fetchall()]
    completed_core=[x for x in sessions if x["module_type"]=="core" and x["status"]=="completed"]
    completed_cardio=[x for x in sessions if x["module_type"]=="cardio" and x["status"]=="completed"]
    total_cardio_minutes=sum(float(x.get("completed_minutes") or 0) for x in completed_cardio)
    best_holds={}
    for x in logs:
        if x.get("duration_seconds"):
            best_holds[x["name"]]=max(best_holds.get(x["name"],0),int(x["duration_seconds"]))
    return {
        "sessions":sessions[:100],
        "recent_core_logs":logs[:100],
        "core_sessions_completed":len(completed_core),
        "cardio_sessions_completed":len(completed_cardio),
        "cardio_minutes_completed":round(total_cardio_minutes,1),
        "best_core_holds":best_holds,
    }


def get_module_status_for_workout(user_id: int, workout_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    with session(db_path) as con:
        rows=con.execute(
            """SELECT * FROM training_module_sessions
               WHERE user_id=? AND workout_id=? ORDER BY id DESC""",(user_id,workout_id)
        ).fetchall()
    out={"core":None,"cardio":None}
    for row in rows:
        d=dict(row)
        if out.get(d["module_type"]) is None:
            out[d["module_type"]]=d
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
    extra={
        "recovery_reminders":"INTEGER NOT NULL DEFAULT 1",
        "deload_reminders":"INTEGER NOT NULL DEFAULT 1",
        "missed_workout_reminders":"INTEGER NOT NULL DEFAULT 1",
        "incomplete_workout_reminders":"INTEGER NOT NULL DEFAULT 1",
        "schedule_change_alerts":"INTEGER NOT NULL DEFAULT 1",
        "browser_notifications":"INTEGER NOT NULL DEFAULT 0",
    }
    with session(db_path) as con:
        cols={r["name"] for r in con.execute("PRAGMA table_info(notification_settings)").fetchall()}
        for name,ddl in extra.items():
            if name not in cols: con.execute(f"ALTER TABLE notification_settings ADD COLUMN {name} {ddl}")
        con.execute("INSERT OR IGNORE INTO notification_settings(user_id) VALUES (?)",(user_id,))
        row=con.execute("SELECT * FROM notification_settings WHERE user_id=?",(user_id,)).fetchone()
    out=dict(row)
    for k in ("workout_reminders","nutrition_reminders","calendar_conflict_alerts","morning_brief","recovery_reminders","deload_reminders","missed_workout_reminders","incomplete_workout_reminders","schedule_change_alerts","browser_notifications"):
        out[k]=bool(out.get(k,0))
    return out

def update_notification_settings(user_id: int, values: dict[str, Any], db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    get_notification_settings(user_id,db_path); fields=[]; args=[]
    for k,v in values.items():
        if k not in {"workout_reminders","nutrition_reminders","calendar_conflict_alerts","morning_brief","recovery_reminders","deload_reminders","missed_workout_reminders","incomplete_workout_reminders","schedule_change_alerts","browser_notifications","reminder_minutes_before"}: continue
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
    # Specific machines remain specific. Owning a leg press, for example, must
    # not unlock every exercise whose legacy requirement is simply "Machine".
    if {"rope_attachment","straight_bar_attachment","lat_bar_attachment","ankle_strap"} & keys and "cable_machine" in keys:
        out.add("cable_machine")

    # EZ/trap bars are not treated as a general Olympic barbell capability.

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


EXERCISE_CANONICAL_ALIASES = {
    "Overhead Dumbbell Triceps Extension": "Dumbbell Overhead Triceps Extension",
    "Cable Overhead Triceps Extension": "Overhead Cable Triceps Extension",
    "Trap Bar Deadlift": "Trap-Bar Deadlift",
    "Treadmill Incline Walk": "Incline Treadmill Walk",
    "Farmer's Carry": "Farmer Carry",
}

def canonical_exercise_name(name: str) -> str:
    return EXERCISE_CANONICAL_ALIASES.get(str(name or "").strip(), str(name or "").strip())


EXPANDED_EXERCISE_LIBRARY = [('Dumbbell Floor Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Floor-based press with reduced shoulder extension.'), ('Close-Grip Bench Press', 'Triceps', 'Chest, Front Delts', 'Horizontal Push', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 6, 10, 3, 150, 'Double progression', 'Bench press variation emphasizing triceps.'), ('Paused Bench Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 4, 8, 3, 180, 'Double progression', 'Brief pause on the chest before pressing.'), ('Spoto Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Barbell, Bench', 'Advanced', 'Compound', 0, 5, 8, 3, 180, 'Double progression', 'Pause just above the chest.'), ('Decline Push-Up', 'Upper Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Bodyweight', 'Intermediate', 'Compound', 1, 8, 20, 3, 90, 'Rep progression', 'Feet elevated push-up.'), ('Incline Push-Up', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Bodyweight', 'Beginner', 'Compound', 1, 8, 20, 3, 75, 'Rep progression', 'Hands elevated to reduce loading.'), ('Dumbbell Squeeze Press', 'Chest', 'Triceps', 'Horizontal Push', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 10, 15, 3, 90, 'Double progression', 'Press dumbbells together throughout the rep.'), ('Dumbbell Pullover', 'Chest', 'Lats, Triceps', 'Horizontal Push', 'Dumbbells, Bench', 'Intermediate', 'Isolation', 0, 10, 15, 2, 90, 'Double progression', 'Shoulder-extension focused pullover.'), ('Low-to-High Cable Fly', 'Upper Chest', 'Front Delts', 'Horizontal Push', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 2, 75, 'Double progression', 'Cable fly finishing high.'), ('High-to-Low Cable Fly', 'Chest', 'Front Delts', 'Horizontal Push', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 2, 75, 'Double progression', 'Cable fly finishing low.'), ('Chest-Supported Dumbbell Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Bench-supported row to reduce lower-back fatigue.'), ('One-Arm Dumbbell Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Single-arm dumbbell row.'), ('Pendlay Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Barbell', 'Intermediate', 'Compound', 0, 5, 10, 3, 150, 'Double progression', 'Row from a dead stop on the floor.'), ('Meadows Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Barbell', 'Intermediate', 'Compound', 0, 8, 15, 3, 120, 'Double progression', 'Landmine-style one-arm row.'), ('Inverted Row', 'Upper Back', 'Lats, Biceps, Core', 'Horizontal Pull', 'Bodyweight', 'Beginner', 'Compound', 1, 6, 15, 3, 90, 'Rep progression', 'Bodyweight horizontal row.'), ('Wide-Grip Seated Cable Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Wide-grip cable row.'), ('Single-Arm Cable Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 10, 15, 3, 90, 'Double progression', 'Unilateral cable row.'), ('Machine High Row', 'Lats', 'Upper Back, Biceps', 'Horizontal Pull', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'High-angle machine row.'), ('Straight-Arm Pulldown', 'Lats', 'Triceps', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 2, 75, 'Double progression', 'Lat isolation with mostly straight elbows.'), ('Neutral-Grip Lat Pulldown', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Neutral-grip pulldown.'), ('Close-Grip Lat Pulldown', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Close neutral or supinated pulldown.'), ('Chin-Up', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Pull-Up Bar', 'Intermediate', 'Compound', 0, 5, 12, 3, 120, 'Rep progression', 'Supinated-grip vertical pull.'), ('Neutral-Grip Pull-Up', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Pull-Up Bar', 'Intermediate', 'Compound', 0, 5, 12, 3, 120, 'Rep progression', 'Neutral-grip pull-up.'), ('Scapular Pull-Up', 'Upper Back', 'Lats', 'Vertical Pull', 'Pull-Up Bar', 'Beginner', 'Isolation', 1, 8, 15, 2, 60, 'Rep progression', 'Scapular depression without elbow flexion.'), ('Arnold Press', 'Shoulders', 'Triceps, Front Delts', 'Vertical Push', 'Dumbbells', 'Intermediate', 'Compound', 0, 8, 12, 3, 120, 'Double progression', 'Rotating dumbbell shoulder press.'), ('Seated Dumbbell Shoulder Press', 'Shoulders', 'Triceps', 'Vertical Push', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 12, 3, 120, 'Double progression', 'Seated overhead dumbbell press.'), ('Machine Shoulder Press', 'Shoulders', 'Triceps', 'Vertical Push', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Selectorized shoulder press.'), ('Landmine Press', 'Shoulders', 'Upper Chest, Triceps', 'Vertical Push', 'Barbell', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Angled single-arm or two-arm press.'), ('Cable Lateral Raise', 'Side Delts', 'Shoulders', 'Shoulder Isolation', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Cable lateral raise.'), ('Lean-Away Cable Lateral Raise', 'Side Delts', 'Shoulders', 'Shoulder Isolation', 'Cable Machine', 'Intermediate', 'Isolation', 0, 10, 20, 2, 60, 'Double progression', 'Long-range cable lateral raise.'), ('Front Raise', 'Shoulders', 'Upper Chest', 'Shoulder Isolation', 'Dumbbells', 'Beginner', 'Isolation', 1, 10, 15, 2, 60, 'Double progression', 'Dumbbell front raise.'), ('Reverse Pec Deck', 'Rear Delts', 'Upper Back', 'Horizontal Pull', 'Machine', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Rear-delt fly on pec deck.'), ('Face Pull', 'Rear Delts', 'Upper Back, Rotator Cuff', 'Horizontal Pull', 'Cable Machine', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Cable face pull.'), ('Bent-Over Rear Delt Raise', 'Rear Delts', 'Upper Back', 'Horizontal Pull', 'Dumbbells', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Bent-over dumbbell rear-delt raise.'), ('Incline Dumbbell Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Dumbbells, Bench', 'Intermediate', 'Isolation', 0, 8, 15, 3, 75, 'Double progression', 'Curl from an incline bench.'), ('Hammer Curl', 'Biceps, Brachialis', 'Forearms', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 8, 15, 3, 75, 'Double progression', 'Neutral-grip dumbbell curl.'), ('Cross-Body Hammer Curl', 'Biceps, Brachialis', 'Forearms', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 10, 15, 2, 60, 'Double progression', 'Hammer curl toward opposite shoulder.'), ('Cable Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 15, 3, 60, 'Double progression', 'Standing cable curl.'), ('Bayesian Cable Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Cable Machine', 'Intermediate', 'Isolation', 0, 10, 15, 3, 60, 'Double progression', 'Cable curl with arm behind torso.'), ('Preacher Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 75, 'Double progression', 'Supported preacher curl.'), ('Reverse Curl', 'Biceps, Brachialis', 'Forearms', 'Elbow Flexion', 'Barbell', 'Intermediate', 'Isolation', 0, 10, 15, 2, 60, 'Double progression', 'Pronated-grip curl.'), ('Wrist Curl', 'Forearms', 'Grip', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 12, 20, 2, 45, 'Double progression', 'Forearm wrist flexion.'), ('Reverse Wrist Curl', 'Forearms', 'Grip', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 12, 20, 2, 45, 'Double progression', 'Forearm wrist extension.'), ('Overhead Dumbbell Triceps Extension', 'Triceps', 'Shoulders', 'Elbow Extension', 'Dumbbells', 'Beginner', 'Isolation', 1, 10, 15, 3, 75, 'Double progression', 'Overhead dumbbell extension.'), ('Single-Arm Cable Triceps Extension', 'Triceps', 'Shoulders', 'Elbow Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Single-arm cable extension.'), ('Cable Overhead Triceps Extension', 'Triceps', 'Shoulders', 'Elbow Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Overhead cable extension.'), ('Diamond Push-Up', 'Triceps', 'Chest, Front Delts', 'Horizontal Push', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 20, 3, 75, 'Rep progression', 'Close-hand push-up emphasizing triceps.'), ('Bench Dip', 'Triceps', 'Chest, Front Delts', 'Elbow Extension', 'Bench', 'Beginner', 'Compound', 1, 8, 20, 3, 75, 'Rep progression', 'Bodyweight dip using a bench.'), ('Machine Dip', 'Triceps', 'Chest, Front Delts', 'Elbow Extension', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Assisted or selectorized dip movement.'), ('Front Squat', 'Quads, Glutes', 'Core, Upper Back', 'Squat', 'Barbell, Squat Rack', 'Intermediate', 'Compound', 0, 5, 10, 3, 180, 'Double progression', 'Front-loaded barbell squat.'), ('Box Squat', 'Quads, Glutes', 'Hamstrings, Core', 'Squat', 'Barbell, Squat Rack', 'Intermediate', 'Compound', 0, 5, 10, 3, 180, 'Double progression', 'Squat to a box or bench.'), ('Goblet Squat', 'Quads, Glutes', 'Core', 'Squat', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Front-loaded goblet squat.'), ('Heel-Elevated Goblet Squat', 'Quads', 'Glutes, Core', 'Squat', 'Dumbbells', 'Beginner', 'Compound', 1, 10, 15, 3, 105, 'Double progression', 'Goblet squat with heels elevated.'), ('Smith Machine Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Fixed-path squat.'), ('Hack Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Machine hack squat.'), ('Belt Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Hip-loaded squat variation.'), ('Bulgarian Split Squat', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells, Bench', 'Intermediate', 'Compound', 0, 8, 15, 3, 120, 'Double progression', 'Rear-foot-elevated split squat.'), ('Reverse Lunge', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Step backward into lunge.'), ('Walking Lunge', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells', 'Intermediate', 'Compound', 0, 10, 20, 3, 105, 'Double progression', 'Alternating forward walking lunge.'), ('Step-Up', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Step onto elevated surface.'), ('Single-Leg Leg Press', 'Quads, Glutes', 'Hamstrings', 'Knee Extension', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Unilateral leg press.'), ('Sissy Squat', 'Quads', 'Core', 'Knee Extension', 'Bodyweight', 'Advanced', 'Isolation', 0, 8, 15, 2, 75, 'Rep progression', 'Bodyweight knee-extension dominant squat.'), ('Romanian Deadlift', 'Hamstrings, Glutes', 'Back, Core', 'Hinge', 'Barbell', 'Intermediate', 'Compound', 0, 6, 12, 3, 150, 'Double progression', 'Hip hinge emphasizing hamstrings.'), ('Dumbbell Romanian Deadlift', 'Hamstrings, Glutes', 'Back, Core', 'Hinge', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Dumbbell hip hinge.'), ('Sumo Deadlift', 'Glutes, Hamstrings, Back', 'Quads, Core', 'Hinge', 'Barbell', 'Intermediate', 'Compound', 0, 4, 8, 3, 180, 'Double progression', 'Wide-stance deadlift.'), ('Trap-Bar Deadlift', 'Glutes, Hamstrings, Back', 'Quads, Core', 'Hinge', 'Barbell', 'Beginner', 'Compound', 1, 5, 10, 3, 150, 'Double progression', 'Neutral-grip deadlift pattern.'), ('Good Morning', 'Hamstrings, Glutes', 'Back, Core', 'Hinge', 'Barbell', 'Advanced', 'Compound', 0, 8, 12, 3, 120, 'Double progression', 'Barbell hip hinge.'), ('Cable Pull-Through', 'Glutes, Hamstrings', 'Core', 'Hip Extension', 'Cable Machine', 'Beginner', 'Compound', 1, 10, 15, 3, 90, 'Double progression', 'Cable hip extension.'), ('Glute Bridge', 'Glutes', 'Hamstrings, Core', 'Hip Extension', 'Bodyweight', 'Beginner', 'Compound', 1, 10, 20, 3, 75, 'Rep progression', 'Floor glute bridge.'), ('Single-Leg Glute Bridge', 'Glutes', 'Hamstrings, Core', 'Hip Extension', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 15, 3, 75, 'Rep progression', 'Unilateral glute bridge.'), ('Dumbbell Hip Thrust', 'Glutes', 'Hamstrings', 'Hip Extension', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Hip thrust loaded with dumbbell.'), ('Cable Kickback', 'Glutes', 'Hamstrings', 'Hip Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Cable hip extension kickback.'), ('Standing Leg Curl', 'Hamstrings', 'Calves', 'Knee Flexion', 'Machine', 'Beginner', 'Isolation', 1, 10, 15, 3, 60, 'Double progression', 'Standing machine hamstring curl.'), ('Nordic Hamstring Curl', 'Hamstrings', 'Glutes', 'Knee Flexion', 'Bodyweight', 'Advanced', 'Compound', 0, 4, 10, 3, 120, 'Rep progression', 'Eccentric-focused bodyweight hamstring curl.'), ('Single-Leg Calf Raise', 'Calves', 'Foot Intrinsics', 'Calf Raise', 'Bodyweight', 'Beginner', 'Isolation', 1, 10, 25, 3, 45, 'Rep progression', 'Single-leg standing calf raise.'), ('Donkey Calf Raise', 'Calves', 'Foot Intrinsics', 'Calf Raise', 'Machine', 'Intermediate', 'Isolation', 0, 10, 20, 3, 60, 'Double progression', 'Hip-hinged calf raise.'), ('Tibialis Raise', 'Tibialis Anterior', 'Lower Leg', 'Calf Raise', 'Bodyweight', 'Beginner', 'Isolation', 1, 12, 25, 3, 45, 'Rep progression', 'Dorsiflexion-focused lower-leg exercise.'), ('Dead Bug', 'Core', 'Hip Flexors', 'Anti-Extension', 'Bodyweight', 'Beginner', 'Core', 1, 8, 16, 3, 45, 'Rep progression', 'Controlled anti-extension drill.'), ('Bird Dog', 'Core', 'Glutes, Back', 'Anti-Extension', 'Bodyweight', 'Beginner', 'Core', 1, 8, 16, 3, 45, 'Rep progression', 'Quadruped contralateral stability drill.'), ('Hollow Body Hold', 'Core', 'Hip Flexors', 'Anti-Extension', 'Bodyweight', 'Intermediate', 'Isometric', 0, 20, 60, 3, 45, 'Time progression', 'Anti-extension isometric hold.'), ('Cable Crunch', 'Abs', 'Hip Flexors', 'Spinal Flexion', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Weighted cable crunch.'), ('Reverse Crunch', 'Abs', 'Hip Flexors', 'Spinal Flexion', 'Bodyweight', 'Beginner', 'Core', 1, 10, 20, 3, 45, 'Rep progression', 'Posterior pelvic tilt crunch.'), ('Hanging Knee Raise', 'Abs', 'Hip Flexors', 'Hip Flexion', 'Pull-Up Bar', 'Intermediate', 'Core', 0, 8, 15, 3, 60, 'Rep progression', 'Hanging knee raise.'), ('Hanging Leg Raise', 'Abs', 'Hip Flexors', 'Hip Flexion', 'Pull-Up Bar', 'Advanced', 'Core', 0, 6, 15, 3, 75, 'Rep progression', 'Straight-leg hanging raise.'), ('Pallof Press', 'Core', 'Obliques', 'Anti-Rotation', 'Cable Machine', 'Beginner', 'Core', 1, 8, 15, 3, 45, 'Double progression', 'Cable anti-rotation press.'), ('Side Plank', 'Core', 'Obliques', 'Anti-Lateral Flexion', 'Bodyweight', 'Beginner', 'Isometric', 1, 20, 60, 3, 45, 'Time progression', 'Lateral core isometric.'), ('Suitcase Carry', 'Core', 'Grip, Obliques', 'Loaded Carry', 'Dumbbells', 'Beginner', 'Core', 1, 20, 60, 3, 60, 'Load/distance progression', 'One-sided loaded carry.'), ("Farmer's Carry", 'Grip', 'Core, Traps', 'Loaded Carry', 'Dumbbells', 'Beginner', 'Compound', 1, 20, 60, 3, 75, 'Load/distance progression', 'Two-handed loaded carry.'), ('Incline Treadmill Walk', 'Cardiovascular', 'Calves, Glutes', 'Steady-State Cardio', 'Treadmill', 'Beginner', 'Cardio', 1, 10, 30, 1, 0, 'Time progression', 'Low-impact incline walking.'), ('Treadmill Intervals', 'Cardiovascular', 'Quads, Calves', 'Interval Cardio', 'Treadmill', 'Intermediate', 'Cardio', 0, 10, 25, 1, 0, 'Interval progression', 'Alternating hard and easy treadmill intervals.'), ('Bike Intervals', 'Cardiovascular', 'Quads', 'Interval Cardio', 'Bike', 'Beginner', 'Cardio', 1, 10, 25, 1, 0, 'Interval progression', 'Stationary bike intervals.'), ('Rowing Intervals', 'Cardiovascular', 'Back, Legs', 'Interval Cardio', 'Rowing Machine', 'Intermediate', 'Cardio', 0, 10, 25, 1, 0, 'Interval progression', 'Rowing ergometer intervals.'), ('Jump Rope', 'Cardiovascular', 'Calves, Shoulders', 'Interval Cardio', 'Bodyweight', 'Intermediate', 'Cardio', 0, 5, 20, 1, 0, 'Time progression', 'Jump-rope conditioning.'), ('Mountain Climber', 'Cardiovascular', 'Core, Hip Flexors', 'Interval Cardio', 'Bodyweight', 'Beginner', 'Cardio', 1, 20, 60, 3, 30, 'Time progression', 'Bodyweight conditioning drill.'), ('Burpee', 'Cardiovascular', 'Chest, Quads, Core', 'Interval Cardio', 'Bodyweight', 'Intermediate', 'Cardio', 0, 6, 15, 3, 45, 'Rep progression', 'Full-body conditioning movement.'), ('Band Pull-Apart', 'Rear Delts', 'Upper Back', 'Horizontal Pull', 'Bodyweight', 'Beginner', 'Isolation', 1, 12, 25, 2, 30, 'Rep progression', 'Upper-back and rear-delt activation.'), ('Wall Slide', 'Shoulders', 'Upper Back', 'Shoulder Isolation', 'Bodyweight', 'Beginner', 'Mobility', 1, 8, 15, 2, 30, 'Rep progression', 'Scapular upward-rotation drill.'), ('Bodyweight Squat', 'Quads, Glutes', 'Core', 'Squat', 'Bodyweight', 'Beginner', 'Compound', 1, 10, 25, 3, 60, 'Rep progression', 'Unloaded squat pattern.'), ('Split Squat', 'Quads, Glutes', 'Hamstrings', 'Lunge', 'Bodyweight', 'Beginner', 'Compound', 1, 8, 15, 3, 75, 'Rep progression', 'Stationary split squat.'), ('Pike Push-Up', 'Shoulders', 'Triceps, Upper Chest', 'Vertical Push', 'Bodyweight', 'Intermediate', 'Compound', 0, 6, 15, 3, 90, 'Rep progression', 'Bodyweight vertical pressing progression.'), ('Assisted Pull-Up', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Machine', 'Beginner', 'Compound', 1, 6, 12, 3, 105, 'Double progression', 'Assisted vertical pull.'), ('Assisted Dip', 'Triceps', 'Chest, Front Delts', 'Elbow Extension', 'Machine', 'Beginner', 'Compound', 1, 6, 12, 3, 105, 'Double progression', 'Assisted dip.'), ('Cable Wood Chop', 'Core', 'Obliques, Shoulders', 'Rotation', 'Cable Machine', 'Beginner', 'Core', 1, 10, 15, 3, 60, 'Double progression', 'Rotational cable core exercise.'), ('Russian Twist', 'Core', 'Obliques', 'Rotation', 'Bodyweight', 'Beginner', 'Core', 1, 12, 24, 3, 45, 'Rep progression', 'Rotational seated core exercise.'), ('Back Extension', 'Glutes, Hamstrings', 'Back', 'Hip Extension', 'Machine', 'Beginner', 'Compound', 1, 10, 20, 3, 75, 'Double progression', '45-degree or machine back extension.'), ('Incline Barbell Bench Press', 'Upper Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Incline Barbell Bench Press variation for broader exercise selection.'), ('Decline Barbell Bench Press', 'Chest', 'Triceps', 'Horizontal Push', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Decline Barbell Bench Press variation for broader exercise selection.'), ('Smith Machine Bench Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Smith Machine, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Smith Machine Bench Press variation for broader exercise selection.'), ('Pec Deck Fly', 'Chest', 'Front Delts', 'Horizontal Push', 'Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Pec Deck Fly variation for broader exercise selection.'), ('Cable Crossover', 'Chest', 'Front Delts', 'Horizontal Push', 'Cable Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Cable Crossover variation for broader exercise selection.'), ('Ring Push-Up', 'Chest', 'Triceps, Core', 'Horizontal Push', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Ring Push-Up variation for broader exercise selection.'), ('T-Bar Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Barbell', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'T-Bar Row variation for broader exercise selection.'), ('Seal Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Seal Row variation for broader exercise selection.'), ('Machine Seated Row', 'Upper Back', 'Lats, Biceps', 'Horizontal Pull', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Machine Seated Row variation for broader exercise selection.'), ('Underhand Lat Pulldown', 'Lats', 'Biceps', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Underhand Lat Pulldown variation for broader exercise selection.'), ('Wide-Grip Pull-Up', 'Lats', 'Upper Back, Biceps', 'Vertical Pull', 'Pull-Up Bar', 'Advanced', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Wide-Grip Pull-Up variation for broader exercise selection.'), ('Dumbbell Renegade Row', 'Upper Back', 'Core, Lats', 'Horizontal Pull', 'Dumbbells', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Dumbbell Renegade Row variation for broader exercise selection.'), ('Push Press', 'Shoulders', 'Triceps, Quads', 'Vertical Push', 'Barbell', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Push Press variation for broader exercise selection.'), ('Z Press', 'Shoulders', 'Triceps, Core', 'Vertical Push', 'Barbell', 'Advanced', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Z Press variation for broader exercise selection.'), ('Dumbbell Upright Row', 'Shoulders', 'Traps', 'Shoulder Isolation', 'Dumbbells', 'Intermediate', 'Isolation', 0, 8, 15, 3, 90, 'Double progression', 'Dumbbell Upright Row variation for broader exercise selection.'), ('Cable Y Raise', 'Shoulders', 'Lower Traps', 'Shoulder Isolation', 'Cable Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Cable Y Raise variation for broader exercise selection.'), ('Rear Delt Cable Fly', 'Rear Delts', 'Upper Back', 'Horizontal Pull', 'Cable Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Rear Delt Cable Fly variation for broader exercise selection.'), ('EZ-Bar Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Barbell', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'EZ-Bar Curl variation for broader exercise selection.'), ('Spider Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Dumbbells, Bench', 'Intermediate', 'Isolation', 0, 8, 15, 3, 90, 'Double progression', 'Spider Curl variation for broader exercise selection.'), ('Concentration Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Concentration Curl variation for broader exercise selection.'), ('Rope Hammer Curl', 'Biceps, Brachialis', 'Forearms', 'Elbow Flexion', 'Cable Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Rope Hammer Curl variation for broader exercise selection.'), ('Skull Crusher', 'Triceps', 'Shoulders', 'Elbow Extension', 'Barbell, Bench', 'Intermediate', 'Isolation', 0, 8, 15, 3, 90, 'Double progression', 'Skull Crusher variation for broader exercise selection.'), ('Dumbbell Skull Crusher', 'Triceps', 'Shoulders', 'Elbow Extension', 'Dumbbells, Bench', 'Intermediate', 'Isolation', 0, 8, 15, 3, 90, 'Double progression', 'Dumbbell Skull Crusher variation for broader exercise selection.'), ('Rope Triceps Pushdown', 'Triceps', 'Shoulders', 'Elbow Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Rope Triceps Pushdown variation for broader exercise selection.'), ('Pendulum Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Pendulum Squat variation for broader exercise selection.'), ('Single-Leg Press', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Single-Leg Press variation for broader exercise selection.'), ('Conventional Deadlift', 'Glutes, Hamstrings', 'Back, Quads', 'Hinge', 'Barbell', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Conventional Deadlift variation for broader exercise selection.'), ('Trap Bar Deadlift', 'Glutes, Quads', 'Hamstrings, Back', 'Hinge', 'Trap Bar', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Trap Bar Deadlift variation for broader exercise selection.'), ('Single-Leg Romanian Deadlift', 'Hamstrings, Glutes', 'Core', 'Hinge', 'Dumbbells', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Single-Leg Romanian Deadlift variation for broader exercise selection.'), ('Seated Leg Curl', 'Hamstrings', 'Calves', 'Knee Flexion', 'Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Seated Leg Curl variation for broader exercise selection.'), ('Barbell Hip Thrust', 'Glutes', 'Hamstrings', 'Hip Extension', 'Barbell, Bench', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Barbell Hip Thrust variation for broader exercise selection.'), ('Single-Leg Hip Thrust', 'Glutes', 'Hamstrings, Core', 'Hip Extension', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Single-Leg Hip Thrust variation for broader exercise selection.'), ('Cable Glute Kickback', 'Glutes', 'Hamstrings', 'Hip Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Cable Glute Kickback variation for broader exercise selection.'), ('Hip Abduction Machine', 'Glutes', 'Hip Abductors', 'Hip Extension', 'Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Hip Abduction Machine variation for broader exercise selection.'), ('Hip Adduction Machine', 'Adductors', 'Quads', 'Hip Extension', 'Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 90, 'Double progression', 'Hip Adduction Machine variation for broader exercise selection.'), ('V-Up', 'Core', 'Hip Flexors', 'Spinal Flexion', 'Bodyweight', 'Intermediate', 'Core', 0, 8, 15, 3, 90, 'Double progression', 'V-Up variation for broader exercise selection.'), ('Bicycle Crunch', 'Core', 'Obliques, Hip Flexors', 'Rotation', 'Bodyweight', 'Beginner', 'Core', 1, 8, 15, 3, 90, 'Double progression', 'Bicycle Crunch variation for broader exercise selection.'), ('Suitcase March', 'Core', 'Hip Flexors, Obliques', 'Anti-Lateral Flexion', 'Dumbbells', 'Beginner', 'Core', 1, 8, 15, 3, 90, 'Double progression', 'Suitcase March variation for broader exercise selection.'), ('Elliptical Steady State', 'Cardiovascular', 'Quads, Glutes', 'Steady-State Cardio', 'Elliptical', 'Beginner', 'Cardio', 1, 20, 60, 1, 0, 'Time progression', 'Elliptical Steady State variation for broader exercise selection.'), ('Stair Climber', 'Cardiovascular', 'Quads, Glutes', 'Steady-State Cardio', 'Stair Climber', 'Beginner', 'Cardio', 1, 20, 60, 1, 0, 'Time progression', 'Stair Climber variation for broader exercise selection.'), ('Ski Erg Intervals', 'Cardiovascular', 'Lats, Core', 'Interval Cardio', 'Ski Erg', 'Intermediate', 'Cardio', 0, 20, 60, 1, 0, 'Time progression', 'Ski Erg Intervals variation for broader exercise selection.'), ('Assault Bike Intervals', 'Cardiovascular', 'Quads, Shoulders', 'Interval Cardio', 'Bike', 'Intermediate', 'Cardio', 0, 20, 60, 1, 0, 'Time progression', 'Assault Bike Intervals variation for broader exercise selection.'), ('Sled Push', 'Quads, Glutes', 'Calves, Core', 'Loaded Carry', 'Sled', 'Intermediate', 'Conditioning', 0, 20, 60, 3, 90, 'Double progression', 'Sled Push variation for broader exercise selection.'), ('Battle Rope Intervals', 'Cardiovascular', 'Shoulders, Core', 'Interval Cardio', 'Battle Ropes', 'Intermediate', 'Cardio', 0, 20, 60, 1, 0, 'Time progression', 'Battle Rope Intervals variation for broader exercise selection.')]


V14_50_EXERCISE_LIBRARY = [('Tempo Push-Up', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 20, 3, 75, 'Rep progression', 'Three-second eccentric push-up for control and hypertrophy.'), ('Deficit Push-Up', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Bodyweight', 'Intermediate', 'Compound', 0, 8, 20, 3, 90, 'Rep progression', 'Hands elevated on handles or plates for greater range of motion.'), ('Single-Arm Machine Chest Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Unilateral machine press for stable chest loading.'), ('Cable Press', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Cable Machine', 'Beginner', 'Compound', 1, 10, 15, 3, 75, 'Double progression', 'Standing or split-stance cable chest press.'), ('Incline Machine Chest Press', 'Upper Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Stable incline machine press.'), ('Dumbbell Bench Press Neutral Grip', 'Chest', 'Triceps, Front Delts', 'Horizontal Push', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 8, 15, 3, 105, 'Double progression', 'Neutral-grip press with shoulder-friendly arm position.'), ('Kneeling Lat Pulldown', 'Lats', 'Biceps, Upper Back', 'Vertical Pull', 'Cable Machine', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Tall-kneeling pulldown emphasizing lat control.'), ('Half-Kneeling Single-Arm Pulldown', 'Lats', 'Biceps, Core', 'Vertical Pull', 'Cable Machine', 'Intermediate', 'Compound', 0, 10, 15, 3, 75, 'Double progression', 'Unilateral pulldown with trunk stability demand.'), ('Dumbbell Pullover Row', 'Lats', 'Upper Back, Triceps', 'Horizontal Pull', 'Dumbbells, Bench', 'Intermediate', 'Compound', 0, 8, 15, 3, 90, 'Double progression', 'Pullover-to-row hybrid for lats and upper back.'), ('Cable Pullover', 'Lats', 'Triceps', 'Vertical Pull', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Cable shoulder extension for lat isolation.'), ('Prone Y Raise', 'Lower Traps', 'Rear Delts, Rotator Cuff', 'Shoulder Isolation', 'Dumbbells, Bench', 'Beginner', 'Isolation', 1, 10, 20, 2, 60, 'Double progression', 'Prone Y raise for lower traps and shoulder control.'), ('Chest-Supported Rear Delt Row', 'Rear Delts', 'Upper Back, Biceps', 'Horizontal Pull', 'Dumbbells, Bench', 'Beginner', 'Compound', 1, 10, 15, 3, 75, 'Double progression', 'Elbows-out supported row emphasizing rear delts.'), ('Single-Arm Landmine Press', 'Shoulders', 'Upper Chest, Triceps, Core', 'Vertical Push', 'Barbell', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Unilateral angled press with core demand.'), ('Tall-Kneeling Dumbbell Press', 'Shoulders', 'Triceps, Core', 'Vertical Push', 'Dumbbells', 'Intermediate', 'Compound', 0, 8, 12, 3, 90, 'Double progression', 'Kneeling overhead press limiting lower-body assistance.'), ('Machine Lateral Raise', 'Side Delts', 'Shoulders', 'Shoulder Isolation', 'Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Stable machine lateral raise.'), ('Cable Front Raise', 'Shoulders', 'Upper Chest', 'Shoulder Isolation', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 2, 60, 'Double progression', 'Cable front raise with continuous tension.'), ('Alternating Dumbbell Curl', 'Biceps', 'Brachialis, Forearms', 'Elbow Flexion', 'Dumbbells', 'Beginner', 'Isolation', 1, 8, 15, 3, 60, 'Double progression', 'Alternating supinated dumbbell curl.'), ('Machine Biceps Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Machine', 'Beginner', 'Isolation', 1, 8, 15, 3, 60, 'Double progression', 'Stable selectorized biceps curl.'), ('Cable Preacher Curl', 'Biceps', 'Brachialis', 'Elbow Flexion', 'Cable Machine, Bench', 'Intermediate', 'Isolation', 0, 10, 15, 3, 60, 'Double progression', 'Preacher curl with cable resistance.'), ('JM Press', 'Triceps', 'Chest, Front Delts', 'Elbow Extension', 'Barbell, Bench', 'Advanced', 'Compound', 0, 6, 12, 3, 120, 'Double progression', 'Hybrid close-grip press and triceps extension.'), ('Cross-Body Cable Triceps Extension', 'Triceps', 'Shoulders', 'Elbow Extension', 'Cable Machine', 'Beginner', 'Isolation', 1, 10, 20, 3, 60, 'Double progression', 'Single-arm cross-body triceps extension.'), ('Reverse-Grip Triceps Pushdown', 'Triceps', 'Forearms', 'Elbow Extension', 'Cable Machine', 'Intermediate', 'Isolation', 0, 10, 20, 2, 60, 'Double progression', 'Supinated cable pushdown.'), ('Cyclist Squat', 'Quads', 'Glutes, Core', 'Squat', 'Bodyweight', 'Beginner', 'Compound', 1, 10, 20, 3, 75, 'Rep progression', 'Heel-elevated narrow-stance squat emphasizing quads.'), ('Safety Bar Squat', 'Quads, Glutes', 'Hamstrings, Core', 'Squat', 'Safety Squat Bar, Squat Rack', 'Intermediate', 'Compound', 0, 5, 10, 3, 180, 'Double progression', 'Squat using a safety squat bar.'), ('Belt Squat', 'Quads, Glutes', 'Hamstrings', 'Squat', 'Belt Squat Machine', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Lower-body squat pattern with reduced spinal loading.'), ('Reverse Lunge', 'Quads, Glutes', 'Hamstrings, Core', 'Lunge', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 90, 'Double progression', 'Backward stepping lunge.'), ('Walking Lunge', 'Quads, Glutes', 'Hamstrings, Core', 'Lunge', 'Dumbbells', 'Intermediate', 'Compound', 0, 8, 20, 3, 90, 'Double progression', 'Alternating forward walking lunge.'), ('Lateral Lunge', 'Adductors, Glutes', 'Quads, Hamstrings', 'Lunge', 'Bodyweight', 'Beginner', 'Compound', 1, 8, 15, 3, 75, 'Rep progression', 'Side-to-side frontal-plane lunge.'), ('Step-Down', 'Quads, Glutes', 'Calves, Core', 'Lunge', 'Bodyweight, Box', 'Beginner', 'Compound', 1, 8, 15, 3, 75, 'Rep progression', 'Controlled single-leg step-down.'), ('Dumbbell Romanian Deadlift', 'Hamstrings, Glutes', 'Back, Core', 'Hinge', 'Dumbbells', 'Beginner', 'Compound', 1, 8, 15, 3, 120, 'Double progression', 'Dumbbell hip hinge emphasizing hamstrings.'), ('Cable Pull-Through', 'Glutes, Hamstrings', 'Core', 'Hinge', 'Cable Machine', 'Beginner', 'Compound', 1, 10, 20, 3, 75, 'Double progression', 'Cable hip hinge with low spinal loading.'), ('45-Degree Back Extension', 'Glutes, Hamstrings', 'Lower Back', 'Hip Extension', 'Back Extension Bench', 'Beginner', 'Compound', 1, 10, 20, 3, 75, 'Double progression', 'Hip extension on a 45-degree bench.'), ('Nordic Hamstring Curl', 'Hamstrings', 'Calves, Glutes', 'Knee Flexion', 'Bodyweight', 'Advanced', 'Isolation', 0, 4, 10, 3, 120, 'Rep progression', 'Eccentric-focused bodyweight hamstring curl.'), ('Slider Leg Curl', 'Hamstrings', 'Glutes, Core', 'Knee Flexion', 'Bodyweight', 'Intermediate', 'Isolation', 0, 8, 15, 3, 75, 'Rep progression', 'Supine hamstring curl using sliders.'), ('Frog Pump', 'Glutes', 'Hamstrings', 'Hip Extension', 'Bodyweight', 'Beginner', 'Isolation', 1, 15, 30, 3, 60, 'Rep progression', 'High-rep glute bridge variation.'), ('Cable Hip Abduction', 'Glutes', 'Hip Abductors', 'Hip Abduction', 'Cable Machine', 'Beginner', 'Isolation', 1, 12, 20, 3, 60, 'Double progression', 'Standing cable hip abduction.'), ('Standing Calf Raise Machine', 'Calves', 'Soleus', 'Plantar Flexion', 'Machine', 'Beginner', 'Isolation', 1, 8, 20, 4, 60, 'Double progression', 'Standing machine calf raise.'), ('Donkey Calf Raise', 'Calves', 'Soleus', 'Plantar Flexion', 'Machine', 'Intermediate', 'Isolation', 0, 10, 20, 3, 60, 'Double progression', 'Hip-hinged calf raise variation.'), ('Tibialis Raise', 'Tibialis', 'Calves', 'Dorsiflexion', 'Bodyweight', 'Beginner', 'Isolation', 1, 12, 25, 3, 45, 'Rep progression', 'Toe raise emphasizing tibialis anterior.'), ('Dead Bug', 'Core', 'Hip Flexors', 'Anti-Extension', 'Bodyweight', 'Beginner', 'Core', 1, 8, 16, 3, 45, 'Rep progression', 'Contralateral core stability drill.'), ('Bird Dog', 'Core', 'Glutes, Back', 'Anti-Rotation', 'Bodyweight', 'Beginner', 'Core', 1, 8, 16, 3, 45, 'Rep progression', 'Quadruped contralateral stability drill.'), ('Hollow Body Hold', 'Core', 'Hip Flexors', 'Anti-Extension', 'Bodyweight', 'Intermediate', 'Isometric', 0, 20, 60, 3, 45, 'Time progression', 'Supine hollow-body isometric hold.'), ('Side Plank Hip Lift', 'Obliques', 'Glutes, Core', 'Anti-Lateral Flexion', 'Bodyweight', 'Intermediate', 'Core', 0, 8, 20, 3, 45, 'Rep progression', 'Dynamic side-plank variation.'), ('Cable Wood Chop', 'Obliques', 'Core, Shoulders', 'Rotation', 'Cable Machine', 'Beginner', 'Core', 1, 10, 20, 3, 60, 'Double progression', 'Diagonal cable rotation.'), ('Landmine Rotation', 'Obliques', 'Core, Shoulders', 'Rotation', 'Barbell', 'Intermediate', 'Core', 0, 8, 16, 3, 75, 'Double progression', 'Landmine rotational core movement.'), ('Farmer Carry', 'Grip, Traps', 'Core, Forearms', 'Loaded Carry', 'Dumbbells', 'Beginner', 'Conditioning', 1, 20, 60, 3, 90, 'Distance progression', 'Bilateral loaded carry.'), ('Suitcase Carry', 'Core, Grip', 'Obliques, Forearms', 'Loaded Carry', 'Dumbbells', 'Beginner', 'Conditioning', 1, 20, 60, 3, 90, 'Distance progression', 'Unilateral loaded carry resisting lateral flexion.'), ('Overhead Carry', 'Shoulders, Core', 'Triceps, Grip', 'Loaded Carry', 'Dumbbells', 'Intermediate', 'Conditioning', 0, 20, 60, 3, 90, 'Distance progression', 'Overhead loaded carry for shoulder stability.'), ('Rowing Ergometer Steady State', 'Cardiovascular', 'Back, Quads, Glutes', 'Steady-State Cardio', 'Rowing Machine', 'Beginner', 'Cardio', 1, 20, 60, 1, 0, 'Time progression', 'Steady aerobic rowing session.'), ('Treadmill Incline Walk', 'Cardiovascular', 'Glutes, Calves', 'Steady-State Cardio', 'Treadmill', 'Beginner', 'Cardio', 1, 20, 60, 1, 0, 'Time progression', 'Low-impact incline walking conditioning.'), ('Bike Sprint Intervals', 'Cardiovascular', 'Quads, Glutes', 'Interval Cardio', 'Bike', 'Intermediate', 'Cardio', 0, 10, 30, 1, 0, 'Interval progression', 'Short hard cycling intervals with recovery periods.')]

def ensure_expanded_exercise_directory(db_path=DEFAULT_DB_PATH) -> dict[str, int]:
    """Idempotently add the expanded directory without deleting existing exercises."""
    inserted=0
    substitutions=0
    with session(db_path) as con:
        existing={r["name"].lower():int(r["id"]) for r in con.execute("SELECT id,name FROM exercises")}
        for row in (EXPANDED_EXERCISE_LIBRARY + V14_50_EXERCISE_LIBRARY):
            name=row[0]
            canonical=canonical_exercise_name(name)
            if name != canonical and canonical.lower() in existing:
                continue
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


def _default_form_package(ex):
    pattern=str(ex.get("movement_pattern") or "").lower()
    equipment=str(ex.get("equipment") or "")
    cues=["Move through a controlled range of motion.","Keep your torso and joints stable throughout the rep."]
    setup=[f"Set up the {equipment.lower()} securely." if equipment and equipment.lower()!="bodyweight" else "Use a stable stance and clear training space."]
    mistakes=["Rushing the movement or losing control.","Using a range of motion you cannot control."]
    breathing="Breathe out through the hardest part of the rep and inhale during the easier return."
    if "squat" in pattern:cues=["Brace before descending.","Keep the knees tracking with the toes.","Maintain balanced pressure through the feet."];mistakes=["Knees collapsing inward.","Losing torso position or foot pressure."]
    elif "hinge" in pattern or "hip extension" in pattern:cues=["Brace the trunk before moving.","Push the hips back while keeping the load close.","Finish with the hips without overextending the low back."];mistakes=["Turning the hinge into a squat.","Rounding or hyperextending the spine."]
    elif "horizontal push" in pattern:cues=["Set the shoulder blades before the rep.","Lower under control.","Press while keeping wrists stacked over the forearms."];mistakes=["Flaring the elbows excessively.","Losing shoulder or wrist position."]
    elif "vertical push" in pattern:cues=["Brace the trunk and glutes.","Press smoothly without excessive back arch.","Finish with the arms controlled overhead."];mistakes=["Overarching the low back.","Pressing around an unstable shoulder position."]
    elif "horizontal pull" in pattern:cues=["Start from a stable torso.","Drive the elbow back without shrugging.","Control the reach on the return."];mistakes=["Using momentum from the torso.","Shrugging instead of pulling with the back."]
    elif "vertical pull" in pattern:cues=["Begin from a controlled shoulder position.","Drive the elbows down.","Lower under control to the start."];mistakes=["Swinging or kicking for momentum.","Cutting the range short without a reason."]
    elif "lunge" in pattern:cues=["Keep the front foot planted.","Track the knee with the toes.","Lower under control and drive through the working leg."];mistakes=["Front knee collapsing inward.","Losing balance by using too narrow a stance."]
    elif any(x in pattern for x in ("anti-extension","anti-rotation","anti-lateral","spinal flexion","rotation","hip flexion")):
        cues=["Brace before beginning.","Keep the movement controlled rather than using momentum.","Stop when you can no longer maintain the intended trunk position."];mistakes=["Using momentum instead of the core.","Continuing after trunk position breaks down."];breathing="Keep breathing behind the brace; do not hold your breath for the entire set."
    return {"form_cues":cues,"setup_cues":setup,"common_mistakes":mistakes,"breathing_cue":breathing,"safety_note":"Use a load and range you can control. Stop if the movement causes sharp or unusual pain."}

def ensure_exercise_form_demo_metadata(db_path=DEFAULT_DB_PATH):
    inserted=0
    with session(db_path) as con:
        exercises=[dict(r) for r in con.execute("SELECT * FROM exercises ORDER BY id")]
        for ex in exercises:
            p=_default_form_package(ex)
            cur=con.execute("""INSERT OR IGNORE INTO exercise_form_demos
                (exercise_id,demo_asset,demo_type,demo_version,primary_view,animation_status,form_cues_json,setup_cues_json,common_mistakes_json,breathing_cue,safety_note,reviewed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,0)""",
                (ex["id"],None,"placeholder",1,"side","metadata_ready",_json(p["form_cues"]),_json(p["setup_cues"]),_json(p["common_mistakes"]),p["breathing_cue"],p["safety_note"]))
            inserted+=max(cur.rowcount,0)
    return {"inserted":inserted,"total":len(exercises)}

def get_exercise_form_demo(exercise_id,db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        row=con.execute("""SELECT d.*,e.name,e.primary_muscle,e.secondary_muscles,e.movement_pattern,e.equipment
            FROM exercise_form_demos d JOIN exercises e ON e.id=d.exercise_id WHERE d.exercise_id=?""",(exercise_id,)).fetchone()
    if not row:
        ensure_exercise_form_demo_metadata(db_path)
        with session(db_path) as con:
            row=con.execute("""SELECT d.*,e.name,e.primary_muscle,e.secondary_muscles,e.movement_pattern,e.equipment
                FROM exercise_form_demos d JOIN exercises e ON e.id=d.exercise_id WHERE d.exercise_id=?""",(exercise_id,)).fetchone()
    if not row: raise ValueError("Exercise not found")
    d=dict(row)
    for k in ("form_cues_json","setup_cues_json","common_mistakes_json"):d[k[:-5]]=json.loads(d.pop(k) or "[]")
    d["reviewed"]=bool(d["reviewed"])
    three_d=get_exercise_3d_demo_asset(exercise_id,db_path)
    d["three_d"]=three_d
    d["has_3d"]=bool(three_d and three_d.get("ready"))
    # v14.37 abandons legacy SVG as an instructional animation. SVG can remain
    # archived in the repository but is no longer surfaced as a completed demo.
    d["legacy_vector_asset"]=d.get("demo_asset") if d.get("demo_type")=="svg" else None
    d["has_animation"]=bool(d.get("demo_asset")) and d.get("demo_type") in {"video","mp4","webm","gif","image"}
    return d

BUNDLED_EXERCISE_DEMOS = {'Back Squat': '/assets/exercise_demos/back-squat.svg', 'Barbell Bench Press': '/assets/exercise_demos/barbell-bench-press.svg', 'Romanian Deadlift': '/assets/exercise_demos/romanian-deadlift.svg', 'Barbell Overhead Press': '/assets/exercise_demos/barbell-overhead-press.svg', 'Pull-Up': '/assets/exercise_demos/pull-up.svg', 'Chin-Up': '/assets/exercise_demos/chin-up.svg', 'Lat Pulldown': '/assets/exercise_demos/lat-pulldown.svg', 'Barbell Row': '/assets/exercise_demos/barbell-row.svg', 'One-Arm Dumbbell Row': '/assets/exercise_demos/one-arm-dumbbell-row.svg', 'Push-Up': '/assets/exercise_demos/push-up.svg', 'Leg Press': '/assets/exercise_demos/leg-press.svg', 'Lying Leg Curl': '/assets/exercise_demos/lying-leg-curl.svg', 'Leg Extension': '/assets/exercise_demos/leg-extension.svg', 'Plank': '/assets/exercise_demos/plank.svg', 'Hanging Knee Raise': '/assets/exercise_demos/hanging-knee-raise.svg', 'Front Squat': '/assets/exercise_demos/front-squat.svg', 'Goblet Squat': '/assets/exercise_demos/goblet-squat.svg', 'Bulgarian Split Squat': '/assets/exercise_demos/bulgarian-split-squat.svg', 'Dumbbell Bench Press': '/assets/exercise_demos/dumbbell-bench-press.svg', 'Incline Dumbbell Press': '/assets/exercise_demos/incline-dumbbell-press.svg', 'Machine Chest Press': '/assets/exercise_demos/machine-chest-press.svg', 'Dumbbell Shoulder Press': '/assets/exercise_demos/dumbbell-shoulder-press.svg', 'Seated Dumbbell Shoulder Press': '/assets/exercise_demos/seated-dumbbell-shoulder-press.svg', 'Machine Shoulder Press': '/assets/exercise_demos/machine-shoulder-press.svg', 'Assisted Pull-Up': '/assets/exercise_demos/assisted-pull-up.svg', 'Chest-Supported Row': '/assets/exercise_demos/chest-supported-row.svg', 'Dumbbell Lateral Raise': '/assets/exercise_demos/dumbbell-lateral-raise.svg', 'Cable Lateral Raise': '/assets/exercise_demos/cable-lateral-raise.svg', 'Barbell Curl': '/assets/exercise_demos/barbell-curl.svg', 'Dumbbell Curl': '/assets/exercise_demos/dumbbell-curl.svg', 'Hammer Curl': '/assets/exercise_demos/hammer-curl.svg', 'Cable Curl': '/assets/exercise_demos/cable-curl.svg', 'Triceps Pushdown': '/assets/exercise_demos/triceps-pushdown.svg', 'Overhead Cable Triceps Extension': '/assets/exercise_demos/overhead-cable-triceps-extension.svg', 'Hip Thrust': '/assets/exercise_demos/hip-thrust.svg', 'Glute Bridge': '/assets/exercise_demos/glute-bridge.svg', 'Standing Calf Raise': '/assets/exercise_demos/standing-calf-raise.svg', 'Seated Calf Raise': '/assets/exercise_demos/seated-calf-raise.svg', 'Reverse Crunch': '/assets/exercise_demos/reverse-crunch.svg', 'Side Plank': '/assets/exercise_demos/side-plank.svg', 'Cable Crunch': '/assets/exercise_demos/cable-crunch.svg', 'Pallof Press': '/assets/exercise_demos/pallof-press.svg', 'Ab Wheel Rollout': '/assets/exercise_demos/ab-wheel-rollout.svg'}

def ensure_bundled_exercise_demo_assets(db_path=DEFAULT_DB_PATH):
    """Attach bundled Forge demo assets by exact exercise name without marking them reviewed."""
    updated=0
    with session(db_path) as con:
        for name,asset in BUNDLED_EXERCISE_DEMOS.items():
            row=con.execute("SELECT id FROM exercises WHERE name=?",(name,)).fetchone()
            if not row:
                continue
            demo=con.execute("SELECT demo_asset,demo_type FROM exercise_form_demos WHERE exercise_id=?",(row["id"],)).fetchone()
            # SVGs are now legacy fallbacks. Never replace a registered video/3D asset.
            if demo and demo["demo_asset"]:
                continue
            con.execute("""UPDATE exercise_form_demos
                SET demo_asset=?,demo_type='svg',animation_status='legacy_vector',reviewed=0,
                    updated_at=CURRENT_TIMESTAMP
                WHERE exercise_id=?""",(asset,row["id"]))
            updated += 1
    return {"updated":updated,"bundled":len(BUNDLED_EXERCISE_DEMOS)}

THREE_D_REVIEW_FIELDS=(
    "correct_exercise","equipment_interaction","range_of_motion","joint_path",
    "primary_view","secondary_view","loop_quality","mobile_tested"
)

def get_exercise_3d_demo_asset(exercise_id:int,db_path=DEFAULT_DB_PATH) -> dict[str,Any]|None:
    with session(db_path) as con:
        row=con.execute("SELECT * FROM exercise_demo_3d_assets WHERE exercise_id=?",(exercise_id,)).fetchone()
    if not row:
        return None
    d=dict(row)
    d["ready"]=bool(d.get("primary_webm")) and d.get("status") in {"asset_ready","reviewed"}
    d["has_secondary"]=bool(d.get("secondary_webm"))
    return d

def register_exercise_3d_demo_asset(exercise_id:int,primary_webm:str,
                                    secondary_webm:str|None=None,poster_asset:str|None=None,
                                    primary_view:str="side",secondary_view:str="front",
                                    status:str="asset_ready",db_path=DEFAULT_DB_PATH) -> dict[str,Any]:
    if not primary_webm or not str(primary_webm).lower().endswith(".webm"):
        raise ValueError("Primary 3D demo must be a .webm asset")
    if secondary_webm and not str(secondary_webm).lower().endswith(".webm"):
        raise ValueError("Secondary 3D demo must be a .webm asset")
    if status not in {"planned","asset_ready","reviewed"}:
        raise ValueError("Invalid 3D demo status")
    with session(db_path) as con:
        ex=con.execute("SELECT id FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not ex: raise ValueError("Exercise not found")
        con.execute("""INSERT INTO exercise_demo_3d_assets
            (exercise_id,primary_webm,secondary_webm,poster_asset,primary_view,secondary_view,render_version,status,source_kind,updated_at)
            VALUES (?,?,?,?,?,?,? ,?,'original_3d',CURRENT_TIMESTAMP)
            ON CONFLICT(exercise_id) DO UPDATE SET
              primary_webm=excluded.primary_webm,secondary_webm=excluded.secondary_webm,
              poster_asset=excluded.poster_asset,primary_view=excluded.primary_view,
              secondary_view=excluded.secondary_view,render_version=excluded.render_version,
              status=excluded.status,updated_at=CURRENT_TIMESTAMP""",
            (exercise_id,primary_webm,secondary_webm,poster_asset,primary_view,secondary_view,"forge_3d_v1",status))
        # Make 3D video the primary Form Guide media. Legacy SVG remains stored on disk only.
        con.execute("""UPDATE exercise_form_demos SET demo_asset=?,demo_type='webm',
            secondary_asset=?,primary_view=?,animation_status=?,reviewed=0,
            demo_version=demo_version+1,updated_at=CURRENT_TIMESTAMP
            WHERE exercise_id=?""",
            (primary_webm,secondary_webm,primary_view,status,exercise_id))
    return get_exercise_3d_demo_asset(exercise_id,db_path)

def get_exercise_3d_review(exercise_id:int,db_path=DEFAULT_DB_PATH) -> dict[str,Any]:
    with session(db_path) as con:
        ex=con.execute("SELECT id,name FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not ex: raise ValueError("Exercise not found")
        con.execute("INSERT OR IGNORE INTO exercise_demo_3d_reviews(exercise_id) VALUES (?)",(exercise_id,))
        row=con.execute("SELECT * FROM exercise_demo_3d_reviews WHERE exercise_id=?",(exercise_id,)).fetchone()
        media=con.execute("SELECT secondary_webm FROM exercise_demo_3d_assets WHERE exercise_id=?",(exercise_id,)).fetchone()
    d=dict(row)
    for field in THREE_D_REVIEW_FIELDS:d[field]=bool(d[field])
    # A secondary view is required by the v1 3D standard. No silent pass when absent.
    d["has_secondary_asset"]=bool(media and media["secondary_webm"])
    d["complete"]=all(d[x] for x in THREE_D_REVIEW_FIELDS) and d["has_secondary_asset"]
    d["exercise_name"]=ex["name"]
    return d

def update_exercise_3d_review(exercise_id:int,values:dict[str,Any],db_path=DEFAULT_DB_PATH) -> dict[str,Any]:
    with session(db_path) as con:
        ex=con.execute("SELECT id FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not ex: raise ValueError("Exercise not found")
        con.execute("INSERT OR IGNORE INTO exercise_demo_3d_reviews(exercise_id) VALUES (?)",(exercise_id,))
        for field in THREE_D_REVIEW_FIELDS:
            if field in values:
                con.execute(f"UPDATE exercise_demo_3d_reviews SET {field}=? WHERE exercise_id=?",
                            (1 if values[field] else 0,exercise_id))
        if "notes" in values:
            con.execute("UPDATE exercise_demo_3d_reviews SET notes=? WHERE exercise_id=?",
                        (str(values.get("notes") or ""),exercise_id))
        con.execute("UPDATE exercise_demo_3d_reviews SET updated_at=CURRENT_TIMESTAMP WHERE exercise_id=?",(exercise_id,))
    review=get_exercise_3d_review(exercise_id,db_path)
    with session(db_path) as con:
        media=con.execute("SELECT primary_webm FROM exercise_demo_3d_assets WHERE exercise_id=?",(exercise_id,)).fetchone()
        if media and media["primary_webm"]:
            status="reviewed" if review["complete"] else "asset_ready"
            con.execute("UPDATE exercise_demo_3d_assets SET status=?,updated_at=CURRENT_TIMESTAMP WHERE exercise_id=?",
                        (status,exercise_id))
            con.execute("UPDATE exercise_form_demos SET animation_status=?,reviewed=?,updated_at=CURRENT_TIMESTAMP WHERE exercise_id=?",
                        (status,1 if review["complete"] else 0,exercise_id))
    return get_exercise_3d_review(exercise_id,db_path)

def get_3d_demo_coverage(db_path=DEFAULT_DB_PATH) -> dict[str,Any]:
    with session(db_path) as con:
        total=int(con.execute("SELECT COUNT(*) FROM exercises").fetchone()[0])
        planned=int(con.execute("SELECT COUNT(*) FROM exercise_demo_3d_assets").fetchone()[0])
        ready=int(con.execute("""SELECT COUNT(*) FROM exercise_demo_3d_assets
            WHERE primary_webm IS NOT NULL AND status IN ('asset_ready','reviewed')""").fetchone()[0])
        dual=int(con.execute("""SELECT COUNT(*) FROM exercise_demo_3d_assets
            WHERE primary_webm IS NOT NULL AND secondary_webm IS NOT NULL
              AND status IN ('asset_ready','reviewed')""").fetchone()[0])
        reviewed=int(con.execute("SELECT COUNT(*) FROM exercise_demo_3d_assets WHERE status='reviewed'").fetchone()[0])
    return {"total_exercises":total,"planned":planned,"three_d_ready":ready,"dual_view_ready":dual,
            "reviewed":reviewed,"coverage_percent":round(ready/total*100,1) if total else 0}

def register_exercise_form_demo_asset(exercise_id: int, demo_asset: str, demo_type: str="video",
                                      secondary_asset: str|None=None, reviewed: bool=False,
                                      db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    allowed={"video","mp4","webm","gif","image","svg"}
    if demo_type not in allowed:
        raise ValueError(f"Unsupported demo type: {demo_type}")
    if not demo_asset:
        raise ValueError("demo_asset is required")
    ensure_exercise_form_demo_metadata(db_path)
    with session(db_path) as con:
        exists=con.execute("SELECT id FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not exists: raise ValueError("Exercise not found")
        con.execute("""UPDATE exercise_form_demos
            SET demo_asset=?,demo_type=?,secondary_asset=?,animation_status=?,
                reviewed=?,demo_version=demo_version+1,updated_at=CURRENT_TIMESTAMP
            WHERE exercise_id=?""",
            (demo_asset,demo_type,secondary_asset,"reviewed" if reviewed else "asset_ready",
             1 if reviewed else 0,exercise_id))
    return get_exercise_form_demo(exercise_id,db_path)

DEMO_REVIEW_FIELDS=("correct_exercise","setup","range_of_motion","joint_alignment","loop_quality","mobile_tested")

def get_exercise_demo_review(exercise_id:int,db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        ex=con.execute("SELECT id,name FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not ex: raise ValueError("Exercise not found")
        con.execute("INSERT OR IGNORE INTO exercise_demo_reviews(exercise_id) VALUES (?)",(exercise_id,))
        row=con.execute("SELECT * FROM exercise_demo_reviews WHERE exercise_id=?",(exercise_id,)).fetchone()
    d=dict(row)
    for k in DEMO_REVIEW_FIELDS:d[k]=bool(d[k])
    d["complete"]=all(d[k] for k in DEMO_REVIEW_FIELDS)
    d["exercise_name"]=ex["name"]
    return d

def update_exercise_demo_review(exercise_id:int,values:dict[str,Any],db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        ex=con.execute("SELECT id FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not ex: raise ValueError("Exercise not found")
        con.execute("INSERT OR IGNORE INTO exercise_demo_reviews(exercise_id) VALUES (?)",(exercise_id,))
        for k in DEMO_REVIEW_FIELDS:
            if k in values: con.execute(f"UPDATE exercise_demo_reviews SET {k}=? WHERE exercise_id=?",(1 if values[k] else 0,exercise_id))
        if "notes" in values: con.execute("UPDATE exercise_demo_reviews SET notes=? WHERE exercise_id=?",(str(values.get("notes") or ""),exercise_id))
        con.execute("UPDATE exercise_demo_reviews SET updated_at=CURRENT_TIMESTAMP WHERE exercise_id=?",(exercise_id,))
        row=con.execute("SELECT * FROM exercise_demo_reviews WHERE exercise_id=?",(exercise_id,)).fetchone()
        complete=all(bool(row[k]) for k in DEMO_REVIEW_FIELDS)
        demo=con.execute("SELECT demo_asset FROM exercise_form_demos WHERE exercise_id=?",(exercise_id,)).fetchone()
        if demo and demo["demo_asset"]:
            con.execute("UPDATE exercise_form_demos SET reviewed=?,animation_status=?,updated_at=CURRENT_TIMESTAMP WHERE exercise_id=?",
                        (1 if complete else 0,"reviewed" if complete else "asset_ready",exercise_id))
    return get_exercise_demo_review(exercise_id,db_path)

def audit_exercise_form_demos(db_path=DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    ensure_exercise_form_demo_metadata(db_path)
    with session(db_path) as con:
        rows=con.execute("""SELECT e.id,e.name,e.primary_muscle,e.equipment,d.demo_asset,d.demo_type,
            d.animation_status,d.reviewed,d.form_cues_json,d.setup_cues_json,d.common_mistakes_json
            FROM exercises e LEFT JOIN exercise_form_demos d ON d.exercise_id=e.id ORDER BY e.name""").fetchall()
    out=[]
    for r in rows:
        d=dict(r)
        three_d=get_exercise_3d_demo_asset(d["id"],db_path)
        d["three_d"]=three_d
        d["has_3d"]=bool(three_d and three_d.get("ready"))
        d["has_animation"]=bool(d.get("demo_asset")) and d.get("demo_type") in {"video","mp4","webm","gif","image"}
        d["reviewed"]=bool(d.get("reviewed")) and d["has_3d"]
        try:d["review"]=get_exercise_demo_review(d["id"],db_path)
        except Exception:d["review"]=None
        d["has_form_cues"]=bool(json.loads(d.get("form_cues_json") or "[]"))
        d["has_setup_cues"]=bool(json.loads(d.get("setup_cues_json") or "[]"))
        d["has_mistakes"]=bool(json.loads(d.get("common_mistakes_json") or "[]"))
        for k in ("form_cues_json","setup_cues_json","common_mistakes_json"): d.pop(k,None)
        out.append(d)
    return out

def get_exercise_demo_coverage(db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        total=con.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
        metadata=con.execute("SELECT COUNT(*) FROM exercise_form_demos").fetchone()[0]
        animations=con.execute("SELECT COUNT(*) FROM exercise_form_demos WHERE demo_asset IS NOT NULL AND demo_type!='placeholder'").fetchone()[0]
        reviewed=con.execute("SELECT COUNT(*) FROM exercise_form_demos WHERE reviewed=1").fetchone()[0]
    return {"total_exercises":total,"metadata_ready":metadata,"animations_ready":animations,"reviewed":reviewed,"coverage_percent":round(animations/total*100,1) if total else 0}

def _is_bodyweight_loaded_exercise(exercise: dict[str, Any]) -> bool:
    """True when body mass is the primary resistance even if equipment is required."""
    name=str(exercise.get("name") or "").lower()
    equipment=str(exercise.get("equipment") or "").lower()
    if "bodyweight" in equipment:
        return True
    if any(x in name for x in ("assisted pull-up","assisted dip","machine dip")):
        return False
    patterns=(
        "pull-up","pull up","chin-up","chin up","scapular pull-up",
        "bench dip","hanging knee raise","hanging leg raise",
        "inverted row","muscle-up","muscle up"
    )
    return any(x in name for x in patterns)


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
    bodyweight = _is_bodyweight_loaded_exercise(exercise)
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
        "movement_plane":("sagittal" if pattern in {"Squat","Hinge","Vertical Push","Vertical Pull","Elbow Flexion","Elbow Extension","Knee Flexion","Hip Extension","Plantar Flexion","Dorsiflexion"} else "transverse" if pattern in {"Horizontal Push","Horizontal Pull","Rotation"} else "frontal" if pattern in {"Lunge","Hip Abduction","Anti-Lateral Flexion"} else "mixed"),
        "programming_roles":[x for x,yes in (("strength",strength>=4),("hypertrophy",hypertrophy>=4),("conditioning",conditioning>=4),("low_fatigue",fatigue<=2),("beginner_friendly",difficulty=="Beginner")) if yes],
        "recovery_cost":"high" if fatigue>=4 else "moderate" if fatigue==3 else "low",
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
        muscle_links={}
        for r in con.execute("SELECT exercise_id,muscle_group,sub_muscle,role FROM exercise_muscles"):
            muscle_links.setdefault(int(r["exercise_id"]),[]).append(dict(r))

    prefs={}
    if user_id:
        with session(db_path) as con:
            prefs={int(r["exercise_id"]):dict(r) for r in con.execute(
                "SELECT exercise_id,preference,notes FROM user_exercise_preferences WHERE user_id=?",
                (user_id,),
            ).fetchall()}

    q=(search or "").strip().lower()
    canonical_names={canonical_exercise_name(r["name"]).lower() for r in rows}
    out=[]
    seen_canonical=set()
    for d in rows:
        canonical=canonical_exercise_name(d["name"])
        key=canonical.lower()
        if key in seen_canonical:
            continue
        # Prefer the canonical database row when both old aliases still exist.
        if d["name"] != canonical and canonical.lower() in {r["name"].lower() for r in rows}:
            continue
        d["name"]=canonical
        seen_canonical.add(key)
        d["beginner_suitable"]=bool(d["beginner_suitable"])
        d["equipment_compatible"]=_equipment_allowed(d["equipment"],profile_equipment) if user_id else True
        d["muscle_links"]=muscle_links.get(int(d["id"]),[])
        d["muscle_groups"]=sorted({x["muscle_group"] for x in d["muscle_links"]})
        d["sub_muscles"]=sorted({x["sub_muscle"] for x in d["muscle_links"]})
        d.update(_exercise_intelligence_metadata(d))
        pref=prefs.get(int(d["id"]),{})
        d["user_preference"]=pref.get("preference","neutral")
        d["preference_notes"]=pref.get("notes")
        if q and q not in (" ".join(str(d.get(k,"")) for k in
            ("name","primary_muscle","secondary_muscles","movement_pattern","equipment")) + " " + " ".join(d.get("sub_muscles",[]))).lower():
            continue
        if muscle and muscle!="All" and muscle.lower() not in " ".join(d.get("muscle_groups",[])+d.get("sub_muscles",[])).lower():
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

    muscles=sorted({x for r in rows for x in ([r.get("primary_muscle","")] + [m["sub_muscle"] for m in muscle_links.get(int(r["id"]),[])]) if x})
    equipment_values=sorted({r["equipment"] for r in rows})
    difficulties=sorted({r["difficulty"] for r in rows})
    movements=sorted({r["movement_pattern"] for r in rows})
    return {
        "exercises":out,
        "total_matches":len(out),
        "directory_total":len({canonical_exercise_name(r["name"]).lower() for r in rows}),
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
    with session(db_path) as con:
        links=[dict(r) for r in con.execute("SELECT muscle_group,sub_muscle,role FROM exercise_muscles WHERE exercise_id=? ORDER BY role,muscle_group,sub_muscle",(exercise_id,))]
    d["muscle_links"]=links; d["muscle_groups"]=sorted({x["muscle_group"] for x in links}); d["sub_muscles"]=sorted({x["sub_muscle"] for x in links})
    d.update(_exercise_intelligence_metadata(d))
    pref=get_user_exercise_preference(user_id,exercise_id,db_path) if user_id else {"preference":"neutral","notes":None}
    d["user_preference"]=pref.get("preference","neutral")
    d["preference_notes"]=pref.get("notes")
    return d

# v14.51-v14.53 daily-use editing helpers
def _owned_workout_context(user_id, workout_id, db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        row=con.execute("""SELECT w.id,w.workout_index,pw.id AS week_id,pw.plan_json FROM workouts w JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id WHERE w.id=? AND p.user_id=?""",(workout_id,user_id)).fetchone()
    if not row: raise ValueError("Workout not found")
    return dict(row)

def _sync_workout_plan(con, ctx, workout_id):
    plan=json.loads(ctx["plan_json"]); wi=int(ctx["workout_index"])
    rows=con.execute("""SELECT we.*,e.name,e.primary_muscle,e.secondary_muscles,e.equipment,e.exercise_type FROM workout_exercises we JOIN exercises e ON e.id=we.exercise_id WHERE we.workout_id=? ORDER BY we.exercise_order""",(workout_id,)).fetchall()
    plan["workouts"][wi]["exercises"]=[dict(r) for r in rows]
    con.execute("UPDATE program_weeks SET plan_json=? WHERE id=?",(_json(plan),ctx["week_id"]))

def add_workout_exercise(user_id, workout_id, exercise_id, db_path=DEFAULT_DB_PATH):
    ctx=_owned_workout_context(user_id,workout_id,db_path)
    with session(db_path) as con:
        e=con.execute("SELECT * FROM exercises WHERE id=?",(exercise_id,)).fetchone()
        if not e: raise ValueError("Exercise not found")
        if con.execute("SELECT 1 FROM workout_exercises WHERE workout_id=? AND exercise_id=?",(workout_id,exercise_id)).fetchone(): raise ValueError("Exercise already in workout")
        order=con.execute("SELECT COALESCE(MAX(exercise_order),-1)+1 n FROM workout_exercises WHERE workout_id=?",(workout_id,)).fetchone()["n"]
        con.execute("INSERT INTO workout_exercises(workout_id,exercise_id,exercise_order,sets,min_reps,max_reps,rest_seconds,progression_method) VALUES(?,?,?,?,?,?,?,?)",(workout_id,exercise_id,order,e["default_sets"],e["min_reps"],e["max_reps"],e["default_rest_seconds"],e["progression_method"]))
        _sync_workout_plan(con,ctx,workout_id)
    return {"status":"added","exercise_id":exercise_id}

def edit_workout_exercise(user_id,workout_id,exercise_id,data,db_path=DEFAULT_DB_PATH):
    ctx=_owned_workout_context(user_id,workout_id,db_path)
    sets=max(1,min(12,int(data["sets"]))); mn=max(1,int(data["min_reps"])); mx=max(mn,int(data["max_reps"])); rest=max(15,min(600,int(data["rest_seconds"])))
    with session(db_path) as con:
        cur=con.execute("UPDATE workout_exercises SET sets=?,min_reps=?,max_reps=?,rest_seconds=? WHERE workout_id=? AND exercise_id=?",(sets,mn,mx,rest,workout_id,exercise_id))
        if not cur.rowcount: raise ValueError("Exercise not found in workout")
        _sync_workout_plan(con,ctx,workout_id)
    return {"status":"updated"}

def remove_workout_exercise(user_id,workout_id,exercise_id,db_path=DEFAULT_DB_PATH):
    ctx=_owned_workout_context(user_id,workout_id,db_path)
    with session(db_path) as con:
        count=con.execute("SELECT COUNT(*) n FROM workout_exercises WHERE workout_id=?",(workout_id,)).fetchone()["n"]
        if count<=1: raise ValueError("A workout must keep at least one exercise")
        con.execute("DELETE FROM workout_exercises WHERE workout_id=? AND exercise_id=?",(workout_id,exercise_id))
        rows=con.execute("SELECT id FROM workout_exercises WHERE workout_id=? ORDER BY exercise_order",(workout_id,)).fetchall()
        for i,r in enumerate(rows): con.execute("UPDATE workout_exercises SET exercise_order=? WHERE id=?",(i,r["id"]))
        _sync_workout_plan(con,ctx,workout_id)
    return {"status":"removed"}

def reorder_workout_exercises(user_id,workout_id,exercise_ids,db_path=DEFAULT_DB_PATH):
    ctx=_owned_workout_context(user_id,workout_id,db_path)
    with session(db_path) as con:
        existing=[r["exercise_id"] for r in con.execute("SELECT exercise_id FROM workout_exercises WHERE workout_id=? ORDER BY exercise_order",(workout_id,)).fetchall()]
        if sorted(map(int,exercise_ids))!=sorted(map(int,existing)): raise ValueError("Reorder list must contain every workout exercise")
        for i,eid in enumerate(exercise_ids): con.execute("UPDATE workout_exercises SET exercise_order=? WHERE workout_id=? AND exercise_id=?",(i,workout_id,int(eid)))
        _sync_workout_plan(con,ctx,workout_id)
    return {"status":"reordered"}


def preview_move_workout_exercise(user_id:int, source_workout_id:int, exercise_id:int, target_workout_id:int, db_path=DEFAULT_DB_PATH):
    if int(source_workout_id)==int(target_workout_id): raise ValueError('Choose a different workout')
    with session(db_path) as con:
        rows=con.execute("""SELECT w.id,w.name,w.workout_index,pw.id AS week_id
            FROM workouts w JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND p.status='active' AND w.id IN (?,?)""",(user_id,source_workout_id,target_workout_id)).fetchall()
        by={int(r['id']):dict(r) for r in rows}
        if source_workout_id not in by or target_workout_id not in by: raise ValueError('Both workouts must belong to the active plan')
        if by[source_workout_id]['week_id']!=by[target_workout_id]['week_id']: raise ValueError('Exercises can only move inside the current program week')
        src=con.execute("""SELECT we.*,e.name,e.primary_muscle,e.secondary_muscles FROM workout_exercises we JOIN exercises e ON e.id=we.exercise_id
            WHERE we.workout_id=? AND we.exercise_id=?""",(source_workout_id,exercise_id)).fetchone()
        if not src: raise ValueError('Exercise is not part of the source workout')
        count=int(con.execute('SELECT COUNT(*) n FROM workout_exercises WHERE workout_id=?',(source_workout_id,)).fetchone()['n'])
        if count<=1: raise ValueError('A workout must keep at least one exercise')
        if con.execute('SELECT 1 FROM workout_exercises WHERE workout_id=? AND exercise_id=?',(target_workout_id,exercise_id)).fetchone(): raise ValueError('Target workout already contains this exercise')
        locks=get_plan_exercise_locks(user_id,db_path)
        if int(exercise_id) in locks.get(int(by[source_workout_id]['workout_index']),[]): raise ValueError('Unlock this exercise before moving it')
        target_count=int(con.execute('SELECT COUNT(*) n FROM workout_exercises WHERE workout_id=?',(target_workout_id,)).fetchone()['n'])
        links=con.execute('SELECT muscle_group,sub_muscle,role FROM exercise_muscles WHERE exercise_id=?',(exercise_id,)).fetchall()
        impact=[{'muscle':r['muscle_group'],'submuscle':r['sub_muscle'],'set_equivalents':round(float(src['sets'])*(1.0 if r['role']=='primary' else .5),1)} for r in links]
        return {'source':by[source_workout_id],'target':by[target_workout_id],'exercise':dict(src),'weekly_volume_change':0,'target_exercise_count_before':target_count,'target_exercise_count_after':target_count+1,'source_exercise_count_after':count-1,'muscle_impact':impact,'warning':'Weekly set volume is unchanged, but training-day distribution and recovery spacing will change.'}

def move_workout_exercise(user_id:int, source_workout_id:int, exercise_id:int, target_workout_id:int, db_path=DEFAULT_DB_PATH):
    preview=preview_move_workout_exercise(user_id,source_workout_id,exercise_id,target_workout_id,db_path)
    with session(db_path) as con:
        row=con.execute('SELECT * FROM workout_exercises WHERE workout_id=? AND exercise_id=?',(source_workout_id,exercise_id)).fetchone()
        target_order=int(con.execute('SELECT COALESCE(MAX(exercise_order),-1)+1 n FROM workout_exercises WHERE workout_id=?',(target_workout_id,)).fetchone()['n'])
        con.execute('UPDATE workout_exercises SET workout_id=?,exercise_order=? WHERE id=?',(target_workout_id,target_order,row['id']))
        for wid in (source_workout_id,target_workout_id):
            rows=con.execute('SELECT id FROM workout_exercises WHERE workout_id=? ORDER BY exercise_order,id',(wid,)).fetchall()
            for i,r in enumerate(rows): con.execute('UPDATE workout_exercises SET exercise_order=? WHERE id=?',(i,r['id']))
        week_id=preview['source']['week_id']; prow=con.execute('SELECT plan_json FROM program_weeks WHERE id=?',(week_id,)).fetchone(); plan=json.loads(prow['plan_json'])
        for wid in (source_workout_id,target_workout_id):
            wr=con.execute('SELECT workout_index FROM workouts WHERE id=?',(wid,)).fetchone(); wi=int(wr['workout_index'])
            erows=con.execute("""SELECT we.*,e.name,e.primary_muscle,e.secondary_muscles,e.movement_pattern,e.equipment,e.difficulty,e.exercise_type
                FROM workout_exercises we JOIN exercises e ON e.id=we.exercise_id WHERE we.workout_id=? ORDER BY we.exercise_order""",(wid,)).fetchall()
            plan['workouts'][wi]['exercises']=[dict(x) for x in erows]
        con.execute('UPDATE program_weeks SET plan_json=? WHERE id=?',(_json(plan),week_id))
        con.execute("""INSERT INTO progression_events(user_id,exercise_id,workout_id,event_type,old_value,new_value,reason)
            VALUES (?,?,?,?,?,?,?)""",(user_id,exercise_id,target_workout_id,'plan_editor_move',str(source_workout_id),str(target_workout_id),'User moved exercise in Plan Editor 2.0'))
    return {'status':'moved',**preview}

def copy_previous_nutrition_day(user_id,target_date,db_path=DEFAULT_DB_PATH):
    from datetime import date,timedelta
    target=date.fromisoformat(target_date); source=(target-timedelta(days=1)).isoformat()
    with session(db_path) as con:
        rows=con.execute("SELECT * FROM nutrition_entries WHERE user_id=? AND entry_date=? ORDER BY id",(user_id,source)).fetchall()
        for r in rows:
            con.execute("INSERT INTO nutrition_entries(user_id,entry_date,meal_type,food_name,calories,protein_g,carbs_g,fat_g,source,source_url) VALUES(?,?,?,?,?,?,?,?,?,?)",(user_id,target_date,r["meal_type"],r["food_name"],r["calories"],r["protein_g"],r["carbs_g"],r["fat_g"],r["source"],r["source_url"]))
    return {"status":"copied","source_date":source,"entry_date":target_date,"entries_copied":len(rows)}

def ensure_training_strategy_state(db_path=DEFAULT_DB_PATH):
    with session(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS training_strategy_state (
          user_id INTEGER PRIMARY KEY, strategy TEXT NOT NULL DEFAULT 'hypertrophy_accumulation',
          rationale TEXT NOT NULL DEFAULT '', specialization_json TEXT NOT NULL DEFAULT '[]',
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS programming_authority (
          user_id INTEGER NOT NULL, domain TEXT NOT NULL, mode TEXT NOT NULL DEFAULT 'recommend_only',
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id,domain))""")

def get_training_strategy_state(user_id,db_path=DEFAULT_DB_PATH):
    ensure_training_strategy_state(db_path)
    with session(db_path) as con:r=con.execute('SELECT * FROM training_strategy_state WHERE user_id=?',(user_id,)).fetchone()
    if not r:return {'strategy':'hypertrophy_accumulation','rationale':'','specialization':[]}
    d=dict(r)
    try:d['specialization']=json.loads(d.pop('specialization_json') or '[]')
    except Exception:d['specialization']=[]
    return d

def save_training_strategy_state(user_id,strategy,rationale='',specialization=None,db_path=DEFAULT_DB_PATH):
    ensure_training_strategy_state(db_path); specialization=list(specialization or [])[:2]
    with session(db_path) as con:
        con.execute("""INSERT INTO training_strategy_state(user_id,strategy,rationale,specialization_json,updated_at)
        VALUES(?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET strategy=excluded.strategy,rationale=excluded.rationale,
        specialization_json=excluded.specialization_json,updated_at=CURRENT_TIMESTAMP""",(user_id,strategy,rationale,_json(specialization)))
    return get_training_strategy_state(user_id,db_path)

def get_programming_authority(user_id,db_path=DEFAULT_DB_PATH):
    ensure_training_strategy_state(db_path)
    domains=['session_load','rest_times','set_count','exercise_substitutions','weekly_volume','workout_scheduling','deload_timing']
    with session(db_path) as con:rows=con.execute('SELECT domain,mode FROM programming_authority WHERE user_id=?',(user_id,)).fetchall()
    found={r['domain']:r['mode'] for r in rows}; return {d:found.get(d,'recommend_only') for d in domains}

def save_programming_authority(user_id,values,db_path=DEFAULT_DB_PATH):
    ensure_training_strategy_state(db_path); valid={'recommend_only','ask_first','auto_apply'}
    current=get_programming_authority(user_id,db_path)
    with session(db_path) as con:
        for d,v in dict(values or {}).items():
            if d in current and v in valid:con.execute("INSERT INTO programming_authority(user_id,domain,mode,updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id,domain) DO UPDATE SET mode=excluded.mode,updated_at=CURRENT_TIMESTAMP",(user_id,d,v))
    return get_programming_authority(user_id,db_path)

def get_data_integrity_report(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    """v15.7 Forge Health Check. Read-only audit of recoverable and review-only data problems."""
    issues=[]
    def add(code,severity,count,repairable,detail):
        if count: issues.append({"code":code,"severity":severity,"count":int(count),"repairable":bool(repairable),"detail":detail})
    with session(db_path) as con:
        active_programs=int(con.execute("SELECT COUNT(*) FROM programs WHERE user_id=? AND status='active'",(user_id,)).fetchone()[0])
        add("multiple_active_programs","high",max(0,active_programs-1),False,"More than one program is active; Forge will not choose one automatically.")
        stale=int(con.execute("""SELECT COUNT(*) FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND ws.status='active' AND p.status!='active'""",(user_id,)).fetchone()[0])
        add("stale_active_sessions","medium",stale,True,"Active sessions attached to replaced programs can be safely abandoned.")
        dup=int(con.execute("""SELECT COUNT(*) FROM (SELECT ws.workout_id,COUNT(*) c FROM workout_sessions ws
            JOIN workouts w ON w.id=ws.workout_id JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id WHERE p.user_id=? AND p.status='active' AND ws.status='active'
            GROUP BY ws.workout_id HAVING c>1)""",(user_id,)).fetchone()[0])
        add("duplicate_active_sessions","medium",dup,True,"Only the newest active session for a workout should remain active.")
        orphan_state=int(con.execute("""SELECT COUNT(*) FROM session_state ss LEFT JOIN workout_sessions ws ON ws.id=ss.session_id
            WHERE ws.id IS NULL""").fetchone()[0])
        add("orphan_session_state","low",orphan_state,True,"Session-state rows without a workout session can be removed.")
        bad_positions=int(con.execute("""SELECT COUNT(*) FROM session_state ss JOIN workout_sessions ws ON ws.id=ss.session_id
            JOIN workouts w ON w.id=ws.workout_id JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND (ss.current_exercise_index<0 OR ss.current_set_index<0 OR
            ss.current_exercise_index >= (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id=w.id))""",(user_id,)).fetchone()[0])
        add("invalid_session_position","medium",bad_positions,True,"Workout position is outside the current workout and can be reconciled.")
        empty_workouts=int(con.execute("""SELECT COUNT(*) FROM workouts w JOIN program_weeks pw ON pw.id=w.program_week_id
            JOIN programs p ON p.id=pw.program_id WHERE p.user_id=? AND p.status='active'
            AND NOT EXISTS(SELECT 1 FROM workout_exercises we WHERE we.workout_id=w.id)""",(user_id,)).fetchone()[0])
        add("empty_active_workouts","high",empty_workouts,False,"An active-plan workout has no exercises and needs plan review.")
        malformed=0
        rows=con.execute("""SELECT pw.plan_json FROM program_weeks pw JOIN programs p ON p.id=pw.program_id WHERE p.user_id=?""",(user_id,)).fetchall()
        for row in rows:
            try: json.loads(row["plan_json"] or "{}")
            except Exception: malformed+=1
        add("malformed_plan_json","high",malformed,False,"Stored plan JSON is malformed; Forge will not overwrite it automatically.")
    return {"version":"1.0","status":"healthy" if not issues else "repairable" if all(x["repairable"] for x in issues) else "review",
            "issues":issues,"repairable_count":sum(x["count"] for x in issues if x["repairable"]),
            "review_count":sum(x["count"] for x in issues if not x["repairable"]),
            "rule":"Forge auto-repairs only state that can be reconstructed without changing training history or choosing between valid programs."}

def repair_data_integrity(user_id: int, db_path=DEFAULT_DB_PATH) -> dict[str, Any]:
    """Apply only deterministic, non-destructive v15.7 repairs."""
    repaired={"stale_sessions_abandoned":0,"duplicate_sessions_abandoned":0,"orphan_session_state_removed":0,"positions_reconciled":0}
    with session(db_path) as con:
        stale=con.execute("""SELECT ws.id FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND ws.status='active' AND p.status!='active'""",(user_id,)).fetchall()
        for row in stale:
            con.execute("UPDATE workout_sessions SET status='abandoned',completed_at=COALESCE(completed_at,CURRENT_TIMESTAMP) WHERE id=?",(row["id"],))
            repaired["stale_sessions_abandoned"]+=1
        groups=con.execute("""SELECT ws.workout_id,MAX(ws.id) keep_id FROM workout_sessions ws JOIN workouts w ON w.id=ws.workout_id
            JOIN program_weeks pw ON pw.id=w.program_week_id JOIN programs p ON p.id=pw.program_id
            WHERE p.user_id=? AND p.status='active' AND ws.status='active' GROUP BY ws.workout_id HAVING COUNT(*)>1""",(user_id,)).fetchall()
        for g in groups:
            cur=con.execute("UPDATE workout_sessions SET status='abandoned',completed_at=COALESCE(completed_at,CURRENT_TIMESTAMP) WHERE workout_id=? AND status='active' AND id<>?",(g["workout_id"],g["keep_id"]))
            repaired["duplicate_sessions_abandoned"]+=max(0,cur.rowcount)
        cur=con.execute("DELETE FROM session_state WHERE session_id NOT IN (SELECT id FROM workout_sessions)")
        repaired["orphan_session_state_removed"]=max(0,cur.rowcount)
    before=get_session_diagnostics(user_id,db_path)
    sync=reconcile_active_session(user_id,None,db_path)
    if sync.get("status")=="ok": repaired["positions_reconciled"]=1
    return {"status":"repaired","repairs":repaired,"session":sync,"report":get_data_integrity_report(user_id,db_path)}
