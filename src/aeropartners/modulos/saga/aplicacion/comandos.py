from dataclasses import dataclass
from typing import Dict, Any, Optional
from ....seedwork.aplicacion.comandos import Comando

@dataclass
class IniciarSagaCommand(Comando):
    tipo: str
    datos_iniciales: Dict[str, Any]
    timeout_minutos: int = 30

@dataclass
class EjecutarPasoCommand(Comando):
    saga_id: str
    paso_id: str
    tipo_paso: str
    datos: Dict[str, Any]

@dataclass
class MarcarPasoExitosoCommand(Comando):
    saga_id: str
    paso_id: str
    resultado: Dict[str, Any]

@dataclass
class MarcarPasoFallidoCommand(Comando):
    saga_id: str
    paso_id: str
    error: str

@dataclass
class IniciarCompensacionCommand(Comando):
    saga_id: str
    paso_fallido: str

@dataclass
class EjecutarCompensacionCommand(Comando):
    saga_id: str
    compensacion_id: str
    tipo_compensacion: str
    datos: Dict[str, Any]

@dataclass
class MarcarCompensacionExitosaCommand(Comando):
    saga_id: str
    compensacion_id: str
    resultado: Dict[str, Any]

@dataclass
class MarcarCompensacionFallidaCommand(Comando):
    saga_id: str
    compensacion_id: str
    error: str

@dataclass
class CrearCampanaCompletaCommand(Comando):
    """Comando específico para crear una campaña completa con SAGA"""
    datos_campana: Dict[str, Any]
    datos_pago: Dict[str, Any]
    datos_reporte: Dict[str, Any]
    timeout_minutos: int = 30

@dataclass
class ProcesarTimeoutSagaCommand(Comando):
    saga_id: str
    timeout_minutos: int
