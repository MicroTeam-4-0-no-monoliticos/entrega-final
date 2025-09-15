"""
Objetos de valor para el módulo de Reporting
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Dict, Any
from decimal import Decimal
from enum import Enum


class TipoReporte(Enum):
    """Enum que define los tipos de reportes disponibles"""
    PAGOS_POR_PERIODO = "pagos_por_periodo"
    CAMPANAS_ACTIVAS = "campanas_activas"
    METRICAS_GENERALES = "metricas_generales"
    AFILIADOS_TOP = "afiliados_top"
    RESUMEN_EJECUTIVO = "resumen_ejecutivo"


@dataclass(frozen=True)
class PeriodoReporte:
    """Objeto de valor que representa un período para el reporte"""
    fecha_inicio: date
    fecha_fin: date
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin")
    
    @property
    def dias_diferencia(self) -> int:
        """Calcula la diferencia en días entre las fechas"""
        return (self.fecha_fin - self.fecha_inicio).days
    
    def incluye_fecha(self, fecha: date) -> bool:
        """Verifica si una fecha está incluida en el período"""
        return self.fecha_inicio <= fecha <= self.fecha_fin


@dataclass(frozen=True)
class FiltrosReporte:
    """Objeto de valor que representa los filtros aplicables a un reporte"""
    periodo: Optional[PeriodoReporte] = None
    afiliado_id: Optional[str] = None
    campana_id: Optional[str] = None
    estado_pago: Optional[str] = None
    moneda: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte los filtros a un diccionario"""
        filtros = {}
        if self.periodo:
            filtros['fecha_inicio'] = self.periodo.fecha_inicio.isoformat()
            filtros['fecha_fin'] = self.periodo.fecha_fin.isoformat()
        if self.afiliado_id:
            filtros['afiliado_id'] = self.afiliado_id
        if self.campana_id:
            filtros['campana_id'] = self.campana_id
        if self.estado_pago:
            filtros['estado_pago'] = self.estado_pago
        if self.moneda:
            filtros['moneda'] = self.moneda
        return filtros


@dataclass(frozen=True)
class MetricaReporte:
    """Objeto de valor que representa una métrica en el reporte"""
    nombre: str
    valor: Decimal
    unidad: str
    descripcion: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if not self.nombre:
            raise ValueError("El nombre de la métrica no puede estar vacío")
        if not self.unidad:
            raise ValueError("La unidad de la métrica no puede estar vacía")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la métrica a un diccionario"""
        return {
            'nombre': self.nombre,
            'valor': float(self.valor),
            'unidad': self.unidad,
            'descripcion': self.descripcion
        }


@dataclass(frozen=True)
class URLServicioDatos:
    """Objeto de valor que representa la URL de un servicio de datos"""
    url: str
    version: str
    timeout: int = 30  # segundos
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if not self.url:
            raise ValueError("La URL no puede estar vacía")
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError("La URL debe comenzar con http:// o https://")
        if not self.version:
            raise ValueError("La versión no puede estar vacía")
        if self.timeout <= 0:
            raise ValueError("El timeout debe ser mayor a 0")
    
    def es_valida(self) -> bool:
        """Verifica si la URL es válida"""
        return bool(self.url and self.version and self.timeout > 0)
