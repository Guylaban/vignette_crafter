import pandas as pd

COND_LABELS = {"full": "Full", "no_formulation": "No Formulation", "zero_shot": "Zero-shot"}
CRITERIA = [
    "clarity","relevance","importance",
    "g1_grounded","g2_narrative","g3_explicit","g4_relevant",
    "dsm_a","dsm_b","dsm_c","dsm_d","dsm_e","dsm_g",
    "ec_threat","ec_appraisals","ec_memory","ec_strategies","ec_triggers",
]

for judge in ["claude-opus-4-5", "deepseek-chat"]:
    print(f"\n{'='*52}")
    print(f"  {judge}")
    print(f"{'='*52}")
    rows = {}
    for version, folder in [("V1", "data/llm_judge_v7"), ("V2", "data/llm_judge_v8")]:
        path = f"{folder}/llm_judge_{judge}.csv"
        try:
            df = pd.read_csv(path)
            df["cond"] = df["condition"].map(COND_LABELS)
            tbl = df.groupby("cond")[CRITERIA].mean()
            for cond in ["Full", "No Formulation", "Zero-shot"]:
                if cond in tbl.index:
                    for c in CRITERIA:
                        rows[(version, cond, c)] = round(tbl.loc[cond, c], 2)
        except FileNotFoundError:
            print(f"  {version} not found at {path}")

    for cond in ["Full", "No Formulation", "Zero-shot"]:
        print(f"\n  {cond}")
        print(f"  {'Criterion':<20} {'V1':>6} {'V2':>6} {'delta':>8}")
        print(f"  {'-'*44}")
        for c in CRITERIA:
            v1 = rows.get(("V1", cond, c))
            v2 = rows.get(("V2", cond, c))
            if v1 is not None and v2 is not None:
                d = round(v2 - v1, 2)
                arrow = " up" if d > 0 else (" dn" if d < 0 else "  =")
                print(f"  {c:<20} {v1:>6} {v2:>6} {str(d)+arrow:>8}")
            else:
                print(f"  {c:<20} {'--':>6} {'--':>6}")
