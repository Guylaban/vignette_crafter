# Human validation of directed-edge recovery (150-vignette study)

Per-judgement annotations behind the paper's **Human Validation of Directed-Edge
Recovery** section and its appendix.

Two clinical raters independently annotated all 20 directed Ehlers & Clark edges
on 150 vignettes (50 personas x 3 conditions, balanced across the ten retained
generation models), blind to condition and to the persona's specified cognitive
graph. That is 3,000 directed-edge judgements per rater. The same 150 vignettes
were then scored on the identical schema by two of the LLM judges used elsewhere
in the paper (`deepseek-v4-flash`, `deepseek-v4-pro`), under the same blinding,
giving a four-rater panel of two humans and two models.

## `edge_validation_150.csv`

One row per (vignette, directed edge); 3,000 rows.

| Column | Description |
| --- | --- |
| `vignette_id` | Vignette identifier (`V001`..`V150`) |
| `persona_id` | Persona identifier; every persona appears under all three conditions |
| `condition` | `full`, `no_formulation`, or `zero_shot` |
| `generation_model` | Model that generated the vignette (10 models, 5 vignettes per model per condition) |
| `edge` | Directed Ehlers & Clark pair, `A -> B` (20 per vignette) |
| `spec_weight` | Weight of this edge in the persona's specified graph (0 if not specified) |
| `spec_active` | Gold label: 1 if `spec_weight > 0`, else 0 |
| `human1_present`, `human1_strength` | Clinical rater 1 (H1 in the paper): binary presence, graded 0-1 prominence |
| `human2_present`, `human2_strength` | Clinical rater 2 (H2 in the paper): binary presence, graded 0-1 prominence |
| `flash_present`, `flash_strength` | `deepseek-v4-flash`, same schema |
| `pro_present`, `pro_strength` | `deepseek-v4-pro`, same schema |

Raters saw the vignette text only. `spec_weight` and `spec_active` are the
generation-side ground truth and were not shown to any rater.

## Reproducing the reported numbers

```
python scripts/analyze_edge_validation.py
```

This prints both tables in the paper: pairwise agreement between the four raters
(Gwet's AC1 on presence, ICC(2,1) on graded strength) and recovery of the
specified graph per rater per condition (MCC, AUC of the specified weight
predicting detection, and Spearman of rated strength against specified weight).

## Scope of this release

This directory contains only the data behind the results reported in the paper.
It does not include the model reasoning traces captured during the probe runs, or
an earlier prompt variant of the probe that is not reported.
