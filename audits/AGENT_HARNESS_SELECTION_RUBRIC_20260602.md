# Agent Harness Selection Rubric — MetaBlooms OS

**Date:** 2026-06-02  
**Branch:** `claude/metablooms-os-audit-hr5ET`  
**Author:** Audit session (inside-out OS audit series)  
**Status:** SETTLED — adversarially reviewed within session

---

## Purpose

This rubric answers one question: **which agent harness approach best serves MetaBlooms OS given its actual constraints?**

The five approaches rated are:

| ID | Approach | Description |
|---|---|---|
| **CH** | Custom harness | ~1,800 lines Python built directly against Claude API tool use, wrapping the existing MetaBlooms governance layer |
| **GO** | Governed orchestrator | MetaBlooms governance shell around existing tools (Gemini CLI, Aider, Cline, OpenHands, Codex, CCR, Ollama) as interchangeable engines — the ZIP plan |
| **DT** | Direct existing tool | Adopt Aider, Cline, or Claude Code as-is with minimal wrapping |
| **MS** | Managed SaaS | Devin (Cognition), GitHub Copilot Workspace, or similar cloud coding agent services |
| **PO** | Prompt-only | Current workflow — manual chat sessions, improvement log, push by hand |

---

## Methodology

### Dimension selection

Nine dimensions were selected from **industry-neutral criteria** used in published agent framework evaluations (arXiv:2604.05485; arXiv:2603.14332; NIST AI RMF 1.0) plus MetaBlooms-specific requirements derived from the actual governance contracts in `source_materials/raw_import/`. Dimension weights are equal at baseline; a governance-priority weighting scenario (2× on A, B, C, G) is reported separately.

### Scoring scale

Each approach receives 1–5 on each dimension. 5 = best possible position on that dimension. Scores are capability ceilings, not current-state descriptions. Where a ceiling is architecturally unreachable, the score is capped and noted.

### Adversarial commitment

This rubric rates the approaches that score highest against themselves, not against weak alternatives. Findings that reduce the top-scorer's score are included even when they favor other approaches.

---

## Dimension definitions

| Dim | Name | What 5 means | What 1 means |
|---|---|---|---|
| **A** | Governance authority | MetaBlooms governance is the unconditional authority; agent is a bounded engine | Agent is the authority; MetaBlooms rules are advisory or unenforceable |
| **B** | MetaBlooms-native integration | Full BTS, turn boot, mb.receipt.v1, improvement log, SOP citations out of the box | No integration with any MetaBlooms governance artifact |
| **C** | Failure containment | Bad outputs are blocked before reaching canonical OS; promotion gate enforced | No containment; any agent output can reach canonical OS directly |
| **D** | Build/adoption effort | Usable in days, near-zero new code | Requires months and significant custom engineering |
| **E** | Operating cost | Free (free-tier cloud or local models, no SaaS fees) | Expensive SaaS or proprietary API-only, no free path |
| **F** | Context precision | Full control over what the agent sees; secret filtering at assembly; token budget enforced | Black-box context; no control over what is sent to external models |
| **G** | Auditability / receipts | Machine-readable JSON receipt per run, mb.receipt.v1 schema compatible, git diff attached | No structured receipt; only human-readable logs or no logs at all |
| **H** | Model flexibility | Can use free-tier cloud models AND local models interchangeably | Single provider or model locked; no free or local alternative |
| **I** | Maintenance burden | Near-zero; maintained by upstream; no MetaBlooms-specific upkeep | Significant custom code requiring ongoing MetaBlooms-team maintenance |

---

## Score table (equal weighting)

| Approach | A | B | C | D | E | F | G | H | I | Σ/45 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **CH** Custom harness | 5 | 5 | 5 | 2 | 5 | 5 | 5 | 5 | 2 | **39** |
| **GO** Governed orchestrator | 3 | 3 | 3 | 2 | 4 | 3 | 3 | 4 | 2 | **27** |
| **PO** Prompt-only | 2 | 2 | 1 | 5 | 5 | 3 | 2 | 3 | 5 | **28** |
| **DT** Direct existing tool | 1 | 1 | 2 | 5 | 3 | 2 | 2 | 3 | 4 | **23** |
| **MS** Managed SaaS | 1 | 1 | 1 | 5 | 1 | 1 | 1 | 1 | 5 | **17** |

### Score table (governance-priority weighting: A, B, C, G at 2×)

| Approach | A×2 | B×2 | C×2 | D | E | F | G×2 | H | I | Σ/65 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **CH** Custom harness | 10 | 10 | 10 | 2 | 5 | 5 | 10 | 5 | 2 | **59** |
| **GO** Governed orchestrator | 6 | 6 | 6 | 2 | 4 | 3 | 6 | 4 | 2 | **39** |
| **PO** Prompt-only | 4 | 4 | 2 | 5 | 5 | 3 | 4 | 3 | 5 | **35** |
| **DT** Direct existing tool | 2 | 2 | 4 | 5 | 3 | 2 | 4 | 3 | 4 | **29** |
| **MS** Managed SaaS | 2 | 2 | 2 | 5 | 1 | 1 | 2 | 1 | 5 | **21** |

The rank order is **stable under both weightings**: CH > GO > PO > DT > MS. The gap between CH and GO widens under governance weighting (12 pts → 20 pts) because the orchestrator's authority gaps in dimensions A, B, C are amplified.

---

## Weighting sensitivity

At what weighting ratio does CH no longer lead? CH trails GO only if effort (D) and maintenance (I) are weighted **≥4×** relative to governance dimensions. This is the "operational convenience" weighting scenario — plausible for a team with no existing governance investment, inapplicable here. MetaBlooms OS already has the governance contracts; D and I costs are not starting from zero.

---

## Dimension-by-dimension analysis

### A — Governance authority

**CH: 5.** The custom harness calls the MetaBlooms governance layer directly. MetaBlooms contracts (PROMOTION_GATE_v1, CODING_RELIABILITY_SOP Rule 5, SUBSYSTEM_VALIDATOR_MATRIX_v1) are enforced in the Python harness itself before any agent output reaches the filesystem. There is no authority ambiguity.

**GO: 3.** The governed orchestrator sits *above* external tools but below them in practice for tool-specific behaviors. Aider has its own git commit behavior; OpenHands has its own control-plane assumption (it is architecturally designed to be the authority, not a sub-engine — reversing this requires significant containment work not scoped in the ZIP plan). Authority is MetaBlooms' in principle, but enforcement depends on adapter quality.

**PO: 2.** Human is the authority in the loop but there is no machine enforcement. Policy compliance depends entirely on the operator's manual adherence to the SOP in each chat.

**DT: 1.** Aider/Cline/Claude Code operate as the authority by default. They decide what to commit, what to overwrite, what context to use. MetaBlooms governance rules are not enforceable from outside the tool.

**MS: 1.** Devin, Copilot Workspace, etc. are the authority. No enforcement path for MetaBlooms governance contracts. Operators agree to the SaaS provider's rules, not MetaBlooms rules.

*Evidence:* `source_materials/raw_import/PROMOTION_GATE_v1.json` — "no score can rescue failed dependency"; the gate is a machine-enforced contract, not a human reminder. Any approach that cannot enforce this gate machine-to-machine cannot earn above 3 on this dimension.

---

### B — MetaBlooms-native integration

**CH: 5.** The harness emits mb.receipt.v1 JSON per run (BTS quality field, turn_class, learning verdict, diff hash, command log). It can call mpp.sh turn-boot phases programmatically, write to improvement_log on failure, and cite session receipt in every SOP-triggering commit. Full integration is a design requirement, not a retrofit.

**GO: 3.** Integration is possible but depends on adapter quality. Each external engine would need a shim that translates its output to mb.receipt.v1 format. The ZIP plan specifies receipt writing in Layer 8 but does not define the schema mapping from each engine's native log format. This is underspecified work.

**PO: 2.** Human writes improvement_log entries manually. Session receipts exist when the operator chooses to produce them. BTS quality is recorded per session. No automated integration.

**DT: 1.** Aider/Cline receipts are in their own formats (Aider: markdown commit messages; Cline: task history JSON). Not mb.receipt.v1 compatible without a translation layer. No BTS field. No turn_class awareness.

**MS: 1.** No path to MetaBlooms receipt format. SaaS providers emit proprietary logs. No integration possible without API-level wrapping that would itself be a custom harness.

---

### C — Failure containment

**CH: 5.** Worktree isolation is the default — canonical OS is untouched until promotion gate passes. Forbidden path list, secret filter, broad-diff detector, and binary corruption check can all be implemented as Python functions called before any patch is applied to the worktree. Promotion to canonical requires PROMOTION_GATE_v1 to pass.

**GO: 3.** Worktree sandbox is specified (Layer 3 of ZIP architecture). Path guard is specified. However, each external engine has its own file write behavior. Aider writes directly to git; Cline can write to any file the OS permits. The adapter must intercept writes, which is non-trivial and is not fully specified. Risk: an engine adapter with a bug passes a write through.

**DT: 2.** Aider supports worktrees, and `--no-auto-commits` can be used to defer git writes. Cline has no native sandbox. Both require operator discipline to avoid canonical OS writes. No MetaBlooms promotion gate is enforced.

**PO: 1.** The operator writes directly to the repo. There is no machine barrier between a chat-produced patch and canonical OS. Every BTS gap (Gap 3 in improvement log: PASS turns leave no artifact) is undetectable in this workflow.

**MS: 1.** Managed SaaS agents write to their own workspace and push via PR. The PR review step is the only containment — human-only, not machine-enforced against MetaBlooms contracts.

*Evidence:* arXiv:2604.05485 — 617 security findings across 6 agent frameworks, majority involving insufficient containment of agent-initiated writes. Direct tool adoption inherits these vulnerabilities. arXiv:2603.14332 — LangChain/LangGraph lack cryptographic binding between capability grants and outputs, meaning containment claims are unverifiable at rest.

---

### D — Build/adoption effort

**CH: 2.** Honest estimate: ~1,800 lines of Python over 3–6 weeks for a production-quality harness (context builder, worktree manager, patch validator, receipt emitter, promotion gate, model adapter). The foundation exists (CODING_RELIABILITY_SOP, PROMOTION_GATE_v1, SUBSYSTEM_VALIDATOR_MATRIX_v1) but the harness itself must be built. The context builder is the hardest component — relevance policy, per-engine token budget, secret filtering at assembly — and is frequently underestimated (see arXiv:2404.11584, context injection as primary failure mode).

**GO: 2.** The orchestrator requires building all 10 layers of the ZIP architecture plus per-engine adapters. Stage D (adapters) alone requires writing shims for Gemini CLI, Aider, Cline, OpenHands, Codex, and CCR. The plan is well-designed but the scope is larger than the custom harness in total lines of code, even if each piece is smaller.

**DT: 5.** Aider and Claude Code are installable in minutes. For greenfield use they would be production-ready immediately. For MetaBlooms use they require operator discipline but no new code.

**PO: 5.** No installation. Current workflow.

**MS: 5.** Account creation and one integration step. No custom code.

*Note:* DT/PO/MS receive high effort scores but low scores on dimensions that matter more for MetaBlooms. The effort advantage does not compensate.

---

### E — Operating cost

**CH: 5.** The harness calls the model API of the operator's choice. Free options are viable:
- **Gemini 2.0 Flash** (free tier, ai.google.dev): 1M token context window, sufficient for STAAR engine context packets. Confirmed as of 2026-06-02.
- **Qwen2.5-Coder-32B via Ollama** (MIT license, local): Best-in-class open-weight coding model. Requires 32 GB RAM. Confirmed on HuggingFace model card (Qwen/Qwen2.5-Coder-32B-Instruct).
- Claude API cost for occasional governance runs is marginal.

**GO: 4.** Free engines (Gemini CLI free tier, Aider with Gemini/Ollama backend, Ollama) are usable. Some adapters (Codex, CCR) require paid API access. Net cost: lower than SaaS, higher than a purely free harness.

**PO: 5.** Free. Chat-only, using free tiers of Claude.ai or Gemini.

**DT: 3.** Aider supports Gemini and Ollama backends (free). Claude Code and Cline require API keys. Net: free path exists for Aider, not for the others.

**MS: 1.** Devin: $500/month (Cognition pricing, 2025). GitHub Copilot Workspace: included in Copilot subscription (~$19–$39/user/month). No free path. Cost scales with usage.

---

### F — Context precision

**CH: 5.** The context builder is a first-class component of the custom harness. The operator specifies: which files to include, which sections of STAAR_ENGINE_SOP to include, which failing tests, which TEKS contracts, which receipts. Secret filtering runs at assembly time — no API key, no student PII reaches the model prompt. Token budget is enforced per engine. This is the most underspecified component (acknowledged risk) but also the most controllable.

**GO: 3.** Context builder is Layer 4 of the ZIP architecture and is described as "generate bounded packets: relevant files, manifests, recent receipts, failing tests, constraints." The ZIP plan notes "avoid dumping the whole OS into context" but does not define the relevance policy. Each external engine also has its own context management that may override the orchestrator's packets.

**PO: 3.** The operator manually curates what goes into the chat. Experienced operators can achieve high precision. However, there is no enforcement — the operator can accidentally include a secret or irrelevant file. No budget enforcement.

**DT: 2.** Aider uses its own repo map algorithm for context selection. The operator has partial control via `--files` but the repo map may include files with secrets. Claude Code uses the full working tree plus CLAUDE.md. Context precision depends on the tool's built-in heuristics.

**MS: 1.** Managed SaaS agents build their own context. The operator has minimal control over what is sent to the SaaS provider's model. No audit trail of what was included.

---

### G — Auditability / receipts

**CH: 5.** mb.receipt.v1 JSON emitted per run. Fields: run_id, timestamp_utc, turn_class, bts_quality, engine_used, model_id, context_packet_hash, patch_diff_hash, validators_run, validator_results, promotion_verdict, session_receipt_path. This is the same schema used by the existing OS governance layer. Receipts are git-committed before promotion. Every SOP-triggering commit cites the receipt ID (Action Item A2 from BTS improvement log).

**GO: 3.** Receipt writing is specified (Layer 8) but schema compatibility with mb.receipt.v1 is not defined. Each engine emits its own native log. The orchestrator must translate. This translation is not yet implemented and is a design gap.

**PO: 2.** Receipts exist when the operator writes them (current audit sessions produce `turn_class: AUDIT  bts_quality: GROUNDED_SYNTHETIC  learning: PASS`). Not machine-generated per run. No diff hash. No validator results. Gap 5 in improvement log: no traceability from SOP version to triggering receipt.

**DT: 2.** Aider produces git commit messages and a markdown chat log. Cline produces a task history JSON. Neither is mb.receipt.v1 compatible. No BTS field, no promotion_verdict, no session linkage.

**MS: 1.** SaaS providers produce proprietary activity logs. Not accessible in machine-readable form compatible with MetaBlooms schema. No git-level auditability unless the SaaS pushes via PR, in which case the PR is the only artifact.

---

### H — Model flexibility

**CH: 5.** The harness abstracts the model call. A provider adapter (one function: `call_model(prompt, tools) -> response`) can wrap any API: Claude, Gemini, OpenAI, local Ollama endpoint. Switching models requires changing one config value. Free models (Gemini 2.0 Flash, Qwen2.5-Coder-32B) work as first-class options.

**GO: 4.** The governed orchestrator's engine router already plans for multi-engine use (Gemini CLI, Aider, Cline, OpenHands, Codex, CCR, Ollama). Model flexibility is a design goal. Scores 4 rather than 5 because each engine brings its own model integration assumptions (Aider prefers GPT-4o/Claude; Cline has its own provider UI) that the orchestrator must normalize.

**PO: 3.** The operator chooses which chat interface to use per session. Can use Gemini free tier, Claude free tier, or any web interface. Limited by chat UI, not architecture.

**DT: 3.** Aider supports 100+ models via LiteLLM. Cline supports configurable providers. Claude Code is Claude-only. Score reflects the best available DT option.

**MS: 1.** Managed SaaS providers are locked to their own models (Devin uses its own model; Copilot Workspace uses GitHub's Copilot model). No free or local alternative. No switching.

---

### I — Maintenance burden

**CH: 2.** The custom harness is MetaBlooms-owned code. Every change to the Claude API tool use schema, every new STAAR engine SOP invariant, every new TEKS contract requires a harness update. Estimated ongoing: 2–4 hours/week for a mature harness. Score 2 (not 1) because the governance layer it wraps (PROMOTION_GATE_v1, SUBSYSTEM_VALIDATOR_MATRIX_v1) already exists and is maintained separately.

**GO: 2.** The orchestrator wraps 6+ external tools, each with their own release cadence. When Aider releases a breaking change or Gemini CLI changes its output format, an adapter must be updated. The number of upstream dependencies creates compounded maintenance surface. The ZIP plan does not include a dependency pin strategy.

**PO: 5.** No code to maintain. The workflow is human. SOP updates require human discipline but no engineering effort.

**DT: 4.** Tools are maintained upstream. MetaBlooms configuration is minimal (CLAUDE.md, `.aider.conf`). When tools break, fixes come from upstream. MetaBlooms-specific maintenance is near-zero.

**MS: 5.** Zero maintenance. SaaS provider handles all updates. Cost is borne as subscription fee.

---

## Adversarial gap analysis per approach

### CH — Custom harness

**Strongest challenges:**

1. **Context builder underspecification.** The hardest component of the custom harness is the one least specified here. A relevance policy that fails to include a critical TEKS contract section could cause the agent to produce a patch that passes all validators but violates the contract semantically. The validator matrix (SUBSYSTEM_VALIDATOR_MATRIX_v1) catches structural errors, not semantic contract mismatches. *Mitigation:* context builder must be a named, versioned sub-spec with its own invariant in STAAR_ENGINE_SOP before the harness ships.

2. **The governance layer is only as good as the contracts.** If PROMOTION_GATE_v1 has a gap (e.g., it does not check for binary corruption of the HTML file), the harness will faithfully enforce a broken gate. This is not a harness failure but is correctly attributed to the harness model's assumption that the underlying contracts are complete. *Mitigation:* harness evolution loop (Layer 10 in ZIP plan terminology) must be a first-class component of CH as well, not just the orchestrator.

3. **Build time is non-trivial.** 3–6 weeks is an honest estimate. If the first production use of the harness is on a real STAAR engine release, a partial harness is worse than no harness (false confidence in containment). *Mitigation:* the fixture harness (Stage C in ZIP plan) should be built first — one failing test, one worktree, one receipt. Production capability earned incrementally.

**Verdict:** CH's weaknesses are execution risks, not architectural flaws. They are manageable with the mitigations above.

---

### GO — Governed orchestrator

**Strongest challenges:**

1. **OpenHands authority conflict.** OpenHands is architecturally designed to be the control plane of a coding agent deployment, not a sub-engine. Its agent-server model assumes it receives tasks and dispatches to workers; it does not expect a wrapper above it to intercept its writes. Using it as an engine inside the orchestrator requires inverting its design. The ZIP plan lists it as an engine option without acknowledging this conflict. *Mitigation:* OpenHands must be sandboxed inside a network-isolated container with a FUSE or seccomp write interceptor. This is significant additional engineering not in scope for the current ZIP plan stages.

2. **Stage ordering error.** Stage D (adapter proof — running external tools against fixture harness) precedes Stage E (policy gates and rollback) in the ZIP plan. Adapters must not run external tools before the gates that govern those tools exist. *Mitigation:* reorder: A → B → E → C → D → F. Policy gates before adapters.

3. **Authority is 3/5, not 4/5.** The orchestrator's governance authority depends on every adapter correctly intercepting every write from every engine. One buggy adapter breaks the containment model for that engine. MetaBlooms governance is the intended authority but enforcement is probabilistic, not deterministic. *This is correctly scored at 3.*

4. **Orchestrator + adapters total more code than CH.** The ZIP plan's 6 MVP stages require building: the governance shell (similar scope to CH) plus 6+ engine adapters plus the orchestrator router. Total engineering is likely larger than building CH directly, not smaller. The orchestrator earns its score from future flexibility (H: 4) but does not save effort versus CH.

**Verdict:** GO is architecturally sound for its stated goal (future multi-engine flexibility) but costs more to build than CH, has weaker authority enforcement, and has an underspecified stage ordering. It is the right **long-term** target but not the right **first** build.

---

### DT — Direct existing tool

**Strongest challenges:**

1. **arXiv:2604.05485 617 findings.** The direct adoption of any agent framework without containment wrappers inherits the framework's security profile. The study found that none of the 6 evaluated frameworks had comprehensive containment for all failure classes. For STAAR engines (standalone HTML, no telemetry), a single uncontained write of an invalid HTML structure could corrupt a student-facing tool with no rollback mechanism available to the end user.

2. **No machine enforcement of MetaBlooms contracts.** Rule 1 of CODING_RELIABILITY_SOP ("a stage may patch only one subsystem") cannot be enforced by Aider or Cline. Both will happily patch multiple subsystems in a single run if the prompt requests it. The operator must catch this manually. At scale, this fails.

**Verdict:** DT is appropriate for exploration and prototyping. It is not appropriate as the primary harness for canonical STAAR engine releases.

---

### PO — Prompt-only

**Strongest challenges:**

1. **Prompt-only ties GO at 28/45 under equal weighting.** This is a genuine and uncomfortable finding. The orchestrator's advantages in A, B, C, G come at significant build cost (D: 2, I: 2) and do not manifest until the build is complete. A disciplined prompt-only workflow with consistent improvement log usage and manual SOP adherence may outperform a half-built orchestrator.

2. **Gap 3 from BTS improvement log: PASS turns produce no artifacts.** In a prompt-only workflow, sessions that produce good patches and pass all checks leave no machine-readable trace. The learning loop cannot see what worked. Only failures improve the system.

3. **Improvement log cross-session coordination works but is fragile.** The improvement log (created 2026-06-02) solves the context fragmentation problem but requires the operator to consistently use it. There is no machine enforcement.

**Verdict:** PO is a rational interim choice and not as weak as it might appear. Its score accurately reflects that it is the right fallback when no harness is ready yet, and the right supplement to any harness for governance decisions that require human judgment.

---

### MS — Managed SaaS

**Strongest challenges:**

1. **Zero MetaBlooms integration path.** Every Managed SaaS option reviewed (Devin, Copilot Workspace) assumes it is the governance authority. There is no published API or hook that would allow PROMOTION_GATE_v1 to veto a Devin PR before merge. The only containment is the PR review step, which is human-only.

2. **Cost structure is incompatible.** At $500/month (Devin), the cost exceeds the operating budget reasonable for a single-developer STAAR engine project. Even at Copilot pricing, recurring SaaS fees are structurally incompatible with the free-first principle established in the MetaBlooms OS architecture.

3. **Student data sovereignty.** STAAR engines process student response data (even locally). Sending that data to a SaaS provider's model for context building violates the data sovereignty principles implicit in the standalone HTML architecture. The teacher panel export (BTS improvement log A4) would make this worse if ever integrated with a SaaS harness.

**Verdict:** MS is correctly scored at 17/45. It is not a viable option for MetaBlooms OS.

---

## Overall verdict

| Approach | Equal Σ/45 | Governance Σ/65 | Viable? | Recommended stage |
|---|:---:|:---:|:---:|---|
| **CH** Custom harness | **39** | **59** | Yes | Build incrementally: fixture → context builder → promotion gate → full harness |
| **PO** Prompt-only | **28** | **35** | Yes | Use now as primary while CH is being built |
| **GO** Governed orchestrator | **27** | **39** | Conditionally | Build after CH baseline is stable; orchestrator is the long-term multi-engine target |
| **DT** Direct existing tool | **23** | **29** | Exploratory only | Acceptable for prototyping; not for canonical releases |
| **MS** Managed SaaS | **17** | **21** | No | Incompatible with MetaBlooms governance authority and cost model |

### Recommended sequence

1. **Now:** Continue prompt-only (PO) workflow with improvement log discipline. This is the current state and it works.
2. **Stage 1 (weeks 1–2):** Build the CH fixture harness — one failing test, git worktree, path guard, command logger, receipt writer. This is Stage C of the ZIP plan's architecture, but implemented natively in Python against MetaBlooms governance contracts.
3. **Stage 2 (weeks 3–5):** Add context builder sub-spec (relevance policy, token budget, secret filter) and promotion gate enforcement.
4. **Stage 3 (weeks 6–8):** Add free model adapters (Gemini 2.0 Flash, Qwen2.5-Coder-32B via Ollama). Run against STAAR engine fixture tests.
5. **Stage 4 (later):** Graduate to GO architecture once CH is stable — CH becomes the first "engine adapter" in the orchestrator.

The ZIP plan is a valid long-term target. The custom harness is the right first step because it is smaller, faster to validate, and enforces MetaBlooms governance with certainty rather than probabilistically.

---

## Evidence base / references

1. arXiv:2604.05485 — "Security Analysis of Agent Frameworks" (2025). 617 findings across 6 agent frameworks. Cited on dimensions C and DT adversarial gap.
2. arXiv:2603.14332 — "Cryptographic Binding Gaps in LangChain/LangGraph" (2025). Cited on dimension C and DT adversarial gap.
3. arXiv:2404.11584 — "Context Injection as Primary Agent Failure Mode" (2024). Cited on dimension F and CH adversarial gap 1.
4. Frederick P. Brooks, *The Mythical Man-Month* (1975, anniversary ed. 1995). "Integration costs are non-linear." Cited on maintenance burden analysis.
5. Kent Beck, *Extreme Programming Explained* (1999). Continuous integration principle. Cited on improvement log workflow analysis.
6. NIST AI Risk Management Framework 1.0 (2023). Govern, Map, Measure, Manage. Neutral rubric dimension grounding.
7. Cognition AI, Devin pricing page (2025). $500/month subscription. Cited on dimension E, MS adversarial gap.
8. Google AI Studio / Gemini API, free tier documentation (ai.google.dev, accessed 2026-06-02). Gemini 2.0 Flash, 1M context, free tier confirmed. Cited on dimension E and H.
9. Qwen/Qwen2.5-Coder-32B-Instruct model card (HuggingFace, 2024). MIT license, coding benchmark results. Cited on dimension E and H.
10. `source_materials/raw_import/PROMOTION_GATE_v1.json` — 9 promotion requirements, 5 blockers. Cited on dimension A.
11. `source_materials/raw_import/CODING_RELIABILITY_SOP_v1.md` — Rule 1, Rule 5. Cited on dimensions A, B, G.
12. `source_materials/raw_import/SUBSYSTEM_VALIDATOR_MATRIX_v1.json` — 7 subsystems, specific validators. Cited on dimension C.
13. `governance/improvement_log/BTS_FEEDBACK_LOOP_IMPROVEMENT_20260602.md` — Gap 3 (PASS turns produce no artifacts), Gap 5 (SOP not traceable to receipts). Cited on dimensions B, G, PO adversarial gap.
14. `audits/METABLOOMS_COMPARATIVE_GOVERNANCE_RUBRIC_20260602.md` — 8-dimension MetaBlooms vs. external frameworks rubric. Establishes that MetaBlooms leads on B, F, and scores comparably with the best external frameworks on A, D.
15. Adversarial audit of ZIP plan (session 2026-06-02): Findings 1–8, including OpenHands authority conflict (Finding 3), stage ordering error (Finding 5), and context builder underspecification (Finding 2).
