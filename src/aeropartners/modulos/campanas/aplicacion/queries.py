from dataclasses import dataclass
from typing import Optional
import uuid
from ....seedwork.aplicacion.queries import Query

@dataclass
class ObtenerCampanaPorIdQuery(Query):
    id_campana: uuid.UUID

@dataclass
class ListarCampanasQuery(Query):
    limit: int = 50
    offset: int = 0
    id_afiliado: Optional[str] = None

@dataclass
class ObtenerMetricasCampanaQuery(Query):
    id_campana: uuid.UUID

@dataclass
class ObtenerEstadisticasGeneralesQuery(Query):
    id_afiliado: Optional[str] = None
