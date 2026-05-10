"""
Build the vignette rating pool from experiment outputs.

Run once after all runs (full / no_formulation / zero_shot) are complete:
    python prepare_rating_pool.py

Output: data/rating_pool.json
"""
import json
import random
from collections import Counter
from pathlib import Path

DATA_DIR    = Path("data/output")
OUTPUT_PATH = Path("data/rating_pool.json")

N_PER_GROUP = 5   # vignettes per (model, condition) pair
SEED        = 55


def best_dir_per_group(data_dir: Path) -> dict:
    groups: dict[tuple, list] = {}
    for d in data_dir.iterdir():
        if not d.is_dir():
            continue
        files = list(d.glob("experiment_*.json"))
        if not files:
            continue
        try:
            with open(files[0], encoding="utf-8") as f:
                cfg = json.load(f).get("config", {})
            models    = cfg.get("models", {})
            model     = next(iter(models.values())) if models else None
            condition = cfg.get("vignette_mode")
            if not model or not condition:
                continue
            groups.setdefault((model, condition), []).append((d, len(files)))
        except Exception:
            continue
    return {key: max(dirs, key=lambda x: x[1])[0] for key, dirs in groups.items()}


def main():
    rng  = random.Random(SEED)
    runs = best_dir_per_group(DATA_DIR)

    print(f"Found {len(runs)} (model, condition) groups:\n")
    for (model, cond), path in sorted(runs.items()):
        n = len(list(path.glob("experiment_*.json")))
        print(f"  {model:<35} {cond:<15} {n:>4} vignettes")

    pool = []
    for (model, condition), run_dir in sorted(runs.items()):
        files = list(run_dir.glob("experiment_*.json"))
        rng.shuffle(files)
        for fp in files[:N_PER_GROUP]:
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                text = data.get("vignette", "").strip()
                if not text:
                    continue
                pool.append({
                    "persona_id": data.get("persona_id"),
                    "model":      model,
                    "condition":  condition,
                    "vignette":   text,
                })
            except Exception as e:
                print(f"  [warn] {fp.name}: {e}")

    rng.shuffle(pool)
    for i, item in enumerate(pool):
        item["vignette_id"] = i

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

    print(f"\nPool saved: {len(pool)} vignettes -> {OUTPUT_PATH}")
    print("By condition:", dict(Counter(v["condition"] for v in pool)))
    print("By model:    ", dict(sorted(Counter(v["model"] for v in pool).items())))


if __name__ == "__main__":
    main()
