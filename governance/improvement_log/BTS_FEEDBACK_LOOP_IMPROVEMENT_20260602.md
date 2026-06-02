# Improvement: BTS Feedback Loop Is Not Driving Real System Improvement

**Date:** 2026-06-02  
**System:** MetaBlooms OS — `mpp.sh turn-boot` → BTS quality measurement → learning loop  
**Priority:** HIGH  
**Source:** Inside-out BTS audit, session `claude/metablooms-os-audit-hr5ET`  
**Status:** OPEN

---

## Problem Statement

BTS (Behavioral Turn Score) is measured and recorded on every turn. The learning
loop runs and returns `PASS` or `FAIL`. But BTS quality is not modulating what
the learning loop does, the most valuable BTS tier (`GROUNDED_REAL`) can never
fire with the current architecture, and `learning: PASS` turns produce no visible
improvement artifacts.

The system is using BTS as a **monitoring instrument**. It should be using it as
a **feedback control system**.

---

## Current State

### What BTS measures

| BTS Quality | Meaning |
|---|---|
| `GROUNDED_REAL` | Session has actual student interaction data |
| `GROUNDED_SYNTHETIC` | Synthetic data grounded in real STAAR released items |
| `SYNTHETIC` | Purely synthetic, no grounding in real test patterns |

### What is actually observed

Every session in the repo is `GROUNDED_SYNTHETIC` or `SYNTHETIC`. No session has
ever produced `GROUNDED_REAL`. The most important tier has never fired.

### What the learning loop currently does

Returns `PASS` (no failure classes detected) or `FAIL` (failure classes detected,
artifacts should be produced). The output is binary and does not vary based on BTS
quality. A `GROUNDED_SYNTHETIC` session and a `SYNTHETIC` session that both PASS
produce identical output.

### What CODING_RELIABILITY_SOP_v1 Rule 5 requires

> "Regression learning must become artifacts. When a failure class appears, add:
> an invariant, a validator, a checklist entry, a patch contract rule."

The SOP invariants (at v32 with 10+ invariants) are proof this worked historically.
INVARIANT 7 (symbolic validator scope), INVARIANT 4 (drag-drop validator), and
INVARIANT 8 (anti-starvation window) are all clearly failure-derived. The mechanism
worked. It is not actively producing new artifacts now.

### The architectural blocker for GROUNDED_REAL

The STAAR engines are standalone HTML files that run locally on student devices
with no server, no login, and no telemetry (by design — STAAR Engine SOP Part 1).
Student interaction data never flows back. There is no data return path from
deployed engines to the governance OS. `GROUNDED_REAL` is architecturally
unreachable until this is built.

---

## Gaps

### Gap 1 — GROUNDED_REAL data pipeline does not exist

**Impact:** The learning loop permanently operates on synthetic signals. Actual
student misconception patterns, which are the ground truth the engine was built
to respond to, never reach the governance layer.

**Root cause:** Standalone HTML architecture has no telemetry mechanism.

### Gap 2 — BTS quality does not modulate learning output

**Impact:** The richer BTS signal is wasted. `GROUNDED_REAL` and `SYNTHETIC`
sessions produce the same `PASS` verdict. There is no mechanism to say "this
failure at GROUNDED_REAL quality requires an immediate mandatory invariant" vs
"this failure at SYNTHETIC quality is provisional."

**Root cause:** The learning loop's output schema does not include a
BTS-quality-weighted confidence level.

### Gap 3 — Positive learning (PASS turns) produces no artifacts

**Impact:** Sessions that PASS leave no improvement trace. The system can only
learn from things that break, never from patterns in what works. Family coverage
data from practice sessions (which families surfaced, which misconceptions were
triggered) is not fed back to the governance layer.

**Root cause:** Rule 5 only specifies what to do on failure. There is no
equivalent rule for what PASS turns should contribute.

### Gap 4 — BTS on AUDIT turns is semantically hollow

**Impact:** An audit session (`turn_class: AUDIT`) with `bts_quality:
GROUNDED_SYNTHETIC` is formally classified but behaviorally meaningless —
governance audits produce no student behavior to score. The BTS taxonomy
conflates audit sessions and practice sessions.

**Root cause:** BTS was designed for practice sessions. It was not given a
distinct path for audit/governance sessions.

### Gap 5 — SOP version history is not traceable to BTS events

**Impact:** The SOP is at v32 but no changelog records which version increment
came from which BTS-triggered failure. You cannot trace any invariant back to
the session receipt that produced it.

**Root cause:** No convention for linking SOP commits to receipt IDs.

---

## Desired State

1. `GROUNDED_REAL` turns exist and occur regularly because a data return path
   exists from deployed engines to the governance OS.

2. BTS quality modulates learning output: GROUNDED_REAL failures trigger required
   artifact creation; GROUNDED_SYNTHETIC failures trigger provisional artifacts
   pending GROUNDED_REAL confirmation; SYNTHETIC failures trigger notes only.

3. PASS turns contribute a structured coverage record: which families fired,
   which misconceptions were exercised, which families had zero coverage. This
   record flows into the governance layer as a positive learning artifact.

4. Audit turns (`turn_class: AUDIT`) use a separate BTS path that does not
   conflate behavioral quality with governance quality. An audit turn's quality
   is measured by a different taxonomy (e.g., `EVIDENCE_QUALITY: DIRECT_CODE /
   RECEIPT_BACKED / RECONSTRUCTED`).

5. Every SOP commit that adds or changes an invariant cites the session receipt
   that triggered it in the commit message.

---

## Action Items

### Immediate (no architectural change required)

- [ ] **A1:** Add Rule 6 to CODING_RELIABILITY_SOP_v1: "PASS turns must produce a
  coverage record artifact listing family exposure, misconceptions exercised, and
  any family with zero coverage."
- [ ] **A2:** Add a convention to the SOP that every invariant addition cites a
  session receipt in its commit message.
- [ ] **A3:** Add a `turn_class`-aware BTS path to `mpp.sh`: audit turns should
  report `audit_evidence_quality` (e.g., `DIRECT_CODE`, `RECEIPT_BACKED`) rather
  than forcing the student-behavior BTS taxonomy.

### Medium-term (design work required)

- [ ] **A4:** Design a minimal telemetry export for the STAAR engine teacher panel:
  a JSON export button that captures session telemetry (family exposure counts,
  misconception counters, mastery state) without requiring a server. Manual upload
  path acceptable for phase 1.
- [ ] **A5:** Define the BTS quality-to-learning-action mapping as a contract:

  ```
  GROUNDED_REAL + FAIL   → mandatory new invariant, blocks promotion
  GROUNDED_SYNTHETIC + FAIL → provisional invariant, requires GROUNDED_REAL confirmation
  SYNTHETIC + FAIL       → note, does not block
  GROUNDED_REAL + PASS   → coverage artifact required
  GROUNDED_SYNTHETIC + PASS → coverage artifact optional
  ```

- [ ] **A6:** Version the SOP with a structured changelog. Each version increment
  records: version number, date, triggering receipt (if failure-driven) or
  "DESIGN" (if proactive).

### Long-term (architectural change required)

- [ ] **A7:** Build a real data return path from deployed STAAR engines to the OS.
  Minimum viable: teacher panel JSON export + import script in
  `tools/metablooms/`. This is the only path to `GROUNDED_REAL` BTS quality.

---

## Evidence Base

All findings come from direct repo inspection (2026-06-02 audit session):

- `runtime/cartridges/release_audit_harness_v1/release_audit_harness_runner_v1.py` — mpp.sh boot receipt format
- `source_materials/raw_import/CODING_RELIABILITY_SOP_v1.md` — Rule 5 definition
- `source_materials/raw_import/STAAR_ENGINE_SOP.md` — v32, 10 invariants
- `source_materials/raw_import/SUBSYSTEM_VALIDATOR_MATRIX_v1.json` — validator matrix
- `source_materials/raw_import/PROMOTION_GATE_v1.json` — promotion requirements
- `source_materials/raw_import/teks_engine_contract_bundle_v1.json` — TEKS contracts
- `metablooms_checkpoints/` — session records (no BTS quality values visible;
  all PASS verdicts without BTS detail in checkpoint summaries)
- `externalization/cold_receipts/` — full OS turn export receipt (10 MB compressed;
  turn receipts externalized but not inspectable from this session)
- Audit session output: `turn_class: AUDIT  bts_quality: GROUNDED_SYNTHETIC  learning: PASS`
