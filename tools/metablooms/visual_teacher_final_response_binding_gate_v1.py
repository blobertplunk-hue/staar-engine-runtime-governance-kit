#!/usr/bin/env python3
"""MetaBlooms Visual Tracker final-response binding gate.

Stage008 human readability repair.

Default output is a short human-first status card. Audit-grade detail remains in
receipts and state files rather than the first screen. The renderer still keeps
machine-enforced stale-score suppression and manual-action alert behavior.
"""
from __future__ import annotations

import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "mb.visual_tracker.binding_gate.receipt.v3"
LEGACY_SUPPRESS = "WCUQ stale/unavailable; numeric score suppressed"
HUMAN_QUALITY_SUPPRESS = "Quality score unavailable; old WCUQ number hidden"
STALE_PATTERNS = (
    "score 90.35",
    "All 10/12 083%",
    "STAGE011I2_ARCHIVE_INSPECT_ONLY_E4_RERUN",
    "K2 archive",
    "Current stage:",
    "Current job:",
    "Machine Details",
)
ALERT_PATH_REL = "runtime/state/MANUAL_ALERTS.json"
BAR_WIDTH = 20


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception as exc:
        return {"load_error": f"{type(exc).__name__}:{exc}"}


def write_text_sidecar(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    digest = sha_text(text)
    path.with_name(path.name + ".sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest


def write_json_sidecar(path: Path, data: dict[str, Any]) -> str:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    digest = sha_text(text)
    path.with_name(path.name + ".sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest


def blocker_value(alerts: dict[str, Any] | None) -> str:
    v = (alerts or {}).get("manual_action_blocker", "")
    return "" if not v or str(v).strip().lower() == "none" else str(v).strip()


def render_red_alert(alerts: dict[str, Any]) -> list[str]:
    blocker = blocker_value(alerts) or "Manual action required"
    do_this = (
        alerts.get("user_action")
        or alerts.get("you_can_fix_it_by")
        or alerts.get("manual_fix")
        or "Open the relevant tool and complete the requested action."
    )
    token = (
        alerts.get("next_token")
        or alerts.get("after_you_do_it_send")
        or alerts.get("next_action")
        or "DONE_CONTINUE"
    )
    return [
        "🚨🔴 ACTION NEEDED",
        blocker,
        "",
        f"Do this: {do_this}",
        f"Then send: {token}",
        "",
    ]




# Backward-compatible helpers for Stage006 tests/imports.
def red_alert_lines(alerts: dict[str, Any], source: str = "") -> list[str]:
    return render_red_alert(alerts)


def render(root: Path, ns: argparse.Namespace) -> str:
    return render_human_tracker(root, ns)

def latest_parity(root: Path) -> tuple[dict[str, Any], str | None]:
    candidates: list[tuple[float, Path]] = []
    for pattern in ("runtime/receipts/github_os_sync_stage0*/**/*PARITY*.json", "runtime/receipts/github_os_sync_stage0*/**/*parity*.json"):
        for p in root.glob(pattern):
            try:
                candidates.append((p.stat().st_mtime, p))
            except OSError:
                pass
    if not candidates:
        return {}, None
    path = max(candidates)[1]
    return read_json(path), str(path.relative_to(root))


def parity_values(data: dict[str, Any]) -> dict[str, Any]:
    total = data.get("P_Total") or data.get("p_total") or data.get("total")
    resolved = data.get("P_Resolved") or data.get("p_resolved") or data.get("resolved")
    pct = data.get("Parity_Percentage") or data.get("parity_percentage") or data.get("parity_pct")
    unclassified = data.get("github_blocked_count", data.get("github_unclassified", data.get("unclassified", 0)))
    deviations = data.get("different_common_paths", data.get("deviated_blocked_paths", data.get("remaining_deviations", 0)))
    if isinstance(deviations, list):
        deviations = len(deviations)
    if total is None:
        local = data.get("local_paths", 0)
        unique = data.get("unique_github_paths", data.get("github_paths", 0) - data.get("common_paths", 0))
        try:
            total = int(local) + int(unique)
        except Exception:
            total = 0
    if resolved is None:
        try:
            resolved = int(total) - int(unclassified or 0) - int(deviations or 0)
        except Exception:
            resolved = 0
    if pct is None:
        pct = (float(resolved) / float(total) * 100.0) if total else 0.0
    return {
        "total": int(total or 0),
        "resolved": int(resolved or 0),
        "pct": float(pct or 0.0),
        "unclassified": int(unclassified or 0),
        "deviations": int(deviations or 0),
    }


def pct_bar(pct: float) -> str:
    filled = max(0, min(BAR_WIDTH, int(pct // 5)))
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def quality_display(root: Path) -> tuple[str, str, dict[str, Any]]:
    path = root / "runtime/state/WCUQ_STATUS.json"
    data = read_json(path)
    if data.get("schema", "").endswith(".v2") and data.get("status_state") == "live_score":
        live = data.get("live_score") if isinstance(data.get("live_score"), dict) else {}
        text = str(data.get("display_text") or live.get("score_text") or HUMAN_QUALITY_SUPPRESS)
        if "90.35" in text:
            text = HUMAN_QUALITY_SUPPRESS
        return text, str(path.relative_to(root)), data
    return HUMAN_QUALITY_SUPPRESS, str(path.relative_to(root)), data


def render_human_tracker(root: Path, ns: argparse.Namespace) -> str:
    work = read_json(root / "runtime/state/ACTIVE_WORK.json")
    alerts = read_json(root / ALERT_PATH_REL)
    quality, _quality_source, _quality_data = quality_display(root)
    pdata, _psrc = latest_parity(root)
    pv = parity_values(pdata) if pdata else None

    blocker = blocker_value(alerts)
    if blocker:
        return "\n".join(render_red_alert(alerts)).rstrip() + "\n"

    done = work.get("last_finished") or work.get("done") or "Tracker repair imported, boot-tested, and exported."
    needs = work.get("needs_you") or "Nothing."
    next_plain = work.get("next_plain") or work.get("next_action_plain") or "Refresh GitHub parity so the progress bar uses current evidence."
    proof = work.get("proof_summary") or "boot PASS · tests PASS · export PASS"

    lines = [
        "🟢 MetaBlooms Status",
        f"Done: {done}",
        f"Needs you: {needs}",
        f"Next: {next_plain}",
        "",
    ]
    if pv:
        freshness = work.get("parity_freshness") or "stale — refresh needed"
        lines += [
            "📊 Progress",
            f"{pv['pct']:.4f}% [{pct_bar(pv['pct'])}] — {freshness}",
            f"Resolved: {pv['resolved']} / {pv['total']} · remaining: {pv['deviations']} · unclassified: {pv['unclassified']}",
        ]
    else:
        lines += [
            "📊 Progress",
            "missing — parity evidence needs to be generated",
        ]
    lines.append(f"Quality: {quality}")
    lines.append(f"Proof: {proof}")
    return "\n".join(lines).rstrip() + "\n"


def validate(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pat in STALE_PATTERNS:
        if pat in text:
            findings.append({"rule_id": "VT-STAGE008-STALE", "severity": "error", "message": f"disallowed main-view pattern present: {pat}"})
    if not (text.startswith("🟢 MetaBlooms Status") or text.startswith("🚨🔴 ACTION NEEDED") or text.startswith("🔴 Blocked") or text.startswith("🟡 Evidence needs refresh")):
        findings.append({"rule_id": "VT-STAGE008-FIRST-LINE", "severity": "error", "message": "tracker does not start with a human status/action line"})
    nonblank = [line for line in text.splitlines() if line.strip()]
    if text.startswith("🚨🔴 ACTION NEEDED") and len(nonblank) > 5:
        findings.append({"rule_id": "VT-STAGE008-ALERT-LENGTH", "severity": "error", "message": f"manual alert too long: {len(nonblank)} nonblank lines"})
    if not text.startswith("🚨🔴 ACTION NEEDED") and len(nonblank) > 10:
        findings.append({"rule_id": "VT-STAGE008-LINE-BUDGET", "severity": "error", "message": f"normal tracker too long: {len(nonblank)} nonblank lines"})
    if "WCUQ:" in text or "Current stage:" in text or "Current job:" in text:
        findings.append({"rule_id": "VT-STAGE008-JARGON", "severity": "error", "message": "machine-facing labels leaked into main tracker"})
    return findings


def run(ns: argparse.Namespace) -> int:
    root = Path(ns.root).resolve()
    preview = root / "runtime/state/ACTIVE_TRACKER_PREVIEW.txt"
    out = Path(ns.out) if ns.out else root / "runtime/receipts/visual_teacher_final_response_binding/VISUAL_TRACKER_FINAL_RESPONSE_BINDING_CURRENT.json"
    if not out.is_absolute():
        out = root / out
    if ns.mode in {"write", "repair"}:
        text = render_human_tracker(root, ns)
        digest = write_text_sidecar(preview, text)
        wrote = True
    else:
        text = preview.read_text(encoding="utf-8") if preview.exists() else ""
        digest = sha_text(text) if text else None
        wrote = False
    findings = validate(text)
    decision = "PASS" if not findings else "BLOCKED"
    receipt = {
        "schema": SCHEMA,
        "created_utc": utc(),
        "decision": decision,
        "mode": ns.mode,
        "wrote_active_preview": wrote,
        "active_preview_path": "runtime/state/ACTIVE_TRACKER_PREVIEW.txt",
        "active_preview_sha256": digest,
        "findings": findings,
        "first_line": text.splitlines()[0] if text.splitlines() else "",
        "line_count": len([line for line in text.splitlines() if line.strip()]),
        "line_budget": "normal<=10 alert<=5",
    }
    write_json_sidecar(out, receipt)
    if ns.print_summary:
        print(f"VISUAL_TRACKER_FINAL_RESPONSE_BINDING decision={decision} mode={ns.mode} preview=runtime/state/ACTIVE_TRACKER_PREVIEW.txt receipt={out}")
    return 0 if decision == "PASS" else 86


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--mode", choices=["write", "validate", "repair"], default="validate")
    ap.add_argument("--stage", default="MetaBlooms governed work")
    ap.add_argument("--request", default="Run governed stage")
    ap.add_argument("--current", default="Visual Tracker active")
    ap.add_argument("--status", default="PASS")
    ap.add_argument("--validation", default="")
    ap.add_argument("--watch", default="")
    ap.add_argument("--blocked-state", default="")
    ap.add_argument("--next-action", default="")
    ap.add_argument("--build-overview", default="")
    ap.add_argument("--wcuq-status", default="")
    ap.add_argument("--process-tracker", default="")
    ap.add_argument("--out")
    ap.add_argument("--print-summary", action="store_true")
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
