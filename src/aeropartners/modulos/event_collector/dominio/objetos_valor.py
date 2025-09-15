from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from .enums import TipoDispositivo, FuenteEvento
from ....seedwork.dominio.objetos_valor import ObjetoValor

@dataclass(frozen=True)
class MetadatosEvento(ObjetoValor):
    ip_origen: str
    user_agent: str
    timestamp: datetime
    session_id: Optional[str] = None
    referrer: Optional[str] = None
    
    def __post_init__(self):
        if not self.ip_origen:
            raise ValueError("IP de origen es requerida")
        if not self.user_agent:
            raise ValueError("User-Agent es requerido")
        if not self.timestamp:
            raise ValueError("Timestamp es requerido")

@dataclass(frozen=True)
class ContextoEvento(ObjetoValor):
    id_afiliado: str
    id_campana: Optional[str] = None
    id_oferta: Optional[str] = None
    url: Optional[str] = None
    parametros_tracking: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.id_afiliado:
            raise ValueError("ID de afiliado es requerido")
        
        if self.id_campana:
            try:
                uuid.UUID(self.id_campana)
            except ValueError:
                raise ValueError("ID de campaña debe ser un UUID válido")

@dataclass(frozen=True)
class DatosDispositivo(ObjetoValor):
    tipo: TipoDispositivo
    identificador: Optional[str] = None
    so: Optional[str] = None
    navegador: Optional[str] = None
    resolucion: Optional[str] = None
    
    def __post_init__(self):
        if not self.tipo:
            raise ValueError("Tipo de dispositivo es requerido")

@dataclass(frozen=True)
class FirmaEvento(ObjetoValor):
    fuente: FuenteEvento
    api_key: Optional[str] = None
    hash_validacion: Optional[str] = None
    
    def __post_init__(self):
        if not self.fuente:
            raise ValueError("Fuente del evento es requerida")
        
        if self.fuente == FuenteEvento.API_DIRECT and not self.api_key:
            raise ValueError("API Key es requerida para llamadas directas a la API")

@dataclass(frozen=True)
class PayloadEvento(ObjetoValor):
    datos_custom: Dict[str, Any]
    valor_conversion: Optional[float] = None
    moneda: Optional[str] = None
    
    def __post_init__(self):
        if self.datos_custom is None:
            object.__setattr__(self, 'datos_custom', {})
        
        if self.valor_conversion is not None and not self.moneda:
            raise ValueError("Si se especifica valor de conversión, la moneda es requerida")