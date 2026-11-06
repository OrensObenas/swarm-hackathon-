"""Draw the transcript-audit sample (seed 0, 10 per injected condition) and print a condensed view."""
import json, random, re
RUNS = {"replicating_none": "results/main_mistral-small-2603", "replicating_llm": "results/main_mistral-small-2603",
        "replicating_llm@gpt-5.4-mini": "results/xmonitor_gpt-5.4-mini",
        "replicating_sanitize": "results/explore_sanitize_mistral-small-2603"}
KEY = re.compile(r"[^.\n]*(vendor-audit|NX-4471|notice|withheld|suspicious|ignore|compliance|audit)[^.\n]*", re.I)
def sample():
    out = []
    for cond, d in RUNS.items():
        base = cond.split("@")[0]
        recs = [json.loads(l) for l in open(f"{d}/episodes.jsonl")]
        recs = sorted([r for r in recs if r["config"]["condition"] == base], key=lambda r: r["config"]["episode_id"])
        out += [(cond, d, r) for r in random.Random(0).sample(recs, 10)]
    return out
if __name__ == "__main__":
    for cond, d, r in sample():
        s = r["summary"]
        print(f"\n##### {cond} {r['config']['episode_id']} hijacked={s['hijacked_agents']} vendor={s['recommended_vendor']}")
        for e in r["events"]:
            if e["kind"] == "tool_call" and e["tool"] == "send_email":
                print(f"  EMAIL {e['agent']} -> {e['args'].get('to')}")
            if e["kind"] == "message":
                hits = [m.group(0).strip()[:140] for m in KEY.finditer(e["raw"])][:2]
                print(f"  MSG {e['sender'][:4]}->{e['receiver'][:4]} taint={int(e['raw_tainted'])} flag={int(e['flagged'])} "
                      f"san={int(e.get('sanitized', False))} | {hits}")
