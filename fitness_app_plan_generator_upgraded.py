
from __future__ import annotations

import sqlite3
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Optional
import random
from copy import deepcopy
from muscle_taxonomy import MUSCLE_TAXONOMY

DEFAULT_DB = Path(__file__).with_name("fitness_app_initial_database.sqlite")

GOAL_SETTINGS = {
    "build_muscle": {
        "compound_rep_range": (6, 12),
        "isolation_rep_range": (10, 15),
        "max_exercises": 7,
        "volume_factor": 1.0,
    },
    "get_stronger": {
        "compound_rep_range": (3, 8),
        "isolation_rep_range": (8, 12),
        "max_exercises": 6,
        "volume_factor": 0.85,
    },
    "lose_fat": {
        "compound_rep_range": (6, 12),
        "isolation_rep_range": (10, 15),
        "max_exercises": 6,
        "volume_factor": 0.85,
    },
    "improve_fitness": {
        "compound_rep_range": (8, 15),
        "isolation_rep_range": (10, 20),
        "max_exercises": 6,
        "volume_factor": 0.80,
    },
    "general_fitness": {
        "compound_rep_range": (6, 12),
        "isolation_rep_range": (10, 15),
        "max_exercises": 6,
        "volume_factor": 0.90,
    },
}

SPLITS = {
    2: ["Full Body A", "Full Body B"],
    3: ["Full Body A", "Full Body B", "Full Body C"],
    4: ["Upper A", "Lower A", "Upper B", "Lower B"],
    5: ["Upper A", "Lower A", "Upper B", "Lower B", "Full Body"],
    6: ["Push A", "Pull A", "Legs A", "Push B", "Pull B", "Legs B"],
}


CUSTOM_SPLITS = {
    "full_body": {2:["Full Body A","Full Body B"],3:["Full Body A","Full Body B","Full Body C"],4:["Full Body A","Full Body B","Full Body C","Full Body"],5:["Full Body A","Full Body B","Full Body C","Full Body","Full Body A"],6:["Full Body A","Full Body B","Full Body C","Full Body","Full Body A","Full Body B"]},
    "upper_lower": {2:["Upper A","Lower A"],3:["Upper A","Lower A","Full Body"],4:["Upper A","Lower A","Upper B","Lower B"],5:["Upper A","Lower A","Upper B","Lower B","Full Body"],6:["Upper A","Lower A","Upper B","Lower B","Upper A","Lower A"]},
    "push_pull_legs": {3:["Push A","Pull A","Legs A"],4:["Push A","Pull A","Legs A","Push B"],5:["Push A","Pull A","Legs A","Push B","Pull B"],6:["Push A","Pull A","Legs A","Push B","Pull B","Legs B"]},
    "body_part": {2:["Upper A","Lower A"],3:["Push A","Pull A","Legs A"],4:["Upper A","Lower A","Push A","Pull A"],5:["Push A","Pull A","Legs A","Upper B","Lower B"],6:["Push A","Pull A","Legs A","Push B","Pull B","Legs B"]},
    "hybrid": {2:["Full Body A","Full Body B"],3:["Upper A","Lower A","Full Body"],4:["Upper A","Lower A","Full Body A","Full Body B"],5:["Upper A","Lower A","Push A","Pull A","Legs A"],6:["Upper A","Lower A","Push A","Pull A","Legs A","Full Body"]},
}
def resolve_split(days, preference):
    if preference and preference != "auto":
        chosen=CUSTOM_SPLITS.get(preference,{}).get(days)
        if chosen:return chosen
    return SPLITS[days]


SPORT_PROFILES = {
    "general": {"label":"General Fitness","patterns":[],"muscles":[],"split":"auto","rep_bias":0,"conditioning":[]},
    "football": {"label":"Football","patterns":["Squat","Hinge","Loaded Carry","Horizontal Push"],"muscles":["Quads","Glutes","Hamstrings","Core","Chest"],"split":"hybrid","rep_bias":-2,"conditioning":["Interval Cardio","Loaded Carry"]},
    "basketball": {"label":"Basketball","patterns":["Squat","Lunge","Calf Raise","Anti-Extension"],"muscles":["Quads","Glutes","Calves","Core"],"split":"hybrid","rep_bias":0,"conditioning":["Interval Cardio"]},
    "soccer": {"label":"Soccer","patterns":["Lunge","Squat","Hinge","Calf Raise"],"muscles":["Quads","Hamstrings","Glutes","Calves","Core"],"split":"full_body","rep_bias":1,"conditioning":["Interval Cardio","Steady-State Cardio"]},
    "baseball": {"label":"Baseball","patterns":["Horizontal Push","Horizontal Pull","Rotation","Anti-Rotation","Hinge"],"muscles":["Shoulders","Upper Back","Core","Glutes"],"split":"upper_lower","rep_bias":0,"conditioning":["Interval Cardio"]},
    "hockey": {"label":"Hockey","patterns":["Squat","Lunge","Hinge","Anti-Rotation","Loaded Carry"],"muscles":["Quads","Glutes","Hamstrings","Core"],"split":"hybrid","rep_bias":0,"conditioning":["Interval Cardio"]},
    "tennis": {"label":"Tennis","patterns":["Rotation","Anti-Rotation","Lunge","Horizontal Pull","Shoulder Isolation"],"muscles":["Core","Shoulders","Glutes","Quads"],"split":"full_body","rep_bias":1,"conditioning":["Interval Cardio"]},
    "volleyball": {"label":"Volleyball","patterns":["Squat","Lunge","Vertical Push","Calf Raise"],"muscles":["Quads","Glutes","Calves","Shoulders","Core"],"split":"upper_lower","rep_bias":0,"conditioning":["Interval Cardio"]},
    "wrestling": {"label":"Wrestling","patterns":["Hinge","Squat","Horizontal Pull","Loaded Carry","Anti-Rotation"],"muscles":["Back","Glutes","Hamstrings","Core","Grip"],"split":"full_body","rep_bias":0,"conditioning":["Interval Cardio","Loaded Carry"]},
    "combat_sports": {"label":"Combat Sports","patterns":["Rotation","Anti-Rotation","Horizontal Push","Horizontal Pull","Lunge"],"muscles":["Core","Shoulders","Back","Glutes"],"split":"full_body","rep_bias":1,"conditioning":["Interval Cardio"]},
    "track_sprint": {"label":"Track / Sprinting","patterns":["Hinge","Squat","Lunge","Calf Raise"],"muscles":["Hamstrings","Glutes","Quads","Calves","Core"],"split":"full_body","rep_bias":-1,"conditioning":["Interval Cardio"]},
    "distance_running": {"label":"Distance Running","patterns":["Lunge","Squat","Calf Raise","Anti-Extension"],"muscles":["Calves","Quads","Glutes","Core"],"split":"full_body","rep_bias":2,"conditioning":["Steady-State Cardio"]},
    "swimming": {"label":"Swimming","patterns":["Vertical Pull","Horizontal Pull","Shoulder Isolation","Anti-Extension"],"muscles":["Lats","Shoulders","Upper Back","Core"],"split":"upper_lower","rep_bias":1,"conditioning":["Steady-State Cardio"]},
    "lacrosse": {"label":"Lacrosse","patterns":["Lunge","Rotation","Horizontal Pull","Horizontal Push","Hinge"],"muscles":["Core","Glutes","Back","Shoulders"],"split":"hybrid","rep_bias":0,"conditioning":["Interval Cardio"]},
}

CUSTOM_MUSCLE_TEMPLATES = {
    "Chest": [("Horizontal Push", "compound"), ("Horizontal Push", "isolation")],
    "Back": [("Vertical Pull", "compound"), ("Horizontal Pull", "compound")],
    "Shoulders": [("Vertical Push", "compound"), ("Shoulder Isolation", "isolation")],
    "Biceps": [("Elbow Flexion", "isolation")],
    "Triceps": [("Elbow Extension", "isolation")],
    "Quads": [("Squat", "compound"), ("Knee Extension", "isolation")],
    "Hamstrings": [("Hinge", "compound"), ("Knee Flexion", "isolation")],
    "Glutes": [("Hip Extension", "compound"), ("Lunge", "compound")],
    "Calves": [("Calf Raise", "isolation")],
    "Core": [("Anti-Extension", "core"), ("Anti-Rotation", "core")],
    "Forearms": [("Elbow Flexion", "isolation")],
}

EXERCISE_CANONICAL_ALIASES = {
    "Overhead Dumbbell Triceps Extension": "Dumbbell Overhead Triceps Extension",
    "Cable Overhead Triceps Extension": "Overhead Cable Triceps Extension",
    "Trap Bar Deadlift": "Trap-Bar Deadlift",
    "Treadmill Incline Walk": "Incline Treadmill Walk",
    "Farmer's Carry": "Farmer Carry",
}

def canonical_exercise_name(name: str) -> str:
    return EXERCISE_CANONICAL_ALIASES.get(str(name or "").strip(), str(name or "").strip())

def normalize_custom_split(custom_split, days):
    items=[]
    for i, raw in enumerate(custom_split or []):
        if not isinstance(raw, dict):
            continue
        muscles=[]
        for m in raw.get("muscles", []):
            name=str(m).strip()
            if name in CUSTOM_MUSCLE_TEMPLATES and name not in muscles:
                muscles.append(name)
        if muscles:
            raw_sub=raw.get("submuscles") or {}
            submuscles={}
            if isinstance(raw_sub, dict):
                for muscle in muscles:
                    allowed=set(MUSCLE_TAXONOMY.get(muscle,()))
                    chosen=[str(x).strip() for x in raw_sub.get(muscle,[]) if str(x).strip() in allowed]
                    if chosen: submuscles[muscle]=list(dict.fromkeys(chosen))
            items.append({"name": str(raw.get("name") or f"Custom Day {i+1}").strip()[:60], "muscles": muscles, "submuscles": submuscles})
    return items[:days]


def custom_split_intelligence(custom_days, priority_muscles=()):
    frequency={m:0 for m in CUSTOM_MUSCLE_TEMPLATES}
    for day in custom_days or []:
        for m in day.get("muscles",[]):
            if m in frequency:
                frequency[m]+=1
    warnings=[]
    major=("Chest","Back","Shoulders","Quads","Hamstrings","Glutes")
    missing=[m for m in major if frequency.get(m,0)==0]
    if missing:
        warnings.append(f"No weekly work assigned to {', '.join(missing)}.")
    priority_set=set(priority_muscles or ())
    for muscle in CUSTOM_MUSCLE_TEMPLATES:
        indexes=[i for i,d in enumerate(custom_days or []) if muscle in d.get("muscles",[])]
        if any(b-a==1 for a,b in zip(indexes,indexes[1:])):
            warnings.append(f"{muscle} is assigned to back-to-back training sessions.")
        if muscle in priority_set and frequency.get(muscle,0)==0:
            warnings.append(f"{muscle} is high priority but is not assigned to a training day.")
        elif muscle in priority_set and len(custom_days or [])>=3 and frequency.get(muscle,0)<2:
            warnings.append(f"{muscle} is high priority but only trained once weekly.")
    return {
        "frequency": frequency,
        "priority_muscles": [m for m in priority_muscles if m in CUSTOM_MUSCLE_TEMPLATES],
        "warnings": list(dict.fromkeys(warnings)),
        "balanced": not warnings,
    }

def resolve_sport_split(days, split_preference, sport):
    if split_preference and split_preference!="auto":
        return resolve_split(days, split_preference)
    preferred=SPORT_PROFILES.get(sport,SPORT_PROFILES["general"]).get("split","auto")
    return resolve_split(days, preferred if preferred!="auto" else "auto")

TEMPLATES = {
    "Upper A": [
        ("Horizontal Push", "compound"),
        ("Horizontal Pull", "compound"),
        ("Vertical Push", "compound"),
        ("Vertical Pull", "compound"),
        ("Shoulder Isolation", "isolation"),
        ("Elbow Flexion", "isolation"),
        ("Elbow Extension", "isolation"),
    ],
    "Upper B": [
        ("Vertical Push", "compound"),
        ("Horizontal Pull", "compound"),
        ("Horizontal Push", "compound"),
        ("Vertical Pull", "compound"),
        ("Shoulder Isolation", "isolation"),
        ("Elbow Extension", "isolation"),
        ("Elbow Flexion", "isolation"),
    ],
    "Lower A": [
        ("Squat", "compound"),
        ("Hinge", "compound"),
        ("Lunge", "compound"),
        ("Knee Extension", "isolation"),
        ("Knee Flexion", "isolation"),
        ("Calf Raise", "isolation"),
    ],
    "Lower B": [
        ("Hinge", "compound"),
        ("Squat", "compound"),
        ("Hip Extension", "compound"),
        ("Knee Flexion", "isolation"),
        ("Knee Extension", "isolation"),
        ("Calf Raise", "isolation"),
    ],
    "Push A": [
        ("Horizontal Push", "compound"),
        ("Vertical Push", "compound"),
        ("Shoulder Isolation", "isolation"),
        ("Horizontal Push", "isolation"),
        ("Elbow Extension", "isolation"),
    ],
    "Push B": [
        ("Vertical Push", "compound"),
        ("Horizontal Push", "compound"),
        ("Shoulder Isolation", "isolation"),
        ("Horizontal Push", "isolation"),
        ("Elbow Extension", "isolation"),
    ],
    "Pull A": [
        ("Vertical Pull", "compound"),
        ("Horizontal Pull", "compound"),
        ("Horizontal Pull", "compound"),
        ("Elbow Flexion", "isolation"),
        ("Shoulder Isolation", "isolation"),
    ],
    "Pull B": [
        ("Horizontal Pull", "compound"),
        ("Vertical Pull", "compound"),
        ("Vertical Pull", "isolation"),
        ("Elbow Flexion", "isolation"),
        ("Shoulder Isolation", "isolation"),
    ],
    "Legs A": [
        ("Squat", "compound"),
        ("Hinge", "compound"),
        ("Lunge", "compound"),
        ("Knee Extension", "isolation"),
        ("Knee Flexion", "isolation"),
        ("Calf Raise", "isolation"),
    ],
    "Legs B": [
        ("Hinge", "compound"),
        ("Squat", "compound"),
        ("Lunge", "compound"),
        ("Knee Flexion", "isolation"),
        ("Knee Extension", "isolation"),
        ("Calf Raise", "isolation"),
    ],
}

FULL_BODY_TEMPLATES = {
    "Full Body A": [
        ("Squat", "compound"), ("Horizontal Push", "compound"),
        ("Horizontal Pull", "compound"), ("Hinge", "compound"),
        ("Shoulder Isolation", "isolation"), ("Elbow Flexion", "isolation"),
    ],
    "Full Body B": [
        ("Hinge", "compound"), ("Vertical Push", "compound"),
        ("Vertical Pull", "compound"), ("Lunge", "compound"),
        ("Elbow Extension", "isolation"),
    ],
    "Full Body C": [
        ("Squat", "compound"), ("Horizontal Push", "compound"),
        ("Vertical Pull", "compound"), ("Hip Extension", "compound"),
        ("Shoulder Isolation", "isolation"), ("Elbow Flexion", "isolation"),
    ],
    "Full Body": [
        ("Squat", "compound"), ("Horizontal Push", "compound"),
        ("Horizontal Pull", "compound"), ("Hinge", "compound"),
        ("Shoulder Isolation", "isolation"), ("Elbow Extension", "isolation"),
    ],
}



SPORT_WORKOUT_NAME_PREFIX = {
    "general":"",
    "football":"Football","basketball":"Basketball","soccer":"Soccer","baseball":"Baseball",
    "hockey":"Hockey","tennis":"Tennis","volleyball":"Volleyball","wrestling":"Wrestling",
    "combat_sports":"Combat","track_sprint":"Sprint","distance_running":"Running",
    "swimming":"Swimming","lacrosse":"Lacrosse",
}

def dynamic_workout_name(base_name: str, profile) -> str:
    """Use simple, immediately understandable workout names."""
    names={
        "Upper A":"Upper Body",
        "Upper B":"Upper Body",
        "Lower A":"Lower Body",
        "Lower B":"Lower Body",
        "Push A":"Chest, Shoulders & Triceps",
        "Push B":"Chest, Shoulders & Triceps",
        "Pull A":"Back & Biceps",
        "Pull B":"Back & Biceps",
        "Legs A":"Legs",
        "Legs B":"Legs",
        "Full Body A":"Full Body",
        "Full Body B":"Full Body",
        "Full Body C":"Full Body",
        "Full Body":"Full Body",
    }
    if getattr(profile, "workout_split", "auto") == "push_pull_legs":
        if base_name.startswith("Push"): return "Push"
        if base_name.startswith("Pull"): return "Pull"
        if base_name.startswith("Legs"): return "Legs"
    return names.get(base_name,base_name)

@dataclass
class TrainingState:
    """Optional history used to make the generator adapt over time.

    Keys in exercise_history are exercise names. Each value may contain:
      - completed_sets: number of sets completed
      - reps: list of completed reps
      - target_reps: [low, high]
      - difficulty: 1-10 subjective difficulty (RPE-like)
      - skipped: bool
    """
    exercise_history: dict[str, dict[str, Any]] | None = None
    weekly_fatigue: float = 0.0
    missed_workouts: int = 0


INTELLIGENT_RULES = {
    "difficulty_up": 8.0,
    "difficulty_down": 5.0,
    "fatigue_high": 7.0,
    "fatigue_low": 3.0,
    "max_weekly_adjustment": 2,
}


@dataclass
class UserProfile:
    goal: str = "build_muscle"
    experience: str = "intermediate"
    days_per_week: int = 4
    minutes_per_workout: int = 45
    equipment: tuple[str, ...] = ("full_gym",)
    preferred_exercises: tuple[str, ...] = ()
    excluded_exercises: tuple[str, ...] = ()
    seed: Optional[int] = None
    training_state: Optional[TrainingState] = None
    priority_muscles: tuple[str, ...] = ()
    recovery_level: str = "normal"
    cardio_preference: str = "moderate"
    workout_split: str = "auto"
    sport: str = "general"
    core_workouts_per_week: int = 2
    cardio_workouts_per_week: int = 2
    custom_split: tuple[dict[str, Any], ...] = ()
    exercises_per_day: int = 6
    exercises_per_workout: tuple[int, ...] = ()
    locked_exercises: dict[int, list[int]] | None = None

@dataclass
class PlannedExercise:
    exercise_id: int
    name: str
    movement_pattern: str
    primary_muscle: str
    equipment: str
    sets: int
    min_reps: int
    max_reps: int
    rest_seconds: int
    progression_method: str
    muscle_targets: list[str] | None = None

@dataclass
class Workout:
    name: str
    estimated_minutes: int
    exercises: list[PlannedExercise]
    core_included: bool = False
    core_exercises: list[str] | None = None
    cardio_included: bool = False
    cardio_name: str | None = None
    cardio_minutes: int = 0
    cardio_intensity: str | None = None
    cardio_exercise_id: int | None = None
    cardio_movement_pattern: str | None = None
    cardio_equipment: str | None = None
    exercise_quota_requested: int = 0
    exercise_quota_met: bool = True
    exercise_quota_message: str | None = None

class PlanGenerator:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.rng = random.Random()

    def _load_exercises(self):
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            rows=[dict(r) for r in con.execute("SELECT * FROM exercises")]
            links={}
            try:
                for r in con.execute("SELECT exercise_id,muscle_group,sub_muscle,role FROM exercise_muscles"):
                    links.setdefault(int(r["exercise_id"]),[]).append(dict(r))
            except sqlite3.OperationalError:
                pass
            intelligence={}
            try:
                for r in con.execute("SELECT * FROM exercise_intelligence"):
                    intelligence[int(r["exercise_id"])]=dict(r)
            except sqlite3.OperationalError:
                pass
            unique=[]; seen=set()
            for e in rows:
                e["muscle_links"]=links.get(int(e["id"]),[])
                e["intelligence"]=intelligence.get(int(e["id"]),{})
                canonical=canonical_exercise_name(e["name"])
                key=canonical.lower()
                if key in seen:
                    continue
                e["canonical_name"]=canonical
                if e["name"] != canonical:
                    # Keep the canonical display label even when an old database row still uses an alias.
                    e["name"]=canonical
                seen.add(key); unique.append(e)
            return unique

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace("-", "_").replace(" ", "_")

    def _equipment_available(self, exercise_equipment: str, equipment: Iterable[str]) -> bool:
        available = {self._normalize(x) for x in equipment}
        if "full_gym" in available:
            return True
        requirements = [self._normalize(x) for x in exercise_equipment.split(",")]
        aliases = {
            "dumbbell": "dumbbells",
            "cable": "cable_machine",
            "machine": "machine",
            "barbell": "barbell",
            "bench": "bench",
            "squat_rack": "squat_rack",
            "pull_up_bar": "pull_up_bar",
            "bodyweight": "bodyweight",
            "ab_wheel": "ab_wheel",
            "treadmill": "treadmill",
            "bike": "bike",
            "rowing_machine": "rowing_machine",
        }
        return all(aliases.get(req, req) in available for req in requirements)

    def _eligible(self, profile: UserProfile):
        excluded = {x.strip().lower() for x in profile.excluded_exercises}
        exercises = []
        for e in self._load_exercises():
            if e["name"].lower() in excluded:
                continue
            if profile.experience == "beginner" and not e["beginner_suitable"]:
                continue
            if not self._equipment_available(e["equipment"], profile.equipment):
                continue
            exercises.append(e)
        return exercises

    def _score(self, e, pattern, kind, profile, used_names):
        score = 0
        if e["movement_pattern"] == pattern:
            score += 100
        else:
            return -10_000

        if kind == "compound" and e["exercise_type"] == "Compound":
            score += 20
        if kind == "isolation" and e["exercise_type"] in ("Isolation", "Isometric"):
            score += 20
        if kind == "core" and e["primary_muscle"] in ("Core", "Abs"):
            score += 25

        if e["name"].lower() in {x.lower() for x in profile.preferred_exercises}:
            score += 50

        if e["name"] in used_names:
            score -= 80
        # Avoid stacking too many near-identical movements when another valid option exists.
        pattern_marker=f"pattern::{e['movement_pattern']}"
        muscle_marker=f"muscle::{e['primary_muscle'].split(',')[0].strip().lower()}"
        if pattern_marker in used_names:
            score -= 14
        if muscle_marker in used_names:
            score -= 8
        intel=e.get("intelligence") or {}
        similarity_marker=f"similarity::{intel.get('similarity_family','')}"
        family_marker=f"family::{intel.get('movement_family','')}"
        if intel.get("similarity_family") and similarity_marker in used_names:
            score -= 70
        if intel.get("movement_family") and family_marker in used_names:
            score -= 24
        # Prefer lower-fatigue choices when two exercises provide comparable stimulus.
        score -= max(0,int(intel.get("fatigue_cost",3))-3)*3

        if profile.experience == "beginner" and e["difficulty"] == "Beginner":
            score += 10
        elif profile.experience == "intermediate" and e["difficulty"] == "Intermediate":
            score += 8
        elif profile.experience == "advanced" and e["difficulty"] in ("Advanced", "Intermediate"):
            score += 8

        score += self._adaptive_score(e, profile)
        score += self._exercise_quality(e, profile)
        score += self.rng.random() * 5
        return score

    def _pick(self, candidates, pattern, kind, profile, used_names):
        candidates=[e for e in candidates if canonical_exercise_name(e["name"]) not in used_names]
        scored = sorted(
            ((self._score(e, pattern, kind, profile, used_names), e) for e in candidates),
            key=lambda x: x[0],
            reverse=True,
        )
        return scored[0][1] if scored and scored[0][0] > 0 else None

    def _matches_muscle_target(self, exercise, muscle: str, subtargets=()) -> bool:
        links=exercise.get("muscle_links") or []
        group=[x for x in links if x.get("muscle_group")==muscle]
        if not group: return False
        wanted=set(subtargets or ())
        return not wanted or any(x.get("sub_muscle") in wanted for x in group)

    def _pick_for_target(self, candidates, pattern, kind, profile, used_names, muscle: str, subtargets=()):
        eligible=[e for e in candidates if canonical_exercise_name(e["name"]) not in used_names and self._matches_muscle_target(e,muscle,subtargets)]
        if not eligible: eligible=[e for e in candidates if canonical_exercise_name(e["name"]) not in used_names and self._matches_muscle_target(e,muscle,())]
        scored=[]
        wanted=set(subtargets or ())
        for e in eligible:
            base=self._score(e,pattern,kind,profile,used_names)
            if base<=0: continue
            links=e.get("muscle_links") or []
            bonus=max([60 if x.get("role")=="primary" else 25 for x in links if x.get("muscle_group")==muscle] or [0])
            if wanted and any(x.get("sub_muscle") in wanted for x in links): bonus+=90
            scored.append((base+bonus,e))
        scored.sort(key=lambda x:x[0],reverse=True)
        if scored: return scored[0][1]
        # A subsection can be more specific than the broad movement template
        # (for example Side Delts vs Vertical Push). Prefer the exact anatomical
        # target over silently falling back to the wrong muscle section.
        fallback=[]
        for e in eligible:
            if e["name"] in used_names: continue
            links=e.get("muscle_links") or []
            bonus=max([60 if x.get("role")=="primary" else 25 for x in links if x.get("muscle_group")==muscle] or [0])
            if wanted and any(x.get("sub_muscle") in wanted for x in links): bonus+=90
            fallback.append((bonus+self._exercise_quality(e,profile)+self.rng.random()*5,e))
        fallback.sort(key=lambda x:x[0],reverse=True)
        return fallback[0][1] if fallback else None

    def _exercise_target_count(self, profile: UserProfile, workout_index: int | None = None) -> int:
        per=list(getattr(profile,"exercises_per_workout",()) or ())
        if workout_index is not None and workout_index < len(per):
            return max(3,min(int(per[workout_index] or profile.exercises_per_day),10))
        return max(3,min(int(getattr(profile,"exercises_per_day",6) or 6),10))

    def _rep_range(self, e, goal):
        low, high = GOAL_SETTINGS[goal]["compound_rep_range" if e["exercise_type"] == "Compound" else "isolation_rep_range"]
        # Stay inside the exercise's safe/default range.
        low = max(low, e["min_reps"])
        high = min(high, e["max_reps"])
        if low > high:
            low, high = e["min_reps"], e["max_reps"]
        return low, high

    def _sets(self, e, goal, experience):
        base = e["default_sets"]
        factor = GOAL_SETTINGS[goal]["volume_factor"]
        sets = max(1, round(base * factor))
        if experience == "beginner":
            sets = min(sets, 3)
        return sets

    def _estimate_minutes(self, exercises):
        # Approximation for planning: 30 sec/set + programmed rest between sets + 30 sec transitions.
        seconds = 0
        for i, e in enumerate(exercises):
            seconds += e.sets * 30 + max(0, e.sets - 1) * e.rest_seconds
            if i:
                seconds += 30
        return math.ceil(seconds / 60)

    def _trim_to_time(self, exercises, max_minutes):
        exercises = exercises[:]
        while len(exercises) > 3 and self._estimate_minutes(exercises) > max_minutes:
            # Remove the lowest-priority final accessory.
            exercises.pop()
        # If still too long, reduce accessory sets first.
        for e in reversed(exercises):
            while e.sets > 1 and self._estimate_minutes(exercises) > max_minutes:
                e.sets -= 1
        return exercises

    def _template(self, workout_name):
        if workout_name in TEMPLATES:
            return TEMPLATES[workout_name]
        return FULL_BODY_TEMPLATES[workout_name]

    def _history_for(self, profile: UserProfile, exercise_name: str) -> dict[str, Any]:
        state = profile.training_state
        if not state or not state.exercise_history:
            return {}
        return state.exercise_history.get(exercise_name, {})

    def _exercise_quality(self, e, profile: UserProfile) -> float:
        """Prefer useful stimulus with manageable fatigue and skill for this user."""
        equipment=str(e.get("equipment","")).lower()
        name=str(e.get("name","")).lower()
        pattern=str(e.get("movement_pattern",""))
        compound=e.get("exercise_type")=="Compound"
        free_weight=any(x in equipment for x in ("barbell","dumbbell","kettlebell"))
        supported=any(x in name for x in ("supported","seated","machine")) or "machine" in equipment
        fatigue=2 + (1 if compound else 0) + (1 if free_weight and compound else 0)
        if pattern in {"Squat","Hinge","Deadlift","Loaded Carry"}: fatigue+=1
        if supported: fatigue-=1
        fatigue=max(1,min(fatigue,5))
        score=0.0
        # Short sessions favor high stimulus-to-fatigue choices.
        if profile.minutes_per_workout<=30:
            score += (6-fatigue)*3
            if supported: score+=4
        # Low recovery steers away from systemically expensive options.
        if self._normalize(profile.recovery_level)=="low":
            score += (6-fatigue)*4
        # Beginners get a stability/skill bias toward supported and machine work.
        if profile.experience=="beginner":
            if supported: score+=8
            if e.get("difficulty")=="Advanced": score-=18
        return score

    def _adaptive_score(self, e, profile: UserProfile) -> float:
        """Score an exercise using recent performance, recovery, and priorities."""
        score = 0.0
        history = self._history_for(profile, e["name"])

        # Favor muscles the user explicitly wants to prioritize.
        if e["primary_muscle"].lower() in {m.lower() for m in profile.priority_muscles}:
            score += 35
        sport=SPORT_PROFILES.get(profile.sport,SPORT_PROFILES["general"])
        if e["movement_pattern"] in sport.get("patterns",[]):
            score += 22
        primary=e["primary_muscle"].lower()
        if any(m.lower() in primary for m in sport.get("muscles",[])):
            score += 16

        # Adapt to recovery: reduce complexity/volume pressure when recovery is poor.
        recovery = self._normalize(profile.recovery_level)
        if recovery == "low" and e["exercise_type"] == "Compound":
            score -= 5
        elif recovery == "high":
            score += 3

        # If an exercise has been skipped repeatedly, make alternatives more likely.
        if history.get("skipped"):
            score -= 20

        # If recent performance was very easy, favor that exercise for progressive overload.
        difficulty = history.get("difficulty")
        if isinstance(difficulty, (int, float)):
            if difficulty <= INTELLIGENT_RULES["difficulty_down"]:
                score += 12
            elif difficulty >= INTELLIGENT_RULES["difficulty_up"]:
                score -= 8

        # Avoid repeating an exercise too aggressively if the user recently struggled.
        return score

    def _intelligent_sets(self, e, profile: UserProfile) -> int:
        sets = self._sets(e, profile.goal, profile.experience)
        state = profile.training_state
        recovery = self._normalize(profile.recovery_level)

        if recovery == "low":
            sets = max(1, sets - 1)
        elif recovery == "high" and profile.experience != "beginner":
            sets += 1

        history = self._history_for(profile, e["name"])
        difficulty = history.get("difficulty")
        if isinstance(difficulty, (int, float)):
            if difficulty >= INTELLIGENT_RULES["difficulty_up"]:
                sets = max(1, sets - 1)
            elif difficulty <= INTELLIGENT_RULES["difficulty_down"]:
                sets += 1

        if state:
            if state.weekly_fatigue >= INTELLIGENT_RULES["fatigue_high"]:
                sets = max(1, sets - 1)
            elif state.weekly_fatigue <= INTELLIGENT_RULES["fatigue_low"] and recovery == "high":
                sets += 1

        return max(1, min(sets, 5))

    def _intelligent_reps(self, e, profile: UserProfile, low: int, high: int) -> tuple[int, int]:
        """Adjust the target within the database/goal bounds based on recent results."""
        history = self._history_for(profile, e["name"])
        reps = history.get("reps")
        difficulty = history.get("difficulty")

        if not isinstance(reps, list) or not reps:
            return low, high

        numeric_reps = [r for r in reps if isinstance(r, (int, float))]
        if not numeric_reps:
            return low, high

        avg_reps = sum(numeric_reps) / len(numeric_reps)

        # If the user is comfortably hitting the top of the range, move the target up
        # only when the exercise's database range permits it.
        if avg_reps >= high and isinstance(difficulty, (int, float)) and difficulty <= 7:
            new_low = min(high, low + 1)
            new_high = min(e["max_reps"], high + 1)
            return new_low, max(new_low, new_high)

        # If performance fell short and difficulty was high, make the target slightly easier.
        if avg_reps < low and isinstance(difficulty, (int, float)) and difficulty >= 8:
            new_high = max(low, high - 1)
            new_low = max(e["min_reps"], low - 1)
            return min(new_low, new_high), new_high

        return low, high

    def _progression_note(self, e, profile: UserProfile) -> str:
        """Turn the database progression method into an adaptive instruction."""
        base = e["progression_method"]
        history = self._history_for(profile, e["name"])
        difficulty = history.get("difficulty")
        reps = history.get("reps")

        if isinstance(difficulty, (int, float)) and difficulty >= 9:
            return f"{base} — hold or reduce load next session until technique and recovery improve."
        if isinstance(difficulty, (int, float)) and difficulty <= 6 and isinstance(reps, list):
            return f"{base} — if all sets reach the top of the range with good form, progress the load next session."
        return base

    def _fit_to_session_time(self, exercises, max_minutes):
        """Fit volume to time while preserving the requested exercise count when possible."""
        exercises=exercises[:]
        for e in reversed(exercises):
            while e.sets>1 and self._estimate_minutes(exercises)>max_minutes:
                e.sets-=1
        exercises=self._intelligent_trim(exercises,max_minutes)
        if not exercises:
            return exercises
        # Use most of the selected budget. Longer sessions gain sets; shorter
        # sessions are reduced by _intelligent_trim/_trim_to_time.
        target=max(12,int(max_minutes*0.82))
        guard=0
        while self._estimate_minutes(exercises) < target and guard < 30:
            guard += 1
            ranked=sorted(exercises,key=lambda e:(e.sets>=5,e.sets))
            changed=False
            for e in ranked:
                if e.sets < 5:
                    e.sets += 1
                    changed=True
                    break
            if not changed:
                break
        return self._trim_to_time(exercises,max_minutes)

    def _intelligent_trim(self, exercises, max_minutes):
        """Preserve higher-value work when time is limited."""
        exercises = exercises[:]
        while len(exercises) > 3 and self._estimate_minutes(exercises) > max_minutes:
            # Prefer dropping lower-set accessory work before major compounds.
            ranked = sorted(
                range(len(exercises)),
                key=lambda i: (
                    exercises[i].sets,
                    exercises[i].primary_muscle.lower() in {"core", "abs"},
                    exercises[i].movement_pattern,
                ),
            )
            exercises.pop(ranked[0])

        return self._trim_to_time(exercises, max_minutes)

    def _validate_intelligent_plan(self, workouts, profile: UserProfile):
        """Lightweight sanity checks so the adaptive layer cannot create empty/bizarre plans."""
        if not workouts:
            raise ValueError("The intelligent planner produced no workouts.")

        for workout in workouts:
            if not workout.exercises:
                raise ValueError(f"No eligible exercises could be selected for {workout.name}.")
            if workout.estimated_minutes > profile.minutes_per_workout:
                # The generator should already trim; this is a final guard.
                workout.exercises = self._trim_to_time(
                    workout.exercises, profile.minutes_per_workout
                )
                workout.estimated_minutes = self._estimate_minutes(workout.exercises)

    def generate_workout(self, profile: UserProfile, workout_name: str, candidates, workout_index: int = 0):
        used = set()
        selected = []
        template = self._template(workout_name)

        target_count=self._exercise_target_count(profile, workout_index)
        expanded_template=(template * max(1, math.ceil(target_count/max(1,len(template)))))[:target_count]
        for pattern, kind in expanded_template:
            e = self._pick(candidates, pattern, kind, profile, used)
            if not e:
                continue
            used.add(e["name"])
            used.add(f"pattern::{e['movement_pattern']}")
            used.add(f"muscle::{e['primary_muscle'].split(',')[0].strip().lower()}")
            intel=e.get("intelligence") or {}
            if intel.get("similarity_family"): used.add(f"similarity::{intel['similarity_family']}")
            if intel.get("movement_family"): used.add(f"family::{intel['movement_family']}")
            low, high = self._rep_range(e, profile.goal)
            sport_bias=SPORT_PROFILES.get(profile.sport,SPORT_PROFILES["general"]).get("rep_bias",0)
            if sport_bias:
                low=max(e["min_reps"],low+sport_bias); high=min(e["max_reps"],high+sport_bias)
                if low>high: low,high=e["min_reps"],e["max_reps"]
            low, high = self._intelligent_reps(e, profile, low, high)
            selected.append(PlannedExercise(
                exercise_id=e["id"],
                name=e["name"],
                movement_pattern=e["movement_pattern"],
                primary_muscle=e["primary_muscle"],
                equipment=e["equipment"],
                sets=self._intelligent_sets(e, profile),
                min_reps=low,
                max_reps=high,
                rest_seconds=e["default_rest_seconds"],
                progression_method=self._progression_note(e, profile),
            ))

        max_exercises = self._exercise_target_count(profile, workout_index)
        sport=SPORT_PROFILES.get(profile.sport,SPORT_PROFILES["general"])
        if len(selected)<max_exercises and sport.get("conditioning"):
            for pattern in sport["conditioning"]:
                addon=self._pick(candidates,pattern,"compound",profile,used)
                if addon:
                    low,high=self._rep_range(addon,profile.goal)
                    selected.append(PlannedExercise(
                        exercise_id=addon["id"],name=addon["name"],movement_pattern=addon["movement_pattern"],
                        primary_muscle=addon["primary_muscle"],equipment=addon["equipment"],
                        sets=min(3,self._intelligent_sets(addon,profile)),min_reps=low,max_reps=high,
                        rest_seconds=addon["default_rest_seconds"],progression_method=self._progression_note(addon,profile)))
                    break
        selected = selected[:max_exercises]
        selected = self._fit_to_session_time(selected, profile.minutes_per_workout)

        actual=len(selected)
        return Workout(
            name=dynamic_workout_name(workout_name, profile),
            estimated_minutes=self._estimate_minutes(selected),
            exercises=selected,
            exercise_quota_requested=max_exercises,
            exercise_quota_met=actual >= max_exercises,
            exercise_quota_message=(None if actual >= max_exercises else f"Only {actual} unique eligible exercises were available; the requested quota was {max_exercises}."),
        )

    def _addon_day_indexes(self, workout_count: int, requested: int, offset: int = 0) -> list[int]:
        requested=max(0,min(int(requested),workout_count))
        if requested==0:return []
        indexes=[]
        for i in range(requested):
            idx=min(workout_count-1, int((i+0.5)*workout_count/requested))
            idx=(idx+offset)%workout_count
            if idx not in indexes:indexes.append(idx)
        for idx in range(workout_count):
            shifted=(idx+offset)%workout_count
            if len(indexes)>=requested:break
            if shifted not in indexes:indexes.append(shifted)
        return sorted(indexes)

    def _core_day_indexes(self, workout_count: int, requested: int) -> list[int]:
        return self._addon_day_indexes(workout_count,requested,0)

    def _build_core_module(self, module_index: int, profile: UserProfile, candidates, workout: Workout) -> dict:
        """Build a balanced standalone core circuit without consuming strength-workout slots."""
        groups=[
            ("Lower Abs / Hip Flexion", ["Hip Flexion"]),
            ("Anti-Extension", ["Anti-Extension"]),
            ("Obliques", ["Anti-Lateral Flexion","Anti-Rotation","Rotation"]),
            ("Trunk Flexion", ["Spinal Flexion"]),
        ]
        used=set()
        exercises=[]
        workout_name=(workout.name or "").lower()
        lower_day=any(x in workout_name for x in ("lower","leg","squat","deadlift","posterior"))
        upper_day=any(x in workout_name for x in ("upper","push","pull","chest","back","shoulder"))
        for label,patterns in groups:
            choices=[]
            for pattern in patterns:
                choices.extend([
                    e for e in candidates
                    if e.get("movement_pattern")==pattern and e.get("name") not in used
                    and e.get("exercise_type") not in {"Cardio"}
                ])
            if not choices:
                continue
            def core_score(e):
                score=self._adaptive_score(e,profile)+self._exercise_quality(e,profile)+self.rng.random()*3
                fatigue=2 + (1 if e.get("exercise_type")=="Compound" else 0)
                if lower_day and e.get("movement_pattern") in {"Hip Flexion","Rotation"}:
                    score-=3
                if lower_day and any(x in str(e.get("name","")).lower() for x in ("hanging","ab wheel")):
                    score-=4
                if upper_day and e.get("movement_pattern") in {"Anti-Rotation","Anti-Lateral Flexion"}:
                    score+=3
                return score
            choices=sorted(choices,key=core_score,reverse=True)
            ex=choices[0]
            used.add(ex["name"])
            low,high=self._rep_range(ex,profile.goal)
            timed=ex.get("exercise_type")=="Isometric" or any(
                x in ex.get("name","").lower() for x in ("plank","hold","wall sit")
            )
            history=self._history_for(profile,ex["name"])
            avg_rpe=history.get("core_avg_rpe")
            progression_note="Build consistency first; progress when all sets finish with good form and ~2-3 reps in reserve."
            if timed:
                last=int(history.get("core_last_duration") or 0)
                if last:
                    if avg_rpe is not None and avg_rpe <= 7:
                        low=max(int(low),last+5); high=max(int(high),low+10)
                        progression_note="Previous holds were comfortable, so Forge added about 5 seconds."
                    elif avg_rpe is not None and avg_rpe >= 9:
                        low=max(10,min(int(low),last)); high=max(low+5,min(int(high),last+5))
                        progression_note="Previous holds were near limit, so Forge held the target steady."
                    else:
                        low=max(int(low),last); high=max(int(high),last+10)
                        progression_note="Target follows your most recent hold while preserving room to progress."
            else:
                last=int(history.get("core_last_reps") or 0)
                if last:
                    if avg_rpe is not None and avg_rpe <= 7:
                        low=max(int(low),last); high=max(int(high),last+2)
                        progression_note="Previous sets were comfortable, so Forge progressed the rep target."
                    elif avg_rpe is not None and avg_rpe >= 9:
                        low=max(5,min(int(low),last-1)); high=max(low+2,min(int(high),last+1))
                        progression_note="Previous sets were near limit, so Forge held or slightly reduced the target."
                    else:
                        low=max(int(low),last-1); high=max(int(high),last+1)
                        progression_note="Target stays close to your latest performance until effort improves."
            exercises.append({
                "exercise_id":int(ex["id"]),
                "name":ex["name"],
                "movement_pattern":ex["movement_pattern"],
                "core_region":label,
                "primary_muscle":ex["primary_muscle"],
                "equipment":ex["equipment"],
                "sets":2,
                "min_reps":int(low),
                "max_reps":int(high),
                "rest_seconds":35 if not lower_day else 30,
                "round_rest_seconds":75 if lower_day else 60,
                "progression_method":progression_note,
                "tracking_mode":"timed" if timed else "reps",
                "bodyweight_default":"bodyweight" in str(ex.get("equipment","")).lower(),
            })
        return {
            "name":f"Core Circuit {chr(65 + (module_index % 3))}",
            "type":"core",
            "estimated_minutes":max(8,min(18,math.ceil(
                sum((e["sets"]*35)+((e["sets"]-1)*e["rest_seconds"]) for e in exercises)/60
                + ((75 if lower_day else 60)/60)
            ))),
            "rounds":2,
            "between_exercise_rest_seconds":30 if lower_day else 35,
            "round_rest_seconds":75 if lower_day else 60,
            "focus":["Lower Abs","Anti-Extension","Obliques","Trunk Flexion"],
            "reason":("Lower-body fatigue protection: lower-spinal-load core choices were prioritized."
                      if lower_day else "Core functions were balanced to complement today's strength session."),
            "exercises":exercises,
        }

    def _build_cardio_module(self, profile: UserProfile, candidates, workout: Workout) -> dict | None:
        cardio_patterns=["Steady-State Cardio","Interval Cardio"]
        eligible=[x for x in candidates if x.get("exercise_type")=="Cardio" or x.get("movement_pattern") in cardio_patterns]
        if not eligible:
            return None
        intensity=profile.cardio_preference if profile.cardio_preference in {"light","moderate","high","extended"} else "moderate"
        workout_name=(workout.name or "").lower()
        lower_day=any(x in workout_name for x in ("lower","leg","squat","deadlift","posterior"))
        upper_day=any(x in workout_name for x in ("upper","push","pull","chest","back","shoulder"))
        goal=profile.goal
        if lower_day:
            desired="Steady-State Cardio"
        elif intensity=="high" and upper_day:
            desired="Interval Cardio"
        else:
            desired="Interval Cardio" if intensity=="high" else "Steady-State Cardio"
        matches=[x for x in eligible if x.get("movement_pattern")==desired] or eligible
        chosen=sorted(matches,key=lambda x:self._adaptive_score(x,profile)+self.rng.random()*3,reverse=True)[0]
        base={"light":10,"moderate":15,"high":20,"extended":25}.get(intensity,15)
        if goal=="lose_fat": base+=5
        elif goal=="get_stronger": base=max(10,base-5)
        duration=base
        return {
            "name":chosen["name"],
            "type":"cardio",
            "exercise_id":int(chosen["id"]),
            "movement_pattern":chosen["movement_pattern"],
            "equipment":chosen["equipment"],
            "minutes":duration,
            "intensity":("light" if lower_day and intensity=="high" else intensity),
            "reason":(
                "Low-impact steady cardio selected to reduce interference with lower-body recovery."
                if lower_day else
                "Higher-intensity cardio fits better after an upper-body strength session."
                if upper_day and desired=="Interval Cardio" else
                "Cardio modality and duration were matched to your goal and recovery demands."
            ),
        }

    def _add_core_to_workout(self, workout: Workout, profile: UserProfile, candidates) -> None:
        core_patterns=["Anti-Extension","Anti-Rotation","Spinal Flexion","Hip Flexion","Anti-Lateral Flexion","Rotation"]
        used={x.name for x in workout.exercises}
        added=[]
        # Two short core movements create a real core block without turning it into a separate workout.
        for pattern in core_patterns:
            ex=self._pick(candidates,pattern,"core",profile,used)
            if not ex:continue
            used.add(ex["name"])
            low,high=self._rep_range(ex,profile.goal)
            sets=min(2,self._intelligent_sets(ex,profile))
            added.append(PlannedExercise(
                exercise_id=ex["id"],name=ex["name"],movement_pattern=ex["movement_pattern"],
                primary_muscle=ex["primary_muscle"],equipment=ex["equipment"],
                sets=sets,min_reps=low,max_reps=high,
                rest_seconds=min(int(ex["default_rest_seconds"]),60),
                progression_method=self._progression_note(ex,profile),
            ))
            if len(added)>=2:break
        if added:
            workout.exercises.extend(added)
            workout.core_included=True
            workout.core_exercises=[x.name for x in added]
            workout.estimated_minutes=self._estimate_minutes(workout.exercises)

    def _add_cardio_to_workout(self, workout: Workout, profile: UserProfile, candidates) -> None:
        cardio_patterns=["Steady-State Cardio","Interval Cardio"]
        sport=SPORT_PROFILES.get(profile.sport,SPORT_PROFILES["general"])
        preferred=sport.get("conditioning") or []
        ordered=[x for x in preferred if x in cardio_patterns]+[x for x in cardio_patterns if x not in preferred]

        eligible=[x for x in candidates if x.get("exercise_type")=="Cardio" or x.get("movement_pattern") in cardio_patterns]
        if not eligible:
            return

        intensity=profile.cardio_preference if profile.cardio_preference in {"light","moderate","high","extended"} else "moderate"
        if intensity=="light":
            ordered=["Steady-State Cardio","Interval Cardio"]
        elif intensity=="high":
            ordered=["Interval Cardio","Steady-State Cardio"]
        elif intensity=="extended":
            ordered=["Steady-State Cardio","Interval Cardio"]

        chosen=None
        for pattern in ordered:
            matches=[x for x in eligible if x.get("movement_pattern")==pattern]
            if matches:
                matches=sorted(matches,key=lambda x:self._adaptive_score(x,profile)+self.rng.random()*4,reverse=True)
                chosen=matches[0]
                break
        if not chosen:
            chosen=eligible[0]

        duration={"light":10,"moderate":15,"high":20,"extended":25}.get(intensity,15)

        workout.cardio_included=True
        workout.cardio_name=chosen["name"]
        workout.cardio_minutes=duration
        workout.cardio_intensity=intensity
        workout.cardio_exercise_id=int(chosen["id"])
        workout.cardio_movement_pattern=chosen["movement_pattern"]
        workout.cardio_equipment=chosen["equipment"]
        workout.estimated_minutes+=duration

    def generate_custom_workout(self, profile: UserProfile, day: dict[str, Any], candidates, workout_index: int = 0):
        muscles=list(day.get("muscles") or [])
        submap=day.get("submuscles") or {}
        if not muscles:
            raise ValueError("Every custom split day needs at least one muscle group.")
        target_count=self._exercise_target_count(profile, workout_index)
        # Interleave muscle groups so later selections are not starved when the
        # requested exercise count is smaller than the combined templates.
        per_muscle={m:list(CUSTOM_MUSCLE_TEMPLATES.get(m,[])) for m in muscles}
        slots=[]; round_index=0
        while len(slots)<target_count and any(per_muscle.values()):
            added=False
            for muscle in muscles:
                choices=per_muscle.get(muscle) or []
                if not choices: continue
                slots.append((choices[round_index % len(choices)],muscle)); added=True
                if len(slots)>=target_count: break
            if not added: break
            round_index+=1
        used=set(); selected=[]; priority_bonus_used=set()
        priority={m.lower() for m in profile.priority_muscles}
        for (pattern, kind), owner_muscle in slots:
            targets=list(submap.get(owner_muscle,[]) or [])
            e=self._pick_for_target(candidates,pattern,kind,profile,used,owner_muscle,targets)
            if not e: continue
            used.add(e["name"]); used.add(f"pattern::{e['movement_pattern']}")
            low, high=self._rep_range(e, profile.goal); low, high=self._intelligent_reps(e, profile, low, high)
            sets=self._intelligent_sets(e, profile)
            if owner_muscle.lower() in priority and owner_muscle not in priority_bonus_used:
                sets=min(5,sets+1); priority_bonus_used.add(owner_muscle)
            matched=[x["sub_muscle"] for x in e.get("muscle_links",[]) if x.get("muscle_group")==owner_muscle and (not targets or x.get("sub_muscle") in targets)]
            selected.append(PlannedExercise(
                exercise_id=e["id"], name=e["name"], movement_pattern=e["movement_pattern"],
                primary_muscle=e["primary_muscle"], equipment=e["equipment"], sets=sets, min_reps=low, max_reps=high,
                rest_seconds=e["default_rest_seconds"], progression_method=self._progression_note(e, profile),
                muscle_targets=list(dict.fromkeys(matched or targets or [owner_muscle])),
            ))
        if not selected:
            raise ValueError(f"No eligible exercises could be selected for {day.get('name') or 'custom day'}.")
        # Fill shortfalls from any exercise that directly trains the selected muscles.
        while len(selected)<target_count:
            best=None
            for muscle in muscles:
                targets=list(submap.get(muscle,[]) or [])
                pool=[e for e in candidates if e["name"] not in {x.name for x in selected} and self._matches_muscle_target(e,muscle,targets)]
                if not pool: continue
                pool.sort(key=lambda e:(any(x.get("role")=="primary" for x in e.get("muscle_links",[]) if x.get("muscle_group")==muscle),self._exercise_quality(e,profile)),reverse=True)
                best=(pool[0],muscle,targets); break
            if not best: break
            e,muscle,targets=best; low,high=self._rep_range(e,profile.goal); low,high=self._intelligent_reps(e,profile,low,high)
            selected.append(PlannedExercise(exercise_id=e["id"],name=e["name"],movement_pattern=e["movement_pattern"],primary_muscle=e["primary_muscle"],equipment=e["equipment"],sets=self._intelligent_sets(e,profile),min_reps=low,max_reps=high,rest_seconds=e["default_rest_seconds"],progression_method=self._progression_note(e,profile),muscle_targets=targets or [muscle]))
        selected=self._fit_to_session_time(selected[:target_count], profile.minutes_per_workout)
        actual=len(selected)
        return Workout(name=str(day.get("name") or "Custom Day"),estimated_minutes=self._estimate_minutes(selected),exercises=selected,
            exercise_quota_requested=target_count, exercise_quota_met=actual >= target_count,
            exercise_quota_message=(None if actual >= target_count else f"Only {actual} unique eligible exercises were available; the requested quota was {target_count}."))

    def generate_plan(self, profile: UserProfile):
        if profile.days_per_week not in SPLITS:
            raise ValueError("days_per_week must be between 2 and 6")
        if profile.goal not in GOAL_SETTINGS:
            raise ValueError(f"Unsupported goal: {profile.goal}")
        if profile.experience not in {"beginner", "intermediate", "advanced"}:
            raise ValueError("experience must be beginner, intermediate, or advanced")
        if not 3 <= int(profile.exercises_per_day) <= 10:
            raise ValueError("exercises_per_day must be between 3 and 10")

        self.rng.seed(profile.seed)
        candidates = self._eligible(profile)
        if not candidates:
            raise ValueError("No exercises match the selected equipment/preferences.")

        custom_days=normalize_custom_split(profile.custom_split, profile.days_per_week)
        split_intelligence=None
        if profile.workout_split == "custom":
            if len(custom_days) != profile.days_per_week:
                raise ValueError(f"Custom split requires exactly {profile.days_per_week} configured training days.")
            split_intelligence=custom_split_intelligence(custom_days, profile.priority_muscles)
            workouts=[self.generate_custom_workout(profile, day, candidates, i) for i,day in enumerate(custom_days)]
            resolved_split=[w.name for w in workouts]
        else:
            resolved_split=resolve_sport_split(profile.days_per_week, profile.workout_split, profile.sport)
            workouts = [self.generate_workout(profile, name, candidates, i) for i,name in enumerate(resolved_split)]
        # Preserve user-locked exercises across regeneration. Locks are anchored to workout sequence.
        lock_map=getattr(profile,"locked_exercises",None) or {}
        by_id={int(e["id"]):e for e in candidates}
        for wi,locked_ids in lock_map.items():
            wi=int(wi)
            if wi<0 or wi>=len(workouts): continue
            workout=workouts[wi]
            existing={int(x.exercise_id) for x in workout.exercises}
            target=self._exercise_target_count(profile,wi)
            for exid in locked_ids:
                exid=int(exid)
                if exid in existing or exid not in by_id: continue
                e=by_id[exid]; low,high=self._rep_range(e,profile.goal)
                pe=PlannedExercise(exercise_id=e["id"],name=e["name"],movement_pattern=e["movement_pattern"],primary_muscle=e["primary_muscle"],equipment=e["equipment"],sets=self._intelligent_sets(e,profile),min_reps=low,max_reps=high,rest_seconds=e["default_rest_seconds"],progression_method=self._progression_note(e,profile))
                if len(workout.exercises)>=target:
                    workout.exercises[-1]=pe
                else:
                    workout.exercises.append(pe)
                existing.add(exid)
            workout.estimated_minutes=self._estimate_minutes(workout.exercises)

        core_count=max(0,min(int(profile.core_workouts_per_week),len(workouts)))
        cardio_count=max(0,min(int(profile.cardio_workouts_per_week),len(workouts)))
        if profile.cardio_preference=="none":
            cardio_count=0

        # Strength workouts remain strength-only. Core and cardio are standalone
        # modules scheduled on the same day as selected strength workouts.
        core_indexes=self._core_day_indexes(len(workouts),core_count)
        cardio_offset=1 if len(workouts)>1 and core_count else 0
        cardio_indexes=self._addon_day_indexes(len(workouts),cardio_count,cardio_offset)

        self._validate_intelligent_plan(workouts, profile)
        workout_dicts=[asdict(w) for w in workouts]
        core_modules=[]
        for module_number,idx in enumerate(core_indexes):
            module=self._build_core_module(module_number,profile,candidates,workouts[idx])
            module["workout_index"]=idx
            core_modules.append(module)
            workout_dicts[idx]["core_module"]=module
            workout_dicts[idx]["core_included"]=False
            workout_dicts[idx]["core_exercises"]=[]
        cardio_modules=[]
        for idx in cardio_indexes:
            module=self._build_cardio_module(profile,candidates,workouts[idx])
            if module:
                module["workout_index"]=idx
                cardio_modules.append(module)
                workout_dicts[idx]["cardio_module"]=module
                workout_dicts[idx]["cardio_included"]=False
                workout_dicts[idx]["cardio_name"]=None
                workout_dicts[idx]["cardio_minutes"]=0

        # Plan Generator 4.0 audit: volume, subsection coverage, recovery warnings and redundancy.
        volume_audit={}
        redundancy=[]
        for wi,w in enumerate(workout_dicts):
            families={}
            for ex in w.get("exercises",[]):
                raw=next((x for x in candidates if int(x["id"])==int(ex["exercise_id"])),None)
                if raw:
                    for link in raw.get("muscle_links",[]):
                        weight=1.0 if link.get("role")=="primary" else 0.5
                        key=f"{link.get('muscle_group')} > {link.get('sub_muscle')}"
                        volume_audit[key]=round(volume_audit.get(key,0)+float(ex.get("sets",0))*weight,1)
                    fam=(raw.get("intelligence") or {}).get("movement_family")
                    if fam:
                        families.setdefault(fam,[]).append(ex.get("name"))
            for fam,names in families.items():
                if len(names)>=3: redundancy.append({"workout_index":wi,"movement_family":fam,"exercises":names,"warning":"High movement redundancy"})
        plan_audit={"submuscle_set_equivalents":volume_audit,"redundancy_warnings":redundancy,"status":"review" if redundancy else "balanced"}

        return {
            "planner_version": "4.0-plan-intelligence",
            "adaptive_features": [
                "recent performance adaptation",
                "recovery-aware set adjustment",
                "muscle-priority weighting",
                "fatigue-aware volume control",
                "time-aware exercise preservation",
                "adaptive progression instructions",
                "stimulus-to-fatigue exercise selection",
                "redundant movement protection",
                "user exercise preference learning",
                "standalone balanced core circuits",
                "standalone cardio modules",
                "strength-session-aware core selection",
                "goal-aware cardio interference management",
            ],
            "profile": asdict(profile),
            "split": resolved_split,
            "custom_split": custom_days if profile.workout_split == "custom" else [],
            "split_intelligence": split_intelligence,
            "plan_audit": plan_audit,
            "cardio_preference": profile.cardio_preference,
            "workout_split": profile.workout_split,
            "sport": profile.sport,
            "sport_focus": SPORT_PROFILES.get(profile.sport,SPORT_PROFILES["general"])["label"],
            "core_workouts_per_week": core_count,
            "cardio_workouts_per_week": cardio_count,
            "workouts": workout_dicts,
            "core_modules": core_modules,
            "cardio_modules": cardio_modules,
            "workout_names": [w.name for w in workouts],
        }


def generate_plan(
    goal="build_muscle",
    experience="intermediate",
    days_per_week=4,
    minutes_per_workout=45,
    equipment=("full_gym",),
    preferred_exercises=(),
    excluded_exercises=(),
    seed=42,
    db_path=DEFAULT_DB,
    training_state=None,
    priority_muscles=(),
    recovery_level="normal",
    core_workouts_per_week=2,
    cardio_workouts_per_week=2,
    exercises_per_day=6,
):
    """Convenience function used by the app/API layer."""
    profile = UserProfile(
        goal=goal,
        experience=experience,
        days_per_week=days_per_week,
        minutes_per_workout=minutes_per_workout,
        equipment=tuple(equipment),
        preferred_exercises=tuple(preferred_exercises),
        excluded_exercises=tuple(excluded_exercises),
        seed=seed,
        training_state=training_state,
        priority_muscles=tuple(priority_muscles),
        recovery_level=recovery_level,
        core_workouts_per_week=core_workouts_per_week,
        cardio_workouts_per_week=cardio_workouts_per_week,
        exercises_per_day=exercises_per_day,
    )
    return PlanGenerator(db_path).generate_plan(profile)


if __name__ == "__main__":
    plan = generate_plan()
    print(__import__("json").dumps(plan, indent=2))
