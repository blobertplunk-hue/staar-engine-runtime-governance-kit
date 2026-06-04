from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / 'governance/github_os_sync/PATH_CLASSIFICATION_RULES_v1.json'
POLICY = ROOT / 'governance/github_os_sync/STRICT_PARITY_GENERATED_RUNTIME_STATE_POLICY_v1.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def classify(path: str):
    doc = load(RULES)
    candidates = []
    for r in doc['rules']:
        if r.get('pattern') == path:
            candidates.append((10000, r))
        elif 'prefix' in r and path.startswith(r['prefix']):
            candidates.append((len(r['prefix']), r))
        elif 'suffix' in r and path.endswith(r['suffix']):
            candidates.append((len(r['suffix']), r))
        elif 'contains' in r and r['contains'] in path:
            candidates.append((len(r['contains']), r))
    return sorted(candidates, key=lambda x: x[0])[-1][1] if candidates else {'class': doc['default_decision']}


def test_active_tracker_preview_excluded_from_strict_parity():
    r = classify('runtime/state/ACTIVE_TRACKER_PREVIEW.txt')
    assert r['class'] == 'generated_runtime_state'
    assert r['strict_parity'] is False


def test_active_work_excluded_from_strict_parity():
    r = classify('runtime/state/ACTIVE_WORK.json')
    assert r['class'] == 'generated_runtime_state'
    assert r['strict_parity'] is False


def test_other_runtime_state_still_os_authoritative():
    r = classify('runtime/state/WCUQ_STATUS.json')
    assert r['class'] == 'os_authoritative'


def test_strict_parity_policy_reports_generated_drift_paths():
    p = load(POLICY)
    assert p['strict_parity'] is True
    drift = p['generated_runtime_state']
    assert drift['strict_parity'] is False
    assert drift['count_in_generated_drift'] is True
    assert drift['count_in_strict_denominator'] is False
    assert 'runtime/state/ACTIVE_TRACKER_PREVIEW.txt' in drift['paths']
    assert 'runtime/state/ACTIVE_WORK.json' in drift['paths']


if __name__ == '__main__':
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            try:
                fn()
                print(name + ': PASS')
            except Exception as e:
                failed += 1
                print(name + ': FAIL ' + repr(e))
    raise SystemExit(1 if failed else 0)
