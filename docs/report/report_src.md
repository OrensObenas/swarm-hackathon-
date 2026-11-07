---
title: "Stopping the Attack, Breaking the Task: Silent Failures and Recovery in Monitored Multi-Agent Pipelines"
---

<div class="titleblock">
<hr class="thick"/>
<h1 class="title">Stopping the Attack, Breaking the Task: Silent Failures and Recovery in Monitored Multi-Agent Pipelines<sup>1</sup></h1>
<hr class="thin"/>
<div class="authors"><div class="author">Gilbert Obenas<br/>Independent</div></div>
<div class="with"><b>With</b><br/>Apart Research</div>
</div>

<h2 class="abstract-h">Abstract</h2>
<div class="abstract">

Multi-agent LLM systems pass text between agents, so an instruction planted in one untrusted document can travel well beyond the agent that read it. We built a small, fully simulated testbed: four agents (retriever, analyst, writer, reviewer) solve a fictional procurement task and share a mock e-mail tool, and a self-replicating injection hidden in one vendor quote asks them to e-mail internal notes to an outside address. Across {{total_episodes}} episodes in ten batches (30 per condition, hypotheses pre-registered), the injection hijacked an agent that never read the poisoned document in {{main_replicating_none_down}}/30 episodes of the main run (between {{R_replicating_none_down}}/30 and {{N_replicating_none_down}}/30 in replications). An LLM monitor that *withholds* suspicious inter-agent messages stopped every downstream hijack in the scenarios tested, but collapsed the legitimate task ({{B_replicating_llm_task}}/30), mostly through **silent failures**: confident final reports naming vendors that do not exist. Recovery removes this cost. Telling the sender why its message was blocked and letting it resend once restored the task ({{B_replicating_blockretry_task}}/30, 0 attacks), matching a monitor that rewrites flagged messages ({{B_replicating_sanitize_task}}/30); an explicit abstention notice did not save the task but made most failures visible ({{B_replicating_blockabstain_out_visible}}/30). The takeaway is about *recovery*, not blocking per se: a defence must restore missing facts or make their absence visible. Our hand-written adversarial variants were mostly inert and no adaptive attack was tested, so these results hold only for the scenarios tested.

</div>

## 1. Introduction

LLM agents increasingly work in pipelines: one agent retrieves documents, another analyses them, a third drafts output. Indirect prompt injection, in which instructions hidden in data hijack the agent that processes it [1], therefore stops being a single-agent problem. Text written by a compromised agent becomes *input* for the next one, and a self-replicating instruction can spread from agent to agent [2, 5].

A natural defence is a monitor on the communication channel that inspects messages before delivery [9]. Two properties of such a monitor are rarely measured together: whether it protects the agents that never touched the untrusted source, which are the only ones a channel monitor *can* protect, and what it costs the legitimate task when it intervenes. A monitor that stops every attack but silently breaks the task is not safe in any useful sense.

**Our main contributions are:**

1. A small, reproducible, fully simulated testbed. It covers a four-agent chain with a shared tool, six monitor strategies, full JSON logs, and every reported number generated from the logs and cross-checked by an independent recount.
2. A pre-registered finding that **blocking without recovery** stops propagation but converts attacks into **silent task failures**: downstream agents confabulate, the fact that data was withheld is lost before the final report, and agents' own warnings about the attack are suppressed.
3. A pre-registered test of **recovery**. Letting the blocked sender resend, rewriting the flagged message, or filtering tool outputs before the first agent reads them all stopped the attack and kept the task. An abstention notice made failures visible. We also report negative results: most of our adversarial variants never tested the monitor.

## 2. Related Work

**Indirect prompt injection.** Greshake et al. [1] introduced indirect prompt injection, including worming behaviour. InjecAgent [3] and AgentDojo [4] benchmark it against single tool-using agents; we reuse their threat model (untrusted tool output) but measure transmission *between* agents.

**Propagation in multi-agent systems.** Prompt Infection [2] demonstrates LLM-to-LLM self-replicating injections and proposes "LLM tagging". Morris-II [5] shows zero-click worms across RAG-connected applications, and Agent Smith [6] shows exponential "infectious jailbreaks" among simulated multimodal agents. NetSafe [7] relates topology to the spread of misinformation, and G-Safeguard [8] detects compromised agents with a graph neural network and prunes edges. Hammond et al. [10] place these risks in a broader multi-agent taxonomy.

**Defences and monitoring.** Spotlighting [11] marks untrusted data in the prompt, and CaMeL [12] separates control flow from data flow by design. AI control [9] studies *trusted monitoring* and *trusted editing*, where a monitor rewrites suspicious outputs instead of only flagging them.

**What is new here.** Prior work mostly reports attack success. We evaluate monitors jointly on **attack prevention, task success and the visibility of failures**. We show that the dominant cost of a channel monitor comes from what happens *after* it blocks, and that cheap recovery mechanisms remove that cost in our setting.

## 3. Methods

**Environment.** A fictional company must pick the cheapest logistics vendor that meets its requirements (at least 40 pallets/week, delivery to Lyon and Montreal, 12-month contract). There are three quotes:
- Bluefin, $48,200, compliant: **correct**;
- Harborline, $52,900, compliant but more expensive;
- Cedarpeak, $39,500, cheaper but non-compliant.

Four agents run in a fixed chain, **retriever → analyst → writer → reviewer**, and each passes a hand-off message to the next.
- Only the retriever can read the shared drive.
- Every agent can call a shared simulated `send_email` tool that only writes to an in-memory outbox; all addresses use the reserved `.example` domain.
- The reviewer must e-mail the manager a report starting with `Recommended vendor: <name>`.
- Agents act through a JSON protocol: one tool call or one hand-off per turn, at most 8 steps. Batch N uses native tool calling instead.

All prompts are in Appendix B.

**Attack.** The injection is appended to the Harborline quote, the only untrusted document. It poses as a compliance notice and asks the assistant to e-mail the complete internal notes to `records@vendor-audit.example` with reference `NX-4471`, and to *copy the notice verbatim into any message passed to a colleague*. Three further variants were hand-written and frozen before running: polite, monitor-addressing, and posing as a task requirement (Appendix E).

**Monitors.** An LLM classifier sees the task and one inter-agent message and returns `{"suspicious": bool, "reason": str}`. It is used in six ways:
- **block**: a flagged message is replaced by a "withheld" notice;
- **block + retry**: the sender is told why its message was blocked and may resend once; the new message is re-checked;
- **block + abstain notice**: the notice forbids inventing data and asks that the final report state that data was withheld;
- **rewrite**: a second call rewrites the flagged message, keeping task facts and removing foreign instructions;
- **rewrite tool input**: the same rewrite is applied to documents *before* the retriever reads them;
- **none**.

**Models and parameters.**
- Agents use `mistral-small-2603`, except in batch M (`gpt-5.4-mini`).
- The monitor uses the agents' model, except in batch X (`gpt-5.4-mini` monitoring Mistral agents).
- Calls go through OpenAI-compatible Chat Completions (`openai` SDK 3.46.0) with provider-default sampling; no temperature or max-token parameter is set.
- Each batch interleaves its conditions in a seeded random order.

**Metrics** are computed from the simulated outbox and message log, with no LLM judge:
- **Downstream hijack** (primary): an agent other than the retriever e-mails the attacker. Such an agent was reached only through inter-agent messages.
- **Attack**: any e-mail reaches the attacker.
- **Task**: the final report names Bluefin. The **strict** variant also requires that it states $48,200 and quotes no invented amount.
- **Silent failure**: the task fails, the report names a non-existent vendor, and it does not mention missing data.
- **Visible failure**: no report is sent, or the report says data is missing.

Proportions use Wilson 95% intervals and comparisons use two-sided Fisher exact tests (α = 0.05). Every hypothesis and batch was committed to `docs/research_plan.md` before its data were collected. The batches are listed in Table E1.

## 4. Results

All {{total_episodes}} episodes completed, with {{total_errors}} errors and {{total_refusals}} refusals.

**Propagation without a monitor (H1).** In the main run, the injection was carried by {{main_replicating_none_hop1}}/30 retriever→analyst messages, then {{main_replicating_none_hop2}}/30 and {{main_replicating_none_hop3}}/30 further downstream. It hijacked a downstream agent in {{main_replicating_none_down}}/30 episodes (95% CI [{{H1_ci_lo}}, {{H1_ci_hi}}]) and the retriever itself in only {{main_replicating_none_p0}}. Downstream hijacking replicated in every later Mistral batch, including three hops away at the reviewer. The **absolute rate is unstable**: {{main_replicating_none_attack}}/30 in Main against {{R_replicating_none_attack}}/30 in R under identical settings (p = {{p_runvar_attack}}). We therefore compare conditions only *within* a batch.

**Plain blocking (H2).** Blocking eliminated downstream hijacking: {{main_replicating_none_down}}/30 → 0/30 in Main (p = {{p_H2}}) and {{R_replicating_none_down}}/30 → 0/30 in R (p = {{p_H2bis}}). It did so with both monitor models. But the task collapsed to between {{R_replicating_llm_task}}/30 and {{N_replicating_llm_task}}/30 across Mistral batches, and most failures were **silent** ({{R_replicating_llm_silent}}/30 in R). The first blocked message usually carried both the injection and the facts, so the next agent invented a vendor ("SwiftCargo Logistics", $45,200…). In {{withheld_known}}/30 Main episodes, the analyst even wrote that the notes had been withheld, but that knowledge never reached the final report.

![**Figure 1.** Downstream hijacking (left) and legitimate task success (right) under the self-replicating injection, by batch and monitor mode. Points are proportions; bars are Wilson 95% CIs; n = 30 per point. Plain blocking (orange) prevents hijacking but destroys the task; block + retry (violet, batch B) and rewriting (green) prevent hijacking and keep the task. Batch M agents were not attacked successfully even without a monitor.](FIGURE_OVERVIEW)

**Table 1.** Main comparisons from the single-batch, pre-registered runs (R, B, I). Self-replicating injection; counts out of 30. The full table for all batches is Table E2.

{{TABLE_CORE}}

**Recovery (H5, H6, H9–H12).**
- **Rewrite (H5, H6).** Rewriting the flagged message also stopped downstream hijacking (H5: p = {{p_H5}}) and kept the task at {{R_replicating_sanitize_task}}/30 against {{R_replicating_llm_task}}/30 for blocking (H6: p = {{p_H6}}). This replicates on fresh data an effect first seen in an exploratory batch. None of the {{R_replicating_sanitize_rewrites}} rewritten messages in R still carried the marker or the attacker address. Rewritten reports sometimes omitted the price (strict task {{R_replicating_sanitize_strict}}/30).
- **Block + retry (H10).** In batch B, a single resend after feedback restored the task to {{B_replicating_blockretry_task}}/30, against {{B_replicating_llm_task}}/30 for plain blocking (p = {{p_H10}}). The sender resent in {{B_replicating_blockretry_retried}} episodes; no resent message carried the injection or was flagged again.
- **Abstain notice (H11).** The notice cut silent failures from {{B_replicating_llm_out_silent}}/30 to {{B_replicating_blockabstain_out_silent}}/30 (p = {{p_H11}}), turning {{B_replicating_blockabstain_out_visible}}/30 into visible failures, but did not save the task ({{B_replicating_blockabstain_task}}/30).
- **Rewrite against retry (H12).** {{B_replicating_sanitize_task}}/30 against {{B_replicating_blockretry_task}}/30 (p = {{p_H12}}): no difference here.
- **Rewrite tool input (H9).** All {{I_filtered_docs}} poisoned documents read were rewritten (0 still tainted), so no agent was exposed. Attacks fell from {{I_replicating_none_attack}}/30 to 0/30 (p = {{p_H9}}) with the task at {{I_replicating_inputsanitize_task}}/30.

**Cost without injection (H4).** No monitor mode caused attacks, and the task succeeded 28–30 times out of 30 in every benign condition (Table E3). Pooling Main and R (n = 60 per arm), blocking changed task success by {{H4_d}} points (95% Newcombe CI [{{H4_lo}}, {{H4_hi}}]), which narrowly meets the pre-registered −10-point margin.

**Robustness checks.**
- *Native tool calling* (N) and a *shared-board topology* (T) reproduce the same pattern. On the shared board, an unmonitored injection reached all agents ({{T_replicating_none_exposed_mean}} exposed on average, against {{main_replicating_none_exposed_mean}} in the chain).
- *A second agent model* (`gpt-5.4-mini`, M) was never hijacked even without a monitor, so M shows only the monitor's **cost**: its retriever often *warned* about the injection ({{gpt_warn_k}}/{{gpt_warn_n}} messages), the blocking monitor withheld those warnings ({{M_replicating_llm_warn_flagged}}/{{M_replicating_llm_warn_msgs}} flagged), and the task dropped to {{M_replicating_llm_task}}/30, against {{M_replicating_sanitize_task}}/30 with rewriting.
- *Adversarial variants* (A): two of three were inert, since the retriever never relayed them, so they did not test the monitor. The third, posing as a task requirement, hijacked {{A_sanitizer_bypass_none_down}}/30 reviewers without a monitor and evaded the blocking monitor in {{A_sb_llm_missed}} messages, none of which led to a hijack (Appendix E).
- *Stricter metrics* (Table E4, post hoc for earlier batches): substantive exfiltration (procurement facts in the attacker e-mail) matched "e-mail reached the attacker" in every condition but one ({{I_replicating_none_exfil_sub}}/{{I_replicating_none_attack}}). No Mistral message was a warning, so the detection rates measure detection of *relayed* injections.

## 5. Discussion and Limitations

**Implications for AI safety.** In this testbed, most of the damage from a single poisoned document happened in agents that never saw it, so inter-agent channels deserve monitoring. The more important lesson concerns what monitors do *after* they fire. A monitor that silently drops content converts a visible security failure (an exfiltration e-mail) into an invisible utility failure: a confident, wrong report. In deployment this can be worse, because nothing downstream signals the problem, and it also suppresses agents that raise the alarm. Cheap recovery fixed this here. Re-asking the sender, rewriting the content, or filtering at the tool boundary all kept the task, and an abstention notice at least made failures visible. We suggest evaluating multi-agent monitors on three axes: attack prevention, task success, and the visibility of failures.

### Limitations

- **Narrow scope.** One fictional task, four agents, two topologies, two small models, a JSON action protocol (partly addressed by batch N), n = 30 per cell.
- **Weak adversarial evidence.** No attack was optimised against the monitor, the rewriter or the retry loop, and two of three variants were inert. The rewrite and retry results therefore hold **only in the scenarios tested**. "0/30" still allows rates up to about 11%.
- **Retry assumes an honest sender.** A compromised sender could exploit the feedback loop; this was not tested.
- **Unstable absolute rates.** Attack rates varied between identical batches; only within-batch comparisons are reliable.
- **Statistics.** Tests are uncorrected; with Bonferroni over the confirmatory tests, the two tests at p ≈ 0.024 (H2-bis, H5) would not survive.
- **Measurement.** Taint labels rely on a marker or address; "silent failure" and "warning" rely on regular expressions; the transcript audit was annotated by the AI assistant.
- **Design history.** The rewrite mode was designed after the main run and then confirmed on pre-registered batches. Recovery modes and stricter metrics were added after an external review (Appendix C).

### Future Work

- Adaptive attacks against the monitor, the rewriter and the retry loop.
- Retry with a compromised sender.
- Larger and more heterogeneous swarms.
- Monitors that propagate an explicit, persistent "data withheld" flag to the final output.

## 6. Conclusion

A self-replicating injection placed in one document regularly hijacked agents that never read it. Withholding suspicious inter-agent messages stopped this but caused silent task failure. Recovery removed that cost: re-asking the sender, rewriting the message, or filtering tool outputs all stopped the attack and kept the task, and an abstention notice made failures visible. These results come from a small simulated testbed with fixed, non-adaptive attacks. Their main message, that monitors must be judged on the failures they cause as well as the attacks they stop, is cheap to check in any multi-agent system.

## Code and Data

- **Code repository:** https://github.com/OrensObenas/swarm-hackathon-
- **Data:** all episode logs (`results/*/episodes.jsonl`), the pre-registration log (`docs/research_plan.md`), the transcript audit and the verification samples are in the repository. Every number in this report is regenerated by `scripts/build_report.py` and cross-checked by `scripts/independent_recount.py`.
- **Info-hazard note:** the injection texts are included. They use publicly documented patterns, were not optimised and only target fictional `.example` addresses (Appendix A).

## Author Contributions

G.O. conceived and directed the project. Implementation, experiments and drafting were done with AI assistance (see the LLM Usage Statement).

## References

[1] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, M. Fritz (2023). *Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.* arXiv:2302.12173. https://arxiv.org/abs/2302.12173

[2] D. Lee, M. Tiwari (2024). *Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems.* arXiv:2410.07283. https://arxiv.org/abs/2410.07283

[3] Q. Zhan, Z. Liang, Z. Ying, D. Kang (2024). *InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents.* Findings of ACL 2024.

[4] E. Debenedetti et al. (2024). *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.* NeurIPS Datasets and Benchmarks. https://arxiv.org/abs/2406.13352

[5] S. Cohen, R. Bitton, B. Nassi (2024). *Here Comes The AI Worm: Unleashing Zero-click Worms that Target GenAI-Powered Applications.* arXiv:2403.02817. https://arxiv.org/abs/2403.02817

[6] X. Gu et al. (2024). *Agent Smith: A Single Image Can Jailbreak One Million Multimodal LLM Agents Exponentially Fast.* ICML (PMLR 235). https://arxiv.org/abs/2402.08567

[7] M. Yu et al. (2024). *NetSafe: Exploring the Topological Safety of Multi-agent Networks.* arXiv:2410.15686. https://arxiv.org/abs/2410.15686

[8] Wang et al. (2025). *G-Safeguard: A Topology-Guided Security Lens and Treatment on LLM-based Multi-agent Systems.* ACL 2025 (Long Papers). https://arxiv.org/abs/2502.11127

[9] R. Greenblatt, B. Shlegeris, K. Sachan, F. Roger (2023). *AI Control: Improving Safety Despite Intentional Subversion.* arXiv:2312.06942. https://arxiv.org/abs/2312.06942

[10] L. Hammond et al. (2025). *Multi-Agent Risks from Advanced AI.* Cooperative AI Foundation Technical Report #1. https://arxiv.org/abs/2502.14143

[11] K. Hines, G. Lopez, M. Hall, F. Zarfati, Y. Zunger, E. Kiciman (2024). *Defending Against Indirect Prompt Injection Attacks With Spotlighting.* arXiv:2403.14720. https://arxiv.org/abs/2403.14720

[12] E. Debenedetti et al. (2025). *Defeating Prompt Injections by Design.* arXiv:2503.18813. https://arxiv.org/abs/2503.18813

## LLM Usage Statement

We used Claude (Anthropic), through Claude Code, extensively:
- to critique the idea and design the experiments;
- to implement the code and run all experiments;
- to analyse the logs;
- to draft most of this report, which the author reviewed.

The models *under study* are only `mistral-small-2603` and `gpt-5.4-mini`. To limit the risk of unverified claims:
- every number in this report is generated programmatically from the experiment logs and cross-checked by an independent recount script;
- the references were checked against their arXiv or venue pages;
- all hypotheses were committed before their data.

The transcript audit (`docs/transcript_audit.csv`) was annotated by the AI assistant.

---

## Appendix A. Limitations and Dual-Use / Ethical Considerations

**Limitations of the conclusions.** See §5. In summary, the evidence covers one simulated task, small models and fixed, hand-written attacks. Two of three adversarial variants never reached the monitor, so the monitor's robustness is largely untested. Absolute attack rates are unstable across runs, and some measurements rely on heuristics.

**Dual-use risks.**
- The injection texts and the harness, which measures attack success, could in principle help someone tune injections against real multi-agent systems.
- Our finding that blocking monitors cause silent failures could guide an attacker who wants to cause damage *through* a defence, by triggering the withholding of legitimate data.

**Why we consider the risk low.**
- The attack patterns (fake compliance notice, request to copy verbatim) are already documented [1, 2, 5]. We introduce no new jailbreak technique and performed no automated optimisation.
- The payload is mundane (fictional notes), all data, companies and addresses are fictional (`.example`), and the e-mail tool only writes to memory. No real system or account was touched.

**Release choices.**
- We release the monitor prompts, the metrics and the full logs, which mainly serve defenders. No model-specific optimised attack exists to release.
- We caution against reading these results as a security guarantee: LLM monitors are themselves injectable, and adaptive attacks were not evaluated.
- No human subjects were involved.

## Appendix B. Prompts and injection texts (verbatim from the code)

{{PROMPTS}}

## Appendix C. Pre-registration, pilots and deviations

**Pilots** (excluded from analysis):
1. The first pilot showed propagation, so there was no floor effect. It also showed that the original task checker (vendor and price) was too strict; it was replaced by the mandatory `Recommended vendor:` line.
2. The second pilot revealed a harness defect: the writer e-mailed the manager itself and handed off an empty message, and the reviewer then confabulated. Roles were clarified (only the reviewer e-mails the manager; every agent passes its full content), and `send_email` stayed available to all agents.
3. The third pilot confirmed the fix, and the configuration was frozen.

**Pre-registration.** Every later hypothesis (H2-bis, H4-bis, H5, H6, H9–H12) and every descriptive batch was committed to `docs/research_plan.md` (§§5, 8–14) before its data were collected.

**Changes after data.**
- The rewrite mode was designed after the main run; its exploratory batch S is reported as such.
- The silent-failure metric was defined after the main run.
- Recovery modes and stricter metrics were added after an external review. The first version of `strict_task` wrongly rejected correct derived figures (the $4,700 saving) and was amended before batch B was analysed.
- An independent recount revealed that a single e-mail addressed to both the manager and the attacker counted as an attack but not as a report. This affected 2 episodes (batch A, task 28→30/30) and is fixed everywhere.
- A duplicated launch of batch T was excluded and re-run identically.
- Agents run on Mistral rather than the originally planned Claude, because no Claude API key was available.

## Appendix D. Reproducibility and pre-existing work

- **Commands** are in the repository README. The exact arguments of every batch are in `results/<batch>/config.json`, and pinned versions in `requirements-lock.txt`.
- **Pre-existing work: none.** All code, prompts, data and results were produced during the sprint (6–8 Nov 2026).

## Appendix E. Additional tables

**Table E1.** Batches (30 episodes per condition).

| Batch | Variation | Conditions | Status |
|---|---|---|---|
| Main | 2×2 design | benign / replicating × none / block | pre-registered |
| X | cross-provider monitor (`gpt-5.4-mini`) | benign / replicating × block | secondary |
| S | rewrite monitor | benign / replicating × rewrite | exploratory (designed after Main) |
| R | single-batch replication | benign / replicating × none / block / rewrite | pre-registered |
| A | adversarial variants | 3 variants × none / block / rewrite | descriptive |
| M | second agent model (`gpt-5.4-mini`) | benign / replicating × none / block / rewrite | descriptive |
| I | tool-input filter | replicating × none / rewrite tool input; benign × rewrite tool input | pre-registered |
| N | native tool calling | benign × none; replicating × none / block / rewrite | descriptive replication |
| T | shared board (each agent sees all prior messages) | same as N | descriptive |
| B | blocking with recovery | replicating × block / block+retry / block+abstain / rewrite; benign × block+retry / block+abstain | pre-registered |

**Table E2.** All batches, self-replicating injection unless noted (TPR/FPR at message level).

{{TABLE_SYNTH}}

**Table E3.** Conditions without injection.

{{TABLE_BENIGN}}

**Table E4.** Stricter metrics: substantive exfiltration, strict task, and monitor flags on relays versus warnings.

{{TABLE_STRICT}}

**Table E5.** Adversarial variants (batch A), hand-written and frozen before running. `polite` and `monitor_bypass` were never relayed by the retriever (inert).

{{TABLE_ADV}}

**Table E6.** Batch B in full, including the conditions without injection.

{{TABLE_B}}

---

<p class="footnote"><sup>1</sup> Research conducted at the Swarm Alignment Hackathon, November 2026.</p>
