"""Operator entrypoints, bounded admission and exact suite coverage controls."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from continuity_economy.__main__ import output_guard
from continuity_economy.fixtures import load_fixture, ROOT
from continuity_economy.schema import HarnessError, strict_loads, validate_contract
from continuity_economy.suite import registry, run_suite, safe_relative, verify_suite


class OperatorTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "continuity_economy", *args],
                              cwd=ROOT, capture_output=True, text=True, timeout=10)

    def test_complete_help_and_main_title_in_both_languages(self):
        commands = ("experiment", "demo", "compare", "successor", "challenge", "run", "verify", "verify-suite")
        for language, title in (("en", "CONTINUITY Ω Harness"), ("fr", "CONTINUITÉ Ω")):
            result = self.cli("--language", language, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(title, result.stdout)
            for command in commands:
                self.assertIn(command, result.stdout)
                help_result = self.cli("--language", language, command, "--help")
                self.assertEqual(help_result.returncode, 0, help_result.stderr)
                self.assertIn("Afficher l’aide" if language == "fr" else "Show complete help", help_result.stdout)
            if language == "fr":
                self.assertIn("Inventer l’économie de la continuité", result.stdout)
                self.assertNotIn("Execution", result.stdout)

    def test_bad_arguments_have_stable_code_and_localized_action(self):
        for language, phrase in (("en", "required"), ("fr", "Arguments invalides")):
            result = self.cli("--language", language, "run")
            self.assertEqual(result.returncode, 2)
            error = json.loads(result.stderr)
            self.assertEqual(error["code"], "CLI_ARGUMENT_ERROR")
            self.assertIn(phrase, error["message"])

    def test_existing_output_is_preserved_with_french_error(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "retained.txt"; marker.write_text("original")
            result = self.cli("--language", "fr", "demo", "--out", directory)
            self.assertEqual(result.returncode, 2)
            error = json.loads(result.stderr)
            self.assertEqual(error["code"], "OUTPUT_EXISTS")
            self.assertIn("Aucune appréciation favorable", error["message"])
            self.assertEqual(marker.read_text(), "original")

    def test_source_tree_and_alias_paths_are_refused_before_creation(self):
        with self.assertRaises(HarnessError): output_guard(ROOT / "new-generated-run")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("../escape", "/absolute", "a/../b", "a/./b", "a//b", "a\\b"):
                with self.subTest(name=name), self.assertRaises(HarnessError): safe_relative(root, name)
            (root / "alias").symlink_to(root, target_is_directory=True)
            with self.assertRaises(HarnessError): safe_relative(root, "alias/evidence")
            with self.assertRaises(HarnessError): output_guard(root / "alias" / "new")

    def test_strict_json_and_nonstring_faults_fail_structurally(self):
        for raw in ('{"amount":1,"amount":2}', '{"amount":NaN}', '{"amount":Infinity}', '{broken', '[1] trailing'):
            with self.subTest(raw=raw), self.assertRaises(HarnessError): strict_loads(raw)
        for value in ([], {}, True, 1, None):
            c = deepcopy(load_fixture("constructed-continuity")["contract"])
            c["fault_schedule"][0]["event"] = value
            with self.subTest(value=value), self.assertRaises(HarnessError): validate_contract(c)

    def test_unknown_cohort_or_suite_kind_cannot_silently_select_a_different_experiment(self):
        with self.assertRaises(HarnessError): registry("unregistered")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "must-not-exist"
            with self.assertRaises(HarnessError): run_suite(target, kind="unregistered")
            self.assertFalse(target.exists())

    def test_missing_or_duplicate_suite_cells_are_not_saved_passes(self):
        spec, sha = registry()
        index = {"schema": "continuity-economy/suite-index/v1", "version": "0.2.0",
                 "kind": "demo", "cohort": "base", "registry_sha256": sha,
                 "methods": ["harness"], "fixture_ids": [f["id"] for f in spec["fixtures"]],
                 "created_utc": "2026-11-06T00:00:00Z", "entries": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "INDEX.json").write_text(json.dumps(index))
            (root / "SUMMARY.json").write_text('{"test_assertion":"PASSED"}')
            with self.assertRaises(HarnessError) as error: verify_suite(root)
            self.assertEqual(error.exception.code, "SUITE_COVERAGE")
            index["fixture_ids"] = []
            (root / "INDEX.json").write_text(json.dumps(index))
            with self.assertRaises(HarnessError) as error: verify_suite(root)
            self.assertEqual(error.exception.code, "REGISTRY_MISMATCH")

    def test_complete_experiment_cannot_omit_successor_or_challenges(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "INDEX.json").write_text(json.dumps({"schema":"continuity-economy/experiment-index/v1",
                "version":"0.2.0","members":{"base":"base"}}))
            with self.assertRaises(HarnessError) as error: verify_suite(root)
            self.assertEqual(error.exception.code, "SUITE_COVERAGE")


if __name__ == "__main__": unittest.main()
