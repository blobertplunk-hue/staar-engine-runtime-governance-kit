import hashlib, json, pathlib, subprocess, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'governance/jobs/mb_install_v0/run_job_governance_checks.py'


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


class ClaudeCodeMbInstallJobGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        fp = self.p / name
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(text, encoding='utf-8')
        return fp

    def packet(self, decision='BLOCK_STAGE9_PREFLIGHT_PENDING_TARGET_TREE', extra_receipt=None, ci=None):
        self.write('COMMAND_TRANSCRIPT.txt', 'no mutations\n')
        self.write('REPRODUCE.sh', 'echo reproduce\n')
        self.write('REPRODUCE.ps1', 'Write-Output reproduce\n')
        receipt = {'stage_id': 's', 'decision': decision, 'score_source': 'execution', 'mutations_performed': [], 'forbidden_actions': {'apply': 'NOT_RUN'}, 'next_stage': 'MB_INSTALL_V0_STAGE9R_MANIFEST_RESTAMP_AND_REVALIDATION'}
        if extra_receipt:
            receipt.update(extra_receipt)
        manifest = {'stage_id': 's', 'decision': decision, 'score_source': 'execution', 'mutations_performed': [], 'forbidden_actions': {'apply': 'NOT_RUN'}, 'artifacts': {}}
        self.write('EXECUTION_RECEIPT.json', json.dumps(receipt))
        self.write('EVIDENCE_MANIFEST.json', json.dumps(manifest))
        if ci:
            self.write('CI_CONFIRMATION.json', json.dumps(ci))
        names = ['COMMAND_TRANSCRIPT.txt', 'EXECUTION_RECEIPT.json', 'REPRODUCE.sh', 'REPRODUCE.ps1']
        self.write('ARTIFACT_SHA256SUMS.txt', ''.join(f'{sha(self.p/n)}  {n}\n' for n in names))

    def run_check(self):
        return subprocess.run([sys.executable, str(RUNNER), '--stage', 's', '--evidence-path', str(self.p), '--mode', 'pre-report'], cwd=ROOT, text=True, capture_output=True)

    def test_accepts_valid_block_packet(self):
        self.packet()
        self.assertEqual(0, self.run_check().returncode)

    def test_rejects_to_be_filled_placeholder(self):
        self.packet()
        self.write('EVIDENCE_MANIFEST.json', json.dumps({'stage_id': 's', 'decision': 'PASS', 'score_source': 'execution', 'mutations_performed': [], 'forbidden_actions': {}, 'commit_sha': 'TO_BE_FILLED'}))
        self.assertNotEqual(0, self.run_check().returncode)

    def test_rejects_stale_sha_chain(self):
        self.packet()
        self.write('COMMAND_TRANSCRIPT.txt', 'changed')
        self.assertNotEqual(0, self.run_check().returncode)

    def test_rejects_manifest_self_hash(self):
        self.packet()
        self.write('EVIDENCE_MANIFEST.json', json.dumps({'stage_id': 's', 'decision': 'PASS', 'score_source': 'execution', 'mutations_performed': [], 'forbidden_actions': {}, 'artifacts': {'EVIDENCE_MANIFEST.json': 'abc'}}))
        self.assertNotEqual(0, self.run_check().returncode)

    def test_rejects_unqualified_ci_closed(self):
        self.packet(ci={'status': 'SUBSTANTIALLY_CLOSED'})
        self.assertNotEqual(0, self.run_check().returncode)

    def test_accepts_ci_substantial_with_residual(self):
        self.packet(ci={'classification': 'SUBSTANTIALLY_CLOSED_WITH_RESIDUAL', 'run_id': 1, 'head_sha': 'a', 'tested_sha': 'b', 'residual_status': 'direct sha absent', 'relationship': 'evidence only'})
        self.assertEqual(0, self.run_check().returncode)

    def test_rejects_live_apply_without_fields(self):
        self.packet(extra_receipt={'live_apply_authorized': True})
        self.assertNotEqual(0, self.run_check().returncode)

    def test_rejects_atomic_swap_without_fields(self):
        self.packet(extra_receipt={'atomic_swap_authorized': True})
        self.assertNotEqual(0, self.run_check().returncode)

    def test_rejects_block_to_execution(self):
        self.packet(extra_receipt={'next_stage': 'MB_INSTALL_V0_STAGE10_EXECUTION'})
        self.assertNotEqual(0, self.run_check().returncode)

    def test_rejects_done_without_reproduce(self):
        self.packet()
        (self.p / 'REPRODUCE.sh').unlink()
        self.assertNotEqual(0, self.run_check().returncode)


if __name__ == '__main__':
    unittest.main()
