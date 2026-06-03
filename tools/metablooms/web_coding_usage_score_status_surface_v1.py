#!/usr/bin/env python3
"""WCUQ Visual Tracker status surface writer (v2 schema)."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _score_text(score: Any, band: Any, ready: Any, gate_decision: Any) -> str:
    return f"score {score}; band {band}; promotion_ready={ready}; gate={gate_decision}"


def compact(validation: dict[str, Any] | None, gate: dict[str, Any] | None) -> dict[str, Any]:
    """Build the v2 WCUQ Visual Tracker status object.

    v1 stored a single free-text score surface. That made it possible for a
    historical calibration score to be rendered as if it were live. v2 separates
    live per-turn scores from last-known calibration and stale/unavailable state.
    """
    now = utc_now()
    gate_decision = (gate or {}).get('decision', 'not gated')
    if not validation:
        return {
            'schema': 'mb.quality_scoring.wcuq_visual_teacher_status.v2',
            'created_at_utc': now,
            'status_state': 'stale_or_unavailable',
            'display_text': 'WCUQ stale/unavailable; numeric score suppressed',
            'live_score': None,
            'last_known_calibration': None,
            'stale_or_unavailable': {
                'reason': 'validation_missing',
                'numeric_score_suppressed': True,
            },
            'sources': {'validation': None, 'gate': None},
        }
    score = (validation.get('score_result') or {}).get('final_score')
    band = (validation.get('band') or {}).get('band')
    ready = validation.get('promotion_ready')
    display = _score_text(score, band, ready, gate_decision)
    return {
        'schema': 'mb.quality_scoring.wcuq_visual_teacher_status.v2',
        'created_at_utc': now,
        'status_state': 'live_score',
        'display_text': display,
        'live_score': {
            'score': score,
            'band': band,
            'promotion_ready': ready,
            'gate_decision': gate_decision,
            'score_text': display,
        },
        'last_known_calibration': None,
        'stale_or_unavailable': None,
        'sources': {'validation': None, 'gate': None},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", default="")
    ap.add_argument("--gate", default="")
    ap.add_argument("--extra", default="")
    ap.add_argument("--out_txt", default="runtime/state/WCUQ_STATUS.txt")
    ap.add_argument("--out_json", default="runtime/state/WCUQ_STATUS.json")
    args = ap.parse_args()
    root = Path.cwd()
    validation = read_json(Path(args.validation).resolve()) if args.validation else None
    gate = read_json(Path(args.gate).resolve()) if args.gate else None
    status = compact(validation, gate)
    status['sources'] = {'validation': args.validation, 'gate': args.gate}
    if args.extra:
        if status.get('status_state') == 'live_score' and status.get('display_text'):
            status['display_text'] = status['display_text'] + '; ' + args.extra
            if isinstance(status.get('live_score'), dict):
                status['live_score']['score_text'] = status['display_text']
        else:
            status.setdefault('stale_or_unavailable', {})['extra'] = args.extra
    text = str(status.get('display_text') or 'WCUQ stale/unavailable; numeric score suppressed')
    out_txt = Path(args.out_txt); out_json = Path(args.out_json)
    if not out_txt.is_absolute(): out_txt = root / out_txt
    if not out_json.is_absolute(): out_json = root / out_json
    write(out_txt, text + '\n')
    write(out_json, json.dumps(status, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'decision': 'PASS', 'text': text, 'out_txt': str(out_txt)}, indent=2))
    return 0

if __name__ == '__main__': raise SystemExit(main())
