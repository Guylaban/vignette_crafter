import json, sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

BAD_CHARS = {
    "‑",  # non-breaking hyphen
    "→",  # arrow ->
    "‘", "’",  # ' '
    "“", "”",  # " "
    "–", "—",  # en/em dash
    "…",  # ellipsis
}

bad_found = Counter()
for fp in Path("data/output").rglob("experiment_*.json"):
    if "_summary" in fp.name:
        continue
    try:
        data = json.loads(fp.read_bytes().decode("utf-8"))
        v = data.get("vignette", "")
        for c in v:
            if c in BAD_CHARS:
                bad_found[c] += 1
    except Exception:
        pass

if bad_found:
    print("Still found typographic chars:")
    for c, n in bad_found.most_common():
        print(f"  U+{ord(c):04X} {repr(c)}  n={n}")
else:
    print("All clean - no typographic chars remaining in experiment JSONs.")

# Also check the exported files
for fp in Path("data").glob("eval_vignettes*.csv"):
    text = fp.read_text(encoding="utf-8-sig")
    found = [c for c in BAD_CHARS if c in text]
    if found:
        print(f"{fp.name}: still has {[repr(c) for c in found]}")
    else:
        print(f"{fp.name}: clean")

rp = json.loads(Path("data/rating_pool.json").read_text(encoding="utf-8"))
bad_rp = [c for item in rp for c in item["vignette"] if c in BAD_CHARS]
if bad_rp:
    print(f"rating_pool.json: still has {Counter(bad_rp).most_common()}")
else:
    print("rating_pool.json: clean")
