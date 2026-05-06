"""Entry point — loads a simulation config YAML and runs the experiment."""
import argparse
import logging
from datetime import datetime
from pathlib import Path

import yaml

from agents.base_agent import set_experiment_dir
from configs.logging_config import setup_logging
from simulation.runner import SimulationRunner


def main():
    parser = argparse.ArgumentParser(description="Run a vignette simulation.")
    parser.add_argument(
        "--config", "-c",
        default="configs/simulation_config.yaml",
        help="Path to the simulation YAML config (default: configs/simulation_config.yaml)",
    )
    parser.add_argument(
        "--persona-source", "-p",
        default=None,
        help="Path to source experiment dir (overrides persona_source in YAML, used with vignette_from_persona)",
    )
    parser.add_argument(
        "--pipeline",
        default=None,
        help="Pipeline to run (overrides pipeline in YAML): vignette_full, vignette_from_persona, zero_shot, ...",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Write results into this existing directory instead of creating a new timestamped one.",
    )
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    sim  = cfg["simulation"]
    models = cfg["models"]

    pipeline = args.pipeline or sim.get("pipeline", "vignette")
    if args.output_dir:
        experiment_dir = Path(args.output_dir)
    else:
        timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_dir = Path("data/output") / f"{pipeline}_{timestamp}"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(experiment_dir)
    set_experiment_dir(experiment_dir)

    _MODE_FLAGS = {
        "full":           {"persona_context": True,  "use_formulation": True},
        "no_formulation": {"persona_context": True,  "use_formulation": False},
        "zero_shot":      {"persona_context": False, "use_formulation": False},
    }
    vignette_mode = sim.get("vignette_mode", "full")
    flags = _MODE_FLAGS.get(vignette_mode, _MODE_FLAGS["full"])

    runner = SimulationRunner(
        num_personas    = sim["num_personas"],
        persona_ids     = sim.get("persona_ids"),
        seed            = sim["seed"],
        max_retries     = sim["max_retries"],
        temperature     = sim["temperature"],
        pipeline        = pipeline,
        vignette_mode   = vignette_mode,
        persona_context  = flags["persona_context"],
        use_formulation  = flags["use_formulation"],
        n_items          = sim["self_report_items"],
        node_prob        = sim.get("node_prob", 0.7),
        edge_prob        = sim.get("edge_prob", 0.5),
        models          = models,
        experiment_dir  = experiment_dir,
        persona_source  = args.persona_source or sim.get("persona_source"),
    )
    runner.run()


if __name__ == "__main__":
    main()
