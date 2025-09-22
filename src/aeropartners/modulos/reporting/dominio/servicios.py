"""
Servicios del dominio para el módulo de Reporting
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .entidades import Reporte, ConfiguracionServicioDatos
from .objetos_valor import FiltrosReporte, URLServicioDatos


class ServicioDatosPort(ABC):
    """Puerto abstracto para servicios de datos externos"""
    
    @abstractmethod
    async def obtener_datos_pagos(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos de pagos desde el servicio externo"""
        pass
    
    @abstractmethod
    async def obtener_datos_campanas(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos de campañas desde el servicio externo"""
        pass
    
    @abstractmethod
    async def obtener_metricas_generales(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene métricas generales desde el servicio externo"""
        pass
    
    @abstractmethod
    async def verificar_conectividad(self) -> bool:
        """Verifica si el servicio está disponible"""
        pass


class GeneradorReporteService:
    """Servicio de dominio para generar reportes"""
    
    def __init__(self, servicio_datos: ServicioDatosPort):
        self.servicio_datos = servicio_datos
    
    async def generar_reporte_pagos(self, filtros: FiltrosReporte) -> Reporte:
        """Genera un reporte de pagos"""
        datos = await self.servicio_datos.obtener_datos_pagos(filtros)
        
        return Reporte(
            id=f"pagos_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            tipo="pagos_por_periodo",
            fecha_generacion=datetime.utcnow(),
            datos=datos,
            metadatos={
                'filtros_aplicados': filtros.to_dict(),
                'total_registros': len(datos.get('pagos', [])),
                'fecha_generacion': datetime.utcnow().isoformat()
            },
            version_servicio_datos="unknown"  # Se actualizará desde la configuración
        )
    
    async def generar_reporte_campanas(self, filtros: FiltrosReporte) -> Reporte:
        """Genera un reporte de campañas"""
        datos = await self.servicio_datos.obtener_datos_campanas(filtros)
        
        return Reporte(
            id=f"campanas_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            tipo="campanas_activas",
            fecha_generacion=datetime.utcnow(),
            datos=datos,
            metadatos={
                'filtros_aplicados': filtros.to_dict(),
                'total_campanas': len(datos.get('campanas', [])),
                'fecha_generacion': datetime.utcnow().isoformat()
            },
            version_servicio_datos="unknown"
        )
    
    async def generar_reporte_metricas(self, filtros: FiltrosReporte) -> Reporte:
        """Genera un reporte de métricas generales"""
        datos = await self.servicio_datos.obtener_metricas_generales(filtros)
        
        return Reporte(
            id=f"metricas_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            tipo="metricas_generales",
            fecha_generacion=datetime.utcnow(),
            datos=datos,
            metadatos={
                'filtros_aplicados': filtros.to_dict(),
                'fecha_generacion': datetime.utcnow().isoformat()
            },
            version_servicio_datos="unknown"
        )
    
    async def generar_reporte_campana_completa(self, filtros: FiltrosReporte) -> Reporte:
        """Genera un reporte completo de campaña para SAGAs"""
        # Obtener datos de campañas y pagos
        datos_campanas = await self.servicio_datos.obtener_datos_campanas(filtros)
        datos_pagos = await self.servicio_datos.obtener_datos_pagos(filtros)
        
        # Combinar datos para reporte completo
        # El servicio de datos v1 devuelve estructura diferente:
        # - Campañas: {"campanas": [...], "total_campanas": 2}
        # - Pagos: {"total_eventos": 15, "eventos_procesados": 12, ...}
        datos_completos = {
            'campanas': datos_campanas.get('campanas', []),
            'pagos': [],  # El servicio v1 no devuelve array de pagos
            'estadisticas_pagos': {
                'total_eventos': datos_pagos.get('total_eventos', 0),
                'eventos_procesados': datos_pagos.get('eventos_procesados', 0),
                'eventos_pendientes': datos_pagos.get('eventos_pendientes', 0),
                'eventos_fallidos': datos_pagos.get('eventos_fallidos', 0)
            },
            'resumen': {
                'total_campanas': len(datos_campanas.get('campanas', [])),
                'total_pagos': 0,  # No hay array de pagos en v1
                'monto_total_pagos': 0,  # No hay datos de monto en v1
                'campanas_activas': len([c for c in datos_campanas.get('campanas', []) if c.get('estado') == 'activa']),
                'pagos_exitosos': datos_pagos.get('eventos_procesados', 0)
            }
        }
        
        return Reporte(
            id=str(uuid.uuid4()),
            tipo="CAMPAÑA_COMPLETA",
            fecha_generacion=datetime.utcnow(),
            datos=datos_completos,
            metadatos={
                'filtros_aplicados': filtros.to_dict(),
                'fecha_generacion': datetime.utcnow().isoformat(),
                'tipo_saga': 'CREAR_CAMPANA_COMPLETA'
            },
            version_servicio_datos="unknown"
        )


class ConfiguracionService:
    """Servicio de dominio para manejar configuraciones"""
    
    def __init__(self, config_repository):
        self.config_repository = config_repository
    
    def actualizar_servicio_datos(self, url: str, version: str) -> ConfiguracionServicioDatos:
        """Actualiza la configuración del servicio de datos"""
        # Desactivar configuración actual
        self.config_repository.desactivar_configuracion_actual()
        
        # Crear nueva configuración
        nueva_config = ConfiguracionServicioDatos(
            url=url,
            version=version,
            activo=True,
            fecha_actualizacion=datetime.utcnow()
        )
        
        # Guardar nueva configuración
        self.config_repository.guardar_configuracion(nueva_config)
        
        return nueva_config
    
    def obtener_servicio_activo(self) -> Optional[ConfiguracionServicioDatos]:
        """Obtiene el servicio de datos activo"""
        return self.config_repository.obtener_configuracion_activa()
    
    def verificar_disponibilidad_servicio(self, url: str) -> bool:
        """Verifica si un servicio está disponible (implementación básica)"""
        # En una implementación real, aquí harías una petición HTTP
        # Por ahora, solo validamos que la URL tenga formato correcto
        return url.startswith(('http://', 'https://'))
