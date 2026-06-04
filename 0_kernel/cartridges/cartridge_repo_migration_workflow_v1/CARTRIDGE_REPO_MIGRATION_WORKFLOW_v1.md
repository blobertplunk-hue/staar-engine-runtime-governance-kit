# MetaBlooms Cartridge Repository Migration Workflow v1

## Purpose

This workflow governs the promotion of mature MetaBlooms cartridge families out of the central OS/governance repository and into dedicated family repositories, while preserving discoverability through a central registry pointer.

## Decision

Use a hybrid architecture:

- central governance / registry repo remains the control plane;
- mature executable cartridge families get dedicated repositories;
- small or experimental cartridges remain embedded;
- large fixtures and generated bundles move to release assets or external artifact storage;
- the old path remains as a compatibility pointer.

## Evidence-backed reasoning

GitHub rulesets support branch, tag, and push rules, including controls that can restrict updates, require status checks, and enforce push rules. This supports a governance repo plus dedicated family repos where each family can have appropriate policy strictness.

GitHub reusable workflows allow common CI logic to be shared from one workflow into many repositories through `workflow_call`, reducing duplicated CI across cartridge-family repositories.

GitHub CODEOWNERS can automatically request review from owners for path ownership, which supports dedicated ownership per cartridge family.

GitHub Releases are designed for downloadable release artifacts and notes, making them better than raw Git history for large fixture packs and exported bundles.

GitHub repository guidance warns against large blobs and recommends keeping repos manageable; this supports keeping generated artifacts and large fixtures out of normal Git history.

GitHub template repositories allow repeatable repo scaffolding, which supports consistent cartridge-family repo creation.

GitHub Packages can host runnable package/container outputs when a cartridge becomes installable.

## Required migration gates

A cartridge family may be externalized only when all required gates pass:

1. source/runtime/generated files are classified;
2. unknown and private/secret classifications are zero;
3. executable source and schemas have tests or validators;
4. large fixtures are split into release assets or artifact pointers;
5. dedicated repo skeleton has README, CARTRIDGE.md, cartridge_contract.json, CODEOWNERS, and CI;
6. first release or commit SHA is recorded;
7. central registry entry points to repo, commit, release tag, and artifacts;
8. old embedded path is replaced by a compatibility pointer;
9. OS resolver can locate the external cartridge by registry pointer;
10. rollback pointer remains available.

## Workflow stages

### S0 Intake and freeze

Capture family ID, old paths, current artifact digests, active branches, open PRs, and owner intent. No mutation.

### S1 Classification

Classify each file as source, schema, tests, fixture-small, fixture-large, generated, runtime-state, receipt, secret/private, or unknown. Fail closed on unknown or secret/private.

### S2 Promotion decision

Apply promotion gates. Keep embedded if the family is markdown-only, experimental, or does not yet have executable/testable value.

### S3 Repository creation or resolution

Resolve existing dedicated repo first. If absent, create from `metablooms-cartridge-template` or equivalent scaffold.

### S4 Source projection

Project source, schema, tests, docs, and small fixtures. Do not copy runtime state or generated receipts as source.

### S5 Artifact split

Move large fixtures, PDFs, binary bundles, and exported OS bundles to release assets or artifact pointers with SHA-256 sidecars.

### S6 CI and ownership

Install reusable workflow caller, CODEOWNERS, branch/ruleset requirements, and validator entrypoints.

### S7 Registry pointer update

Write central `cartridge_index.json` entry with repo URL, commit SHA, release tag, artifact digests, resolver mode, and rollback pointer.

### S8 Compatibility stub

Replace old embedded source location with pointer files: `CARTRIDGE_POINTER.json` and `README_POINTER.md`.

### S9 Validation

Run family repo CI, registry validator, resolver smoke test, and OS boot/import smoke. Fail closed if any required gate fails.

### S10 Handoff

Write migration receipt, update improvement log, tag chat URL/provenance, and stop with next-step handoff.

## Output artifacts

- cartridge migration receipt
- registry pointer update
- dedicated repo PR
- governance repo PR
- release asset pointer ledger
- rollback pointer

## Default first migration order

1. GitHub sync / chat work registry cartridge
2. PDF cartridge
3. Spreadsheet cartridge
4. Recipe cartridge
5. Finance cartridge
6. TEKS cartridge

Reason: GitHub sync should migrate first because it becomes the cross-chat and cross-repo control plane used by later migrations.
