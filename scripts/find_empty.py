import json, re
from pathlib import Path
from collections import defaultdict

OUTPUT_DIR = Path("data/output")
EVAL_MODELS = [
    "claude-haiku-4-5", "claude-sonnet-4-6",
    "deepseek-chat", "deepseek-reasoner",
    "gemini-2.5-flash", "gemini-2.5-pro",
    "gpt-4o-mini", "gpt-5.4", "gpt-5.4-mini",
    "qwen2.5-32b", "qwen3.6-35b",
]
CONDITIONS = ["full", "no_formulation", "zero_shot"]

empty_by = defaultdict(list)
for cond in CONDITIONS:
    for model in EVAL_MODELS:
        d = OUTPUT_DIR / cond / model
        for fp in sorted(d.glob("experiment_*.json")):
            if "_summary" in fp.name:
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                if not data.get("vignette", "").strip():
                    m = re.search(r"experiment_(\w+)\.json", fp.name)
                    if m:
                        empty_by[(model, cond)].append(m.group(1))
            except Exception:
                pass

for (model, cond), ids in sorted(empty_by.items()):
    print(f"{model}/{cond}: {','.join(ids)}")
