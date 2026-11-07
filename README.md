# Stopping the Attack, Breaking the Task: Silent Failures and Recovery in Monitored Multi-Agent Pipelines

Submission to the **Swarm Alignment Hackathon** (Apart Research, 6–8 Nov 2026). Tracks: *science of agent networks & failure propagation* and *multi-agent oversight & control*.
Author: Gilbert Obenas (independent).

- 📄 **Report:** [`docs/report/report.pdf`](docs/report/report.pdf) (source: [`docs/report/report.md`](docs/report/report.md))
- 📊 **Overview figure:** [`results/overview.png`](results/overview.png)

## In one paragraph

Four LLM agents (retriever → analyst → writer → reviewer) solve a fictional procurement task and share a mock e-mail tool. A self-replicating prompt injection is hidden in one untrusted vendor quote, which only the first agent reads. Across 1,380 episodes in ten batches (30 per condition; hypotheses pre-registered, exploratory parts labelled), the injection regularly hijacked agents that never read the poisoned document.

An LLM monitor that **withholds** suspicious inter-agent messages stopped every such hijack in the scenarios tested. But it collapsed the legitimate task through **silent failures**: confident reports naming vendors that do not exist. **Recovery** removed this cost:
- letting the blocked sender resend after feedback performed as well as rewriting the message (30/30 tasks, 0 attacks);
- an explicit abstention notice made failures **visible** instead of silent.

All data, companies, addresses and tools are fictional and simulated. No real account was used and no external action was taken.

## Repository map

| Path | What it is |
|---|---|
| `pi_swarm/world.py` | Fictional environment: documents, injection texts, simulated tools, ground-truth labels |
| `pi_swarm/episode.py` | Four-agent chain or shared board, JSON or native tool-calling protocol, monitors (`none`, `llm` = block, `block_retry`, `block_abstain`, `llm_sanitize`, `input_sanitize`, `keyword`), per-episode metrics |
| `pi_swarm/backends.py` | OpenAI-compatible backend (Mistral, OpenAI), Anthropic backend (unused in reported runs), and a seeded `mock` backend used **only** for tests |
| `run_experiment.py` | Runs conditions × trials in a shuffled order, logs JSONL, resumes after interruption |
| `analyze.py` | Wilson CIs, Fisher exact tests, Newcombe CI, silent-failure and strict metrics, figures |
| `scripts/report_numbers.py`, `scripts/build_report.py` | Generate **every number** in the report from the logs, and build the report |
| `scripts/independent_recount.py` | Recounts the headline metrics from raw logs without using `analyze.py` (cross-check) |
| `scripts/final_analysis.sh` | Regenerates all summaries and the overview figure |
| `scripts/audit_*.py`, `docs/transcript_audit.csv` | Random transcript audit (40 episodes, AI-annotated) |
| `scripts/verification_sample.py`, `docs/verification/` | 23 complete, human-readable episodes (successes and failures) |
| `results/<batch>/` | `episodes.jsonl` (every LLM call, tool call, message and monitor verdict), `config.json` (arguments, git commit), `summary.md`, figures |
| `docs/research_plan.md` | Pre-registration log: hypotheses, pilots and amendments, each committed before its data (in French) |
| `docs/results.md` | Working results notes (in French) |
| `tests/test_pipeline.py` | 12 tests, including an end-to-end mock run and analysis |

**Batches reported:** `main`, `xmonitor` (X), `explore_sanitize` (S), `replication` (R), `adversarial` (A), `model_gpt-5.4-mini` (M), `input` (I), `native` (N), `board` (T), `recovery` (B).

**Not reported:**
- `pilot*`: excluded pilots;
- `mock_smoke`: synthetic numbers from the mock backend, a pipeline test only, **not evidence**;
- `excluded/`: a duplicated run, see its README.

## Reproduce

```bash
pip install -r requirements.txt          # exact versions: requirements-lock.txt (Python 3.13)
python tests/test_pipeline.py            # no API key needed

# Re-run a batch (needs MISTRAL_API_KEY; OPENAI_API_KEY for gpt-5.4-mini). Example: batch B
python run_experiment.py --backend mistral --model mistral-small-2603 --trials 30 --workers 6 --seed 70 \
  --conditions replicating_llm replicating_blockretry replicating_blockabstain replicating_sanitize \
               benign_blockretry benign_blockabstain --out results/recovery_mistral-small-2603

# Recompute everything from the logs
bash scripts/final_analysis.sh
python scripts/independent_recount.py
python scripts/build_report.py
```

The exact arguments of every batch are stored in `results/<batch>/config.json`.

- **Options:** `--protocol native` (native tool calling), `--topology board` (shared board), `--monitor-backend` / `--monitor-model`.
- **Condition names:** `<injection>_<monitor>`, where:
  - injection is one of `benign`, `replicating`, `direct`, `polite`, `monitor_bypass`, `sanitizer_bypass`;
  - monitor is one of `none`, `keyword`, `llm`, `blockretry`, `blockabstain`, `sanitize`, `inputsanitize`.

LLM outputs are not deterministic: re-runs give close, not identical, numbers.

## Integrity notes

- Every hypothesis, pilot amendment and new batch was written into `docs/research_plan.md` and committed **before** its data were collected. The git history carries the timestamps. Exploratory and post-hoc analyses are labelled as such in the report.
- Every number in the report is generated from the logs, and an unknown placeholder makes the build fail. `scripts/independent_recount.py` matches `analyze.py` on every batch. It found one analysis bug, which is fixed and documented in Appendix C of the report.
- The transcript audit (`docs/transcript_audit.csv`) was annotated by an AI assistant.

## Pre-existing work and AI assistance

- **Pre-existing work: none.** All code, prompts, data and results were produced during the sprint (6–8 Nov 2026). The initial commit contains only a one-line README.
- **AI assistance:** the code, the running of experiments, the analysis and the drafting were done with the help of Claude (Claude Code). The models **under study** are `mistral-small-2603` and `gpt-5.4-mini` only.

## Dual use

The injection texts and the harness could in principle help someone tune injections against real multi-agent systems. The patterns used are already public, no attack was optimised, and everything runs in a simulated environment with `.example` addresses. See *Appendix A: Limitations and Dual-Use / Ethical Considerations* in the report.
