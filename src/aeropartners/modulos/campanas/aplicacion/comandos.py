from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from ....seedwork.aplicacion.comandos import Comando

@dataclass
class CrearCampanaCommand(Comando):
    nombre: str
    tipo: str
    presupuesto_monto: Decimal
    presupuesto_moneda: str
    fecha_inicio: datetime
    fecha_fin: datetime
    id_afiliado: str
    descripcion: Optional[str] = None
    id_campana: Optional[uuid.UUID] = None
    
    def __post_init__(self):
        if self.id_campana is None:
            self.id_campana = uuid.uuid4()

@dataclass
class ActualizarPresupuestoCampanaCommand(Comando):
    id_campana: uuid.UUID
    nuevo_presupuesto_monto: Decimal
    nueva_moneda: str

@dataclass
class ActivarCampanaCommand(Comando):
    id_campana: uuid.UUID

@dataclass
class ActualizarInformacionCampanaCommand(Comando):
    id_campana: uuid.UUID
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None

@dataclass
class ActualizarMetricasCampanaCommand(Comando):
    id_campana: uuid.UUID
    impresiones: Optional[int] = None
    clicks: Optional[int] = None
    conversiones: Optional[int] = None
    gasto_actual: Optional[Decimal] = None

@dataclass
class PausarCampanaCommand(Comando):
    id_campana: uuid.UUID

@dataclass
class FinalizarCampanaCommand(Comando):
    id_campana: uuid.UUID

@dataclass
class CancelarCampanaCommand(Comando):
    id_campana: uuid.UUID
