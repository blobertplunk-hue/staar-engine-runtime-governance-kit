# MetaBlooms checkpoint — Stage008 cold restore drill

Decision: PARTIAL_PASS_POINTER_DRIVEN_LOCAL_COLD_RESTORE

Packet: /mnt/data/COLD_RESTORE_DRILL_FROM_GITHUB_POINTERS_STAGE008_20260531T2342Z.zip
Packet SHA-256: 785b83fbd6a7d4be21b1a5f9b5e283260ab7e23ff49830832f46faf6561d3d85

Passed:
- GitHub connector fetched LATEST.json.
- GitHub connector fetched FLOOR_POINTERS.json.
- Pointers select recovered durable full OS export 20260531T2244Z.
- Local archive SHA matches pointer SHA e544267babc40ea2f8cbc841c0904e74dc2928c1cbba08021037423ef2028e64.
- Archive extracted to staging.
- Portable full OS verifier passed on staged root.
- Staged root mpp turn-boot passed.
- Fixtures passed.

Blocked boundary:
- The available GitHub connector could not fetch the release-asset binary URL; it only supports repository file URLs for GitHub.fetch.
- Therefore this is not a true connector-only GitHub binary restore.

Next correction:
Build a GitHub release-asset restore packet for Termux or add a supported release-asset binary retrieval lane before claiming true GitHub-only cold restore.
