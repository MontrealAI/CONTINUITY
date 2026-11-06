"""Admission of the bounded semantic product format before durable mutation."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from continuity_economy.fixtures import fixture_names, load_fixture
from continuity_economy.schema import (HarnessError, MAX_JSON_BYTES, canonical,
    digest, product_byte_bound, validate_contract)


def changed_text_fixture(text, *, split=False, quantities=None):
    fixture = load_fixture("primary-recovery")
    contract = deepcopy(fixture["contract"])
    contract["allow_split"] = split
    active = {o["obligation_id"] for o in contract["obligations"] if o["status"] == "ACTIVE"}
    def change(obligation):
        if obligation["obligation_id"] in active:
            for key in ("name_en", "name_fr", "instructions_en", "instructions_fr"):
                obligation["spec"][key] = text
            if quantities is not None:
                obligation["quantity"] = quantities[obligation["obligation_id"]]
    for obligation in contract["obligations"]:
        change(obligation)
    for event in contract["source_events"]:
        if "obligation" in event:
            change(event["obligation"])
    contract["source_sha256"] = digest(contract["source_events"])
    return contract, fixture["policies"]


class ProductSizeAdmissionTests(unittest.TestCase):
    def test_all_registered_1900_unit_fixtures_remain_admitted(self):
        for name in fixture_names():
            with self.subTest(fixture=name):
                contract = load_fixture(name)["contract"]
                validate_contract(contract)
                self.assertEqual(sum(o["quantity"] for o in contract["obligations"] if o["status"] == "ACTIVE"), 1900)
                for obligation in contract["obligations"]:
                    if obligation["status"] == "ACTIVE":
                        self.assertLessEqual(product_byte_bound(contract, obligation), MAX_JSON_BYTES)

    def test_long_non_ascii_unsplit_contract_is_refused_at_admission(self):
        contract, _ = changed_text_fixture("é" * 160)
        self.assertLess(len(canonical(contract)), MAX_JSON_BYTES)
        with self.assertRaises(HarnessError) as caught:
            validate_contract(contract)
        self.assertEqual(caught.exception.code, "PRODUCT_SIZE_LIMIT")

    def test_size_refusal_precedes_any_controller_authority_or_runtime_creation(self):
        from continuity_economy.controller import Controller
        contract, policies = changed_text_fixture("é" * 160)
        with tempfile.TemporaryDirectory() as folder:
            run, authority = Path(folder)/"run", Path(folder)/"authority"
            with self.assertRaises(HarnessError) as caught:
                Controller(contract, policies, "harness", run, authority)
            self.assertEqual(caught.exception.code, "PRODUCT_SIZE_LIMIT")
            self.assertFalse(run.exists())
            self.assertFalse(authority.exists())

    def test_small_unicode_product_is_supported_without_changing_its_content(self):
        contract, _ = changed_text_fixture("é" * 160, quantities={"DL-100": 100, "DL-200": 80})
        before = deepcopy(contract)
        validate_contract(contract)
        self.assertEqual(contract, before)
        self.assertEqual(contract["obligations"][0]["spec"]["name_fr"], "é" * 160)

    def test_non_bmp_escape_width_is_counted_before_accepting_a_lot(self):
        narrow, _ = changed_text_fixture("é" * 160, quantities={"DL-100": 160, "DL-200": 150})
        wide, _ = changed_text_fixture("🛡" * 160, quantities={"DL-100": 160, "DL-200": 150})
        validate_contract(narrow)
        self.assertGreater(product_byte_bound(wide, wide["obligations"][0]),
                           product_byte_bound(narrow, narrow["obligations"][0]))
        with self.assertRaises(HarnessError) as caught:
            validate_contract(wide)
        self.assertEqual(caught.exception.code, "PRODUCT_SIZE_LIMIT")

    def test_bound_applies_to_the_authorized_lot_not_aggregate_customer_quantity(self):
        contract, _ = changed_text_fixture("é" * 70, split=True)
        validate_contract(contract)
        contract["allow_split"] = False
        with self.assertRaises(HarnessError) as caught:
            validate_contract(contract)
        self.assertEqual(caught.exception.code, "PRODUCT_SIZE_LIMIT")


if __name__ == "__main__":
    unittest.main()
