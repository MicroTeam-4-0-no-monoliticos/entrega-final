"""
Handlers de aplicación para el módulo de Reporting
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..dominio.entidades import Reporte, ConfiguracionServicioDatos
from ..dominio.servicios import GeneradorReporteService, ConfiguracionService
from ..dominio.repositorios import ReporteRepository, ConfiguracionServicioDatosRepository
from ..infraestructura.adaptadores import ServicioDatosAdapter
from .comandos import (
    GenerarReporteCommand, 
    ActualizarServicioDatosCommand, 
    VerificarServicioDatosCommand
)
from .queries import (
    ObtenerReporteQuery,
    ObtenerReportesPorTipoQuery,
    ObtenerReportesRecientesQuery,
    ObtenerConfiguracionServicioQuery,
    ObtenerEstadisticasServicioQuery
)

logger = logging.getLogger(__name__)


class GenerarReporteHandler:
    """Handler para generar reportes"""
    
    def __init__(
        self, 
        reporte_repository: ReporteRepository,
        config_repository: ConfiguracionServicioDatosRepository
    ):
        self.reporte_repository = reporte_repository
        self.config_repository = config_repository
    
    async def handle(self, command: GenerarReporteCommand) -> Reporte:
        """Maneja el comando de generar reporte"""
        try:
            # Obtener configuración del servicio de datos activo
            config = self.config_repository.obtener_configuracion_activa()
            if not config:
                raise ValueError("No hay servicio de datos configurado")
            
            if not config.activo:
                raise ValueError("El servicio de datos no está activo")
            
            # Crear adaptador del servicio de datos
            servicio_datos = ServicioDatosAdapter(config.url, config.version)
            
            # Crear servicio de generación de reportes
            generador_service = GeneradorReporteService(servicio_datos)
            
            # Convertir filtros
            filtros = command.to_filtros()
            
            # Generar reporte según el tipo
            if command.tipo_reporte == "pagos_por_periodo":
                reporte = await generador_service.generar_reporte_pagos(filtros)
            elif command.tipo_reporte == "campanas_activas":
                reporte = await generador_service.generar_reporte_campanas(filtros)
            elif command.tipo_reporte == "metricas_generales":
                reporte = await generador_service.generar_reporte_metricas(filtros)
            else:
                raise ValueError(f"Tipo de reporte no soportado: {command.tipo_reporte}")
            
            # Actualizar versión del servicio en el reporte
            reporte.version_servicio_datos = config.version
            
            # Guardar reporte
            self.reporte_repository.guardar(reporte)
            
            logger.info(f"Reporte generado exitosamente: {reporte.id}")
            return reporte
            
        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}")
            raise


class ActualizarServicioDatosHandler:
    """Handler para actualizar el servicio de datos"""
    
    def __init__(self, config_repository: ConfiguracionServicioDatosRepository):
        self.config_repository = config_repository
        self.config_service = ConfiguracionService(config_repository)
    
    def handle(self, command: ActualizarServicioDatosCommand) -> ConfiguracionServicioDatos:
        """Maneja el comando de actualizar servicio de datos"""
        try:
            # Verificar que la URL sea válida
            if not self.config_service.verificar_disponibilidad_servicio(command.url):
                raise ValueError("La URL del servicio no es válida")
            
            # Actualizar configuración
            nueva_config = self.config_service.actualizar_servicio_datos(
                command.url, 
                command.version
            )
            
            logger.info(f"Servicio de datos actualizado: {command.url} (v{command.version})")
            return nueva_config
            
        except Exception as e:
            logger.error(f"Error actualizando servicio de datos: {str(e)}")
            raise


class VerificarServicioDatosHandler:
    """Handler para verificar la conectividad del servicio de datos"""
    
    def __init__(self, config_repository: ConfiguracionServicioDatosRepository):
        self.config_repository = config_repository
    
    async def handle(self, command: VerificarServicioDatosCommand) -> Dict[str, Any]:
        """Maneja el comando de verificar servicio de datos"""
        try:
            url = command.url
            if not url:
                config = self.config_repository.obtener_configuracion_activa()
                if not config:
                    return {"disponible": False, "error": "No hay servicio configurado"}
                url = config.url
            
            # Crear adaptador temporal para verificar conectividad
            servicio_datos = ServicioDatosAdapter(url, "verificacion")
            disponible = await servicio_datos.verificar_conectividad()
            
            return {
                "disponible": disponible,
                "url": url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verificando servicio de datos: {str(e)}")
            return {
                "disponible": False,
                "error": str(e),
                "url": command.url or "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }


class ObtenerReporteHandler:
    """Handler para obtener reportes"""
    
    def __init__(self, reporte_repository: ReporteRepository):
        self.reporte_repository = reporte_repository
    
    def handle(self, query: ObtenerReporteQuery) -> Optional[Reporte]:
        """Maneja el query de obtener reporte por ID"""
        return self.reporte_repository.obtener_por_id(query.reporte_id)
    
    def handle_por_tipo(self, query: ObtenerReportesPorTipoQuery) -> List[Reporte]:
        """Maneja el query de obtener reportes por tipo"""
        filtros = query.to_filtros()
        return self.reporte_repository.obtener_por_tipo(query.tipo_reporte, filtros)
    
    def handle_recientes(self, query: ObtenerReportesRecientesQuery) -> List[Reporte]:
        """Maneja el query de obtener reportes recientes"""
        return self.reporte_repository.obtener_recientes(query.limite)


class ObtenerConfiguracionHandler:
    """Handler para obtener configuraciones"""
    
    def __init__(self, config_repository: ConfiguracionServicioDatosRepository):
        self.config_repository = config_repository
    
    def handle(self, query: ObtenerConfiguracionServicioQuery) -> Dict[str, Any]:
        """Maneja el query de obtener configuración"""
        config_activa = self.config_repository.obtener_configuracion_activa()
        
        resultado = {
            "configuracion_activa": config_activa.__dict__ if config_activa else None
        }
        
        if query.incluir_historial:
            historial = self.config_repository.obtener_historial_configuraciones()
            resultado["historial"] = [config.__dict__ for config in historial]
        
        return resultado
