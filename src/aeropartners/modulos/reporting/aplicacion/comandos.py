"""
Comandos de aplicación para el módulo de Reporting
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import date

from ..dominio.objetos_valor import FiltrosReporte, PeriodoReporte


@dataclass
class GenerarReporteCommand:
    """Comando para generar un reporte"""
    tipo_reporte: str
    filtros: Optional[Dict[str, Any]] = None
    
    def to_filtros(self) -> FiltrosReporte:
        """Convierte los filtros del comando a FiltrosReporte"""
        if not self.filtros:
            return FiltrosReporte()
        
        periodo = None
        if 'fecha_inicio' in self.filtros and 'fecha_fin' in self.filtros:
            try:
                periodo = PeriodoReporte(
                    fecha_inicio=date.fromisoformat(str(self.filtros['fecha_inicio'])),
                    fecha_fin=date.fromisoformat(str(self.filtros['fecha_fin']))
                )
            except (ValueError, TypeError) as e:
                # Si hay error en el parsing de fechas, continuar sin período
                pass
        
        return FiltrosReporte(
            periodo=periodo,
            afiliado_id=self.filtros.get('afiliado_id'),
            campana_id=self.filtros.get('campana_id'),
            estado_pago=self.filtros.get('estado_pago'),
            moneda=self.filtros.get('moneda')
        )


@dataclass
class ActualizarServicioDatosCommand:
    """Comando para actualizar el servicio de datos"""
    url: str
    version: str
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if not self.url:
            raise ValueError("La URL no puede estar vacía")
        if not self.version:
            raise ValueError("La versión no puede estar vacía")
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError("La URL debe comenzar con http:// o https://")


@dataclass
class VerificarServicioDatosCommand:
    """Comando para verificar la conectividad del servicio de datos"""
    url: Optional[str] = None  # Si no se proporciona, usa el servicio activo
