# Side-Chat to GitHub Sandbox Tool Research Workflow — Revamp

Generated: 2026-06-01T11:18Z  
Repo target: `blobertplunk-hue/staar-engine-runtime-governance-kit`  
Side-chat role: research/incubation stream, not direct main-OS mutation  
Main-OS role: later importer/promoter in a different chat  
Default next packet: `SHELL_COREUTILS_JQ_TAR_OFFBEAT_RESEARCH_PACKET_001`

## 1. Root correction

The previous plan treated the side chat too much like a local OS implementation stage. The revised plan separates four layers:

1. **Side-chat research layer** — discovers sources, extracts practices, compares against current assistant behavior, and writes portable artifacts.
2. **GitHub relay layer** — publishes distilled, machine-readable research packets to the STARR repo so any future chat can retrieve them.
3. **Main-OS intake layer** — later imports GitHub packets into `/mnt/data/Metablooms_OS` through governed intake, not chat memory.
4. **Promotion layer** — turns accepted lessons into validators, gates, fixtures, command templates, or cartridges.

This prevents side-chat findings from being mistaken for installed OS behavior.

## 2. Evidence basis

The search method uses multivocal literature review principles because the goal is not only official documentation. It explicitly includes blogs, white papers, practitioner notes, issue discussions, Q&A threads, postmortems, and unusual workflows. Garousi/Felderer/Mäntylä define multivocal literature reviews as systematic reviews that include grey literature such as blog posts and white papers in addition to formal literature, and emphasize source-quality assessment for that material.

The search strategy is hybrid: seeded web search plus backward/forward snowballing plus off-path practitioner search. Hybrid search research in software engineering reports that combining database search and snowballing can identify more relevant studies than database search alone; one replicated study found a hybrid strategy identified 30% more primary studies.

The GitHub relay is based on repository contents and git database semantics. GitHub's repository contents REST API creates or replaces repository files and explicitly warns serial use is required for content mutation conflicts. GitHub's contents API also has directory/file-size constraints, so larger or multi-file packets should prefer commit/tree flows or release/artifact strategies.

Artifact provenance should be carried as hashes, metadata, and optional attestation where available. GitHub artifact attestations are designed to establish provenance for builds; side-chat artifacts should be ready for later attestation even if this chat only creates files and checksums.

## 3. Tool routing rule

`file_search` is **not** used for this workflow unless the task is specifically to inspect uploaded files. This research workflow uses:

- `web.run` for current external evidence and source discovery.
- `container`/shell for local artifact generation, checksums, receipts, and packaging.
- `GitHub` connector for STARR repo publication when available.
- `/mnt/data/Metablooms_OS` only for boot receipts and local handoff state.

If native `git clone` fails in the sandbox, use the GitHub connector as the relay path. Do not call the repository inaccessible until connector probing also fails.

## 4. Packet output contract

Each side-chat research packet must produce these local files:

```text
<PACKET_ID>/SOURCE_CARDS.jsonl
<PACKET_ID>/SOURCE_MATRIX.md
<PACKET_ID>/OFFBEAT_FINDINGS.md
<PACKET_ID>/COMPARISON_TO_CURRENT_BEHAVIOR.md
<PACKET_ID>/ADOPT_NOW.md
<PACKET_ID>/NEEDS_PROBE.md
<PACKET_ID>/REJECTED_OR_DEMOTED.md
<PACKET_ID>/GITHUB_RELAY_MANIFEST.json
<PACKET_ID>/MAIN_OS_INTAKE_HINTS.md
<PACKET_ID>/SELF_SAR.md
<PACKET_ID>/SHA256SUMS.txt
```

Optional:

```text
<PACKET_ID>/PROPOSED_VALIDATORS/
<PACKET_ID>/PROPOSED_FIXTURES/
<PACKET_ID>/COMMAND_TEMPLATES/
```

## 5. GitHub relay contract

Every packet sent to GitHub must land under:

```text
metablooms_sidechat_research/<YYYYMMDD>/<PACKET_ID>/
```

Minimum files to publish:

```text
README.md
SOURCE_MATRIX.md
ADOPT_NOW.md
NEEDS_PROBE.md
GITHUB_RELAY_MANIFEST.json
MAIN_OS_INTAKE_HINTS.md
SELF_SAR.md
SHA256SUMS.txt
```

`README.md` must include:

- packet id
- source count
- source classes
- high-value offbeat findings
- current assistant behavior gaps
- proposed OS artifacts
- pass/block state
- exact next main-OS intake prompt

## 6. Machine-enforced gates

A packet cannot be marked PASS unless all of these pass:

| Gate | Pass rule |
|---|---|
| BOOT_GATE | `/mnt/data/Metablooms_OS` boot was attempted and recorded, or blocker documented. |
| SOURCE_COUNT_GATE | 20–100 sources. |
| SOURCE_DIVERSITY_GATE | At least 30% offbeat/practitioner/problem sources. |
| AUTHORITY_GATE | At least 25% official, standards, peer-reviewed, or maintainer-authored sources. |
| CURRENTNESS_GATE | For tools likely to change, at least 50% of operational docs must be current or explicitly versioned. |
| CLAIM_TRACE_GATE | Every recommendation maps to at least one source card. |
| COMPARISON_GATE | Every accepted finding compares against current assistant behavior. |
| ADOPTION_GATE | Every `ADOPT_NOW` item maps to a proposed validator, fixture, receipt field, command template, or routing rule. |
| PROBE_GATE | Every uncertain item maps to a concrete probe command and pass/fail criterion. |
| GITHUB_RELAY_GATE | Relay manifest exists and target repo/path is specified. |
| MAIN_OS_INTAKE_GATE | Main-OS import prompt exists and says the side-chat packet is not yet promoted. |
| HASH_GATE | SHA-256 sidecars or SHA256SUMS exist for all local packet files. |
| SELF_SAR_GATE | Self-SAR identifies risks, overclaims, and promotion blockers. |

## 7. Search strategy

For each sandbox tool family, run five search passes:

1. **Official baseline pass** — manuals, specifications, maintainer docs, release notes.
2. **Practitioner excellence pass** — high-signal blogs, postmortems, build notes, toolsmith writeups.
3. **Failure/offbeat pass** — pitfalls, bug reports, incident reports, weird edge cases, anti-patterns.
4. **Adjacent-domain pass** — DevOps, reproducible builds, digital preservation, CI, supply chain security, HPC, embedded, Termux/mobile where relevant.
5. **Snowball pass** — use the best source cards as pearls; follow links, cited tools, maintainers, changelogs, related issues, and terminology.

## 8. Source card schema

Each source becomes one JSONL record with URL, title, author/publisher, date/version, class, authority grade, offbeat score, claims, tool aspect, recommended behavior, current assistant gap, adoption candidate, and risk notes.

## 9. Side-chat to main-OS boundary

The side chat may publish research and proposed deltas to GitHub, but must not claim OS behavior changed permanently, validators are installed, gates are enforced, cartridges are promoted, full OS export is updated, or future chats will use the lesson automatically.

Those claims become valid only after a main-OS intake/promotion stage imports the packet, installs machine-enforced artifacts, validates them, and writes receipts.

## 10. GitHub-first continuity model

Future chats should be able to recover from GitHub even if `/mnt/data` is reset. Therefore each packet must include a copy/pasteable intake prompt:

```text
Boot MetaBlooms from /mnt/data/Metablooms_OS. Use GitHub repo blobertplunk-hue/staar-engine-runtime-governance-kit as the relay source. Import side-chat research packet <PACKET_ID> from metablooms_sidechat_research/<YYYYMMDD>/<PACKET_ID>/. Treat it as NOT_PROMOTED_TO_MAIN_OS. Validate SOURCE_COUNT, SOURCE_DIVERSITY, CLAIM_TRACE, ADOPTION, PROBE, HASH, and SELF_SAR gates. Promote only accepted findings into deterministic OS artifacts, validators, fixtures, command templates, receipt fields, or routing rules. Write intake receipt, promotion decision, and handoff. Do not claim durable behavior until installed and validated.
```

## 11. Recommended next packet

```text
SHELL_COREUTILS_JQ_TAR_OFFBEAT_RESEARCH_PACKET_001
```

Target source mix:

- 8–12 official/manual sources: Bash, GNU coreutils, findutils, tar, jq, ShellCheck, POSIX where relevant.
- 8–15 practitioner/offbeat sources: Bash Pitfalls, ShellCheck wiki/rules, Unix StackExchange high-signal threads, maintainer blogs, failure postmortems.
- 4–10 adjacent-domain sources: reproducible builds, CI shell hardening, digital preservation/archive safety, supply-chain provenance, Termux portability.

Main expected upgrade classes: null-delimited path handling, no parsing `ls`, safe quoting and glob discipline, staged temp directories and atomic promotion, trap/cleanup patterns, `set -euo pipefail` nuance, JSON mutation discipline with `jq`, tar path safety and deterministic archive listing, timeout/cancellation semantics, checksum manifest generation and verification.

## 12. Pass/block output states

```text
PASS_READY_FOR_GITHUB_RELAY
PASS_RELAYED_TO_GITHUB_NOT_PROMOTED
BLOCKED_RESEARCH_INSUFFICIENT
BLOCKED_GITHUB_RELAY_UNAVAILABLE
BLOCKED_HASH_OR_MANIFEST_MISSING
BLOCKED_MAIN_OS_BOOT_UNAVAILABLE
```

Preferred state for this side chat:

```text
PASS_RELAYED_TO_GITHUB_NOT_PROMOTED
```

## 13. Implementation note

If GitHub write is available through the connector, write the packet to the STARR repo immediately. If it is not available, create a local ZIP containing the packet and a GitHub relay instruction file. Do not use `file_search` to retrieve or validate the packet; validate local files directly and use GitHub connector or web-visible GitHub evidence for relay checks.
