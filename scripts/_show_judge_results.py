import pandas as pd
from pathlib import Path

COND_LABELS = {"full": "Full", "no_formulation": "No Formulation", "zero_shot": "Zero-shot"}
CRITERIA = [
    "clarity","relevance","importance",
    "g1_grounded","g2_narrative","g3_explicit","g4_relevant",
    "dsm_a","dsm_b","dsm_c","dsm_d","dsm_e","dsm_g",
    "ec_threat","ec_appraisals","ec_memory","ec_strategies","ec_triggers",
]

ROOT = Path(__file__).parent.parent

for judge in ["claude-opus-4-5", "deepseek-chat"]:
    frames = []
    for folder in ["data/llm_judge_v7", "data/llm_judge_v9"]:
        p = ROOT / folder / f"llm_judge_{judge}.csv"
        if p.exists():
            frames.append(pd.read_csv(p))

    if not frames:
        print(f"\n{judge}: no data found")
        continue

    df = pd.concat(frames, ignore_index=True)
    df["cond"] = df["condition"].map(COND_LABELS)

    print(f"\n{'='*56}")
    print(f"  {judge}  (n={len(df)} total ratings)")
    print(f"{'='*56}")
    tbl = df.groupby("cond")[CRITERIA].mean().T
    for c in ["Full", "No Formulation", "Zero-shot"]:
        if c not in tbl.columns:
            tbl[c] = float("nan")
    print(tbl[["Full", "No Formulation", "Zero-shot"]].round(2).to_string())
