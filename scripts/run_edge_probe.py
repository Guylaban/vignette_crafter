"""run_edge_probe.py — independent per-edge presence probe over eval_vignettes_330.csv.

Usage:
    python scripts/run_edge_probe.py deepseek-v4-flash
    python scripts/run_edge_probe.py claude-opus-4-5 --workers 5
    python scripts/run_edge_probe.py deepseek-v4-flash --limit 10  # smoke test

Resumable: results append to data/edge_probe/edge_probe_<judge>.jsonl, and
finished vignette_ids are skipped on re-run.

Output schema (one JSON line per vignette): vignette_id, persona_id, model, condition,
plus a column per directed edge like 'Triggers__to__Memory' with a 0/1 value, plus
the judge's rationale string.
"""
import argparse, csv, json, logging, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

from simulation.factory import build_llm
from agents.edge_probe_agent import EdgeProbeAgent, DIRECTED_EDGES, _field

ROOT = Path(__file__).parent.parent

def _load_done(out_path):
    if not out_path.exists(): return set()
    done = set()
    for line in open(out_path, encoding="utf-8"):
        line = line.strip()
        if line: done.add(json.loads(line)["vignette_id"])
    return done

def _row(v, parsed, judge_model):
    rec = {"timestamp": datetime.now().isoformat(),
           "judge_model": judge_model,
           "vignette_id": v["vignette_id"],
           "persona_id": v.get("persona_id", ""),
           "model": v.get("model", ""),
           "condition": v.get("condition", "")}
    if parsed is None:
        rec["parse_error"] = True
        return rec
    pdict = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
    for (a, b) in DIRECTED_EDGES:
        rec[_field(a, b)] = int(pdict.get(_field(a, b), 0))
    rec["rationale"] = pdict.get("rationale", "")
    return rec

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--input", default=str(ROOT/"data/eval_vignettes_330.csv"))
    parser.add_argument("--output_dir", default=str(ROOT/"data/edge_probe"))
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    out_dir = Path(args.output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    safe = args.model.replace("/","-").replace(":","-")
    out_path = out_dir / f"edge_probe_{safe}.jsonl"
    write_lock = threading.Lock()

    vignettes = list(csv.DictReader(open(args.input, encoding="utf-8-sig")))
    if args.limit: vignettes = vignettes[:args.limit]
    done = _load_done(out_path)
    pending = [v for v in vignettes if v["vignette_id"] not in done]
    logger.info(f"Total vignettes: {len(vignettes)}, done: {len(done)}, pending: {len(pending)}")
    if not pending: logger.info("Nothing to do."); return

    llm = build_llm(args.model, args.temperature)
    agent_local = threading.local()
    def get_agent():
        if not hasattr(agent_local, "agent"):
            agent_local.agent = EdgeProbeAgent(name=f"EdgeProbe_{args.model}", role="EdgeProbe", llm=llm)
        return agent_local.agent

    def process(v):
        try:
            parsed = get_agent().probe(v["vignette"])
            return _row(v, parsed, args.model)
        except Exception as e:
            logger.exception(f"failed on {v['vignette_id']}")
            return {"timestamp": datetime.now().isoformat(),
                    "judge_model": args.model,
                    "vignette_id": v["vignette_id"],
                    "persona_id": v.get("persona_id",""),
                    "model": v.get("model",""),
                    "condition": v.get("condition",""),
                    "parse_error": True, "exception": str(e)}

    start = time.time(); succeeded = 0; failed = 0
    if args.workers <= 1:
        for i, v in enumerate(pending, 1):
            rec = process(v)
            with write_lock, open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            if rec.get("parse_error"): failed += 1
            else: succeeded += 1
            if args.delay: time.sleep(args.delay)
            logger.info(f"[{i}/{len(pending)}] {v['vignette_id']} -> ok={not rec.get('parse_error')}")
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(process, v): v for v in pending}
            for i, fut in enumerate(as_completed(futures), 1):
                v = futures[fut]
                rec = fut.result()
                with write_lock, open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec) + "\n")
                if rec.get("parse_error"): failed += 1
                else: succeeded += 1
                logger.info(f"[{i}/{len(pending)}] {v['vignette_id']} -> ok={not rec.get('parse_error')}")

    logger.info(f"DONE in {time.time()-start:.0f}s: succeeded={succeeded}, failed={failed}, wrote {out_path}")

if __name__ == "__main__":
    main()
