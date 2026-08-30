# Analysis Notes (coordinator only)

Once the completed `rating_form.csv` comes back from the rater(s), the planned
analyses are:

## 1. Judge validity — human vs LLM

Merge on (vignette_id, edge). LLM ratings are in `llm_graded_merged.csv`
(columns `llm_present`, `llm_strength`).

- **Binary agreement** (present columns): Gwet's AC1 per condition and pooled;
  also raw percent agreement and Cohen's kappa for comparability with the
  paper's Appendix O machinery. This is the direct validity check on the
  paper's edge-probe: the LLM binary judgements on these 30 vignettes used the
  same standard as the 330-vignette run.
- **Graded agreement** (strength columns): ICC(3,1) treating human and LLM as
  two fixed raters over the 600 (vignette, edge) units; report per condition.
  Optionally quadratic-weighted AC2 after binning strength into the four
  anchor levels (0 / passing / implicit / explicit).

## 2. Generation fidelity — did the text realise the specified weight?

Only meaningful for **full-condition** vignettes (10 vignettes, 200 edge
judgements): the specified graph was not communicated to the generator in the
other two conditions.

- Spearman correlation between rater strength and `spec_weight` on
  full-condition rows. Compute separately for human and LLM strength; compare.
- Expectation management: the Crafter received the *bucketed* prominence
  instruction (explicit > 0.5 / implicit 0.1-0.5 / passing < 0.1), not the raw
  weight, so recoverable resolution is capped at ~4 levels. A Spearman in the
  0.4-0.7 range on active edges would already indicate good fidelity.
- Negative control: the same correlation on zero-shot rows should be ~0.

## 3. Bridge to the paper's numbers

- Threshold the human strength at >= 0.3 to reproduce a binary rating and
  recompute the paper's MCC-vs-specified-gold on the human data; compare with
  the LLM judge's MCC on the same 30 vignettes.
- Where human present = 0 but strength in [0.05, 0.2] (the "hinted" zone),
  inspect LLM behaviour: does the LLM binary judge systematically flip these
  to 1? That quantifies the strictness difference between judges.

## File provenance

- `llm_graded_ratings.jsonl` — raw per-vignette LLM responses (full response
  text preserved), judge = deepseek-v4-flash, temperature 0, same 30 blind
  vignette texts the human rates.
- `llm_graded_merged.csv` — long format, one row per (vignette, edge):
  llm_present, llm_strength, spec_weight (persona's specified directed weight),
  spec_edge_active (both endpoints active AND weight > 0).
- `submission_key.csv` (package root) — vignette_id -> persona/condition/model.
