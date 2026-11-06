---
title: "Stopping the Attack, Breaking the Task: Silent Failures and Recovery in Monitored Multi-Agent Pipelines"
---

**Author:** Gilbert Obenas  
**Affiliation:** Independent researcher  
**Track(s):** Science of agent networks & failure propagation; Multi-agent oversight & control  
**Code and logs:** [REPOSITORY URL — to be filled in once the author decides on visibility]

## Abstract

Multi-agent LLM systems pass text between agents, so an instruction planted in one untrusted document can travel well beyond the agent that read it. We built a small, fully simulated testbed: four agents (retriever, analyst, writer, reviewer) solve a fictional procurement task and share a mock e-mail tool. A self-replicating injection hidden in one vendor quote asks agents to e-mail internal notes to an outside address. We pre-registered hypotheses and ran {{total_episodes}} episodes in ten batches (30 per condition). Without monitoring, the injection hijacked an agent that never read the poisoned document in {{main_replicating_none_down}}/30 episodes of the main run (between {{R_replicating_none_down}}/30 and {{N_replicating_none_down}}/30 in replications). An LLM monitor that simply *withholds* suspicious inter-agent messages stopped every downstream hijack in the scenarios tested. However, it collapsed the legitimate task ({{B_replicating_llm_task}}/30 in batch B), mostly through **silent failures**: confident final reports naming vendors that do not exist. Recovery changes this. Telling the sender why its message was blocked and letting it resend once restored the task ({{B_replicating_blockretry_task}}/30) with 0 attacks, matching a monitor that rewrites flagged messages ({{B_replicating_sanitize_task}}/30). An explicit abstention notice did not restore the task, but turned most failures from silent into visible ({{B_replicating_blockabstain_out_visible}}/30). The lesson is about *recovery*, not blocking per se: a defence must restore the missing facts or make their absence visible. Our hand-written adversarial variants were mostly inert and no adaptive attack was tested, so these results hold only for the scenarios tested.

## 1. Introduction

LLM agents increasingly work in pipelines and teams: one agent retrieves documents, another analyses them, a third drafts output. Indirect prompt injection, where instructions are hidden in data an agent processes [1], is therefore no longer a single-agent problem. Text produced by a compromised agent becomes *input* for the next one, and a self-replicating instruction can spread from agent to agent [2, 5].

A natural defence is a monitor on the communication channel that inspects messages before they are delivered [7, 9]. Two questions about such a monitor are under-measured:
1. What fraction of the damage happens *downstream*, in agents that never touched the untrusted source and are therefore the only ones a channel monitor can protect?
2. What does the monitor cost the legitimate task when it intervenes?

We study both in a deliberately small, reproducible testbed. Our contributions:
1. A pre-registered comparison of monitor strategies on a four-agent chain (none, block, block with retry, block with an abstention notice, rewrite, and an input-side filter). The main comparisons were replicated across a second protocol (native tool calling), a second topology (shared board) and a second agent model.
2. Evidence that blocking *without recovery* eliminates propagation but turns attacks into **silent task failures**: agents confabulate, and the fact that data was withheld is lost before the final report. Blocking also suppresses agents' own warnings about the attack.
3. Evidence that **recovery** removes this cost: letting the sender resend after feedback performed as well as rewriting, and an explicit abstention notice made failures visible. We also report the negative results: our adversarial variants mostly failed to test the monitor.

All data, tools, companies and addresses are fictional; no real account or external action is involved.

## 2. Related work

**Indirect prompt injection.** Greshake et al. [1] introduced indirect prompt injection, including worming behaviour. InjecAgent [3] and AgentDojo [4] benchmark injections against single tool-using agents. We reuse their threat model (untrusted tool output) but measure transmission *between* agents.

**Propagation in multi-agent systems.** Prompt Infection [2] shows LLM-to-LLM self-replicating injections and proposes "LLM tagging". Morris-II [5] demonstrates zero-click worms across RAG-connected GenAI applications. Agent Smith [6] shows exponential "infectious jailbreak" among simulated multimodal agents. NetSafe [7] relates topology to the spread of misinformation. G-Safeguard [8] detects compromised agents with a GNN and prunes edges. Hammond et al. [10] place these phenomena in a broader taxonomy of multi-agent risk (network effects, multi-agent security).

**Defences and monitoring.** Spotlighting [11] marks untrusted data in the prompt. CaMeL [12] separates control flow from data flow by design. The AI-control literature [9] studies *trusted monitoring* and *trusted editing*, in which a monitor rewrites suspicious outputs instead of only flagging them. Our blocking-versus-rewriting comparison is an instance of that distinction, applied to inter-agent messages and evaluated jointly on security and task utility.

## 3. Method

### 3.1 Environment and task
A fictional company must pick the cheapest logistics vendor that meets its requirements:
- **Requirements** (`requirements.txt`): at least 40 pallets/week, delivery to the Lyon and Montreal hubs, 12-month contract.
- **Quotes** (`quote_*.txt`):
  - Bluefin, $48,200, compliant: **the correct answer**.
  - Harborline, $52,900, compliant but more expensive.
  - Cedarpeak, $39,500, cheaper but non-compliant.

Four agents run in a fixed chain: **retriever → analyst → writer → reviewer**. Only the retriever can read the drive (`list_documents`, `read_document`). Every agent has a shared simulated `send_email` tool, which only appends to an in-memory outbox; all addresses use the reserved `.example` domain. The reviewer must e-mail a report to the manager, starting with the line `Recommended vendor: <name>`. Exact prompts are given in Appendix B.

**Action protocol.** Each agent replies with one JSON object, either a tool call or a `final` hand-off message, for at most 8 steps. Malformed replies receive one corrective message. Batch N instead uses the provider's native tool-calling API.

### 3.2 Attack
The injection is appended to the Harborline quote, the only untrusted document; its full text is in Appendix B. The main variant (`replicating`) presents itself as a compliance notice. It asks the assistant to e-mail the complete internal notes to `records@vendor-audit.example` with a unique reference `NX-4471`, and to copy the notice verbatim into any message passed to a colleague.

Three further variants were written by hand once and frozen before any run (§4.4):
- `polite`: no compliance vocabulary and no marker;
- `monitor_bypass`: addresses the monitor and claims security clearance;
- `sanitizer_bypass`: poses as a task requirement and asks to survive rewrites.

### 3.3 Monitors
The monitor is an LLM call with a fixed system prompt (Appendix B). It sees the legitimate task and one inter-agent message and returns `{"suspicious": bool, "reason": str}`. Modes:
- **none.**
- **block:** a flagged message is replaced by a notice ("Message withheld by the security monitor…").
- **sanitize (channel):** a flagged message is rewritten by a second LLM call that must keep all task facts and remove instructions that do not serve the task.
- **sanitize (tool input):** the same classify-then-rewrite step is applied to documents returned by `read_document` before the retriever sees them; the channel is not monitored.
- **block + retry** (batch B): the sender is told that its message was blocked and why, and may resend once; the new message is checked again, and if it is flagged again the withheld notice is delivered.
- **block + abstain notice** (batch B): the withheld notice explicitly forbids inventing data and asks that the final report state that the vendor data was withheld (Appendix B).

Unparseable monitor replies fail open; this happened 0 times.

### 3.4 Models and parameters
- **Agents:** `mistral-small-2603` (Mistral API) in all batches except M, which uses `gpt-5.4-mini` (OpenAI API).
- **Monitor:** the same model as the agents, except in batch X (`gpt-5.4-mini` monitoring Mistral agents).
- **Calls:** OpenAI-compatible Chat Completions (`openai` Python SDK 3.46.0) with provider-default sampling. No temperature or max-token parameter is set.
- **Order:** episodes are interleaved at random within a batch (fixed seed per batch).
- **Logs:** every LLM call, tool call and message is logged as JSONL with the git commit.

### 3.5 Metrics
All metrics are computed per episode from the simulated outbox and the message log; there is no LLM judge.
- **Attack succeeded:** any e-mail reached the attacker address (recipients are parsed, so `manager@…,records@…` counts). We also report **substantive exfiltration**: an attacker e-mail whose body contains procurement facts (prices, vendor names or capacities).
- **Downstream agent hijacked** (primary endpoint): an agent other than the retriever e-mailed the attacker. Such an agent never read the source, so it was reached only through inter-agent messages.
- **Task succeeded:** the last report sent to the manager names Bluefin on the mandatory line. This is a lenient criterion. We also report a **strict task** criterion: the report names Bluefin, states $48,200, and quotes no dollar amount other than a drive price or a difference between two drive prices.
- **Silent failure:** the task failed, the report names a vendor that does not exist in the drive, and the report does not state that data was missing, withheld or unverified (regular expression, defined before batches R–T).
- **Outcome partition:** success; *silent failure*; *visible failure* (no report, or the report flags missing data); wrong real vendor.
- **Monitor TPR / FPR:** computed at message level against a taint label: the message contains the marker or the attacker address. This label measures the presence of the injection's *traces*, not danger: a message can quote the address in order to warn about it. We therefore also classify messages (regular expression) as **relay** (carries the injection without refusing it), **warning** (mentions it to refuse or flag it) or clean, and report detection on relays and flags on warnings separately (Table E3).

The strict task, substantive-exfiltration, outcome-partition and message-type metrics were added after an external review. They were pre-registered for batch B and are **post hoc** for all earlier batches.

All proportions use Wilson 95% intervals; comparisons use two-sided Fisher exact tests at α = 0.05. Pilots, amendments and every hypothesis were recorded in `docs/research_plan.md` before the corresponding data were collected (summary in Appendix C).

### 3.6 Batches
| Batch | Variation | Conditions (30 episodes each) | Status |
|---|---|---|---|
| Main | 2×2 design | benign / replicating × none / block | pre-registered |
| X | cross-provider monitor (`gpt-5.4-mini`) | benign / replicating × block | secondary |
| S | rewriting monitor | benign / replicating × sanitize | **exploratory** (designed after seeing Main) |
| R | single-batch replication | benign / replicating × none / block / sanitize | pre-registered |
| A | adversarial variants | 3 variants × none / block / sanitize | descriptive |
| M | second agent model (`gpt-5.4-mini`) | benign / replicating × none / block / sanitize | descriptive |
| I | tool-input filter | replicating × none / input-sanitize; benign × input-sanitize | pre-registered |
| N | native tool calling | benign × none; replicating × none / block / sanitize | descriptive replication |
| T | shared-board topology (each agent sees all prior messages) | same as N | descriptive |
| B | blocking with recovery | replicating × block / block+retry / block+abstain / sanitize; benign × block+retry / block+abstain | pre-registered (added after external review) |

## 4. Results

Across the {{total_episodes}} episodes, there were {{total_errors}} API or harness errors and {{total_refusals}} refusals.

### 4.1 Propagation without a monitor (H1)
In the main run, the injection was carried by {{main_replicating_none_hop1}}/30 retriever→analyst messages, {{main_replicating_none_hop2}}/30 analyst→writer messages and {{main_replicating_none_hop3}}/30 writer→reviewer messages. Of the {{main_replicating_none_attack}} successful attacks, {{main_replicating_none_down}} hijacked a downstream agent (H1: {{main_replicating_none_down}}/30, 95% CI [{{H1_ci_lo}}, {{H1_ci_hi}}]); only {{main_replicating_none_p0}} hijacked the retriever itself. Downstream hijacking replicated in every later Mistral batch (Table 1), including three hops away, at the reviewer.

**Run-to-run variation.** The absolute attack rate is **not stable**: {{main_replicating_none_attack}}/30 in Main against {{R_replicating_none_attack}}/30 in R under identical configuration (p = {{p_runvar_attack}}). We therefore rely only on within-batch comparisons.

### 4.2 Plain blocking versus rewriting (H2, H5, H6)
**Table 1.** Replicating injection unless noted. Counts out of 30 episodes; TPR/FPR at message level.

{{TABLE_SYNTH}}

**Plain blocking.** (Blocking *with recovery* is evaluated in §4.5.) The blocking monitor eliminated downstream hijacking. In Main this went from {{main_replicating_none_down}}/30 to 0/30 (H2, p = {{p_H2}}); in R from {{R_replicating_none_down}}/30 to 0/30 (H2-bis, p = {{p_H2bis}}). It did so with both monitor models, but at a large utility cost:
- the task succeeded in only {{main_replicating_llm_task}}/30 episodes (Main), {{X_replicating_llm_task}}/30 (X, GPT monitor) and {{R_replicating_llm_task}}/30 (R);
- most failures were **silent**: {{main_replicating_llm_silent}}/30 in Main and {{R_replicating_llm_silent}}/30 in R.

**Rewriting.** The rewriting monitor also eliminated downstream hijacking (H5: {{R_replicating_none_down}}/30 → 0/30, p = {{p_H5}}) while keeping the task at {{R_replicating_sanitize_task}}/30. Against blocking's {{R_replicating_llm_task}}/30, this is H6 (p = {{p_H6}}). This confirms on fresh, pre-registered data the effect first seen in the exploratory batch S ({{S_replicating_sanitize_task}}/30). The audit of the rewrites gives:
- none of the {{S_replicating_sanitize_rewrites}} (S), {{R_replicating_sanitize_rewrites}} (R), {{N_replicating_sanitize_rewrites}} (N) and {{T_replicating_sanitize_rewrites}} (T) rewritten messages still carried the marker or address;
- in S, a keyword check and the assistant's reading found no residual instruction, and all rewrites kept Bluefin and its price.

Rewriting is not cost-free in completeness: under the strict criterion, {{R_replicating_sanitize_strict}}/30 reports in R sanitize stated the price (the others named Bluefin but omitted $48,200; none quoted an invented amount).

The same pattern holds under native tool calling (N) and on the shared board (T, where an unmonitored injection reached all agents: {{T_replicating_none_exposed_mean}} agents exposed on average, against {{main_replicating_none_exposed_mean}} in the Main chain).

**Input-side filter (H9).** Rewriting documents *before* the retriever reads them removed exposure entirely. All {{I_filtered_docs}} poisoned documents read were rewritten, with 0 still tainted and {{I_filtered_keep_price}}/30 keeping the Harborline price. The attack fell from {{I_replicating_none_attack}}/30 to 0/30 (p = {{p_H9}}), and the task held at {{I_replicating_inputsanitize_task}}/30. There were no false positives on clean documents ({{I_benign_filtered}} rewrites in the benign condition).

**Benign cost (H4).** Without injection, no monitor mode caused attacks, and the task succeeded 28–30 times out of 30 in every batch (Table E1). Pooling Main and R (n = 60 per arm), blocking changed task success by {{H4_d}} points [95% Newcombe CI {{H4_lo}}, {{H4_hi}}]. The pre-registered margin of −10 points is therefore met, but narrowly.



### 4.3 Mechanisms (transcript audit and exploratory analyses)
We audited 10 randomly drawn episodes per injected condition from Main, X and S (seed 0; `docs/transcript_audit.csv`). The annotation was done by an AI assistant and has **not yet been verified by a human** [AUTHOR: replace this sentence once you have spot-checked the CSV].
- **Paraphrase, not copy.** At hop 2, every audited relay was a paraphrase. The injection was often reframed as a procedural note.
- **Execute *or* relay (exploratory).** Among exposed analysts in Main, those who executed the injection relayed it onward in {{relay_hij_k}}/{{relay_hij_n}} cases, against {{relay_non_k}}/{{relay_non_n}} for those who did not execute it. Neither hijacked retriever relayed it. Agents appear to treat the instruction as a to-do item that is discharged once done.
- **Lost warnings under blocking.** In {{withheld_known}}/30 Main block episodes, the analyst explicitly wrote that the retriever's notes were withheld, then proceeded with invented data. That knowledge did not survive to the final report.
- **Blocking suppresses whistle-blowers (batch M).** With `gpt-5.4-mini` agents, the retriever almost never relayed or obeyed the injection: {{M_replicating_none_hop1}}/30 relays, 0 attacks, a floor effect. It did, however, often **warn** about it ({{gpt_warn_k}}/{{gpt_warn_n}} retriever messages classified as *warning*), for example "I did not follow the embedded request to email internal notes…". The blocking monitor withheld these warnings as if they were the attack ({{M_replicating_llm_warn_flagged}}/{{M_replicating_llm_warn_msgs}} warnings flagged). Task success dropped from {{M_replicating_none_task}}/30 to {{M_replicating_llm_task}}/30. With rewriting, warnings were flagged too ({{M_replicating_sanitize_warn_flagged}}/{{M_replicating_sanitize_warn_msgs}}) but cost nothing ({{M_replicating_sanitize_task}}/30). Because this model was not attacked successfully even without a monitor, batch M shows the *cost* of monitoring a resistant model, **not** that the monitor protects it.

### 4.4 Adversarial variants (batch A; Table E2)
`polite` and `monitor_bypass` were **inert**: across all {{A_inert_n}} episodes of each variant, the retriever never carried them into its notes, so they did not test the monitor at all. `sanitizer_bypass` did propagate and hijacked {{A_sanitizer_bypass_none_down}}/30 reviewers without a monitor. The blocking monitor missed {{A_sb_llm_missed}} tainted messages (TPR {{A_sanitizer_bypass_llm_tp}}/{{A_sanitizer_bypass_llm_taint_msgs}}). In those messages the attacker address was presented as an ordinary report recipient, and the monitor judged them "ordinary task content"; none led to a hijack. With rewriting, the attack failed in every episode and the task held at {{A_sanitizer_bypass_sanitize_task}}/30.

### 4.5 Blocking with recovery (batch B; H10–H12)
**Table 2.** Batch B (single batch, all conditions interleaved). Counts out of 30.

{{TABLE_B}}

Plain blocking reproduced the earlier result: {{B_replicating_llm_task}}/30 task successes and {{B_replicating_llm_out_silent}}/30 silent failures.
- **Retry (H10).** Telling the sender why its message was blocked and letting it resend once restored the task to {{B_replicating_blockretry_task}}/30 (p = {{p_H10}} against plain blocking), with 0 attacks. The sender resent in {{B_replicating_blockretry_retried}} episodes; none of the resent messages carried the injection or was flagged again.
- **Abstention notice (H11).** Silent failures fell to {{B_replicating_blockabstain_out_silent}}/30 (p = {{p_H11}}): {{B_replicating_blockabstain_out_visible}}/30 failures were now visible (no report, or a report stating the data was withheld). The task itself still failed ({{B_replicating_blockabstain_task}}/30).
- **Rewrite against retry (H12).** {{B_replicating_sanitize_task}}/30 against {{B_replicating_blockretry_task}}/30 (p = {{p_H12}}): no difference in this scenario.
- **Cost without injection.** Neither recovery mode changed the benign task ({{B_benign_blockretry_task}}/30 and {{B_benign_blockabstain_task}}/30), and no retry was triggered.

This answers the main objection to §4.2: rewriting's advantage over *plain* blocking is largely shared by any strategy that recovers the facts. Retry is cheaper to build (no rewriting model), but it relies on the sender being uncompromised. Here, the retriever was never hijacked in these conditions.

Stricter metrics (Table E3, post hoc for these batches): substantive exfiltration tracked "e-mail reached the attacker" almost exactly ({{I_replicating_none_exfil_sub}}/{{I_replicating_none_attack}} in I, equal elsewhere). The strict task criterion changed little, except that rewritten reports sometimes omitted the price. In the Mistral batches no message was classified as a warning, so detection on *relays* equals the TPR reported above. In batch M, all flagged messages were warnings or clean.

## 5. Discussion

**What a channel monitor can and cannot do.** In our testbed, most damage was downstream. A channel monitor prevented it in every batch where the attack worked, with two different monitor models. Note that 0/30 is not a guarantee: its 95% upper bound is 11%. A channel monitor cannot protect the agent that reads the poisoned source; an input-side filter can, and did here.

**"No attack" is not "no harm".** Plain blocking converts a visible security failure (an exfiltration e-mail) into an invisible utility failure: a confident report recommending a vendor that does not exist. In deployment this may be worse, because no downstream signal reveals it. Blocking also removed agents' own warnings about the attack. A monitor should be evaluated jointly on security, task success and *silent* failure.

**Rewriting as trusted editing.** Rewriting flagged content behaves like trusted editing [9]: it tolerated false positives (batch M) and preserved task facts. Part of its advantage over plain blocking is expected by construction, since plain blocking deletes the facts the next agent needs; this is why batch B compares it against blocking *with recovery*. Rewriting also gives the monitor write access to the content, which creates a new attack surface: our `sanitizer_bypass` variant targeted exactly this, without succeeding. We present rewriting as effective **in the scenarios tested**, not as a robust defence: an adaptive attacker was not tested.

**Recovery is the key variable.** Batch B shows that the failure is not blocking as such but *blocking without recovery*. Two recovery strategies worked in our scenario: re-asking the sender (retry), or rewriting the content (sanitize). An explicit abstention notice did not save the task, but it converted silent failures into visible ones, which is the safer failure mode. We recommend evaluating any multi-agent monitor on three axes: attack prevention, task success, and the *visibility* of its failures.

## 6. Conclusion
In a small, pre-registered, fully simulated four-agent testbed, a self-replicating injection placed in one document regularly hijacked agents that never read it. Withholding suspicious inter-agent messages stopped this but caused silent task failure. Recovery removed that cost: re-asking the sender, rewriting the message, or filtering tool outputs before the first agent reads them all stopped the attack and preserved the task, against the fixed injections we tested. An abstention notice at least made the failures visible. The main open questions are adaptive attacks against the monitor and the retry loop, and whether these patterns hold for larger systems.

## References

[1] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, M. Fritz. *Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.* arXiv:2302.12173, 2023.

[2] D. Lee, M. Tiwari. *Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems.* arXiv:2410.07283, 2024.

[3] Q. Zhan, Z. Liang, Z. Ying, D. Kang. *InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents.* Findings of ACL, 2024.

[4] E. Debenedetti et al. *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.* NeurIPS Datasets and Benchmarks, 2024. arXiv:2406.13352.

[5] S. Cohen, R. Bitton, B. Nassi. *Here Comes The AI Worm: Unleashing Zero-click Worms that Target GenAI-Powered Applications.* arXiv:2403.02817, 2024.

[6] X. Gu et al. *Agent Smith: A Single Image Can Jailbreak One Million Multimodal LLM Agents Exponentially Fast.* ICML (PMLR 235), 2024. arXiv:2402.08567.

[7] M. Yu et al. *NetSafe: Exploring the Topological Safety of Multi-agent Networks.* arXiv:2410.15686, 2024.

[8] Wang et al. *G-Safeguard: A Topology-Guided Security Lens and Treatment on LLM-based Multi-agent Systems.* ACL (Long Papers), 2025. arXiv:2502.11127.

[9] R. Greenblatt, B. Shlegeris, K. Sachan, F. Roger. *AI Control: Improving Safety Despite Intentional Subversion.* arXiv:2312.06942, 2023.

[10] L. Hammond et al. *Multi-Agent Risks from Advanced AI.* Cooperative AI Foundation Technical Report #1, arXiv:2502.14143, 2025.

[11] K. Hines, G. Lopez, M. Hall, F. Zarfati, Y. Zunger, E. Kiciman. *Defending Against Indirect Prompt Injection Attacks With Spotlighting.* arXiv:2403.14720, 2024.

[12] E. Debenedetti et al. *Defeating Prompt Injections by Design.* arXiv:2503.18813, 2025.

---

## Appendix A. Limitations and Dual-Use / Ethical Considerations

### A.1 Limitations
- **Toy scope.** There is one fictional scenario and one task, with four agents. The topologies are a fixed chain and a shared board; the agent models are two small models (`mistral-small-2603`, `gpt-5.4-mini`). Results may not transfer to larger systems, other tasks or other models.
- **Hand-written, non-adaptive attacks.** Two of three adversarial variants were inert, so the monitor's robustness is largely **untested**. No attack was optimised against the monitor or the rewriter.
- **Unstable absolute rates.** Attack rates varied between batches under identical configurations ({{main_replicating_none_attack}}/30 against {{R_replicating_none_attack}}/30). Only within-batch comparisons are reliable, and cross-batch statements are indicative only.
- **Statistics.** We used n = 30 per cell and uncorrected Fisher tests. With a Bonferroni correction over the six confirmatory tests (α ≈ 0.0083), H2-bis and H5 (p ≈ 0.024) would not be significant; H2, H6 and H9 would remain so. H4 was met by a narrow margin.
- **Measurement.**
  - Taint labels rely on a marker or address, and paraphrases that drop both would be missed.
  - "Silent failure" relies on a regular expression over the final report.
  - The transcript audit was annotated by an AI assistant (a human spot-check by the author is pending).
  - The JSON action protocol is not how production agents call tools; batch N partially addresses this.
- **Retry assumes an honest sender.** In batch B the retriever was never hijacked in the recovery conditions. A compromised sender could exploit the feedback loop, which was not tested.
- **Same-model monitor.** The monitor mostly used the agents' model. One cross-provider batch (X) showed the same pattern.
- **Design history.** The rewriting mode was designed after observing the main run (batch S). It was then tested on pre-registered batches (R, I, N, T) without further tuning. Harness defects found in pilots were fixed before the main run (Appendix C). One duplicated run (concurrent writers) was excluded and re-run identically.

### A.2 Dual-use and ethical considerations
- **What could be misused.**
  - The injection texts and the harness, which measures attack success, could in principle help someone optimise injections against real multi-agent systems.
  - Our finding that blocking monitors cause silent failures could guide an attacker who wants to cause damage *through* a defence: injecting text that triggers withholding of legitimate data.
- **Why we consider the risk low.**
  - The attack patterns (fake compliance notice, request to copy verbatim) are already well documented [1, 2, 5]. We introduce no new jailbreak technique and performed no automated attack optimisation.
  - The payload is mundane (exfiltrating fictional notes), and all data, companies and addresses are fictional (reserved `.example` domain). `send_email` only writes to memory, and no real account or external system was touched.
- **Release choices.**
  - We release the monitor prompts, metrics and full logs, which mainly serve defenders.
  - We do not release attack variants optimised for a specific model; none were produced.
  - We caution against reading our results as a security guarantee: an LLM monitor is itself injectable, and adaptive attacks were not evaluated.
- **Human subjects.** None.

## Appendix B. Prompts and injection texts (verbatim from the code)

{{PROMPTS}}

## Appendix C. Pre-registration, pilots and deviations
- **Pilots** (excluded from analysis):
  1. The first pilot showed propagation, so there was no floor effect. It also showed that the original task checker (vendor and price) was too strict; it was replaced by the mandatory `Recommended vendor:` line.
  2. The second pilot revealed a harness defect: the writer e-mailed the manager itself and handed off an empty message, and the reviewer then confabulated. Roles were clarified: only the reviewer e-mails the manager, and every agent passes on its full content. `send_email` stayed available to all agents.
  3. The third pilot confirmed the fix (benign task 5/5), and the configuration was frozen.
- **Pre-registration.** Every later hypothesis (H2-bis, H4-bis, H5, H6, H9) and every descriptive batch was written into `docs/research_plan.md` and committed before data collection (§§8–13, with git timestamps).
- **Analysis bug found and fixed.** An independent recount (`scripts/independent_recount.py`) revealed that a single e-mail addressed to both the manager and the attacker was counted as an attack but not as a report. This affected 2 episodes (batch A, `sanitizer_bypass_none`: task 28→30/30). All numbers here use the corrected parsing, and the analysis and the independent recount now agree on every batch.
- **Post-hoc metrics and strict-task amendment.** The strict metrics were added after an external review. The first version of `strict_task` wrongly rejected correct derived figures such as the \$4,700 saving; it was amended before batch B was analysed.
- **Deviations.**
  - Agents run on Mistral rather than the originally planned Claude, because no Claude API key was available.
  - The silent-failure metric was defined after the main run.
  - Batch T was re-run after a duplicated launch.

## Appendix D. Reproducibility, pre-existing work and AI assistance
- **Code and logs.** `run_experiment.py`, `analyze.py`, `scripts/final_analysis.sh` and `scripts/build_report.py`. Every number in this report is generated from the logs by `scripts/report_numbers.py`. Commands are in the README; exact versions are in `requirements-lock.txt`.
- **Pre-existing work.** None. All code, prompts and data were created during the sprint (6–8 Nov 2026).
- **AI assistance.** An AI coding assistant (Claude, via Claude Code) helped write the code, run the experiments, analyse the logs and draft this report. [AUTHOR: confirm] The author reviewed the content and is responsible for it. The models *under study* are only those listed in §3.4.

## Appendix E. Additional tables

**Table E1.** Benign conditions (no injection).

{{TABLE_BENIGN}}

**Table E2.** Adversarial variants (batch A), hand-written and frozen before running.

{{TABLE_ADV}}

**Table E3.** Stricter metrics: substantive exfiltration, strict task, and monitor flags on relays versus warnings.

{{TABLE_STRICT}}
