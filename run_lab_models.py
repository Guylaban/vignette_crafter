"""
run_lab_models.py — run vignette_from_persona sequentially for all lab models.

Edit MODELS_TO_RUN to skip models already completed or not needed.
Run with: python run_lab_models.py
"""

import copy
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

CONFIG_PATH = Path("configs/simulation_config.yaml")

MODELS_TO_RUN = [
    "llama3.1-70b",
    "qwen2.5-72b",
]

with open(CONFIG_PATH, encoding="utf-8") as f:
    base_cfg = yaml.safe_load(f)

for model in MODELS_TO_RUN:
    print(f"\n{'='*60}")
    print(f"  Starting run: {model}")
    print(f"{'='*60}")

    cfg = copy.deepcopy(base_cfg)
    cfg["models"] = {
        "persona_validator":  model,
        "persona_crafter":    model,
        "vignette_crafter":   model,
        "vignette_validator": model,
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        yaml.dump(cfg, tmp, allow_unicode=True)
        tmp_path = tmp.name

    result = subprocess.run(
        [sys.executable, "main.py", "--config", tmp_path],
        check=False,
    )

    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"\n[WARNING] {model} exited with code {result.returncode} — continuing to next model")
    else:
        print(f"\n[DONE] {model} completed successfully")

print("\nAll lab model runs finished.")
