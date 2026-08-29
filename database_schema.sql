PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    goal TEXT NOT NULL,
    experience TEXT NOT NULL,
    days_per_week INTEGER NOT NULL,
    minutes_per_workout INTEGER NOT NULL,
    equipment_json TEXT NOT NULL DEFAULT '[]',
    preferred_exercises_json TEXT NOT NULL DEFAULT '[]',
    excluded_exercises_json TEXT NOT NULL DEFAULT '[]',
    priority_muscles_json TEXT NOT NULL DEFAULT '[]',
    recovery_level TEXT NOT NULL DEFAULT 'normal',
    cardio_preference TEXT NOT NULL DEFAULT 'moderate',
    workout_split TEXT NOT NULL DEFAULT 'auto',
    custom_split_json TEXT NOT NULL DEFAULT '[]',
    sport TEXT NOT NULL DEFAULT 'general',
    core_workouts_per_week INTEGER NOT NULL DEFAULT 2,
    cardio_workouts_per_week INTEGER NOT NULL DEFAULT 2,
    exercises_per_day INTEGER NOT NULL DEFAULT 6,
    seed INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    current_week INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS program_weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    recommendation TEXT,
    fatigue_score REAL NOT NULL DEFAULT 0,
    completion_rate REAL NOT NULL DEFAULT 1,
    consecutive_hard_weeks INTEGER NOT NULL DEFAULT 0,
    missed_workouts INTEGER NOT NULL DEFAULT 0,
    plan_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(program_id, week_number),
    FOREIGN KEY(program_id) REFERENCES programs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_week_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    workout_index INTEGER NOT NULL,
    estimated_minutes INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    started_at TEXT,
    completed_at TEXT,
    notes TEXT,
    FOREIGN KEY(program_week_id) REFERENCES program_weeks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    exercise_order INTEGER NOT NULL,
    sets INTEGER NOT NULL,
    min_reps INTEGER NOT NULL,
    max_reps INTEGER NOT NULL,
    rest_seconds INTEGER NOT NULL,
    progression_method TEXT,
    FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id)
);

CREATE TABLE IF NOT EXISTS workout_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT,
    completed_at TEXT,
    notes TEXT,
    FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercise_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    completed_sets INTEGER NOT NULL DEFAULT 0,
    reps_json TEXT NOT NULL DEFAULT '[]',
    difficulty REAL,
    skipped INTEGER,
    weight REAL,
    duration_seconds INTEGER,
    load_mode TEXT NOT NULL DEFAULT 'weight',
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES workout_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id)
);

CREATE TABLE IF NOT EXISTS training_state (
    user_id INTEGER PRIMARY KEY,
    week_number INTEGER NOT NULL DEFAULT 1,
    consecutive_hard_weeks INTEGER NOT NULL DEFAULT 0,
    missed_workouts INTEGER NOT NULL DEFAULT 0,
    fatigue_score REAL NOT NULL DEFAULT 0,
    completion_rate REAL NOT NULL DEFAULT 1,
    exercise_history_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS progression_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exercise_id INTEGER,
    workout_id INTEGER,
    event_type TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id),
    FOREIGN KEY(workout_id) REFERENCES workouts(id)
);

CREATE INDEX IF NOT EXISTS idx_programs_user ON programs(user_id);
CREATE INDEX IF NOT EXISTS idx_weeks_program ON program_weeks(program_id, week_number);
CREATE INDEX IF NOT EXISTS idx_workouts_week ON workouts(program_week_id, workout_index);
CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout ON workout_exercises(workout_id, exercise_order);
CREATE INDEX IF NOT EXISTS idx_performance_session ON exercise_performance(session_id);
CREATE INDEX IF NOT EXISTS idx_performance_exercise ON exercise_performance(exercise_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_progression_user ON progression_events(user_id, created_at);


CREATE TABLE IF NOT EXISTS user_accounts (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions(token_hash);


CREATE TABLE IF NOT EXISTS session_state (
    session_id INTEGER PRIMARY KEY,
    current_exercise_index INTEGER NOT NULL DEFAULT 0,
    current_set_index INTEGER NOT NULL DEFAULT 0,
    rest_started_at TEXT,
    rest_duration_seconds INTEGER,
    feedback TEXT,
    abandoned_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES workout_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS set_log_requests (
    request_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    performance_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(session_id) REFERENCES workout_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id),
    FOREIGN KEY(performance_id) REFERENCES exercise_performance(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_set_log_requests_session ON set_log_requests(session_id);


CREATE TABLE IF NOT EXISTS coach_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
    message TEXT NOT NULL,
    action_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_coach_messages_user_created
ON coach_messages(user_id, created_at);


CREATE TABLE IF NOT EXISTS workout_schedule (
    workout_id INTEGER PRIMARY KEY,
    scheduled_day INTEGER NOT NULL CHECK(scheduled_day BETWEEN 0 AND 6),
    original_day INTEGER NOT NULL CHECK(original_day BETWEEN 0 AND 6),
    is_skipped INTEGER NOT NULL DEFAULT 0,
    scheduled_time TEXT NOT NULL DEFAULT '17:00',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workout_schedule_day
ON workout_schedule(scheduled_day);


CREATE TABLE IF NOT EXISTS user_equipment_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    equipment_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Other',
    details_json TEXT NOT NULL DEFAULT '{}',
    is_custom INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, equipment_key),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_equipment_log_user
ON user_equipment_log(user_id);


CREATE TABLE IF NOT EXISTS exercise_substitutions (
    exercise_id INTEGER NOT NULL,
    substitute_exercise_id INTEGER NOT NULL,
    reason TEXT,
    PRIMARY KEY(exercise_id, substitute_exercise_id),
    FOREIGN KEY(exercise_id) REFERENCES exercises(id),
    FOREIGN KEY(substitute_exercise_id) REFERENCES exercises(id)
);

CREATE INDEX IF NOT EXISTS idx_exercise_substitutions_exercise
ON exercise_substitutions(exercise_id);

CREATE TABLE IF NOT EXISTS user_exercise_preferences (
    user_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    preference TEXT NOT NULL DEFAULT 'neutral'
        CHECK(preference IN ('neutral','favorite','avoid','painful')),
    notes TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, exercise_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_exercise_preferences_user
ON user_exercise_preferences(user_id);


CREATE TABLE IF NOT EXISTS user_time_settings (
    user_id INTEGER PRIMARY KEY,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    utc_offset_minutes INTEGER NOT NULL DEFAULT 0,
    default_workout_time TEXT NOT NULL DEFAULT '17:00',
    calendar_sync_enabled INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS google_calendar_connections (
    user_id INTEGER PRIMARY KEY,
    calendar_id TEXT NOT NULL DEFAULT 'primary',
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TEXT,
    scope TEXT,
    google_email TEXT,
    connected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS calendar_oauth_states (
    state TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    return_url TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workout_calendar_links (
    workout_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    google_event_id TEXT NOT NULL,
    google_calendar_id TEXT NOT NULL DEFAULT 'primary',
    last_google_updated TEXT,
    last_forge_signature TEXT,
    last_synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workout_calendar_links_user
ON workout_calendar_links(user_id);


CREATE TABLE IF NOT EXISTS nutrition_targets (
    user_id INTEGER PRIMARY KEY,
    calories INTEGER NOT NULL DEFAULT 2200,
    protein_g INTEGER NOT NULL DEFAULT 150,
    carbs_g INTEGER NOT NULL DEFAULT 250,
    fat_g INTEGER NOT NULL DEFAULT 70,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS nutrition_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    meal_type TEXT NOT NULL DEFAULT 'Meal',
    food_name TEXT NOT NULL,
    calories INTEGER NOT NULL DEFAULT 0,
    protein_g REAL NOT NULL DEFAULT 0,
    carbs_g REAL NOT NULL DEFAULT 0,
    fat_g REAL NOT NULL DEFAULT 0,
    source TEXT,
    source_url TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nutrition_entries_user_date
ON nutrition_entries(user_id, entry_date);


CREATE TABLE IF NOT EXISTS nutrition_saved_foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    normalized_name TEXT NOT NULL,
    food_name TEXT NOT NULL,
    calories INTEGER NOT NULL DEFAULT 0,
    protein_g REAL NOT NULL DEFAULT 0,
    carbs_g REAL NOT NULL DEFAULT 0,
    fat_g REAL NOT NULL DEFAULT 0,
    source TEXT,
    source_url TEXT,
    is_favorite INTEGER NOT NULL DEFAULT 0,
    use_count INTEGER NOT NULL DEFAULT 1,
    last_used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, normalized_name),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nutrition_saved_foods_user
ON nutrition_saved_foods(user_id, is_favorite DESC, last_used_at DESC);

CREATE TABLE IF NOT EXISTS notification_settings (
 user_id INTEGER PRIMARY KEY, workout_reminders INTEGER NOT NULL DEFAULT 1,
 nutrition_reminders INTEGER NOT NULL DEFAULT 1, calendar_conflict_alerts INTEGER NOT NULL DEFAULT 1,
 morning_brief INTEGER NOT NULL DEFAULT 1, reminder_minutes_before INTEGER NOT NULL DEFAULT 90,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS dismissed_notifications (
 user_id INTEGER NOT NULL, notification_key TEXT NOT NULL, dismissed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(user_id,notification_key), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);


CREATE TABLE IF NOT EXISTS body_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    weight_lb REAL,
    body_fat_pct REAL,
    waist_in REAL,
    chest_in REAL,
    hips_in REAL,
    arm_in REAL,
    thigh_in REAL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, entry_date),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_body_metrics_user_date
ON body_metrics(user_id, entry_date DESC);


CREATE TABLE IF NOT EXISTS training_module_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    workout_id INTEGER NOT NULL,
    module_type TEXT NOT NULL CHECK(module_type IN ('core','cardio')),
    module_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','abandoned')),
    planned_minutes INTEGER,
    completed_minutes REAL,
    distance REAL,
    pace TEXT,
    rpe REAL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    notes TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_training_module_sessions_user
ON training_module_sessions(user_id, module_type, status);

CREATE TABLE IF NOT EXISTS training_module_exercise_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_session_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    sets_completed INTEGER NOT NULL DEFAULT 1,
    reps_json TEXT NOT NULL DEFAULT '[]',
    duration_seconds INTEGER,
    weight REAL,
    load_mode TEXT NOT NULL DEFAULT 'bodyweight',
    rpe REAL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(module_session_id) REFERENCES training_module_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id)
);

CREATE TABLE IF NOT EXISTS exercise_form_demos (
 exercise_id INTEGER PRIMARY KEY, demo_asset TEXT, demo_type TEXT NOT NULL DEFAULT 'placeholder',
 demo_version INTEGER NOT NULL DEFAULT 1, primary_view TEXT NOT NULL DEFAULT 'side',
 secondary_asset TEXT, animation_status TEXT NOT NULL DEFAULT 'metadata_ready',
 form_cues_json TEXT NOT NULL DEFAULT '[]', setup_cues_json TEXT NOT NULL DEFAULT '[]',
 common_mistakes_json TEXT NOT NULL DEFAULT '[]', breathing_cue TEXT, safety_note TEXT,
 reviewed INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercise_demo_reviews (
 exercise_id INTEGER PRIMARY KEY,
 correct_exercise INTEGER NOT NULL DEFAULT 0,
 setup INTEGER NOT NULL DEFAULT 0,
 range_of_motion INTEGER NOT NULL DEFAULT 0,
 joint_alignment INTEGER NOT NULL DEFAULT 0,
 loop_quality INTEGER NOT NULL DEFAULT 0,
 mobile_tested INTEGER NOT NULL DEFAULT 0,
 notes TEXT,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
);


-- v14.37.0: 3D form-demo delivery. Kept separate from legacy SVG demo records so
-- existing user databases migrate safely without destructive ALTER statements.
CREATE TABLE IF NOT EXISTS exercise_demo_3d_assets (
    exercise_id INTEGER PRIMARY KEY,
    primary_webm TEXT,
    secondary_webm TEXT,
    poster_asset TEXT,
    primary_view TEXT NOT NULL DEFAULT 'side',
    secondary_view TEXT DEFAULT 'front',
    render_version TEXT NOT NULL DEFAULT 'forge_3d_v1',
    status TEXT NOT NULL DEFAULT 'planned',
    source_kind TEXT NOT NULL DEFAULT 'original_3d',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercise_demo_3d_reviews (
    exercise_id INTEGER PRIMARY KEY,
    correct_exercise INTEGER NOT NULL DEFAULT 0,
    equipment_interaction INTEGER NOT NULL DEFAULT 0,
    range_of_motion INTEGER NOT NULL DEFAULT 0,
    joint_path INTEGER NOT NULL DEFAULT 0,
    primary_view INTEGER NOT NULL DEFAULT 0,
    secondary_view INTEGER NOT NULL DEFAULT 0,
    loop_quality INTEGER NOT NULL DEFAULT 0,
    mobile_tested INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS muscle_taxonomy (
    muscle_group TEXT NOT NULL,
    sub_muscle TEXT NOT NULL,
    PRIMARY KEY(muscle_group, sub_muscle)
);

CREATE TABLE IF NOT EXISTS exercise_muscles (
    exercise_id INTEGER NOT NULL,
    muscle_group TEXT NOT NULL,
    sub_muscle TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('primary','secondary')),
    PRIMARY KEY(exercise_id, muscle_group, sub_muscle, role),
    FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_exercise_muscles_group ON exercise_muscles(muscle_group, sub_muscle);
