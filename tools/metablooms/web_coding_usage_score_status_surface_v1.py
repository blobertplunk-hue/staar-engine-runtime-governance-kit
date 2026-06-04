#!/usr/bin/env python3
"""WCUQ status surface writer for Visual Tracker v2."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
SUPPRESS="WCUQ stale/unavailable; numeric score suppressed"
def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def compact(status_state='stale_or_unavailable', live_score=None):
    return {"schema":"mb.quality_scoring.wcuq_visual_teacher_status.v2","created_at_utc":utc(),"status_state":status_state,"display_text":SUPPRESS if status_state!='live_score' else str(live_score),"live_score":live_score if status_state=='live_score' else None,"last_known_calibration":None,"stale_or_unavailable":{"numeric_score_suppressed":status_state!='live_score'},"sources":{}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out', default='runtime/state/WCUQ_STATUS.json'); ns=ap.parse_args()
    p=Path(ns.out); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(compact(), indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(f"WCUQ_STATUS_WRITTEN {p}")
if __name__=='__main__': main()
