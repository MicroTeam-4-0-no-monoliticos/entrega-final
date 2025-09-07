"""Eventos de dominio reusables parte del seedwork del proyecto

En este archivo usted encontrará las clases para eventos reusables parte del seedwork del proyecto

"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class EventoDominio():
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha_evento: datetime = field(default_factory=datetime.now)
