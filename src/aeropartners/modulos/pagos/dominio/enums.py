from enum import Enum

class EstadoPago(Enum):
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    EXITOSO = "EXITOSO"
    FALLIDO = "FALLIDO"
    REVERSADO = "REVERSADO"
