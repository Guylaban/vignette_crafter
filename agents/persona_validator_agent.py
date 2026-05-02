"""Validates persona profiles for clinical plausibility in two stages:
1. Demographics-only consistency (before self-report selection)
2. Self-report alignment with demographics and trauma type (after selection)
"""

import logging
from typing import Literal
from pydantic import BaseModel
from .base_agent import BaseAgent
from configs.prompts import (
    PERSONA_VALIDATOR_DEMOGRAPHICS_SYSTEM_PROMPT,
    PERSONA_VALIDATOR_DEMOGRAPHICS_USER_PROMPT,
    PERSONA_VALIDATOR_SELFREPORT_SYSTEM_PROMPT,
    PERSONA_VALIDATOR_SELFREPORT_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class DemographicsValidationResult(BaseModel):
    verdict:              Literal["PASS", "FAIL"]
    issue_fields:         list[str] = []  # e.g. ["age", "relationship_status"]
    issue_explanations:   list[str] = []  # parallel to issue_fields


class SelfReportValidationResult(BaseModel):
    verdict:              Literal["PASS", "FAIL"]
    issue_components:     list[str] = []  # node names e.g. ["Triggers"]
    issue_items:          list[str] = []  # item keys, parallel to issue_components
    issue_explanations:   list[str] = []  # parallel to issue_components


class PersonaValidatorAgent(BaseAgent):
    def __init__(self, name: str, role: str, llm):
        super().__init__(name, role, "", llm)

    def setup_agent(self):
        return None

    def _run_validation(self, system_prompt: str, user_prompt: str, schema):
        """Invoke structured validation and log the response. Returns parsed result or None."""
        self.system_prompt = system_prompt
        return self._invoke_structured(schema, system_prompt, user_prompt)

    def validate_demographics(self, demographics: dict) -> dict:
        """Check internal consistency of demographics (age/relationship/trauma type).
        Returns {"passed": bool, "issues": [{"field": str, "explanation": str}], "problematic_fields": [str]}.
        """
        user_prompt = PERSONA_VALIDATOR_DEMOGRAPHICS_USER_PROMPT.format(
            demographics=self.fmt_demographics(demographics),
        )
        result: DemographicsValidationResult = self._run_validation(
            PERSONA_VALIDATOR_DEMOGRAPHICS_SYSTEM_PROMPT, user_prompt, DemographicsValidationResult
        )
        if result is None:
            logger.warning("[%s] demographics validation parsing failed — defaulting to PASS", self.name)
            return {"passed": True, "issues": [], "problematic_fields": []}

        passed = result.verdict == "PASS"
        issues = [{"field": f, "explanation": e}
                  for f, e in zip(result.issue_fields, result.issue_explanations)]
        problematic_fields = list(result.issue_fields)
        logger.info("[%s] demographics validation: %s — %s", self.name, result.verdict,
                    ", ".join(f"{i['field']}: {i['explanation']}" for i in issues) or "no issues")
        return {"passed": passed, "issues": issues, "problematic_fields": problematic_fields}

    def validate_self_report(self, demographics: dict, agg_edges: dict, self_report: dict) -> dict:
        """Check that self-report items are coherent with demographics, cognitive model, and trauma type.
        Returns {"passed": bool, "issues": [...], "problematic_items": {node: [bad_keys]}}.
        """
        active  = "\n".join(f"  - {p} → {c} (strength: {w:.2f})"
                            for (p, c), w in agg_edges.items() if w > 0)
        inactive = "\n".join(f"  - {p} → {c}"
                             for (p, c), w in agg_edges.items() if w == 0)
        cognitive_model_str = (
            f"Active edges:\n{active or '  (none)'}\n\n"
            f"Inactive edges:\n{inactive or '  (none)'}"
        )
        user_prompt = PERSONA_VALIDATOR_SELFREPORT_USER_PROMPT.format(
            demographics=self.fmt_demographics(demographics),
            cognitive_model=cognitive_model_str,
            self_report=self.fmt_self_report(self_report),
        )
        result: SelfReportValidationResult = self._run_validation(
            PERSONA_VALIDATOR_SELFREPORT_SYSTEM_PROMPT, user_prompt, SelfReportValidationResult
        )
        if result is None:
            logger.warning("[%s] self-report validation parsing failed — defaulting to PASS", self.name)
            return {"passed": True, "issues": [], "problematic_items": {}}

        passed = result.verdict == "PASS"
        issues = [{"component": c, "item": it, "explanation": e}
                  for c, it, e in zip(result.issue_components, result.issue_items, result.issue_explanations)]
        # Normalize: LLM sometimes returns "ComponentName: ItemKey: value" — extract just the key
        problematic_items: dict[str, list[str]] = {}
        for c, it in zip(result.issue_components, result.issue_items):
            # Strip component prefix if LLM included it (e.g. "Memory: Verbal Access: ...")
            if it.startswith(c + ":"):
                it = it[len(c) + 1:].strip()
            key = it.split(":")[0].strip()
            problematic_items.setdefault(c, []).append(key)
        logger.info("[%s] self-report validation: %s — %s", self.name, result.verdict,
                    ", ".join(f"{i['component']}/{i['item']}: {i['explanation']}" for i in issues) or "no issues")
        return {"passed": passed, "issues": issues, "problematic_items": problematic_items}

