"""Тесты бизнес-логики учёта продуктов.

Запуск из корневой папки проекта:
    python -m unittest
"""

import unittest
from datetime import date, timedelta

from src.producttrack.inventory import Inventory, InventoryError
from src.producttrack.models import Operation


class InventoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = Inventory()
        self.milk = self.inventory.add_product(
            "Молоко", "Молочные продукты", "л", 10, 90, date.today() + timedelta(days=2)
        )

    def test_add_product(self):
        self.assertEqual(self.milk.id, 1)
        self.assertEqual(len(self.inventory.all_products()), 1)

    def test_add_product_without_name(self):
        with self.assertRaises(InventoryError):
            self.inventory.add_product(" ", "Крупы", "кг", 1, 50, date.today())

    def test_receive_increases_quantity(self):
        self.inventory.receive(self.milk.id, 5)
        self.assertEqual(self.milk.quantity, 15)

    def test_write_off_decreases_quantity(self):
        operation = self.inventory.write_off(self.milk.id, 4)
        self.assertEqual(self.milk.quantity, 6)
        self.assertEqual(operation.op_type, Operation.WRITE_OFF)

    def test_write_off_more_than_stock(self):
        with self.assertRaises(InventoryError):
            self.inventory.write_off(self.milk.id, 100)
        self.assertEqual(self.milk.quantity, 10)

    def test_search_by_category(self):
        self.assertEqual(self.inventory.search("молоч"), [self.milk])

    def test_expiring_products(self):
        self.inventory.add_product("Гречка", "Крупы", "кг", 5, 100, date.today() + timedelta(days=200))
        self.assertEqual(self.inventory.expiring(days=3), [self.milk])

    def test_total_cost(self):
        self.assertEqual(self.inventory.total_cost(), 900)


if __name__ == "__main__":
    unittest.main()
