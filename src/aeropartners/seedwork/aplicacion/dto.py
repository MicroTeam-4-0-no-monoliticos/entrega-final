from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class DTO:
    pass

@dataclass
class RespuestaDTO(DTO):
    mensaje: str
    datos: Any = None
    exitoso: bool = True

@dataclass
class ErrorDTO(DTO):
    mensaje: str
    codigo: str
    detalles: Optional[Dict] = None