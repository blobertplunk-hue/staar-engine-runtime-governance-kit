from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.metablooms.visual_teacher_final_response_binding_gate_v1 import blocker_value, red_alert_lines, render, validate

def load(name): return json.loads((ROOT/'tests/fixtures/visual_tracker'/name).read_text())

def test_blocker_value_none_variants():
    assert blocker_value({'manual_action_blocker':'none'}) == ''
    assert blocker_value({'manual_action_blocker':''}) == ''
    assert blocker_value({}) == ''
    assert blocker_value(None) == ''

def test_blocker_value_active():
    assert blocker_value({'manual_action_blocker':'PR approval required'}) == 'PR approval required'

def test_active_alert_lines_have_required_fields():
    lines='\n'.join(red_alert_lines(load('active_blocker_alerts.json'),'runtime/state/MANUAL_ALERTS.json'))
    assert lines.startswith('🚨🔴 ACTION NEEDED')
    for s in ['PR approval required', 'Do this: Approve the PR manually in GitHub.', 'Then send: GITHUB_STAGE_NEXT']:
        assert s in lines

def test_production_no_blocker_tracker_shape():
    class NS: current='test'; stage='stage'; next_action='next'
    text=render(ROOT, NS())
    assert text.startswith('🟢 MetaBlooms Status')
    assert '🚨🔴 ACTION NEEDED' not in text
    assert 'Needs you: Nothing.' in text
    assert '📊 Progress' in text
    assert 'Quality score unavailable; old WCUQ number hidden' in text
    assert 'Proof:' in text
    assert 'Current stage:' not in text and 'Current job:' not in text and 'Machine Details' not in text
    assert len([l for l in text.splitlines() if l.strip()]) <= 10
    assert not validate(text)

def test_active_blocker_is_short_and_first():
    alerts_path=ROOT/'runtime/state/MANUAL_ALERTS.json'
    original=alerts_path.read_text()
    alerts_path.write_text((ROOT/'tests/fixtures/visual_tracker/active_blocker_alerts.json').read_text())
    try:
        class NS: current='test'; stage='stage'; next_action='next'
        text=render(ROOT, NS())
    finally:
        alerts_path.write_text(original)
    assert text.startswith('🚨🔴 ACTION NEEDED')
    assert '🧭 MetaBlooms Work Status' not in text
    assert 'Do this: Approve the PR manually in GitHub.' in text
    assert 'Then send: GITHUB_STAGE_NEXT' in text
    assert len([l for l in text.splitlines() if l.strip()]) <= 5
    assert not validate(text)

def test_stale_patterns_absent_in_current_preview():
    text=(ROOT/'runtime/state/ACTIVE_TRACKER_PREVIEW.txt').read_text()
    for pat in ('score 90.35','All 10/12 083%','STAGE011I2_ARCHIVE_INSPECT_ONLY_E4_RERUN','K2 archive'):
        assert pat not in text

if __name__=='__main__':
    funcs=[v for k,v in sorted(globals().items()) if k.startswith('test_')]
    failed=0
    for f in funcs:
        try:
            f(); print(f.__name__+': PASS')
        except Exception as e:
            failed+=1; print(f.__name__+': FAIL '+repr(e))
    raise SystemExit(1 if failed else 0)
