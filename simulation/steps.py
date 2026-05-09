"""
Pipeline step functions for vignette creation and validation.
Each step receives/returns a state dict.
"""
import json
import logging
from pathlib import Path
from agents.vignette_crafter_agent import VignetteCrafterAgent
from agents.zero_shot_vignette_agent import ZeroShotVignetteAgent
from agents.vignette_validator_agent import VignetteValidatorAgent
from agents.no_formulation_validator_agent import NoFormulationValidatorAgent
from agents.persona_crafter_agent import PersonaCrafterAgent
from agents.persona_validator_agent import PersonaValidatorAgent
from data.input.input import (sample_formulation, sample_cognitive_model, sample_demographics,
                              sample_self_report, resample_demographics_fields)

logger = logging.getLogger(__name__)


def step_craft_persona(label: str, persona_id, llms: dict, max_retries: int, n_items: int = 3, node_prob: float = 0.7, edge_prob: float = 0.5) -> dict:
    """Three-stage persona construction:
      Stage 1 — Sample demographics, validate for internal consistency. Retry on FAIL.
      Stage 2 — Sample cognitive model (edges + active nodes). No validation.
      Stage 3 — Sample self-report items for active nodes, validate against demographics
                 and cognitive model. Retry on FAIL.
    """
    persona_validator = PersonaValidatorAgent(
        name=f"{label}_PersonaValidator", role="PersonaValidator", llm=llms["persona_validator"]
    )

    # ── Stage 1: demographics ─────────────────────────────────────────────────
    demographics_attempts = []
    demographics = sample_demographics()

    for attempt in range(max_retries + 1):
        result = persona_validator.validate_demographics(demographics)
        demographics_attempts.append({
            "attempt":            attempt + 1,
            "passed":             result["passed"],
            "issues":             result["issues"],
            "problematic_fields": result["problematic_fields"],
        })
        if result["passed"]:
            logger.info("[%s] demographics PASS on attempt %d", label, attempt + 1)
            break
        logger.warning("[%s] demographics FAIL on attempt %d/%d — fixing fields: %s",
                       label, attempt + 1, max_retries + 1, result["problematic_fields"])
        demographics = resample_demographics_fields(demographics, result["problematic_fields"])

    # ── Stage 2: cognitive model ──────────────────────────────────────────────
    cognitive_model = sample_cognitive_model(node_prob, edge_prob)
    agg_edges    = cognitive_model["edges"]
    active_nodes = cognitive_model["active_nodes"]

    # ── Stage 3: self-report items ────────────────────────────────────────────
    selfreport_attempts = []
    self_report = sample_self_report(cognitive_model, n_items)
    persona_crafter = PersonaCrafterAgent(
        name=f"{label}_PersonaCrafter", role="PersonaCrafter", llm=llms["persona_crafter"],
        n_items=n_items,
    )
    cumulative_bad_keys: dict[str, set] = {}  # tracks all ever-rejected keys per node

    for attempt in range(max_retries + 1):
        result = persona_validator.validate_self_report(demographics, agg_edges, self_report)
        selfreport_attempts.append({
            "attempt":           attempt + 1,
            "passed":            result["passed"],
            "issues":            result["issues"],
            "problematic_items": result["problematic_items"],
        })
        if result["passed"]:
            logger.info("[%s] self-report PASS on attempt %d", label, attempt + 1)
            break
        for node, keys in result["problematic_items"].items():
            cumulative_bad_keys.setdefault(node, set()).update(keys)
        logger.warning("[%s] self-report FAIL on attempt %d/%d — fixing items: %s",
                       label, attempt + 1, max_retries + 1,
                       list(result["problematic_items"].keys()))
        self_report = persona_crafter.fix_self_report(
            demographics, self_report, result["issues"], result["problematic_items"],
            cumulative_bad_keys=cumulative_bad_keys,
        )

    return {
        "agg_edges":                        agg_edges,
        "active_nodes":                     active_nodes,
        "demographics":                     demographics,
        "self_report":                      self_report,
        "demographics_validation_attempts": demographics_attempts,
        "selfreport_validation_attempts":   selfreport_attempts,
    }


def step_persona(label: str, persona_id, llms: dict, persona_context: bool = False,
                 state: dict = None, use_formulation: bool = True, node_prob: float = 0.7,
                 edge_prob: float = 0.5, n_items: int = 3) -> dict:
    # Reuse already-validated inputs from step_craft_persona if available
    if state and "agg_edges" in state:
        agg_edges    = state["agg_edges"]
        demographics = state["demographics"]
        self_report  = state["self_report"]
    else:
        formulation  = sample_formulation(n_items=n_items, node_prob=node_prob, edge_prob=edge_prob)
        agg_edges    = {edge: v["strength"] for edge, v in formulation["edges"].items()}
        demographics = sample_demographics()
        self_report  = {node: data["items"] for node, data in formulation["nodes"].items()}

    formulation = {
        "nodes": {node: {"items": items} for node, items in self_report.items()},
        "edges": {edge: {"strength": weight} for edge, weight in agg_edges.items()},
    }
    vignette_crafter = VignetteCrafterAgent(
        name=f"{label}_VignetteCrafter", role="VignetteCrafter",
        llm=llms["vignette_crafter"],
        use_demographics=persona_context, use_self_report=persona_context,
        use_formulation=use_formulation, demographics=demographics,
        self_report=self_report, formulation=formulation,
    )
    vignette = vignette_crafter.create_vignette()
    return {
        "vignette":          vignette,
        "vignette_attempts": [{"vignette": vignette, "passed": True, "violations": [], "violation_count": 0, "feedback": None}],
        "agg_edges":         agg_edges,
        "demographics":      demographics,
        "self_report":       self_report,
        "_vignette_crafter": vignette_crafter,
    }


def step_zero_shot(label: str, persona_id, llms: dict, node_prob: float = 0.7, edge_prob: float = 0.5, n_items: int = 3,
                   state: dict = None) -> dict:
    agent = ZeroShotVignetteAgent(
        name=f"{label}_ZeroShot", role="ZeroShotVignetteCrafter",
        llm=llms["vignette_crafter"],
    )

    if state and state.get("demographics"):
        demographics = state["demographics"]
        self_report  = {}
        agg_edges    = {}
        fmt_demo = "\n".join(f"- {k.replace('_', ' ').title()}: {v}" for k, v in demographics.items())
        vignette = agent.create_vignette_from_demographics(fmt_demo)
    else:
        formulation  = sample_formulation(n_items=n_items, node_prob=node_prob, edge_prob=edge_prob)
        agg_edges    = {edge: v["strength"] for edge, v in formulation["edges"].items()}
        demographics = sample_demographics()
        self_report  = {node: data["items"] for node, data in formulation["nodes"].items()}
        vignette     = agent.create_vignette()

    return {
        "vignette":                         vignette,
        "vignette_attempts":                [{"vignette": vignette, "passed": True, "missing": [], "missing_count": 0, "feedback": None}],
        "agg_edges":                        agg_edges,
        "demographics":                     demographics,
        "self_report":                      self_report,
        "demographics_validation_attempts": [],
        "selfreport_validation_attempts":   [],
    }


def step_load_persona(label: str, persona_id, persona_source_dir: str) -> dict:
    """Load a previously saved persona from an experiment JSON file.
    Edges are stored as 'A -- B' strings in JSON; this restores them as (A, B) tuples.
    """
    source_path = Path(persona_source_dir) / f"experiment_{persona_id}.json"
    if not source_path.exists():
        raise FileNotFoundError(f"[{label}] Persona source not found: {source_path}")
    with open(source_path, encoding="utf-8") as f:
        data = json.load(f)
    # Restore tuple keys: "A -- B" → ("A", "B")
    raw_edges = data.get("agg_edges", {})
    agg_edges = {tuple(k.split(" -- ")): v for k, v in raw_edges.items()}
    logger.info("[%s] Loaded persona from %s", label, source_path)
    return {
        "source_persona_id":                data.get("persona_id"),
        "agg_edges":                        agg_edges,
        "active_nodes":                     data.get("active_nodes", []),
        "demographics":                     data.get("demographics", {}),
        "self_report":                      data.get("self_report",  {}),
        "demographics_validation_attempts": data.get("demographics_validation_attempts", []),
        "selfreport_validation_attempts":   data.get("selfreport_validation_attempts", []),
    }


def step_validate_no_formulation(label: str, state: dict, validator: NoFormulationValidatorAgent, max_retries: int) -> dict:
    demographics = state["demographics"]
    self_report  = state["self_report"]
    crafter      = state["_vignette_crafter"]

    vignette, attempts = validator.validate_with_retry(
        initial_vignette=state["vignette"],
        demographics=demographics,
        self_report=self_report,
        retry_fn=crafter.create_vignette_with_no_formulation_feedback,
        max_retries=max_retries,
        label=label,
    )
    return {"vignette": vignette, "vignette_attempts": attempts}


def step_validate_persona(label: str, state: dict, validator: VignetteValidatorAgent, max_retries: int) -> dict:
    edges = state["agg_edges"]
    strong   = sum(1 for v in edges.values() if v >= 0.7)
    moderate = sum(1 for v in edges.values() if 0.4 <= v < 0.7)
    inactive = sum(1 for v in edges.values() if v == 0.0)
    logger.info("[%s] Validator — context: %d strong, %d moderate, %d inactive edges",
                label, strong, moderate, inactive)

    vignette, attempts = validator.validate_with_retry(
        initial_vignette=state["vignette"],
        context={"edges": edges},
        retry_fn=state["_vignette_crafter"].create_vignette_with_feedback,
        max_retries=max_retries,
        label=label,
    )
    return {"vignette": vignette, "vignette_attempts": attempts}
