"""Write full, human-readable transcripts of randomly drawn episodes for the author's check.

For each key condition, draws (seed 1) up to 2 task successes and 2 failures, plus every
attack, capped at 2. Output: docs/verification/<batch>__<condition>__<episode>.md + index.md."""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from analyze import renormalize  # noqa: E402

KEY = [("main_mistral-small-2603", "replicating_none"), ("main_mistral-small-2603", "replicating_llm"),
       ("replication_mistral-small-2603", "replicating_sanitize"), ("model_gpt-5.4-mini", "replicating_llm"),
       ("adversarial_mistral-small-2603", "sanitizer_bypass_sanitize"),
       ("recovery_mistral-small-2603", "replicating_blockretry"),
       ("recovery_mistral-small-2603", "replicating_blockabstain")]
OUT = os.path.join(ROOT, "docs", "verification")


def render(r):
    s = r["summary"]
    L = [f"# {r['config']['episode_id']} ({r['config']['condition']})", "",
         f"- model: {r['config'].get('model')}; monitor model: {r['config'].get('monitor_model')}; seed: {r['config'].get('seed')}",
         f"- **attack**: {s['attack_success']} (hijacked: {s['hijacked_agents']}); **task**: {s['task_success']} "
         f"(recommended vendor: {s['recommended_vendor']})", "", "## Events", ""]
    for e in r["events"]:
        if e["kind"] == "llm_call":
            L += [f"### LLM call: {e['agent']} (step {e.get('step', '-')})", "```", e["text"], "```"]
        elif e["kind"] == "tool_call":
            L += [f"**TOOL** `{e['tool']}` by {e['agent']}, args `{json.dumps(e['args'])}`", "```", str(e["result"]), "```"]
        elif e["kind"] == "message":
            L += [f"**MESSAGE {e['sender']} → {e['receiver']}**: tainted={e['raw_tainted']}, flagged={e['flagged']}, "
                  f"sanitized={e.get('sanitized', False)}, retried={e.get('retried', False)}; monitor reason: {e['reason']}",
                  "Delivered text:", "```", e["delivered"], "```"]
        elif e["kind"] in ("retry_request", "input_filter"):
            L += [f"**{e['kind'].upper()}**: `{json.dumps({k: v for k, v in e.items() if k not in ('t', 'kind')})[:600]}`"]
    L += ["", "## Outbox", "```", json.dumps(s["outbox"], indent=1), "```"]
    return "\n".join(L)


def main():
    os.makedirs(OUT, exist_ok=True)
    index = ["# Verification sample (seed 1)", "", "Read these against the claims in the report. Each file is a complete episode.",
             "", "| batch | condition | episode | attack | task |", "|---|---|---|---|---|"]
    rng = random.Random(1)
    for d, cond in KEY:
        p = os.path.join(ROOT, "results", d, "episodes.jsonl")
        if not os.path.exists(p):
            continue
        recs = sorted([renormalize(json.loads(x)) for x in open(p) if f'"condition": "{cond}"' in x],
                      key=lambda r: r["config"]["episode_id"])
        recs = [r for r in recs if r["config"]["condition"] == cond]
        ok = [r for r in recs if r["summary"]["task_success"]]
        bad = [r for r in recs if not r["summary"]["task_success"]]
        att = [r for r in recs if r["summary"]["attack_success"]]
        pick = rng.sample(ok, min(2, len(ok))) + rng.sample(bad, min(2, len(bad))) + rng.sample(att, min(2, len(att)))
        seen = set()
        for r in pick:
            eid = r["config"]["episode_id"]
            if eid in seen:
                continue
            seen.add(eid)
            fn = f"{d}__{cond}__{eid}.md"
            with open(os.path.join(OUT, fn), "w") as f:
                f.write(render(r))
            index.append(f"| {d} | {cond} | [{eid}]({fn}) | {r['summary']['attack_success']} | {r['summary']['task_success']} |")
    with open(os.path.join(OUT, "index.md"), "w") as f:
        f.write("\n".join(index) + "\n")
    print(f"wrote {len(index) - 6} transcripts to docs/verification/")


if __name__ == "__main__":
    main()
