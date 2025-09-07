from dataclasses import dataclass
from enum import Enum

class Moneda(Enum):
    USD = "USD"
    EUR = "EUR"
    COP = "COP"

@dataclass
class Dinero:
    monto: float
    moneda: Moneda
