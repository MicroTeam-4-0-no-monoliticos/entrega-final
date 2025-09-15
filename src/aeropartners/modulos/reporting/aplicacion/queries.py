"""
Queries de aplicación para el módulo de Reporting
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date

from ..dominio.entidades import Reporte, ConfiguracionServicioDatos
from ..dominio.objetos_valor import FiltrosReporte, PeriodoReporte


@dataclass
class ObtenerReporteQuery:
    """Query para obtener un reporte por ID"""
    reporte_id: str


@dataclass
class ObtenerReportesPorTipoQuery:
    """Query para obtener reportes por tipo con filtros opcionales"""
    tipo_reporte: str
    filtros: Optional[Dict[str, Any]] = None
    limite: int = 10
    
    def to_filtros(self) -> FiltrosReporte:
        """Convierte los filtros del query a FiltrosReporte"""
        if not self.filtros:
            return FiltrosReporte()
        
        periodo = None
        if 'fecha_inicio' in self.filtros and 'fecha_fin' in self.filtros:
            periodo = PeriodoReporte(
                fecha_inicio=date.fromisoformat(self.filtros['fecha_inicio']),
                fecha_fin=date.fromisoformat(self.filtros['fecha_fin'])
            )
        
        return FiltrosReporte(
            periodo=periodo,
            afiliado_id=self.filtros.get('afiliado_id'),
            campana_id=self.filtros.get('campana_id'),
            estado_pago=self.filtros.get('estado_pago'),
            moneda=self.filtros.get('moneda')
        )


@dataclass
class ObtenerReportesRecientesQuery:
    """Query para obtener los reportes más recientes"""
    limite: int = 10


@dataclass
class ObtenerConfiguracionServicioQuery:
    """Query para obtener la configuración del servicio de datos"""
    incluir_historial: bool = False


@dataclass
class ObtenerEstadisticasServicioQuery:
    """Query para obtener estadísticas del servicio de datos"""
    url: Optional[str] = None
