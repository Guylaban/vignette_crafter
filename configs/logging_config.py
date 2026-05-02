import logging
from pathlib import Path


def setup_logging(experiment_dir: Path, level: int = logging.INFO) -> None:
    """Configure file-based logging for the simulation.

    Call once at startup (main.py). All modules then use:
        logger = logging.getLogger(__name__)
    and the output goes to <experiment_dir>/simulation.log
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.FileHandler(experiment_dir / "simulation.log", encoding="utf-8")
    handler.setFormatter(formatter)

    # Suppress third-party library noise (openai, httpx, httpcore, langchain, etc.)
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    root.addHandler(handler)


    # Enable full logging only for our own modules
    for name in ("agents", "simulation", "config", "data"):
        logging.getLogger(name).setLevel(level)

    logging.getLogger(__name__).info("Logging initialized → %s", experiment_dir / "simulation.log")
