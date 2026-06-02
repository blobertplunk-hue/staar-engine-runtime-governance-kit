# MetaBlooms OS WCUQ and Post-Rubric Repair Improvement — 2026-06-02

**System:** MetaBlooms OS  
**Topic:** WCUQ stale tracker display and post-rubric repair carry-forward  
**Priority:** HIGH / P0-P2 mixed  
**Source:** Comparative governance rubric repair chain, Stage002–Stage004H follow-up, WCUQ static-score investigation  
**Current branch:** `claude/metablooms-os-audit-hr5ET`

## Summary

A governed rubric-repair sequence exposed several MetaBlooms OS issues that should be tracked in the repository improvement log instead of remaining only in local runtime receipts. The most urgent user-facing defect is that the Visual Tracker displays a static historical WCUQ score as though it were live.

The current tracker repeatedly shows:

```text
score 90.35; band A; promotion_ready=True; gate=PASS_WCUQ_CONTROLLER_PROMOTION; field_schema=STRICT_SCHEMA_READY; calibration=INITIAL_BASELINE_NEEDS_FIELD_DATA; controller_injection=STAGE9_BATCH
```

Investigation found that this value is read from persisted WCUQ status state rather than recomputed per turn. This creates a false-confidence surface: the displayed number looks current but is actually a historical calibration/status surface.

## Current state

- The WCUQ display is stale/static and should be treated as untrusted until repaired.
- Post-rubric repair artifacts proved several fixes in local OS packets, but not all are yet native in the full exported OS bundle.
- Gemini external review required the comparative artifact to be reframed as an **Internal Deterministic Process Enforcement Matrix**, locked at **28/40**, with H capped at **1** until independent state-graph/security review exists.

## Desired state

- The Visual Tracker must never present stale WCUQ state as a live score.
- WCUQ status must distinguish `live_score`, `last_known_calibration`, and `stale_or_unavailable`.
- Proven Stage004G/Stage004H repairs must be promoted into the native OS export, not left only in runtime analysis packets.
- External-review amendments must be carried forward into registry/export state.
- Export/audit workflows must remain bounded, resumable, and hygienic.

## Action items

| ID | Priority | Item | Acceptance criteria |
|---|---:|---|---|
| WQ1 | P0 | Add WCUQ freshness gate | Tracker shows `WCUQ stale/unavailable` when status is older than allowed freshness window or lacks current turn/input signature. |
| WQ2 | P0 | Separate WCUQ calibration from live score | `runtime/state/WCUQ_STATUS.*` or successor schema explicitly separates calibration baseline from live per-turn measurement. |
| WQ3 | P0 | Refresh WCUQ from current receipts or suppress it | Boot either writes a current WCUQ receipt-derived display value or omits the numeric score from Visual Tracker. |
| WQ4 | P1 | Add WCUQ receipt signatures | WCUQ receipts include turn id, task, source context/input signature, timestamp, score source, and freshness decision. |
| WQ5 | P1 | Add Visual Tracker stale-display regression test | Test fails if a stale WCUQ status file can render as a current numeric score. |
| CR1 | P0 | Promote Stage004G official fast-proof tool and harness patches into native export | Full OS export contains `cold_restore_fast_path_proof_v1.py` Stage004G+ behavior and release audit harness accepts valid fast-proof receipts without timeout false-fail. |
| CR2 | P0 | Promote Gemini-amended matrix registry | Native OS export contains the amended Internal Deterministic Process Enforcement Matrix, 28/40 score, H-index cap, and PASS_WITH_AMENDMENTS disposition. |
| CR3 | P1 | Make final harness rerun deterministic/resumable | Stage004H-style final lock readiness no longer depends on a prior Stage004G receipt because fresh harness rerun can checkpoint/resume and write `audit_result.json`. |
| CR4 | P1 | Codify export hygiene exclusions | Export manifest excludes generated cold-restore/extract work directories while preserving receipts, reports, manifests, sidecars, and proof artifacts. |
| CR5 | P2 | Promote minor self-heal normalization gate | Low-risk lexical variants like `Forbidden Pass`, `Forbidden-Pass`, and `forbidden_pass` are canonicalized through a shared validator with negative fixtures for semantic/security changes. |
| CR6 | P1 | Build independent state-graph/security audit path | H score cannot exceed 1 until a separate parser/reviewer audits state graph and security boundaries independently of MetaBlooms self-certification. |
| CR7 | P1 | Add Stage004E router-security regression tests | `universal-select-tool` remains local/read-only/unprotected while Track B hosted-smoke protected commands remain protected. |

## Non-goals

- Do not raise MetaBlooms H score based on Gemini packet review alone.
- Do not present the internal matrix as an independent security audit.
- Do not treat WCUQ calibration baseline as a live per-turn quality score.
- Do not weaken hosted-smoke requirements for protected Track B operations.

## Suggested next governed stage

```text
WCUQ_STATIC_SCORE_STAGE001_FRESHNESS_GATE_AND_TRACKER_REPAIR
```

Followed by:

```text
METABLOOMS_OS_POST_RUBRIC_REPAIR_STAGE001_PROMOTE_004G_AND_GEMINI_AMENDMENTS_TO_NATIVE_EXPORT
```

## Review notes

This item should remain open until the repairs are present in a rebuilt full OS export and validated through a cold-restore or equivalent bounded fast-path proof.
