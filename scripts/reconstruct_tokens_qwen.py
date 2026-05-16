"""
Reconstruct per-experiment token counts for qwen runs that didn't save usage.

Qwen runs (full, no_formulation, zero_shot) load personas from gpt-5.4, so qwen
only makes vignette-stage calls: VignetteCrafter (initial + retries) and
{VignetteValidator|NoFormulationValidator}. Persona-stage calls in the JSON
were made by gpt-5.4 and are not counted here.

The prompts that were actually sent are reconstructed from each experiment JSON
using the same templates the pipeline uses, then tokenized with the Qwen2.5
tokenizer (Qwen2.5 and Qwen3 share the same vocab).

Writes data/analysis/qwen_tokens.csv (per-experiment totals).
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from configs.prompts import (
    VIGNETTE_CRAFTER_PROMPT_CONTEXT, VIGNETTE_CRAFTER_USER_PROMPT,
    VIGNETTE_CRAFTER_RETRY_PROMPT,
    NO_FORMULATION_SR_SYSTEM_PROMPT, NO_FORMULATION_SR_USER_PROMPT,
    VIGNETTE_CRAFTER_NO_FORMULATION_RETRY_PROMPT,
    ZERO_SHOT_DEMOGRAPHICS_SYSTEM_PROMPT, ZERO_SHOT_DEMOGRAPHICS_USER_PROMPT,
    VALIDATOR_VIGNETTE_SYSTEM_PROMPT, VALIDATOR_VIGNETTE_USER_PROMPT,
    VALIDATOR_NO_FORMULATION_SYSTEM_PROMPT, VALIDATOR_NO_FORMULATION_USER_PROMPT,
)
from agents.base_agent import BaseAgent
from simulation.output import write_json

from transformers import AutoTokenizer
import pandas as pd

TOKENIZER_NAME = "Qwen/Qwen2.5-32B-Instruct"
MODELS     = ["qwen2.5-32b", "qwen3.6-35b"]
CONDITIONS = ["full", "no_formulation", "zero_shot"]
OUT_CSV    = REPO / "data" / "analysis" / "qwen_tokens.csv"


def fmt_demographics(d):  return BaseAgent.fmt_demographics(d)
def fmt_self_report(sr):  return BaseAgent.fmt_self_report(sr)
def fmt_active_nodes(nodes_list):
    return "\n".join(f"  - {n}" for n in nodes_list) or "  (none)"
def fmt_required_edges(edges_strs):
    return "\n".join(f"  - {e.replace(' → ', ' → ')}" for e in edges_strs) or "  (none)"

def fmt_demographics_zero_shot(d):
    return "\n".join(f"- {k.replace('_', ' ').title()}: {v}" for k, v in d.items())


def build_validator_system_full(active_components, required_edges_strs):
    return VALIDATOR_VIGNETTE_SYSTEM_PROMPT.format(
        active_components="\n".join(f"  - {n}" for n in sorted(active_components)) or "  (none)",
        required_edges="\n".join(f"  - {e}" for e in required_edges_strs) or "  (none)",
    )


def n_tokens(tok, s):
    if not s:
        return 0
    return len(tok.encode(s, add_special_tokens=False))


def count_call(tok, system, user, assistant):
    """Approximate per-call token cost as len(system)+len(user) input and len(assistant) output."""
    return n_tokens(tok, system) + n_tokens(tok, user), n_tokens(tok, assistant)


def calls_full(data, tok):
    """VignetteCrafter (initial + retries) + VignetteValidator per attempt."""
    demographics   = data["demographics"]
    self_report    = data["self_report"]
    active_nodes   = data.get("active_nodes", [])
    required_edges = data.get("required_edges", [])
    attempts       = data.get("vignette_attempts", [])
    if not attempts:
        return 0, 0, 0

    in_tot = out_tot = n_calls = 0

    # 1. Initial VignetteCrafter call
    user = VIGNETTE_CRAFTER_USER_PROMPT.format(
        demographics=fmt_demographics(demographics),
        self_report=fmt_self_report(self_report),
        active_nodes=fmt_active_nodes(active_nodes),
        required_edges=fmt_required_edges(required_edges),
    )
    i, o = count_call(tok, VIGNETTE_CRAFTER_PROMPT_CONTEXT, user, attempts[0]["vignette"])
    in_tot += i; out_tot += o; n_calls += 1

    validator_system = build_validator_system_full(set(active_nodes), required_edges)

    for idx, att in enumerate(attempts):
        # 2. VignetteValidator on this attempt's vignette
        v_user   = VALIDATOR_VIGNETTE_USER_PROMPT.format(vignette=att["vignette"])
        v_output = json.dumps({
            "verdict": "PASS" if att.get("passed") else "FAIL",
            "violation_edges":        [v["edge"]        for v in att.get("violations", [])],
            "violation_explanations": [v["explanation"] for v in att.get("violations", [])],
        }, ensure_ascii=False)
        i, o = count_call(tok, validator_system, v_user, v_output)
        in_tot += i; out_tot += o; n_calls += 1

        # 3. VignetteCrafter retry call (if not the last attempt)
        if idx < len(attempts) - 1:
            retry_user = VIGNETTE_CRAFTER_RETRY_PROMPT.format(
                feedback=att.get("feedback") or "",
                previous_vignette=att["vignette"],
            )
            # Output: patch blocks producing attempts[idx+1].vignette via diff.
            # Approximate the patch by the added text (next vignette length - this one)
            # plus a small fixed tag overhead (~30 tokens).
            delta_chars = max(0, len(attempts[idx + 1]["vignette"]) - len(att["vignette"]))
            approx_patch = "x" * delta_chars
            i = n_tokens(tok, VIGNETTE_CRAFTER_PROMPT_CONTEXT) + n_tokens(tok, retry_user)
            o = n_tokens(tok, approx_patch) + 30
            in_tot += i; out_tot += o; n_calls += 1

    return in_tot, out_tot, n_calls


def calls_no_formulation(data, tok):
    demographics = data["demographics"]
    self_report  = data["self_report"]
    attempts     = data.get("vignette_attempts", [])
    if not attempts:
        return 0, 0, 0

    in_tot = out_tot = n_calls = 0

    # 1. Initial VignetteCrafter (no formulation)
    user = NO_FORMULATION_SR_USER_PROMPT.format(
        demographics=fmt_demographics(demographics),
        self_report=fmt_self_report(self_report),
    )
    i, o = count_call(tok, NO_FORMULATION_SR_SYSTEM_PROMPT, user, attempts[0]["vignette"])
    in_tot += i; out_tot += o; n_calls += 1

    for idx, att in enumerate(attempts):
        # 2. NoFormulationValidator on this attempt
        v_user = VALIDATOR_NO_FORMULATION_USER_PROMPT.format(
            demographics=fmt_demographics(demographics),
            self_report=fmt_self_report(self_report),
            vignette=att["vignette"],
        )
        missing = att.get("missing", []) or []
        v_output = json.dumps({
            "verdict": "PASS" if att.get("passed") else "FAIL",
            "missing_items":        [m["item"]        for m in missing],
            "missing_explanations": [m["explanation"] for m in missing],
        }, ensure_ascii=False)
        i, o = count_call(tok, VALIDATOR_NO_FORMULATION_SYSTEM_PROMPT, v_user, v_output)
        in_tot += i; out_tot += o; n_calls += 1

        # 3. VignetteCrafter no-formulation retry (full rewrite returned)
        if idx < len(attempts) - 1:
            retry_user = VIGNETTE_CRAFTER_NO_FORMULATION_RETRY_PROMPT.format(
                feedback=att.get("feedback") or "",
                previous_vignette=att["vignette"],
            )
            i, o = count_call(tok, NO_FORMULATION_SR_SYSTEM_PROMPT, retry_user,
                              attempts[idx + 1]["vignette"])
            in_tot += i; out_tot += o; n_calls += 1

    return in_tot, out_tot, n_calls


def calls_zero_shot(data, tok):
    demographics = data["demographics"]
    vignette     = data.get("vignette", "")
    user = ZERO_SHOT_DEMOGRAPHICS_USER_PROMPT.format(
        demographics=fmt_demographics_zero_shot(demographics),
    )
    i, o = count_call(tok, ZERO_SHOT_DEMOGRAPHICS_SYSTEM_PROMPT, user, vignette)
    return i, o, 1


COUNTERS = {"full": calls_full, "no_formulation": calls_no_formulation, "zero_shot": calls_zero_shot}


def main():
    print(f"Loading tokenizer {TOKENIZER_NAME}...")
    tok = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

    rows = []
    for model in MODELS:
        for cond in CONDITIONS:
            run_dir = REPO / "data" / "output" / cond / model
            if not run_dir.is_dir():
                continue
            files = sorted(run_dir.glob("experiment_*.json"),
                           key=lambda p: int(p.stem.split("_")[-1]))
            print(f"  {model:<14} {cond:<14} {len(files):>4} files", flush=True)
            for f in files:
                try:
                    data = json.load(open(f, encoding="utf-8"))
                except Exception as e:
                    print(f"    skip {f.name}: {e}")
                    continue
                pid = data.get("persona_id")
                in_t, out_t, n = COUNTERS[cond](data, tok)
                rows.append({
                    "model":         model,
                    "condition":     cond,
                    "persona_id":    pid,
                    "n_calls":       n,
                    "tokens_input":  in_t,
                    "tokens_output": out_t,
                    "tokens_total":  in_t + out_t,
                })
                data["token_usage"] = {"input": in_t, "output": out_t, "total": in_t + out_t}
                with open(f, "w", encoding="utf-8") as fh:
                    write_json(data, fh)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(df)} rows -> {OUT_CSV}")
    print("\nSummary (mean per experiment):")
    print(df.groupby(["model", "condition"])[["tokens_input", "tokens_output", "tokens_total", "n_calls"]]
            .mean().round(0).to_string())


if __name__ == "__main__":
    main()
