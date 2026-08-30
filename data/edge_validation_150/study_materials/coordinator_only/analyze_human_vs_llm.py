"""Human-vs-LLM edge-probe validity analysis.

Replicates the paper's edge-recovery analysis on the human ratings and adds the
graded comparisons. Run AFTER the rater returns the completed rating_form.csv.

Usage:
    python analyze_human_vs_llm.py --form ../rating_form.csv

Inputs (this folder unless stated):
    ../rating_form.csv                        completed human form (wide, 30 rows)
    ../submission_key.csv                     vignette -> persona/condition/model
    original_binary_edge_probe_subset.csv     the paper's LLM binary judgements (same 30 vignettes)
    llm_graded_merged.csv                     graded LLM re-run (present + strength + spec_weight)

Outputs (written next to this script, all NEW files):
    results_binary_agreement.csv    human-vs-LLM binary agreement per condition (pooled + per cond):
                                    percent agreement, Cohen's kappa, Gwet's AC1
    results_graded_agreement.csv    human-vs-LLM strength: Pearson, Spearman, ICC(3,1)
    results_spec_recovery.csv       MCC of each rater's binary vs specified gold (edge active),
                                    per condition  [replicates the paper's MCC analysis]
    results_weight_correlation.csv  Spearman(strength, spec_weight) per rater, full condition
                                    + zero-shot negative control
    merged_long.csv                 one row per (vignette, edge): everything joined
"""
import argparse, csv, math, pathlib
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).parent

NODES = ["Triggers", "Negative Appraisals", "Memory", "Threat", "Maladaptive Strategies"]
def fld(a, b): return f"{a.replace(' ', '_')}__to__{b.replace(' ', '_')}"
EDGES = [(a, b) for a in NODES for b in NODES if a != b]

def gwet_ac1(x, y):
    """Gwet's AC1 for two raters, binary."""
    x, y = np.asarray(x), np.asarray(y)
    n = len(x)
    po = float(np.mean(x == y))
    pi = (np.mean(x) + np.mean(y)) / 2          # overall prevalence of category 1
    pe = 2 * pi * (1 - pi)                       # AC1 chance agreement
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")

def cohen_kappa(x, y):
    x, y = np.asarray(x), np.asarray(y)
    po = float(np.mean(x == y))
    p1x, p1y = np.mean(x), np.mean(y)
    pe = p1x * p1y + (1 - p1x) * (1 - p1y)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")

def mcc(pred, gold):
    pred, gold = np.asarray(pred).astype(int), np.asarray(gold).astype(int)
    tp = int(np.sum((pred == 1) & (gold == 1))); tn = int(np.sum((pred == 0) & (gold == 0)))
    fp = int(np.sum((pred == 1) & (gold == 0))); fn = int(np.sum((pred == 0) & (gold == 1)))
    den = math.sqrt((tp+fp) * (tp+fn) * (tn+fp) * (tn+fn))
    return (tp * tn - fp * fn) / den if den else float("nan")

def icc_3_1(x, y):
    """ICC(3,1), two fixed raters (two-way mixed, consistency)."""
    data = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
    n, k = data.shape
    ms_rows = np.var(data.mean(axis=1), ddof=1) * k
    ms_err  = (np.sum((data - data.mean(axis=1, keepdims=True)
                       - data.mean(axis=0, keepdims=True) + data.mean()) ** 2)
               / ((n - 1) * (k - 1)))
    return (ms_rows - ms_err) / (ms_rows + (k - 1) * ms_err)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", default=str(HERE.parent / "rating_form.csv"))
    args = ap.parse_args()

    human_w = pd.read_csv(args.form)
    key     = pd.read_csv(HERE.parent / "submission_key.csv", dtype=str)
    orig    = pd.read_csv(HERE / "original_binary_edge_probe_subset.csv", dtype=str)
    graded  = pd.read_csv(HERE / "llm_graded_merged.csv")

    # --- long-format human ratings ---
    rows = []
    for _, r in human_w.iterrows():
        for a, b in EDGES:
            rows.append({
                "vignette_id": r["vignette_id"],
                "edge": f"{a} -> {b}",
                "human_present": r[f"present__{fld(a,b)}"],
                "human_strength": r[f"strength__{fld(a,b)}"],
            })
    human = pd.DataFrame(rows)
    if human["human_present"].isna().any():
        n = int(human["human_present"].isna().sum())
        print(f"WARNING: {n} empty present cells - those rows are dropped")
        human = human.dropna(subset=["human_present"])
    human["human_present"] = human["human_present"].astype(int)
    human["human_strength"] = human["human_strength"].astype(float)

    # --- long-format original LLM binary ---
    orows = []
    for _, r in orig.iterrows():
        for a, b in EDGES:
            orows.append({"vignette_id": r["vignette_id"], "edge": f"{a} -> {b}",
                          "llm_binary_orig": int(r[f"llm_binary__{fld(a,b)}"])})
    llm_orig = pd.DataFrame(orows)

    # --- join everything (original probe exists only for the 10 eval-subsample
    #     personas -> left join; its rows are NaN for the other 40 personas) ---
    m = (human
         .merge(llm_orig, on=["vignette_id", "edge"], how="left")
         .merge(graded[["vignette_id", "edge", "llm_present", "llm_strength",
                        "spec_weight", "spec_edge_active"]],
                on=["vignette_id", "edge"])
         .merge(key, on="vignette_id"))
    m.to_csv(HERE / "merged_long.csv", index=False)
    n_orig = int(m["llm_binary_orig"].notna().sum())
    print(f"merged_long.csv: {len(m)} rows ({n_orig} with original-probe judgements)")

    conds = ["full", "no_formulation", "zero_shot", "POOLED"]
    def sub(c): return m if c == "POOLED" else m[m["condition"] == c]

    # --- 1. binary agreement: human vs original LLM probe (overlap subset),
    #        and vs graded re-run (all rows) ---
    out = []
    for c in conds:
        s = sub(c)
        s_orig = s.dropna(subset=["llm_binary_orig"])
        if len(s_orig):
            out.append({"condition": c, "llm_source": "orig_binary_probe", "n": len(s_orig),
                        "pct_agree": round(float(np.mean(s_orig["human_present"] == s_orig["llm_binary_orig"].astype(int))), 4),
                        "cohen_kappa": round(cohen_kappa(s_orig["human_present"], s_orig["llm_binary_orig"].astype(int)), 4),
                        "gwet_ac1": round(gwet_ac1(s_orig["human_present"], s_orig["llm_binary_orig"].astype(int)), 4)})
        out.append({"condition": c, "llm_source": "graded_rerun", "n": len(s),
                    "pct_agree": round(float(np.mean(s["human_present"] == s["llm_present"])), 4),
                    "cohen_kappa": round(cohen_kappa(s["human_present"], s["llm_present"]), 4),
                    "gwet_ac1": round(gwet_ac1(s["human_present"], s["llm_present"]), 4)})
    pd.DataFrame(out).to_csv(HERE / "results_binary_agreement.csv", index=False)

    # --- 2. graded agreement: human strength vs LLM strength ---
    out = []
    for c in conds:
        s = sub(c)
        out.append({"condition": c, "n": len(s),
                    "pearson": round(float(np.corrcoef(s["human_strength"], s["llm_strength"])[0, 1]), 4),
                    "spearman": round(float(s["human_strength"].corr(s["llm_strength"], method="spearman")), 4),
                    "icc_3_1": round(icc_3_1(s["human_strength"], s["llm_strength"]), 4)})
    pd.DataFrame(out).to_csv(HERE / "results_graded_agreement.csv", index=False)

    # --- 3. spec recovery: binary vs specified gold (replicates the paper's MCC) ---
    out = []
    for c in ["full", "no_formulation", "zero_shot"]:
        s = sub(c)
        gold = s["spec_edge_active"].astype(int)
        out.append({"condition": c, "n": len(s), "gold_prevalence": round(float(gold.mean()), 3),
                    "human_mcc": round(mcc(s["human_present"], gold), 4),
                    "llm_orig_mcc": round(mcc(s["llm_binary_orig"], gold), 4),
                    "llm_rerun_mcc": round(mcc(s["llm_present"], gold), 4)})
    pd.DataFrame(out).to_csv(HERE / "results_spec_recovery.csv", index=False)

    # --- 4. strength vs specified weight ---
    out = []
    for c in ["full", "zero_shot"]:   # full = the claim; zero_shot = negative control
        s = sub(c)
        out.append({"condition": c, "n": len(s),
                    "spearman_human_weight": round(float(s["human_strength"].corr(s["spec_weight"], method="spearman")), 4),
                    "spearman_llm_weight": round(float(s["llm_strength"].corr(s["spec_weight"], method="spearman")), 4)})
    pd.DataFrame(out).to_csv(HERE / "results_weight_correlation.csv", index=False)

    print("Wrote results_binary_agreement.csv, results_graded_agreement.csv,")
    print("      results_spec_recovery.csv, results_weight_correlation.csv")

if __name__ == "__main__":
    main()
