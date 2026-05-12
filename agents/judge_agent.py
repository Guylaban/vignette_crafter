"""LLM-as-a-judge agent for rating PTSD clinical vignettes."""

from typing import Literal
from pydantic import BaseModel, Field
from agents.base_agent import BaseAgent


# ── Structured output schema ──────────────────────────────────────────────────

class JudgeRating(BaseModel):
    """Ratings produced by the LLM judge for a single vignette."""

    # Content Validity Index
    clarity:            Literal[1, 2, 3] = Field(description="How clearly is the vignette written? 1=Unclear, 2=Somewhat clear, 3=Very clear")
    relevance:          Literal[1, 2, 3] = Field(description="Is this vignette relevant to a PTSD case? 1=Not relevant, 2=Somewhat, 3=Very relevant")
    representativeness: Literal[1, 2, 3] = Field(description="Does this accurately represent PTSD as seen in clinical practice? 1=Not representative, 2=Somewhat, 3=Very representative")

    # Construction quality (Evans guidelines)
    g1_grounded: Literal[1, 2, 3] = Field(description="The vignette appears grounded in realistic clinical experience or literature. 1=Not at all, 2=Somewhat, 3=Very much")
    g2_narrative: Literal[1, 2, 3] = Field(description="The vignette reads as a personal narrative rather than a symptom checklist. 1=Not at all, 2=Somewhat, 3=Very much")
    g3_explicit:  Literal[1, 2, 3] = Field(description="PTSD-relevant details are explicit and identifiable. 1=Not at all, 2=Somewhat, 3=Very much")
    g4_relevant:  Literal[1, 2, 3] = Field(description="Only relevant clinical information is included; nothing confusing or misleading. 1=Not at all, 2=Somewhat, 3=Very much")

    # DSM-5 criteria (1=present, 0=absent)
    dsm_a: Literal[0, 1] = Field(description="Criterion A: Traumatic event exposure is described. 1=present, 0=absent")
    dsm_b: Literal[0, 1] = Field(description="Criterion B: Intrusion symptoms present (flashbacks, nightmares, distress at cues). 1=present, 0=absent")
    dsm_c: Literal[0, 1] = Field(description="Criterion C: Avoidance of internal thoughts or external reminders. 1=present, 0=absent")
    dsm_d: Literal[0, 1] = Field(description="Criterion D: Negative cognitions or mood (guilt, shame, detachment, numbing, negative beliefs). 1=present, 0=absent")
    dsm_e: Literal[0, 1] = Field(description="Criterion E: Hyperarousal or reactivity (hypervigilance, startle, sleep problems, irritability). 1=present, 0=absent")
    dsm_g: Literal[0, 1] = Field(description="Criterion G: Functional impairment is mentioned. 1=present, 0=absent")

    # Ehlers & Clark (2000) components (1=present, 0=absent)
    ec_threat:     Literal[0, 1] = Field(description="Sense of current threat: the person feels the trauma is still happening or still dangerous now. 1=present, 0=absent")
    ec_appraisals: Literal[0, 1] = Field(description="Negative appraisals: catastrophic or overly negative interpretation of the trauma or its aftermath. 1=present, 0=absent")
    ec_memory:     Literal[0, 1] = Field(description="Nature of trauma memory: fragmented, disorganised, feels like happening now rather than in the past. 1=present, 0=absent")
    ec_strategies: Literal[0, 1] = Field(description="Maladaptive coping strategies that maintain PTSD (avoidance, thought suppression, rumination, substance use). 1=present, 0=absent")
    ec_triggers:   Literal[0, 1] = Field(description="Triggers for re-experiencing: specific internal or external cues that activate trauma memory or distress. 1=present, 0=absent")

    rationale: str = Field(description="2-3 sentence summary of your key observations — what the vignette does well and any notable weaknesses.")


# ── Prompts ───────────────────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """\
You are a critical reviewer evaluating short clinical vignettes for a PTSD research study.
Your job is to rate each vignette on several dimensions. You must be discriminating —
most vignettes will have genuine weaknesses. Reserve score 3 only for truly exceptional
writing or criterion coverage; score 1 for clear failures; score 2 for the typical case
that is adequate but imperfect.

## Rating anchors

**CVI scales (1–3):**
- Clarity 1 = hard to follow, ambiguous or contradictory phrasing; 2 = readable but some
awkward phrasing or vague descriptions; 3 = exceptionally clear, precise, and easy to follow
- Relevance 1 = little connection to PTSD; 2 = clearly a PTSD case but generic or thin;
3 = directly and richly relevant to PTSD
- Representativeness 1 = atypical, implausible, or stereotyped presentation; 2 = plausible
but could fit many anxiety disorders; 3 = distinctly representative of PTSD as seen clinically

**Construction quality (1–3):**
- g1 Grounded 1 = reads like a textbook example or symptom list; 2 = some grounding in
realistic detail; 3 = clearly rooted in lived clinical experience
- g2 Narrative 1 = reads as a symptom checklist; 2 = narrative frame present but thin;
3 = fully personal narrative with character, context, and flow
- g3 Explicit 1 = PTSD features buried or only implied; 2 = most features identifiable with
effort; 3 = PTSD details named and shown, not just implied
- g4 Relevant 1 = contains distracting, irrelevant, or misleading content; 2 = mostly
focused with minor noise; 3 = every detail serves the clinical picture

**DSM-5 criteria (0/1):** Score 1 only if the criterion is clearly and explicitly present
in the text — not merely inferable. Score 0 if absent or only vaguely implied.

**Ehlers & Clark components (0/1):** Score 1 only if the component is explicitly shown,
not just consistent with having PTSD.

## Important
- Do NOT give all maximum scores. If a vignette scores 3 on every dimension, re-read it
and identify at least one genuine weakness.
- Base ratings solely on what is written — do not infer content that is not present.
"""

JUDGE_USER_PROMPT = """\
Rate the following clinical vignette:

---
{vignette}
---

Provide your ratings in the required structured format.
"""


# ── Agent ─────────────────────────────────────────────────────────────────────

class JudgeAgent(BaseAgent):
    def __init__(self, name: str, role: str, llm):
        super().__init__(name, role, JUDGE_SYSTEM_PROMPT, llm)

    def setup_agent(self):
        return None

    def rate(self, vignette_text: str) -> JudgeRating | None:
        """Rate a single vignette. Returns JudgeRating or None on parse failure."""
        user_prompt = JUDGE_USER_PROMPT.format(vignette=vignette_text.strip())
        return self._invoke_structured(JudgeRating, self.system_prompt, user_prompt)
