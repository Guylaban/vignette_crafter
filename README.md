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

LLM-based pipeline for generating PTSD vignettes from synthetic personas, and evaluating them with LLM judges.

**FORMA** compiles a cognitive model of a disorder into a directed weighted graph, samples a person-specific configuration of that graph, and validates whether the generated vignette preserves the specified components and causal links. The graph is an auditable specification: the output can be checked against it, edge by edge. We instantiate it on PTSD using the Ehlers and Clark cognitive model, generating **16,500 vignettes** across **500 personas**, **11 generation models**, and **three ablation conditions**.

## Key results

| | Full | Zero-shot |
| --- | --- | --- |
| Graph recovery (MCC) | **+0.41** | +0.01 |
| Graph recovery (AUC) | **0.70** | 0.50 |
| Read as human-written by clinicians | **85%** | 22% |

Evaluation triangulates an external edge-recovery probe, two clinical experts, a scaled LLM judge, and a user study with **100 licensed practitioners**. FORMA also reduces demographic disparity in perceived quality by 1.5–7×.

A separate human validation had **two clinical raters annotate all 20 directed causal edges on 150 vignettes**, blind to condition and to the specified graph (3,000 judgements per rater). The automated probe agrees with each human as strongly as the two humans agree with each other (Gwet's AC1 0.67 vs 0.63), and the humans independently reproduce the recovery gradient.

An interactive browser for the 500 full-condition vignettes, each shown beside its persona graph and self-report items, is at <https://clinical-vignettes.streamlit.app/>.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in API keys
```

## Quick start

Run one model end-to-end (persona crafting + vignette generation + validation):

```bash
python scripts/run_model.py gpt-5.4 --mode full
python scripts/run_model.py claude-sonnet-4-6 --mode no_formulation
python scripts/run_model.py gpt-5.4-mini --mode zero_shot
```

Modes:
- `full` — demographics + self-report + cognitive formulation
- `no_formulation` — demographics + self-report only
- `zero_shot` — no persona context

Outputs land under `data/output/<mode>/<model>/experiment_<persona_id>.json`.

Run a judge over generated vignettes:

```bash
python scripts/collect_judge_input.py --all --condition full
python scripts/run_judge.py claude-sonnet-4-6 --input data/judge_input/full/_batch.jsonl --output_dir data/llm_judge/full/claude-sonnet-4-6
```

Launch the analysis dashboard:

```bash
streamlit run streamlit_app/Home.py
```

## Repository layout

```
vignette_crafter/
├── main.py                  # Single-config entry point (used by run_model.py)
├── agents/                  # LLM agents: persona crafter/validator, vignette crafter/validator, judge
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

### `agents/`
One file per LLM role. All inherit from `base_agent.py`.

### `simulation/`
- `runner.py` — orchestrates a full simulation
- `pipelines.py` — defines the available pipelines (`vignette_from_persona`, `zero_shot_from_persona`, etc.)
- `steps.py` — individual pipeline steps
- `judge_runner.py` — separate runner for LLM-as-judge evaluation
- `factory.py` — instantiates the right LLM client per model name
- `deepseek_llm.py`, `open_source_llm.py` — model-specific clients

### `configs/`
- `simulation_config.yaml` — **the only YAML**. Holds simulation params + default models. `scripts/run_model.py` overrides `pipeline`, `vignette_mode`, and `models` based on `--mode` and the CLI model arg.
- `prompts.py` — LLM prompt templates
- `demographics.py`, `self_report.py`, `formulation_config.py` — sampling pools and cognitive edges
- `config.py` — dataclass-style sim config
- `logging_config.py` — logging setup

### `scripts/`
- `run_model.py` — main entry (wraps `main.py` per `--mode`)
- `run_judge.py` — LLM-as-judge evaluation
- `collect_judge_input.py` — builds judge input JSONLs from `data/output/`
- `analyze_runs.py` — post-hoc aggregation
- `export_eval_vignettes.py`, `export_rating_pool_330.py`, `select_eval_personas.py` — evaluation artifact builders
- `clean_vignettes.py`, `check_clean.py`, `find_empty.py` — data hygiene utilities
- `migrate_output_structure.py`, `reconstruct_tokens_qwen.py` — one-off historical migrations (kept for reference)
- `_add_headline_figure.py` — notebook-cell injection helper (stale, see leading underscore)

### `streamlit_app/pages/`
- `2_Experiments.py` — browse experiment runs
- `3_Persona_Crafter.py` — design personas
- `4_Vignette.py` — generate single vignettes
- `5_Vignette_Analysis.py` — text-level vignette analysis
- `6_Demographics.py` — demographic distributions
- `7_Embedding_Clusters.py` — live t-SNE of vignettes per condition, with trauma-type highlighting
- `8_Vignette_TSNE_Clusters.py` — cached t-SNE + HDBSCAN/KMeans cluster analysis

### `data/`

```
data/
├── output/                  # Generated experiment runs
│   ├── full/<model>/experiment_<pid>.json
│   ├── no_formulation/<model>/experiment_<pid>.json
│   ├── zero_shot/<model>/experiment_<pid>.json
│   ├── context/             # Per-call agent context dumps (debugging)
│   └── _archive/            # Historical runs
│
├── judge_input/             # JSONLs fed to run_judge.py
│   ├── full/<model>.jsonl
│   ├── no_formulation/<model>.jsonl
│   └── zero_shot/<model>.jsonl
│
├── llm_judge/               # Judge outputs (CSVs of per-vignette scores)
│   ├── full/<crafter_model>/llm_judge_<judge_model>.csv
│   ├── no_formulation/<crafter_model>/llm_judge_<judge_model>.csv
│   ├── zero_shot/<crafter_model>/llm_judge_<judge_model>.csv
│   └── opus_deepseek_pro/   # Opus + DeepSeek-V4-Pro on the 330-vignette eval set
│
├── llm_judge_legacy/        # Historic single-CSV judge runs from older judge models
├── analysis/                # Generated figures (PDF) + analysis CSVs
├── input/                   # Persona sampling module (input.py)
├── eval_personas.json       # Eval persona set
├── eval_vignettes.csv       # Full eval vignette set
├── eval_vignettes_330.csv   # 330-vignette rating pool source
└── rating_pool.json         # Rating pool consumed by rating_app/
```

### `analysis/`
Two Jupyter notebooks:
- `vignette_embedding_analysis.ipynb` — main analysis (t-SNE/UMAP, silhouette, headline figures)
- `persona_bias_analysis.ipynb` — demographic bias inspection

Generated figures (PDF only) are written to `data/analysis/`.

## Common workflows

**Add a new model:** add it to the model factory in `simulation/factory.py`, then call `scripts/run_model.py <new_model> --mode <mode>`.

**Add a new judge:** call `scripts/run_judge.py <judge_model> --input <jsonl> --output_dir data/llm_judge/<cond>/<crafter>`.

**Re-generate judge inputs after a fresh run:**
```bash
python scripts/collect_judge_input.py --all --condition full
python scripts/collect_judge_input.py --all --condition no_formulation
python scripts/collect_judge_input.py --all --condition zero_shot
```

**Inspect a run:** `streamlit run streamlit_app/Home.py` and navigate to the `Experiments` page.

## Released data for the paper

Beyond the pipeline outputs described above:

- `data/personas/` — the 500 persona specifications (`persona_<id>.json`): demographics, sampled self-report items, active nodes, and `agg_edges` holding the specified weight for each of the 20 directed Ehlers and Clark pairs. These are the gold labels the structural-fidelity results are scored against.
- `data/edge_validation_150/` — the human edge-validation study: per-judgement annotations from two clinical raters and two LLM judges, the study materials given to raters (rubric, instructions, rating form, sample key, and the 150 vignette texts), and the raw judge output. See its own README.
- `data/edge_probe/` — output of the binary edge-recovery probe.

Reproduce the human edge-validation tables:

```bash
python scripts/analyze_edge_validation.py
```

Re-run the probes. The edge probe reads a vignette's prose alone and judges each of the 20 directed pairs; it never receives the graph, the self-report items, or the condition.

```bash
python scripts/run_edge_probe.py                    # binary probe
python scripts/run_graded_edge_probe_flash.py       # graded 0-1 probe
python scripts/run_graded_edge_probe_pro.py
```

## Ethics and intended use

**The dataset contains no real patient material.** Every persona, demographic profile, self-report item, and vignette is model-generated from the documented sampling distributions. The cognitive-model parameters derive from published clinical theory and from prior work that re-derived the Ehlers and Clark graph from ecological momentary assessment data; no individual-level patient data was ingested.

Full-condition vignettes pass as human-written to clinicians 85% of the time, which is an ethical concern as much as a result. Anything redistributing this material should label every vignette as synthetic and as not representing a real individual. We see appropriate uses as standardised training and research stimuli, and we caution against using the set to train or evaluate clinical models without accounting for the theoretical and stylistic commitments it inherits.

Fidelity to one cognitive model is not the same as clinical validity. The framework does not address complex PTSD, comorbidity, or culturally specific presentations.

## Licence

Code is released under the MIT License (see `LICENSE`). The datasets, including
the generated vignettes, persona specifications, and the human edge-validation
study, are released under CC BY 4.0 (see `LICENSE-DATA`, which also sets out
what we ask of anyone reusing the vignettes).

## Citation

```bibtex
@inproceedings{oren2026forma,
  title     = {Generating Clinical Vignettes that Preserve Cognitive Formulations},
  author    = {Oren, Amit and Hertz-Palmor, Nimrod and Ariel, Dean and Laban, Guy},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2026},
  year      = {2026}
}
```
