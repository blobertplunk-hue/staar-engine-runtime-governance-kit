#!/usr/bin/env python3
"""Validate WCUQ/Visual Tracker stale-score suppression, Stage008 human view."""
from __future__ import annotations
import argparse, json
from pathlib import Path
STALE=("score 90.35","All 10/12 083%","STAGE011I2_ARCHIVE_INSPECT_ONLY_E4_RERUN","K2 archive")
ACCEPT=("Quality score unavailable; old WCUQ number hidden","WCUQ stale/unavailable; numeric score suppressed")
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--root', default='.'); ap.add_argument('--out', default='runtime/receipts/wcuq_schema_repair/WCUQ_VALIDATOR_RECEIPT.json'); ns=ap.parse_args(argv)
    root=Path(ns.root).resolve(); preview=root/'runtime/state/ACTIVE_TRACKER_PREVIEW.txt'; status=root/'runtime/state/WCUQ_STATUS.json'
    text=preview.read_text(encoding='utf-8') if preview.exists() else ''
    errors=[]
    for pat in STALE:
        if pat in text: errors.append(f'stale pattern present: {pat}')
    if not any(a in text for a in ACCEPT): errors.append('quality suppression text missing')
    try: data=json.loads(status.read_text(encoding='utf-8'))
    except Exception as e: data={}; errors.append(f'WCUQ_STATUS.json unreadable: {type(e).__name__}:{e}')
    if data.get('schema')!='mb.quality_scoring.wcuq_visual_teacher_status.v2': errors.append('WCUQ schema is not v2')
    if data.get('status_state')!='stale_or_unavailable': errors.append('WCUQ status_state is not stale_or_unavailable')
    receipt={"schema":"mb.wcuq.visual_tracker_validator.v2","decision":"PASS" if not errors else "BLOCKED","errors":errors,"accepted_suppression_phrases":list(ACCEPT)}
    out=root/ns.out; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not errors else 87
if __name__=='__main__': raise SystemExit(main())
