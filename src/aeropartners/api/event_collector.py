from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from ..modulos.event_collector.aplicacion.comandos import ProcesarEventoTrackingCommand, ReprocesarEventoFallidoCommand
from ..modulos.event_collector.aplicacion.queries import (
    ObtenerEstadoEventoQuery, ObtenerEstadisticasProcessingQuery,
    ObtenerEventosFallidosQuery, ObtenerRateLimitStatusQuery
)
from ..modulos.event_collector.aplicacion.handlers import (
    ProcesarEventoTrackingHandler, ReprocesarEventoFallidoHandler,
    ObtenerEstadoEventoHandler, ObtenerEstadisticasProcessingHandler,
    ObtenerEventosFallidosHandler, ObtenerRateLimitStatusHandler
)
from ..modulos.event_collector import factory as ec_factory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/event-collector", tags=["Event Collector BFF"])

class EventoTrackingRequest(BaseModel):
    tipo_evento: str = Field(..., description="Tipo de evento: CLICK, IMPRESSION, CONVERSION, PAGE_VIEW")
    id_afiliado: str = Field(..., description="ID del afiliado que genera el evento")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp del evento")
    
    id_campana: Optional[str] = Field(None, description="ID de la campaña asociada")
    id_oferta: Optional[str] = Field(None, description="ID de la oferta asociada")
    url: Optional[str] = Field(None, description="URL donde ocurrió el evento")
    parametros_tracking: Optional[Dict[str, Any]] = Field(None, description="Parámetros adicionales de tracking")
    
    datos_custom: Optional[Dict[str, Any]] = Field(None, description="Datos custom del evento")
    valor_conversion: Optional[float] = Field(None, description="Valor monetario para conversiones")
    moneda: Optional[str] = Field(None, description="Moneda del valor de conversión")
    
    tipo_dispositivo: Optional[str] = Field("OTHER", description="Tipo de dispositivo: DESKTOP, MOBILE, TABLET, OTHER")
    identificador_dispositivo: Optional[str] = Field(None, description="Cookie ID, Device ID, etc.")
    sistema_operativo: Optional[str] = Field(None, description="Sistema operativo")
    navegador: Optional[str] = Field(None, description="Navegador utilizado")
    resolucion_pantalla: Optional[str] = Field(None, description="Resolución de pantalla")
    
    fuente_evento: Optional[str] = Field("WEB_TAG", description="Fuente: WEB_TAG, MOBILE_SDK, API_DIRECT, WEBHOOK")
    api_key: Optional[str] = Field(None, description="API Key para llamadas directas")
    hash_validacion: Optional[str] = Field(None, description="Hash de validación")

class EventoTrackingResponse(BaseModel):
    exito: bool
    id_evento: Optional[str] = None
    estado: Optional[str] = None
    mensaje: str
    hash_evento: Optional[str] = None
    topic_destino: Optional[str] = None
    timestamp_procesamiento: datetime = Field(default_factory=datetime.now)

class ReprocesarEventoRequest(BaseModel):
    id_evento: str
    forzar_reproceso: bool = False

class RateLimitStatusResponse(BaseModel):
    id_afiliado: str
    eventos_actuales: int
    ventana_minutos: int
    limite_maximo: Optional[int] = None
    timestamp: datetime

async def get_request_metadata(request: Request) -> Dict[str, Any]:
    return {
        'ip_origen': request.client.host,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'session_id': request.headers.get('X-Session-ID'),
        'referrer': request.headers.get('Referer')
    }

@router.post("/events", response_model=EventoTrackingResponse, status_code=201)
async def procesar_evento_tracking(
    evento_request: EventoTrackingRequest,
    request_metadata: Dict[str, Any] = Depends(get_request_metadata)
):
    try:
        handler: ProcesarEventoTrackingHandler = ec_factory.get_procesar_evento_handler()
        comando = ProcesarEventoTrackingCommand(
            tipo_evento=evento_request.tipo_evento.upper(),
            id_afiliado=evento_request.id_afiliado,
            timestamp=evento_request.timestamp or datetime.now(),
            
            id_campana=evento_request.id_campana,
            id_oferta=evento_request.id_oferta,
            url=evento_request.url,
            parametros_tracking=evento_request.parametros_tracking,
            
            datos_custom=evento_request.datos_custom,
            valor_conversion=evento_request.valor_conversion,
            moneda=evento_request.moneda,
            
            ip_origen=request_metadata['ip_origen'],
            user_agent=request_metadata['user_agent'],
            session_id=request_metadata['session_id'],
            referrer=request_metadata['referrer'],
            
            tipo_dispositivo=evento_request.tipo_dispositivo,
            identificador_dispositivo=evento_request.identificador_dispositivo,
            sistema_operativo=evento_request.sistema_operativo,
            navegador=evento_request.navegador,
            resolucion_pantalla=evento_request.resolucion_pantalla,
            
            fuente_evento=evento_request.fuente_evento,
            api_key=evento_request.api_key,
            hash_validacion=evento_request.hash_validacion
        )
        
        resultado = await handler.handle(comando)
        
        if resultado['exito']:
            return EventoTrackingResponse(
                exito=True,
                id_evento=resultado['id_evento'],
                estado=resultado['estado'],
                mensaje="Evento procesado exitosamente",
                hash_evento=resultado.get('hash_evento'),
                topic_destino=resultado.get('topic_destino')
            )
        else:
            return EventoTrackingResponse(
                exito=False,
                id_evento=resultado.get('id_evento'),
                estado=resultado.get('estado'),
                mensaje=resultado.get('razon', 'Error procesando evento')
            )
            
    except ValueError as e:
        logger.error(f"Error de validación procesando evento: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error interno procesando evento: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/events/{id_evento}/retry", response_model=EventoTrackingResponse)
async def reprocesar_evento_fallido(
    id_evento: str,
    request: ReprocesarEventoRequest
):
    try:
        handler: ReprocesarEventoFallidoHandler = ec_factory.get_retry_handler()
        comando = ReprocesarEventoFallidoCommand(
            id_evento=id_evento,
            forzar_reproceso=request.forzar_reproceso
        )
        
        resultado = await handler.handle(comando)
        
        return EventoTrackingResponse(
            exito=resultado['exito'],
            id_evento=resultado['id_evento'],
            mensaje=resultado.get('razon', 'Reproceso completado')
        )
        
    except Exception as e:
        logger.error(f"Error reprocesando evento {id_evento}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{id_evento}/status")
async def obtener_estado_evento(
    id_evento: str
):
    try:
        handler: ObtenerEstadoEventoHandler = ec_factory.get_estado_evento_handler()
        query = ObtenerEstadoEventoQuery(id_evento=id_evento)
        resultado = await handler.handle(query)
        return resultado
        
    except Exception as e:
        logger.error(f"Error consultando estado del evento {id_evento}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def obtener_estadisticas_processing(
    id_afiliado: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    tipo_evento: Optional[str] = None,
):
    try:
        handler: ObtenerEstadisticasProcessingHandler = ec_factory.get_estadisticas_handler()
        query = ObtenerEstadisticasProcessingQuery(
            id_afiliado=id_afiliado,
            desde=desde,
            hasta=hasta,
            tipo_evento=tipo_evento
        )
        
        resultado = await handler.handle(query)
        return resultado
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/failed-events")
async def obtener_eventos_fallidos(
    id_afiliado: Optional[str] = None,
    desde: Optional[datetime] = None,
    limite: int = 100,
    solo_reintentables: bool = True,
):
    try:
        handler: ObtenerEventosFallidosHandler = ec_factory.get_eventos_fallidos_handler()
        query = ObtenerEventosFallidosQuery(
            id_afiliado=id_afiliado,
            desde=desde,
            limite=limite,
            solo_reintentables=solo_reintentables
        )
        
        resultado = await handler.handle(query)
        return resultado
        
    except Exception as e:
        logger.error(f"Error obteniendo eventos fallidos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rate-limit/{id_afiliado}", response_model=RateLimitStatusResponse)
async def obtener_rate_limit_status(
    id_afiliado: str,
    ventana_minutos: int = 1,
):
    try:
        handler: ObtenerRateLimitStatusHandler = ec_factory.get_rate_limit_status_handler()
        query = ObtenerRateLimitStatusQuery(
            id_afiliado=id_afiliado,
            ventana_minutos=ventana_minutos
        )
        
        resultado = await handler.handle(query)
        
        return RateLimitStatusResponse(
            id_afiliado=resultado['id_afiliado'],
            eventos_actuales=resultado['eventos_actuales'],
            ventana_minutos=resultado['ventana_minutos'],
            timestamp=datetime.fromisoformat(resultado['timestamp'])
        )
        
    except Exception as e:
        logger.error(f"Error consultando rate limit para {id_afiliado}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "event-collector-bff",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    try:
        return {
            "status": "ready",
            "dependencies": {
                "pulsar": "connected",
                "redis": "connected"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")

@router.post("/admin/rate-limit/{id_afiliado}/reset")
async def resetear_rate_limit(
    id_afiliado: str,
):
    try:
        return {
            "mensaje": f"Rate limit reseteado para afiliado {id_afiliado}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error reseteando rate limit para {id_afiliado}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))