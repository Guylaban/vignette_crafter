"""
migrate_output_structure.py — reorganise data/output/ from timestamp dirs to
condition/model dirs.

Old:  data/output/vignette_from_persona_20260502_132625/experiment_N.json
New:  data/output/full/claude-haiku-4-5/experiment_N.json

Run once:
    python scripts/migrate_output_structure.py [--dry-run]
"""
import json
import shutil
import argparse
from pathlib import Path
from collections import defaultdict

ROOT       = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "data/output"

SKIP = {
    # llama3.1-70b no_formulation run is still in progress — migrate manually after
    ("no_formulation", "llama3.1-70b"),
}

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", help="Print plan without moving files")
args = parser.parse_args()
DRY = args.dry_run

if DRY:
    print("=== DRY RUN — no files will be moved ===\n")


def detect_run(d: Path):
    files = list(d.glob("experiment_*.json"))
    if not files:
        return None, None
    try:
        with open(files[0], encoding="utf-8") as f:
            cfg = json.load(f).get("config", {})
        model     = next(iter(cfg.get("models", {}).values()), None)
        condition = cfg.get("vignette_mode")
        return condition, model
    except Exception:
        return None, None


# ── 1. Group existing dirs by (condition, model) ─────────────────────────────
groups: dict[tuple, list[tuple[Path, int]]] = defaultdict(list)
old_dirs: list[Path] = []

for d in OUTPUT_DIR.iterdir():
    if not d.is_dir():
        continue
    if d.name in ("full", "no_formulation", "zero_shot", "_archive"):
        continue  # already migrated
    files = list(d.glob("experiment_*.json"))
    condition, model = detect_run(d)
    if condition and model:
        groups[(condition, model)].append((d, len(files)))
        old_dirs.append(d)
    elif files:
        # Unknown condition (old format) → archive
        groups[("_archive", d.name)].append((d, len(files)))
        old_dirs.append(d)

# ── 2. Migrate each group ─────────────────────────────────────────────────────
for (condition, model), runs in sorted(groups.items()):
    if (condition, model) in SKIP:
        print(f"  SKIP  {condition}/{model}  (run in progress)")
        continue

    runs.sort(key=lambda x: x[1], reverse=True)  # largest first
    dest = OUTPUT_DIR / condition / model
    total_files = sum(r[1] for r in runs)
    print(f"  >>  {condition}/{model:<35}  {len(runs)} run(s), {total_files} total files  ->  {dest.relative_to(ROOT)}")

    if not DRY:
        dest.mkdir(parents=True, exist_ok=True)

        # Collect all experiment files, dedupe by persona_id keeping latest mtime
        seen: dict[str, tuple[Path, float]] = {}
        for src_dir, _ in runs:
            for fp in src_dir.glob("experiment_*.json"):
                key = fp.name
                mtime = fp.stat().st_mtime
                if key not in seen or mtime > seen[key][1]:
                    seen[key] = (fp, mtime)

        for fname, (src_fp, _) in seen.items():
            dst_fp = dest / fname
            if not dst_fp.exists():
                shutil.copy2(src_fp, dst_fp)

        print(f"       {len(seen)} files written")

# ── 3. Remove old dirs ────────────────────────────────────────────────────────
if not DRY:
    print("\nRemoving old timestamp directories...")
    for d in old_dirs:
        condition, model = detect_run(d)
        if condition and (condition, model) in SKIP:
            continue
        shutil.rmtree(d)
        print(f"  deleted  {d.name}")

print("\nDone.")
