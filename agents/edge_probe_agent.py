"""Edge Probe Agent: independent per-edge presence judgement.

For each vignette, this agent rates whether each of the 20 directed
Ehlers & Clark edges (A -> B) is conveyed in the text. Critically, the
agent is BLIND to the persona's prompted active_nodes / required_edges
set, so its judgements are an independent check on whether the
formulation actually shaped the text.

Uses the same causal standard as the structural Vignette Validator:
an edge A -> B is present iff some paragraph in the vignette names both
components (or their synonyms) and conveys that A influences, drives, or
leads to B.
"""
from typing import Literal
from pydantic import BaseModel, Field
from agents.base_agent import BaseAgent
from configs.formulation_config import COMPONENT_SYNONYMS

COMPONENTS = list(COMPONENT_SYNONYMS.keys())  # 5 nodes
DIRECTED_EDGES = [(a, b) for a in COMPONENTS for b in COMPONENTS if a != b]  # 20


def _field(a: str, b: str) -> str:
    return f"{a.replace(' ', '_')}__to__{b.replace(' ', '_')}"


# Build the schema dynamically: 20 binary fields, one per directed edge.
_fields = {
    _field(a, b): (Literal[0, 1], Field(description=f"Does the vignette convey {a} influencing {b}?"))
    for a, b in DIRECTED_EDGES
}
_fields["rationale"] = (str, Field(description="One short sentence summary."))

# Use pydantic's create_model to build the schema at import time
from pydantic import create_model
EdgeProbeOutput = create_model("EdgeProbeOutput", **_fields)


EDGE_PROBE_SYSTEM_PROMPT = """You are evaluating a PTSD case vignette for the presence of causal
connections between five Ehlers & Clark cognitive components: Triggers, Negative Appraisals, Memory,
Threat, and Maladaptive Strategies.

For each of the 20 ordered, directed (A -> B) pairs of distinct components, decide whether the
vignette conveys, in some paragraph, that A influences, drives, or leads to B. Apply the same
causal standard as a structural validator:

COMPONENT SYNONYMS (any of these synonyms count as the component appearing):
  Triggers              -> "triggers", "reminders", "cues", "triggering stimuli"
  Negative Appraisals   -> "negative appraisals", "negative beliefs", "appraisals", "distorted beliefs"
  Memory                -> "intrusive memory", "trauma memory", "traumatic memory", "the memory"
  Threat                -> "sense of threat", "perceived threat", "threat", "feeling of danger"
  Maladaptive Strategies-> "maladaptive strategies", "avoidance", "safety behaviours", "maladaptive coping"

CAUSAL STANDARD
An edge A -> B is PRESENT (return 1) iff, within the same paragraph:
  (i) both A and B (or their synonyms) appear; AND
  (ii) the paragraph conveys that A influences / drives / leads to B, through direct causal
       language, sequential structure, or connecting phrases like "because of", "this meant",
       "so", "which led", "as a result", "consequently", "in turn".
If no paragraph conveys the A -> B relationship, return 0 for that edge.

You will return a binary judgement for each of the 20 ordered pairs. Be strict: do not assume
an edge based on mere co-occurrence; the paragraph must actually convey directional influence.
"""

EDGE_PROBE_USER_PROMPT = """Evaluate the following vignette and judge each of the 20 directed edges
(A -> B) on whether the vignette conveys A influencing B.

VIGNETTE
{vignette}
"""


class EdgeProbeAgent(BaseAgent):
    def __init__(self, name: str, role: str, llm):
        super().__init__(name, role, EDGE_PROBE_SYSTEM_PROMPT, llm)

    def setup_agent(self):
        return None

    def probe(self, vignette_text: str):
        """Return EdgeProbeOutput model with 20 binary fields plus rationale."""
        user = EDGE_PROBE_USER_PROMPT.format(vignette=vignette_text.strip())
        return self._invoke_structured(EdgeProbeOutput, EDGE_PROBE_SYSTEM_PROMPT, user)
