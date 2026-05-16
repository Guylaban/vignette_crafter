"""JudgeRunner — iterates over eval vignettes and rates each with a JudgeAgent."""

import csv
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from agents.judge_agent import JudgeAgent, JudgeRating
from simulation.factory import build_llm
from utils.text import strip_markdown

logger = logging.getLogger(__name__)


class JudgeRunner:
    def __init__(self, model: str, temperature: float, input_path: Path,
                 output_dir: Path, blind: bool = False, delay: float = 0.0,
                 limit: int = None, workers: int = 10):
        self.model        = model
        self.temperature  = temperature
        self.input_path   = Path(input_path)
        self.output_dir   = Path(output_dir)
        self.blind        = blind
        self.delay        = delay
        self.limit        = limit
        self.workers      = workers
        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe_name         = model.replace("/", "-").replace(":", "-")
        self.output_path  = self.output_dir / f"llm_judge_{safe_name}.jsonl"

    def _load_done_ids(self) -> set:
        if not self.output_path.exists():
            return set()
        done = set()
        with open(self.output_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    done.add(json.loads(line)["vignette_id"])
        return done

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

    def _rate_one(self, v: dict, agent: JudgeAgent) -> dict | None:
        vid       = v["vignette_id"]
        model_src = v.get("model", "")
        condition = v.get("condition", "")
        persona   = v.get("persona_id", "")
        logger.info("  rating %s  %s/%s", vid, model_src, condition)
        try:
            rating = agent.rate(strip_markdown(v["vignette"]))
            if rating is None:
                logger.warning("  Parse failed for %s — skipping", vid)
                return None
            return self._row_from_rating(rating, vid, persona, model_src, condition)
        except Exception as e:
            logger.warning("  Failed %s: %s", vid, e)
            return None

    def _load_vignettes(self) -> list[dict]:
        if self.input_path.suffix == ".jsonl":
            with open(self.input_path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        with open(self.input_path, encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def run(self):
        vignettes = self._load_vignettes()
        logger.info("Loaded %d vignettes from %s", len(vignettes), self.input_path)

        done_ids = self._load_done_ids()
        todo     = [v for v in vignettes if v["vignette_id"] not in done_ids]
        if self.limit:
            todo = todo[:self.limit]
        logger.info("Already done: %d  |  To rate: %d", len(done_ids), len(todo))

        if not todo:
            logger.info("Nothing to do.")
            return

        write_lock = threading.Lock()

        def make_agent():
            llm = build_llm(self.model, self.temperature)
            return JudgeAgent(name="LLMJudge", role="Judge", llm=llm)

        completed = 0
        with open(self.output_path, "a", encoding="utf-8") as out_f:
            if self.workers <= 1:
                agent = make_agent()
                for i, v in enumerate(todo, 1):
                    logger.info("[%d/%d] %s  %s/%s", i, len(todo),
                                v["vignette_id"], v.get("model",""), v.get("condition",""))
                    row = self._rate_one(v, agent)
                    if row:
                        out_f.write(json.dumps(row) + "\n")
                        out_f.flush()
                    if self.delay > 0 and i < len(todo):
                        time.sleep(self.delay)
            else:
                with ThreadPoolExecutor(max_workers=self.workers) as pool:
                    futures = {pool.submit(self._rate_one, v, make_agent()): v for v in todo}
                    for future in as_completed(futures):
                        completed += 1
                        row = future.result()
                        if row:
                            with write_lock:
                                out_f.write(json.dumps(row) + "\n")
                                out_f.flush()
                        logger.info("  [%d/%d] done", completed, len(todo))

        logger.info("Done. Results saved -> %s", self.output_path)
