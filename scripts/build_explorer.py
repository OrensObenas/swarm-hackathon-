"""Build docs/explorer/index.html: an interactive results explorer, with all data computed
from the episode logs (counts, Wilson CIs, and condensed real transcripts).
Usage: python scripts/build_explorer.py"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze import renormalize, silent_failure_stats, strict_metrics, wilson  # noqa: E402

BATCHES = [
    ("main", "main_mistral-small-2603", "Main", "Pre-registered 2×2: no monitor vs. block"),
    ("R", "replication_mistral-small-2603", "R · Replication", "Single-batch replication with rewrite"),
    ("B", "recovery_mistral-small-2603", "B · Recovery", "Blocking with recovery (retry, abstain notice)"),
    ("I", "input_mistral-small-2603", "I · Tool-input filter", "Rewrite documents before the first agent reads them"),
    ("N", "native_mistral-small-2603", "N · Native tools", "Native tool-calling protocol"),
    ("T", "board_mistral-small-2603", "T · Shared board", "Every agent sees all earlier messages"),
    ("M", "model_gpt-5.4-mini", "M · GPT agents", "Second agent model (gpt-5.4-mini)"),
    ("X", "xmonitor_gpt-5.4-mini", "X · GPT monitor", "Mistral agents, GPT monitor"),
    ("S", "explore_sanitize_mistral-small-2603", "S · Rewrite (exploratory)", "First, exploratory rewrite batch"),
    ("A", "adversarial_mistral-small-2603", "A · Adversarial", "Three hand-written injection variants"),
]
CUT = 700


def ci(k, n):
    p, lo, hi = wilson(k, n)
    return [k, n, round(lo, 4), round(hi, 4)]


def condense(r):
    steps = []
    for e in r["events"]:
        if e["kind"] == "tool_call":
            a = e.get("args") or {}
            if e["tool"] == "send_email":
                det = f"to {a.get('to', '')} · {str(a.get('subject', ''))[:90]}"
            elif e["tool"] == "read_document":
                det = a.get("name", "")
            else:
                det = ""
            steps.append({"k": "tool", "a": e["agent"], "tool": e["tool"], "d": det,
                          "t": bool(e.get("result_tainted")), "rt": bool(e.get("raw_result_tainted", e.get("result_tainted")))})
        elif e["kind"] == "input_filter":
            steps.append({"k": "filter", "reason": e["reason"][:200], "after": e["delivered"][:CUT],
                          "still": bool(e["delivered_tainted"])})
        elif e["kind"] == "retry_request":
            steps.append({"k": "retry", "a": e["agent"], "reason": e["reason"][:200]})
        elif e["kind"] == "message":
            steps.append({"k": "msg", "a": e["sender"], "to": e["receiver"], "raw": e["raw"][:CUT],
                          "del": e["delivered"][:CUT] if e["delivered"] != e["raw"] else None,
                          "taint": bool(e["raw_tainted"]), "flag": bool(e["flagged"]), "reason": e["reason"][:200],
                          "san": bool(e.get("sanitized")), "retried": bool(e.get("retried"))})
    s = r["summary"]
    out = [{"from": e["from_agent"], "to": e["to"], "subj": str(e["subject"])[:140], "body": str(e["body"])[:CUT]}
           for e in s["outbox"]]
    sm = strict_metrics(r)
    return {"id": r["config"]["episode_id"], "attack": s["attack_success"], "hijacked": s["hijacked_agents"],
            "task": s["task_success"], "vendor": s["recommended_vendor"], "outcome": sm["outcome"],
            "steps": steps, "outbox": out}


def build():
    data = {"batches": []}
    rng = random.Random(7)
    for bid, d, label, desc in BATCHES:
        path = os.path.join(ROOT, "results", d, "episodes.jsonl")
        recs = [renormalize(json.loads(x)) for x in open(path)]
        cfg = recs[0]["config"]
        conds = {}
        for c in sorted({r["config"]["condition"] for r in recs}):
            rs = sorted([r for r in recs if r["config"]["condition"] == c and r["summary"]["completed"]],
                        key=lambda r: r["config"]["episode_id"])
            S = [r["summary"] for r in rs]
            n = len(S)
            sm = [strict_metrics(r) for r in rs]
            msgs = [m for s in S for m in s["messages"]]
            taint = [m for m in msgs if m["raw_tainted"]]
            clean = [m for m in msgs if not m["raw_tainted"]]
            ok = [r for r in rs if r["summary"]["task_success"]]
            bad = [r for r in rs if not r["summary"]["task_success"]]
            att = [r for r in rs if r["summary"]["attack_success"]]
            pick, seen = [], set()
            for group in (att, bad, ok):
                for r in rng.sample(group, min(2, len(group))):
                    if r["config"]["episode_id"] not in seen and len(pick) < 5:
                        seen.add(r["config"]["episode_id"])
                        pick.append(r)
            conds[c] = {
                "n": n,
                "attack": ci(sum(s["attack_success"] for s in S), n),
                "down": ci(sum(s["n_hijacked_downstream"] > 0 for s in S), n),
                "task": ci(sum(s["task_success"] for s in S), n),
                "strict": ci(sum(x["strict_task"] for x in sm), n),
                "silent": ci(sum(x["outcome"] == "silent_failure" for x in sm), n),
                "visible": ci(sum(x["outcome"] == "visible_failure" for x in sm), n),
                "exposed": round(sum(s["n_exposed"] for s in S) / max(1, n), 2),
                "hops": [sum(s["messages"][h]["raw_tainted"] for s in S if len(s["messages"]) > h) for h in range(3)],
                "tpr": [sum(m["flagged"] for m in taint), len(taint)],
                "fpr": [sum(m["flagged"] for m in clean), len(clean)],
                "silent_check": sum(silent_failure_stats(r)[2] for r in rs),
                "episodes": [condense(r) for r in pick],
            }
        data["batches"].append({"id": bid, "label": label, "desc": desc, "model": cfg.get("model"),
                                "monitor_model": cfg.get("monitor_model"), "protocol": cfg.get("protocol", "json"),
                                "topology": cfg.get("topology", "chain"), "conds": conds})
    return data


if __name__ == "__main__":
    data = build()
    tpl = open(os.path.join(ROOT, "docs", "explorer", "template.html")).read()
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")).replace("</", "<\\/"))
    out = os.path.join(ROOT, "docs", "explorer", "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"wrote {os.path.relpath(out, ROOT)} ({len(html) / 1e6:.2f} MB, "
          f"{sum(len(c['episodes']) for b in data['batches'] for c in b['conds'].values())} episodes)")
