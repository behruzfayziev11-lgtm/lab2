"""Экспорт данных из базы в форматы JSON, CSV, XML и YAML (ЛР №5).

Запуск из корневой папки проекта:

    python -m src.producttrack.export_data

Программа берёт все записи таблицы products вместе со связанной таблицей
categories (SQL-запрос с JOIN) и создаёт в папке out четыре файла:
data.json, data.csv, data.xml, data.yaml.

Код универсален: чтобы выгрузить другую таблицу, достаточно изменить
SQL_QUERY, ROOT_TAG и ITEM_TAG. Поля связанной таблицы в запросе называют
по правилу «группа__поле» (например, category__name), и они автоматически
попадают во вложенный объект category.
"""

import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from . import database

OUT_DIR = database.ROOT_DIR / "out"

# SQL-запрос: все продукты + связанная категория.
# Поля с «__» в имени становятся вложенным объектом: category__name -> category.name
SQL_QUERY = """
SELECT p.id,
       p.name,
       p.unit,
       p.quantity,
       p.price,
       p.expiry_date,
       c.id   AS category__id,
       c.name AS category__name
FROM products AS p
LEFT JOIN categories AS c ON c.id = p.category_id
ORDER BY p.id
"""

ROOT_TAG = "products"  # корневой тег в XML
ITEM_TAG = "product"   # тег одной записи в XML
NEST_SEP = "__"        # разделитель «группа__поле»


# ---------------------------------------------------------------- данные

def build_records(cursor):
    """Превращает строки результата SQL в список словарей.

    Поля вида «группа__поле» собираются во вложенный словарь.
    """
    names = [column[0] for column in cursor.description]
    records = []
    for row in cursor.fetchall():
        record = {}
        for name, value in zip(names, row):
            if NEST_SEP in name:
                group, field = name.split(NEST_SEP, 1)
                record.setdefault(group, {})[field] = value
            else:
                record[name] = value
        records.append(record)
    return records


def flatten(record, prefix=""):
    """Делает запись плоской для CSV: вложенные поля -> category_name,
    списки склеиваются через «;»."""
    flat = {}
    for key, value in record.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(flatten(value, name + "_"))
        elif isinstance(value, list):
            flat[name] = ";".join(str(item) for item in value)
        else:
            flat[name] = "" if value is None else value
    return flat


# ---------------------------------------------------------------- JSON

def write_json(records, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)
        file.write("\n")


# ---------------------------------------------------------------- CSV

def write_csv(records, path):
    rows = [flatten(record) for record in records]
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    # utf-8-sig: чтобы Excel правильно показал русские буквы
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, restval="")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------- XML

def _fill_element(element, value):
    if isinstance(value, dict):
        for key, child_value in value.items():
            _fill_element(ET.SubElement(element, key), child_value)
    elif isinstance(value, list):
        for item in value:
            _fill_element(ET.SubElement(element, "item"), item)
    elif value is None:
        pass  # пустой тег
    elif isinstance(value, bool):
        element.text = "true" if value else "false"
    else:
        element.text = str(value)


def write_xml(records, path, root_tag=ROOT_TAG, item_tag=ITEM_TAG):
    root = ET.Element(root_tag)
    for record in records:
        _fill_element(ET.SubElement(root, item_tag), record)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


# ---------------------------------------------------------------- YAML
# Небольшой собственный сериализатор: внешние библиотеки не нужны.

_RESERVED = {"true", "false", "null", "yes", "no", "on", "off", "y", "n", "~"}
_PLAIN = re.compile(r"[^\W\d_][\w .,%()/+-]*")


def _yaml_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value)
    safe = (
        _PLAIN.fullmatch(text)
        and text == text.strip()
        and text.lower() not in _RESERVED
    )
    # Строка в двойных кавычках в формате JSON — это тоже корректный YAML
    return text if safe else json.dumps(text, ensure_ascii=False)


def _yaml_inline(value):
    if isinstance(value, dict):
        return "{}"
    if isinstance(value, list):
        return "[]"
    return _yaml_scalar(value)


def _yaml_lines(value, level=0):
    pad = "  " * level
    lines = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{pad}{_yaml_scalar(key)}:")
                lines.extend(_yaml_lines(item, level + 1))
            else:
                lines.append(f"{pad}{_yaml_scalar(key)}: {_yaml_inline(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item:
                sub = _yaml_lines(item, level + 1)
                lines.append(f"{pad}- {sub[0].lstrip()}")
                lines.extend(sub[1:])
            elif isinstance(item, list) and item:
                lines.append(f"{pad}-")
                lines.extend(_yaml_lines(item, level + 1))
            else:
                lines.append(f"{pad}- {_yaml_inline(item)}")
    return lines


def write_yaml(records, path):
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(_yaml_lines(records)) + "\n")


# ---------------------------------------------------------------- запуск

def export_all(db_path=database.DB_PATH, out_dir=OUT_DIR, sql=SQL_QUERY,
               root_tag=ROOT_TAG, item_tag=ITEM_TAG):
    """Выполняет SQL-запрос и создаёт четыре файла в папке out.

    Возвращает список путей к созданным файлам.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)  # создаём out, если её нет

    conn = database.connect(db_path)
    try:
        records = build_records(conn.execute(sql))
    finally:
        conn.close()

    paths = {
        "json": out_dir / "data.json",
        "csv": out_dir / "data.csv",
        "xml": out_dir / "data.xml",
        "yaml": out_dir / "data.yaml",
    }
    write_json(records, paths["json"])
    write_csv(records, paths["csv"])
    write_xml(records, paths["xml"], root_tag, item_tag)
    write_yaml(records, paths["yaml"])
    return list(paths.values())


def main():
    paths = export_all()
    print(f"Выгружено записей. Создано файлов: {len(paths)}")
    for path in paths:
        print(f"  {path}")


if __name__ == "__main__":
    main()
