"""DTOs reusables parte del seedwork del proyecto

En este archivo usted encontrará los DTOs reusables parte del seedwork del proyecto

"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

@dataclass
class DTO:
    ...

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
