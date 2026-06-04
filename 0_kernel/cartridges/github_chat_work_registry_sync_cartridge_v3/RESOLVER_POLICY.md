# Repository Resolver Policy

The executable resolver is included in the authoritative sandbox artifact:

`github_chat_work_registry_sync_cartridge_v3_20260604T203120Z.zip`

SHA-256:

`80c5c5a0797c5d0197a9544e796bba156cd4c9374c3fc3e6e5f55f6b645f6ed2`

## Required behavior

The cartridge, not the user, resolves the repository first.

Resolution order:

1. Existing `.metablooms/chat_work_registry/` records.
2. Artifact provenance and manifests.
3. Git remote configuration.
4. Prior MetaBlooms receipts.
5. Installed GitHub repository search.
6. GitHub code or file search for strong marker files.
7. Name similarity only as weak evidence.

## Ask-user conditions

Ask the user only when:

- no safe repository candidate is found; or
- multiple candidates tie too closely to resolve safely.

## Current resolution for this work

Registry target:

`blobertplunk-hue/staar-engine-runtime-governance-kit`

Reason:

The installed GitHub repository search found this repo with admin, maintain, pull, push, and triage permissions and default branch `main`. The sibling `staar-engine-runtime-governance-kit-v2` was size 1 and therefore scored below the active governance repo.
