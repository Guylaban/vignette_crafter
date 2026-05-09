import json
from pathlib import Path

REPO_ROOT  = Path(__file__).parent.parent.parent
POOL_PATH  = REPO_ROOT / "data" / "rating_pool.json"
DEMO_PATH  = REPO_ROOT / "data" / "demo_pool.json"


def load_vignettes() -> list[dict]:
    path = POOL_PATH if POOL_PATH.exists() else DEMO_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Rating pool not found. Run `python prepare_rating_pool.py` first."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)
