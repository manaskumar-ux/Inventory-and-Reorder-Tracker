import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import Item, get_summary, category_report

class InventoryLogicTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            Item("A1", "Resistor", "Passive", 10, 5, 1.0, "2026-11-13"),
            Item("A2", "LED", "Semiconductor", 3, 5, 2.0, "2026-11-13"),
            Item("A3", "Wire", "Tools", 0, 2, 5.0, "2026-11-13"),
        ]

    def test_stock_status(self):
        self.assertEqual(self.items[0].status, "IN STOCK")
        self.assertEqual(self.items[1].status, "REORDER")
        self.assertEqual(self.items[2].status, "OUT OF STOCK")

    def test_summary(self):
        summary = get_summary(self.items)
        self.assertEqual(summary["items"], 3)
        self.assertEqual(summary["units"], 13)
        self.assertEqual(summary["reorder"], 1)
        self.assertEqual(summary["out"], 1)
        self.assertAlmostEqual(summary["inventory_value"], 16.0)

    def test_negative_quantity_rejected(self):
        item = Item("A4", "Bad", "Tools", -1, 0, 1.0, "2026-11-13")
        with self.assertRaises(ValueError):
            item.validate()

    def test_category_report(self):
        report = category_report(self.items)
        self.assertEqual(len(report), 3)
        self.assertIn("stock_value", report.columns)

if __name__ == "__main__":
    unittest.main()
