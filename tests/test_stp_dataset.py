import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StpDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data" / "stp_exploratory_dataset.json").open(encoding="utf-8") as handle:
            cls.dataset = json.load(handle)

    def test_dataset_has_source_provenance_and_limitations(self):
        self.assertTrue(self.dataset.get("sourceFile"))
        self.assertTrue(self.dataset.get("sourceFileSha256"))
        self.assertIn("not", self.dataset.get("sourceNote", "").lower())
        self.assertIn("verify", self.dataset.get("sourceNote", "").lower())

    def test_expected_record_counts(self):
        self.assertEqual(len(self.dataset.get("tankReadings", [])), 27)
        self.assertEqual(len(self.dataset.get("flowGasReadings", [])), 12)

    def test_each_tank_record_has_location_date_and_audit_notes(self):
        for index, row in enumerate(self.dataset["tankReadings"], start=1):
            with self.subTest(record=index):
                self.assertTrue(str(row.get("date", "")).strip())
                self.assertTrue(str(row.get("point", "")).strip())
                self.assertIn("confidence", row)
                self.assertIn("notes", row)

    def test_each_flow_record_has_route_date_units_and_notes(self):
        for index, row in enumerate(self.dataset["flowGasReadings"], start=1):
            with self.subTest(record=index):
                self.assertTrue(str(row.get("date", "")).strip())
                self.assertTrue(str(row.get("route", "")).strip())
                self.assertTrue(str(row.get("unitPeriod", "")).strip())
                self.assertTrue(str(row.get("notes", "")).strip())

if __name__ == "__main__":
    unittest.main()
