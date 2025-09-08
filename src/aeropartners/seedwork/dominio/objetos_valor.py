from dataclasses import dataclass
from enum import Enum

@dataclass(frozen=True)
class ObjetoValor:
    def __post_init__(self):
        self.validar()

    def validar(self):
        pass

class Moneda(Enum):
    USD = "USD"
    EUR = "EUR"
    COP = "COP"

@dataclass(frozen=True)
class Dinero(ObjetoValor):
    monto: float
    moneda: Moneda

    def validar(self):
        if self.monto <= 0:
            raise ValueError("El monto debe ser mayor a cero")
