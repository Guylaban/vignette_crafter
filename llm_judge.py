"""
llm_judge.py — LLM-as-a-judge evaluation of vignettes.

Rates every vignette in data/eval_vignettes.csv on the same dimensions
used by human raters in the rating app:
  - Content Validity Index (CVI): clarity, relevance, representativeness (1-3)
  - Construction quality (Evans guidelines): g1–g4 (1-3)
  - DSM-5 criterion checklist: A, B, C, D, E, G  (0/1)
  - Ehlers & Clark component checklist: 5 components (0/1)

Output columns match the human-rater CSV so both can be analysed together.

Usage:
    python llm_judge.py --model gpt-5.4
    python llm_judge.py --model claude-sonnet-4-6 --temperature 0
    python llm_judge.py --model gpt-5.4 --limit 10          # quick test
    python llm_judge.py --model gpt-5.4 --blind             # hide model/condition
"""

import argparse
import csv
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)

INPUT_PATH  = Path("data/eval_vignettes.csv")
OUTPUT_DIR  = Path("data/llm_judge")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    ec_threat:     Literal[0, 1] = Field(description="Sense of current threat: the person feels the trauma is still happening or still dangerous now (not just a bad memory). 1=present, 0=absent")
    ec_appraisals: Literal[0, 1] = Field(description="Negative appraisals: catastrophic or overly negative interpretation of the trauma or its aftermath (e.g. self-blame, permanent change). 1=present, 0=absent")
    ec_memory:     Literal[0, 1] = Field(description="Nature of trauma memory: fragmented, disorganised, feels like happening now rather than in the past. 1=present, 0=absent")
    ec_strategies: Literal[0, 1] = Field(description="Maladaptive coping strategies that maintain PTSD (avoidance, thought suppression, rumination, substance use, safety behaviours). 1=present, 0=absent")
    ec_triggers:   Literal[0, 1] = Field(description="Triggers for re-experiencing: specific internal or external cues that activate trauma memory or distress. 1=present, 0=absent")

    rationale: str = Field(description="2-3 sentence summary of your key observations about this vignette — what it does well and any notable weaknesses.")


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
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

USER_PROMPT_TEMPLATE = """
Rate the following clinical vignette:

---
{vignette}
---

Provide your ratings in the required structured format.
"""


# ── Core rating function ──────────────────────────────────────────────────────

def rate_vignette(vignette_text: str, chain) -> JudgeRating:
    msg = USER_PROMPT_TEMPLATE.format(vignette=vignette_text.strip())
    return chain.invoke(msg)


# ── CSV helpers ───────────────────────────────────────────────────────────────

FIELDNAMES = [
    "timestamp", "judge_model", "vignette_id", "persona_id", "model", "condition",
    # CVI
    "clarity", "relevance", "representativeness",
    # Construction
    "g1_grounded", "g2_narrative", "g3_explicit", "g4_relevant",
    # DSM-5
    "dsm_a", "dsm_b", "dsm_c", "dsm_d", "dsm_e", "dsm_g", "dsm_valid",
    # E&C
    "ec_threat", "ec_appraisals", "ec_memory", "ec_strategies", "ec_triggers",
    # Rationale
    "rationale",
]


def load_done_ids(output_path: Path) -> set:
    if not output_path.exists():
        return set()
    with open(output_path, encoding="utf-8") as f:
        return {row["vignette_id"] for row in csv.DictReader(f)}


def row_from_rating(rating: JudgeRating, vignette_id: str,
                    persona_id, model: str, condition: str,
                    judge_model: str) -> dict:
    dsm_valid = int(all([
        rating.dsm_a, rating.dsm_b, rating.dsm_c,
        rating.dsm_d, rating.dsm_e, rating.dsm_g,
    ]))
    return {
        "timestamp":          datetime.now().isoformat(),
        "judge_model":        judge_model,
        "vignette_id":        vignette_id,
        "persona_id":         persona_id,
        "model":              model,
        "condition":          condition,
        "clarity":            rating.clarity,
        "relevance":          rating.relevance,
        "representativeness": rating.representativeness,
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
        "dsm_valid":          dsm_valid,
        "ec_threat":          rating.ec_threat,
        "ec_appraisals":      rating.ec_appraisals,
        "ec_memory":          rating.ec_memory,
        "ec_strategies":      rating.ec_strategies,
        "ec_triggers":        rating.ec_triggers,
        "rationale":          rating.rationale,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LLM-as-a-judge vignette evaluation")
    parser.add_argument("--model",       default="gpt-5.4",    help="Judge model name")
    parser.add_argument("--temperature", type=float, default=0, help="Sampling temperature (default 0 for determinism)")
    parser.add_argument("--input",       default=str(INPUT_PATH), help="Input CSV path")
    parser.add_argument("--limit",       type=int,   default=None, help="Stop after N vignettes (for testing)")
    parser.add_argument("--blind",       action="store_true",  help="Pass only vignette text, hide model/condition in output")
    parser.add_argument("--delay",       type=float, default=0.5, help="Seconds to wait between API calls")
    args = parser.parse_args()

    # Build LLM + structured output chain
    from simulation.factory import build_llm
    llm   = build_llm(args.model, temperature=args.temperature)
    chain = llm.with_structured_output(JudgeRating)

    # Output path: one file per judge model
    safe_name   = args.model.replace("/", "-").replace(":", "-")
    output_path = OUTPUT_DIR / f"llm_judge_{safe_name}.csv"

    # Load vignettes
    with open(args.input, encoding="utf-8") as f:
        vignettes = list(csv.DictReader(f))
    log.info(f"Loaded {len(vignettes)} vignettes from {args.input}")

    # Resume: skip already rated
    done_ids = load_done_ids(output_path)
    todo     = [v for v in vignettes if v["vignette_id"] not in done_ids]
    if args.limit:
        todo = todo[:args.limit]
    log.info(f"Already done: {len(done_ids)}  |  To rate: {len(todo)}")

    if not todo:
        log.info("Nothing to do.")
        return

    # Open output CSV (append mode)
    is_new = not output_path.exists()
    with open(output_path, "a", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()

        for i, v in enumerate(todo, 1):
            vid       = v["vignette_id"]
            model_src = v.get("model", "")
            condition = v.get("condition", "")
            persona   = v.get("persona_id", "")

            log.info(f"[{i}/{len(todo)}] {vid}  {model_src}/{condition}")
            try:
                rating = rate_vignette(v["vignette"], chain)
                row    = row_from_rating(
                    rating, vid, persona,
                    "" if args.blind else model_src,
                    "" if args.blind else condition,
                    args.model,
                )
                writer.writerow(row)
                out_f.flush()
            except Exception as e:
                log.warning(f"  Failed: {e}")

            if args.delay > 0 and i < len(todo):
                time.sleep(args.delay)

    log.info(f"Done. Results saved -> {output_path}")


if __name__ == "__main__":
    main()
