"""
API endpoints para el módulo de Reporting
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import date
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..modulos.reporting.aplicacion.comandos import (
    GenerarReporteCommand,
    ActualizarServicioDatosCommand,
    VerificarServicioDatosCommand
)
from ..modulos.reporting.aplicacion.queries import (
    ObtenerReporteQuery,
    ObtenerReportesPorTipoQuery,
    ObtenerReportesRecientesQuery,
    ObtenerConfiguracionServicioQuery
)
from ..modulos.reporting.aplicacion.handlers import (
    GenerarReporteHandler,
    ActualizarServicioDatosHandler,
    VerificarServicioDatosHandler,
    ObtenerReporteHandler,
    ObtenerConfiguracionHandler
)
from ..modulos.reporting.infraestructura.repositorios import (
    ReporteRepositoryImpl,
    ConfiguracionServicioDatosRepositoryImpl
)
from ..seedwork.infraestructura.db import DATABASE_URL

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/reporting", tags=["reporting"])

# Dependencias
def get_reporte_repository():
    """Obtiene el repositorio de reportes"""
    return ReporteRepositoryImpl(DATABASE_URL)

def get_config_repository():
    """Obtiene el repositorio de configuración"""
    return ConfiguracionServicioDatosRepositoryImpl(DATABASE_URL)

def get_generar_handler():
    """Obtiene el handler de generar reportes"""
    return GenerarReporteHandler(
        get_reporte_repository(),
        get_config_repository()
    )

def get_actualizar_handler():
    """Obtiene el handler de actualizar servicio"""
    return ActualizarServicioDatosHandler(get_config_repository())

def get_verificar_handler():
    """Obtiene el handler de verificar servicio"""
    return VerificarServicioDatosHandler(get_config_repository())

def get_obtener_handler():
    """Obtiene el handler de obtener reportes"""
    return ObtenerReporteHandler(get_reporte_repository())

def get_config_handler():
    """Obtiene el handler de configuración"""
    return ObtenerConfiguracionHandler(get_config_repository())


# Modelos Pydantic para requests/responses
class FiltrosReporteRequest(BaseModel):
    """Modelo para filtros de reporte"""
    fecha_inicio: Optional[date] = Field(None, description="Fecha de inicio del período")
    fecha_fin: Optional[date] = Field(None, description="Fecha de fin del período")
    afiliado_id: Optional[str] = Field(None, description="ID del afiliado")
    campana_id: Optional[str] = Field(None, description="ID de la campaña")
    estado_pago: Optional[str] = Field(None, description="Estado del pago")
    moneda: Optional[str] = Field(None, description="Moneda")

class GenerarReporteRequest(BaseModel):
    """Modelo para generar reporte"""
    tipo_reporte: str = Field(..., description="Tipo de reporte a generar")
    filtros: Optional[FiltrosReporteRequest] = Field(None, description="Filtros opcionales")

class ActualizarServicioRequest(BaseModel):
    """Modelo para actualizar servicio de datos"""
    url: str = Field(..., description="URL del servicio de datos")
    version: str = Field(..., description="Versión del servicio de datos")

class ReporteResponse(BaseModel):
    """Modelo de respuesta para reportes"""
    id: str
    tipo: str
    fecha_generacion: str
    datos: Dict[str, Any]
    metadatos: Dict[str, Any]
    version_servicio_datos: str

class ConfiguracionResponse(BaseModel):
    """Modelo de respuesta para configuración"""
    configuracion_activa: Optional[Dict[str, Any]]
    historial: Optional[List[Dict[str, Any]]] = None

class VerificacionResponse(BaseModel):
    """Modelo de respuesta para verificación de servicio"""
    disponible: bool
    url: str
    timestamp: str
    error: Optional[str] = None


# ENDPOINT PRINCIPAL DE LÓGICA DE NEGOCIO
@router.post("/report", response_model=ReporteResponse)
async def generar_reporte(
    request: GenerarReporteRequest,
    handler: GenerarReporteHandler = Depends(get_generar_handler)
):
    """
    **Endpoint de Lógica de Negocio** - Genera un reporte
    
    Este es el endpoint que el usuario final llama para obtener el reporte.
    Su lógica es simple y no se modifica, que usa la URL del servicio de datos 
    que esté configurada en ese momento.
    """
    try:
        # Convertir request a comando
        filtros_dict = request.filtros.dict() if request.filtros else None
        command = GenerarReporteCommand(
            tipo_reporte=request.tipo_reporte,
            filtros=filtros_dict
        )
        
        # Generar reporte
        reporte = await handler.handle(command)
        
        # Convertir a response
        return ReporteResponse(
            id=reporte.id,
            tipo=reporte.tipo,
            fecha_generacion=reporte.fecha_generacion.isoformat(),
            datos=reporte.datos,
            metadatos=reporte.metadatos,
            version_servicio_datos=reporte.version_servicio_datos
        )
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generando reporte: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ENDPOINT DE ADMINISTRACIÓN PARA CAMBIAR SERVICIOS
@router.post("/admin/servicio-datos", response_model=Dict[str, str])
async def actualizar_servicio_datos(
    request: ActualizarServicioRequest,
    handler: ActualizarServicioDatosHandler = Depends(get_actualizar_handler)
):
    """
    **Endpoint de Administración** - Cambia el servicio de datos
    
    Este endpoint es el corazón de la facilidad de modificación sin interrupción.
    Es un punto de control que solo debe ser accesible para sistemas internos.
    """
    try:
        # Convertir request a comando
        command = ActualizarServicioDatosCommand(
            url=request.url,
            version=request.version
        )
        
        # Actualizar configuración
        configuracion = handler.handle(command)
        
        logger.info(f"Servicio de datos actualizado: {request.url} (v{request.version})")
        
        return {
            "mensaje": "Servicio de datos actualizado exitosamente",
            "url": configuracion.url,
            "version": configuracion.version,
            "fecha_actualizacion": configuracion.fecha_actualizacion.isoformat()
        }
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error actualizando servicio: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ENDPOINTS ADICIONALES DE CONSULTA
@router.get("/report/{reporte_id}", response_model=ReporteResponse)
async def obtener_reporte(
    reporte_id: str,
    handler: ObtenerReporteHandler = Depends(get_obtener_handler)
):
    """Obtiene un reporte por ID"""
    try:
        query = ObtenerReporteQuery(reporte_id=reporte_id)
        reporte = handler.handle(query)
        
        if not reporte:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
        
        return ReporteResponse(
            id=reporte.id,
            tipo=reporte.tipo,
            fecha_generacion=reporte.fecha_generacion.isoformat(),
            datos=reporte.datos,
            metadatos=reporte.metadatos,
            version_servicio_datos=reporte.version_servicio_datos
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo reporte: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reports", response_model=List[ReporteResponse])
async def obtener_reportes(
    tipo: Optional[str] = Query(None, description="Tipo de reporte"),
    limite: int = Query(10, description="Límite de resultados"),
    handler: ObtenerReporteHandler = Depends(get_obtener_handler)
):
    """Obtiene reportes con filtros opcionales"""
    try:
        if tipo:
            query = ObtenerReportesPorTipoQuery(tipo_reporte=tipo, limite=limite)
            reportes = handler.handle_por_tipo(query)
        else:
            query = ObtenerReportesRecientesQuery(limite=limite)
            reportes = handler.handle_recientes(query)
        
        return [
            ReporteResponse(
                id=r.id,
                tipo=r.tipo,
                fecha_generacion=r.fecha_generacion.isoformat(),
                datos=r.datos,
                metadatos=r.metadatos,
                version_servicio_datos=r.version_servicio_datos
            )
            for r in reportes
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo reportes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/admin/configuracion", response_model=ConfiguracionResponse)
async def obtener_configuracion(
    incluir_historial: bool = Query(False, description="Incluir historial de configuraciones"),
    handler: ObtenerConfiguracionHandler = Depends(get_config_handler)
):
    """Obtiene la configuración actual del servicio de datos"""
    try:
        query = ObtenerConfiguracionServicioQuery(incluir_historial=incluir_historial)
        resultado = handler.handle(query)
        
        return ConfiguracionResponse(**resultado)
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/admin/verificar-servicio", response_model=VerificacionResponse)
async def verificar_servicio(
    url: Optional[str] = Query(None, description="URL del servicio a verificar"),
    handler: VerificarServicioDatosHandler = Depends(get_verificar_handler)
):
    """Verifica la conectividad del servicio de datos"""
    try:
        command = VerificarServicioDatosCommand(url=url)
        resultado = await handler.handle(command)
        
        return VerificacionResponse(**resultado)
        
    except Exception as e:
        logger.error(f"Error verificando servicio: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Health check específico para reporting
@router.get("/health")
async def health_check():
    """Health check para el servicio de reporting"""
    return {
        "status": "healthy",
        "service": "reporting",
        "timestamp": "2024-01-15T10:30:00Z"
    }
