# Improvement: Cross-Session Coordination Is Missing Two Key Artifacts

**Date:** 2026-06-02  
**System:** MetaBlooms OS — session workflow / improvement log  
**Priority:** HIGH  
**Source:** Workflow analysis session `claude/metablooms-os-audit-hr5ET`  
**Status:** OPEN

---

## Problem Statement

The improvement-log-first workflow (push findings to improvement log, then open a
new chat with a real plan and priority order) is sound and evidence-backed
(Frederick Brooks 1975: integration costs are non-linear; Kent Beck XP 1999:
small frequent integrations beat big-bang merges). It is now in effect as of
this audit session.

But the workflow has two missing artifacts that reduce its value in new planning
chats:

1. **No current-state snapshot document.** A new planning chat has no single file
   that summarizes what MetaBlooms OS is right now — what the STAAR engine does,
   what the governance layer enforces, what the durable floor hash is, what the
   SOP is at. Every new session rebuilds this orientation by reading multiple files.
   This costs context and risks missing something important.

2. **No dependency-ordered improvement backlog.** Improvement log files are
   individual and unordered. A new planning chat cannot see "fix X before Y because
   X blocks Y" without reading all files. The ordering and dependency structure exist
   only in the session that produced the findings, not in the repo.

---

## Current State

The improvement log exists (`governance/improvement_log/`) with a README and one
filing to date (BTS feedback loop). Files are individually well-structured but:

- There is no index of priority order.
- There is no "blocks/blocked-by" relationship between items.
- There is no single current-state snapshot for new-chat orientation.
- The README table lists files with dates but no sequencing guidance.

---

## Desired State

1. `governance/improvement_log/CURRENT_STATE_SNAPSHOT.md` exists and is updated
   at the start of every planning session. It contains:
   - STAAR engine summary (what it is, what TEKS it covers, current SOP version)
   - Governance layer summary (contracts, gate, validator matrix, SOP rules)
   - Durable floor hash and last binary readback date
   - Current open improvement items with priority and block/blocked-by links
   - Last 3 session receipt IDs and their BTS quality

2. `governance/improvement_log/IMPROVEMENT_BACKLOG_ORDERED.md` exists and is
   maintained. It contains all open action items from all improvement files, sorted
   by dependency order (items that unblock other items come first), with explicit
   "blocks:" and "blocked-by:" annotations.

---

## Action Items

### Immediate

- [ ] **W1:** Create `CURRENT_STATE_SNAPSHOT.md` in the improvement log. Populate
  from the current audit session findings. Convention: updated at the start of
  every new planning chat before other work begins.

- [ ] **W2:** Create `IMPROVEMENT_BACKLOG_ORDERED.md`. Seed it with all open items
  from BTS_FEEDBACK_LOOP_IMPROVEMENT and AGENT_HARNESS_IMPROVEMENT (see that
  file). Include explicit block/blocked-by annotations. Sort so items with no
  blockers appear first.

### Ongoing convention

- [ ] **W3:** Every planning chat begins by reading CURRENT_STATE_SNAPSHOT.md and
  IMPROVEMENT_BACKLOG_ORDERED.md before any other file. These two files replace
  the multi-file orientation pass.

- [ ] **W4:** Every session that closes an action item updates IMPROVEMENT_BACKLOG_ORDERED
  to mark it DONE and updates CURRENT_STATE_SNAPSHOT if any state it describes
  has changed.

---

## Evidence

- Frederick P. Brooks, *The Mythical Man-Month* (1975, anniversary ed. 1995):
  integration costs are non-linear. Small, frequent integrations with good
  orientation artifacts beat large cross-session rebuilds.
- Kent Beck, *Extreme Programming Explained* (1999): continuous integration.
  The improvement log is the integration artifact for governance decisions.
- Direct observation in this session: multi-task sessions spanning BTS audit,
  rubric production, workflow analysis, and harness design exhausted context
  before completing the final task. The fix was a 5-minute write once the
  design was in the summary — the research was not the bottleneck, orientation
  overhead was.
