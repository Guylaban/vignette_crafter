import logging
from .base_agent import BaseAgent, _count
from configs.prompts import (
    ZERO_SHOT_DEMOGRAPHICS_SYSTEM_PROMPT,
    ZERO_SHOT_DEMOGRAPHICS_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class ZeroShotVignetteAgent(BaseAgent):
    """Generates a vignette from demographics only (zero-shot baseline)."""

    def __init__(self, name: str, role: str, llm):
        super().__init__(name, role, system_prompt=ZERO_SHOT_DEMOGRAPHICS_SYSTEM_PROMPT, llm=llm)

    def create_vignette_from_demographics(self, demographics: str) -> str:
        user_prompt = ZERO_SHOT_DEMOGRAPHICS_USER_PROMPT.format(demographics=demographics)
        response = self.llm.invoke([
            {"role": "system", "content": ZERO_SHOT_DEMOGRAPHICS_SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ])
        _count(response)
        vignette = response.content
        self.log_response(user_prompt, vignette)
        logger.info("[%s] zero-shot demographics vignette written", self.name)
        return vignette
