from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from ....seedwork.dominio.objetos_valor import Moneda

@dataclass(frozen=True)
class Presupuesto:
    """Objeto valor que representa el presupuesto de una campaña"""
    monto: Decimal
    moneda: Moneda
    
    def __post_init__(self):
        if self.monto < 0:
            raise ValueError("El monto del presupuesto no puede ser negativo")
        if self.monto > Decimal('1000000'):
            raise ValueError("El monto del presupuesto no puede exceder 1,000,000")

@dataclass(frozen=True)
class MetricasCampana:
    """Objeto valor que representa las métricas de una campaña"""
    impresiones: int = 0
    clicks: int = 0
    conversiones: int = 0
    gasto_actual: Decimal = Decimal('0')
    
    def __post_init__(self):
        if self.impresiones < 0:
            raise ValueError("Las impresiones no pueden ser negativas")
        if self.clicks < 0:
            raise ValueError("Los clicks no pueden ser negativos")
        if self.conversiones < 0:
            raise ValueError("Las conversiones no pueden ser negativas")
        if self.gasto_actual < 0:
            raise ValueError("El gasto actual no puede ser negativo")
    
    @property
    def ctr(self) -> float:
        """Click Through Rate"""
        if self.impresiones == 0:
            return 0.0
        return (self.clicks / self.impresiones) * 100
    
    @property
    def tasa_conversion(self) -> float:
        """Tasa de conversión"""
        if self.clicks == 0:
            return 0.0
        return (self.conversiones / self.clicks) * 100
