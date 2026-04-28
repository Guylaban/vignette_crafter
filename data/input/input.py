import random
from configs.formulation_config import DIRECT_EDGES
from configs.demographics import AGE, GENDER, ETHNICITY, RELATIONSHIP_STATUS, OCCUPATION, TRAUMA_TYPE, PCL5
from configs.self_report import (TRIGGERS, NEGATIVE_APPRAISALS, MEMORY,
                                  THREAT, MALADAPTIVE_STRATEGIES,
                                  DISTRACTION_STRATEGIES, AVOIDANCE_STRATEGIES)

_STRATEGIES_POOL = {**MALADAPTIVE_STRATEGIES, **DISTRACTION_STRATEGIES, **AVOIDANCE_STRATEGIES}

_NODE_POOLS: dict[str, dict] = {
    "Triggers":               TRIGGERS,
    "Negative Appraisals":    NEGATIVE_APPRAISALS,
    "Memory":                 MEMORY,
    "Threat":                 THREAT,
    "Maladaptive Strategies": _STRATEGIES_POOL,
}


# ── Sampling ──────────────────────────────────────────────────────────────────

def sample_demographics() -> dict:
    """Sample a random patient demographics profile."""
    return {
        "age":                 random.randint(AGE["min"], AGE["max"]),
        "gender":              random.choices(list(GENDER), weights=list(GENDER.values()))[0],
        "ethnicity":           random.choice(ETHNICITY),
        "relationship_status": random.choice(RELATIONSHIP_STATUS),
        "occupation":          random.choice(OCCUPATION),
        "trauma_type":         random.choice(TRAUMA_TYPE),
        "pcl5":                random.randint(PCL5["min"], PCL5["max"]),
    }


def resample_demographics_fields(demographics: dict, fields: list[str]) -> dict:
    """Re-sample only the specified fields, keeping all others unchanged."""
    _samplers = {
        "age":                 lambda: random.randint(AGE["min"], AGE["max"]),
        "gender":              lambda: random.choices(list(GENDER), weights=list(GENDER.values()))[0],
        "ethnicity":           lambda: random.choice(ETHNICITY),
        "relationship_status": lambda: random.choice(RELATIONSHIP_STATUS),
        "occupation":          lambda: random.choice(OCCUPATION),
        "trauma_type":         lambda: random.choice(TRAUMA_TYPE),
        "pcl5":                lambda: random.randint(PCL5["min"], PCL5["max"]),
    }
    updated = dict(demographics)
    for field in fields:
        if field in _samplers:
            updated[field] = _samplers[field]()
    return updated


def sample_self_report(cognitive_model: dict, n_items: int = 3) -> dict:
    """Sample self-report items for each active node in the cognitive model.
    Returns dict of node_name → list of {key, value} dicts.
    """
    result = {}
    for node in cognitive_model["active_nodes"]:
        pool = _NODE_POOLS.get(node, {})
        sampled = random.sample(list(pool.items()), min(n_items, len(pool)))
        result[node] = [{"key": k, "value": v} for k, v in sampled]
    return result


_ALL_NODES = list(dict.fromkeys(n for edge in DIRECT_EDGES for n in edge))

def sample_cognitive_model(node_prob: float = 0.7, edge_prob: float = 0.5) -> dict:
    """Sample a random cognitive model for the Ehlers & Clark graph.

    Step 1 — each node is independently activated with probability node_prob.
    Step 2 — each directed edge where both endpoints are active is independently
              activated with probability edge_prob, then gets a random weight in
              (0.0, 1.0]. Inactive edges are set to 0.
    Step 3 — active_nodes are derived from edges: any node that appears in at
              least one active edge. This means a node activated in step 1 but
              with no active edges is treated as inactive.

    Returns {"edges": {(parent, child): float}, "active_nodes": [str]}.
    """
    active_set = {n for n in _ALL_NODES if random.random() < node_prob}
    edges = {
        (p, c): (
            round(random.uniform(0.01, 1.0), 4)
            if p in active_set and c in active_set and random.random() < edge_prob
            else 0.0
        )
        for (p, c) in DIRECT_EDGES
    }
    active_nodes = list(dict.fromkeys(
        n for (p, c), w in edges.items() if w > 0 for n in (p, c)
    ))
    return {"edges": edges, "active_nodes": active_nodes}


def sample_formulation(n_items: int = 3, node_prob: float = 0.7, edge_prob: float = 0.5) -> dict:
    """Sample a full formulation (cognitive model + self-report items).
    Returns {"nodes": ..., "edges": ...} — used by paths that skip step_craft_persona.
    """
    model = sample_cognitive_model(node_prob, edge_prob)
    ni    = sample_self_report(model, n_items)
    return {
        "nodes": {node: {"items": items} for node, items in ni.items()},
        "edges": {
            edge: {
                "strength":     weight,
                "parent_items": ni.get(edge[0], []),
                "child_items":  ni.get(edge[1], []),
            }
            for edge, weight in model["edges"].items()
        },
    }
