"""Бизнес-логика учёта продуктов.

Пока данные хранятся в памяти программы. В следующей лабораторной работе
хранение будет перенесено в базу данных SQLite.
"""

from datetime import date

from src.producttrack.models import Operation, Product


class InventoryError(Exception):
    """Ошибка при работе с учётом продуктов (неверные данные, нехватка остатка)."""


class Inventory:
    """Склад продуктов: карточки продуктов и история операций."""

    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._operations: list[Operation] = []
        self._next_id = 1

    # ---------- Карточки продуктов ----------

    def add_product(
        self,
        name: str,
        category: str,
        unit: str,
        quantity: float,
        price: float,
        expiry_date: date,
    ) -> Product:
        """Добавить новый продукт (блок-схема «Добавление продукта»)."""
        name, category, unit = name.strip(), category.strip(), unit.strip()
        if not name or not category or not unit:
            raise InventoryError("Название, категория и единица измерения обязательны.")
        if quantity < 0:
            raise InventoryError("Количество не может быть отрицательным.")
        if price < 0:
            raise InventoryError("Цена не может быть отрицательной.")

        product = Product(self._next_id, name, category, unit, quantity, price, expiry_date)
        self._products[product.id] = product
        self._next_id += 1
        if quantity > 0:
            self._operations.append(Operation(product.id, Operation.INCOME, quantity))
        return product

    def get_product(self, product_id: int) -> Product:
        """Получить продукт по номеру."""
        try:
            return self._products[product_id]
        except KeyError:
            raise InventoryError(f"Продукт с номером {product_id} не найден.") from None

    def delete_product(self, product_id: int) -> None:
        """Удалить карточку продукта."""
        self.get_product(product_id)
        del self._products[product_id]

    def all_products(self) -> list[Product]:
        """Все продукты, отсортированные по номеру."""
        return sorted(self._products.values(), key=lambda p: p.id)

    def search(self, text: str) -> list[Product]:
        """Поиск продукта по названию или категории (без учёта регистра)."""
        text = text.strip().lower()
        return [
            p
            for p in self.all_products()
            if text in p.name.lower() or text in p.category.lower()
        ]

    # ---------- Операции ----------

    def receive(self, product_id: int, quantity: float) -> Operation:
        """Зарегистрировать поступление продукта."""
        if quantity <= 0:
            raise InventoryError("Количество должно быть больше нуля.")
        product = self.get_product(product_id)
        product.quantity += quantity
        operation = Operation(product_id, Operation.INCOME, quantity)
        self._operations.append(operation)
        return operation

    def write_off(self, product_id: int, quantity: float) -> Operation:
        """Зарегистрировать расход (блок-схема «Списание продуктов»)."""
        if quantity <= 0:
            raise InventoryError("Количество должно быть больше нуля.")
        product = self.get_product(product_id)
        if quantity > product.quantity:
            raise InventoryError(
                f"Недостаточно остатка: на складе {product.quantity:g} {product.unit}."
            )
        product.quantity -= quantity
        operation = Operation(product_id, Operation.WRITE_OFF, quantity)
        self._operations.append(operation)
        return operation

    def history(self) -> list[Operation]:
        """История всех операций."""
        return list(self._operations)

    # ---------- Отчёты ----------

    def expiring(self, days: int = 3, today: date | None = None) -> list[Product]:
        """Продукты, у которых срок годности истекает в ближайшие days дней."""
        return [p for p in self.all_products() if p.days_to_expiry(today) <= days]

    def total_cost(self) -> float:
        """Общая стоимость всех остатков."""
        return sum(p.total_cost for p in self._products.values())


def create_demo_inventory() -> Inventory:
    """Склад с тестовыми данными для демонстрации работы программы."""
    from datetime import timedelta

    today = date.today()
    inventory = Inventory()
    inventory.add_product("Молоко 3,2%", "Молочные продукты", "л", 24, 89.90, today + timedelta(days=2))
    inventory.add_product("Хлеб пшеничный", "Хлебобулочные изделия", "шт", 15, 45.00, today + timedelta(days=1))
    inventory.add_product("Гречка", "Крупы", "кг", 40, 110.00, today + timedelta(days=300))
    inventory.add_product("Яблоки", "Фрукты", "кг", 18.5, 129.00, today + timedelta(days=14))
    inventory.add_product("Сыр российский", "Молочные продукты", "кг", 6, 720.00, today + timedelta(days=20))
    return inventory
