# CODING_RELIABILITY_SOP_v1

Created: 2026-04-19T00:06:32.845446+00:00

## Purpose
Make coding and patching structurally reliable by forcing:
- bounded changes
- explicit review order
- validator-backed promotion
- artifact-backed receipts

## External grounding
This SOP is aligned to:
- small, focused changes with one purpose
- explicit reviewer context and file order
- validation before merge/promotion
- review criteria that check design, functionality, complexity, tests, naming, comments, and context
- automated formatting/consistency where possible

## Required stage order

### Phase 1 — Contract
Every implementation stage must declare:
- stage_id
- mode: repair / expansion / UI polish / canonicalization
- source_runtime
- target_runtime
- subsystem
- objectives
- must_not_change
- success_conditions
- fail_closed_if

### Phase 2 — Read before patch
Before changing code, the stage must:
- locate the exact target block(s)
- count duplicate definitions for critical functions
- identify the last-winning definition when duplicates exist
- identify dependent event handlers, DOM hooks, validators, and state objects
- identify required companion changes for the subsystem

### Phase 3 — Patch
Patch only the declared subsystem.
Do not mix modes.
Do not silently expand scope.

### Phase 4 — Read after patch
Verify:
- the intended new block exists
- the old broken block is removed or intentionally superseded
- expected before/after counts match the contract
- no later duplicate overrides the intended live path
- the winning code path is the intended one

### Phase 5 — Validate
Run subsystem-specific validators, not syntax only.

### Phase 6 — Promote or fail closed
A runtime may be promoted only if the promotion gate passes.
Otherwise it remains an experiment branch.

## Required coding rules

### Rule 1 — One bounded subsystem per stage
A stage may patch only one subsystem.

### Rule 2 — Read the winning path
Before and after patching, explicitly identify:
- which definition wins
- which handler is live
- which render path is used
- which chooser is called
- which state object is mutated

### Rule 3 — Required companion changes
A subsystem is not complete unless all required companion edits are present.

### Rule 4 — No promotion by vibe
“Looks better” is not enough.
Promotion requires validator pass + receipt.

### Rule 5 — Regression learning must become artifacts
When a failure class appears, add:
- an invariant
- a validator
- a checklist entry
- a patch contract rule

## Failure classes this SOP is meant to block
- patching the wrong block
- leaving shadowed code alive
- forgetting required companion changes
- claiming a family is implemented when it is only half-wired
- skipping a check that should have blocked promotion
