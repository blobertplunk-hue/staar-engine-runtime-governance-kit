#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, sys

PLACEHOLDER_RE = re.compile(r"\\b(TO_BE_FILLED|TBD|PLACEHOLDER|UNKNOWN_COMMIT)\\b", re.I)
ALLOWED_CI = {"DIRECTLY_CONFIRMED", "SUBSTANTIALLY_CLOSED_WITH_RESIDUAL", "NOT_CONFIRMED"}
LIVE_REQ = ["target_tree", "responsible_principal", "robert_auth_token_scope", "exact_command", "rollback_plan", "preflight_receipt", "dry_run_receipt", "final_go_no_go_confirmation"]


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def sha256(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)
    else:
        yield obj


def read_sha_sums(path):
    entries = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"malformed sha line: {line}")
        entries[parts[1].lstrip("*")] = parts[0]
    return entries


def validate_evidence_packet(ep):
    p = pathlib.Path(ep)
    errors = []
    required = ["EVIDENCE_MANIFEST.json", "EXECUTION_RECEIPT.json", "COMMAND_TRANSCRIPT.txt", "ARTIFACT_SHA256SUMS.txt", "REPRODUCE.sh", "REPRODUCE.ps1"]
    for name in required:
        if not (p / name).exists():
            errors.append(f"missing required file: {name}")
    for name in ["EVIDENCE_MANIFEST.json", "EXECUTION_RECEIPT.json"]:
        fp = p / name
        if fp.exists():
            obj = load_json(fp)
            bad = [str(v) for v in walk(obj) if isinstance(v, str) and PLACEHOLDER_RE.search(v)]
            if bad:
                errors.append(f"{name} contains placeholder values: {bad[:3]}")
            for field in ["stage_id", "decision", "score_source", "mutations_performed", "forbidden_actions"]:
                if field not in obj:
                    errors.append(f"{name} missing {field}")
            if obj.get("score_source") != "execution":
                errors.append(f"{name} score_source must be execution")
    sums = p / "ARTIFACT_SHA256SUMS.txt"
    if sums.exists():
        try:
            entries = read_sha_sums(sums)
            if "ARTIFACT_SHA256SUMS.txt" in entries:
                errors.append("ARTIFACT_SHA256SUMS.txt must not list itself")
            for name, expected in entries.items():
                fp = p / name
                if not fp.exists():
                    errors.append(f"checksummed artifact missing: {name}")
                elif sha256(fp) != expected:
                    errors.append(f"sha mismatch: {name}")
        except Exception as exc:
            errors.append(str(exc))
    manifest = p / "EVIDENCE_MANIFEST.json"
    if manifest.exists():
        artifacts = load_json(manifest).get("artifacts", {})
        if isinstance(artifacts, dict) and "EVIDENCE_MANIFEST.json" in artifacts:
            errors.append("EVIDENCE_MANIFEST.json must not pin its own SHA inside itself")
    return errors


def validate_authorization(ep):
    p = pathlib.Path(ep)
    merged = {}
    for name in ["AUTHORIZATION_SCOPE.json", "EXECUTION_RECEIPT.json", "EVIDENCE_MANIFEST.json"]:
        fp = p / name
        if fp.exists():
            merged.update(load_json(fp))
    errors = []
    if merged.get("live_apply_authorized") is True:
        missing = [x for x in LIVE_REQ if not merged.get(x)]
        if missing:
            errors.append("live_apply_authorized=true missing: " + ",".join(missing))
    if merged.get("atomic_swap_authorized") is True:
        missing = [x for x in ["target_tree", "exact_command", "rollback_plan", "preflight_receipt", "dry_run_receipt", "final_go_no_go_confirmation"] if not merged.get(x)]
        if missing:
            errors.append("atomic_swap_authorized=true missing: " + ",".join(missing))
    return errors


def validate_ci(ep):
    fp = pathlib.Path(ep) / "CI_CONFIRMATION.json"
    if not fp.exists():
        return []
    c = load_json(fp)
    cls = c.get("classification") or c.get("status")
    errors = []
    if cls == "SUBSTANTIALLY_CLOSED":
        errors.append("CI claim must use SUBSTANTIALLY_CLOSED_WITH_RESIDUAL, not unqualified SUBSTANTIALLY_CLOSED")
    elif cls not in ALLOWED_CI:
        errors.append("CI classification is invalid or absent")
    return errors


def validate_stage_transition(ep):
    fp = pathlib.Path(ep) / "EXECUTION_RECEIPT.json"
    if not fp.exists():
        return []
    r = load_json(fp)
    decision = str(r.get("decision", ""))
    next_stage = str(r.get("next_stage", ""))
    if decision.startswith("BLOCK") and next_stage and not any(x in next_stage.lower() for x in ["repair", "revalid", "governance", "audit"]):
        return [f"blocked decision cannot advance to {next_stage}"]
    return []


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--evidence-path", required=True)
    ap.add_argument("--mode", default="pre-report")
    args = ap.parse_args(argv)
    errors = []
    errors += ["evidence_packet: " + e for e in validate_evidence_packet(args.evidence_path)]
    errors += ["authorization: " + e for e in validate_authorization(args.evidence_path)]
    errors += ["ci: " + e for e in validate_ci(args.evidence_path)]
    errors += ["stage_transition: " + e for e in validate_stage_transition(args.evidence_path)]
    result = {"schema": "mb.claudecode.job_governance_check_result.v1", "stage": args.stage, "evidence_path": args.evidence_path, "mode": args.mode, "decision": "PASS" if not errors else "FAIL_CLOSED", "errors": errors}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
