"""
run_no_formulation.py — run vignette_from_persona (no_formulation mode) for a group of models.

Edit MODELS_TO_RUN to the group you want this terminal to handle.
Run with: python run_no_formulation.py

Suggested parallel split across terminals:
  Terminal 1: CLOUD_MODELS   (OpenAI / Anthropic / Gemini / DeepSeek)
  Terminal 2: LAB_MODELS     (Tailscale server — run after full-formulation lab runs finish)
"""

import copy
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

BASE_CONFIG_PATH = Path("configs/no_formulation_test.yaml")
OUTPUT_DIR       = Path("data/output")

CLOUD_MODELS = [
    "gpt-5.4",
    "gpt-4o-mini",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "deepseek-reasoner",
    "deepseek-chat",
]

LAB_MODELS = [
    "qwen2.5-32b",
    "qwen3.6-35b",
    "qwen3.6-35b-ablit",
]

# ── Edit this to choose which group this terminal runs ────────────────────────
MODELS_TO_RUN = LAB_MODELS
# MODELS_TO_RUN = CLOUD_MODELS
# ------------------------------------------------------------------------------

# ── Test personas — runs these first; if all pass, continues with the rest ───
TEST_PERSONA_IDS = [1, 2, 3]
# -----------------------------------------------------------------------------


def count_experiments(run_dir: Path) -> int:
    return sum(1 for f in run_dir.iterdir() if re.match(r"experiment_\d+\.json", f.name))


def find_latest_run_dir() -> Path:
    dirs = sorted(
        OUTPUT_DIR.glob("vignette_from_persona_*"),
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    return dirs[0] if dirs else None


def run_main(cfg: dict, output_dir: Path = None) -> int:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        yaml.dump(cfg, tmp, allow_unicode=True)
        tmp_path = tmp.name

    cmd = [sys.executable, "main.py", "--config", tmp_path]
    if output_dir:
        cmd += ["--output-dir", str(output_dir)]

    result = subprocess.run(cmd, check=False)
    Path(tmp_path).unlink(missing_ok=True)
    return result.returncode


with open(BASE_CONFIG_PATH, encoding="utf-8") as f:
    base_cfg = yaml.safe_load(f)

for model in MODELS_TO_RUN:
    print(f"\n{'='*60}")
    print(f"  Starting no_formulation run: {model}")
    print(f"{'='*60}")

    # ── Phase 1: test run ─────────────────────────────────────────────────────
    cfg = copy.deepcopy(base_cfg)
    cfg["models"] = {k: model for k in ("persona_validator", "persona_crafter", "vignette_crafter", "vignette_validator")}
    cfg["simulation"]["persona_ids"] = TEST_PERSONA_IDS

    rc = run_main(cfg)
    run_dir = find_latest_run_dir()
    completed = count_experiments(run_dir) if run_dir else 0

    if rc != 0 or completed < len(TEST_PERSONA_IDS):
        print(f"\n[FAIL] {model} test failed ({completed}/{len(TEST_PERSONA_IDS)} personas completed) — skipping full run")
        continue

    print(f"\n[TEST PASSED] {model} — {completed}/{len(TEST_PERSONA_IDS)} personas OK, continuing with remaining...")

    # ── Phase 2: remaining personas in the same directory ────────────────────
    all_ids = list(range(1, base_cfg["simulation"]["num_personas"] + 1))
    remaining = [i for i in all_ids if i not in TEST_PERSONA_IDS]

    cfg2 = copy.deepcopy(base_cfg)
    cfg2["models"] = {k: model for k in ("persona_validator", "persona_crafter", "vignette_crafter", "vignette_validator")}
    cfg2["simulation"]["persona_ids"] = remaining

    rc2 = run_main(cfg2, output_dir=run_dir)

    if rc2 != 0:
        print(f"\n[WARNING] {model} full run exited with code {rc2}")
    else:
        print(f"\n[DONE] {model} completed successfully")

print("\nAll no_formulation runs finished.")
