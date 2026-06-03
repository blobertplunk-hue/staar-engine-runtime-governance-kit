#!/usr/bin/env python3
"""MetaBlooms GitHub/OS sync gate.

Dependency-free classifier and validation CLI for the GitHub/OS sync control
plane. Matching is fail-closed: unknown paths block movement unless explicitly
classified by a rule.
"""
from __future__ import annotations
import argparse
import fnmatch
import json
import pathlib
from typing import Any, Dict, Iterable, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "governance" / "github_os_sync" / "PATH_CLASSIFICATION_RULES_v1.json"


def load_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _matches(path: str, rule: Dict[str, Any]) -> bool:
    if "pattern" in rule and fnmatch.fnmatch(path, rule["pattern"]):
        return True
    if "prefix" in rule and path.startswith(rule["prefix"]):
        return True
    if "suffix" in rule and path.endswith(rule["suffix"]):
        return True
    if "contains" in rule and rule["contains"] in path:
        return True
    return False


def _specificity(rule: Dict[str, Any]) -> int:
    for key in ("pattern", "prefix", "suffix", "contains"):
        if key in rule:
            return len(str(rule[key]))
    return 0


def classify_path(path: str, rules_doc: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    matches = [r for r in rules_doc.get("rules", []) if _matches(path, r)]
    if not matches:
        return rules_doc.get("default_decision", "UNCLASSIFIED_BLOCK_MOVEMENT"), "no_rule_matched", {}
    safety = set(rules_doc.get("safety_precedence", ["private_excluded", "release_asset_only"]))
    safety_matches = [r for r in matches if r.get("class") in safety]
    pool = safety_matches or matches
    best = max(pool, key=_specificity)
    return best.get("class", rules_doc.get("default_decision", "UNCLASSIFIED_BLOCK_MOVEMENT")), best.get("reason", "matched"), best


def classify(paths: Iterable[str], rules_path: pathlib.Path = RULES_PATH) -> Dict[str, Any]:
    rules = load_json(rules_path)
    rows = []
    blocked = []
    for path in paths:
        cls, reason, rule = classify_path(path, rules)
        rows.append({"path": path, "class": cls, "reason": reason, "rule": rule})
        if cls == "UNCLASSIFIED_BLOCK_MOVEMENT":
            blocked.append(path)
    return {
        "schema": "mb.github_os_sync.classification_result.v1",
        "decision": "PASS" if not blocked else "BLOCKED",
        "blocked_count": len(blocked),
        "paths": rows,
    }


def validate_contracts() -> Dict[str, Any]:
    errors: List[str] = []
    if not RULES_PATH.exists():
        errors.append(f"missing {RULES_PATH}")
    else:
        doc = load_json(RULES_PATH)
        if doc.get("default_decision") != "UNCLASSIFIED_BLOCK_MOVEMENT":
            errors.append("default_decision must fail closed")
        if not isinstance(doc.get("rules"), list) or not doc["rules"]:
            errors.append("rules must be a non-empty list")
        for idx, rule in enumerate(doc.get("rules", [])):
            if "class" not in rule:
                errors.append(f"rule {idx} missing class")
            if not any(k in rule for k in ("pattern", "prefix", "suffix", "contains")):
                errors.append(f"rule {idx} missing matcher")
    return {"schema": "mb.github_os_sync.gate_result.v1", "gate": "validate-contracts", "decision": "PASS" if not errors else "BLOCKED", "errors": errors}


def validate_authority_map(path: pathlib.Path) -> Dict[str, Any]:
    errors: List[str] = []
    doc = load_json(path)
    entries = doc.get("path_authorities", [])
    if not any(e.get("path") == "governance/github_os_sync/SYNC_AUTHORITY_MAP_v1.json" and e.get("authority_class") == "os_authoritative_with_github_pr_proposal_path" for e in entries):
        errors.append("SYNC_AUTHORITY_MAP_v1.json must be os_authoritative_with_github_pr_proposal_path")
    for entry in entries:
        if entry.get("authority_class") == "bidirectional_source" and entry.get("diverged") and not entry.get("human_merge_receipt"):
            errors.append(f"{entry.get('path')} diverged bidirectional_source requires human merge receipt")
    try:
        unclassifiable = int(doc.get("divergence_summary", {}).get("unclassifiable_split_brain_paths", 0))
    except Exception:
        unclassifiable = 101
    if unclassifiable > 100:
        errors.append(f"unclassifiable_split_brain_paths {unclassifiable} > 100")
    return {"schema": "mb.github_os_sync.gate_result.v1", "gate": "validate-authority-map", "decision": "PASS" if not errors else "BLOCKED", "errors": errors}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate-contracts")
    classify_parser = sub.add_parser("classify-paths")
    classify_parser.add_argument("paths", nargs="+")
    map_parser = sub.add_parser("validate-authority-map")
    map_parser.add_argument("path")
    args = parser.parse_args(argv)
    if args.cmd == "validate-contracts":
        result = validate_contracts()
    elif args.cmd == "classify-paths":
        result = classify(args.paths)
    elif args.cmd == "validate-authority-map":
        result = validate_authority_map(pathlib.Path(args.path))
    else:
        raise AssertionError(args.cmd)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("decision") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
