from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from ....seedwork.aplicacion.queries import Query

@dataclass
class ObtenerEstadoEventoQuery(Query):
    id_evento: str

@dataclass  
class ObtenerEstadisticasProcessingQuery(Query):
    id_afiliado: Optional[str] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
    tipo_evento: Optional[str] = None

@dataclass
class ObtenerEventosFallidosQuery(Query):
    id_afiliado: Optional[str] = None
    desde: Optional[datetime] = None
    limite: int = 100
    solo_reintentables: bool = True

@dataclass
class ObtenerRateLimitStatusQuery(Query):
    id_afiliado: str
    ventana_minutos: int = 1