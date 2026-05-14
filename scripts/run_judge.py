"""
run_judge.py — LLM-as-a-judge evaluation of vignettes.

Usage:
    python scripts/run_judge.py gpt-5.4
    python scripts/run_judge.py claude-sonnet-4-6 --temperature 0
    python scripts/run_judge.py gpt-5.4 --limit 10
    python scripts/run_judge.py gpt-5.4 --blind
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")

from simulation.judge_runner import JudgeRunner

ROOT = Path(__file__).parent.parent

parser = argparse.ArgumentParser(description="LLM-as-a-judge vignette evaluation")
parser.add_argument("model",         help="Judge model name (e.g. gpt-5.4, claude-sonnet-4-6)")
parser.add_argument("--temperature", type=float, default=0,                                       help="Sampling temperature (default 0)")
parser.add_argument("--input",       default=str(ROOT / "data/eval_vignettes.csv"),               help="Input CSV path")
parser.add_argument("--output_dir",  default=str(ROOT / "data/llm_judge"),                       help="Output directory")
parser.add_argument("--limit",       type=int,   default=None,                                    help="Stop after N vignettes (for testing)")
parser.add_argument("--blind",       action="store_true",                                         help="Hide model/condition in output")
parser.add_argument("--delay",       type=float, default=0.5,                                     help="Seconds between API calls (sequential only)")
parser.add_argument("--workers",     type=int,   default=1,                                        help="Parallel workers (default 1 = sequential)")
args = parser.parse_args()

runner = JudgeRunner(
    model       = args.model,
    temperature = args.temperature,
    input_path  = Path(args.input),
    output_dir  = Path(args.output_dir),
    blind       = args.blind,
    delay       = args.delay,
    limit       = args.limit,
    workers     = args.workers,
)
runner.run()
