"""Модели предметной области «Учёт продуктов»."""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Product:
    """Карточка продукта."""

    id: int
    name: str
    category: str
    unit: str
    quantity: float
    price: float
    expiry_date: date

    @property
    def total_cost(self) -> float:
        """Стоимость всего остатка продукта."""
        return self.quantity * self.price

    def days_to_expiry(self, today: date | None = None) -> int:
        """Сколько дней осталось до окончания срока годности."""
        today = today or date.today()
        return (self.expiry_date - today).days


@dataclass
class Operation:
    """Операция с продуктом: поступление или расход (списание)."""

    INCOME = "Поступление"
    WRITE_OFF = "Расход"

    product_id: int
    op_type: str
    quantity: float
    created_at: datetime = field(default_factory=datetime.now)
