# Improvement: Agent Harness Plan Has Stage Ordering Error and Three Underspecified Risks

**Date:** 2026-06-02  
**System:** MetaBlooms OS — agent harness / governed orchestrator plan  
**Priority:** HIGH  
**Source:** Adversarial audit of ZIP plan + harness selection rubric, session `claude/metablooms-os-audit-hr5ET`  
**Status:** OPEN  
**Related:** `audits/AGENT_HARNESS_SELECTION_RUBRIC_20260602.md`

---

## Problem Statement

The MetaBlooms native agent harness research produced two artifacts:

1. The ZIP plan (`METABLOOMS_NATIVE_AGENT_HARNESS_RESEARCH_DESIGN_20260602T162210Z`)
   — a governed orchestrator wrapping existing tools (Gemini CLI, Aider, Cline,
   OpenHands, Codex, CCR, Ollama) as interchangeable engines.

2. The harness selection rubric (`audits/AGENT_HARNESS_SELECTION_RUBRIC_20260602.md`)
   — a 9-dimension comparison of 5 approaches that finds: custom harness (CH) scores
   39/45; governed orchestrator (GO) scores 27/45; prompt-only (PO) scores 28/45.

Both documents contain findings that need to be acted on. Four gaps require
improvement log entries:

1. The ZIP plan's MVP stage ordering is wrong — adapters run before gates exist.
2. The OpenHands authority conflict is not acknowledged in the plan.
3. The context builder is the highest-risk component and is underspecified.
4. The recommended build sequence (CH first, not GO) is not documented as a
   governance decision.

---

## Gap 1 — Stage ordering error in governed orchestrator plan

**Current:** ZIP plan stages are ordered A → B → C → D → E → F, where:
- Stage C = Disposable fixture harness
- Stage D = Aider/Gemini adapter proof (running external tools)
- Stage E = Policy gates and rollback

**Problem:** Stage D runs adapters against external tools before Stage E creates the
policy gates that govern those tools. An adapter with a bug in Stage D can write to
the canonical OS before containment exists. This is the exact failure class the
harness is designed to prevent.

**Desired:** Stage ordering must be A → B → E → C → D → F. Policy gates exist before
any external engine runs.

---

## Gap 2 — OpenHands authority conflict not acknowledged

**Current:** ZIP plan lists OpenHands as one of several interchangeable engine options
in the engine router (Layer 2).

**Problem:** OpenHands is architecturally designed to be the control plane of a coding
agent deployment — it dispatches to workers, it does not expect a wrapper above it.
Using it as a sub-engine inside the MetaBlooms orchestrator requires inverting its
design. The ZIP plan does not acknowledge this conflict and does not include a
containment mechanism for it.

**Risk class:** If OpenHands is adopted as an engine without a containment mechanism,
it will attempt to take governance authority. MetaBlooms governance will not be the
actual authority even if it is the intended authority.

**Desired:** Risk register for the governed orchestrator must include OpenHands as a
HIGH-risk engine requiring a specific containment mechanism (network-isolated container,
write interceptor at FUSE or seccomp level) before it can be used as an engine. This
work must be scoped separately from the adapter proof stage.

---

## Gap 3 — Context builder is underspecified

**Current:** ZIP plan Layer 4 ("Context builder") is described as: "Generate bounded
packets: relevant files, manifests, recent receipts, failing tests, constraints. Avoid
dumping the whole OS into context."

**Problem:** This description does not define:
- Relevance policy (how are relevant files selected?)
- Per-engine token budget (1M context engine vs. 128k context engine need different packets)
- Secret filtering (when does filtering run — at assembly time or at patch time?)
- What happens when a required file is outside the token budget

arXiv:2404.11584 identifies context injection (what goes into the agent prompt) as the
primary failure mode in agent systems — more common than tool misuse or output parsing
failures. The context builder is where most agent failures happen in practice.

**Desired:** Context builder must have its own sub-spec as a named deliverable before
Stage C. Sub-spec must define: relevance policy, per-engine token budget table, secret
filter timing (assembly), budget overflow behavior (truncate with summary, or fail
closed). The context builder sub-spec becomes an invariant in STAAR_ENGINE_SOP.

---

## Gap 4 — Build sequence is not documented as a governance decision

**Current:** The ZIP plan and the harness selection rubric both exist as audit/research
artifacts. No governance decision has been recorded about which approach to build first.

**Problem:** Without a recorded decision, the next session that works on agent harness
infrastructure can pick up the ZIP plan (governed orchestrator) and start building from
Stage A. This is the wrong first step — the selection rubric shows the custom harness
(CH) should be built first:
- CH fixture harness is smaller and faster to validate
- CH enforces MetaBlooms governance deterministically, not probabilistically
- CH becomes the first "engine adapter" when the orchestrator is eventually built

**Desired:** Record the governance decision: **build custom harness (CH) first,
graduated to governed orchestrator (GO) after CH baseline is stable.** Document the
recommended sequence (below) as a binding plan, not a rubric finding.

---

## Action Items

### Immediate (no build work required — documentation only)

- [ ] **H1:** Update the ZIP plan stage order in the research document or in a
  companion amendment file: correct sequence is A → B → E → C → D → F.

- [ ] **H2:** Add OpenHands to the ZIP plan risk register as HIGH risk, with a note
  that it requires a containment mechanism (write interceptor) before it can be used
  as an engine. This is separate work from the adapter proof.

- [ ] **H3:** Write context builder sub-spec as a named document in
  `governance/` or `source_materials/`. Fields: relevance policy, per-engine token
  budget, secret filter timing, budget overflow behavior. This is a prerequisite for
  Stage C (fixture harness), not Stage D.

- [ ] **H4:** Record governance decision in this improvement log or in
  `governance/sops/`: "Build CH (custom harness) fixture first. Graduate to GO
  (governed orchestrator) after CH is stable. CH is the first engine adapter when
  GO is eventually built."

### Build sequence (for when harness work begins)

Recommended sequence from harness selection rubric (CH path):

1. **CH Stage 1 (weeks 1–2):** Fixture harness — one failing STAAR engine test,
   git worktree, path guard, command logger, receipt writer. No external engine yet.
   Output: single Python script, mb.receipt.v1 JSON, one passing test.

2. **CH Stage 2 (weeks 3–5):** Context builder sub-spec (H3) implemented.
   PROMOTION_GATE_v1 enforced in Python. Secret filter at assembly time.
   Output: context builder module, promotion gate module.

3. **CH Stage 3 (weeks 6–8):** Free model adapters. Gemini 2.0 Flash (1M context,
   free tier, ai.google.dev). Qwen2.5-Coder-32B via Ollama (MIT, requires 32 GB RAM).
   Run against STAAR engine fixture tests.
   Output: two model adapters, integration test against fixture.

4. **CH Stage 4 (later):** Graduate to GO architecture. CH becomes the first engine
   adapter inside the orchestrator. Policy gates (CH Stage 2) carry over as the
   orchestrator's gate layer.

---

## Evidence

- arXiv:2604.05485 — 617 security findings across 6 agent frameworks; majority involve
  insufficient containment of agent-initiated writes. Supports OpenHands risk rating.
- arXiv:2603.14332 — LangChain/LangGraph lack cryptographic binding between capability
  grants and outputs. Supports policy-gates-before-adapters principle.
- arXiv:2404.11584 — Context injection is the primary agent failure mode. Supports
  context builder sub-spec as prerequisite.
- OpenHands architecture documentation: agent-server model, workers dispatched from
  control plane. Supports Gap 2 authority conflict finding.
- `audits/AGENT_HARNESS_SELECTION_RUBRIC_20260602.md` — full 9-dimension rubric,
  CH 39/45 vs GO 27/45, recommended sequence, adversarial gap analysis per approach.
- `source_materials/raw_import/PROMOTION_GATE_v1.json` — gate is machine-enforced;
  any approach that cannot enforce it machine-to-machine cannot earn A > 3.
