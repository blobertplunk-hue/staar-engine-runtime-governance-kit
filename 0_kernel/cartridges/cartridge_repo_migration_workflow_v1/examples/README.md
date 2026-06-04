# Cartridge registry example

The executable example registry is included in the authoritative local artifact:

`/mnt/data/cartridge_repo_migration_workflow_v1_20260604T214740Z.zip`

SHA-256 sidecar:

`/mnt/data/cartridge_repo_migration_workflow_v1_20260604T214740Z.zip.sha256`

The example demonstrates an `mb.cartridge_registry.v1` record for an externalized `github_sync_chat_work_registry` family with:

- old embedded cartridge path
- dedicated repo pointer
- commit SHA
- release tag
- compatibility pointer path
- source bundle artifact digest
- zero unknown classifications
- zero secret/private classifications
- no blocked promotion gates

The GitHub connector blocked direct replay of the raw example JSON during this projection, so this README preserves the pointer and summary while the authoritative artifact remains local.
