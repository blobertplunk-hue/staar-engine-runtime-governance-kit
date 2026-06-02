# Improvement Log

Forward-looking improvement suggestions for the MetaBlooms OS and STAAR Engine
governance runtime. Each file documents a specific gap, its current state, the
desired state, and concrete action items.

## File naming

`<SYSTEM>_<TOPIC>_IMPROVEMENT_<YYYYMMDD>.md`

## Contents

| File | System | Topic | Priority | Date |
|---|---|---|---|---|
| [BTS_FEEDBACK_LOOP_IMPROVEMENT_20260602.md](BTS_FEEDBACK_LOOP_IMPROVEMENT_20260602.md) | MetaBlooms OS | BTS/learning loop not driving real improvement | HIGH | 2026-06-02 |
| [METABLOOMS_OS_CROSS_SESSION_WORKFLOW_IMPROVEMENT_20260602.md](METABLOOMS_OS_CROSS_SESSION_WORKFLOW_IMPROVEMENT_20260602.md) | MetaBlooms OS | Cross-session coordination missing snapshot and ordered backlog | HIGH | 2026-06-02 |
| [METABLOOMS_OS_AGENT_HARNESS_IMPROVEMENT_20260602.md](METABLOOMS_OS_AGENT_HARNESS_IMPROVEMENT_20260602.md) | MetaBlooms OS | Agent harness plan gaps: stage order, OpenHands risk, context builder, build sequence | HIGH | 2026-06-02 |
| [METABLOOMS_OS_BOOT_AND_RESEARCH_GATE_IMPROVEMENT_20260602.md](METABLOOMS_OS_BOOT_AND_RESEARCH_GATE_IMPROVEMENT_20260602.md) | MetaBlooms OS | Boot blocker recursion, BTS boot contract, and research-gate remediation | CRITICAL | 2026-06-02 |
| [METABLOOMS_OS_VISUAL_FORENSICS_AND_ARTIFACT_INTENT_IMPROVEMENT_20260602.md](METABLOOMS_OS_VISUAL_FORENSICS_AND_ARTIFACT_INTENT_IMPROVEMENT_20260602.md) | MetaBlooms OS | Visual forensics, user correction ledger, generated-map QA, markdown artifact intent | HIGH | 2026-06-02 |
| [METABLOOMS_OS_WCUQ_AND_POST_RUBRIC_REPAIR_IMPROVEMENT_20260602.md](METABLOOMS_OS_WCUQ_AND_POST_RUBRIC_REPAIR_IMPROVEMENT_20260602.md) | MetaBlooms OS | WCUQ stale tracker display and post-rubric repair carry-forward | HIGH | 2026-06-02 |

## Open action items at a glance

| ID | Source | Item | Status | Blocks |
|---|---|---|---|---|
| B1 | Boot | Add recursive boot repair controller | OPEN | B2, B3, B4, B7 |
| B2 | Boot | Add repeated-blocker detection and root-cause repair routing | OPEN | — |
| B3 | Boot | Add boot-contract exception for missing BTS full-decision fields | OPEN | B1 |
| B4 | Boot | Add research-gate remediation contract output | OPEN | B1, B5 |
| B5 | Boot | Add explicit local-only repair exemption path with receipt/SAR | OPEN | B4 |
| B6 | Boot | Couple behavior-changing repairs to export/diff-packet creation and readback validation | OPEN | B1 |
| B7 | Boot | Add boot incident ledger with blocker fingerprints and recurrence counts | OPEN | B1, B2 |
| A1 | BTS | Add Rule 6 to CODING_RELIABILITY_SOP (PASS turns → coverage record) | OPEN | — |
| A2 | BTS | SOP invariant additions cite session receipt in commit message | OPEN | — |
| A3 | BTS | Add turn_class-aware BTS path (audit turns → audit_evidence_quality) | OPEN | — |
| A4 | BTS | Design minimal telemetry export for STAAR engine teacher panel | OPEN | A7 |
| A5 | BTS | Define BTS-quality-to-learning-action mapping as contract | OPEN | A4 |
| A6 | BTS | Version SOP with structured changelog | OPEN | — |
| A7 | BTS | Build real data return path from engines to OS (enables GROUNDED_REAL) | OPEN | A4 |
| W1 | Workflow | Create CURRENT_STATE_SNAPSHOT.md | OPEN | W2 |
| W2 | Workflow | Create IMPROVEMENT_BACKLOG_ORDERED.md | OPEN | — |
| W3 | Workflow | Convention: every planning chat reads snapshot + backlog first | OPEN | W1, W2 |
| W4 | Workflow | Convention: every session updates snapshot + backlog when items close | OPEN | W1, W2 |
| H1 | Harness | Fix ZIP plan stage order: A→B→E→C→D→F | OPEN | — |
| H2 | Harness | Add OpenHands HIGH-risk containment requirement to ZIP plan | OPEN | — |
| H3 | Harness | Write context builder sub-spec (relevance policy, token budget, secret filter) | OPEN | H4 |
| H4 | Harness | Record governance decision: build CH fixture first, graduate to GO later | OPEN | — |
| V1 | Visual | Add forensic_scene_reconstruction_schema | OPEN | V2, V3, V4 |
| V2 | Visual | Add user_correction_supersession_ledger | OPEN | V3, V4, V7 |
| V3 | Visual | Add visual_planning_image_gate before map-like image generation | OPEN | V4 |
| V4 | Visual | Add generated visual QA checks for map-like outputs | OPEN | — |
| V5 | Visual | Add markdown_artifact_intent_gate for downloadable `.md` defaults | OPEN | — |
| V6 | Visual | Add deterministic SVG/HTML renderer for exact planning diagrams | OPEN | V1, V2 |
| V7 | Visual | Add stale-artifact marker for generated images contradicted by user corrections | OPEN | V2 |
| WQ1 | WCUQ | Add WCUQ freshness gate for Visual Tracker | OPEN | WQ2, WQ3, WQ5 |
| WQ2 | WCUQ | Separate calibration baseline from live per-turn WCUQ score | OPEN | WQ1, WQ3 |
| WQ3 | WCUQ | Refresh WCUQ from current receipts or suppress numeric score | OPEN | WQ1 |
| WQ4 | WCUQ | Add WCUQ input signatures and freshness decisions to receipts | OPEN | WQ1 |
| WQ5 | WCUQ | Add Visual Tracker stale-WCUQ regression test | OPEN | WQ1 |
| CR1 | Comparative Rubric | Promote Stage004G fast-proof tool and harness patches into native export | OPEN | CR3 |
| CR2 | Comparative Rubric | Promote Gemini-amended matrix registry into native export | OPEN | — |
| CR3 | Comparative Rubric | Make final harness rerun deterministic and resumable | OPEN | CR1 |
| CR4 | Comparative Rubric | Codify export hygiene exclusions for restore/extract work directories | OPEN | CR3 |
| CR5 | Comparative Rubric | Promote minor self-heal normalization gate | OPEN | — |
| CR6 | Comparative Rubric | Build independent state-graph/security audit path before raising H above 1 | OPEN | — |
| CR7 | Comparative Rubric | Add Stage004E router-security regression tests | OPEN | CR1 |
