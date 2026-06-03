# Evidence and justification map

This workflow is evidence-backed. Each major design step is justified by official external sources and current MetaBlooms repo artifacts.

## External sources

| ID | Source | Claim used | Workflow implication |
|---|---|---|---|
| E1 | Anthropic Claude Code overview, https://code.claude.com/docs/en/overview | Claude Code reads codebases, edits files, runs commands, integrates with development tools, creates commits/PRs, and can automate tests/fixes. | Store a repo-native work order with branch, test, commit, and PR requirements. |
| E2 | Anthropic Claude Code hooks, https://code.claude.com/docs/en/hooks | Hooks include `PreToolUse`, can inspect tool input, and can deny tool calls. | Wrong-tool prevention must be implemented as a hook-compatible guard, not prose. |
| E3 | Anthropic Claude Code subagents, https://code.claude.com/docs/en/sub-agents | Built-in and custom subagents can be read-only or all-tools; custom subagents use prompts/tool restrictions. | Separate discovery/review from implementation and require SAR review. |
| E4 | Anthropic Claude Code GitHub Actions, https://code.claude.com/docs/en/github-actions | Claude Code GitHub Actions can implement features, create PRs, and follow project standards. | Require PR output and CI/test receipts. |
| E5 | NIST SP 800-218 SSDF, https://csrc.nist.gov/pubs/sp/800/218/final | SSDF practices help reduce vulnerabilities, mitigate exploitation impact, and address root causes to prevent recurrence. | Repeated blockers must force root-cause routing. |
| E6 | SLSA provenance v1.1, https://slsa.dev/spec/v1.1/provenance | Provenance records where, when, and how artifacts were produced and supports verification/rebuild. | Require source-to-output binding, digests, command ledger, and receipts. |
| E7 | GitHub Actions artifact attestations, https://docs.github.com/en/actions/concepts/security/artifact-attestations | Artifact attestations bind build artifacts to provenance for security and verification. | Future CI integration should publish/attest receipts and workflow outputs. |

## MetaBlooms repo sources

| ID | Repo file | Claim used | Workflow implication |
|---|---|---|---|
| M1 | `governance/improvement_log/METABLOOMS_CHAT790_POSTMORTEM_URGENT_OS_CHANGES_20260602.md` | Mounted `/mnt/data` OS artifact work should use direct filesystem/ZIP/tar/hash tools; file_search should be blocked for mounted OS truth. | Implement tool router policy and fixture. |
| M2 | `audits/METABLOOMS_COMPARATIVE_GOVERNANCE_RUBRIC_20260602.md` | MetaBlooms strength is governance lifecycle, cryptographic receipts, false-pass prevention, and proof; weaknesses include portability/external validation. | Require receipts, tests, and PR rather than narrative. |
| M3 | `governance/improvement_log/NATIVE_METABLOOMS_OS_SOURCE_PATCH_LOCATION_AND_EXPORT_LINEAGE_BINDING_20260602.md` | Native OS source patches are in `/mnt/data/Metablooms_OS`, while the STAAR repo may carry proof artifacts. | PR must distinguish native repo machinery from proof/artifact carrier. |

## Step-by-step justification

1. **Create repo workflow pack instead of a prompt.** Justified by E1/E4: Claude Code can act from repo files, branches, tests, and PRs.
2. **Use hook-compatible tool guard.** Justified by E2 and M1: wrong-tool use must be prevented before execution.
3. **Use repeated-blocker ledger.** Justified by E5: root causes and recurrence prevention are secure-development requirements.
4. **Require fixtures.** Justified by M2: MetaBlooms false-pass prevention requires machine-verifiable proof.
5. **Require provenance and receipts.** Justified by E6/E7/M2: outputs need hash-bound lineage and audit evidence.
6. **Distinguish repo-native work from proof carriers.** Justified by M3: avoid false claims about source application.
