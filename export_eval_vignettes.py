"""
export_eval_vignettes.py — export vignettes for the 10 evaluation personas.

For each persona × model × condition, extracts the vignette text and
saves to data/eval_vignettes.csv.

Run:
    python export_eval_vignettes.py
"""
import json
import csv
from pathlib import Path
from collections import defaultdict

EVAL_PATH      = Path("data/eval_personas.json")
DATA_DIR       = Path("data/output")
OUTPUT_PATH    = Path("data/eval_vignettes.csv")
BLINDED_PATH   = Path("data/eval_vignettes_blinded.csv")
SEED           = 42

# The 10 models selected for evaluation (must have all 3 conditions × 10 personas)
EVAL_MODELS = {
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-4o-mini",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "gemini-2.5-flash",
    "deepseek-chat",
    "deepseek-reasoner",
    "qwen2.5-32b",
    "qwen3.6-35b",
}


def best_dir_per_group(data_dir: Path) -> dict:
    groups = defaultdict(list)
    for d in data_dir.iterdir():
        if not d.is_dir() or d.name.startswith("craft_persona"):
            continue
        files = list(d.glob("experiment_*.json"))
        if not files:
            continue
        try:
            with open(files[0], encoding="utf-8") as f:
                cfg = json.load(f).get("config", {})
            model     = next(iter(cfg.get("models", {}).values()), None)
            condition = cfg.get("vignette_mode")
            if model and condition:
                groups[(model, condition)].append((d, len(files)))
        except Exception:
            continue
    return {key: max(dirs, key=lambda x: x[1])[0] for key, dirs in groups.items()}


def main():
    import random
    rng = random.Random(SEED)

    with open(EVAL_PATH, encoding="utf-8") as f:
        eval_personas = json.load(f)

    eval_ids  = {p["persona_id"]: p for p in eval_personas}
    runs      = best_dir_per_group(DATA_DIR)

    print(f"Eval personas: {sorted(eval_ids)}")
    print(f"Found {len(runs)} (model, condition) groups\n")

    rows = []
    missing = []

    for (model, condition), run_dir in sorted(runs.items()):
        if model not in EVAL_MODELS:
            continue
        for pid, demo in eval_ids.items():
            fp = run_dir / f"experiment_{pid}.json"
            if not fp.exists():
                missing.append((model, condition, pid))
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                vignette = data.get("vignette", "").strip()
                if not vignette:
                    missing.append((model, condition, pid))
                    continue
                rows.append({
                    "persona_id":          pid,
                    "model":               model,
                    "condition":           condition,
                    "age":                 demo.get("age"),
                    "gender":              demo.get("gender"),
                    "ethnicity":           demo.get("ethnicity"),
                    "trauma_type":         demo.get("trauma_type"),
                    "pcl5":                demo.get("pcl5"),
                    "occupation":          demo.get("occupation"),
                    "relationship_status": demo.get("relationship_status"),
                    "vignette":            vignette,
                })
            except Exception as e:
                missing.append((model, condition, pid))
                print(f"  [warn] {model} / {condition} / persona {pid}: {e}")

    # Assign shuffled vignette IDs
    indices = list(range(len(rows)))
    rng.shuffle(indices)
    id_map = {orig_idx: f"V{new_pos+1:03d}" for new_pos, orig_idx in enumerate(indices)}
    for i, row in enumerate(rows):
        row["vignette_id"] = id_map[i]

    # Sort full CSV by vignette_id for readability
    rows.sort(key=lambda r: r["vignette_id"])

    # Write full CSV (internal)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["vignette_id", "persona_id", "model", "condition",
                  "age", "gender", "ethnicity", "trauma_type", "pcl5",
                  "occupation", "relationship_status", "vignette"]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    blinded = [{"vignette_id": r["vignette_id"], "vignette": r["vignette"]} for r in rows]
    with open(BLINDED_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["vignette_id", "vignette"])
        writer.writeheader()
        writer.writerows(blinded)

    # Summary
    from collections import Counter
    print(f"Exported {len(rows)} rows -> {OUTPUT_PATH}")
    print(f"Blinded  {len(blinded)} rows -> {BLINDED_PATH}\n")

    model_counts = Counter(r["model"] for r in rows)
    cond_counts  = Counter(r["condition"] for r in rows)
    print("Rows per condition:")
    for c, n in sorted(cond_counts.items()):
        print(f"  {c:<20} {n}")
    print(f"\nRows per model:")
    for m, n in sorted(model_counts.items()):
        print(f"  {m:<35} {n}")

    if missing:
        print(f"\nMissing ({len(missing)}):")
        for model, condition, pid in sorted(missing):
            print(f"  {model:<35} {condition:<20} persona {pid}")


if __name__ == "__main__":
    main()
