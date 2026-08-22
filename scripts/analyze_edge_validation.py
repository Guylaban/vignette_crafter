"""Reproduce the human edge-validation results reported in the paper.

Reads data/edge_validation_150/edge_validation_150.csv and prints the two
tables in the paper's "Human Validation of Directed-Edge Recovery" section:

  Table 1  pairwise agreement between the four raters
           (Gwet's AC1 on presence, ICC(2,1) on graded strength)
  Table 2  recovery of the specified cognitive graph, per rater per condition
           (MCC, AUC of specified weight predicting detection, and
            Spearman of rated strength against specified weight)

Usage:  python scripts/analyze_edge_validation.py
"""
import itertools
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import matthews_corrcoef, roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, os.pardir, "data", "edge_validation_150",
                   "edge_validation_150.csv")

RATERS = {
    "H1": ("human1_present", "human1_strength"),
    "H2": ("human2_present", "human2_strength"),
    "Flash": ("flash_present", "flash_strength"),
    "Pro": ("pro_present", "pro_strength"),
}
CONDITIONS = ["full", "no_formulation", "zero_shot"]


def gwet_ac1(a, b):
    """Gwet's AC1 for two raters on a binary scale."""
    a = np.asarray(a, dtype=int)
    b = np.asarray(b, dtype=int)
    pa = (a == b).mean()
    p1 = ((a == 1).mean() + (b == 1).mean()) / 2.0
    pe = 2 * p1 * (1 - p1)
    return (pa - pe) / (1 - pe)


def icc21(a, b):
    """ICC(2,1): two-way random effects, absolute agreement, single rater."""
    Y = np.column_stack([np.asarray(a, float), np.asarray(b, float)])
    n, k = Y.shape
    gm = Y.mean()
    msr = k * ((Y.mean(axis=1) - gm) ** 2).sum() / (n - 1)
    msc = n * ((Y.mean(axis=0) - gm) ** 2).sum() / (k - 1)
    resid = Y - Y.mean(axis=1, keepdims=True) - Y.mean(axis=0, keepdims=True) + gm
    mse = (resid ** 2).sum() / ((n - 1) * (k - 1))
    return (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)


def main():
    df = pd.read_csv(CSV)
    print("n = {} directed-edge judgements | {} vignettes | {} personas | "
          "{} edges".format(len(df), df.vignette_id.nunique(),
                            df.persona_id.nunique(), df.edge.nunique()))

    print("\nTable 1. Pairwise agreement (pooled over conditions)")
    print("{:<18} {:>14} {:>16}".format("Rater pair", "AC1 (present)",
                                        "ICC (strength)"))
    for r1, r2 in itertools.combinations(RATERS, 2):
        p1, s1 = RATERS[r1]
        p2, s2 = RATERS[r2]
        print("{:<18} {:>14.3f} {:>16.3f}".format(
            "{} vs {}".format(r1, r2),
            gwet_ac1(df[p1], df[p2]),
            icc21(df[s1], df[s2])))

    print("\nTable 2. Recovery of the specified graph, by rater and condition")
    blocks = [
        ("MCC vs specified graph",
         lambda sub, p, s: matthews_corrcoef(sub.spec_active, sub[p])),
        ("AUC (specified weight -> detection)",
         lambda sub, p, s: roc_auc_score(sub[p], sub.spec_weight)),
        ("Spearman (rated strength, specified weight)",
         lambda sub, p, s: spearmanr(sub[s], sub.spec_weight).statistic),
    ]
    for title, fn in blocks:
        print("\n  " + title)
        print("  {:<8}".format("") + "".join(
            "{:>16}".format(c) for c in CONDITIONS))
        for r, (p, s) in RATERS.items():
            cells = []
            for cond in CONDITIONS:
                sub = df[df.condition == cond]
                cells.append("{:>16.3f}".format(fn(sub, p, s)))
            print("  {:<8}".format(r) + "".join(cells))


if __name__ == "__main__":
    main()
