
from __future__ import annotations

import sqlite3
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Iterable, Optional
import random
from copy import deepcopy

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
        ("Anti-Extension", "core"),
    ],
    "Lower B": [
        ("Hinge", "compound"),
        ("Squat", "compound"),
        ("Hip Extension", "compound"),
        ("Knee Flexion", "isolation"),
        ("Knee Extension", "isolation"),
        ("Calf Raise", "isolation"),
        ("Anti-Extension", "core"),
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
        ("Anti-Extension", "core"),
    ],
    "Legs B": [
        ("Hinge", "compound"),
        ("Squat", "compound"),
        ("Lunge", "compound"),
        ("Knee Flexion", "isolation"),
        ("Knee Extension", "isolation"),
        ("Calf Raise", "isolation"),
        ("Anti-Extension", "core"),
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
        ("Elbow Extension", "isolation"), ("Anti-Extension", "core"),
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

@dataclass
class Workout:
    name: str
    estimated_minutes: int
    exercises: list[PlannedExercise]

class PlanGenerator:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.rng = random.Random()

    def _load_exercises(self):
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            return [dict(r) for r in con.execute("SELECT * FROM exercises")]

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

        if profile.experience == "beginner" and e["difficulty"] == "Beginner":
            score += 10
        elif profile.experience == "intermediate" and e["difficulty"] == "Intermediate":
            score += 8
        elif profile.experience == "advanced" and e["difficulty"] in ("Advanced", "Intermediate"):
            score += 8

        score += self._adaptive_score(e, profile)
        score += self.rng.random() * 8
        return score

    def _pick(self, candidates, pattern, kind, profile, used_names):
        scored = sorted(
            ((self._score(e, pattern, kind, profile, used_names), e) for e in candidates),
            key=lambda x: x[0],
            reverse=True,
        )
        return scored[0][1] if scored and scored[0][0] > 0 else None

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

    def _adaptive_score(self, e, profile: UserProfile) -> float:
        """Score an exercise using recent performance, recovery, and priorities."""
        score = 0.0
        history = self._history_for(profile, e["name"])

        # Favor muscles the user explicitly wants to prioritize.
        if e["primary_muscle"].lower() in {m.lower() for m in profile.priority_muscles}:
            score += 35

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

    def generate_workout(self, profile: UserProfile, workout_name: str, candidates):
        used = set()
        selected = []
        template = self._template(workout_name)

        for pattern, kind in template:
            e = self._pick(candidates, pattern, kind, profile, used)
            if not e:
                continue
            used.add(e["name"])
            low, high = self._rep_range(e, profile.goal)
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

        max_exercises = GOAL_SETTINGS[profile.goal]["max_exercises"]
        selected = selected[:max_exercises]
        selected = self._intelligent_trim(selected, profile.minutes_per_workout)

        return Workout(
            name=workout_name,
            estimated_minutes=self._estimate_minutes(selected),
            exercises=selected,
        )

    def generate_plan(self, profile: UserProfile):
        if profile.days_per_week not in SPLITS:
            raise ValueError("days_per_week must be between 2 and 6")
        if profile.goal not in GOAL_SETTINGS:
            raise ValueError(f"Unsupported goal: {profile.goal}")
        if profile.experience not in {"beginner", "intermediate", "advanced"}:
            raise ValueError("experience must be beginner, intermediate, or advanced")

        self.rng.seed(profile.seed)
        candidates = self._eligible(profile)
        if not candidates:
            raise ValueError("No exercises match the selected equipment/preferences.")

        workouts = [
            self.generate_workout(profile, name, candidates)
            for name in SPLITS[profile.days_per_week]
        ]
        self._validate_intelligent_plan(workouts, profile)

        return {
            "planner_version": "2.0-intelligent",
            "adaptive_features": [
                "recent performance adaptation",
                "recovery-aware set adjustment",
                "muscle-priority weighting",
                "fatigue-aware volume control",
                "time-aware exercise preservation",
                "adaptive progression instructions",
            ],
            "profile": asdict(profile),
            "split": SPLITS[profile.days_per_week],
            "workouts": [asdict(w) for w in workouts],
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
    )
    return PlanGenerator(db_path).generate_plan(profile)



@dataclass
class WeeklyWorkoutResult:
    workout_name: str
    completed: bool = True
    average_difficulty: Optional[float] = None
    average_reps: Optional[float] = None
    notes: str = ""


@dataclass
class WeeklyProgramState:
    """Persistent state for controlling progression from week to week."""
    week_number: int = 1
    consecutive_hard_weeks: int = 0
    missed_workouts: int = 0
    fatigue_score: float = 0.0
    last_week_completion_rate: float = 1.0
    exercise_history: dict[str, dict[str, Any]] = field(default_factory=dict)


class WeeklyProgramController:
    """
    Controls a training program across weeks instead of generating every week
    independently.

    The controller:
      1. records completed/missed workouts,
      2. updates exercise performance history,
      3. estimates fatigue and recovery,
      4. adjusts the next week's programming inputs,
      5. automatically recommends normal progression, maintenance, or a
         reduced-volume recovery week.
    """

    def __init__(self, generator: Optional[PlanGenerator] = None):
        self.generator = generator or PlanGenerator()

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def record_week(
        self,
        state: WeeklyProgramState,
        results: Iterable[WeeklyWorkoutResult],
    ) -> WeeklyProgramState:
        results = list(results)
        if not results:
            return state

        completed = sum(1 for r in results if r.completed)
        completion_rate = completed / len(results)

        difficulties = [
            r.average_difficulty
            for r in results
            if r.completed and isinstance(r.average_difficulty, (int, float))
        ]

        avg_difficulty = (
            sum(difficulties) / len(difficulties)
            if difficulties else None
        )

        # Fatigue rises with difficult work and missed sessions, then partially
        # decays between weeks.
        fatigue = state.fatigue_score * 0.65

        if avg_difficulty is not None:
            fatigue += max(0.0, avg_difficulty - 5.0) * 0.8

        fatigue += (1.0 - completion_rate) * 2.0
        fatigue = self._clamp(fatigue, 0.0, 10.0)

        missed = len(results) - completed

        # Store the latest useful performance signal per exercise/workout.
        history = deepcopy(state.exercise_history)
        for result in results:
            if not result.completed:
                continue

            key = result.workout_name
            history[key] = {
                "difficulty": result.average_difficulty,
                "average_reps": result.average_reps,
                "notes": result.notes,
            }

        hard_week = avg_difficulty is not None and avg_difficulty >= 8.0
        easy_week = avg_difficulty is not None and avg_difficulty <= 5.5

        if hard_week or fatigue >= 7.0:
            consecutive_hard = state.consecutive_hard_weeks + 1
        elif easy_week and fatigue <= 4.0:
            consecutive_hard = max(0, state.consecutive_hard_weeks - 1)
        else:
            consecutive_hard = state.consecutive_hard_weeks

        return WeeklyProgramState(
            week_number=state.week_number + 1,
            consecutive_hard_weeks=consecutive_hard,
            missed_workouts=state.missed_workouts + missed,
            fatigue_score=round(fatigue, 2),
            last_week_completion_rate=round(completion_rate, 3),
            exercise_history=history,
        )

    def _recommendation(self, state: WeeklyProgramState) -> str:
        if state.fatigue_score >= 8.0 or state.consecutive_hard_weeks >= 3:
            return "recovery"
        if state.fatigue_score >= 6.0 or state.last_week_completion_rate < 0.75:
            return "maintenance"
        return "progress"

    def _adjust_profile(
        self,
        profile: UserProfile,
        state: WeeklyProgramState,
        recommendation: str,
    ) -> UserProfile:
        adjusted = deepcopy(profile)

        adjusted.training_state = TrainingState(
            exercise_history=state.exercise_history,
            weekly_fatigue=state.fatigue_score,
            missed_workouts=state.missed_workouts,
        )

        if recommendation == "recovery":
            adjusted.recovery_level = "low"
            adjusted.minutes_per_workout = max(20, round(profile.minutes_per_workout * 0.85))
        elif recommendation == "maintenance":
            adjusted.recovery_level = "normal"
        else:
            adjusted.recovery_level = "high"

        return adjusted

    def generate_next_week(
        self,
        profile: UserProfile,
        state: WeeklyProgramState,
    ) -> dict:
        """
        Generate the next week's program using the current weekly state.

        Returns the plan plus controller decisions explaining why the
        programming changed.
        """
        recommendation = self._recommendation(state)
        adjusted_profile = self._adjust_profile(profile, state, recommendation)

        plan = self.generator.generate_plan(adjusted_profile)

        # Apply a controller-level volume modifier after plan generation.
        if recommendation == "recovery":
            for workout in plan["workouts"]:
                for exercise in workout["exercises"]:
                    exercise["sets"] = max(1, exercise["sets"] - 1)
                workout["estimated_minutes"] = self.generator._estimate_minutes(
                    [
                        PlannedExercise(**exercise)
                        for exercise in workout["exercises"]
                    ]
                )
            controller_note = (
                "Reduced-volume recovery week: fatigue is elevated or "
                "multiple hard weeks have accumulated."
            )
        elif recommendation == "maintenance":
            controller_note = (
                "Maintenance week: preserve the current training structure "
                "while recovery or consistency catches up."
            )
        else:
            controller_note = (
                "Progression week: recovery and consistency support gradual "
                "progression."
            )

        plan["weekly_controller"] = {
            "week_number": state.week_number,
            "recommendation": recommendation,
            "fatigue_score": state.fatigue_score,
            "completion_rate_last_week": state.last_week_completion_rate,
            "consecutive_hard_weeks": state.consecutive_hard_weeks,
            "missed_workouts_total": state.missed_workouts,
            "controller_note": controller_note,
        }

        return plan

    def run_week(
        self,
        profile: UserProfile,
        state: WeeklyProgramState,
        results: Iterable[WeeklyWorkoutResult],
    ) -> tuple[WeeklyProgramState, dict]:
        """Record the finished week and immediately build the next one."""
        new_state = self.record_week(state, results)
        next_plan = self.generate_next_week(profile, new_state)
        return new_state, next_plan


def create_weekly_controller(
    db_path: str | Path = DEFAULT_DB,
) -> WeeklyProgramController:
    """Convenience constructor for app/API integrations."""
    return WeeklyProgramController(PlanGenerator(db_path))




@dataclass
class WeeklyWorkoutResult:
    workout_name: str
    completed: bool = True
    average_difficulty: Optional[float] = None
    average_reps: Optional[float] = None
    notes: str = ""


@dataclass
class WeeklyProgramState:
    """Persistent state for controlling progression from week to week."""
    week_number: int = 1
    consecutive_hard_weeks: int = 0
    missed_workouts: int = 0
    fatigue_score: float = 0.0
    last_week_completion_rate: float = 1.0
    exercise_history: dict[str, dict[str, Any]] = field(default_factory=dict)


class WeeklyProgramController:
    """
    Controls a training program across weeks instead of generating every week
    independently.

    The controller:
      1. records completed/missed workouts,
      2. updates exercise performance history,
      3. estimates fatigue and recovery,
      4. adjusts the next week's programming inputs,
      5. automatically recommends normal progression, maintenance, or a
         reduced-volume recovery week.
    """

    def __init__(self, generator: Optional[PlanGenerator] = None):
        self.generator = generator or PlanGenerator()

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def record_week(
        self,
        state: WeeklyProgramState,
        results: Iterable[WeeklyWorkoutResult],
    ) -> WeeklyProgramState:
        results = list(results)
        if not results:
            return state

        completed = sum(1 for r in results if r.completed)
        completion_rate = completed / len(results)

        difficulties = [
            r.average_difficulty
            for r in results
            if r.completed and isinstance(r.average_difficulty, (int, float))
        ]

        avg_difficulty = (
            sum(difficulties) / len(difficulties)
            if difficulties else None
        )

        # Fatigue rises with difficult work and missed sessions, then partially
        # decays between weeks.
        fatigue = state.fatigue_score * 0.65

        if avg_difficulty is not None:
            fatigue += max(0.0, avg_difficulty - 5.0) * 0.8

        fatigue += (1.0 - completion_rate) * 2.0
        fatigue = self._clamp(fatigue, 0.0, 10.0)

        missed = len(results) - completed

        # Store the latest useful performance signal per exercise/workout.
        history = deepcopy(state.exercise_history)
        for result in results:
            if not result.completed:
                continue

            key = result.workout_name
            history[key] = {
                "difficulty": result.average_difficulty,
                "average_reps": result.average_reps,
                "notes": result.notes,
            }

        hard_week = avg_difficulty is not None and avg_difficulty >= 8.0
        easy_week = avg_difficulty is not None and avg_difficulty <= 5.5

        if hard_week or fatigue >= 7.0:
            consecutive_hard = state.consecutive_hard_weeks + 1
        elif easy_week and fatigue <= 4.0:
            consecutive_hard = max(0, state.consecutive_hard_weeks - 1)
        else:
            consecutive_hard = state.consecutive_hard_weeks

        return WeeklyProgramState(
            week_number=state.week_number + 1,
            consecutive_hard_weeks=consecutive_hard,
            missed_workouts=state.missed_workouts + missed,
            fatigue_score=round(fatigue, 2),
            last_week_completion_rate=round(completion_rate, 3),
            exercise_history=history,
        )

    def _recommendation(self, state: WeeklyProgramState) -> str:
        if state.fatigue_score >= 8.0 or state.consecutive_hard_weeks >= 3:
            return "recovery"
        if state.fatigue_score >= 6.0 or state.last_week_completion_rate < 0.75:
            return "maintenance"
        return "progress"

    def _adjust_profile(
        self,
        profile: UserProfile,
        state: WeeklyProgramState,
        recommendation: str,
    ) -> UserProfile:
        adjusted = deepcopy(profile)

        adjusted.training_state = TrainingState(
            exercise_history=state.exercise_history,
            weekly_fatigue=state.fatigue_score,
            missed_workouts=state.missed_workouts,
        )

        if recommendation == "recovery":
            adjusted.recovery_level = "low"
            adjusted.minutes_per_workout = max(20, round(profile.minutes_per_workout * 0.85))
        elif recommendation == "maintenance":
            adjusted.recovery_level = "normal"
        else:
            adjusted.recovery_level = "high"

        return adjusted

    def generate_next_week(
        self,
        profile: UserProfile,
        state: WeeklyProgramState,
    ) -> dict:
        """
        Generate the next week's program using the current weekly state.

        Returns the plan plus controller decisions explaining why the
        programming changed.
        """
        recommendation = self._recommendation(state)
        adjusted_profile = self._adjust_profile(profile, state, recommendation)

        plan = self.generator.generate_plan(adjusted_profile)

        # Apply a controller-level volume modifier after plan generation.
        if recommendation == "recovery":
            for workout in plan["workouts"]:
                for exercise in workout["exercises"]:
                    exercise["sets"] = max(1, exercise["sets"] - 1)
                workout["estimated_minutes"] = self.generator._estimate_minutes(
                    [
                        PlannedExercise(**exercise)
                        for exercise in workout["exercises"]
                    ]
                )
            controller_note = (
                "Reduced-volume recovery week: fatigue is elevated or "
                "multiple hard weeks have accumulated."
            )
        elif recommendation == "maintenance":
            controller_note = (
                "Maintenance week: preserve the current training structure "
                "while recovery or consistency catches up."
            )
        else:
            controller_note = (
                "Progression week: recovery and consistency support gradual "
                "progression."
            )

        plan["weekly_controller"] = {
            "week_number": state.week_number,
            "recommendation": recommendation,
            "fatigue_score": state.fatigue_score,
            "completion_rate_last_week": state.last_week_completion_rate,
            "consecutive_hard_weeks": state.consecutive_hard_weeks,
            "missed_workouts_total": state.missed_workouts,
            "controller_note": controller_note,
        }

        return plan

    def run_week(
        self,
        profile: UserProfile,
        state: WeeklyProgramState,
        results: Iterable[WeeklyWorkoutResult],
    ) -> tuple[WeeklyProgramState, dict]:
        """Record the finished week and immediately build the next one."""
        new_state = self.record_week(state, results)
        next_plan = self.generate_next_week(profile, new_state)
        return new_state, next_plan


def create_weekly_controller(
    db_path: str | Path = DEFAULT_DB,
) -> WeeklyProgramController:
    """Convenience constructor for app/API integrations."""
    return WeeklyProgramController(PlanGenerator(db_path))



if __name__ == "__main__":
    import json

    profile = UserProfile()
    controller = create_weekly_controller()

    state = WeeklyProgramState()
    state, next_week = controller.run_week(
        profile,
        state,
        [
            WeeklyWorkoutResult("Upper A", completed=True, average_difficulty=7.0),
            WeeklyWorkoutResult("Lower A", completed=True, average_difficulty=7.5),
            WeeklyWorkoutResult("Upper B", completed=True, average_difficulty=6.5),
            WeeklyWorkoutResult("Lower B", completed=False),
        ],
    )

    print(json.dumps(next_week, indent=2))
