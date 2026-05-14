"""
export_eval_vignettes.py — export vignettes for the 10 evaluation personas.

For each persona × model × condition, extracts the vignette text and
saves to data/eval_vignettes.csv.

Run:
    python scripts/export_eval_vignettes.py
"""
import json
import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.text import strip_markdown

ROOT           = Path(__file__).parent.parent
EVAL_PATH      = ROOT / "data/eval_personas.json"
DATA_DIR       = ROOT / "data/output"
OUTPUT_PATH    = ROOT / "data/eval_vignettes.csv"
BLINDED_PATH   = ROOT / "data/eval_vignettes_blinded.csv"
SEED           = 42

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


def load_runs(data_dir: Path) -> dict:
    runs = {}
    for condition_dir in data_dir.iterdir():
        if not condition_dir.is_dir() or condition_dir.name.startswith("_"):
            continue
        for model_dir in condition_dir.iterdir():
            if not model_dir.is_dir():
                continue
            if list(model_dir.glob("experiment_*.json")):
                runs[(model_dir.name, condition_dir.name)] = model_dir
    return runs


def main():
    import random
    rng = random.Random(SEED)

    with open(EVAL_PATH, encoding="utf-8") as f:
        eval_personas = json.load(f)

    eval_ids  = {p["persona_id"]: p for p in eval_personas}
    runs      = load_runs(DATA_DIR)

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
                vignette = strip_markdown(data.get("vignette", ""))
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

    indices = list(range(len(rows)))
    rng.shuffle(indices)
    id_map = {orig_idx: f"V{new_pos+1:03d}" for new_pos, orig_idx in enumerate(indices)}
    for i, row in enumerate(rows):
        row["vignette_id"] = id_map[i]

    rows.sort(key=lambda r: r["vignette_id"])

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

    from collections import Counter
    print(f"Exported {len(rows)} rows -> {OUTPUT_PATH}")
    print(f"Blinded  {len(blinded)} rows -> {BLINDED_PATH}\n")
    print("Rows per condition:")
    for c, n in sorted(Counter(r["condition"] for r in rows).items()):
        print(f"  {c:<20} {n}")
    print(f"\nRows per model:")
    for m, n in sorted(Counter(r["model"] for r in rows).items()):
        print(f"  {m:<35} {n}")

    if missing:
        print(f"\nMissing ({len(missing)}):")
        for model, condition, pid in sorted(missing):
            print(f"  {model:<35} {condition:<20} persona {pid}")


if __name__ == "__main__":
    main()
