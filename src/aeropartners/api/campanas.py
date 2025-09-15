from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

from ..modulos.campanas.aplicacion.comandos import (
    CrearCampanaCommand, ActualizarPresupuestoCampanaCommand, ActivarCampanaCommand,
    ActualizarInformacionCampanaCommand, ActualizarMetricasCampanaCommand,
    PausarCampanaCommand, FinalizarCampanaCommand, CancelarCampanaCommand
)
from ..modulos.campanas.aplicacion.queries import (
    ObtenerCampanaPorIdQuery, ListarCampanasQuery, ObtenerMetricasCampanaQuery,
    ObtenerEstadisticasGeneralesQuery
)
from ..modulos.campanas.aplicacion.handlers import (
    CrearCampanaHandler, ActualizarPresupuestoCampanaHandler, ActivarCampanaHandler,
    ActualizarInformacionCampanaHandler, ActualizarMetricasCampanaHandler,
    PausarCampanaHandler, FinalizarCampanaHandler, CancelarCampanaHandler,
    ObtenerCampanaPorIdHandler, ListarCampanasHandler, ObtenerMetricasCampanaHandler,
    ObtenerEstadisticasGeneralesHandler
)
from ..modulos.campanas.infraestructura.adaptadores import RepositorioCampanasSQLAlchemy
from ..modulos.campanas.infraestructura.outbox import OutboxCampanasProcessor

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Dependencias
def get_repositorio_campanas():
    return RepositorioCampanasSQLAlchemy()

def get_outbox_processor():
    return OutboxCampanasProcessor()

# DTOs para la API

class PresupuestoRequest(BaseModel):
    monto: Decimal
    moneda: str

class CrearCampanaRequest(BaseModel):
    nombre: str
    tipo: str
    presupuesto: PresupuestoRequest
    fecha_inicio: datetime
    fecha_fin: datetime
    id_afiliado: str
    descripcion: Optional[str] = None

class ActualizarPresupuestoRequest(BaseModel):
    monto: Decimal
    moneda: str

class ActualizarInformacionRequest(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None

class ActualizarMetricasRequest(BaseModel):
    impresiones: Optional[int] = None
    clicks: Optional[int] = None
    conversiones: Optional[int] = None
    gasto_actual: Optional[Decimal] = None

class CampanaResponse(BaseModel):
    id: str
    nombre: str
    tipo: str
    descripcion: Optional[str]
    estado: str
    presupuesto: dict
    fecha_inicio: str
    fecha_fin: str
    fecha_creacion: str
    fecha_actualizacion: str
    id_afiliado: str
    metricas: dict

class ListaCampanasResponse(BaseModel):
    campanas: List[dict]
    total: int
    limit: int
    offset: int

class MetricasResponse(BaseModel):
    id_campana: str
    metricas_basicas: dict
    metricas_calculadas: dict
    rendimiento: str
    optimizaciones: dict

class EstadisticasResponse(BaseModel):
    total_campanas: int
    metricas_agregadas: dict
    distribucion_por_estado: dict
    id_afiliado: Optional[str]

class OutboxStatsResponse(BaseModel):
    total_eventos: int
    eventos_procesados: int
    eventos_pendientes: int
    distribucion_por_tipo: dict

# Endpoints de Comandos (CQS - Commands)

@router.post("/", response_model=CampanaResponse)
async def crear_campana(
    request: CrearCampanaRequest,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Crear una nueva campaña"""
    try:
        # Crear comando
        comando = CrearCampanaCommand(
            nombre=request.nombre,
            tipo=request.tipo,
            presupuesto_monto=request.presupuesto.monto,
            presupuesto_moneda=request.presupuesto.moneda,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            id_afiliado=request.id_afiliado,
            descripcion=request.descripcion
        )
        
        # Ejecutar comando
        handler = CrearCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        # Mapear respuesta
        return CampanaResponse(
            id=str(campana.id),
            nombre=campana.nombre,
            tipo=campana.tipo.value,
            descripcion=campana.descripcion,
            estado=campana.estado.value,
            presupuesto={
                "monto": float(campana.presupuesto.monto),
                "moneda": campana.presupuesto.moneda.value
            },
            fecha_inicio=campana.fecha_inicio.isoformat(),
            fecha_fin=campana.fecha_fin.isoformat(),
            fecha_creacion=campana.fecha_creacion.isoformat(),
            fecha_actualizacion=campana.fecha_actualizacion.isoformat(),
            id_afiliado=campana.id_afiliado,
            metricas={
                "impresiones": campana.metricas.impresiones,
                "clicks": campana.metricas.clicks,
                "conversiones": campana.metricas.conversiones,
                "gasto_actual": float(campana.metricas.gasto_actual),
                "ctr": campana.metricas.ctr,
                "tasa_conversion": campana.metricas.tasa_conversion
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_campana}/budget")
async def actualizar_presupuesto(
    id_campana: str,
    request: ActualizarPresupuestoRequest,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Actualizar el presupuesto de una campaña"""
    try:
        comando = ActualizarPresupuestoCampanaCommand(
            id_campana=uuid.UUID(id_campana),
            nuevo_presupuesto_monto=request.monto,
            nueva_moneda=request.moneda
        )
        
        handler = ActualizarPresupuestoCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        return {"message": "Presupuesto actualizado exitosamente", "id_campana": str(campana.id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_campana}/activate")
async def activar_campana(
    id_campana: str,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Activar una campaña"""
    try:
        comando = ActivarCampanaCommand(id_campana=uuid.UUID(id_campana))
        
        handler = ActivarCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        return {"message": "Campaña activada exitosamente", "id_campana": str(campana.id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_campana}")
async def actualizar_informacion(
    id_campana: str,
    request: ActualizarInformacionRequest,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Actualizar información básica de una campaña"""
    try:
        comando = ActualizarInformacionCampanaCommand(
            id_campana=uuid.UUID(id_campana),
            nombre=request.nombre,
            descripcion=request.descripcion,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin
        )
        
        handler = ActualizarInformacionCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        return {"message": "Campaña actualizada exitosamente", "id_campana": str(campana.id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_campana}/metrics")
async def actualizar_metricas(
    id_campana: str,
    request: ActualizarMetricasRequest,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Actualizar métricas de una campaña"""
    try:
        comando = ActualizarMetricasCampanaCommand(
            id_campana=uuid.UUID(id_campana),
            impresiones=request.impresiones,
            clicks=request.clicks,
            conversiones=request.conversiones,
            gasto_actual=request.gasto_actual
        )
        
        handler = ActualizarMetricasCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        return {"message": "Métricas actualizadas exitosamente", "id_campana": str(campana.id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_campana}/pause")
async def pausar_campana(
    id_campana: str,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Pausar una campaña"""
    try:
        comando = PausarCampanaCommand(id_campana=uuid.UUID(id_campana))
        
        handler = PausarCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        return {"message": "Campaña pausada exitosamente", "id_campana": str(campana.id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_campana}/finish")
async def finalizar_campana(
    id_campana: str,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Finalizar una campaña"""
    try:
        comando = FinalizarCampanaCommand(id_campana=uuid.UUID(id_campana))
        
        handler = FinalizarCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        return {"message": "Campaña finalizada exitosamente", "id_campana": str(campana.id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_campana}/cancel")
async def cancelar_campana(
    id_campana: str,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Cancelar una campaña"""
    try:
        comando = CancelarCampanaCommand(id_campana=uuid.UUID(id_campana))
        
        handler = CancelarCampanaHandler(repositorio)
        campana = handler.handle(comando)
        
        return {"message": "Campaña cancelada exitosamente", "id_campana": str(campana.id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# Endpoints de Queries (CQS - Queries)

# Endpoint de health check (debe ir antes que /{id_campana})
@router.get("/health")
async def health_check():
    """Health check para el servicio de campañas"""
    try:
        # Verificar conexión a base de datos
        repositorio = RepositorioCampanasSQLAlchemy()
        repositorio.listar(limit=1)
        
        return {
            "status": "healthy",
            "service": "campaigns",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Service unhealthy: {str(e)}"
        )

# Endpoint adicional /healthz para compatibilidad con el proxy
@router.get("/healthz")
async def healthz_check():
    """Health check alternativo para compatibilidad con proxy"""
    return await health_check()

@router.get("/{id_campana}", response_model=CampanaResponse)
async def obtener_campana(
    id_campana: str,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Obtener una campaña por su ID"""
    try:
        query = ObtenerCampanaPorIdQuery(id_campana=uuid.UUID(id_campana))
        
        handler = ObtenerCampanaPorIdHandler(repositorio)
        resultado = handler.handle(query)
        
        if resultado.resultado is None:
            raise HTTPException(status_code=404, detail="Campaña no encontrada")
        
        return CampanaResponse(**resultado.resultado)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de campaña inválido")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/", response_model=ListaCampanasResponse)
async def listar_campanas(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    id_afiliado: Optional[str] = Query(None),
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Listar campañas con paginación"""
    try:
        query = ListarCampanasQuery(
            limit=limit,
            offset=offset,
            id_afiliado=id_afiliado
        )
        
        handler = ListarCampanasHandler(repositorio)
        resultado = handler.handle(query)
        
        return ListaCampanasResponse(**resultado.resultado)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{id_campana}/metrics", response_model=MetricasResponse)
async def obtener_metricas_campana(
    id_campana: str,
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Obtener métricas detalladas de una campaña"""
    try:
        query = ObtenerMetricasCampanaQuery(id_campana=uuid.UUID(id_campana))
        
        handler = ObtenerMetricasCampanaHandler(repositorio)
        resultado = handler.handle(query)
        
        if resultado.resultado is None:
            raise HTTPException(status_code=404, detail="Campaña no encontrada")
        
        return MetricasResponse(**resultado.resultado)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de campaña inválido")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/stats/general", response_model=EstadisticasResponse)
async def obtener_estadisticas_generales(
    id_afiliado: Optional[str] = Query(None),
    repositorio: RepositorioCampanasSQLAlchemy = Depends(get_repositorio_campanas)
):
    """Obtener estadísticas generales de campañas"""
    try:
        query = ObtenerEstadisticasGeneralesQuery(id_afiliado=id_afiliado)
        
        handler = ObtenerEstadisticasGeneralesHandler(repositorio)
        resultado = handler.handle(query)
        
        return EstadisticasResponse(**resultado.resultado)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# Endpoint para estadísticas del outbox
@router.get("/outbox/stats", response_model=OutboxStatsResponse)
async def obtener_estadisticas_outbox(
    outbox_processor: OutboxCampanasProcessor = Depends(get_outbox_processor)
):
    """Obtener estadísticas del outbox de campañas"""
    try:
        stats = outbox_processor.obtener_estadisticas()
        return OutboxStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

