"""Тесты экспорта данных в JSON, CSV, XML и YAML (ЛР №5)."""

import csv
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.producttrack import export_data


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.out = base / "out"  # папки out ещё нет, программа должна создать её
        self.paths = export_data.export_all(base / "test.db", self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_out_folder_and_four_files(self):
        self.assertTrue(self.out.is_dir())
        names = sorted(path.name for path in self.paths)
        self.assertEqual(names, ["data.csv", "data.json", "data.xml", "data.yaml"])
        for path in self.paths:
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_json_has_nested_category(self):
        data = json.loads((self.out / "data.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data), 6)
        self.assertEqual(data[0]["name"], "Молоко 3,2%")
        self.assertEqual(data[0]["category"], {"id": 1, "name": "Молочные продукты"})

    def test_csv_is_flat(self):
        with open(self.out / "data.csv", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 6)
        self.assertIn("category_name", rows[0])
        self.assertEqual(rows[0]["category_name"], "Молочные продукты")

    def test_xml_is_valid(self):
        root = ET.parse(self.out / "data.xml").getroot()
        self.assertEqual(root.tag, "products")
        products = root.findall("product")
        self.assertEqual(len(products), 6)
        self.assertEqual(products[0].findtext("category/name"), "Молочные продукты")

    def test_yaml_content(self):
        text = (self.out / "data.yaml").read_text(encoding="utf-8")
        self.assertIn("- id: 1", text)
        self.assertIn("name: Молоко 3,2%", text)
        self.assertIn("category:", text)
        self.assertIn('expiry_date: "2026-12-15"', text)

    def test_yaml_scalars(self):
        scalar = export_data._yaml_scalar
        self.assertEqual(scalar(None), "null")
        self.assertEqual(scalar(True), "true")
        self.assertEqual(scalar(5), "5")
        self.assertEqual(scalar("да"), "да")
        self.assertEqual(scalar("true"), '"true"')
        self.assertEqual(scalar("12"), '"12"')
        self.assertEqual(scalar("a: b"), '"a: b"')

    def test_nested_none_and_lists(self):
        record = {"id": 1, "tags": ["a", "b"], "owner": {"name": None}}
        flat = export_data.flatten(record)
        self.assertEqual(flat, {"id": 1, "tags": "a;b", "owner_name": ""})


if __name__ == "__main__":
    unittest.main()
