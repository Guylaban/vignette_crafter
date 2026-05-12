"""
run_judge.py — LLM-as-a-judge evaluation of vignettes.

Usage:
    python run_judge.py gpt-5.4
    python run_judge.py claude-sonnet-4-6 --temperature 0
    python run_judge.py gpt-5.4 --limit 10
    python run_judge.py gpt-5.4 --blind
"""

import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")

from simulation.judge_runner import JudgeRunner

parser = argparse.ArgumentParser(description="LLM-as-a-judge vignette evaluation")
parser.add_argument("model",         help="Judge model name (e.g. gpt-5.4, claude-sonnet-4-6)")
parser.add_argument("--temperature", type=float, default=0,                       help="Sampling temperature (default 0)")
parser.add_argument("--input",       default="data/eval_vignettes.csv",           help="Input CSV path")
parser.add_argument("--output_dir",  default="data/llm_judge",                   help="Output directory")
parser.add_argument("--limit",       type=int,   default=None,                    help="Stop after N vignettes (for testing)")
parser.add_argument("--blind",       action="store_true",                         help="Hide model/condition in output")
parser.add_argument("--delay",       type=float, default=0.5,                     help="Seconds between API calls")
args = parser.parse_args()

runner = JudgeRunner(
    model       = args.model,
    temperature = args.temperature,
    input_path  = Path(args.input),
    output_dir  = Path(args.output_dir),
    blind       = args.blind,
    delay       = args.delay,
    limit       = args.limit,
)
runner.run()
