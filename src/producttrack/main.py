"""Точка входа в программу «Учёт продуктов».

Запуск из корневой папки проекта:
    python -m src.producttrack.main
"""

from src.producttrack.inventory import create_demo_inventory
from src.producttrack.menu import run_menu


def main() -> None:
    print("Hello, World! Добро пожаловать в систему «Учёт продуктов».")
    inventory = create_demo_inventory()
    run_menu(inventory)


if __name__ == "__main__":
    main()
