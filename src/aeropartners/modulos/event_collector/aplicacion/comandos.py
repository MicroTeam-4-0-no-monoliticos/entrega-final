from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from ....seedwork.aplicacion.comandos import Comando

@dataclass
class ProcesarEventoTrackingCommand(Comando):
    tipo_evento: str
    id_afiliado: str
    timestamp: datetime
    
    id_campana: Optional[str] = None
    id_oferta: Optional[str] = None
    url: Optional[str] = None
    parametros_tracking: Optional[Dict[str, Any]] = None
    
    datos_custom: Optional[Dict[str, Any]] = None
    valor_conversion: Optional[float] = None
    moneda: Optional[str] = None
    
    ip_origen: str = None
    user_agent: str = None
    session_id: Optional[str] = None
    referrer: Optional[str] = None
    
    tipo_dispositivo: str = "OTHER"
    identificador_dispositivo: Optional[str] = None
    sistema_operativo: Optional[str] = None
    navegador: Optional[str] = None
    resolucion_pantalla: Optional[str] = None
    
    fuente_evento: str = "WEB_TAG"
    api_key: Optional[str] = None
    hash_validacion: Optional[str] = None

@dataclass
class ReprocesarEventoFallidoCommand(Comando):
    id_evento: str
    forzar_reproceso: bool = False