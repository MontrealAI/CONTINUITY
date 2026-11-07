"""Aggregate coverage must be established independently of favorable labels.

These admission tests stub only leaf run/challenge judgments. They exercise the
real registered indexes, contract/policy binding, exact cell/control coverage and
aggregate dispatch. They are not additional digital-production experiments;
the verifier and challenge tests exercise those durable-evidence judgments.
"""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from continuity_economy import __version__
from continuity_economy.challenges import _fixture_for, registry as challenge_registry
from continuity_economy.schema import HarnessError, canonical, digest, strict_load
from continuity_economy.suite import (
    METHODS, cohort_fixture, expected_for, registry, verify_suite,
)


class ExperimentCoverageTests(unittest.TestCase):
    def setUp(self):
        self.storage = tempfile.TemporaryDirectory(prefix="continuity-economy-coverage-")
        self.addCleanup(self.storage.cleanup)
        self.root = Path(self.storage.name)
        self.members = {name: name for name in ("base", "successor", "challenges")}
        self.experiment = {"schema": "continuity-economy/experiment-index/v1",
                           "version": __version__, "members": self.members}
        self.write_comparison(self.root / "base", "base")
        self.write_comparison(self.root / "successor", "successor")
        self.write_challenges(self.root / "challenges")
        self.write(self.root / "INDEX.json", self.experiment)
        self.write(self.root / "SUMMARY.json", {"test_assertion": "PASSED"})
        self.fail_run = False
        self.fail_challenge = False
        run_patch = patch("continuity_economy.verifier.verify_run", side_effect=self.run_judgment)
        self.run_oracle = run_patch.start()
        self.addCleanup(run_patch.stop)
        challenge_patch = patch("continuity_economy.challenges._assess_case", side_effect=self.challenge_judgment)
        self.challenge_oracle = challenge_patch.start()
        self.addCleanup(challenge_patch.stop)

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(value))

    def write_comparison(self, root, cohort, kind="comparison"):
        spec, checksum = registry(cohort)
        methods = list(METHODS) if kind == "comparison" else ["harness"]
        index = {"schema": "continuity-economy/suite-index/v1", "version": __version__,
                 "kind": kind, "cohort": cohort, "registry_sha256": checksum,
                 "methods": methods, "fixture_ids": [f["id"] for f in spec["fixtures"]],
                 "created_utc": "2026-11-07T00:00:00Z", "entries": []}
        for item in spec["fixtures"]:
            fixture = cohort_fixture(item["id"], cohort)
            for method in methods:
                name = item["id"] + "." + method
                entry = {"fixture_id": item["id"], "method": method, "run": "runs/" + name,
                         "authority": "authorities/" + name, "reference_sha256": "a" * 64}
                index["entries"].append(entry)
                self.write(root / entry["run"] / "controller.json", {"method": method})
                self.write(root / entry["authority"] / "contract.json", fixture["contract"])
                self.write(root / entry["authority"] / "policies.json", fixture["policies"])
        self.write(root / "INDEX.json", index)
        self.write(root / "SUMMARY.json", {"test_assertion": "PASSED"})

    def write_challenges(self, root):
        spec, checksum = challenge_registry()
        index = {"schema": "continuity-economy/challenge-index/v1", "version": __version__,
                 "registry_sha256": checksum, "created_utc": "2026-11-07T00:00:00Z", "entries": []}
        references = {case["id"]: {"test_reference": case["id"]} for case in spec["cases"]}
        for case in spec["cases"]:
            cid = case["id"]
            reference = references[cid]
            pin = (None if case.get("mutation") == "missing_pin" else
                   digest(references["valid-digital-control"]) if case.get("mutation") == "quantity_1850_original_pin"
                   else digest(reference))
            entry = {"case_id": cid, "run": "runs/" + cid,
                     "authority": "authorities/" + cid, "reference_sha256": pin}
            index["entries"].append(entry)
            self.write(root / entry["authority"] / "reference.json", reference)
            if case["kind"] == "live":
                fixture = _fixture_for(case, spec)
                self.write(root / entry["authority"] / "contract.json", fixture["contract"])
                self.write(root / entry["authority"] / "policies.json", fixture["policies"])
        self.write(root / "INDEX.json", index)
        self.write(root / "SUMMARY.json", {"test_assertion": "PASSED"})

    def run_judgment(self, run, authority, *, expected_reference_sha256):
        contract = strict_load(authority / "contract.json")
        method = strict_load(run / "controller.json")["method"]
        expected = expected_for(cohort_fixture(contract["fixture_id"], contract["cohort"]), method)
        if self.fail_run and contract["fixture_id"] == "primary-recovery" and method == "harness":
            expected = {"outcome": "FAILED", "service_feasibility": "FAILED", "accepted_units": 0}
        return {"claims": {key: expected[key] for key in ("outcome", "service_feasibility")},
                "assessment": {"target_verdict": "NOT_RUN" if method == "ai" else "COMPLETED"},
                "totals": {"accepted_units": expected["accepted_units"]}, "safety_status": "DEMONSTRATED"}

    def challenge_judgment(self, root, case, entry):
        status = "FAILED" if self.fail_challenge and case["id"] == "valid-digital-control" else "PASSED"
        report = {"assessment": {"test_assertion": status}, "claims": {},
                  "challenge": {"assertion": {"status": status}}}
        return report, None, None

    def assert_refused(self, code="SUITE_COVERAGE"):
        with self.assertRaises(HarnessError) as error:
            verify_suite(self.root)
        self.assertEqual(error.exception.code, code)

    def test_complete_registered_children_are_verified_freshly_despite_saved_failed_labels(self):
        for directory in (self.root, *(self.root / name for name in self.members)):
            self.write(directory / "SUMMARY.json", {"test_assertion": "FAILED"})
        result = verify_suite(self.root)
        self.assertTrue(result["fresh"])
        self.assertEqual(result["test_assertion"], "PASSED")
        self.assertEqual({name: len(child.get("runs", child.get("records", [])))
                          for name, child in result["members"].items()},
                         {"base": 28, "successor": 4, "challenges": 26})
        self.assertEqual(self.run_oracle.call_count, 32)
        self.assertEqual(self.challenge_oracle.call_count, 26)

    def test_passing_base_demo_cannot_supply_three_members_by_alias_or_distinct_copies(self):
        self.write_comparison(self.root / "demo", "base", kind="demo")
        self.assertEqual(verify_suite(self.root / "demo")["test_assertion"], "PASSED")
        for distinct in (False, True):
            with self.subTest(distinct=distinct):
                paths = {name: "demo" for name in self.members}
                if distinct:
                    for name in self.members:
                        paths[name] = "demo-" + name
                        shutil.copytree(self.root / "demo", self.root / paths[name])
                self.write(self.root / "INDEX.json", {**self.experiment, "members": paths})
                self.assert_refused()

    def test_passing_base_comparison_cannot_replace_successor_or_registered_challenges(self):
        shutil.copytree(self.root / "base", self.root / "another-base")
        self.assertEqual(verify_suite(self.root / "another-base")["test_assertion"], "PASSED")
        for member in ("successor", "challenges"):
            with self.subTest(member=member):
                self.write(self.root / "INDEX.json", {**self.experiment,
                           "members": {**self.members, member: "another-base"}})
                self.assert_refused()

    def test_swapped_comparison_cohorts_are_refused(self):
        self.write(self.root / "INDEX.json", {**self.experiment,
                   "members": {"base": "successor", "successor": "base", "challenges": "challenges"}})
        self.assert_refused()

    def test_passing_nested_experiment_cannot_replace_any_required_child(self):
        nested = self.root / "nested"
        for member in self.members:
            shutil.copytree(self.root / member, nested / member)
        self.write(nested / "INDEX.json", self.experiment)
        self.assertEqual(verify_suite(nested)["test_assertion"], "PASSED")
        for member in self.members:
            with self.subTest(member=member):
                self.write(self.root / "INDEX.json", {**self.experiment,
                           "members": {**self.members, member: "nested"}})
                self.assert_refused()

    def test_experiment_requires_supported_version_and_exact_member_mapping(self):
        for version in (None, True, 2, [], {}, "", "0.1.0", "0.2.1"):
            with self.subTest(version=version):
                self.write(self.root / "INDEX.json", {**self.experiment, "version": version})
                self.assert_refused("UNSUPPORTED_VERSION")
        for members in (None, True, 3, "base", list(self.members), [[k, v] for k, v in self.members.items()]):
            with self.subTest(members=members):
                self.write(self.root / "INDEX.json", {**self.experiment, "members": members})
                self.assert_refused("INVALID_TYPE")
        for members in ({}, {"base": "base"}, {**self.members, "extra": "base"},
                        {"base": "base", "successor": "successor", "challenge": "challenges"}):
            with self.subTest(members=members):
                self.write(self.root / "INDEX.json", {**self.experiment, "members": members})
                self.assert_refused()
        self.run_oracle.assert_not_called()
        self.challenge_oracle.assert_not_called()

    def test_nonobject_indexes_and_unknown_outer_fields_are_structured_refusals(self):
        for value in (None, [], [self.experiment], True, "experiment"):
            with self.subTest(index=value):
                self.write(self.root / "INDEX.json", value)
                self.assert_refused("INVALID_TYPE")
        self.write(self.root / "INDEX.json", {**self.experiment, "saved_pass": True})
        self.assert_refused("INVALID_FIELDS")

    def test_member_paths_are_distinct_safe_strings_and_cannot_use_symlink_aliases(self):
        self.write(self.root / "INDEX.json", {**self.experiment,
                   "members": {**self.members, "successor": "base"}})
        self.assert_refused()
        for path in (None, True, 1, [], {}, "", "/base", "../base", "base/../successor",
                     "./base", "base/", "base//nested", "base\\nested"):
            with self.subTest(path=path):
                self.write(self.root / "INDEX.json", {**self.experiment,
                           "members": {**self.members, "base": path}})
                self.assert_refused("UNSAFE_PATH")
        (self.root / "alias").symlink_to(self.root / "base", target_is_directory=True)
        self.write(self.root / "INDEX.json", {**self.experiment,
                   "members": {**self.members, "base": "alias"}})
        self.assert_refused("UNSAFE_PATH")
        self.run_oracle.assert_not_called()
        self.challenge_oracle.assert_not_called()

    def test_all_child_versions_remain_required(self):
        for member in self.members:
            path = self.root / member / "INDEX.json"
            original = strict_load(path)
            with self.subTest(member=member):
                self.write(path, {**original, "version": "0.2.1"})
                self.assert_refused("UNSUPPORTED_VERSION")
                self.write(path, original)

    def test_missing_cell_or_challenge_cannot_be_hidden_by_saved_passes(self):
        for member in self.members:
            path = self.root / member / "INDEX.json"
            original = strict_load(path)
            with self.subTest(member=member):
                altered = deepcopy(original)
                altered["entries"].pop()
                self.write(path, altered)
                self.assert_refused()
                self.write(path, original)

    def test_child_metadata_does_not_replace_independent_contract_binding(self):
        index = strict_load(self.root / "successor" / "INDEX.json")
        authority = self.root / "successor" / index["entries"][0]["authority"]
        self.write(authority / "contract.json", cohort_fixture("primary-recovery", "base")["contract"])
        self.assert_refused("SUITE_CELL_BINDING")

    def test_failed_fresh_run_or_challenge_cannot_be_hidden_by_saved_passes(self):
        for failed_member in ("base", "challenges"):
            with self.subTest(member=failed_member):
                self.fail_run = failed_member == "base"
                self.fail_challenge = failed_member == "challenges"
                result = verify_suite(self.root)
                self.assertEqual(result["test_assertion"], "FAILED")
                self.assertEqual(result["members"][failed_member]["test_assertion"], "FAILED")


if __name__ == "__main__":
    unittest.main()
