"""Консольное меню программы «Учёт продуктов»."""

from datetime import date

from src.producttrack.inventory import Inventory, InventoryError
from src.producttrack.models import Product

MAIN_MENU = """
===== Учёт продуктов =====
1. Список продуктов
2. Добавить продукт
3. Поступление
4. Расход (списание)
5. Поиск
6. Отчёты
0. Выход"""


def input_number(prompt: str, as_int: bool = False) -> float:
    """Ввести число; при ошибке повторить ввод."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            return int(raw) if as_int else float(raw)
        except ValueError:
            print("Ошибка: введите число.")


def input_date(prompt: str) -> date:
    """Ввести дату в формате ДД.ММ.ГГГГ; при ошибке повторить ввод."""
    while True:
        raw = input(prompt).strip()
        try:
            day, month, year = (int(x) for x in raw.split("."))
            return date(year, month, day)
        except ValueError:
            print("Ошибка: введите дату в формате ДД.ММ.ГГГГ.")


def print_products(products: list[Product]) -> None:
    """Вывести продукты таблицей."""
    if not products:
        print("Продукты не найдены.")
        return
    print(f"{'№':>3} | {'Название':<18} | {'Категория':<22} | {'Остаток':>10} | {'Цена':>8} | Годен до")
    print("-" * 86)
    for p in products:
        stock = f"{p.quantity:g} {p.unit}"
        print(
            f"{p.id:>3} | {p.name:<18} | {p.category:<22} | {stock:>10} | "
            f"{p.price:>8.2f} | {p.expiry_date:%d.%m.%Y}"
        )


def add_product(inventory: Inventory) -> None:
    print("\n--- Добавление продукта ---")
    try:
        product = inventory.add_product(
            name=input("Название: "),
            category=input("Категория: "),
            unit=input("Единица измерения (шт, кг, л): "),
            quantity=input_number("Количество: "),
            price=input_number("Цена за единицу, руб.: "),
            expiry_date=input_date("Срок годности (ДД.ММ.ГГГГ): "),
        )
        print(f"Продукт «{product.name}» сохранён под номером {product.id}.")
    except InventoryError as error:
        print(f"Ошибка: {error}")


def register_operation(inventory: Inventory, income: bool) -> None:
    print("\n--- Поступление ---" if income else "\n--- Расход (списание) ---")
    print_products(inventory.all_products())
    product_id = input_number("Номер продукта: ", as_int=True)
    quantity = input_number("Количество: ")
    try:
        if income:
            inventory.receive(product_id, quantity)
        else:
            inventory.write_off(product_id, quantity)
        product = inventory.get_product(product_id)
        print(f"Готово. Остаток «{product.name}»: {product.quantity:g} {product.unit}.")
    except InventoryError as error:
        print(f"Ошибка: {error}")


def search(inventory: Inventory) -> None:
    text = input("\nВведите название или категорию: ")
    print_products(inventory.search(text))


def reports(inventory: Inventory) -> None:
    print("\n--- Отчёты ---")
    print(f"Всего наименований: {len(inventory.all_products())}")
    print(f"Общая стоимость остатков: {inventory.total_cost():.2f} руб.")
    print("\nСрок годности истекает в ближайшие 3 дня:")
    print_products(inventory.expiring(days=3))
    print("\nИстория операций:")
    names = {p.id: p.name for p in inventory.all_products()}
    for op in inventory.history():
        name = names.get(op.product_id, f"#{op.product_id} (удалён)")
        print(f"{op.created_at:%d.%m.%Y %H:%M} | {op.op_type:<12} | {name:<18} | {op.quantity:g}")


def run_menu(inventory: Inventory) -> None:
    """Главный цикл меню."""
    actions = {
        "1": lambda: print_products(inventory.all_products()),
        "2": lambda: add_product(inventory),
        "3": lambda: register_operation(inventory, income=True),
        "4": lambda: register_operation(inventory, income=False),
        "5": lambda: search(inventory),
        "6": lambda: reports(inventory),
    }
    while True:
        print(MAIN_MENU)
        choice = input("Выберите пункт: ").strip()
        if choice == "0":
            print("До свидания!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Нет такого пункта меню.")
