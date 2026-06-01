# MetaBlooms checkpoint — Stage011C Export Debt Decision Atom

Decision: FULL_EXPORT_REQUIRED

Packet: /mnt/data/STAGE011C_EXPORT_DEBT_DECISION_ATOM_20260601T014011Z.zip
Packet SHA-256: d6ea81a65ebedff64dedd361128ac420a4091b69a1dcb7eb7304f41c389ae7d5

Router: PASS_ATOM_READY for E0_EXPORT_DEBT_DECISION.

Reason codes:
- Latest offsite floor predates Stage007 runtime tooling.
- Remote Recovery Ledger changed after the latest offsite floor.
- Project Pack tooling changed after the latest offsite floor.
- Atomic export router changed after the latest offsite floor.
- Visual Tracker changed after the latest offsite floor.
- Local exports exist but are not cold-verified, Project-packed, externalized, landed, and pointer-updated as the durable remote floor.

Latest offsite floor:
- METABLOOMS_FULL_OS_EXPORT_RECOVERED_DURABLE_FULL_OS_EXPORT_20260531T2244Z.tar.zst
- SHA-256 e544267babc40ea2f8cbc841c0904e74dc2928c1cbba08021037423ef2028e64

Local newer candidates:
- METABLOOMS_FULL_OS_EXPORT_EMERGENCY_FULL_OS_DOWNLOAD_20260601T012636Z.tar.zst
- METABLOOMS_FULL_OS_EXPORT_POST_STAGE007_PROJECT_PACK_STAGE011_20260601T0020Z.tar.zst

Next: STAGE011D_PREFLIGHT_FREEZE_ATOM_E1A_BOOT_MERKLE

Claim boundary: this atom only decides export debt. No archive build, Project Pack assembly, cold restore, externalization, landed receipt import, or pointer update was performed.
