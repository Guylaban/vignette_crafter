"""
run_model.py — run a single vignette_from_persona experiment for one model.

Usage: python scripts/run_model.py <model_name> [--mode full|no_formulation|zero_shot]

Examples:
  python scripts/run_model.py gpt-5.4
  python scripts/run_model.py claude-sonnet-4-6 --mode no_formulation
  python scripts/run_model.py gpt-5.4 --mode zero_shot
"""

import argparse
import copy
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent

CONFIG_PATHS = {
    "full":           ROOT / "configs/simulation_config.yaml",
    "no_formulation": ROOT / "configs/no_formulation_config.yaml",
    "zero_shot":      ROOT / "configs/zero_shot_config.yaml",
}

parser = argparse.ArgumentParser()
parser.add_argument("model", help="Model name (e.g. gpt-5.4, claude-haiku-4-5)")
parser.add_argument("--mode", choices=["full", "no_formulation", "zero_shot"], default="no_formulation")
parser.add_argument("--persona_ids", help="Comma-separated persona IDs to run (e.g. 1,2,3)", default=None)
parser.add_argument("--output_dir", help="Write into this existing directory instead of creating a new one", default=None)
args = parser.parse_args()

with open(CONFIG_PATHS[args.mode], encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

if args.persona_ids:
    cfg["simulation"]["persona_ids"] = [int(x) for x in args.persona_ids.split(",")]

if args.mode == "zero_shot":
    cfg["models"] = {"vignette_crafter": args.model}
else:
    cfg["models"] = {
        "persona_validator":  args.model,
        "persona_crafter":    args.model,
        "vignette_crafter":   args.model,
        "vignette_validator": args.model,
    }

with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
    yaml.dump(cfg, tmp, allow_unicode=True)
    tmp_path = tmp.name

print(f"Starting [{args.mode}] run: {args.model}")
cmd = [sys.executable, str(ROOT / "main.py"), "--config", tmp_path]
if args.output_dir:
    cmd += ["--output-dir", args.output_dir]
result = subprocess.run(cmd, check=False)
Path(tmp_path).unlink(missing_ok=True)

if result.returncode != 0:
    print(f"[WARNING] {args.model} exited with code {result.returncode}")
else:
    print(f"[DONE] {args.model} completed successfully")
