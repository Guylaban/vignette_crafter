import logging
import re
from .base_agent import BaseAgent
from data.input.input import sample_formulation, sample_demographics
from configs.prompts import (VIGNETTE_CRAFTER_PROMPT_CONTEXT,
                             VIGNETTE_CRAFTER_RETRY_PROMPT,
                             VIGNETTE_CRAFTER_USER_PROMPT,
                             NO_FORMULATION_SR_SYSTEM_PROMPT,
                             NO_FORMULATION_SR_USER_PROMPT,
                             ZERO_SHOT_VIGNETTE_PROMPT)

logger = logging.getLogger(__name__)


class VignetteCrafterAgent(BaseAgent):
    """Writes a clinical vignette grounded in the patient's EMA formulation."""

    def __init__(self, name: str, role: str, llm,
                 use_demographics: bool = True, use_self_report: bool = True,
                 use_formulation: bool = True, demographics: dict = None,
                 self_report: dict = None, formulation: dict = None,
                 node_prob: float = 0.7, edge_prob: float = 0.5):
        context = formulation or sample_formulation(node_prob=node_prob, edge_prob=edge_prob)
        demo = demographics or sample_demographics()

        self._required_edges_str = "  (none)"

        if not use_formulation and (use_demographics or use_self_report):
            sr = self_report if self_report is not None else self._nodes_to_self_report(context["nodes"])
            prompt = NO_FORMULATION_SR_SYSTEM_PROMPT.format(
                demographics=self.fmt_demographics(demo) if use_demographics else "  (not provided)",
                self_report=self.fmt_self_report(sr)     if use_self_report  else "  (not provided)",
            )
            self._user_prompt = NO_FORMULATION_SR_USER_PROMPT
        elif not use_formulation:
            # no_context: no demographics, no self-report, no edges
            prompt = ZERO_SHOT_VIGNETTE_PROMPT
            self._user_prompt = "Write a clinical vignette for a patient with PTSD."
        elif use_demographics or use_self_report:
            required_edges = self._fmt_required_edges(context["edges"])
            active_nodes = self._fmt_active_nodes(context["nodes"])
            sr = self_report if self_report is not None else self._nodes_to_self_report(context["nodes"])
            self._required_edges_str = required_edges
            prompt = VIGNETTE_CRAFTER_PROMPT_CONTEXT
            self._user_prompt = VIGNETTE_CRAFTER_USER_PROMPT.format(
                demographics=self.fmt_demographics(demo) if use_demographics else "  (not provided)",
                self_report=self.fmt_self_report(sr) if use_self_report else "  (not provided)",
                active_nodes=active_nodes,
                required_edges=required_edges,
            )
        super().__init__(name, role, prompt, llm)

    _VIGNETTE_SEP = "---VIGNETTE---"

    _COMPONENT_SYNONYMS: dict[str, list[str]] = {
        "Triggers":             ["triggering stimuli", "triggers", "reminders", "cues"],
        "Negative Appraisals":  ["negative appraisals", "negative beliefs", "distorted beliefs", "appraisals"],
        "Memory":               ["intrusive memory", "traumatic memory", "trauma memory", "the memory"],
        "Threat":               ["sense of threat", "perceived threat", "feeling of danger", "threat"],
        "Maladaptive Strategies": ["maladaptive strategies", "safety behaviours", "maladaptive coping", "avoidance"],
    }

    def _extract_vignette(self, raw: str) -> str:
        if self._VIGNETTE_SEP in raw:
            return raw.split(self._VIGNETTE_SEP, 1)[1].strip()
        return raw.strip()

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

    def _source_component(self, sentence: str) -> str | None:
        """Return the first component mentioned in sentence (the A in A→B)."""
        s = sentence.lower()
        earliest, result = len(s), None
        for component, synonyms in self._COMPONENT_SYNONYMS.items():
            for syn in synonyms:
                pos = s.find(syn.lower())
                if 0 <= pos < earliest:
                    earliest, result = pos, component
        return result

    def _insert_near_source(self, vignette: str, new_sentence: str) -> str:
        """Insert new_sentence after the last vignette sentence that mentions the source component."""
        component = self._source_component(new_sentence)
        if component:
            synonyms = self._COMPONENT_SYNONYMS[component]
            sentences = re.split(r'(?<=[.!?])\s+', vignette)
            last_idx = next(
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

    def _apply_diff(self, vignette: str, diff_output: str) -> str:
        result = vignette

        insert_blocks = re.findall(
            r'<<<INSERT_AFTER>>>(.*?)<<<NEW_SENTENCE>>>(.*?)<<<END>>>',
            diff_output, re.DOTALL
        )
        for anchor, new_sentence in insert_blocks:
            anchor = anchor.strip()
            new_sentence = new_sentence.strip()
            if anchor in result:
                result = result.replace(anchor, anchor + " " + new_sentence, 1)
                logger.debug("[%s] inserted after: %.60s…", self.name, anchor)
            else:
                result = self._insert_near_source(result, new_sentence)
                logger.warning("[%s] INSERT_AFTER anchor not found — inserting near source component", self.name)

        if not insert_blocks:
            logger.warning("[%s] no valid patch blocks found — vignette unchanged", self.name)

        return result

    @staticmethod
    def _fmt_active_nodes(nodes: dict) -> str:
        return "\n".join(f"  - {n}" for n in nodes) or "  (none)"

    def _fmt_required_edges(self, edges: dict) -> str:
        required = [k for k, v in edges.items() if v.get("strength", 0) > 0]
        return "\n".join(f"  - {k[0]} → {k[1]}" for k in required) or "  (none)"

    @staticmethod
    def _nodes_to_self_report(nodes: dict) -> dict:
        """Convert get_aggregated_context nodes format to self_report format."""
        return {node: data.get("items", []) for node, data in nodes.items() if data.get("items")}
