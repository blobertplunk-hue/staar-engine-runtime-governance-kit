#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REPO_RE = re.compile(r'^[^/]+/[^/]+$')
SHA40_RE = re.compile(r'^[0-9a-f]{40}$')
SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
EXTERNAL_REQUIRED = {'repo_full_name', 'commit_sha', 'release_tag', 'pointer_path', 'resolver_required'}
NO_UNKNOWN_REQUIRED = {'unknown': 0, 'secret_or_private': 0}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        raise SystemExit(f'FAIL invalid JSON {path}: {e}')


def fail(msg):
    print('FAIL ' + msg)
    raise SystemExit(1)


def validate_registry(path: Path):
    doc = load_json(path)
    if doc.get('schema') != 'mb.cartridge_registry.v1':
        fail('registry schema must be mb.cartridge_registry.v1')
    families = doc.get('families')
    if not isinstance(families, list) or not families:
        fail('registry families must be a non-empty list')
    for fam in families:
        fid = fam.get('family_id')
        if not fid:
            fail('family missing family_id')
        status = fam.get('status')
        if status not in {'embedded','candidate','externalizing','externalized','rollback'}:
            fail(f'{fid}: invalid status {status}')
        if not fam.get('old_paths'):
            fail(f'{fid}: missing old_paths')
        cls = fam.get('path_classification_summary') or {}
        for k,v in NO_UNKNOWN_REQUIRED.items():
            if int(cls.get(k,0)) != v:
                fail(f'{fid}: classification {k} must be {v}')
        gates = fam.get('promotion_state') or {}
        if gates.get('gates_blocked'):
            fail(f'{fid}: blocked gates remain: {gates.get("gates_blocked")}')
        if status == 'externalized':
            for key in EXTERNAL_REQUIRED:
                if not fam.get(key):
                    fail(f'{fid}: externalized missing {key}')
            if not REPO_RE.match(fam['repo_full_name']):
                fail(f'{fid}: invalid repo_full_name')
            if not SHA40_RE.match(fam['commit_sha']):
                fail(f'{fid}: commit_sha must be 40 lowercase hex chars')
            for artifact in fam.get('artifacts', []):
                if not SHA256_RE.match(artifact.get('sha256','')):
                    fail(f'{fid}: artifact {artifact.get("name")} missing valid sha256')
    print(f'PASS registry valid: families={len(families)}')


def validate_family_repo(repo: Path):
    required = ['README.md','CARTRIDGE.md','cartridge_contract.json','.github/CODEOWNERS']
    missing = [p for p in required if not (repo/p).exists()]
    if missing:
        fail('family repo missing required files: ' + ', '.join(missing))
    if not any((repo/'.github/workflows').glob('*.yml')) and not any((repo/'.github/workflows').glob('*.yaml')):
        fail('family repo missing GitHub workflow')
    contract = load_json(repo/'cartridge_contract.json')
    if not contract.get('family_id'):
        fail('cartridge_contract.json missing family_id')
    print('PASS family repo skeleton valid')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--registry')
    ap.add_argument('--repo', default='.')
    ap.add_argument('--mode', choices=['registry','family-repo','both'], default='registry')
    ns = ap.parse_args()
    repo = Path(ns.repo)
    if ns.mode in {'registry','both'}:
        reg = Path(ns.registry) if ns.registry else repo/'cartridge_index.json'
        validate_registry(reg)
    if ns.mode in {'family-repo','both'}:
        validate_family_repo(repo)

if __name__ == '__main__':
    main()
