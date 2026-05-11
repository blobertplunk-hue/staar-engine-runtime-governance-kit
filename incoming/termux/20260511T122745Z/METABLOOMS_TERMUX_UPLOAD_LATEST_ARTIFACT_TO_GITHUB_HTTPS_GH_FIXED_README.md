# MetaBlooms Termux GitHub uploader — HTTPS/GitHub-CLI fixed version

This version fixes `git@github.com: Permission denied (publickey)` by not using SSH as the default Git transport.

It uses:

- `gh auth login --git-protocol https --web`
- `gh auth setup-git`
- `gh repo clone OWNER/REPO`
- HTTPS origin URL: `https://github.com/blobertplunk-hue/staar-engine-runtime-governance-kit.git`

## Run

```bash
termux-setup-storage
bash /storage/emulated/0/Download/METABLOOMS_TERMUX_UPLOAD_LATEST_ARTIFACT_TO_GITHUB_HTTPS_GH_FIXED_ONESHOT.sh
```

If browser auth opens, authenticate with GitHub. Do not paste tokens into ChatGPT.

## Existing SSH failure cleanup

If a previous run left an SSH clone, this script changes `origin` from `git@github.com:...` to `https://github.com/...` automatically.
