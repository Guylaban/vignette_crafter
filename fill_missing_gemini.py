"""
fill_missing_gemini.py — fill in missing personas for incomplete Gemini runs.

Detects which experiment_*.json files are absent in each run directory and
re-runs only those persona IDs, writing results back into the original directory.

Run with: python fill_missing_gemini.py
"""

import copy
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

CONFIG_PATH = Path("configs/simulation_config.yaml")
OUTPUT_DIR  = Path("data/output")

RUNS = [
    # gemini-2.5-pro full: 12 missing
    {
        "model":  "gemini-2.5-pro",
        "dir":    "vignette_from_persona_20260502_152558",
        "total":  500,
    },
    # qwen3.6-35b no_formulation: 3 missing (310, 311, 312)
    {
        "model":  "qwen3.6-35b",
        "dir":    "vignette_from_persona_20260507_020840",
        "total":  500,
        "config": "configs/no_formulation_test.yaml",
    },
]


def find_missing(run_dir: Path, total: int) -> list[int]:
    existing = {
        int(m.group(1))
        for f in run_dir.iterdir()
        if (m := re.match(r"experiment_(\d+)\.json", f.name))
    }
    return sorted(set(range(1, total + 1)) - existing)


for run in RUNS:
    run_dir = OUTPUT_DIR / run["dir"]
    missing = find_missing(run_dir, run["total"])

    if not missing:
        print(f"[SKIP] {run['model']} — already complete")
        continue

    print(f"\n{'='*60}")
    print(f"  {run['model']} ({run.get('config', CONFIG_PATH)}): filling {len(missing)} missing persona(s)")
    print(f"{'='*60}")

    cfg_path = run.get("config", CONFIG_PATH)
    with open(cfg_path, encoding="utf-8") as f:
        base_cfg = yaml.safe_load(f)

    cfg = copy.deepcopy(base_cfg)
    cfg["simulation"]["persona_ids"] = missing
    cfg["models"] = {
        "persona_validator":  run["model"],
        "persona_crafter":    run["model"],
        "vignette_crafter":   run["model"],
        "vignette_validator": run["model"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        yaml.dump(cfg, tmp, allow_unicode=True)
        tmp_path = tmp.name

    result = subprocess.run(
        [sys.executable, "main.py", "--config", tmp_path, "--output-dir", str(run_dir)],
        check=False,
    )

    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"\n[WARNING] {run['model']} exited with code {result.returncode}")
    else:
        print(f"\n[DONE] {run['model']} fill complete")

print("\nAll fill runs finished.")
