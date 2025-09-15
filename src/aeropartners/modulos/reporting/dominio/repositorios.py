"""
Repositorios del dominio para el módulo de Reporting
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from .entidades import Reporte, ConfiguracionServicioDatos
from .objetos_valor import FiltrosReporte


class ReporteRepository(ABC):
    """Repositorio abstracto para la entidad Reporte"""
    
    @abstractmethod
    def guardar(self, reporte: Reporte) -> None:
        """Guarda un reporte"""
        pass
    
    @abstractmethod
    def obtener_por_id(self, reporte_id: str) -> Optional[Reporte]:
        """Obtiene un reporte por su ID"""
        pass
    
    @abstractmethod
    def obtener_por_tipo(self, tipo: str, filtros: Optional[FiltrosReporte] = None) -> List[Reporte]:
        """Obtiene reportes por tipo con filtros opcionales"""
        pass
    
    @abstractmethod
    def obtener_recientes(self, limite: int = 10) -> List[Reporte]:
        """Obtiene los reportes más recientes"""
        pass
    
    @abstractmethod
    def eliminar_antiguos(self, dias_antiguedad: int) -> int:
        """Elimina reportes más antiguos que el número de días especificado"""
        pass


class ConfiguracionServicioDatosRepository(ABC):
    """Repositorio abstracto para la configuración del servicio de datos"""
    
    @abstractmethod
    def obtener_configuracion_activa(self) -> Optional[ConfiguracionServicioDatos]:
        """Obtiene la configuración activa del servicio de datos"""
        pass
    
    @abstractmethod
    def guardar_configuracion(self, configuracion: ConfiguracionServicioDatos) -> None:
        """Guarda la configuración del servicio de datos"""
        pass
    
    @abstractmethod
    def obtener_historial_configuraciones(self) -> List[ConfiguracionServicioDatos]:
        """Obtiene el historial de configuraciones"""
        pass
    
    @abstractmethod
    def desactivar_configuracion_actual(self) -> None:
        """Desactiva la configuración actual"""
        pass
