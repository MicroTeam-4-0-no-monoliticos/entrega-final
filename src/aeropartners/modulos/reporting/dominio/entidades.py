"""
Entidades del dominio para el módulo de Reporting
"""
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TipoReporte(Enum):
    """Tipos de reportes disponibles"""
    PAGOS_POR_PERIODO = "pagos_por_periodo"
    CAMPAÑAS_ACTIVAS = "campanas_activas"
    MÉTRICAS_GENERALES = "metricas_generales"
    RENDIMIENTO_AFILIADOS = "rendimiento_afiliados"
    CAMPAÑA_COMPLETA = "CAMPAÑA_COMPLETA"


@dataclass
class Reporte:
    """Entidad principal que representa un reporte generado"""
    id: str
    tipo: TipoReporte
    fecha_generacion: datetime
    datos: Dict[str, Any]
    metadatos: Dict[str, Any]
    version_servicio_datos: str
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if not self.id:
            raise ValueError("El ID del reporte no puede estar vacío")
        if not self.datos:
            raise ValueError("El reporte debe contener datos")
    
    def agregar_metadato(self, clave: str, valor: Any) -> None:
        """Agrega un metadato al reporte"""
        self.metadatos[clave] = valor
    
    def obtener_metadato(self, clave: str) -> Optional[Any]:
        """Obtiene un metadato del reporte"""
        return self.metadatos.get(clave)
    
    def es_valido(self) -> bool:
        """Valida si el reporte es válido"""
        return bool(self.id and self.datos and self.tipo)


@dataclass
class ConfiguracionServicioDatos:
    """Configuración del servicio de datos actual"""
    url: str
    version: str
    activo: bool = True
    fecha_actualizacion: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if not self.url:
            raise ValueError("La URL del servicio de datos no puede estar vacía")
        if not self.version:
            raise ValueError("La versión del servicio de datos no puede estar vacía")
    
    def actualizar_url(self, nueva_url: str, nueva_version: str) -> None:
        """Actualiza la URL y versión del servicio de datos"""
        self.url = nueva_url
        self.version = nueva_version
        self.fecha_actualizacion = datetime.utcnow()
    
    def desactivar(self) -> None:
        """Desactiva el servicio de datos"""
        self.activo = False
        self.fecha_actualizacion = datetime.utcnow()
    
    def activar(self) -> None:
        """Activa el servicio de datos"""
        self.activo = True
        self.fecha_actualizacion = datetime.utcnow()
