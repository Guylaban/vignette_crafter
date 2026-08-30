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

## `study_materials/`

Everything the human raters were given, so the annotation task can be inspected
or repeated:

- `RUBRIC.md` — the edge-annotation rubric, including the causal standard applied
- `INSTRUCTIONS.md`, `README.md` — rater-facing instructions
- `rating_form.csv` — the blank form as issued
- `submission_key.csv` — the sample definition, mapping each `vignette_id` to its
  persona, condition, and generation model
- `vignettes/` — the 150 vignette texts as shown to raters (`V001.txt` .. `V150.txt`)
- `coordinator_only/` — material withheld from raters during annotation (LLM
  ratings and analysis notes), kept separate so the blinding is auditable

## `raw_judge_output/`

Per-call output from the two LLM judges, one JSON object per vignette, carrying
the raw response and the judge's rationale alongside the parsed per-edge scores.
The `flash_*` and `pro_*` columns of the CSV derive from these.

## Regenerating the judge columns

```
FORMA_PERSONA_DIR=/path/to/personas python scripts/run_graded_edge_probe_flash.py
FORMA_PERSONA_DIR=/path/to/personas python scripts/run_graded_edge_probe_pro.py
```

Both read `DEEPSEEK_API_KEY` from `.env`. Paths are configurable through
`FORMA_REPO`, `FORMA_SAMPLE_DIR`, `FORMA_OUT_DIR`, and `FORMA_PERSONA_DIR`;
the defaults point at this directory. The human columns cannot be regenerated,
being the raters' own judgements.

## Scope of this release

This directory contains only the data behind the results reported in the paper.
It does not include the model reasoning traces captured during the probe runs, or
an earlier prompt variant of the probe that is not reported.
