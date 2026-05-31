# MetaBlooms checkpoint — new full OS export Termux packet ready

Decision: PACKET_READY_PENDING_DEVICE_LANDED_RECEIPT

Self-contained packet:
`/mnt/data/METABLOOMS_FULL_EXPORT_EXTERNALIZE_TERMUX_PACKET_20260531T2252Z.zip`

Packet SHA-256:
`e9fb274c4150b15e093306c965e7f738675cf2734b879a3011fdcc3e4b90b9bb`

Packet contents:
- recovered durable full OS archive `METABLOOMS_FULL_OS_EXPORT_RECOVERED_DURABLE_FULL_OS_EXPORT_20260531T2244Z.tar.zst`
- archive SHA sidecar
- provenance JSON
- manifest CSV
- one-command Termux runner
- v2 landed receipt schema
- fixtures and validator

Target release:
`MB-FULL-RECOVERED-DURABLE-20260531T2244Z`

Target asset SHA-256:
`e544267babc40ea2f8cbc841c0904e74dc2928c1cbba08021037423ef2028e64`

Claim boundary:
The new full export packet is self-contained and locally ZIP-tested. The new full export is not offsite-proven until Robert runs the packet in Termux and returns a `LANDED_ASSET_FULL_EXPORT_*.json` receipt with binary readback proof.
