"""Graded edge-probe on the 150-vignette human sample (50 personas x 3 conditions).
Same judge (deepseek-v4-flash via DeepSeek API), same two-scale schema as the
30-vignette run. NEW output files; resumable; parallel workers.

Outputs:
  emnlp26/graded_edge_probe/graded_edge_probe_deepseek-v4-flash_150.jsonl
  emnlp26/graded_edge_probe/reasoning_deepseek-v4-flash_150.jsonl
  emnlp26/graded_edge_probe/graded_edge_probe_merged_150.csv
"""
import json, os, time, pathlib, csv, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Paths are configurable so the script runs outside the original machine.
# REPO defaults to this file's repository root; the study materials and the
# output directory default to their released locations.
REPO = pathlib.Path(os.environ.get("FORMA_REPO", pathlib.Path(__file__).resolve().parents[1]))
DATA = REPO / "data" / "edge_validation_150"
SAMPLE = pathlib.Path(os.environ.get("FORMA_SAMPLE_DIR", DATA / "study_materials"))
OUT = pathlib.Path(os.environ.get("FORMA_OUT_DIR", DATA / "raw_judge_output"))
OUT.mkdir(parents=True, exist_ok=True)
load_dotenv(REPO / ".env")

JUDGE = "deepseek-v4-pro"
client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

NODES = ["Triggers", "Negative Appraisals", "Memory", "Threat", "Maladaptive Strategies"]
EDGES = [f"{a} -> {b}" for a in NODES for b in NODES if a != b]

SYSTEM = """You are evaluating a PTSD case vignette for the presence and prominence of causal
connections between five Ehlers & Clark cognitive components: Triggers, Negative Appraisals,
Memory, Threat, and Maladaptive Strategies.

COMPONENT SYNONYMS (any synonym counts as the component appearing):
  Triggers              -> "triggers", "reminders", "cues", "triggering stimuli", "sensory cues"
  Negative Appraisals   -> "negative appraisals", "negative beliefs", "appraisals", "distorted beliefs", "catastrophic thoughts"
  Memory                -> "intrusive memory", "trauma memory", "traumatic memory", "the memory", "flashbacks", "sensory reliving"
  Threat                -> "sense of threat", "perceived threat", "threat", "feeling of danger", "hypervigilance", "feeling unsafe"
  Maladaptive Strategies-> "maladaptive strategies", "avoidance", "safety behaviours", "coping", "checking", "substance use", "thought suppression"

For each of the 20 ordered directed pairs (A -> B) of distinct components, give TWO ratings:

1. "present" (0 or 1) - STRICT BINARY STANDARD. An edge A -> B is present (1) iff, within the
   same paragraph: (i) both A and B (or synonyms / clear phenomenological description) appear;
   AND (ii) the paragraph conveys that A influences / drives / leads to B, through direct causal
   language, sequential structure, or connecting phrases ("because of", "this meant", "so",
   "which led", "as a result", "consequently", "in turn", "every time X, Y"). Mere co-occurrence
   is NOT enough. Direction matters: A -> B is not B -> A.

2. "strength" (RAW continuous score, 0.0 to 1.0) - HOW STRONGLY the text conveys A driving B.
   This is a raw, free continuous estimate. Use the WHOLE range and any value you like.
   Endpoints only:
     0.0 = no causal link from A to B in the text at all
     1.0 = the strongest, most explicit and emphatic causal link possible
   Everything between is a smooth continuum - the clearer, more direct, and more emphatic the
   causal connection, the higher the value. Do NOT snap to preset levels; give your best
   continuous estimate (two decimals fine). strength may be > 0 even when present = 0 if there
   is any trace of the link; strength = 0.0 only when there is no trace at all.

Return STRICT JSON, no markdown fences, with this shape:
{"edges": {"Triggers -> Negative Appraisals": {"present": 0, "strength": 0.0}, ... all 20 keys ...},
 "rationale": "one short sentence"}"""

USER_TMPL = """Evaluate the following vignette. Rate all 20 directed edges (present + strength).

VIGNETTE
{vignette}"""

def load_done(path):
    if not path.exists(): return set()
    return {json.loads(l)["vignette_id"] for l in path.read_text(encoding="utf-8").splitlines() if l.strip()}

out_path = OUT / f"graded_edge_probe_{JUDGE}_150_raw.jsonl"
reason_path = OUT / f"reasoning_{JUDGE}_150_raw.jsonl"
write_lock = threading.Lock()

def probe_one(row):
    vid = row["vignette_id"]
    vignette = (SAMPLE / "vignettes" / f"{vid}.txt").read_text(encoding="utf-8")
    resp = client.chat.completions.create(
        model=JUDGE, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": USER_TMPL.format(vignette=vignette.strip())}])
    msg = resp.choices[0].message
    raw = msg.content or ""
    reasoning = getattr(msg, "reasoning_content", None)
    rec = {"timestamp": datetime.now().isoformat(), "judge_model": JUDGE, "api_model": JUDGE,
           "vignette_id": vid, "persona_id": row["persona_id"],
           "condition": row["condition"], "model": row["model"],
           "raw_response": raw,
           "usage": {"prompt": resp.usage.prompt_tokens, "completion": resp.usage.completion_tokens}}
    try:
        parsed = json.loads(raw)
        edges = parsed.get("edges", {})
        rec["rationale"] = parsed.get("rationale", "")
        for e in EDGES:
            v = edges.get(e, {})
            rec[f"present::{e}"] = int(v.get("present", 0))
            rec[f"strength::{e}"] = float(v.get("strength", 0.0))
        rec["parse_error"] = False
    except Exception as ex:
        rec["parse_error"] = True
        rec["parse_exception"] = str(ex)
    with write_lock, open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if reasoning:
        with write_lock, open(reason_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"vignette_id": vid, "judge_model": JUDGE,
                                "reasoning_content": reasoning}, ensure_ascii=False) + "\n")
    return vid, rec["parse_error"]

def main():
    key = list(csv.DictReader(open(SAMPLE / "submission_key.csv", encoding="utf-8")))
    done = load_done(out_path)
    pending = [r for r in key if r["vignette_id"] not in done]
    print(f"total={len(key)} done={len(done)} pending={len(pending)}")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(probe_one, r): r for r in pending}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                vid, err = fut.result()
                print(f"[{i}/{len(pending)}] {vid} ok={not err}")
            except Exception as e:
                print(f"[{i}/{len(pending)}] EXCEPTION {futs[fut]['vignette_id']}: {e}")
    print(f"probe done in {time.time()-t0:.0f}s")

    # merged clean CSV
    personas = {}
    # Persona specifications, one JSON per persona named persona_<id>.json.
    PDIR = pathlib.Path(os.environ["FORMA_PERSONA_DIR"])
    for r in key:
        pid = r["persona_id"]
        if pid not in personas:
            personas[pid] = json.load(open(PDIR / f"persona_{pid}.json", encoding="utf-8"))
    recs = {json.loads(l)["vignette_id"]: json.loads(l)
            for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip()}
    merged = OUT / "graded_edge_probe_merged_150_raw_dspro.csv"
    with open(merged, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["vignette_id", "persona_id", "condition", "generation_model", "judge_model",
                    "edge", "llm_present", "llm_strength", "spec_weight", "spec_edge_active"])
        for row in key:
            vid = row["vignette_id"]; rec = recs.get(vid)
            if rec is None or rec.get("parse_error"): continue
            p = personas[row["persona_id"]]
            agg = p.get("agg_edges", {}); active = set(p.get("active_nodes", []))
            for e in EDGES:
                a, b = e.split(" -> ")
                wgt = agg.get(f"{a} -- {b}", 0.0)
                edge_active = (a in active and b in active and wgt > 0)
                w.writerow([vid, row["persona_id"], row["condition"], row["model"], JUDGE,
                            e, rec[f"present::{e}"], rec[f"strength::{e}"],
                            f"{wgt:.4f}", int(edge_active)])
    print(f"merged CSV -> {merged}")

if __name__ == "__main__":
    main()
