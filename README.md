# Generating Clinical Vignettes that Preserve Cognitive Formulations

**Findings of the Association for Computational Linguistics: EMNLP 2026**

Amit Oren<sup>1</sup> · Nimrod Hertz-Palmor<sup>2</sup> · Dean Ariel<sup>3,4</sup> · Guy Laban<sup>1,5,6</sup>

<sup>1</sup> Department of Industrial Engineering and Management, Ben-Gurion University of the Negev, Beer Sheva, Israel
<sup>2</sup> MRC Cognition and Brain Sciences Unit, University of Cambridge, United Kingdom
<sup>3</sup> Clalit Health Services, Israel
<sup>4</sup> School of Public Health, Tel Aviv University, Israel
<sup>5</sup> School of Brain Sciences and Cognition, Ben-Gurion University of the Negev, Beer Sheva, Israel
<sup>6</sup> Azrieli National Center for Autism and Neurodevelopment Research, Beer Sheva, Israel

Corresponding author: [laban@bgu.ac.il](mailto:laban@bgu.ac.il)

---

## Overview

Language models write fluent clinical vignettes, but fluency says nothing about whether a vignette is faithful to a *specifiable* clinical picture. **FORMA** compiles a cognitive model of a disorder into a directed weighted graph, samples a person-specific configuration of that graph, and validates whether the generated text preserves the specified components and causal links. The graph is an auditable specification: the output can be checked against it, edge by edge.

We instantiate FORMA on PTSD using the Ehlers and Clark cognitive model, generating **16,500 vignettes** across **500 personas**, **11 generation models**, and **three ablation conditions** (full / no-formulation / zero-shot).

## Key results

| | Full | Zero-shot |
| --- | --- | --- |
| Graph recovery (MCC) | **+0.41** | +0.01 |
| Graph recovery (AUC) | **0.70** | 0.50 |
| Read as human-written by clinicians | **85%** | 22% |

Evaluation triangulates an external edge-recovery probe, two clinical experts, a scaled LLM judge, and a user study with **100 licensed practitioners**. FORMA also reduces demographic disparity in perceived quality by 1.5–7×.

A separate human validation had **two clinical raters annotate all 20 directed causal edges on 150 vignettes**, blind to condition and to the specified graph (3,000 judgements per rater). The automated probe agrees with each human as strongly as the two humans agree with each other (Gwet's AC1 0.67 vs 0.63), and the humans independently reproduce the recovery gradient.

## What is in this repository

The generation pipeline, the evaluation protocol, and the released data.

| Path | Contents |
| --- | --- |
| `agents/` | LLM roles: persona crafter/validator, vignette crafter/validator, judge, edge probe |
| `simulation/` | Runner, pipelines, per-model LLM clients |
| `configs/` | Prompts, demographic and self-report sampling pools, cognitive edges |
| `scripts/` | CLI entry points for generation, judging, and the edge probes |
| `data/personas/` | The 500 persona specifications: demographics, self-report items, and the specified weighted graph |
| `data/edge_validation_150/` | The human edge-validation study: judgements, study materials, raw judge output |
| `data/output/` | Generated vignettes, by condition and model |
| `data/llm_judge/` | Judge scores per vignette |
| `data/analysis/` | Analysis outputs and figures |
| `streamlit_app/`, `rating_app/` | Dashboards for inspecting runs and collecting human ratings |

An interactive browser for the 500 full-condition vignettes, each shown beside its persona graph and self-report items, is at <https://clinical-vignettes.streamlit.app/>.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in API keys
```

Run one model end-to-end (persona crafting, vignette generation, validation):

```bash
python scripts/run_model.py gpt-5.4 --mode full
python scripts/run_model.py claude-sonnet-4-6 --mode no_formulation
python scripts/run_model.py gpt-5.4-mini --mode zero_shot
```

Modes: `full` (demographics + self-report + cognitive formulation), `no_formulation` (demographics + self-report only), `zero_shot` (no persona context). Outputs land under `data/output/<mode>/<model>/experiment_<persona_id>.json`.

Judge generated vignettes:

```bash
python scripts/collect_judge_input.py --all --condition full
python scripts/run_judge.py claude-sonnet-4-6 --input data/judge_input/full/_batch.jsonl --output_dir data/llm_judge/full/claude-sonnet-4-6
```

Reproduce the human edge-validation tables:

```bash
python scripts/analyze_edge_validation.py
```

Launch the dashboard:

```bash
streamlit run streamlit_app/Home.py
```

## Reproducing the structural-fidelity results

The edge probe reads a vignette's prose alone and judges each of the 20 directed Ehlers and Clark pairs. It never receives the graph, the self-report items, or the condition, which is what makes recovery evidence rather than read-back.

```bash
python scripts/run_edge_probe.py                    # binary probe
python scripts/run_graded_edge_probe_flash.py       # graded 0-1 probe
python scripts/run_graded_edge_probe_pro.py
```

Gold labels come from `data/personas/persona_<id>.json`, whose `agg_edges` field holds the specified weight for each directed pair.

## Repository layout

<details>
<summary>Full directory reference</summary>

```
vignette_crafter/
├── main.py                  # Single-config entry point (used by run_model.py)
├── agents/                  # LLM agents: persona crafter/validator, vignette crafter/validator, judge, edge probe
├── simulation/              # Runner, pipelines, LLM wrappers, judge runner
├── configs/                 # Single YAML + Python configs (prompts, demographics, self-report items)
├── utils/                   # Shared utilities (text processing)
├── scripts/                 # CLI scripts (see below)
├── streamlit_app/           # Multi-page dashboard for inspecting runs
├── rating_app/              # Streamlit app for human rating of vignettes
├── analysis/                # Jupyter notebooks (embedding analysis, persona bias)
├── docs/                    # Architecture diagrams (drawio)
└── data/                    # All inputs, outputs, intermediates
```

### `simulation/`
- `runner.py` — orchestrates a full simulation
- `pipelines.py` — available pipelines (`vignette_from_persona`, `zero_shot_from_persona`, etc.)
- `steps.py` — individual pipeline steps
- `judge_runner.py` — separate runner for LLM-as-judge evaluation
- `factory.py` — instantiates the right LLM client per model name
- `deepseek_llm.py`, `open_source_llm.py` — model-specific clients

### `configs/`
- `simulation_config.yaml` — the only YAML. Simulation params and default models; `scripts/run_model.py` overrides `pipeline`, `vignette_mode`, and `models` from `--mode` and the CLI model argument
- `prompts.py` — LLM prompt templates
- `demographics.py`, `self_report.py`, `formulation_config.py` — sampling pools and cognitive edges
- `config.py`, `logging_config.py` — sim config and logging

### `scripts/`
- `run_model.py` — main entry (wraps `main.py` per `--mode`)
- `run_judge.py`, `collect_judge_input.py` — LLM-as-judge evaluation and its inputs
- `run_edge_probe.py` — binary edge-recovery probe
- `run_graded_edge_probe_flash.py`, `run_graded_edge_probe_pro.py` — graded 0-1 probes on the 150-vignette sample
- `analyze_edge_validation.py` — reproduces the human-validation tables
- `analyze_runs.py` — post-hoc aggregation
- `export_eval_vignettes.py`, `export_rating_pool_330.py`, `select_eval_personas.py` — evaluation artifact builders
- `clean_vignettes.py`, `check_clean.py`, `find_empty.py` — data hygiene utilities
- `migrate_output_structure.py`, `reconstruct_tokens_qwen.py` — one-off historical migrations, kept for reference

### `streamlit_app/pages/`
- `2_Experiments.py` — browse experiment runs
- `3_Persona_Crafter.py` — design personas
- `4_Vignette.py` — generate single vignettes
- `5_Vignette_Analysis.py` — text-level vignette analysis
- `6_Demographics.py` — demographic distributions
- `7_Embedding_Clusters.py` — live t-SNE per condition, with trauma-type highlighting
- `8_Vignette_TSNE_Clusters.py` — cached t-SNE + HDBSCAN/KMeans cluster analysis

### `data/`

```
data/
├── personas/                # 500 persona specifications (persona_<id>.json)
├── edge_validation_150/     # Human edge-validation study (see its own README)
├── output/                  # Generated experiment runs
│   ├── full/<model>/experiment_<pid>.json
│   ├── no_formulation/<model>/experiment_<pid>.json
│   ├── zero_shot/<model>/experiment_<pid>.json
│   ├── context/             # Per-call agent context dumps
│   └── _archive/            # Historical runs
├── judge_input/             # JSONLs fed to run_judge.py
├── llm_judge/               # Judge outputs (per-vignette scores)
├── llm_judge_legacy/        # Historic single-CSV judge runs from older judge models
├── edge_probe/              # Binary edge-probe output
├── analysis/                # Generated figures (PDF) and analysis CSVs
├── input/                   # Persona sampling module
├── eval_personas.json       # Eval persona set
├── eval_vignettes.csv       # Full eval vignette set
├── eval_vignettes_330.csv   # 330-vignette rating pool source
└── rating_pool.json         # Rating pool consumed by rating_app/
```

### `analysis/`
- `vignette_embedding_analysis.ipynb` — main analysis (t-SNE/UMAP, silhouette, headline figures)
- `persona_bias_analysis.ipynb` — demographic bias inspection

Generated figures (PDF) are written to `data/analysis/`.

### Common workflows

**Add a model:** register it in `simulation/factory.py`, then `scripts/run_model.py <model> --mode <mode>`.

**Add a judge:** `scripts/run_judge.py <judge_model> --input <jsonl> --output_dir data/llm_judge/<cond>/<crafter>`.

**Regenerate judge inputs after a run:**
```bash
python scripts/collect_judge_input.py --all --condition full
python scripts/collect_judge_input.py --all --condition no_formulation
python scripts/collect_judge_input.py --all --condition zero_shot
```

</details>

## Ethics and intended use

**The dataset contains no real patient material.** Every persona, demographic profile, self-report item, and vignette is model-generated from the documented sampling distributions. The cognitive-model parameters derive from published clinical theory and from prior work that re-derived the Ehlers and Clark graph from ecological momentary assessment data; no individual-level patient data was ingested.

Full-condition vignettes pass as human-written to clinicians 85% of the time, which is an ethical concern as much as a result. Anything redistributing this material should label every vignette as synthetic and as not representing a real individual. We see appropriate uses as standardised training and research stimuli, and we caution against using the set to train or evaluate clinical models without accounting for the theoretical and stylistic commitments it inherits.

Fidelity to one cognitive model is not the same as clinical validity. The framework does not address complex PTSD, comorbidity, or culturally specific presentations.

## Citation

```bibtex
@inproceedings{oren2026forma,
  title     = {Generating Clinical Vignettes that Preserve Cognitive Formulations},
  author    = {Oren, Amit and Hertz-Palmor, Nimrod and Ariel, Dean and Laban, Guy},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2026},
  year      = {2026}
}
```
