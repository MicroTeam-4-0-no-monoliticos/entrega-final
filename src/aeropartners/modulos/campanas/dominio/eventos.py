from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import uuid

@dataclass
class CampanaCreada:
    id_campana: str
    nombre: str
    tipo: str
    presupuesto_monto: Decimal
    presupuesto_moneda: str
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str
    id_afiliado: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha_evento: datetime = field(default_factory=datetime.now)

@dataclass
class CampanaActualizada:
    id_campana: str
    nombre: str
    presupuesto_monto: Decimal
    presupuesto_moneda: str
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha_evento: datetime = field(default_factory=datetime.now)

@dataclass
class CampanaActivada:
    id_campana: str
    nombre: str
    fecha_activacion: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha_evento: datetime = field(default_factory=datetime.now)

@dataclass
class PresupuestoCampanaActualizado:
    id_campana: str
    presupuesto_anterior: Decimal
    presupuesto_nuevo: Decimal
    moneda: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha_evento: datetime = field(default_factory=datetime.now)

@dataclass
class MetricasCampanaActualizadas:
    id_campana: str
    impresiones: int
    clicks: int
    conversiones: int
    gasto_actual: Decimal
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha_evento: datetime = field(default_factory=datetime.now)
