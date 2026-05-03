# Security Policy

## Reporting
Open a private advisory or issue marked security-sensitive. Do not paste secrets into issues.

## Required checks
- GitHub Actions use least-privilege `permissions`.
- Workflow changes require CODEOWNERS review.
- Artifact exports require SHA-256 sidecars and replay proof.
- External write tools require explicit authorization and receipt.
- Dependency updates require lockfile/provenance review.
