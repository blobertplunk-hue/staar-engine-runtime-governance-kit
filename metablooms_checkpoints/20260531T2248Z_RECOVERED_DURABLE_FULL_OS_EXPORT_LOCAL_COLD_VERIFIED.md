# MetaBlooms checkpoint — recovered durable full OS export local cold-verified

Decision: PASS_LOCAL_COLD_VERIFIED_NEW_FULL_OS_EXPORT_CREATED

Archive:
`/mnt/data/METABLOOMS_FULL_OS_EXPORT_RECOVERED_DURABLE_FULL_OS_EXPORT_20260531T2244Z.tar.zst`

Archive SHA-256:
`e544267babc40ea2f8cbc841c0904e74dc2928c1cbba08021037423ef2028e64`

Archive size:
`234503739` bytes

Manifest:
`/mnt/data/METABLOOMS_FULL_OS_EXPORT_RECOVERED_DURABLE_FULL_OS_EXPORT_20260531T2244Z.manifest.csv`

Manifest SHA-256:
`78e4a20a615ef7fe0ebbe580ca2838eb1c4b7a7d5c85773a6fda03df9312e273`

Provenance:
`/mnt/data/METABLOOMS_FULL_OS_EXPORT_RECOVERED_DURABLE_FULL_OS_EXPORT_20260531T2244Z.provenance.json`

Cold verification:
- Manual archive extraction PASS.
- Extracted `portable_full_os_boot_verify.py --json` PASS.
- Extracted root `mpp.sh turn-boot` PASS with LLMI packet.

Claim boundary:
- The no-timeout export orchestrator passed preflight, stabilize, manifest, archive, sha, and inspect.
- Its strict artifact_verify phase timed out in the chat tool call, so this checkpoint does not claim orchestrator artifact_verify PASS.
- The new archive is not offsite-proven until a new landed release-asset receipt is generated.
- Stage003 cold archive remains unavailable.

Next required stage:
`EXTERNALIZE_NEW_FULL_OS_EXPORT_WITH_SELF_CONTAINED_TERMUX_PACKET`
