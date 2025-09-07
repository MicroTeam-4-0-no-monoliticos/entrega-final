from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ResultadoPago:
    exitoso: bool
    mensaje_error: str = None
    referencia_transaccion: str = None

class PasarelaDePagos(ABC):
    """Puerto para la pasarela de pagos externa"""
    
    @abstractmethod
    def procesar_pago(self, referencia: str, monto: float, moneda: str, id_afiliado: str) -> ResultadoPago:
        raise NotImplementedError()
