"""Eventos del dominio de pagos"""

from dataclasses import dataclass
from ....seedwork.dominio.eventos import EventoDominio

@dataclass
class PagoExitoso(EventoDominio):
    id_pago: str
    id_afiliado: str
    monto: float
    moneda: str
    referencia_pago: str

@dataclass
class PagoFallido(EventoDominio):
    id_pago: str
    id_afiliado: str
    monto: float
    moneda: str
    referencia_pago: str
    mensaje_error: str
