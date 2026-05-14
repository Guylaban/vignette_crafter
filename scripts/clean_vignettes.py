"""
clean_vignettes.py — strip markdown from vignette field in all experiment JSON files.

Run once to clean existing data in data/output/:
    python scripts/clean_vignettes.py

Skips files whose vignette is already clean. Reports counts at the end.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.text import strip_markdown

DATA_DIR = Path(__file__).parent.parent / "data/output"


def main():
    files = list(DATA_DIR.rglob("experiment_*.json"))
    print(f"Found {len(files)} experiment files")

    cleaned = 0
    skipped = 0
    errors  = 0

    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)

            original = data.get("vignette", "")
            if not original:
                skipped += 1
                continue

            cleaned_text = strip_markdown(original)
            if cleaned_text == original:
                skipped += 1
                continue

            data["vignette"] = cleaned_text
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            cleaned += 1

        except Exception as e:
            print(f"  [error] {fp}: {e}")
            errors += 1

    print(f"\nDone:  {cleaned} cleaned  |  {skipped} already clean  |  {errors} errors")


if __name__ == "__main__":
    main()
