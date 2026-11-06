#!/usr/bin/env python3
"""Run the prompt-injection propagation experiment.

Examples
  # Harness smoke test, no API key needed (synthetic numbers, NOT evidence):
  python run_experiment.py --backend mock --trials 20 --out results/mock_smoke

  # Real run (core 2x2 design), 30 trials per condition:
  python run_experiment.py --backend anthropic --model claude-opus-5-5 --trials 30 \
      --workers 4 --out results/main

Output: <out>/config.json, <out>/episodes.jsonl (one JSON line per episode, appended
as they finish; re-running with the same --out resumes and skips finished episodes).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import subprocess
import sys
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from pi_swarm.backends import make_backend
from pi_swarm.episode import run_episode

CONDITIONS = {
    #  name               injection       monitor
    "benign_none":       (None,          "none"),
    "benign_llm":        (None,          "llm"),
    "benign_keyword":    (None,          "keyword"),
    "replicating_none":  ("replicating", "none"),
    "replicating_llm":   ("replicating", "llm"),
    "replicating_keyword": ("replicating", "keyword"),
    "direct_none":       ("direct",      "none"),
    "direct_llm":        ("direct",      "llm"),
}
CORE = ["benign_none", "benign_llm", "replicating_none", "replicating_llm"]


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["mock", "anthropic", "openai", "mistral"], required=True)
    ap.add_argument("--model", default="claude-opus-5-5", help="agent model (anthropic backend)")
    ap.add_argument("--monitor-model", default=None, help="monitor model; defaults to --model")
    ap.add_argument("--monitor-backend", default=None, choices=["mock", "anthropic", "openai", "mistral"],
                    help="monitor provider; defaults to --backend (use with --monitor-model)")
    ap.add_argument("--effort", default="low", choices=["low", "medium", "high"])
    ap.add_argument("--conditions", nargs="+", default=CORE, choices=list(CONDITIONS))
    ap.add_argument("--trials", type=int, default=20, help="episodes per condition")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    episodes = [{"episode_id": f"{c}-{k:03d}", "condition": c, "trial": k,
                 "injection": CONDITIONS[c][0], "monitor": CONDITIONS[c][1]}
                for c in args.conditions for k in range(args.trials)]
    random.Random(args.seed).shuffle(episodes)  # interleave conditions over time

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "episodes.jsonl")
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                rec = json.loads(line)
                if rec["summary"]["error"] is None:
                    done.add(rec["config"]["episode_id"])
    todo = [e for e in episodes if e["episode_id"] not in done]
    print(f"{len(episodes)} episodes planned, {len(done)} already done, {len(todo)} to run.")
    if args.dry_run:
        print("Upper bound on LLM calls: ~", len(todo) * (4 * 8 + 3))
        return

    cfg_path = os.path.join(args.out, "config.json")
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w") as f:
            json.dump({"args": vars(args), "git_commit": git_commit(),
                       "started_utc": datetime.now(timezone.utc).isoformat(),
                       "python": sys.version, "platform": platform.platform()}, f, indent=2)

    lock = threading.Lock()

    def one(ep):
        seed = zlib.crc32(f"{args.seed}:{ep['episode_id']}".encode())
        backend = make_backend(args.backend, model=args.model, effort=args.effort, seed=seed)
        mon = (make_backend(args.monitor_backend or args.backend, model=args.monitor_model or args.model,
                            effort=args.effort, seed=seed + 1)
               if (args.monitor_model or args.monitor_backend) else None)
        rec = run_episode(ep, backend, mon)
        rec["config"].update({"backend": backend.name, "model": backend.model,
                              "monitor_model": (mon or backend).model, "seed": seed})
        with lock, open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return rec

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one, ep) for ep in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            s = fut.result()["summary"]
            print(f"[{i}/{len(todo)}] {fut.result()['config']['episode_id']}: "
                  f"attack={s['attack_success']} hijacked={s['hijacked_agents']} "
                  f"task={s['task_success']} err={'yes' if s['error'] else 'no'} "
                  f"({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
