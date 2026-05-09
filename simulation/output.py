import json
import math
import textwrap
import numpy as np

WRAP_WIDTH = 100


def wrap(text: str) -> str:
    return "\n".join(
        textwrap.fill(line, width=WRAP_WIDTH) if line.strip() else ""
        for line in text.splitlines()
    )


def to_serializable(obj):
    if isinstance(obj, dict):
        def _key(k):
            if isinstance(k, tuple):
                return " -- ".join(k)
            if isinstance(k, np.integer):
                return int(k)
            return k
        return {_key(k): to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(i) for i in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


def write_json(output: dict, f):
    """Write output JSON with blank lines between vignette attempts."""
    vignette_attempts = output.pop("vignette_attempts", None)

    if vignette_attempts is None:
        f.write(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
        return

    f.write(json.dumps(output, indent=2, ensure_ascii=False)[:-1])

    f.write(',\n\n  "vignette_attempts": [\n')
    for i, attempt in enumerate(vignette_attempts):
        f.write("    " + json.dumps(attempt, ensure_ascii=False))
        f.write(",\n\n" if i < len(vignette_attempts) - 1 else "\n")
    f.write("  ]\n}\n")



def write_txt(output: dict, path):
    """Write a human-readable vignette report."""
    SEP = "─" * WRAP_WIDTH

    def section(title):
        return f"\n{title}\n{SEP}\n"

    with open(path, "w", encoding="utf-8") as f:

        # ── Header ──────────────────────────────────────────────────────────
        f.write(f"PERSONA {output['persona_id']}  |  {output['experiment_timestamp']}\n")
        f.write(SEP + "\n")

        # ── Config ──────────────────────────────────────────────────────────
        cfg = output.get("config", {})
        f.write(section("CONFIG"))
        f.write(f"  pipeline:    {cfg.get('pipeline')}\n")
        f.write(f"  temperature: {cfg.get('temperature')}\n")
        f.write(f"  max_retries: {cfg.get('max_retries')}\n")
        f.write(f"  seed:        {cfg.get('seed')}\n")
        f.write("  models:\n")
        for role, model in cfg.get("models", {}).items():
            f.write(f"    {role:<20} {model}\n")

        # ── Demographics ─────────────────────────────────────────────────────
        demo = output.get("demographics", {})
        f.write(section("DEMOGRAPHICS"))
        for k, v in demo.items():
            f.write(f"  {k:<15} {v}\n")

        # ── Self-report ──────────────────────────────────────────
        sr = output.get("self_report", {})
        f.write(section("SELF-REPORT"))
        for node, items in sr.items():
            if not items:
                continue
            f.write(f"  {node}:\n")
            for item in items:
                if isinstance(item, dict) and "key" in item:
                    f.write(f"    • {item['key']}: {item['value']}\n")
                else:
                    f.write(f"    • {item}\n")

        # ── Aggregated edges ─────────────────────────────────────────────────
        f.write(section("COGNITIVE MODEL EDGES"))
        for edge, val in output.get("agg_edges", {}).items():
            arrow = edge.replace("--", "→")
            f.write(f"  {arrow:<50} {val:.4f}\n")

        # ── Demographics validation ───────────────────────────────────────────
        demo_attempts = output.get("demographics_validation_attempts", [])
        if demo_attempts:
            f.write(section("DEMOGRAPHICS VALIDATION"))
            for attempt in demo_attempts:
                status = "PASS" if attempt["passed"] else "FAIL"
                f.write(f"  [{attempt['attempt']}] {status}\n")
                for issue in attempt.get("issues", []):
                    f.write(f"    item:        {issue['field']}\n")
                    f.write(f"    explanation: {issue['explanation']}\n")

        # ── Self-report validation ────────────────────────────────────────────
        sr_attempts = output.get("selfreport_validation_attempts", [])
        if sr_attempts:
            f.write(section("SELF-REPORT VALIDATION"))
            for attempt in sr_attempts:
                status = "PASS" if attempt["passed"] else "FAIL"
                f.write(f"  [{attempt['attempt']}] {status}\n")
                for issue in attempt.get("issues", []):
                    f.write(f"    item:        {issue['component']} / {issue['item']}\n")
                    f.write(f"    explanation: {issue['explanation']}\n")

        # ── Token usage ──────────────────────────────────────────────────────
        tu = output.get("token_usage", {})
        if tu:
            f.write(section("TOKEN USAGE"))
            f.write(f"  input:   {tu.get('input',  0):>8,}\n")
            f.write(f"  output:  {tu.get('output', 0):>8,}\n")
            f.write(f"  total:   {tu.get('total',  0):>8,}\n")

        # ── Validation summary ───────────────────────────────────────────────
        vs = output.get("validation_summary", {})
        status = "PASS" if vs.get("ultimately_passed") else "FAIL"
        f.write(section("VALIDATION SUMMARY"))
        f.write(f"  {vs.get('attempts', 0)} attempt(s)  →  {status}\n")

        # ── Vignette validation attempts ──────────────────────────────────────
        f.write(section("VIGNETTE ATTEMPTS"))
        for i, attempt in enumerate(output.get("vignette_attempts", []), 1):
            status = "PASS" if attempt["passed"] else "FAIL"
            f.write(f"\n  [{i}] {status}\n")
            f.write(wrap(attempt["vignette"]) + "\n")
            for v in attempt.get("violations", []):
                f.write(f"\n    ✗ edge:        {v['edge']}\n")
                f.write(f"      explanation: {v['explanation']}\n")

        # ── Vignette (final) ─────────────────────────────────────────────────
        f.write(section("VIGNETTE (final)"))
        f.write(wrap(output.get("vignette", "")) + "\n")
