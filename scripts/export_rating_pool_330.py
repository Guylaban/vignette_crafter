"""
export_rating_pool_330.py

Sample 10 persona IDs × 11 models × 3 conditions = 330 vignettes.
The same 10 persona IDs are used across every model/condition so cross-condition
comparisons are possible.

Outputs:
  data/eval_vignettes_330.csv   — full CSV with metadata
  data/rating_pool.json         — replaces the old pool used by rating_app/
"""

import csv
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.text import strip_markdown

ROOT       = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "data" / "output"
DATA_DIR   = ROOT / "data"

SEED = 77
N_PERSONAS = 10

EVAL_MODELS = [
    "claude-haiku-4-5", "claude-sonnet-4-6",
    "deepseek-chat", "deepseek-reasoner",
    "gemini-2.5-flash", "gemini-2.5-pro",
    "gpt-4o-mini", "gpt-5.4", "gpt-5.4-mini",
    "qwen2.5-32b", "qwen3.6-35b",
]
CONDITIONS = ["full", "no_formulation", "zero_shot"]


def get_persona_ids(model: str, condition: str) -> set[str]:
    d = OUTPUT_DIR / condition / model
    ids = set()
    for fp in d.glob("experiment_*.json"):
        if "_summary" in fp.name:
            continue
        m = re.search(r"experiment_(\w+)\.json$", fp.name)
        if m:
            ids.add(m.group(1))
    return ids


def main():
    rng = random.Random(SEED)

    # Use the same personas as the original eval pool
    sampled_ids = sorted(["112", "122", "142", "149", "239", "252", "299", "311", "384", "403"])
    print(f"Using fixed persona IDs: {sampled_ids}")

    # Collect all vignettes
    rows = []
    missing = []
    for model in EVAL_MODELS:
        for cond in CONDITIONS:
            for pid in sampled_ids:
                fp = OUTPUT_DIR / cond / model / f"experiment_{pid}.json"
                try:
                    with open(fp, encoding="utf-8") as f:
                        data = json.load(f)
                    text = strip_markdown(data.get("vignette", ""))
                    if not text:
                        missing.append((model, cond, pid))
                        continue
                    rows.append({
                        "persona_id": pid,
                        "model":      model,
                        "condition":  cond,
                        "vignette":   text,
                    })
                except Exception as e:
                    missing.append((model, cond, pid))
                    print(f"  [warn] {model}/{cond}/{pid}: {e}")

    print(f"\nCollected {len(rows)} vignettes  (expected {len(EVAL_MODELS)*len(CONDITIONS)*N_PERSONAS})")
    if missing:
        print(f"Missing {len(missing)}: {missing[:5]}{'...' if len(missing)>5 else ''}")

    # Shuffle and assign V001–V330 IDs
    indices = list(range(len(rows)))
    rng.shuffle(indices)
    id_map = {orig: f"V{new+1:03d}" for new, orig in enumerate(indices)}
    for i, row in enumerate(rows):
        row["vignette_id"] = id_map[i]

    rows.sort(key=lambda r: r["vignette_id"])

    # Save CSV
    csv_path = DATA_DIR / "eval_vignettes_330.csv"
    fieldnames = ["vignette_id", "persona_id", "model", "condition", "vignette"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved CSV  -> {csv_path}")

    # Save rating_pool.json
    pool = [{"vignette_id": r["vignette_id"], "persona_id": r["persona_id"],
             "model": r["model"], "condition": r["condition"], "vignette": r["vignette"]}
            for r in rows]
    pool_path = DATA_DIR / "rating_pool.json"
    with open(pool_path, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)
    print(f"Saved pool -> {pool_path}  ({len(pool)} vignettes)")

    # Summary
    from collections import Counter
    print("\nPer condition:")
    for c, n in sorted(Counter(r["condition"] for r in rows).items()):
        print(f"  {c:<20} {n}")
    print("\nPer model:")
    for m, n in sorted(Counter(r["model"] for r in rows).items()):
        print(f"  {m:<30} {n}")
    print(f"\nPersona IDs used: {sampled_ids}")


if __name__ == "__main__":
    main()
