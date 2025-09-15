from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class EventoDominio():
    id: uuid.UUID = field(default_factory=uuid.uuid4, kw_only=True)
    fecha_evento: datetime = field(default_factory=datetime.now, kw_only=True)

    @property
    def fecha_ocurrencia(self) -> datetime:
        return self.fecha_evento