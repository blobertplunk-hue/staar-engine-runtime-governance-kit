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

## Open action items at a glance

| ID | Source | Item | Status | Blocks |
|---|---|---|---|---|
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
