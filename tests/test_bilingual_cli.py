"""Offline bilingual interface checks, not qualification of the historical checker.

Contrôles de l’interface bilingue hors ligne, sans qualification du vérificateur.
"""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('bilingual_cli', ROOT / 'scripts' / 'continuity.py')
cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)


class BilingualCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def historical_demo(self, directory, scenario='nominal'):
        with redirect_stdout(io.StringIO()):
            return cli.historical_cli.main(['demo', '--case', scenario, '--out', str(directory)])

    def snapshot(self, directory):
        return {str(path.relative_to(directory)): path.read_bytes()
                for path in directory.rglob('*') if path.is_file()}

    def test_all_scenarios_preserve_historical_bytes_and_make_both_reports(self):
        self.assertEqual(set(cli.CASES), set(cli.CASE_DESCRIPTIONS))
        for scenario in cli.CASES:
            baseline = self.root / (scenario + '-historical')
            original_code = self.historical_demo(baseline, scenario)
            for language in ('en', 'fr'):
                evidence = self.root / (scenario + '-' + language)
                with self.subTest(scenario=scenario, language=language):
                    code, stdout, stderr = self.invoke('demo', '--case', scenario, '--out', str(evidence), '--language', language)
                    self.assertEqual(original_code, code)
                    self.assertEqual('', stderr)
                    self.assertEqual(self.snapshot(baseline), self.snapshot(evidence))
                    reports = evidence.with_name(evidence.name + '-reports')
                    self.assertEqual({'PASSPORT.en.md', 'PASSPORT.fr.md'}, set(self.snapshot(reports)))
                    for report_language in ('en', 'fr'):
                        self.assertEqual(cli.reader.present(evidence, report_language),
                                         (reports / ('PASSPORT.' + report_language + '.md')).read_text(encoding='utf-8'))
                    self.assertIn('Verdict consigné' if language == 'fr' else 'Recorded verdict', stdout)
                    self.assertIn('aucune certification tierce' if language == 'fr' else 'third-party certification', stdout)
                    if original_code == 2:
                        self.assertIn('REJECTED_BEFORE_HANDOFF', stdout)
                        receipt = json.loads((evidence / 'REJECTION.json').read_text())
                        self.assertIn(cli.reader.reason_description(receipt['reason'], language), stdout)

    def test_help_is_localized_at_root_and_for_all_commands(self):
        for command in (None, 'demo', 'verify', 'inspect'):
            prefix = [] if command is None else [command]
            for language in ('en', 'fr'):
                for spelling in (['--language', language], ['--language=' + language]):
                    with self.subTest(command=command, language=language, spelling=spelling):
                        code, stdout, stderr = self.invoke(*prefix, '--help', *spelling)
                        self.assertEqual(0, code)
                        self.assertEqual('', stderr)
                        self.assertIn('utilisation :' if language == 'fr' else 'usage:', stdout)
                        self.assertIn('Afficher cette aide' if language == 'fr' else 'Show this help', stdout)
                        if language == 'fr':
                            self.assertNotIn('usage:', stdout)
                            self.assertNotIn('show this help', stdout)
                            self.assertNotIn('positional arguments:', stdout)
                            self.assertNotIn('options:', stdout)

    def test_language_can_precede_or_follow_subcommand(self):
        evidence = self.root / 'evidence'
        self.historical_demo(evidence)
        for args in (('--language', 'fr', 'verify'), ('verify', '--language', 'fr')):
            code, stdout, stderr = self.invoke(*args, '--in-dir', str(evidence))
            self.assertEqual(0, code)
            self.assertEqual('', stderr)
            self.assertIn('Résultat du nouveau contrôle historique', stdout)
        code, stdout, stderr = self.invoke('--language', 'fr', 'verify', '--language', 'en', '--in-dir', str(evidence))
        self.assertEqual(0, code)
        self.assertIn('Fresh historical checker result', stdout)

    def test_argument_errors_are_localized_without_tracebacks(self):
        invalid_arguments = [[], ['demo'], ['verify'], ['inspect'], ['missing-command'],
                             ['demo', '--out'], ['demo', '--unknown'],
                             ['demo', '--case', 'unknown', '--out', 'unused'],
                             ['--language', 'unknown'], ['--lang', 'fr'],
                             ['verify', '--in-dir', 'unused', '--json', '--out', 'unused']]
        for args in invalid_arguments:
            with self.subTest(args=args):
                code, stdout, stderr = self.invoke('--language', 'fr', *args)
                self.assertEqual(2, code)
                self.assertEqual('', stdout)
                self.assertIn('Opération refusée', stderr)
                self.assertIn('Arguments invalides', stderr)
                self.assertNotIn('Traceback', stderr)
                self.assertNotIn('error:', stderr)

    def test_empty_invocation_shows_help(self):
        code, stdout, stderr = self.invoke()
        self.assertEqual(0, code)
        self.assertIn('CONTINUITY Ω', stdout)
        self.assertEqual('', stderr)

    def test_demo_json_remains_machine_readable_and_creates_reports(self):
        evidence = self.root / 'evidence'
        reports = self.root / 'custom-reports'
        code, stdout, stderr = self.invoke('demo', '--language', 'fr', '--out', str(evidence),
                                           '--reports-dir', str(reports), '--json')
        self.assertEqual(0, code)
        self.assertEqual('', stderr)
        self.assertEqual({'directory': str(evidence), 'verdict': 'PASS_SYNTHETIC_ONLY',
                          'orders': 2, 'units': 1900, 'restore_findings': 3}, json.loads(stdout))
        self.assertTrue((reports / 'PASSPORT.fr.md').is_file())

    def test_existing_or_overlapping_outputs_are_refused_before_writes(self):
        existing = self.root / 'existing'
        existing.mkdir()
        (existing / 'preserve').write_text('original')
        before = self.snapshot(self.root)
        pairs = [(existing, self.root / 'new-reports'),
                 (self.root / 'new-evidence', existing),
                 (self.root / 'same', self.root / 'same'),
                 (self.root / 'outer', self.root / 'outer' / 'reports'),
                 (self.root / 'outer' / 'evidence', self.root / 'outer')]
        for evidence, reports in pairs:
            with self.subTest(evidence=evidence, reports=reports):
                code, stdout, stderr = self.invoke('demo', '--language', 'fr', '--out', str(evidence), '--reports-dir', str(reports))
                self.assertEqual(2, code)
                self.assertEqual('', stdout)
                self.assertIn('Opération refusée', stderr)
                self.assertEqual(before, self.snapshot(self.root))

    def test_dangling_links_and_loops_have_localized_refusals(self):
        dangling = self.root / 'dangling'
        dangling.symlink_to(self.root / 'absent')
        loop = self.root / 'loop'
        loop.symlink_to(loop)
        for path in (dangling, loop):
            for command, flag in (('demo', '--out'), ('inspect', '--in-dir')):
                code, stdout, stderr = self.invoke(command, '--language', 'fr', flag, str(path))
                self.assertEqual(2, code)
                self.assertEqual('', stdout)
                self.assertNotIn('Traceback', stderr)
                self.assertIn('refusée', stderr)

    def test_fresh_verification_and_saved_inspection_are_distinct_and_read_only(self):
        evidence = self.root / 'evidence'
        self.historical_demo(evidence)
        handoff_path = evidence / 'HANDOFF.json'
        handoff = json.loads(handoff_path.read_text())
        handoff['required_units'] = 1
        handoff_path.write_text(json.dumps(handoff), encoding='utf-8')
        before = self.snapshot(evidence)
        for language in ('en', 'fr'):
            code, stdout, stderr = self.invoke('verify', '--in-dir', str(evidence), '--language', language)
            self.assertEqual(3, code)
            self.assertEqual('', stderr)
            self.assertIn('FAIL', stdout)
            self.assertIn('REQUIRED_UNITS', stdout)
            self.assertIn('Quantité requise incohérente' if language == 'fr' else 'Failed condition: required units', stdout)
            self.assertIn('n’a été ni lu ni mis à jour' if language == 'fr' else 'was not read or updated', stdout)
            code, stdout, stderr = self.invoke('inspect', '--in-dir', str(evidence), '--language', language)
            self.assertEqual(0, code)
            self.assertEqual('', stderr)
            self.assertIn('PASS_SYNTHETIC_ONLY', stdout)
            self.assertIn('Aucun nouvel audit' if language == 'fr' else 'No fresh audit', stdout)
        self.assertEqual(before, self.snapshot(evidence))

    def test_verify_ignores_saved_audit_and_matches_original_checker(self):
        evidence = self.root / 'evidence'
        self.historical_demo(evidence)
        (evidence / 'AUDIT.json').write_text('not JSON', encoding='utf-8')
        before = self.snapshot(evidence)
        inputs = [json.loads((evidence / name).read_text()) for name in ('INPUT.json', 'HANDOFF.json', 'PASSPORT.json')]
        for language in ('en', 'fr'):
            code, stdout, stderr = self.invoke('verify', '--in-dir', str(evidence), '--language', language, '--json')
            self.assertEqual(0, code)
            self.assertEqual('', stderr)
            self.assertEqual(cli.audit(*inputs), json.loads(stdout))
        self.assertEqual(before, self.snapshot(evidence))

    def test_malformed_and_missing_verification_inputs_do_not_become_verdicts(self):
        evidence = self.root / 'evidence'
        self.historical_demo(evidence)
        for raw in ('{', 'null', '[]', '42', '{"objective": [1]}'):
            (evidence / 'INPUT.json').write_text(raw, encoding='utf-8')
            before = self.snapshot(evidence)
            code, stdout, stderr = self.invoke('verify', '--language', 'fr', '--in-dir', str(evidence))
            self.assertEqual(3, code)
            self.assertEqual('', stdout)
            self.assertIn('Aucun nouveau verdict', stderr)
            self.assertNotIn('PASS_SYNTHETIC_ONLY', stderr)
            self.assertNotIn('Traceback', stderr)
            self.assertEqual(before, self.snapshot(evidence))
        code, stdout, stderr = self.invoke('verify', '--language', 'en', '--in-dir', str(self.root / 'absent'))
        self.assertEqual(3, code)
        self.assertIn('No fresh verdict', stderr)

    def test_malformed_shape_that_checker_can_reject_keeps_its_completed_verdict(self):
        evidence = self.root / 'evidence'
        self.historical_demo(evidence)
        (evidence / 'INPUT.json').write_text('{"source_events": [null]}', encoding='utf-8')
        inputs = [json.loads((evidence / name).read_text()) for name in ('INPUT.json', 'HANDOFF.json', 'PASSPORT.json')]
        code, stdout, stderr = self.invoke('verify', '--language', 'fr', '--in-dir', str(evidence), '--json')
        self.assertEqual(3, code)
        self.assertEqual('', stderr)
        self.assertEqual(cli.audit(*inputs), json.loads(stdout))
        self.assertEqual('FAIL', json.loads(stdout)['verdict'])

    def test_inspect_can_write_a_separate_report_but_not_into_evidence(self):
        evidence = self.root / 'evidence'
        self.historical_demo(evidence)
        before = self.snapshot(evidence)
        report = self.root / 'reading.fr.md'
        code, stdout, stderr = self.invoke('inspect', '--language', 'fr', '--in-dir', str(evidence), '--out', str(report))
        self.assertEqual(0, code)
        self.assertIn('aucun nouvel audit', stdout)
        self.assertEqual('', stderr)
        self.assertEqual(cli.reader.present(evidence, 'fr'), report.read_text(encoding='utf-8'))
        for path in (report, evidence / 'reading.fr.md'):
            code, stdout, stderr = self.invoke('inspect', '--language', 'fr', '--in-dir', str(evidence), '--out', str(path))
            self.assertEqual(2, code)
            self.assertEqual('', stdout)
            self.assertIn('Opération refusée', stderr)
        self.assertEqual(before, self.snapshot(evidence))

    def test_output_io_failure_does_not_claim_no_artifacts_were_created(self):
        evidence = self.root / 'evidence'
        blocker = self.root / 'file'
        blocker.write_text('not a directory')
        code, stdout, stderr = self.invoke('demo', '--language', 'fr', '--out', str(evidence),
                                           '--reports-dir', str(blocker / 'reports'))
        self.assertEqual(2, code)
        self.assertEqual('', stdout)
        self.assertIn('peuvent être incomplets', stderr)
        self.assertNotIn('aucun élément probant', stderr)
        self.assertTrue((evidence / 'AUDIT.json').is_file())

    def test_historical_demo_argument_refusals_do_not_leak_english(self):
        def refuse(*args):
            print('usage: historical English error', file=sys.stderr)
            raise SystemExit(2)
        with patch.object(cli.historical_cli, 'main', side_effect=refuse):
            code, stdout, stderr = self.invoke('demo', '--language', 'fr', '--out', str(self.root / 'evidence'))
        self.assertEqual(2, code)
        self.assertEqual('', stdout)
        self.assertIn('démonstration historique a refusé', stderr)
        self.assertNotIn('English', stderr)

    def test_interruption_is_localized_without_claiming_completion(self):
        with patch.object(cli.historical_cli, 'main', side_effect=KeyboardInterrupt):
            code, stdout, stderr = self.invoke('demo', '--language', 'fr', '--out', str(self.root / 'evidence'))
        self.assertEqual(130, code)
        self.assertEqual('', stdout)
        self.assertIn('Opération interrompue', stderr)
        self.assertIn('peuvent être incomplets', stderr)
        self.assertNotIn('Traceback', stderr)

    def test_script_runs_from_another_working_directory_without_pythonpath(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'continuity.py'),
                                 '--language', 'fr', '--help'], cwd=self.root,
                                capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode)
        self.assertIn('CONTINUITÉ Ω', result.stdout)
        self.assertEqual('', result.stderr)


if __name__ == '__main__':
    unittest.main()
