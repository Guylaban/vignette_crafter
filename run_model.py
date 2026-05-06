"""
run_model.py — run a single vignette_from_persona experiment for one model.

Usage: python run_model.py <model_name> [--mode full|no_formulation]

Examples:
  python run_model.py gpt-5.4
  python run_model.py claude-sonnet-4-6 --mode no_formulation
"""

import argparse
import copy
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

CONFIG_PATH = Path("configs/simulation_config.yaml")
NO_FORMULATION_CONFIG_PATH = Path("configs/no_formulation_test.yaml")

parser = argparse.ArgumentParser()
parser.add_argument("model", help="Model name (e.g. gpt-5.4, claude-haiku-4-5)")
parser.add_argument("--mode", choices=["full", "no_formulation"], default="no_formulation")
args = parser.parse_args()

base_path = NO_FORMULATION_CONFIG_PATH if args.mode == "no_formulation" else CONFIG_PATH

with open(base_path, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

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
