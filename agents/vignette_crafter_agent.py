import logging
import re
from .base_agent import BaseAgent
from data.input.input import sample_formulation, sample_demographics
from configs.prompts import (VIGNETTE_CRAFTER_PROMPT_CONTEXT,
                             VIGNETTE_CRAFTER_RETRY_PROMPT,
                             VIGNETTE_CRAFTER_NO_FORMULATION_RETRY_PROMPT,
                             VIGNETTE_CRAFTER_USER_PROMPT,
                             NO_FORMULATION_SR_SYSTEM_PROMPT,
                             NO_FORMULATION_SR_USER_PROMPT)
from configs.formulation_config import COMPONENT_SYNONYMS

logger = logging.getLogger(__name__)


class VignetteCrafterAgent(BaseAgent):
    """Writes a clinical vignette grounded in the patient's EMA formulation."""

    _VIGNETTE_SEP = "---VIGNETTE---"

    # ── Construction ──────────────────────────────────────────────────────────

    def __init__(self, name: str, role: str, llm,
                 use_demographics: bool = True, use_self_report: bool = True,
                 use_formulation: bool = True, demographics: dict = None,
                 self_report: dict = None, formulation: dict = None,
                 node_prob: float = 0.7, edge_prob: float = 0.5):
        context = formulation or sample_formulation(node_prob=node_prob, edge_prob=edge_prob)
        demo    = demographics or sample_demographics()
        prompt, user_prompt = self._build_prompts(
            context, demo, self_report, use_demographics, use_self_report, use_formulation
        )
        self._user_prompt = user_prompt
        super().__init__(name, role, prompt, llm)

    def _build_prompts(self, context, demo, self_report,
                       use_demographics, use_self_report, use_formulation) -> tuple[str, str]:
        if not use_formulation and (use_demographics or use_self_report):
            sr = self_report or self._nodes_to_self_report(context["nodes"])
            user_prompt = NO_FORMULATION_SR_USER_PROMPT.format(
                demographics=self.fmt_demographics(demo) if use_demographics else "  (not provided)",
                self_report=self.fmt_self_report(sr)     if use_self_report  else "  (not provided)",
            )
            return NO_FORMULATION_SR_SYSTEM_PROMPT, user_prompt

        if use_demographics or use_self_report:
            sr = self_report or self._nodes_to_self_report(context["nodes"])
            user_prompt = VIGNETTE_CRAFTER_USER_PROMPT.format(
                demographics=self.fmt_demographics(demo) if use_demographics else "  (not provided)",
                self_report=self.fmt_self_report(sr)     if use_self_report  else "  (not provided)",
                active_nodes=self._fmt_active_nodes(context["nodes"]),
                required_edges=self._fmt_required_edges(context["edges"]),
            )
            return VIGNETTE_CRAFTER_PROMPT_CONTEXT, user_prompt

        return VIGNETTE_CRAFTER_PROMPT_CONTEXT, "Write a clinical vignette for a patient with PTSD."

    # ── Public API ────────────────────────────────────────────────────────────

    def create_vignette(self) -> str:
        raw = self.respond(self._user_prompt)
        self.vignette = self._extract_vignette(raw)
        logger.info("[%s] vignette written", self.name)
        return self.vignette

    def create_vignette_with_feedback(self, feedback: str) -> str:
        retry_prompt = VIGNETTE_CRAFTER_RETRY_PROMPT.format(
            feedback=feedback,
            previous_vignette=self.vignette,
        )
        self.reset_memory()
        raw = self.respond(retry_prompt)
        self.vignette = self._apply_diff(self.vignette, raw)
        logger.info("[%s] vignette revised after feedback", self.name)
        return self.vignette

    def create_vignette_with_no_formulation_feedback(self, feedback: str) -> str:
        retry_prompt = VIGNETTE_CRAFTER_NO_FORMULATION_RETRY_PROMPT.format(
            feedback=feedback,
            previous_vignette=self.vignette,
        )
        self.reset_memory()
        raw = self.respond(retry_prompt)
        self.vignette = self._extract_vignette(raw)
        logger.info("[%s] vignette rewritten after no_formulation feedback", self.name)
        return self.vignette

    # ── Vignette extraction ───────────────────────────────────────────────────

    def _extract_vignette(self, raw: str) -> str:
        if self._VIGNETTE_SEP in raw:
            return raw.split(self._VIGNETTE_SEP, 1)[1].strip()
        return raw.strip()

    # ── Diff application ──────────────────────────────────────────────────────

    def _apply_diff(self, vignette: str, diff_output: str) -> str:
        insert_blocks = re.findall(
            r'<<<INSERT_AFTER>>>(.*?)<<<NEW_SENTENCE>>>(.*?)<<<END>>>',
            diff_output, re.DOTALL
        )
        if not insert_blocks:
            logger.warning("[%s] no valid patch blocks found — vignette unchanged", self.name)
            return vignette

        result = vignette
        for anchor, new_sentence in insert_blocks:
            anchor, new_sentence = anchor.strip(), new_sentence.strip()
            if anchor in result:
                result = result.replace(anchor, anchor + " " + new_sentence, 1)
                logger.debug("[%s] inserted after: %.60s…", self.name, anchor)
            else:
                result = self._insert_near_source(result, new_sentence)
                logger.warning("[%s] INSERT_AFTER anchor not found — inserting near source component", self.name)
        return result

    def _insert_near_source(self, vignette: str, new_sentence: str) -> str:
        component = self._source_component(new_sentence)
        if component:
            synonyms  = COMPONENT_SYNONYMS[component]
            sentences = re.split(r'(?<=[.!?])\s+', vignette)
            last_idx  = next(
                (i for i in reversed(range(len(sentences)))
                 if any(syn.lower() in sentences[i].lower() for syn in synonyms)),
                -1
            )
            if last_idx != -1:
                sentences.insert(last_idx + 1, new_sentence)
                logger.debug("[%s] fallback inserted after sentence mentioning '%s'", self.name, component)
                return " ".join(sentences)
        logger.warning("[%s] fallback: source component not found — appending to end", self.name)
        return vignette.rstrip() + " " + new_sentence

    def _source_component(self, sentence: str) -> str | None:
        s = sentence.lower()
        earliest, result = len(s), None
        for component, synonyms in COMPONENT_SYNONYMS.items():
            for syn in synonyms:
                pos = s.find(syn.lower())
                if 0 <= pos < earliest:
                    earliest, result = pos, component
        return result

    # ── Formatting helpers ────────────────────────────────────────────────────

    @staticmethod
    def _fmt_active_nodes(nodes: dict) -> str:
        return "\n".join(f"  - {n}" for n in nodes) or "  (none)"

    @staticmethod
    def _fmt_required_edges(edges: dict) -> str:
        required = [k for k, v in edges.items() if v.get("strength", 0) > 0]
        return "\n".join(f"  - {k[0]} → {k[1]}" for k in required) or "  (none)"

    @staticmethod
    def _nodes_to_self_report(nodes: dict) -> dict:
        return {node: data.get("items", []) for node, data in nodes.items() if data.get("items")}
