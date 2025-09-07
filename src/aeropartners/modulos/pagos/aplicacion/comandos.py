"""Comandos de la aplicación de pagos"""

from dataclasses import dataclass
from typing import Optional
import uuid
from ....seedwork.aplicacion.comandos import Comando
from ....seedwork.dominio.objetos_valor import Moneda

@dataclass
class ProcesarPagoCommand(Comando):
    id_afiliado: str
    monto: float
    moneda: str
    id_pago: Optional[uuid.UUID] = None

    def __post_init__(self):
        if self.id_pago is None:
            self.id_pago = uuid.uuid4()
        
        # Validar que la moneda sea válida
        try:
            Moneda(self.moneda)
        except ValueError:
            raise ValueError(f"Moneda no válida: {self.moneda}")
