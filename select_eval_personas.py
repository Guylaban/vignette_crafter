"""
select_eval_personas.py — stratified sampling of 10 evaluation personas.

Selects 10 personas from the 500-persona pool to serve as the core evaluation
set. Stratification ensures coverage of gender, age group, ethnicity, trauma
category, and PCL-5 severity.

Run once:
    python select_eval_personas.py

Output: data/eval_personas.json
"""
import json
import random
from pathlib import Path

PERSONA_DIR = Path("data/output/craft_persona_20260501_184525")
OUTPUT_PATH = Path("data/eval_personas.json")
SEED        = 42
N           = 10


# ── Strata definitions ────────────────────────────────────────────────────────

def age_group(age):
    if age <= 30: return "young"
    if age <= 54: return "middle"
    return "older"

def pcl5_band(pcl5):
    if pcl5 <= 45: return "mild"
    if pcl5 <= 60: return "moderate"
    return "severe"

TRAUMA_CATEGORIES = {
    "interpersonal": {
        "Rape", "Sexual assault", "Physical abuse by romantic partner",
        "Physical abuse by caregiver (childhood)", "Stalking",
        "Witnessed domestic violence (childhood)", "Assault", "Mugging or robbery",
        "Torture", "Captivity",
    },
    "combat_occupational": {
        "Combat", "Military", "Police", "Police violence",
        "Relief worker in war zone", "Civilian in war zone", "Terrorism", "Refugee",
    },
    "accident_disaster": {
        "Life-threatening accident", "Life-threatening motor vehicle collision",
        "Natural disaster", "Man-made disaster", "Toxic chemical exposure",
    },
    "loss_medical": {
        "Unexpected or traumatic death of a loved one", "Trauma to a loved one",
        "Child's life-threatening illness", "Life-threatening illness",
        "Accidentally caused serious injury to another",
    },
    "other": set(),
}

def trauma_category(trauma):
    for cat, types in TRAUMA_CATEGORIES.items():
        if trauma in types:
            return cat
    return "other"


# ── Load personas ─────────────────────────────────────────────────────────────

def load_personas():
    personas = []
    for fp in sorted(PERSONA_DIR.glob("experiment_*.json")):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            demo = data.get("demographics", {})
            personas.append({
                "persona_id":      data["persona_id"],
                "age":             demo.get("age"),
                "gender":          demo.get("gender"),
                "ethnicity":       demo.get("ethnicity"),
                "trauma_type":     demo.get("trauma_type"),
                "pcl5":            demo.get("pcl5"),
                "occupation":      demo.get("occupation"),
                "relationship_status": demo.get("relationship_status"),
                "age_group":       age_group(demo["age"]),
                "pcl5_band":       pcl5_band(demo["pcl5"]),
                "trauma_category": trauma_category(demo.get("trauma_type", "")),
            })
        except Exception:
            continue
    return personas


# ── Stratified sampling ───────────────────────────────────────────────────────

def stratified_sample(personas, n, seed):
    rng = random.Random(seed)

    # Target one persona per trauma_category, with demographic diversity constraints
    strata_targets = [
        {"trauma_category": "interpersonal",        "gender": "Female", "pcl5_band": "severe"},
        {"trauma_category": "combat_occupational",  "gender": "Male",   "age_group": "middle"},
        {"trauma_category": "accident_disaster",    "gender": "Male",   "age_group": "young"},
        {"trauma_category": "loss_medical",         "gender": "Female", "age_group": "older"},
        {"trauma_category": "other",                "pcl5_band": "moderate"},
    ]

    selected = []
    used_ids = set()
    used_trauma_types = set()

    def matches(p, criteria):
        return all(p.get(k) == v for k, v in criteria.items())

    def pick(criteria, exclude_traumas=True):
        candidates = [
            p for p in personas
            if p["persona_id"] not in used_ids
            and matches(p, criteria)
            and (not exclude_traumas or p["trauma_type"] not in used_trauma_types)
        ]
        if not candidates:
            # Relax trauma uniqueness constraint
            candidates = [p for p in personas
                          if p["persona_id"] not in used_ids and matches(p, criteria)]
        if not candidates:
            return None
        chosen = rng.choice(candidates)
        used_ids.add(chosen["persona_id"])
        used_trauma_types.add(chosen["trauma_type"])
        return chosen

    # Fill one per trauma category
    for target in strata_targets:
        if len(selected) >= n:
            break
        p = pick(target)
        if p:
            selected.append(p)

    # Fill remaining 5 slots: unique trauma type + ethnicity/gender diversity
    ethnicities_covered = {p["ethnicity"] for p in selected}
    genders_covered     = {p["gender"] for p in selected}

    # Try to get remaining from underrepresented trauma types and ethnicities
    remaining = [p for p in personas if p["persona_id"] not in used_ids]
    rng.shuffle(remaining)

    # Sort by how "new" their trauma type and ethnicity are (unseen ones first)
    def diversity_score(p):
        return (
            (0 if p["trauma_type"] not in used_trauma_types else 1),
            (0 if p["ethnicity"] not in ethnicities_covered else 1),
            (0 if p["gender"] not in genders_covered else 1),
        )

    remaining.sort(key=diversity_score)
    for p in remaining:
        if len(selected) >= n:
            break
        selected.append(p)
        used_ids.add(p["persona_id"])
        used_trauma_types.add(p["trauma_type"])
        ethnicities_covered.add(p["ethnicity"])
        genders_covered.add(p["gender"])

    return selected


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    personas = load_personas()
    print(f"Loaded {len(personas)} personas")

    selected = stratified_sample(personas, N, SEED)

    print(f"\nSelected {len(selected)} evaluation personas:\n")
    print(f"{'ID':>4}  {'Gender':<8} {'Age':>3} {'Age group':<8} {'Ethnicity':<22} {'Trauma category':<22} {'PCL-5':>5} {'Band'}")
    print("-" * 100)
    for p in sorted(selected, key=lambda x: x["persona_id"]):
        print(f"{p['persona_id']:>4}  {p['gender']:<8} {p['age']:>3} {p['age_group']:<8} "
              f"{p['ethnicity']:<22} {p['trauma_category']:<22} {p['pcl5']:>5} {p['pcl5_band']}")

    print(f"\nGender:           {dict(zip(*zip(*[(p['gender'],1) for p in selected])))}")

    from collections import Counter
    print(f"Gender:           {dict(Counter(p['gender'] for p in selected))}")
    print(f"Age group:        {dict(Counter(p['age_group'] for p in selected))}")
    print(f"Trauma category:  {dict(Counter(p['trauma_category'] for p in selected))}")
    print(f"PCL-5 band:       {dict(Counter(p['pcl5_band'] for p in selected))}")
    print(f"Ethnicities:      {dict(Counter(p['ethnicity'] for p in selected))}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = [
        {k: v for k, v in p.items() if k not in ("age_group", "pcl5_band", "trauma_category")}
        for p in selected
    ]
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nSaved -> {OUTPUT_PATH}")
    print(f"Persona IDs: {sorted(p['persona_id'] for p in selected)}")


if __name__ == "__main__":
    main()
