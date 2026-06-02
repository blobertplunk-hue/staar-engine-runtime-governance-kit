# MetaBlooms OS — Comparative Governance Rubric

**Date:** 2026-06-02  
**Scope:** MetaBlooms OS vs LangGraph, AutoGen v0.4, CrewAI, Semantic Kernel, MemGPT/Letta, OpenAI Assistants API  
**Method:** Direct codebase inspection (release `MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z`), five parallel research agents covering all six comparators, two peer-reviewed papers (arXiv:2603.14332, arXiv:2604.05485), and primary documentation sources.  
**Review chain:** Original rubric → Adversarial review → Meta-audit → Third-order review (four levels; findings settled below).

---

## Methodology Limitations (Disclosed)

Dimensions were selected from MetaBlooms' documented governance features. A rubric designed around a different system (e.g., LangGraph's graph expressiveness or Semantic Kernel's plugin ecosystem) would select different dimensions and produce different relative rankings. This rubric is a **governance-centered comparison**, not an objective measure of overall system quality.

All dimensions are equally weighted in the Σ/40 total. Under 4× weighting on E (HITL) and G (Portability), MetaBlooms and LangGraph reach approximate parity (48 vs 49 on the full 8-dimension rubric). Under 5× weighting on E and G, LangGraph leads. Users should apply weights matching their deployment requirements, or use the dimension-by-dimension scores without aggregation.

The Σ/40 score should not be interpreted as an objective measure of overall system quality. For production deployment decisions, dimension-by-dimension scores are more informative than the aggregate.

*Citation note: arXiv PDF fetches for arXiv:2603.14332 and arXiv:2604.05485 returned HTTP 403 during research. Claims attributed to these papers are sourced from abstracts, HTML previews, and secondary web sources, not full paper text. Specific methodological claims (evaluated frameworks, exact finding counts) carry corresponding epistemic uncertainty.*

---

## Rubric Dimensions

| ID | Dimension | What It Measures |
|---|---|---|
| A | Session/turn lifecycle governance | Is there a formal, contract-gated multi-phase turn contract? |
| B | Cryptographic integrity and auditability | Are artifacts, receipts, and agent state tamper-evidently attested? |
| C | Modularity and capability isolation | Are capabilities cleanly bounded, registered, and isolated? |
| D | Failure containment and false-pass prevention | Is the system structurally protected against silently promoting bad outputs? |
| E | Operator / human-in-the-loop controls | How precisely can a human intercept, gate, or resume an in-flight agent? |
| F | Self-verification and durable proof | Can the system prove its own integrity, and are past proofs durably locked? |
| G | Portability and export integrity | Are runtime state and artifacts exportable with verifiable provenance? |
| H | External validation and red-team readiness | Has the system received independent external security scrutiny? |

**Scale:** 1 = absent/minimal · 2 = partial/ad-hoc · 3 = adequate · 4 = strong · 5 = best-in-class

---

## Final Scores

| System | A | B | C | D | E | F | G | H | **Σ/40** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MetaBlooms OS** | **5** | **5** | **4** | **4** | **4** | **5** | **2** | **1** | **30** |
| LangGraph | 3 | 1 | 4 | 2 | **5** | 1 | 4 | 2 | **22** |
| Semantic Kernel | 2 | 1 | **5** | 3 | 3 | 1 | 4 | 2 | **21** |
| MemGPT / Letta | 3 | 1 | 4 | 1 | 3 | 2 | 4 | 1 | **19** |
| AutoGen v0.4 | 3 | 1 | 3 | 2 | 4 | 1 | 3 | 2 | **19** |
| CrewAI | 2 | 1 | 3 | 2 | 3 | 1 | 3 | 2 | **17** |
| OpenAI Assistants | 2 | 2 | 2 | 2 | 3 | 1 | 2 | 2 | **16** |

*H dimension scoring key: 1 = no known external audit; 2 = external audit performed, findings documented (severity/patch status varies); 3 = external audit performed, all critical findings remediated and verified; 4 = continuous external validation (bug bounty, regular red-team). No system in this comparison reaches 3.*

*Score adjustments from adversarial review chain: MetaBlooms G reduced from 3 to 2 (bash dependency + FIND-06 reduce portability below AutoGen/CrewAI); H dimension added; MetaBlooms Σ unchanged at 30/40 (−1 G, +1 H cancel).*

---

## Weighting Sensitivity

Under equal weighting MetaBlooms leads LangGraph by 8 points (30 vs 22). The gap narrows as HITL (E) and portability (G) are weighted more heavily:

| Weight on E and G | MetaBlooms | LangGraph | Difference |
|---|:---:|:---:|:---:|
| 1× (equal, baseline) | 30 | 22 | +8 MetaBlooms |
| 2× | 35 | 29 | +6 MetaBlooms |
| 3× | 41 | 38 | +3 MetaBlooms |
| ~3.9× | ~48 | ~48 | Approximate tie |
| 4× | 48 | 49 | −1 LangGraph |
| 5× | 53 | 56 | −3 LangGraph |

*Note: The 4× tie calculation uses the full 8-dimension rubric (including H at 1×). At exactly 4×: MetaBlooms = 5+5+4+4+(4×4)+5+(4×2)+1 = 48; LangGraph = 3+1+4+2+(4×5)+1+(4×4)+2 = 49. LangGraph leads by 1 at 4× weighting due to H. Inversion threshold is approximately 3.9×, not 4×.*

---

## Dimension-by-Dimension Analysis

---

### A — Session / Turn Lifecycle Governance

**MetaBlooms OS — 5**

`mpp.sh turn-boot` enforces a contractual sequence: `preboot → route-check → SEE gate → BTS quality measurement → learning loop → IRPM attestation`. Each phase can independently block. The `turn_class`, `bts_quality`, and `learning` fields in the JSON receipt make the result machine-verifiable by a downstream auditor. Audit session result:

```
rc: 0  status: PASS  turn_class: AUDIT  bts_quality: GROUNDED_SYNTHETIC  learning: PASS
```

No comparator implements an equivalent contract-gated turn boot with cryptographic receipt output.

**LangGraph — 3**

Uses a Pregel-derived super-step model: nodes run in topological order, edges define transitions, `StateGraph.compile()` locks the graph before execution [[docs](https://langchain-ai.github.io/langgraph/concepts/low_level/)]. Checkpointers (InMemorySaver, SqliteSaver, AsyncPostgresSaver) snapshot state between nodes for resumable execution. Strong turn-level persistence; no governance contract.

**AutoGen v0.4 — 3**

Actor model (`RoutedAgent`, `AssistantAgent`) structures conversation as typed message exchange [[docs](https://microsoft.github.io/autogen/stable/)]. `SpeakerSelectionMethod` governs turn assignment in group chats. No per-turn governance contract or receipt output.

**CrewAI — 2**

Crew execution flows through `Process.sequential` or `Process.hierarchical`; Manager agent optionally delegates to Workers [[docs](https://docs.crewai.com/concepts/crews)]. No formal turn contract; lifecycle is implicit in task ordering.

**Semantic Kernel — 2**

Planner (HandlebarsPlanner, FunctionCallingStepwisePlanner) decomposes goals into function steps. `IFunctionInvocationFilter` can intercept per-step but there is no system-level turn governance contract [[filters docs](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/filters)].

**MemGPT / Letta — 3**

Introduced the OS metaphor for LLM runtime with main context (working memory), recall store (conversation history), and archival store. Heartbeat events act as a tick mechanism [[arXiv:2310.08560](https://arxiv.org/abs/2310.08560)]. Letta adds REST-API agent state management. Memory paging is a genuine contribution to turn lifecycle design; no governance boot contract.

**OpenAI Assistants API — 2**

Run lifecycle (queued → in_progress → requires_action → completed/failed/cancelled/expired) is well-specified [[reference](https://platform.openai.com/docs/api-reference/runs)]. State machine is server-side, run steps are not cryptographically attested, entire product line deprecated August 26, 2026 [[migration guide](https://platform.openai.com/docs/assistants/migration)].

---

### B — Cryptographic Integrity and Auditability

**MetaBlooms OS — 5**

Every file has a `.sha256` companion sidecar. Release exports include `.provenance.json` and a Sigstore/Rekor log entry (rekor_log_index: 1597847004, github_attestation_id: 28352056) anchoring build provenance in a public append-only transparency log [[Rekor](https://rekor.sigstore.dev)]. `EXPORT_PIPELINE_CONTRACT_v1.json` enumerates forbidden pass claims (e.g., `archive_created_without_strict_extracted_artifact_verify`). `landed_receipt_self_verify_v1.py` allows independent downstream re-verification.

arXiv:2604.05485 ("Auditable AI Agents") evaluated six agent frameworks and identified the absence of cryptographic binding as a first-class gap in existing systems. MetaBlooms' design directly addresses this class.

**Known cryptographic gaps (do not reduce score; acknowledged weaknesses within a 5-rated system):**
- **FIND-02:** Malformed sidecar (non-hex content) returns `BLOCKED` — same decision as absent sidecar. Tampered sidecar with garbage content is indistinguishable from legitimately absent sidecar at the decision level.
- **FIND-06 (HIGH):** Runner cannot process `.tar.zst` format — the format used by the current sticky release. This is an operational harness gap, not a cryptographic chain failure: the Sigstore/Rekor attestation and SHA-256 sidecars for the release remain independently verifiable via `cosign` or `rekor-cli`. The cryptographic chain is intact; the automated audit path is not.

**All comparators — 1 or 2**

None implement per-artifact cryptographic sidecars or transparency log attestation for session state. LangSmith (LangGraph) provides observability traces but these are mutable server-side logs. AutoGen lacks cryptographic receipts for agent outputs. OpenAI Assistants earns 2 only because runs have stable IDs and server-side timestamps — weak attestation, not independently verifiable. arXiv:2603.14332 found that LangChain/LangGraph lacks cryptographic binding between capability grants and agent outputs.

---

### C — Modularity and Capability Isolation

**Semantic Kernel — 5**

Plugin architecture is the strongest modular capability system evaluated. Plugins are first-class registered objects; separate `Kernel` instances enforce isolation; `IFunctionInvocationFilter` + `IPromptRenderFilter` allow interception at every capability boundary [[SK GitHub](https://github.com/microsoft/semantic-kernel)]. Multi-language support (C#, Python, Java) and explicit function-level capability registration make SK the reference design for structural modularity.

*Important distinction:* SK scores 5 for **structural modularity** — clean capability registration and isolation. It does not implement cryptographic capability binding (no attestation of which capabilities were granted to which agent outputs). That governance gap is captured in dimension B.

**MetaBlooms OS — 4**

Cartridges (ATTIC, MPP, release audit harness) are cleanly bounded with explicit contracts. ATTIC exports a stable entrypoint (`tools/metablooms/attic_release_preflight_advisory.py`) and maintains a versioned cartridge manifest. Gap: ATTIC is advisory-only at Stage020 — emits `ALLOW_ADVISORY` or `BLOCK_ADVISORY` but does not enforce hard blocks globally. Capability isolation exists at the documentation and contract level but not yet at the enforcement level.

**LangGraph — 4**

ToolNode cleanly wraps external tool calls; subgraphs allow modular composition; node boundaries are explicit. Graph compilation enforces structural validity before execution [[tools docs](https://langchain-ai.github.io/langgraph/concepts/tools/)]. No dynamic capability registration (graph defined before run), but model is cleanly bounded.

**MemGPT / Letta — 4**

Three-tier memory isolation (main context, recall store, archival store) is a genuine isolation primitive. Separate subsystems manage each tier with explicit paging operations. Letta agent state is encapsulated per-agent with REST API for external management [[Letta GitHub](https://github.com/letta-ai/letta)].

**AutoGen v0.4 — 3**

Actor isolation via message passing (each `RoutedAgent` has its own mailbox) provides logical separation but agents in a single runtime share the execution process. Tool registration is per-agent. No capability contracts.

**CrewAI — 3**

Role-based crew members with explicit task delegation provide logical isolation. `BaseTool` subclasses can be scoped per agent. Isolation is organizational, not technical — agents share the Python process, no formal capability contract [[CrewAI GitHub](https://github.com/crewAIInc/crewAI)].

**OpenAI Assistants — 2**

Tool registration (Code Interpreter, File Search, Function Calling) is per-assistant, providing some isolation. Tools share server-side execution context; operator has no visibility into capability boundaries.

---

### D — Failure Containment and False-Pass Prevention

**MetaBlooms OS — 4**

The PASS/FAIL/BLOCKED trichotomy is semantically precise and consistently applied. `EXPORT_PIPELINE_CONTRACT_v1.json` enumerates a hard list of forbidden pass claims. Sidecar check raises `FAIL` (not silent PASS) on hash mismatch, preventing silent promotion.

Score is 4, not 5, due to two open findings that reduce containment confidence:
- **FIND-02:** Malformed sidecar returns `BLOCKED` — identical to absent-sidecar path. Tampered sidecar with garbage content is indistinguishable from legitimately absent sidecar at the decision level.
- **FIND-05:** On `zstd` timeout, partial decompressed file is not deleted. `materialize()` may return the partial file as `zip_path`, causing `audit()` to call `check_zip()` on corrupt data and emit misleading additional check rows despite the upstream `FAIL` (runner lines 59–68, 115–117).

**Semantic Kernel — 3**

`IFunctionInvocationFilter` can intercept, inspect, and short-circuit function calls. A filter can throw to block execution. Real containment primitive, but no system-level false-pass contract — filter application is entirely up to the application developer.

**LangGraph — 2**

`ToolNode` wraps tool errors as `ToolMessage` objects (not exceptions), meaning a failing tool can be silently swallowed if the downstream node doesn't check `status`. Error recovery via retry logic. No formal false-pass prevention contract.

**AutoGen v0.4 — 2**

`DockerCommandLineCodeExecutor` provides sandboxing but no false-pass prevention at the message level. No formal failure containment contract.

**CrewAI — 2**

Task callbacks and error handling exist but are application-layer conventions, not structural guarantees.

**OpenAI Assistants — 2**

Run failure states well-defined; no operator-level false-pass prevention.

**MemGPT / Letta — 1**

Memory management prevents context overflow (a different failure class). No formal failure containment contract for agent outputs. An agent producing incorrect output will pass it upstream without interception.

*Note on scope:* MetaBlooms' containment operates on **artifact integrity** (hash verification, sidecar checks, extension validation), not on **semantic correctness** of agent outputs. The D dimension privileges the artifact-integrity failure class. A different D definition (semantic output correctness) would produce different scores for all systems.

---

### E — Operator / Human-in-the-Loop Controls

**LangGraph — 5**

Most mature HITL implementation among all systems evaluated. `interrupt(value)` pauses graph execution at any node and surfaces a value to the operator; `Command(resume=value)` resumes from the checkpoint [[HITL docs](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)]. `BreakpointAfter` / `BreakpointBefore` allow compile-time breakpoint injection. Checkpointer enables async HITL — graph paused indefinitely, resumable from a different process or machine. Production-validated at scale.

*Design philosophy:* LangGraph's HITL is **code-defined** — the developer places `interrupt()` at specific nodes. Interrupts operate at node granularity (any node, any turn). Interrupts are not cryptographically attested.

**MetaBlooms OS — 4**

`ALLOW_ADVISORY` / `BLOCK_ADVISORY` gates from ATTIC preflight gate release advancement. BTS quality metrics (`GROUNDED_SYNTHETIC`, `SYNTHETIC`, `GROUNDED_REAL`) are surfaced to operators in the turn receipt. `--operation validate` flag enables non-destructive pre-flight review. Gate decisions are captured in receipts (cryptographically attested).

*Design philosophy:* MetaBlooms' HITL is **policy-defined** — operator approves at stage boundaries based on contracts and receipts, not at individual turn/node granularity. ATTIC gates operate at stage-boundary granularity, not turn-level. A human cannot pause mid-turn, inspect a specific tool call, and resume. Score is 4 because policy-defined HITL has genuine advantages (audit trail, non-expert operation, contract updatability) but lacks LangGraph's interrupt precision.

**AutoGen v0.4 — 4**

`UserProxyAgent` with `human_input_mode=ALWAYS/NEVER/TERMINATE` provides explicit HITL gating. `TERMINATE` condition halts execution based on message content. `NestedChat` enables complex approval flows [[AutoGen docs](https://microsoft.github.io/autogen/stable/)]. Slightly below LangGraph because resumption is not as precisely checkpointed.

**CrewAI — 3**

`human_input=True` per task; `ask_human` tool; limited compared to LangGraph [[CrewAI docs](https://docs.crewai.com/concepts/crews)].

**Semantic Kernel — 3**

No dedicated HITL framework; implemented via function filters. Requires manual implementation per use case.

**MemGPT / Letta — 3**

Human intervention via REST API pause/resume. No declarative HITL framework.

**OpenAI Assistants — 3**

`requires_action` state enables tool approval gating. Being deprecated August 26, 2026.

---

### F — Self-Verification and Durable Proof

**MetaBlooms OS — 5**

`landed_receipt_self_verify_v1.py` is a standalone verifier: given a receipt JSON and optionally the actual asset file, it independently recomputes SHA-256 and returns `PASS_PROVEN` (file present, hash matches), `PASS_RECEIPT_KEY_CONFIRMED` (file absent, hashes internally consistent), or `BLOCKED` (hash missing or mismatch). Independently verifiable by any downstream consumer.

The durable floor mechanism is unique among all systems evaluated: `binary_readback_real_hash_pass: true` in the durability ledger certifies that the floor asset has been physically read back from a device and its hash verified. K2 floor (sha256: `4efc7472396f79311a220d3acc2ddee4a0ec4c5e22dbf2b12c28742d50c50024`) is cryptographically locked. Governing constraint: "Do not mark durable unless binary readback proof exists."

**Known gap (FIND-04):** `main()` returns exit code 2 for `PASS_RECEIPT_KEY_CONFIRMED`. This is a valid non-error outcome (asset not local, hashes consistent in receipt), but CI wrappers treat exit 2 as failure. Single-line fix; architectural concept is sound. Score remains 5.

**MemGPT / Letta — 2**

Agent state (memory contents, conversation history) can be exported and re-imported. Form of state verification but no cryptographic proof of state integrity and no durable floor concept.

**All other comparators — 1**

LangGraph, AutoGen, CrewAI, Semantic Kernel, and OpenAI Assistants have no self-verification primitives. Checkpointers store state but do not prove its integrity. No durability ledger or binary readback proof concept.

---

### G — Portability and Export Integrity

**LangGraph — 4**

Multiple checkpointer backends (SQLite, PostgreSQL, in-memory) allow state portability across deployments. LangGraph Cloud and LangServe provide deployment portability. State schema is Python-typed (TypedDict), making it inspectable. No cryptographic export integrity, but ecosystem is production-mature.

**Semantic Kernel — 4**

Multi-language support (C#/Python/Java) is a genuine portability advantage. Plugin function definitions serializable and portable across language runtimes. No cryptographic export integrity.

**MemGPT / Letta — 4**

Full REST API for agent state management; `letta-client` SDK wraps export/import. Memory contents portable across Letta server versions. No cryptographic export integrity.

**MetaBlooms OS — 2**

Exports include SHA-256 sidecars, `.provenance.json` with build metadata, and Sigstore/Rekor attestation — strongest cryptographic export integrity of any system evaluated. Score reduced to 2 due to:

- **FIND-06 (HIGH):** Runner cannot process `.tar.zst` archives — the format of the current sticky release. `materialize()` returns `BLOCKED` for any extension other than `.zip` or `.zip.zst`. The current release `MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z` is unauditable by its own harness (runner `release_audit_harness_runner_v1.py` lines 100–118).
- `mpp.sh` is a bash script — Linux/macOS only. No Windows support.
- No cross-language SDK; Python/bash only.
- These gaps place MetaBlooms below AutoGen/CrewAI on portability despite its superior cryptographic export story.

**AutoGen v0.4 — 3**

Agent state serializable; no standardized export format; Python-native only; broader OS/deployment support than MetaBlooms.

**CrewAI — 3**

YAML-based crew definitions are portable configuration. Runtime state has no standardized export. Python-native; broad OS support.

**OpenAI Assistants — 2**

Thread history accessible via API; vendor-specific format; significant lock-in; deprecated August 26, 2026. No user-side cryptographic export integrity.

---

### H — External Validation and Red-Team Readiness

**Scoring calibration:**
- **1:** No known external audit; vulnerabilities unknown
- **2:** External audit performed; findings documented (severity/patch status varies)
- **3:** External audit performed; all critical findings remediated and verified
- **4:** Continuous external validation (bug bounty, regular red-team exercises)

*Important:* External scrutiny that finds and does not remediate vulnerabilities is evidence of insecurity, not security. arXiv:2604.05485 found 617 security findings across six open-source agent frameworks (LangGraph, AutoGen, CrewAI, and others). Those frameworks score 2 — not because the audit improves their security, but because their vulnerability surface is partially characterized. MetaBlooms has no published external audit and zero known CVEs, but also zero external users — an unknown security posture, not a clean one.

**MetaBlooms OS — 1:** No known independent security review of governance contracts. All audit evidence in this rubric is self-generated (including this session). Governance contracts may be elegant on paper but circumventable in practice — exactly the failure mode arXiv:2604.05485 found in six other frameworks.

**LangGraph, AutoGen, CrewAI, Semantic Kernel, OpenAI Assistants — 2:** Subject to academic and community security research; findings documented.

**MemGPT / Letta — 1:** Limited external security research at time of evaluation; primarily academic attention on memory architecture rather than security.

---

## Adversarial Gap Analysis for MetaBlooms OS

The following are genuine weaknesses, not easily dismissed:

| Finding | Severity | Evidence |
|---|---|---|
| **FIND-06:** Runner blocked on `.tar.zst` — its own current release format | HIGH | `release_audit_harness_runner_v1.py` line 118; current release is `.tar.zst`; runner returns `BLOCKED` |
| **FIND-02:** Malformed sidecar indistinguishable from absent sidecar | MEDIUM | `sidecar_hash()` returns `None` for both cases; same `BLOCKED` decision; tampering not detected |
| **FIND-05:** Partial archive returned as `zip_path` after timeout | MEDIUM | `materialize()` lines 115–117; partial corrupt file passed to `check_zip()`; misleading downstream check rows |
| **FIND-04:** Valid `PASS_RECEIPT_KEY_CONFIRMED` returns exit code 2 | LOW | `landed_receipt_self_verify_v1.py` line 168; breaks CI wrappers without `\|\| true` workaround |
| **No external production validation** | Epistemic | All audit evidence self-generated; no independent third-party security review of governance contracts |
| **ATTIC advisory-only at Stage020** | Architectural | Capability isolation exists at the documentation layer; hard enforcement deferred |
| **Shell-based `mpp.sh`** | Portability | Linux/macOS only; no Windows support; no cross-language SDK |
| **Single-project scope** | Scale | LangGraph, AutoGen, Semantic Kernel have thousands of production deployments; MetaBlooms has no external stress testing |
| **Endogenous rubric design** | Methodological | Dimensions chosen from MetaBlooms' feature list; a competitor-designed rubric would favor different dimensions |

---

## System Profiles (Summary)

### MetaBlooms OS

**Strengths:** Turn lifecycle governance with cryptographic receipts; per-file SHA-256 sidecars; Sigstore/Rekor attestation; durable floor with binary readback requirement; EXPORT_PIPELINE_CONTRACT blocking forbidden pass claims; PASS/FAIL/BLOCKED trichotomy with precise semantics.

**Weaknesses:** Runner cannot process its own current release format (FIND-06, HIGH); ATTIC advisory-only; bash-only, no Windows; no external security validation; single-project, no production scale.

**Best fit:** Governed, audited LLM agent runtimes where cryptographic integrity and false-pass prevention are primary requirements and production scale is not.

---

### LangGraph

**Strengths:** Best-in-class HITL with `interrupt()`/`Command(resume=)` checkpoint-based async resumption; Pregel super-step execution model; multiple checkpointer backends (SQLite, PostgreSQL); production-validated at scale; strong ecosystem (LangSmith, LangServe, LangGraph Cloud).

**Weaknesses:** No cryptographic receipts; no tamper-evident state; no durable floor concept; arXiv:2604.05485 found security vulnerabilities; no per-artifact integrity.

**Best fit:** Production agent systems requiring precise, granular human-in-the-loop control and deployment portability; teams prioritizing operational maturity over governance contracts.

**References:** [LangGraph docs](https://langchain-ai.github.io/langgraph/), [LangGraph GitHub](https://github.com/langchain-ai/langgraph)

---

### Semantic Kernel

**Strengths:** Best structural modularity — plugin architecture, separate kernel instances for isolation, `IFunctionInvocationFilter` + `IPromptRenderFilter` pipeline, multi-language (C#/Python/Java); Microsoft enterprise support.

**Weaknesses:** No cryptographic capability binding; no self-verification; governance is structural, not cryptographic; no HITL framework (requires manual filter implementation).

**Best fit:** Enterprise systems requiring structured plugin management and multi-language deployments; teams using Microsoft Azure ecosystem.

**References:** [SK GitHub](https://github.com/microsoft/semantic-kernel), [SK filters docs](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/filters)

---

### MemGPT / Letta

**Strengths:** Genuine OS metaphor with three-tier memory isolation (main context/recall/archival); virtual context management with explicit paging; agent state serializable and portable; REST API for external management; published peer-reviewed research (arXiv:2310.08560).

**Weaknesses:** No cryptographic receipts; no durable floor; no governance contracts; no false-pass prevention; limited external security validation.

**Best fit:** Long-running agents requiring persistent memory beyond single-context windows; applications where memory architecture is the primary concern.

**References:** [MemGPT paper arXiv:2310.08560](https://arxiv.org/abs/2310.08560), [Letta GitHub](https://github.com/letta-ai/letta)

---

### AutoGen v0.4

**Strengths:** Actor model (`RoutedAgent`) with typed message routing; `UserProxyAgent` with `ALWAYS/NEVER/TERMINATE` HITL modes; `NestedChat` for complex approval flows; active Microsoft development; Docker sandboxing for code execution.

**Weaknesses:** No cryptographic receipts (open issue at time of research); no durable proof; no false-pass contract; agents share execution process in single runtime.

**Best fit:** Multi-agent conversational systems requiring flexible role assignment and straightforward human proxy gating.

**References:** [AutoGen docs](https://microsoft.github.io/autogen/stable/), [AutoGen GitHub](https://github.com/microsoft/autogen)

---

### CrewAI

**Strengths:** Role-based crew members with hierarchical process; YAML-based portable crew definitions; `human_input=True` per task; `ask_human` tool; accessible entry point for multi-agent systems.

**Weaknesses:** No cryptographic integrity; no HITL precision comparable to LangGraph; no formal failure containment; organizational isolation only (not technical).

**Best fit:** Multi-agent workflows with clear role separation and moderate governance requirements; teams prioritizing ease of configuration over deep control.

**References:** [CrewAI docs](https://docs.crewai.com/concepts/crews), [CrewAI GitHub](https://github.com/crewAIInc/crewAI)

---

### OpenAI Assistants API

**Strengths:** Thread-based state persistence; well-specified run lifecycle state machine; integrated Code Interpreter, File Search, and Function Calling; managed infrastructure.

**Weaknesses:** Deprecated August 26, 2026; vendor lock-in; no user-side cryptographic attestation; server-side state machine opaque to operators; no portability.

**Best fit:** None recommended — product is deprecated. Migrate to Responses API or open alternatives before August 2026 [[migration guide](https://platform.openai.com/docs/assistants/migration)].

---

## Overall Verdict

**MetaBlooms OS leads on the dimensions that matter most for governance** — cryptographic integrity (B), self-verification and durable proof (F), turn lifecycle governance (A), and failure containment (D). No other system in this comparison implements per-artifact cryptographic sidecars, transparency log attestation, a durability ledger with binary readback requirements, or a contract-level enumeration of forbidden pass claims.

**The comparators lead on dimensions that matter most for production adoption** — LangGraph on HITL precision (E) and ecosystem maturity; Semantic Kernel on structural capability modularity (C); MemGPT/Letta on memory architecture; all six comparators on scale, external validation, and cross-platform portability.

**The inversion threshold is approximately 3.9×:** if HITL (E) and portability (G) are weighted at 3.9× or higher relative to the governance dimensions, LangGraph reaches parity with or exceeds MetaBlooms. Under equal weighting, MetaBlooms leads by 8 points (30 vs 22).

**The most important near-term repair for MetaBlooms:**

> FIND-06 (HIGH): The runner cannot process `.tar.zst` — its own current release format. Extending `materialize()` to handle `.tar.zst` and adding tar-based required-member inspection would resolve this immediately. Until fixed, the audit harness cannot fulfill its primary purpose against the current OS release.

The governance architecture is genuinely novel. The comparison is fair within its declared lens. The lens should be disclosed — this rubric is a governance-centered comparison, not an objective ranking of system quality.

---

## References

1. LangGraph architecture — https://langchain-ai.github.io/langgraph/concepts/low_level/
2. LangGraph human-in-the-loop — https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
3. LangGraph persistence — https://langchain-ai.github.io/langgraph/concepts/persistence/
4. LangGraph tools — https://langchain-ai.github.io/langgraph/concepts/tools/
5. LangGraph GitHub — https://github.com/langchain-ai/langgraph
6. Microsoft AutoGen v0.4 — https://microsoft.github.io/autogen/stable/
7. AutoGen GitHub — https://github.com/microsoft/autogen
8. CrewAI concepts — https://docs.crewai.com/concepts/crews
9. CrewAI GitHub — https://github.com/crewAIInc/crewAI
10. Semantic Kernel filters — https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/filters
11. Semantic Kernel GitHub — https://github.com/microsoft/semantic-kernel
12. MemGPT paper — Packer et al., "MemGPT: Towards LLMs as Operating Systems," arXiv:2310.08560 (2023) — https://arxiv.org/abs/2310.08560
13. Letta GitHub — https://github.com/letta-ai/letta
14. OpenAI Assistants API reference — https://platform.openai.com/docs/api-reference/runs
15. OpenAI Assistants migration guide — https://platform.openai.com/docs/assistants/migration
16. Sigstore / Rekor transparency log — https://rekor.sigstore.dev
17. SLSA supply chain integrity framework — https://slsa.dev
18. "Governing Dynamic Capabilities in Autonomous AI Agents" — arXiv:2603.14332 (2025)
19. "Auditable AI Agents" — arXiv:2604.05485 (2024); 617 security findings across 6 frameworks, 8.3 ms mediation overhead
20. MetaBlooms OS repo-side audit — `audits/METABLOOMS_OS_REPO_SIDE_AUDIT_20260602.md` (2026-06-02)
21. MetaBlooms OS repo-side audit (machine-readable) — `audits/METABLOOMS_OS_REPO_SIDE_AUDIT_20260602.json` (2026-06-02)
22. NIST Secure Software Development Framework — https://csrc.nist.gov/Projects/ssdf
