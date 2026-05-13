"""JudgeRunner — iterates over eval vignettes and rates each with a JudgeAgent."""

import csv
import logging
import time
from datetime import datetime
from pathlib import Path

from agents.base_agent import reset_run_tokens, set_context_subdir
from agents.judge_agent import JudgeAgent, JudgeRating
from simulation.factory import build_llm
from utils.text import strip_markdown

logger = logging.getLogger(__name__)

FIELDNAMES = [
    "timestamp", "judge_model", "vignette_id", "persona_id", "model", "condition",
    "clarity", "relevance", "importance",
    "g1_grounded", "g2_narrative", "g3_explicit", "g4_relevant",
    "dsm_a", "dsm_b", "dsm_c", "dsm_d", "dsm_e", "dsm_g",
    "ec_threat", "ec_appraisals", "ec_memory", "ec_strategies", "ec_triggers",
    "rationale",
]


class JudgeRunner:
    def __init__(self, model: str, temperature: float, input_path: Path,
                 output_dir: Path, blind: bool = False, delay: float = 0.5,
                 limit: int = None):
        self.model        = model
        self.temperature  = temperature
        self.input_path   = Path(input_path)
        self.output_dir   = Path(output_dir)
        self.blind        = blind
        self.delay        = delay
        self.limit        = limit
        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe_name         = model.replace("/", "-").replace(":", "-")
        self.output_path  = self.output_dir / f"llm_judge_{safe_name}.csv"

    def _load_done_ids(self) -> set:
        if not self.output_path.exists():
            return set()
        with open(self.output_path, encoding="utf-8") as f:
            return {row["vignette_id"] for row in csv.DictReader(f)}

    def _row_from_rating(self, rating: JudgeRating, vignette_id: str,
                         persona_id: str, model_src: str, condition: str) -> dict:
        return {
            "timestamp":          datetime.now().isoformat(),
            "judge_model":        self.model,
            "vignette_id":        vignette_id,
            "persona_id":         persona_id,
            "model":              "" if self.blind else model_src,
            "condition":          "" if self.blind else condition,
            "clarity":    rating.clarity,
            "relevance":  rating.relevance,
            "importance": rating.importance,
            "g1_grounded":        rating.g1_grounded,
            "g2_narrative":       rating.g2_narrative,
            "g3_explicit":        rating.g3_explicit,
            "g4_relevant":        rating.g4_relevant,
            "dsm_a":              rating.dsm_a,
            "dsm_b":              rating.dsm_b,
            "dsm_c":              rating.dsm_c,
            "dsm_d":              rating.dsm_d,
            "dsm_e":              rating.dsm_e,
            "dsm_g":              rating.dsm_g,
            "ec_threat":          rating.ec_threat,
            "ec_appraisals":      rating.ec_appraisals,
            "ec_memory":          rating.ec_memory,
            "ec_strategies":      rating.ec_strategies,
            "ec_triggers":        rating.ec_triggers,
            "rationale":          rating.rationale,
        }

    def run(self):
        llm   = build_llm(self.model, self.temperature)
        agent = JudgeAgent(name="LLMJudge", role="Judge", llm=llm)

        with open(self.input_path, encoding="utf-8") as f:
            vignettes = list(csv.DictReader(f))
        logger.info("Loaded %d vignettes from %s", len(vignettes), self.input_path)

        done_ids = self._load_done_ids()
        todo     = [v for v in vignettes if v["vignette_id"] not in done_ids]
        if self.limit:
            todo = todo[:self.limit]
        logger.info("Already done: %d  |  To rate: %d", len(done_ids), len(todo))

        if not todo:
            logger.info("Nothing to do.")
            return

        is_new = not self.output_path.exists()
        with open(self.output_path, "a", newline="", encoding="utf-8") as out_f:
            writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
            if is_new:
                writer.writeheader()

            for i, v in enumerate(todo, 1):
                vid       = v["vignette_id"]
                model_src = v.get("model", "")
                condition = v.get("condition", "")
                persona   = v.get("persona_id", "")

                set_context_subdir(f"judge_{vid}")
                reset_run_tokens()

                logger.info("[%d/%d] %s  %s/%s", i, len(todo), vid, model_src, condition)
                try:
                    rating = agent.rate(strip_markdown(v["vignette"]))
                    if rating is None:
                        logger.warning("  Parse failed for %s — skipping", vid)
                        continue
                    row = self._row_from_rating(rating, vid, persona, model_src, condition)
                    writer.writerow(row)
                    out_f.flush()
                except Exception as e:
                    logger.warning("  Failed: %s", e)

                if self.delay > 0 and i < len(todo):
                    time.sleep(self.delay)

        logger.info("Done. Results saved -> %s", self.output_path)
