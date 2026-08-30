# Human Edge-Probe Inter-Rater Validity Package

A self-contained package for a human rater to replicate, on a 150-vignette
sample, the edge-probe task our LLM judge performed — extended with a graded
0–1 strength scale. Human ratings validate the LLM judge (inter-rater
agreement, ICC) and test whether the generator realised each edge at its
specified prominence.

## What's in the box

```
human_edge_probe/
├── README.md              # this file
├── INSTRUCTIONS.md        # full task instructions (rater: read first)
├── RUBRIC.md              # anchors for both scales, one example phrasing per
│                          #   edge (all 20), nine worked decisions, boundary rules
├── rating_form.csv        # THE form: one row per vignette, vignette text inside,
│                          #   20 present columns (0/1) + 20 strength columns (0-1)
├── vignettes/             # V001.txt ... V150.txt (same texts as in the CSV,
│                          #   for comfortable reading)
├── submission_key.csv     # SEALED - rater must not open until done
└── coordinator_only/      # NOT for the rater
    ├── original_binary_edge_probe_subset.csv  # the paper's LLM binary judgements
    │                                          #   on these exact 30 vignettes
    ├── llm_graded_ratings.jsonl               # graded LLM re-run (raw, full responses)
    ├── llm_graded_merged.csv                  # graded LLM ratings + specified weights
    ├── analyze_human_vs_llm.py                # one-command analysis (see below)
    └── ANALYSIS_NOTES.md                      # what gets computed and why
```

## Rater quick-start

1. Read `INSTRUCTIONS.md`, then `RUBRIC.md` (~20 min).
2. Open `rating_form.csv` in a spreadsheet. One row per vignette; the vignette
   text is in the `vignette` column (or read `vignettes/Vxx.txt`).
3. For each vignette fill all 40 rating cells: 20 × present (0/1) and
   20 × strength (0.0–1.0).
4. Save as .csv and send back. Estimated 10–15 hours total (multi-day);
   max 15 vignettes per sitting.

## Design (coordinator)

- **Sample:** 150 vignettes = 50 personas × 3 conditions. The 50 personas are
  the 10 evaluation-subsample personas (112, 122, 142, 149, 239, 252, 299,
  311, 384, 403) plus 40 more sampled with a fixed seed from the remaining
  490. Generation models rotated deterministically across cells, order
  shuffled with a fixed seed, fully blind to the rater.
- **Exact replication:** for the 10 evaluation-subsample personas (30 of the
  150 vignettes), the sampled (persona, condition, model) cells exist in the
  paper's 330-vignette evaluation set, so the original LLM binary edge-probe
  judgements for those very texts are included
  (`coordinator_only/original_binary_edge_probe_subset.csv`). The binary human
  task uses the identical components, synonyms, and paragraph-level causal
  standard as the LLM probe's system prompt.
- **Graded extension:** the strength scale is anchored on the Crafter's own
  weight-to-prominence mapping (explicit > 0.5 / implicit 0.1–0.5 / passing
  < 0.1). The LLM judge was re-run on all 150 texts with the same
  two-scale schema (`coordinator_only/llm_graded_*`).

## Analysis (coordinator) — after the form comes back

```bash
cd coordinator_only
python analyze_human_vs_llm.py --form ../rating_form.csv
```

Produces four result CSVs plus a merged long table:

1. `results_binary_agreement.csv` — human vs LLM binary (both the paper's
   original probe judgements and the graded re-run): percent agreement,
   Cohen's κ, Gwet's AC1, per condition and pooled. **This is the direct
   validity check on the paper's edge probe.**
2. `results_graded_agreement.csv` — human vs LLM strength: Pearson, Spearman,
   ICC(3,1), per condition and pooled.
3. `results_spec_recovery.csv` — MCC of each rater's binary ratings against
   the persona's specified gold (edge active), per condition. **Replicates the
   paper's MCC edge-recovery analysis on the human data** — expect positive
   MCC in full, chance in zero-shot, for both raters if the paper's claim holds.
4. `results_weight_correlation.csv` — Spearman between strength and the
   specified continuous edge weight, full condition (the fidelity claim) and
   zero-shot (negative control). Expectation note: the Crafter received the
   *bucketed* prominence instruction, so recoverable resolution is capped at
   ~4 levels; ρ ≈ 0.4–0.7 on full already indicates good fidelity.

## If the rater stops halfway

Partial forms are still useful — the analysis script drops unrated rows and
reports how many were missing.
