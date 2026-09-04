from __future__ import annotations

MUSCLE_TAXONOMY = {
    "Chest": ["Upper Chest", "Mid Chest", "Lower Chest"],
    "Back": ["Lats", "Upper Back", "Traps", "Spinal Erectors"],
    "Shoulders": ["Front Delts", "Side Delts", "Rear Delts"],
    "Biceps": ["Biceps Long Head", "Biceps Short Head", "Brachialis"],
    "Triceps": ["Triceps Long Head", "Triceps Lateral/Medial Heads"],
    "Quads": ["Rectus Femoris", "Vastus Lateralis", "Vastus Medialis"],
    "Hamstrings": ["Biceps Femoris", "Semitendinosus/Semimembranosus"],
    "Glutes": ["Glute Max", "Glute Med/Min", "Adductors"],
    "Calves": ["Gastrocnemius", "Soleus", "Tibialis Anterior"],
    "Core": ["Rectus Abdominis", "Obliques", "Deep Core", "Hip Flexors"],
    "Forearms": ["Wrist Flexors", "Wrist Extensors", "Grip"],
}

TOKEN_TO_PARENT = {
    "chest":"Chest", "upper chest":"Chest", "pecs":"Chest",
    "back":"Back", "lats":"Back", "upper back":"Back", "traps":"Back", "upper traps":"Back", "lower back":"Back", "spinal erectors":"Back",
    "shoulders":"Shoulders", "front delts":"Shoulders", "side delts":"Shoulders", "rear delts":"Shoulders", "delts":"Shoulders",
    "biceps":"Biceps", "brachialis":"Biceps",
    "triceps":"Triceps",
    "quads":"Quads", "quadriceps":"Quads",
    "hamstrings":"Hamstrings",
    "glutes":"Glutes", "adductors":"Glutes", "abductors":"Glutes",
    "calves":"Calves", "gastrocnemius":"Calves", "soleus":"Calves",
    "core":"Core", "abs":"Core", "obliques":"Core", "hip flexors":"Core",
    "forearms":"Forearms", "grip":"Forearms",
    "tibialis anterior":"Calves", "lower leg":"Calves",
}

def _parts(text: str | None) -> list[str]:
    return [x.strip() for x in str(text or "").split(",") if x.strip()]

def parent_for_token(token: str) -> str | None:
    return TOKEN_TO_PARENT.get(token.strip().lower())

def subsections_for_token(token: str, exercise_name: str = "") -> list[str]:
    t=token.strip().lower(); n=exercise_name.lower()
    parent=parent_for_token(token)
    if parent=="Chest":
        if "upper" in t or "incline" in n: return ["Upper Chest"]
        if "lower" in t or "decline" in n or "dip" in n: return ["Lower Chest"]
        return ["Mid Chest"]
    if parent=="Back":
        if "lat" in t or "pulldown" in n or "pull-up" in n or "pull up" in n: return ["Lats"]
        if "trap" in t or "shrug" in n: return ["Traps"]
        if "lower back" in t or "erector" in t or "back extension" in n or "good morning" in n: return ["Spinal Erectors"]
        return ["Upper Back"]
    if parent=="Shoulders":
        if "rear" in t or "reverse" in n or "face pull" in n: return ["Rear Delts"]
        if "side" in t or "lateral" in n: return ["Side Delts"]
        return ["Front Delts"]
    if parent=="Biceps":
        if "brachialis" in t or "hammer" in n: return ["Brachialis"]
        if "incline" in n or "behind" in n: return ["Biceps Long Head"]
        if "preacher" in n or "concentration" in n: return ["Biceps Short Head"]
        return ["Biceps Long Head", "Biceps Short Head"]
    if parent=="Triceps":
        if "overhead" in n or "long head" in t: return ["Triceps Long Head"]
        return ["Triceps Lateral/Medial Heads"]
    if parent=="Quads":
        if "leg extension" in n: return ["Rectus Femoris", "Vastus Lateralis", "Vastus Medialis"]
        return ["Rectus Femoris", "Vastus Lateralis", "Vastus Medialis"]
    if parent=="Hamstrings":
        return ["Biceps Femoris", "Semitendinosus/Semimembranosus"]
    if parent=="Glutes":
        if "adductor" in t or "adduction" in n: return ["Adductors"]
        if "abductor" in t or "abduction" in n or "lateral band" in n: return ["Glute Med/Min"]
        return ["Glute Max"]
    if parent=="Calves":
        if "tibialis" in t or "tibialis" in n: return ["Tibialis Anterior"]
        if "seated" in n or "soleus" in t: return ["Soleus"]
        return ["Gastrocnemius"]
    if parent=="Forearms":
        if "reverse wrist" in n or "extensor" in t: return ["Wrist Extensors"]
        if "grip" in t: return ["Grip"]
        return ["Wrist Flexors"]
    if parent=="Core":
        if "oblique" in t or "rotation" in n or "side plank" in n: return ["Obliques"]
        if "hip flex" in t or "leg raise" in n or "knee raise" in n: return ["Hip Flexors", "Rectus Abdominis"]
        if "anti" in n or "plank" in n or "dead bug" in n or "bird dog" in n: return ["Deep Core"]
        return ["Rectus Abdominis"]
    return []

def exercise_links(exercise: dict) -> list[dict]:
    name=str(exercise.get("name") or "")
    links=[]; seen=set()
    raw=[]
    for token in _parts(exercise.get("primary_muscle")):
        raw.append((token,"primary"))
    for token in _parts(exercise.get("secondary_muscles")):
        raw.append((token,"secondary"))
    for token,role in raw:
        if token.strip().lower()=="legs":
            for parent, subs in (("Quads",["Rectus Femoris","Vastus Lateralis","Vastus Medialis"]),("Hamstrings",["Biceps Femoris","Semitendinosus/Semimembranosus"]),("Glutes",["Glute Max"]),("Calves",["Gastrocnemius","Soleus"])):
                for sub in subs:
                    key=(parent,sub,role)
                    if key not in seen:
                        seen.add(key); links.append({"muscle_group":parent,"sub_muscle":sub,"role":role})
            continue
        parent=parent_for_token(token)
        if not parent: continue
        subs=subsections_for_token(token,name) or MUSCLE_TAXONOMY.get(parent,[])[:1]
        for sub in subs:
            key=(parent,sub,role)
            if key in seen: continue
            seen.add(key)
            links.append({"muscle_group":parent,"sub_muscle":sub,"role":role})
    return links
