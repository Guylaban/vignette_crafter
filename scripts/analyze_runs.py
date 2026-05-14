"""
analyze_runs.py — load all complete experiment runs and export clean CSVs.

Outputs to data/analysis/:
  summary_by_model_condition.csv  — one row per model × condition
  personas_long.csv               — one row per persona × model × condition

Run with: python scripts/analyze_runs.py
"""

import json
import re
from pathlib import Path

import pandas as pd

ROOT         = Path(__file__).parent.parent
OUTPUT_DIR   = ROOT / "data/output"
ANALYSIS_DIR = ROOT / "data/analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


def load_all_runs() -> dict[tuple[str, str], Path]:
    runs = {}
    for condition_dir in OUTPUT_DIR.iterdir():
        if not condition_dir.is_dir() or condition_dir.name.startswith("_"):
            continue
        for model_dir in condition_dir.iterdir():
            if not model_dir.is_dir():
                continue
            if list(model_dir.glob("experiment_*.json")):
                runs[(model_dir.name, condition_dir.name)] = model_dir
    return runs


def parse_experiment(f: Path, model: str, mode: str) -> dict | None:
    try:
        data = json.load(open(f, encoding="utf-8"))
    except Exception:
        return None

    summary  = data.get("validation_summary") or {}
    tokens   = data.get("token_usage") or {}
    demo     = data.get("demographics") or {}

    is_zero_shot = (mode == "zero_shot")
    row = {
        "model":               model,
        "condition":           mode,
        "persona_id":          data.get("persona_id"),
        "source_persona_id":   data.get("source_persona_id"),
        "word_count":          data.get("vignette_word_count", 0),
        "has_vignette":        len(data.get("vignette", "").strip()) > 50,
        "n_attempts":          1 if is_zero_shot else summary.get("attempts", 1),
        "ultimately_passed":   True if is_zero_shot else summary.get("ultimately_passed", False),
        "attempt_1_passed":    True if is_zero_shot else (summary.get("attempts", 1) == 1 and summary.get("ultimately_passed", False)),
        "tokens_input":        tokens.get("input", 0),
        "tokens_output":       tokens.get("output", 0),
        "tokens_total":        tokens.get("total", 0),
        "age":                 demo.get("age"),
        "gender":              demo.get("gender"),
        "ethnicity":           demo.get("ethnicity"),
        "trauma_type":         demo.get("trauma_type"),
        "pcl5":                demo.get("pcl5"),
        "relationship_status": demo.get("relationship_status"),
        "occupation":          demo.get("occupation"),
    }

    if mode == "full":
        row.update({
            "edge_coverage_rate":        data.get("edge_coverage_rate"),
            "edge_density":              data.get("edge_density"),
            "mean_required_edge_weight": data.get("mean_required_edge_weight"),
            "n_required_edges":          len(data.get("required_edges", [])),
            "n_satisfied_edges":         len(data.get("satisfied_edges", [])),
            "n_active_nodes":            len(data.get("active_nodes", [])),
        })
    else:
        row.update({
            "edge_coverage_rate": None, "edge_density": None,
            "mean_required_edge_weight": None, "n_required_edges": None,
            "n_satisfied_edges": None, "n_active_nodes": None,
        })

    return row


print("Scanning run directories...")
canonical_runs = load_all_runs()
print(f"Found {len(canonical_runs)} model × condition combinations\n")

rows = []
for (model, mode), run_dir in sorted(canonical_runs.items()):
    files = sorted(
        run_dir.glob("experiment_*.json"),
        key=lambda f: int(re.search(r"(\d+)", f.stem).group(1))
    )
    parsed = 0
    for f in files:
        row = parse_experiment(f, model, mode)
        if row:
            rows.append(row)
            parsed += 1
    print(f"  {model:30s} [{mode:14s}]  {parsed:>3} personas  ({run_dir.name})")

df = pd.DataFrame(rows)
print(f"\nTotal rows loaded: {len(df)}")

out_long = ANALYSIS_DIR / "personas_long.csv"
df.to_csv(out_long, index=False, encoding="utf-8")
print(f"\nSaved: {out_long}  ({len(df)} rows)")

agg = (
    df.groupby(["model", "condition"])
    .agg(
        n_personas             = ("persona_id",               "count"),
        word_count_mean        = ("word_count",               "mean"),
        word_count_std         = ("word_count",               "std"),
        word_count_min         = ("word_count",               "min"),
        word_count_max         = ("word_count",               "max"),
        attempt_1_pass_rate    = ("attempt_1_passed",         "mean"),
        mean_attempts          = ("n_attempts",               "mean"),
        ultimately_passed_rate = ("ultimately_passed",        "mean"),
        tokens_input_mean      = ("tokens_input",             "mean"),
        tokens_output_mean     = ("tokens_output",            "mean"),
        tokens_total_mean      = ("tokens_total",             "mean"),
        edge_coverage_mean     = ("edge_coverage_rate",       "mean"),
        edge_density_mean      = ("edge_density",             "mean"),
        mean_edge_weight       = ("mean_required_edge_weight","mean"),
        n_required_edges_mean  = ("n_required_edges",         "mean"),
        n_active_nodes_mean    = ("n_active_nodes",           "mean"),
    )
    .round(4)
    .reset_index()
)

out_summary = ANALYSIS_DIR / "summary_by_model_condition.csv"
agg.to_csv(out_summary, index=False, encoding="utf-8")
print(f"Saved: {out_summary}  ({len(agg)} rows)")

print("\n" + "=" * 90)
print(f"{'Model':<30} {'Condition':<15} {'N':>5} {'Words':>7} {'Pass@1':>7} {'Attempts':>9} {'Tokens':>8}")
print("=" * 90)
for _, r in agg.iterrows():
    print(
        f"{r['model']:<30} {r['condition']:<15} {int(r['n_personas']):>5} "
        f"{r['word_count_mean']:>7.0f} {r['attempt_1_pass_rate']:>7.1%} "
        f"{r['mean_attempts']:>9.2f} {r['tokens_total_mean']:>8.0f}"
    )
print("=" * 90)
print("\nDone.")
