"""
loader.py — utilities for reading experiment outputs from disk.
"""

import json
import re
from pathlib import Path

import yaml

# Navigate from streamlit_app/utils/ up two levels to the project root.
PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_experiments() -> list[dict]:
    """
    Return all experiment directories under data/output/{condition}/{model}/.

    Each item:  {"path": Path, "name": str, "condition": str, "model": str}
    """
    output_dir = PROJECT_ROOT / "data" / "output"
    if not output_dir.exists():
        return []

    experiments = []
    for condition_dir in sorted(output_dir.iterdir()):
        if not condition_dir.is_dir() or condition_dir.name.startswith("_"):
            continue
        for model_dir in sorted(condition_dir.iterdir()):
            if not model_dir.is_dir():
                continue
            if not list(model_dir.glob("experiment_*.json")):
                continue
            experiments.append({
                "path":      model_dir,
                "name":      f"{condition_dir.name} / {model_dir.name}",
                "condition": condition_dir.name,
                "model":     model_dir.name,
                "timestamp": f"{condition_dir.name}  |  {model_dir.name}",
            })
    return experiments


def get_personas(experiment_dir: Path) -> list[dict]:
    """
    Return persona result files inside *experiment_dir*.

    Each item:  {"path": Path, "persona_id": str}
    """
    personas = []
    for json_file in sorted(experiment_dir.glob("experiment_*.json")):
        if json_file.name.endswith("_summary.json"):
            continue
        m = re.search(r"experiment_(\w+)\.json$", json_file.name)
        persona_id = m.group(1) if m else json_file.stem
        personas.append({"path": json_file, "persona_id": persona_id})
    return personas


def load_persona(json_path: Path) -> dict:
    """Load and return the persona result JSON as a dict."""
    with open(json_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(experiment_dir: Path) -> list[str]:
    """Read simulation.log and return its lines."""
    log_path = experiment_dir / "simulation.log"
    if not log_path.exists():
        return []
    with open(log_path, "r", encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh.readlines()]


def load_config() -> dict:
    """Load configs/simulation_config.yaml. Returns {} if missing."""
    config_path = PROJECT_ROOT / "configs" / "simulation_config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def get_context_files(experiment_dir: Path, persona_id: str) -> list[dict]:
    """
    Load all per-call context JSON files for *persona_id*.

    Each item:  {"filename": str, "data": dict}
    """
    context_dir = experiment_dir / "context" / f"persona_{persona_id}"
    if not context_dir.exists():
        # backward compat: old runs used patient_ prefix
        context_dir = experiment_dir / "context" / f"patient_{persona_id}"
    if not context_dir.exists():
        context_dir = experiment_dir / "context"
    if not context_dir.exists():
        return []

    results = []
    for json_file in sorted(context_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            data = {}
        results.append({"filename": json_file.name, "data": data})
    return results
