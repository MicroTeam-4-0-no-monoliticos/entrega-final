from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from ....seedwork.dominio.eventos import EventoDominio

@dataclass
class EventoRecibido(EventoDominio):
    id_evento_tracking: str
    tipo_evento: str
    id_afiliado: str
    timestamp_recepcion: datetime
    fuente: str
    ip_origen: str
    
    def __post_init__(self):
        super().__init__()

@dataclass
class EventoValidado(EventoDominio):
    id_evento_tracking: str
    tipo_evento: str
    id_afiliado: str
    validaciones_pasadas: Dict[str, bool]
    
    def __post_init__(self):
        super().__init__()

@dataclass
class EventoPublicado(EventoDominio):
    id_evento_tracking: str
    tipo_evento: str
    topic_destino: str
    partition_key: str
    timestamp_publicacion: datetime
    
    def __post_init__(self):
        super().__init__()

@dataclass
class EventoFallido(EventoDominio):
    id_evento_tracking: str
    tipo_evento: str
    razon_fallo: str
    codigo_error: str
    intentos_realizados: int
    
    def __post_init__(self):
        super().__init__()

@dataclass
class EventoDescartado(EventoDominio):
    id_evento_tracking: str
    tipo_evento: str
    razon_descarte: str
    regla_violada: str
    
    def __post_init__(self):
        super().__init__()

@dataclass
class EventoLimiteProcesamiento(EventoDominio):
    id_afiliado: str
    limite_alcanzado: str
    eventos_bloqueados: int
    ventana_tiempo: str
    
    def __post_init__(self):
        super().__init__()