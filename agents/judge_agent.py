"""LLM-as-a-judge agent for rating PTSD clinical vignettes.

Each dimension is rated in a separate LLM call to avoid anchoring effects.
Within each call, the model reasons (CoT) before committing to a score.
"""

from typing import Literal
from pydantic import BaseModel, Field
from agents.base_agent import BaseAgent
from configs.prompts import (
    JUDGE_CLARITY_SYSTEM_PROMPT, JUDGE_RELEVANCE_SYSTEM_PROMPT,
    JUDGE_IMPORTANCE_SYSTEM_PROMPT,
    JUDGE_G1_SYSTEM_PROMPT, JUDGE_G2_SYSTEM_PROMPT,
    JUDGE_G3_SYSTEM_PROMPT, JUDGE_G4_SYSTEM_PROMPT,
    JUDGE_DSM_A_SYSTEM_PROMPT, JUDGE_DSM_B_SYSTEM_PROMPT,
    JUDGE_DSM_C_SYSTEM_PROMPT, JUDGE_DSM_D_SYSTEM_PROMPT,
    JUDGE_DSM_E_SYSTEM_PROMPT, JUDGE_DSM_G_SYSTEM_PROMPT,
    JUDGE_EC_THREAT_SYSTEM_PROMPT, JUDGE_EC_APPRAISALS_SYSTEM_PROMPT,
    JUDGE_EC_MEMORY_SYSTEM_PROMPT, JUDGE_EC_STRATEGIES_SYSTEM_PROMPT,
    JUDGE_EC_TRIGGERS_SYSTEM_PROMPT,
    JUDGE_USER_PROMPT,
)


# ── Per-dimension schemas ─────────────────────────────────────────────────────

class _Scale3(BaseModel):
    reasoning: str = Field(description="Quote the specific sentence(s) from the vignette that most influenced your rating, then explain why they justify your score.")
    score: Literal[1, 2, 3]
    rationale: str = Field(description="One sentence summary of your score.")

class _Scale2(BaseModel):
    reasoning: str = Field(description="Quote the specific sentence(s) from the vignette that most influenced your rating, then explain whether this criterion is present or absent.")
    score: Literal[0, 1]
    rationale: str = Field(description="One sentence summary of your score.")


# ── Combined output schema ────────────────────────────────────────────────────

class JudgeRating(BaseModel):
    """Ratings produced by the LLM judge for a single vignette."""

    clarity:    Literal[1, 2, 3]
    relevance:  Literal[1, 2, 3]
    importance: Literal[1, 2, 3]

    g1_grounded:  Literal[1, 2, 3]
    g2_narrative: Literal[1, 2, 3]
    g3_explicit:  Literal[1, 2, 3]
    g4_relevant:  Literal[1, 2, 3]

    dsm_a: Literal[0, 1]
    dsm_b: Literal[0, 1]
    dsm_c: Literal[0, 1]
    dsm_d: Literal[0, 1]
    dsm_e: Literal[0, 1]
    dsm_g: Literal[0, 1]

    ec_threat:     Literal[0, 1]
    ec_appraisals: Literal[0, 1]
    ec_memory:     Literal[0, 1]
    ec_strategies: Literal[0, 1]
    ec_triggers:   Literal[0, 1]

    rationale: str


# ── Agent ─────────────────────────────────────────────────────────────────────

class JudgeAgent(BaseAgent):
    def __init__(self, name: str, role: str, llm):
        super().__init__(name, role, "", llm)

    def setup_agent(self):
        return None

    def _rate_one(self, schema, system_prompt: str, user_prompt: str):
        return self._invoke_structured(schema, system_prompt, user_prompt)

    def rate(self, vignette_text: str) -> JudgeRating | None:
        """Rate a vignette with one CoT call per dimension."""
        user_prompt = JUDGE_USER_PROMPT.format(vignette=vignette_text.strip())

        dims = [
            ("clarity",       _Scale3, JUDGE_CLARITY_SYSTEM_PROMPT),
            ("relevance",     _Scale3, JUDGE_RELEVANCE_SYSTEM_PROMPT),
            ("importance",    _Scale3, JUDGE_IMPORTANCE_SYSTEM_PROMPT),
            ("g1_grounded",   _Scale3, JUDGE_G1_SYSTEM_PROMPT),
            ("g2_narrative",  _Scale3, JUDGE_G2_SYSTEM_PROMPT),
            ("g3_explicit",   _Scale3, JUDGE_G3_SYSTEM_PROMPT),
            ("g4_relevant",   _Scale3, JUDGE_G4_SYSTEM_PROMPT),
            ("dsm_a",         _Scale2, JUDGE_DSM_A_SYSTEM_PROMPT),
            ("dsm_b",         _Scale2, JUDGE_DSM_B_SYSTEM_PROMPT),
            ("dsm_c",         _Scale2, JUDGE_DSM_C_SYSTEM_PROMPT),
            ("dsm_d",         _Scale2, JUDGE_DSM_D_SYSTEM_PROMPT),
            ("dsm_e",         _Scale2, JUDGE_DSM_E_SYSTEM_PROMPT),
            ("dsm_g",         _Scale2, JUDGE_DSM_G_SYSTEM_PROMPT),
            ("ec_threat",     _Scale2, JUDGE_EC_THREAT_SYSTEM_PROMPT),
            ("ec_appraisals", _Scale2, JUDGE_EC_APPRAISALS_SYSTEM_PROMPT),
            ("ec_memory",     _Scale2, JUDGE_EC_MEMORY_SYSTEM_PROMPT),
            ("ec_strategies", _Scale2, JUDGE_EC_STRATEGIES_SYSTEM_PROMPT),
            ("ec_triggers",   _Scale2, JUDGE_EC_TRIGGERS_SYSTEM_PROMPT),
        ]

        scores = {}
        rationales = []
        for field_name, schema, sys_prompt in dims:
            result = self._rate_one(schema, sys_prompt, user_prompt)
            if result is None:
                return None
            scores[field_name] = result.score
            rationales.append(f"{field_name}: {result.rationale}")

        return JudgeRating(
            **scores,
            rationale=" | ".join(rationales),
        )
