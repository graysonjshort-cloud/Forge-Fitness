
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
import urllib.error
from difflib import SequenceMatcher

FDC_API_KEY=os.getenv("FDC_API_KEY","DEMO_KEY").strip() or "DEMO_KEY"
FDC_BASE=os.getenv("FDC_BASE_URL","https://api.nal.usda.gov/fdc/v1").rstrip("/")
OFF_BASE=os.getenv("OPENFOODFACTS_BASE_URL","https://world.openfoodfacts.org").rstrip("/")
LOOKUP_ENABLED=os.getenv("NUTRITION_LOOKUP_ENABLED","1").strip().lower() not in {"0","false","no","off"}
OFF_ENABLED=os.getenv("OPENFOODFACTS_ENABLED","1").strip().lower() not in {"0","false","no","off"}

NUTRIENT_KEYS={
    "Energy":"calories",
    "Protein":"protein_g",
    "Carbohydrate, by difference":"carbs_g",
    "Total lipid (fat)":"fat_g",
}
MEAL_TYPES={
    "breakfast":"Breakfast","lunch":"Lunch","dinner":"Dinner","snack":"Snack",
    "pre-workout":"Pre-Workout","pre workout":"Pre-Workout",
    "post-workout":"Post-Workout","post workout":"Post-Workout",
}
SIZE_WORDS=("small","medium","large","regular","kids","kid's","6 inch","6-inch","12 inch","12-inch",
            "footlong","half","whole","single","double")
SIZE_SENSITIVE=("sub","sandwich","fries","fry","drink","soda","pizza","bowl","wrap","burger","shake","smoothie","coffee")

def configured() -> bool:
    return bool(LOOKUP_ENABLED and FDC_API_KEY)

class NutritionProviderError(RuntimeError):
    def __init__(self, provider: str, kind: str, detail: str):
        self.provider=provider
        self.kind=kind
        self.detail=detail
        super().__init__(f"{provider}: {kind}: {detail}")

def _http_json(url: str, timeout=10, provider="Nutrition provider") -> dict:
    req=urllib.request.Request(url,headers={
        "Accept":"application/json",
        "User-Agent":"ForgeFitness/14.19 nutrition-provider-stabilization",
    })
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try: detail=exc.read().decode("utf-8",errors="replace")[:220]
        except Exception: detail=""
        kind="authentication" if exc.code in (401,403) else "rate_limit" if exc.code==429 else "http_error"
        raise NutritionProviderError(provider,kind,f"HTTP {exc.code}" + (f": {detail}" if detail else "")) from exc
    except urllib.error.URLError as exc:
        raise NutritionProviderError(provider,"network",str(exc.reason)) from exc
    except TimeoutError as exc:
        raise NutritionProviderError(provider,"timeout","request timed out") from exc
    except json.JSONDecodeError as exc:
        raise NutritionProviderError(provider,"invalid_response","invalid JSON") from exc

def _number(value: str | None) -> float | None:
    if not value:return None
    value=value.strip().lower()
    fractions={"½":0.5,"¼":0.25,"¾":0.75,"⅓":1/3,"⅔":2/3}
    if value in fractions:return fractions[value]
    if "/" in value:
        try:
            a,b=value.split("/",1);return float(a)/float(b)
        except Exception:return None
    try:return float(value)
    except Exception:return None

def meal_type_from_text(text: str) -> str:
    lower=text.lower()
    for key,label in MEAL_TYPES.items():
        if re.search(rf"\b{re.escape(key)}\b",lower):return label
    return "Meal"

def detect_source(text: str) -> str | None:
    # "from Subway", "at Chipotle", "from Nutrition Hub for dinner".
    patterns=[
        r"\bfrom\s+([A-Za-z0-9&'’.\- ]+?)(?=\s+(?:for|at)\s+(?:breakfast|lunch|dinner|snack)\b|[,.!?]|$)",
        r"\bat\s+([A-Za-z0-9&'’.\- ]+?)(?=\s+(?:for)\s+(?:breakfast|lunch|dinner|snack)\b|[,.!?]|$)",
    ]
    for pat in patterns:
        m=re.search(pat,text,re.I)
        if m:
            value=m.group(1).strip(" .")
            # Avoid treating meal-time "at lunch" as a restaurant.
            if value.lower() not in MEAL_TYPES:return value
    return None

def _strip_source(text: str, source: str | None) -> str:
    if not source:return text
    return re.sub(rf"\s+(?:from|at)\s+{re.escape(source)}(?=\s+(?:for\s+)?(?:breakfast|lunch|dinner|snack)?\s*$|[,.!?]|$)",
                  "",text,flags=re.I).strip()

def _strip_lead(text: str) -> str:
    t=text.strip(" .")
    patterns=[
        r"^(?:can you\s+)?(?:please\s+)?(?:add|log|track)\s+",
        r"^(?:i\s+)?(?:just\s+)?(?:had|ate|eaten|have|consumed)\s+",
        r"^(?:for\s+)?(?:breakfast|lunch|dinner|snack|pre[- ]workout|post[- ]workout)\s*(?:i\s+)?(?:had|ate)?\s*",
        r"^(?:my\s+)?(?:breakfast|lunch|dinner|snack)\s+(?:was|is)\s+",
    ]
    changed=True
    while changed:
        changed=False
        for pat in patterns:
            n=re.sub(pat,"",t,flags=re.I).strip()
            if n!=t:t=n;changed=True
    t=re.sub(r"\s+for\s+(?:breakfast|lunch|dinner|snack|pre[- ]workout|post[- ]workout)\s*$","",t,flags=re.I)
    return t.strip(" .")

def split_meal(text: str, source: str | None=None) -> list[str]:
    text=_strip_source(_strip_lead(text),source)
    text=re.sub(r"\s+(?:with|plus)\s+",",",text,flags=re.I)
    # Root beer, mac and cheese, peanut butter and jelly are common compounds.
    protected={
        "mac and cheese":"mac & cheese",
        "peanut butter and jelly":"peanut butter & jelly",
        "root beer":"root_beer",
    }
    lower=text.lower()
    for k,v in protected.items():
        text=re.sub(re.escape(k),v,text,flags=re.I)
    parts=re.split(r"\s*,\s*|\s+and\s+",text,flags=re.I)
    result=[]
    for x in parts:
        x=x.replace("root_beer","root beer").replace("mac & cheese","mac and cheese").replace("peanut butter & jelly","peanut butter and jelly")
        if x.strip(" ."):result.append(x.strip(" ."))
    return result

def _portion(part: str) -> tuple[str,float | None,str | None]:
    m=re.match(
        r"^\s*(\d+(?:\.\d+)?|\d+/\d+|[½¼¾⅓⅔])\s*"
        r"(g|gram|grams|fl oz|fluid ounce|fluid ounces|floz|ml|milliliter|milliliters|l|liter|liters|"
        r"oz|ounce|ounces|lb|lbs|pound|pounds|cup|cups|tbsp|tablespoons?|tsp|teaspoons?|"
        r"slice|slices|piece|pieces|egg|eggs|serving|servings|can|cans|bottle|bottles)?\s+(.+)$",
        part,re.I
    )
    if not m:return part,None,None
    qty=_number(m.group(1));unit=(m.group(2) or "count").lower();food=m.group(3).strip()
    if unit in {"egg","eggs"}:food="egg "+food
    return food,qty,unit

def _grams_for_portion(food: str, qty: float | None, unit: str | None,
                       serving_size=None, serving_unit=None) -> float:
    if qty is None:
        if serving_size and str(serving_unit or "").lower() in {"g","gram","grams"}:
            return float(serving_size)
        return 100.0
    u=(unit or "count").lower()
    if u in {"g","gram","grams"}:return qty
    if u in {"fl oz","fluid ounce","fluid ounces","floz"}:return qty*29.5735
    if u in {"ml","milliliter","milliliters"}:return qty
    if u in {"l","liter","liters"}:return qty*1000.0
    if u in {"oz","ounce","ounces"}:return qty*28.3495
    if u in {"lb","lbs","pound","pounds"}:return qty*453.592
    if u in {"cup","cups"}:return qty*240.0
    if u in {"tbsp","tablespoon","tablespoons"}:return qty*15.0
    if u in {"tsp","teaspoon","teaspoons"}:return qty*5.0
    lower=food.lower()
    if u in {"egg","eggs"} or "egg" in lower:return qty*50.0
    if u in {"slice","slices"}:
        if any(x in lower for x in ["bread","toast","cheese"]):return qty*28.0
        return qty*30.0
    if u in {"can","cans"}:return qty*355.0
    if u in {"bottle","bottles"}:return qty*500.0
    if u in {"serving","servings"} and serving_size and str(serving_unit or "").lower() in {"g","gram","grams"}:
        return qty*float(serving_size)
    if "banana" in lower:return qty*118.0
    if "apple" in lower:return qty*182.0
    if "orange" in lower:return qty*131.0
    return qty*(float(serving_size) if serving_size and str(serving_unit or "").lower() in {"g","gram","grams"} else 100.0)

def _query_similarity(query: str, food: dict, source: str | None) -> float:
    q=query.lower()
    desc=(food.get("description") or "").lower()
    brand=" ".join(str(food.get(k) or "") for k in ("brandOwner","brandName","ingredients")).lower()
    score=SequenceMatcher(None,q,desc).ratio()*30
    if all(tok in desc for tok in re.findall(r"[a-z0-9]+",q) if len(tok)>2):score+=20
    dtype=food.get("dataType","")
    if source:
        s=source.lower()
        if s in brand or s in desc:score+=55
        elif any(tok in brand for tok in s.split() if len(tok)>2):score+=20
        if dtype=="Branded":score+=12
    elif dtype in {"Foundation","SR Legacy","Survey (FNDDS)"}:
        score+=20
    return score

def _fallback_queries(query: str) -> list[str]:
    q=" ".join((query or "").strip().split())
    low=q.lower()
    variants=[q]

    # Normalize common diet/zero-sugar beverage wording.
    if "zero sugar" in low:
        variants.append(re.sub(r"\bzero sugar\b","diet",q,flags=re.I))
        variants.append(re.sub(r"\bzero sugar\b","",q,flags=re.I).strip())
    if "sugar free" in low:
        variants.append(re.sub(r"\bsugar free\b","diet",q,flags=re.I))
        variants.append(re.sub(r"\bsugar free\b","",q,flags=re.I).strip())
    if "diet" in low:
        variants.append(re.sub(r"\bdiet\b","",q,flags=re.I).strip())

    # Remove common size adjectives if the database doesn't index them consistently.
    stripped=re.sub(r"\b(?:small|medium|large|regular|12 inch|12-inch|6 inch|6-inch|footlong)\b","",q,flags=re.I)
    variants.append(" ".join(stripped.split()))

    # Generic soda/root-beer fallback.
    if "root beer" in low:
        variants.extend(["diet root beer","root beer"])
    elif "soda" in low or "coke" in low or "pepsi" in low:
        variants.extend(["diet soda","carbonated beverage"])

    out=[]
    for v in variants:
        v=" ".join(v.split()).strip()
        if v and v.lower() not in {x.lower() for x in out}:
            out.append(v)
    return out

def search_usda(query: str, source: str | None=None) -> dict:
    if not configured():raise RuntimeError("USDA nutrition lookup is disabled")

    candidates=[]
    errors=[]
    for q in _fallback_queries(query):
        search_query=f"{q} {source}" if source else q
        try:
            params=urllib.parse.urlencode({"api_key":FDC_API_KEY,"query":search_query,"pageSize":20})
            foods=(_http_json(FDC_BASE+"/foods/search?"+params,provider="USDA FoodData Central").get("foods") or [])
            if not foods and source:
                params=urllib.parse.urlencode({"api_key":FDC_API_KEY,"query":q,"pageSize":20})
                foods=(_http_json(FDC_BASE+"/foods/search?"+params,provider="USDA FoodData Central").get("foods") or [])
            for food in foods:
                food=dict(food)
                food["_forge_query_used"]=q
                food["_forge_provider"]="USDA FoodData Central"
                food["_forge_source_url"]=f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{food.get('fdcId')}/nutrients" if food.get("fdcId") else "https://fdc.nal.usda.gov/"
                food["_forge_match_score"]=_query_similarity(q,food,source)
                candidates.append(food)
        except Exception as exc:
            errors.append(str(exc))

        # If we already have a strong match, stop broadening.
        if candidates and max(x.get("_forge_match_score",0) for x in candidates)>=55:
            break

    if not candidates:
        raise ValueError("; ".join(errors) or f"No USDA match found for {query}")

    return max(candidates,key=lambda x:x.get("_forge_match_score",0))

def search_openfoodfacts(query: str, source: str | None=None) -> dict:
    if not OFF_ENABLED:raise RuntimeError("OpenFoodFacts fallback disabled")
    search=f"{source} {query}" if source else query
    params=urllib.parse.urlencode({"search_terms":search,"search_simple":1,"action":"process","json":1,"page_size":15})
    products=(_http_json(OFF_BASE+"/cgi/search.pl?"+params,provider="Open Food Facts").get("products") or [])
    if not products:raise ValueError(f"No OpenFoodFacts match found for {query}")
    def score(x):
        name=" ".join(str(x.get(k) or "") for k in ("product_name","brands","generic_name"))
        s=SequenceMatcher(None,search.lower(),name.lower()).ratio()*50
        if source and source.lower() in (x.get("brands") or "").lower():s+=50
        return s
    product=max(products,key=score)
    nutr=product.get("nutriments") or {}
    food={
        "fdcId":None,
        "description":product.get("product_name") or query,
        "brandOwner":product.get("brands"),
        "dataType":"Branded",
        "servingSize":product.get("serving_quantity"),
        "servingSizeUnit":"g",
        "foodNutrients":[
            {"nutrientName":"Energy","value":nutr.get("energy-kcal_100g") or 0},
            {"nutrientName":"Protein","value":nutr.get("proteins_100g") or 0},
            {"nutrientName":"Carbohydrate, by difference","value":nutr.get("carbohydrates_100g") or 0},
            {"nutrientName":"Total lipid (fat)","value":nutr.get("fat_100g") or 0},
        ],
        "_forge_provider":"OpenFoodFacts",
        "_forge_source_url":product.get("url") or "https://world.openfoodfacts.org/",
        "_forge_match_score":score(product),
    }
    return food

def search_food(query: str, source: str | None=None) -> dict:
    errors=[]
    usda=None
    try:
        usda=search_usda(query,source)
        if not source or usda.get("_forge_match_score",0)>=45:return usda
    except Exception as exc:
        errors.append(str(exc))
    try:
        off=search_openfoodfacts(query,source)
        if usda and usda.get("_forge_match_score",0)>=off.get("_forge_match_score",0):return usda
        return off
    except Exception as exc:
        errors.append(str(exc))
    if usda:return usda
    detail=" | ".join(errors) or f"No online nutrition match found for {query}"
    kind="no_match"
    low=detail.lower()
    if "authentication" in low or "http 401" in low or "http 403" in low:kind="authentication"
    elif "rate_limit" in low or "http 429" in low:kind="rate_limit"
    elif "network" in low:kind="network"
    elif "timeout" in low:kind="timeout"
    raise NutritionProviderError("Nutrition providers",kind,detail)

def nutrition_from_food(food: dict, grams: float) -> dict:
    per100={"calories":0.0,"protein_g":0.0,"carbs_g":0.0,"fat_g":0.0}
    for n in food.get("foodNutrients") or []:
        name=n.get("nutrientName") or (n.get("nutrient") or {}).get("name")
        key=NUTRIENT_KEYS.get(name)
        if not key:continue
        value=n.get("value")
        if value is None:value=n.get("amount")
        try:per100[key]=float(value or 0)
        except Exception:pass
    scale=max(0.0,float(grams))/100.0
    return {
        "calories":round(per100["calories"]*scale),
        "protein_g":round(per100["protein_g"]*scale,1),
        "carbs_g":round(per100["carbs_g"]*scale,1),
        "fat_g":round(per100["fat_g"]*scale,1),
    }

def needs_size_clarification(parts: list[str], source: str | None) -> str | None:
    if not source:return None
    for raw in parts:
        low=raw.lower()
        if any(x in low for x in SIZE_SENSITIVE) and not any(x in low for x in SIZE_WORDS):
            clean=re.sub(r"^(?:a|an|the)\s+","",raw.strip(),flags=re.I)
            return f"What size was the {clean} from {source}? If there wasn't a size option, say “regular.”"
    return None

def _generic_fallback_component(raw: str, food_query: str, qty: float | None, unit: str | None) -> dict | None:
    low=food_query.lower().strip()

    # Explicitly support common zero-calorie beverages when online providers fail.
    zero_beverage=(
        ("zero sugar" in low or "diet " in low or "sugar free" in low)
        and any(x in low for x in ["root beer","soda","coke","pepsi","soft drink"])
    )
    if zero_beverage:
        grams=_grams_for_portion(food_query,qty,unit,355,None)
        return {
            "input":raw,
            "query":food_query,
            "restaurant_or_brand":None,
            "matched_food":"Generic zero-sugar soft drink",
            "brand":None,
            "fdc_id":None,
            "data_type":"Forge Generic Fallback",
            "estimated_grams":round(grams,1),
            "calories":0,
            "protein_g":0.0,
            "carbs_g":0.0,
            "fat_g":0.0,
            "provider":"Forge generic estimate",
            "source_url":None,
            "confidence":"generic",
        }
    return None

def provider_health() -> dict:
    result={"nutrition_lookup_enabled":LOOKUP_ENABLED,"providers":{}}
    if not LOOKUP_ENABLED:
        return {"nutrition_lookup_enabled":False,"providers":{
            "usda":{"status":"disabled","detail":"NUTRITION_LOOKUP_ENABLED is off"},
            "openfoodfacts":{"status":"disabled","detail":"NUTRITION_LOOKUP_ENABLED is off"}}}

    if not FDC_API_KEY:
        result["providers"]["usda"]={"status":"misconfigured","detail":"FDC_API_KEY is missing"}
    else:
        try:
            params=urllib.parse.urlencode({"api_key":FDC_API_KEY,"query":"banana","pageSize":1})
            data=_http_json(FDC_BASE+"/foods/search?"+params,timeout=6,provider="USDA FoodData Central")
            result["providers"]["usda"]={"status":"online" if "foods" in data else "degraded","detail":"reachable"}
        except Exception as exc:
            result["providers"]["usda"]={"status":"offline","detail":str(exc)}

    if not OFF_ENABLED:
        result["providers"]["openfoodfacts"]={"status":"disabled","detail":"OPENFOODFACTS_ENABLED is off"}
    else:
        try:
            params=urllib.parse.urlencode({
                "search_terms":"banana","search_simple":1,"action":"process","json":1,
                "page_size":1,"fields":"code,product_name"
            })
            data=_http_json(OFF_BASE+"/cgi/search.pl?"+params,timeout=6,provider="Open Food Facts")
            result["providers"]["openfoodfacts"]={"status":"online" if "products" in data else "degraded","detail":"reachable"}
        except Exception as exc:
            result["providers"]["openfoodfacts"]={"status":"offline","detail":str(exc)}
    return result

def lookup_meal(description: str, correction: str | None=None) -> dict:
    combined=(description+" "+correction).strip() if correction else description
    source=detect_source(combined) or detect_source(description)
    parts=split_meal(description,source)
    clarification=needs_size_clarification(parts,source)
    if clarification and not correction:
        return {
            "description":_strip_source(_strip_lead(description),source),
            "meal_type":meal_type_from_text(description),
            "source_name":source,
            "needs_clarification":True,
            "clarification":clarification,
            "original_text":description,
        }

    # Corrections such as "it was large" should modify the first size-sensitive item.
    if correction:
        corr=correction.lower()
        size=next((x for x in SIZE_WORDS if x in corr),None)
        qty_match=re.search(r"\b(\d+(?:\.\d+)?|\d+/\d+)\s*(g|oz|cups?|slices?|pieces?)\b",corr)
        if size:
            for i,raw in enumerate(parts):
                if any(x in raw.lower() for x in SIZE_SENSITIVE) and not any(x in raw.lower() for x in SIZE_WORDS):
                    parts[i]=f"{size} {raw}";break
        elif qty_match and len(parts)==1:
            parts[0]=f"{qty_match.group(0)} {parts[0]}"

    components=[]
    totals={"calories":0,"protein_g":0.0,"carbs_g":0.0,"fat_g":0.0}
    errors=[]
    providers=[]
    source_urls=[]
    for raw in parts:
        food_query,qty,unit=_portion(raw)
        try:
            food=search_food(food_query,source)
            grams=_grams_for_portion(food_query,qty,unit,food.get("servingSize"),food.get("servingSizeUnit"))
            macros=nutrition_from_food(food,grams)
            for k in totals:totals[k]+=macros[k]
            provider=food.get("_forge_provider") or "USDA FoodData Central"
            url=food.get("_forge_source_url")
            providers.append(provider)
            if url:source_urls.append(url)
            components.append({
                "input":raw,"query":food_query,"restaurant_or_brand":source,
                "matched_food":food.get("description"),"brand":food.get("brandOwner") or food.get("brandName"),
                "fdc_id":food.get("fdcId"),"data_type":food.get("dataType"),
                "estimated_grams":round(grams,1),**macros,
                "provider":provider,"source_url":url,
            })
        except Exception as exc:
            fallback=_generic_fallback_component(raw,food_query,qty,unit)
            if fallback:
                components.append(fallback)
                providers.append(fallback["provider"])
                for k in totals:
                    totals[k]+=fallback[k]
            else:
                errors.append({"input":raw,"error":str(exc)})

    totals["calories"]=round(totals["calories"])
    for k in ("protein_g","carbs_g","fat_g"):totals[k]=round(totals[k],1)
    if not components:
        raise ValueError("I couldn't find a reliable online nutrition match for that meal")

    provider_summary=" + ".join(dict.fromkeys(providers)) or "Online nutrition lookup"
    return {
        "description":_strip_source(_strip_lead(description),source),
        "meal_type":meal_type_from_text(description),
        "source_name":source,
        "totals":totals,"components":components,"errors":errors,
        "source":provider_summary,
        "source_url":source_urls[0] if len(source_urls)==1 else None,
        "source_urls":source_urls,
        "estimated":True,
        "needs_clarification":False,
        "original_text":description,
    }
