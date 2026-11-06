"""Offline launcher tests; tests hors ligne de l’interface de maintenance.

No TeX builds, source downloads, publication or historical source edits.
A successful mock checks routing, not the underlying scientific claim.
"""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "research.py"
SPEC = importlib.util.spec_from_file_location("research_tools", SCRIPT)
research = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research)


class ResearchToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "new-output"
        self.raw_log = self.root / "raw.log"
        self.source277 = self.root / "source277"
        self.source278 = self.root / "source278"
        self.source277.mkdir()
        self.source278.mkdir()

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = research.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def arguments(self, command):
        if command == "package":
            return ["--output", str(self.output)]
        if command == "reproduce":
            return ["--output", str(self.output), "--source277", str(self.source277),
                    "--source278", str(self.source278)]
        if command == "counterexamples":
            return ["--output", str(self.output), "--source278", str(self.source278)]
        return []

    def test_complete_help_in_each_language_does_not_execute(self):
        for language, heading, usage in (("en", "CONTINUITY Ω", "usage:"),
                                         ("fr", "CONTINUITÉ Ω", "utilisation :")):
            with self.subTest(language=language), patch.object(research.subprocess, "run") as run:
                code, stdout, stderr = self.invoke("--help", "--language", language)
            self.assertEqual(0, code)
            self.assertEqual("", stderr)
            self.assertIn(heading, stdout)
            self.assertIn(usage, stdout)
            for command in research.SCRIPTS:
                self.assertIn(command, stdout)
            for option in research.VALUES | research.SWITCHES:
                self.assertIn(option, stdout)
            self.assertIn("docs/RESEARCH_TOOLS", stdout)
            run.assert_not_called()
        self.assertNotIn("usage:", stdout)
        self.assertNotIn("Required", stdout)

    def test_command_help_needs_no_required_paths(self):
        with patch.object(research.subprocess, "run") as run:
            for command in research.SCRIPTS:
                code, stdout, stderr = self.invoke(command, "-h", "--language=fr")
                self.assertEqual(0, code)
                self.assertIn("utilisation :", stdout)
                self.assertEqual("", stderr)
            run.assert_not_called()

    def test_only_fixed_commands_are_executed_in_both_languages(self):
        for language in ("en", "fr"):
            for command, script in research.SCRIPTS.items():
                with self.subTest(language=language, command=command), patch.object(
                        research.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
                    code, stdout, stderr = self.invoke(command, "--language", language, *self.arguments(command))
                self.assertEqual(0, code)
                self.assertEqual("", stderr)
                self.assertIn(research.TEXT[language]["success"][command], stdout)
                argv = run.call_args.args[0]
                self.assertEqual([research.sys.executable, "-B", "-s", str(research.PAPER / script)], argv[:4])
                self.assertNotIn("shell", run.call_args.kwargs)
                self.assertEqual(research.PAPER, run.call_args.kwargs["cwd"])
                self.assertEqual(subprocess.DEVNULL, run.call_args.kwargs["stdout"])
                self.assertEqual(subprocess.STDOUT, run.call_args.kwargs["stderr"])
                self.assertFalse(self.output.exists())

    def test_interface_language_and_paper_language_are_independent(self):
        for interface in ("en", "fr"):
            for paper in ("en", "fr", "all"):
                with patch.object(research.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
                    code, stdout, stderr = self.invoke("--language", interface, "build", "--paper-language=" + paper)
                self.assertEqual(0, code)
                self.assertEqual(["--language", paper], run.call_args.args[0][4:])
                self.assertIn(research.TEXT[interface]["success"]["build"], stdout)
                self.assertNotIn("--publish", run.call_args.args[0])
        with patch.object(research.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(0, self.invoke("build", "--language", "fr")[0])
            self.assertEqual(["--language", "all"], run.call_args.args[0][4:])

    def test_verify_check_build_is_forwarded_without_building(self):
        with patch.object(research.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(0, self.invoke("verify", "--check-build")[0])
            self.assertEqual(["--check-build"], run.call_args.args[0][4:])
            self.assertEqual(1, run.call_count)

    def test_all_validation_errors_are_localized_and_do_not_execute(self):
        cases = [[], ["wat"], ["verify", "pooling"], ["--language"], ["--language", "zz"],
                 ["--language", "fr", "--language", "fr"], ["verify", "--wat"],
                 ["build", "--publish"], ["build", "--paper-language", "zz"],
                 ["pooling", "--output", str(self.output)], ["verify", "--paper-language", "fr"],
                 ["package"], ["package", "--output"], ["counterexamples", "--output", str(self.output)],
                 ["reproduce", "--output", str(self.output)], ["--help=false"],
                 ["verify", "--check-build=true"], ["verify", "; touch /tmp/UNAUTHORIZED"],
                 ["--help", "--source278", str(self.source278)], ["build", "--paper-language="],
                 ["verify", "--", "--help"]]
        for args in cases:
            with self.subTest(args=args), patch.object(research.subprocess, "run") as run:
                code, stdout, stderr = self.invoke(*args, "--language=fr")
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("Invocation refusée", stderr)
            self.assertIn("utilisation :", stderr)
            self.assertNotIn("Traceback", stderr)
            self.assertNotIn("usage:", stderr)
            run.assert_not_called()

    def test_downloads_require_explicit_opt_in_for_each_missing_snapshot(self):
        with patch.object(research.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            for sources in ([], ["--source277", str(self.source277)], ["--source278", str(self.source278)]):
                run.reset_mock()
                args = ["reproduce", "--output", str(self.output), *sources]
                self.assertEqual(2, self.invoke(*args)[0])
                run.assert_not_called()
                code, stdout, stderr = self.invoke(*args, "--download-sources", "--language", "fr")
                self.assertEqual(0, code)
                self.assertIn("peuvent être téléchargées", stdout)
                self.assertNotIn("--download-sources", run.call_args.args[0])

    def test_raw_log_is_explicit_untranslated_and_never_echoed(self):
        original = b"Historical technical error: NOT_TRANSLATED\n{\"verdict\": \"FAIL\"}\n"

        def execute(command, **kwargs):
            kwargs["stdout"].write(original)
            return subprocess.CompletedProcess(command, 7)

        with patch.object(research.subprocess, "run", side_effect=execute):
            code, stdout, stderr = self.invoke("verify", "--raw-log", str(self.raw_log), "--language", "fr")
        self.assertEqual(7, code)
        self.assertEqual(original, self.raw_log.read_bytes())
        self.assertIn("non traduite", stdout)
        self.assertIn(str(self.raw_log), stdout)
        self.assertIn("Échec de verify (code de sortie 7)", stderr)
        self.assertNotIn("NOT_TRANSLATED", stdout + stderr)
        self.assertNotIn("checks passed", stdout + stderr)

    def test_failure_and_signal_codes_are_preserved(self):
        for backend, expected in ((1, 1), (2, 2), (3, 3), (-15, 143)):
            with patch.object(research.subprocess, "run", return_value=subprocess.CompletedProcess([], backend)):
                code, stdout, stderr = self.invoke("counterexamples", "--language", "fr", *self.arguments("counterexamples"))
            self.assertEqual(expected, code)
            self.assertIn("Échec de counterexamples", stderr)
            self.assertNotIn("ont été reproduites", stdout)

    def test_launch_failure_and_interruption_do_not_leak_english_exception(self):
        for error, expected, fragment in ((OSError("RAW_ENGLISH_ERROR"), 1, "Impossible de démarrer"),
                                           (KeyboardInterrupt(), 130, "Exécution interrompue")):
            with patch.object(research.subprocess, "run", side_effect=error):
                code, stdout, stderr = self.invoke("pooling", "--language", "fr")
            self.assertEqual(expected, code)
            self.assertIn(fragment, stderr)
            self.assertNotIn("RAW_ENGLISH_ERROR", stdout + stderr)
            self.assertNotIn("Traceback", stdout + stderr)

    def test_execution_environment_avoids_bytecode_and_pythonpath_injection(self):
        with patch.dict(research.os.environ, {"PYTHONPATH": "/tmp/untrusted", "PYTHONDONTWRITEBYTECODE": "0"}), patch.object(
                research.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(0, self.invoke("pooling")[0])
        env = run.call_args.kwargs["env"]
        self.assertNotIn("PYTHONPATH", env)
        self.assertEqual("1", env["PYTHONDONTWRITEBYTECODE"])
        self.assertEqual("1", env["PYTHONNOUSERSITE"])

    def test_outputs_and_logs_cannot_modify_repository_sources_or_existing_paths(self):
        existing = self.root / "existing"
        existing.write_text("preserve", encoding="utf-8")
        linked = self.root / "linked"
        linked.symlink_to(existing)
        broken = self.root / "broken"
        broken.symlink_to(self.root / "absent")
        alias = self.root / "repo-alias"
        alias.symlink_to(research.ROOT, target_is_directory=True)
        for option in ("--output", "--raw-log"):
            for path in (Path("relative"), existing, linked, broken,
                         research.ROOT / "forbidden-new", alias / "forbidden-new"):
                args = ["package", "--output", str(path)] if option == "--output" else ["pooling", "--raw-log", str(path)]
                with self.subTest(option=option, path=path), patch.object(research.subprocess, "run") as run:
                    self.assertEqual(2, self.invoke(*args, "--language", "fr")[0])
                    run.assert_not_called()
        self.assertEqual("preserve", existing.read_text(encoding="utf-8"))
        self.assertFalse((research.ROOT / "forbidden-new").exists())

    def test_supplied_sources_are_protected_from_logs_and_output(self):
        for option in ("--output", "--raw-log"):
            args = ["counterexamples", "--source278", str(self.source278), "--output", str(self.output)]
            if option == "--output":
                args[-1] = str(self.source278 / "new")
            else:
                args.extend(["--raw-log", str(self.source278 / "new.log")])
            with patch.object(research.subprocess, "run") as run:
                self.assertEqual(2, self.invoke(*args)[0])
                run.assert_not_called()
            self.assertEqual([], list(self.source278.iterdir()))

    def test_raw_log_parent_and_output_overlap_are_validated_before_execution(self):
        for path in (self.root / "missing" / "raw.log", self.output, self.output / "raw.log"):
            with self.subTest(path=path), patch.object(research.subprocess, "run") as run:
                self.assertEqual(2, self.invoke("package", "--output", str(self.output), "--raw-log", str(path))[0])
                run.assert_not_called()
            self.assertFalse(self.output.exists())

    def test_invalid_paths_and_symlink_loops_are_localized(self):
        loop = self.root / "loop"
        loop.symlink_to(loop)
        cases = ["bad\0path", "bad\npath", str(loop), str(loop / "new")]
        for path in cases:
            with self.subTest(path=path), patch.object(research.subprocess, "run") as run:
                code, stdout, stderr = self.invoke("package", "--output", path, "--language", "fr")
            self.assertEqual(2, code)
            self.assertIn("Invocation refusée", stderr)
            self.assertNotIn("Traceback", stderr)
            run.assert_not_called()

    def test_missing_source_directory_is_localized(self):
        with patch.object(research.subprocess, "run") as run:
            code, stdout, stderr = self.invoke("counterexamples", "--source278", str(self.root / "absent"),
                                                "--output", str(self.output), "--language", "fr")
        self.assertEqual(2, code)
        self.assertIn("répertoire de sources existant", stderr)
        run.assert_not_called()

    def test_changed_or_symlinked_historical_scripts_refuse_execution(self):
        paper = self.root / "paper"
        paper.mkdir()
        files = {}
        for name in research.HISTORICAL_SCRIPTS:
            data = (research.PAPER / name).read_bytes()
            (paper / name).write_bytes(data)
            files[name] = hashlib.sha256(data).hexdigest()
        manifest = paper / "PUBLICATION.json"
        manifest.write_text(json.dumps({"files": files}), encoding="utf-8")
        with patch.object(research, "PAPER", paper):
            research.check_script_identities()
            original = (paper / "verify.py").read_bytes()
            for mode in ("modified", "symlink", "missing_manifest"):
                path = paper / "verify.py"
                path.write_bytes(original + b"\n# changed")
                if mode == "symlink":
                    path.unlink()
                    path.symlink_to(research.ROOT / "docs" / "continuity-omega-paper" / "verify.py")
                if mode == "missing_manifest":
                    path.unlink()
                    path.write_bytes(original)
                    manifest.unlink()
                with self.subTest(mode=mode), patch.object(research.subprocess, "run") as run:
                    code, stdout, stderr = self.invoke("pooling", "--language", "fr")
                self.assertEqual(2, code)
                self.assertIn("script historique", stderr)
                run.assert_not_called()
                if path.is_symlink():
                    path.unlink()

    def test_build_refuses_symlinked_output_directory(self):
        paper = self.root / "paper"
        paper.mkdir()
        build = paper / "build"
        build.symlink_to(self.source278, target_is_directory=True)
        with patch.object(research, "PAPER", paper), patch.object(research.subprocess, "run") as run:
            code, stdout, stderr = self.invoke("build", "--language", "fr")
        self.assertEqual(2, code)
        self.assertIn("sans liens symboliques", stderr)
        run.assert_not_called()

    def test_real_pooling_is_offline_and_preserves_all_historical_script_bytes(self):
        before = {name: (research.PAPER / name).read_bytes() for name in research.HISTORICAL_SCRIPTS}
        code, stdout, stderr = self.invoke("pooling", "--language", "fr", "--raw-log", str(self.raw_log))
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        raw = json.loads(self.raw_log.read_text(encoding="utf-8"))
        self.assertEqual(3, raw["minimum_buyers_for_nonnegative_contribution"])
        self.assertEqual(2, raw["maximum_buyers_for_simultaneous_capacity"])
        self.assertEqual([], raw["feasible_counts"])
        self.assertIn("mutualisation", stdout)
        self.assertIn("not prices", raw["scope"])
        self.assertEqual(before, {name: (research.PAPER / name).read_bytes() for name in before})


if __name__ == "__main__":
    unittest.main()
