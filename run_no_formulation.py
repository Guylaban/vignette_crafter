"""
run_no_formulation.py — run vignette_from_persona (no_formulation mode) for a group of models.

Edit MODELS_TO_RUN to the group you want this terminal to handle.
Run with: python run_no_formulation.py

Suggested parallel split across terminals:
  Terminal 1: CLOUD_MODELS   (OpenAI / Anthropic / Gemini / DeepSeek)
  Terminal 2: LAB_MODELS     (Tailscale server — run after full-formulation lab runs finish)
"""

import copy
import json
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


def existing_ids(run_dir: Path) -> set[int]:
    return {
        int(m.group(1))
        for f in run_dir.iterdir()
        if (m := re.match(r"experiment_(\d+)\.json", f.name))
    }


def find_run(model: str) -> tuple[Path | None, bool]:
    """Return (best_run_dir, is_complete) for this model's no_formulation runs.

    Scans all runs, returns complete run immediately if found, otherwise the
    most populated partial run so we always resume the right directory.
    """
    total = base_cfg["simulation"]["num_personas"]
    best: tuple[Path | None, int] = (None, 0)
    for d in sorted(OUTPUT_DIR.glob("vignette_from_persona_*"),
                    key=lambda d: d.stat().st_mtime, reverse=True):
        files = list(d.glob("experiment_*.json"))
        if not files:
            continue
        try:
            data = json.load(open(files[0], encoding="utf-8"))
            cfg = data.get("config", {})
            if (cfg.get("models", {}).get("vignette_crafter") == model
                    and cfg.get("vignette_mode") == "no_formulation"):
                done = len(existing_ids(d))
                if done >= total:
                    return d, True
                if done > best[1]:
                    best = (d, done)
        except Exception:
            continue
    return best[0], False


def find_latest_run_dir() -> Path:
    dirs = sorted(OUTPUT_DIR.glob("vignette_from_persona_*"),
                  key=lambda d: d.stat().st_mtime, reverse=True)
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

total = base_cfg["simulation"]["num_personas"]

for model in MODELS_TO_RUN:
    print(f"\n{'='*60}")
    print(f"  no_formulation run: {model}")
    print(f"{'='*60}")

    # ── Skip if already complete; resume if incomplete ───────────────────────
    run_dir, is_complete = find_run(model)
    if is_complete:
        print(f"[SKIP] {model} — already complete (500/500)")
        continue

    if run_dir:
        done = existing_ids(run_dir)
        missing = sorted(set(range(1, total + 1)) - done)
        print(f"[RESUME] Found existing run ({len(done)}/{total} done) — filling {len(missing)} missing personas")

        cfg = copy.deepcopy(base_cfg)
        cfg["models"] = {k: model for k in ("persona_validator", "persona_crafter", "vignette_crafter", "vignette_validator")}
        cfg["simulation"]["persona_ids"] = missing

        rc = run_main(cfg, output_dir=run_dir)
        if rc != 0:
            print(f"\n[WARNING] {model} exited with code {rc}")
        else:
            print(f"\n[DONE] {model} completed successfully")
        continue

    # ── Fresh start: test 3 personas first ───────────────────────────────────
    cfg = copy.deepcopy(base_cfg)
    cfg["models"] = {k: model for k in ("persona_validator", "persona_crafter", "vignette_crafter", "vignette_validator")}
    cfg["simulation"]["persona_ids"] = TEST_PERSONA_IDS

    rc = run_main(cfg)
    run_dir = find_latest_run_dir()
    done = existing_ids(run_dir) if run_dir else set()

    if rc != 0 or len(done) < len(TEST_PERSONA_IDS):
        print(f"\n[FAIL] {model} test failed ({len(done)}/{len(TEST_PERSONA_IDS)} personas completed) — skipping")
        continue

    print(f"\n[TEST PASSED] {model} — {len(done)}/{len(TEST_PERSONA_IDS)} OK, continuing with remaining...")

    # ── Continue with remaining personas in the same directory ───────────────
    missing = sorted(set(range(1, total + 1)) - done)
    cfg2 = copy.deepcopy(base_cfg)
    cfg2["models"] = {k: model for k in ("persona_validator", "persona_crafter", "vignette_crafter", "vignette_validator")}
    cfg2["simulation"]["persona_ids"] = missing

    rc2 = run_main(cfg2, output_dir=run_dir)
    if rc2 != 0:
        print(f"\n[WARNING] {model} full run exited with code {rc2}")
    else:
        print(f"\n[DONE] {model} completed successfully")

print("\nAll no_formulation runs finished.")
