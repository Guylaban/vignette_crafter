"""
run_model.py — run a single vignette_from_persona experiment for one model.

Usage: python run_model.py <model_name> [--mode full|no_formulation|zero_shot]

Examples:
  python run_model.py gpt-5.4
  python run_model.py claude-sonnet-4-6 --mode no_formulation
  python run_model.py gpt-5.4 --mode zero_shot
"""

import argparse
import copy
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

CONFIG_PATHS = {
    "full":           Path("configs/simulation_config.yaml"),
    "no_formulation": Path("configs/no_formulation_test.yaml"),
    "zero_shot":      Path("configs/zero_shot_config.yaml"),
}

parser = argparse.ArgumentParser()
parser.add_argument("model", help="Model name (e.g. gpt-5.4, claude-haiku-4-5)")
parser.add_argument("--mode", choices=["full", "no_formulation", "zero_shot"], default="no_formulation")
args = parser.parse_args()

with open(CONFIG_PATHS[args.mode], encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

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
result = subprocess.run([sys.executable, "main.py", "--config", tmp_path], check=False)
Path(tmp_path).unlink(missing_ok=True)

if result.returncode != 0:
    print(f"[WARNING] {args.model} exited with code {result.returncode}")
else:
    print(f"[DONE] {args.model} completed successfully")
