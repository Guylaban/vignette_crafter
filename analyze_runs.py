"""
analyze_runs.py — load all complete experiment runs and export clean CSVs.

Outputs to data/analysis/:
  summary_by_model_condition.csv  — one row per model × condition
  personas_long.csv               — one row per persona × model × condition

Run with: python analyze_runs.py
"""

import json
import re
from pathlib import Path

import pandas as pd

OUTPUT_DIR   = Path("data/output")
ANALYSIS_DIR = Path("data/analysis")
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


# ── 1. Identify canonical run for each (model, condition) ─────────────────────

def load_all_runs() -> dict[tuple[str, str], Path]:
    """Return {(model, mode): run_dir} keeping the most complete dir per pair."""
    best: dict[tuple[str, str], tuple[Path, int]] = {}
    for d in OUTPUT_DIR.glob("vignette_from_persona_*"):
        files = list(d.glob("experiment_*.json"))
        if not files:
            continue
        try:
            data = json.load(open(files[0], encoding="utf-8"))
            cfg  = data.get("config", {})
            model = cfg.get("models", {}).get("vignette_crafter", "?")
            mode  = cfg.get("vignette_mode", "full")
            key   = (model, mode)
            if key not in best or len(files) > best[key][1]:
                best[key] = (d, len(files))
        except Exception:
            continue
    return {k: v[0] for k, v in best.items()}


# ── 2. Parse a single experiment file ─────────────────────────────────────────

def parse_experiment(f: Path, model: str, mode: str) -> dict | None:
    try:
        data = json.load(open(f, encoding="utf-8"))
    except Exception:
        return None

    summary  = data.get("validation_summary", {})
    tokens   = data.get("token_usage", {})
    demo     = data.get("demographics", {})
    attempts = data.get("vignette_attempts", [])

    row = {
        "model":            model,
        "condition":        mode,
        "persona_id":       data.get("persona_id"),
        "source_persona_id": data.get("source_persona_id"),
        # vignette
        "word_count":       data.get("vignette_word_count", 0),
        "has_vignette":     len(data.get("vignette", "").strip()) > 50,
        # validation
        "n_attempts":       summary.get("attempts", 1),
        "ultimately_passed": summary.get("ultimately_passed", False),
        "attempt_1_passed": (summary.get("attempts", 1) == 1 and summary.get("ultimately_passed", False)),
        # tokens
        "tokens_input":     tokens.get("input", 0),
        "tokens_output":    tokens.get("output", 0),
        "tokens_total":     tokens.get("total", 0),
        # demographics
        "age":              demo.get("age"),
        "gender":           demo.get("gender"),
        "ethnicity":        demo.get("ethnicity"),
        "trauma_type":      demo.get("trauma_type"),
        "pcl5":             demo.get("pcl5"),
        "relationship_status": demo.get("relationship_status"),
        "occupation":       demo.get("occupation"),
    }

    # formulation fields (full condition only)
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
            "edge_coverage_rate":        None,
            "edge_density":              None,
            "mean_required_edge_weight": None,
            "n_required_edges":          None,
            "n_satisfied_edges":         None,
            "n_active_nodes":            None,
        })

    return row


# ── 3. Load all personas ───────────────────────────────────────────────────────

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


# ── 4. Save personas_long.csv ──────────────────────────────────────────────────

out_long = ANALYSIS_DIR / "personas_long.csv"
df.to_csv(out_long, index=False, encoding="utf-8")
print(f"\nSaved: {out_long}  ({len(df)} rows)")


# ── 5. Build summary_by_model_condition.csv ───────────────────────────────────

agg = (
    df.groupby(["model", "condition"])
    .agg(
        n_personas          = ("persona_id",             "count"),
        word_count_mean     = ("word_count",             "mean"),
        word_count_std      = ("word_count",             "std"),
        word_count_min      = ("word_count",             "min"),
        word_count_max      = ("word_count",             "max"),
        attempt_1_pass_rate = ("attempt_1_passed",       "mean"),
        mean_attempts       = ("n_attempts",             "mean"),
        ultimately_passed_rate = ("ultimately_passed",   "mean"),
        tokens_input_mean   = ("tokens_input",           "mean"),
        tokens_output_mean  = ("tokens_output",          "mean"),
        tokens_total_mean   = ("tokens_total",           "mean"),
        edge_coverage_mean  = ("edge_coverage_rate",     "mean"),
        edge_density_mean   = ("edge_density",           "mean"),
        mean_edge_weight    = ("mean_required_edge_weight", "mean"),
        n_required_edges_mean = ("n_required_edges",     "mean"),
        n_active_nodes_mean = ("n_active_nodes",         "mean"),
    )
    .round(4)
    .reset_index()
)

out_summary = ANALYSIS_DIR / "summary_by_model_condition.csv"
agg.to_csv(out_summary, index=False, encoding="utf-8")
print(f"Saved: {out_summary}  ({len(agg)} rows)")


# ── 6. Print summary table ────────────────────────────────────────────────────

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
