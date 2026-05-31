# Recovery From /mnt/data + GitHub Plan — Adversarial Audit

## Verdict
The plan is directionally correct, but it is not yet sufficient as a fully autonomous recovery system. It has a good floor and a good transport split, but it still depends on several implicit assumptions that must be turned into artifacts, stable pointers, and executable recovery gates.

## High-risk flaws found

1. **Weak GitHub release retrieval pointer.** The landed receipt proves the Stage10A asset was uploaded and binary-readback verified, but it does not include `asset_id`, `release_id`, `browser_download_url`, or API URL. It has repo/tag/asset name, which is recoverable with `gh` or REST search, but not a direct immutable retrieval pointer.

2. **No stable latest pointer in GitHub.** The pushed runbook is timestamped. A future chat can recover it only if it already knows the path or searches correctly. There is no stable `metablooms_recovery/LATEST.json` pointer.

3. **Runbook is not an executable recovery harness.** The runbook tells what to do, but it is not a one-command recovery harness. It does not stage-extract, verify tools, select local-vs-GitHub source, or promote only after boot/Merkle.

4. **GitHub connector overlay semantics are under-specified.** The plan says to import connector checkpoints as governance overlays, but does not define order, conflict handling, schema validation, or whether checkpoint text is authoritative over local OS artifacts.

5. **Stage003 unavailable state may fossilize.** Marking Stage003 unavailable is correct from current bytes, but the plan can accidentally treat unavailable as permanent truth rather than current evidence state.

6. **/mnt/data start-state assumption is not precise enough.** The plan says recover from files already present in `/mnt/data`, but not every future chat will necessarily inherit the same `/mnt/data` contents. It needs a minimum recovery set definition and a decision tree when parts are missing.

7. **No cold-restore drill from GitHub-only source.** We proved upload/readback on the phone, but did not yet prove a new sandbox can recover using only GitHub references when local archive is missing.

8. **Fresh full OS export is still missing.** The current durable floor is Stage10A plus later small policy/checkpoint overlays. That is recoverable, but not ideal. The system still lacks a new full OS export that includes the newly encoded governance, router, policies, fixtures, and recovery runbook.

## Corrected recovery architecture

1. Stable pointers: GitHub stores `LATEST.json`, floor pointer, checkpoint index, and runbook.
2. Full floor: large binary release asset, binary-readback proven.
3. Small continuity overlay: connector-pushed text artifacts, ordered by manifest.
4. Executable recovery harness: local-first restore, GitHub fallback, staging extraction, boot/Merkle, promote only after pass.
5. Periodic full export: after major governance changes, collapse floor+overlays into a new full OS export to reduce overlay complexity.

## Updated next action
Do not jump directly to general forward work. Next stage should be:

`RECOVERY_POINTERS_AND_EXECUTABLE_HARNESS_STAGE004`

It should write stable GitHub pointers, build the recovery harness, and push a connector checkpoint. Then run `PRODUCE_RECOVERED_DURABLE_FULL_OS_EXPORT` to collapse the current overlay stack into a new full baseline.
