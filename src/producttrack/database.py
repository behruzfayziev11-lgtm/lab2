"""Работа с базой данных SQLite.

Минимальная схема для лабораторной работы №5: две связанные таблицы.
Каждый продукт (products) ссылается на категорию (categories).
"""

import sqlite3
from pathlib import Path

# Корень проекта: .../ProductTrack/src/producttrack/database.py -> .../ProductTrack
ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "producttrack.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category_id INTEGER REFERENCES categories (id),
    unit        TEXT NOT NULL,
    quantity    REAL NOT NULL DEFAULT 0,
    price       REAL NOT NULL,
    expiry_date TEXT
);
"""

CATEGORIES = ["Молочные продукты", "Хлебобулочные изделия", "Крупы"]

# (название, номер категории, единица, количество, цена, годен до)
PRODUCTS = [
    ("Молоко 3,2%", 1, "л", 24, 89.90, "2026-12-15"),
    ("Кефир 1%", 1, "л", 10, 74.50, "2026-12-10"),
    ("Хлеб пшеничный", 2, "шт", 15, 45.00, "2026-12-05"),
    ("Батон нарезной", 2, "шт", 12, 38.00, "2026-12-03"),
    ("Гречка", 3, "кг", 40, 110.00, "2027-08-25"),
    ("Рис длиннозёрный", 3, "кг", 25, 95.00, "2027-06-30"),
]


def init_db(conn):
    """Создаёт таблицы, если их ещё нет."""
    conn.executescript(SCHEMA)
    conn.commit()


def seed(conn):
    """Заполняет пустую базу тестовыми данными."""
    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if count:
        return
    conn.executemany(
        "INSERT INTO categories (name) VALUES (?)",
        [(name,) for name in CATEGORIES],
    )
    conn.executemany(
        "INSERT INTO products (name, category_id, unit, quantity, price, expiry_date) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        PRODUCTS,
    )
    conn.commit()


def connect(db_path=DB_PATH):
    """Открывает базу, создаёт таблицы и тестовые данные при необходимости."""
    conn = sqlite3.connect(db_path)
    init_db(conn)
    seed(conn)
    return conn
