#!/usr/bin/env bash
# Regenerates every summary/figure used in docs/results.md.
set -e
cd "$(dirname "$0")/.."
A="python3 analyze.py"
$A results/main_mistral-small-2603 results/xmonitor_gpt-5.4-mini results/explore_sanitize_mistral-small-2603 --out results/combined >/dev/null
for d in replication_mistral-small-2603 adversarial_mistral-small-2603 model_gpt-5.4-mini input_mistral-small-2603 \
         native_mistral-small-2603 board_mistral-small-2603; do
  [ -s results/$d/episodes.jsonl ] && $A results/$d >/dev/null && echo "analyzed $d"
done
# H4-bis: pooled benign arms (main + replication), n = 60 per arm
$A results/main_mistral-small-2603 results/replication_mistral-small-2603 --out results/pooled_benign_main_replication >/dev/null
echo done
