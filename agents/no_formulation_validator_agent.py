"""Validates no-formulation vignettes: checks demographics + self-report item coverage."""

import logging
from typing import Literal
from pydantic import BaseModel
from .base_agent import BaseAgent
from configs.prompts import (
    VALIDATOR_NO_FORMULATION_SYSTEM_PROMPT,
    VALIDATOR_NO_FORMULATION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class NoFormulationValidationResult(BaseModel):
    verdict:               Literal["PASS", "FAIL"]
    missing_items:         list[str] = []
    missing_explanations:  list[str] = []


class NoFormulationValidatorAgent(BaseAgent):
    def __init__(self, name: str, role: str, llm):
        super().__init__(name, role, "", llm)

    def setup_agent(self):
        return None

    def validate(self, vignette: str, demographics: dict, self_report: dict) -> dict:
        user_prompt = VALIDATOR_NO_FORMULATION_USER_PROMPT.format(
            demographics=self.fmt_demographics(demographics),
            self_report=self.fmt_self_report(self_report),
            vignette=vignette,
        )
        result: NoFormulationValidationResult = self._invoke_structured(
            NoFormulationValidationResult,
            VALIDATOR_NO_FORMULATION_SYSTEM_PROMPT,
            user_prompt,
        )
        if result is None:
            logger.warning("[%s] no_formulation validation parsing failed — defaulting to FAIL", self.name)
            return {"passed": False, "missing": [], "feedback": "Validation could not be parsed. Please rewrite the vignette."}

        missing = [
            {"item": item, "explanation": ex}
            for item, ex in zip(result.missing_items, result.missing_explanations)
        ]
        passed   = len(missing) == 0
        feedback = self._build_feedback(missing)
        logger.info("[%s] %s", self.name, "PASS" if passed else f"FAIL — {len(missing)} missing item(s)")
        return {"passed": passed, "missing": missing, "feedback": feedback}

    @staticmethod
    def _build_feedback(missing: list[dict]) -> str | None:
        if not missing:
            return None
        lines = ["MISSING FROM VIGNETTE:"]
        for m in missing:
            lines.append(f"- {m['item']}: {m['explanation']}")
        return "\n".join(lines)

    def validate_with_retry(self, initial_vignette: str, demographics: dict, self_report: dict,
                            retry_fn, max_retries: int, label: str) -> tuple[str, list]:
        vignette = initial_vignette
        attempts = []

        for attempt in range(max_retries + 1):
            result = self.validate(vignette, demographics, self_report)
            attempts.append({
                "vignette":        vignette,
                "passed":          result["passed"],
                "missing":         result["missing"],
                "missing_count":   len(result["missing"]),
                "feedback":        result["feedback"],
            })

            if result["passed"]:
                logger.info("[%s] PASS on attempt %d", label, attempt + 1)
                return vignette, attempts

            logger.warning("[%s] FAIL on attempt %d", label, attempt + 1)
            if attempt < max_retries:
                vignette = retry_fn(result["feedback"])

        logger.warning("[%s] max retries reached — using last vignette", label)
        return vignette, attempts
