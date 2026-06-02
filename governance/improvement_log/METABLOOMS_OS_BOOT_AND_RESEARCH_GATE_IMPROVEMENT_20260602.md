# Improvement: Boot Blockers Need Recursive Repair and Research-Gate Remediation

**Date:** 2026-06-02  
**System:** MetaBlooms OS — `mpp.sh turn-boot`, boot blocker handling, research evidence gate  
**Priority:** CRITICAL  
**Source:** ChatGPT garden-analysis session boot repair incident, latest OS bundle `METABLOOMS_FULL_OS_STICKY_DURABLE_FLOOR_IMPORTED_20260601T2326Z.tar.zst`  
**Status:** OPEN

---

## Problem Statement

During the garden-analysis workflow, boot entered a repeated blocker loop instead of using the LLM-governed repair capability to diagnose and repair the blocker. The observed failure was:

```text
MPP-TURN-BOOT decision=BLOCKED_BTS_FULL_DECISION_REQUIRED
bts_error=BTS full decision requires --instinctive-choice.
```

The assistant repeatedly emitted the same blocker. This was not a normal runtime failure; it was a governance bootstrap deadlock. Boot required BTS full-decision fields before repair work could begin, but the canonical boot invocation did not provide those fields. A later manual repair added grounded BTS synthesis fallback, after which boot progressed to the next blocker:

```text
MPP-TURN-BOOT decision=PENDING_RESEARCH_EVIDENCE
research_gate=BLOCKED
```

That second blocker was legitimate in principle, but too opaque as an operator experience. The system should have returned a structured remediation contract or self-healed by requesting/supplying same-turn evidence where permitted.

---

## Gaps

### Gap 1 — Boot blockers can become self-referential deadlocks

**Impact:** A small local argument-contract mismatch can prevent the OS from reaching the repair layer that would fix it.

**Root cause:** Boot treats some governance-contract errors as terminal blockers instead of privileged boot-contract repair cases.

### Gap 2 — Repeated blocker output is not routed to root-cause repair

**Impact:** The same failing boot command can be run repeatedly with the same result. This wastes turns and violates the intended LLM-governed self-repair model.

**Root cause:** No blocker fingerprint / retry-delta detector forces a different action after the same blocker recurs.

### Gap 3 — Research evidence gate blocks without actionable remediation

**Impact:** Artifact-affecting repair turns can stop at `PENDING_RESEARCH_EVIDENCE` even when the fix is local and the missing evidence requirement could be satisfied or explicitly scoped.

**Root cause:** The research gate exposes a verdict but not a structured operator contract: required source type, claim binding format, re-run command, or allowed local-only exemption path.

### Gap 4 — Boot repairs are not automatically exported into the durable bundle

**Impact:** A live-root boot repair may work in the current chat but not survive into future chats unless a new OS export or diff packet is produced and verified.

**Root cause:** Repair completion is not coupled to export/readback validation.

---

## Desired State

1. Boot has a privileged, narrow `BOOT_CONTRACT_REPAIR_REQUIRED` path for missing local boot arguments, malformed local contracts, and repeated blocker fingerprints.
2. Same blocker twice forces root-cause repair mode. It may not keep re-running the same boot command unchanged.
3. Research-gate blockers return a machine-readable remediation contract with exact fields needed to satisfy the gate.
4. Local-only repair work can use an explicit, receipt-backed `research_not_required_reason` only when the repair does not depend on unstable external facts.
5. Any repair that modifies OS behavior triggers export or diff-packet creation plus readback verification before the improvement is considered durable.

---

## Action Items

### Immediate

- [ ] **B1:** Add a recursive boot repair controller. Algorithm: run boot, fingerprint blocker, classify blocker, apply smallest authorized repair, reboot, stop only on `PASS` or unrecoverable blocker, and write attempt receipts.
- [ ] **B2:** Add repeated-blocker detection. If the same normalized blocker occurs twice with no changed inputs or repair receipt, block the repeated action and route to root-cause repair.
- [ ] **B3:** Add a boot-contract exception for missing BTS full-decision fields. `turn-boot` must auto-enable grounded BTS synthesis or return `BOOT_CONTRACT_REPAIR_REQUIRED`; it must not deadlock on `--instinctive-choice` absence.
- [ ] **B4:** Add a research-gate remediation contract output containing required evidence type, accepted source/claim binding format, and exact re-run command.
- [ ] **B5:** Add an explicit local-only repair exemption path: `research_not_required_reason`, bounded to artifact-local repairs, with receipt and SAR review.

### Medium-term

- [ ] **B6:** Couple behavior-changing repairs to export/diff-packet creation and readback validation before marking the repair durable.
- [ ] **B7:** Add a boot incident ledger that records blocker fingerprints, repairs attempted, final status, and recurrence count.

---

## Evidence

- Repeated observed blocker in garden-analysis session: `BLOCKED_BTS_FULL_DECISION_REQUIRED` / missing `--instinctive-choice`.
- Manual local repair in live root: grounded BTS synthesis fallback for artifact-affecting turns with incomplete explicit BTS fields.
- Follow-on observed blocker after BTS repair: `PENDING_RESEARCH_EVIDENCE`, resolved only after same-turn source/claim binding was manually supplied.
- Latest bundle comparison found the uploaded durable floor predates these chat-discovered workflow improvements; therefore export/readback is required for persistence.
