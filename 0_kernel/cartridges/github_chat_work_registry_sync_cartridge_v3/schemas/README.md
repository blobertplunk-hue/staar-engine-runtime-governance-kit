# Schemas

The authoritative schema is included in the sandbox artifact:

`github_chat_work_registry_sync_cartridge_v3_20260604T203120Z.zip`

SHA-256:

`80c5c5a0797c5d0197a9544e796bba156cd4c9374c3fc3e6e5f55f6b645f6ed2`

The schema validates `mb.github.chat_work_session.v1` session records under:

`.metablooms/chat_work_registry/sessions/<work_id>.json`

Required fields include `work_id`, `chat`, `intended_work`, `github.repository_full_name`, `resume.next_step`, artifact pointers, receipt pointers, and `updated_at_utc`.
