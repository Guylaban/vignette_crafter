"""
collect_judge_input.py — collect vignettes from output/full/ for judge evaluation.

Walks data/output/full/{model}/experiment_{persona_id}.json for each specified
model and writes a combined JSONL file ready for run_judge.py.

Usage:
    python scripts/collect_judge_input.py
    python scripts/collect_judge_input.py --models claude-haiku-4-5 claude-sonnet-4-6
    python scripts/collect_judge_input.py --condition zero_shot --all
    python scripts/collect_judge_input.py --output data/judge_input/full/batch2.jsonl

Output layout:
    data/judge_input/<condition>/<model>.jsonl   (single model)
    data/judge_input/<condition>/_batch.jsonl    (multiple models, default name)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.text import strip_markdown

ROOT       = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "data/output"

BATCH1_MODELS = [
    "claude-haiku-4-5",
    "claude-sonnet-4-6",
    "deepseek-chat",
    "deepseek-reasoner",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

ALL_MODELS = [
    "claude-haiku-4-5",
    "claude-sonnet-4-6",
    "deepseek-chat",
    "deepseek-reasoner",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gpt-4o-mini",
    "gpt-5.4",
    "gpt-5.4-mini",
    "qwen2.5-32b",
    "qwen3.6-35b",
]


def collect(models: list[str], output_path: Path, condition: str):
    rows = []
    missing = []
    condition_dir = OUTPUT_DIR / condition

    for model in models:
        model_dir = condition_dir / model
        if not model_dir.exists():
            print(f"  [warn] {model}: directory not found, skipping")
            continue

        files = sorted(model_dir.glob("experiment_*.json"),
                       key=lambda p: int(p.stem.split("_")[1]))
        if not files:
            print(f"  [warn] {model}: no experiment files found")
            continue

        model_rows = 0
        for fp in files:
            persona_id = fp.stem.split("_")[1]
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                vignette = strip_markdown(data.get("vignette", ""))
                if not vignette:
                    missing.append((model, persona_id, "empty vignette"))
                    continue
                rows.append({
                    "vignette_id": f"{condition}_{model}_{persona_id}",
                    "persona_id":  persona_id,
                    "model":       model,
                    "condition":   condition,
                    "vignette":    vignette,
                })
                model_rows += 1
            except Exception as e:
                missing.append((model, persona_id, str(e)))

        print(f"  {model}: {model_rows} vignettes")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nTotal: {len(rows)} vignettes -> {output_path}")
    if missing:
        print(f"Missing/failed ({len(missing)}):")
        for model, pid, reason in missing:
            print(f"  {model}  persona {pid}: {reason}")


def main():
    parser = argparse.ArgumentParser(description="Collect full-condition vignettes for judge input")
    parser.add_argument("--models", nargs="+", default=BATCH1_MODELS,
                        help="Model names to include (default: batch1 = 6 claude/deepseek/gemini models)")
    parser.add_argument("--all",    action="store_true",
                        help="Include all 11 models (overrides --models)")
    parser.add_argument("--output", default=None,
                        help="Output JSONL path (default: auto-named by model)")
    parser.add_argument("--condition", default="full",
                        help="Source condition under data/output/ (default: full)")
    args = parser.parse_args()

    models = ALL_MODELS if args.all else args.models
    if args.output:
        output = Path(args.output)
    elif len(models) == 1:
        output = ROOT / f"data/judge_input/{args.condition}/{models[0]}.jsonl"
    else:
        output = ROOT / f"data/judge_input/{args.condition}/_batch.jsonl"

    print(f"Collecting {len(models)} models [{args.condition}] -> {output}")
    print(f"Models: {models}\n")
    collect(models, output, args.condition)


if __name__ == "__main__":
    main()
