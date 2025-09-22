from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid

from ..modulos.saga.aplicacion.comandos import CrearCampanaCompletaCommand
from ..modulos.saga.aplicacion.handlers import CrearCampanaCompletaHandler
from ..modulos.saga.infraestructura.adaptadores import RepositorioSagaSQLAlchemy
from ..seedwork.infraestructura.pulsar_producer import PulsarEventProducer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/saga", tags=["SAGA Orchestrator"])

# Dependencias
def get_saga_repository():
    return RepositorioSagaSQLAlchemy()

def get_pulsar_producer():
    return PulsarEventProducer(topic="saga-events")

def get_saga_handler():
    return CrearCampanaCompletaHandler(
        get_saga_repository(),
        get_pulsar_producer()
    )

# Modelos de request/response
class CrearCampanaCompletaRequest(BaseModel):
    """Request para crear una campaña completa usando SAGA"""
    campana: Dict[str, Any] = Field(..., description="Datos de la campaña")
    pago: Dict[str, Any] = Field(..., description="Datos del pago")
    reporte: Dict[str, Any] = Field(..., description="Datos del reporte")
    timeout_minutos: int = Field(30, description="Timeout de la SAGA en minutos")

class CrearCampanaCompletaResponse(BaseModel):
    """Response de creación de campaña completa"""
    exito: bool
    saga_id: str
    estado: str
    mensaje: str
    datos_iniciales: Optional[Dict[str, Any]] = None

class SagaStatusResponse(BaseModel):
    """Response del estado de una SAGA"""
    saga_id: str
    estado: str
    tipo: str
    pasos: List[Dict[str, Any]]
    compensaciones: List[Dict[str, Any]]
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    error_message: Optional[str] = None

class ListarSagasResponse(BaseModel):
    """Response para listar SAGAs"""
    sagas: List[SagaStatusResponse]
    total: int
    pagina: int
    limite: int

# Endpoints
@router.post("/crear-campana-completa", response_model=CrearCampanaCompletaResponse)
async def crear_campana_completa(
    request: CrearCampanaCompletaRequest,
    saga_handler: CrearCampanaCompletaHandler = Depends(get_saga_handler)
):
    """
    Crear una campaña completa usando SAGA.
    
    Este endpoint orquesta la creación de:
    1. Una campaña (a través del proxy de campañas)
    2. Un pago (a través del servicio de pagos)
    3. Un reporte (a través del servicio de reporting)
    
    Si cualquier paso falla, se ejecutan las compensaciones automáticamente.
    """
    try:
        # Crear comando
        comando = CrearCampanaCompletaCommand(
            datos_campana=request.campana,
            datos_pago=request.pago,
            datos_reporte=request.reporte,
            timeout_minutos=request.timeout_minutos
        )
        
        # Ejecutar SAGA
        saga = saga_handler.handle(comando)
        
        # Ejecutar primer paso (crear campaña)
        await _ejecutar_primer_paso(saga)
        
        return CrearCampanaCompletaResponse(
            exito=True,
            saga_id=str(saga.id),
            estado=saga.estado.value,
            mensaje="SAGA iniciada exitosamente",
            datos_iniciales=saga.datos_iniciales
        )
        
    except Exception as e:
        logger.error(f"Error creando campaña completa: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

@router.get("/{saga_id}/status", response_model=SagaStatusResponse)
async def obtener_estado_saga(
    saga_id: str,
    saga_repo: RepositorioSagaSQLAlchemy = Depends(get_saga_repository)
):
    """Obtener el estado actual de una SAGA"""
    try:
        saga = saga_repo.obtener_por_id(saga_id)
        if not saga:
            raise HTTPException(
                status_code=404,
                detail=f"SAGA {saga_id} no encontrada"
            )
        
        return SagaStatusResponse(
            saga_id=str(saga.id),
            estado=saga.estado.value,
            tipo=saga.tipo,
            pasos=[{
                "id": paso.id,
                "tipo": paso.tipo.value,
                "exitoso": paso.exitoso,
                "error": paso.error,
                "fecha_ejecucion": paso.fecha_ejecucion.isoformat(),
                "resultado": paso.resultado
            } for paso in saga.pasos],
            compensaciones=[{
                "id": comp.id,
                "tipo": comp.tipo.value,
                "exitoso": comp.exitoso,
                "error": comp.error,
                "fecha_ejecucion": comp.fecha_ejecucion.isoformat(),
                "resultado": comp.resultado
            } for comp in saga.compensaciones],
            fecha_inicio=saga.fecha_inicio,
            fecha_fin=saga.fecha_fin,
            error_message=saga.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado de SAGA {saga_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

@router.get("/", response_model=ListarSagasResponse)
async def listar_sagas(
    estado: Optional[str] = None,
    tipo: Optional[str] = None,
    pagina: int = 1,
    limite: int = 10,
    saga_repo: RepositorioSagaSQLAlchemy = Depends(get_saga_repository)
):
    """Listar SAGAs con filtros opcionales"""
    try:
        if estado:
            sagas = saga_repo.obtener_por_estado(estado)
        elif tipo:
            sagas = saga_repo.obtener_por_tipo(tipo)
        else:
            sagas = saga_repo.obtener_todas()
        
        # Paginación simple
        inicio = (pagina - 1) * limite
        fin = inicio + limite
        sagas_paginadas = sagas[inicio:fin]
        
        return ListarSagasResponse(
            sagas=[SagaStatusResponse(
                saga_id=str(saga.id),
                estado=saga.estado.value,
                tipo=saga.tipo,
                pasos=[{
                    "id": paso.id,
                    "tipo": paso.tipo.value,
                    "exitoso": paso.exitoso,
                    "error": paso.error,
                    "fecha_ejecucion": paso.fecha_ejecucion.isoformat(),
                    "resultado": paso.resultado
                } for paso in saga.pasos],
                compensaciones=[{
                    "id": comp.id,
                    "tipo": comp.tipo.value,
                    "exitoso": comp.exitoso,
                    "error": comp.error,
                    "fecha_ejecucion": comp.fecha_ejecucion.isoformat(),
                    "resultado": comp.resultado
                } for comp in saga.compensaciones],
                fecha_inicio=saga.fecha_inicio,
                fecha_fin=saga.fecha_fin,
                error_message=saga.error_message
            ) for saga in sagas_paginadas],
            total=len(sagas),
            pagina=pagina,
            limite=limite
        )
        
    except Exception as e:
        logger.error(f"Error listando SAGAs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

@router.delete("/{saga_id}")
async def eliminar_saga(
    saga_id: str,
    saga_repo: RepositorioSagaSQLAlchemy = Depends(get_saga_repository)
):
    """Eliminar una SAGA (solo para testing/limpieza)"""
    try:
        exito = saga_repo.eliminar(saga_id)
        if not exito:
            raise HTTPException(
                status_code=404,
                detail=f"SAGA {saga_id} no encontrada"
            )
        
        return {"mensaje": f"SAGA {saga_id} eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando SAGA {saga_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

@router.delete("/cleanup")
async def limpiar_sagas(
    saga_repo: RepositorioSagaSQLAlchemy = Depends(get_saga_repository)
):
    """Limpiar todas las SAGAs (solo para pruebas)"""
    try:
        # Obtener todas las SAGAs
        sagas = saga_repo.obtener_todas()
        total_sagas = len(sagas)
        
        # Eliminar todas las SAGAs
        for saga in sagas:
            saga_repo.eliminar(str(saga.id))
        
        return {
            "mensaje": f"Se eliminaron {total_sagas} SAGAs",
            "total_eliminadas": total_sagas,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando SAGAs: {str(e)}"
        )

@router.delete("/cleanup-all")
async def limpiar_todo(
    saga_repo: RepositorioSagaSQLAlchemy = Depends(get_saga_repository)
):
    """Limpiar todos los datos (SAGAs, campañas, pagos) - solo para pruebas"""
    try:
        import httpx
        
        # Limpiar SAGAs
        sagas = saga_repo.obtener_todas()
        total_sagas = len(sagas)
        for saga in sagas:
            saga_repo.eliminar(str(saga.id))
        
        # Limpiar campañas
        try:
            response_campanas = httpx.delete("http://localhost:8080/api/campaigns/cleanup")
            campanas_eliminadas = response_campanas.json() if response_campanas.status_code == 200 else {"total_eliminadas": 0}
        except:
            campanas_eliminadas = {"total_eliminadas": 0}
        
        # Limpiar pagos
        try:
            response_pagos = httpx.delete("http://localhost:8000/pagos/cleanup")
            pagos_eliminados = response_pagos.json() if response_pagos.status_code == 200 else {"total_eliminados": 0}
        except:
            pagos_eliminados = {"total_eliminados": 0}
        
        return {
            "mensaje": "Limpieza completa realizada",
            "sagas_eliminadas": total_sagas,
            "campanas_eliminadas": campanas_eliminadas.get("total_eliminadas", 0),
            "pagos_eliminados": pagos_eliminados.get("total_eliminados", 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en limpieza completa: {str(e)}"
        )

# Función auxiliar para ejecutar el primer paso
async def _ejecutar_primer_paso(saga):
    """Ejecutar el primer paso de la SAGA (crear campaña)"""
    try:
        import httpx
        
        # Obtener el primer paso
        primer_paso = saga.pasos[0] if saga.pasos else None
        if not primer_paso:
            return
        
        # Llamar al proxy de campañas
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://campaigns-proxy:8080/api/campaigns/",
                json=primer_paso.datos
            )
            
            if response.status_code == 200:
                resultado = response.json()
                primer_paso.marcar_exitoso(resultado)
                logger.info(f"Primer paso de SAGA {saga.id} ejecutado exitosamente")
            else:
                primer_paso.marcar_fallido(f"HTTP {response.status_code}: {response.text}")
                logger.error(f"Primer paso de SAGA {saga.id} falló: {response.text}")
                
    except Exception as e:
        if primer_paso:
            primer_paso.marcar_fallido(str(e))
        logger.error(f"Error ejecutando primer paso de SAGA {saga.id}: {str(e)}")
