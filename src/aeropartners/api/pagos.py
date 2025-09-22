from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from ..modulos.pagos.aplicacion.comandos import ProcesarPagoCommand, RevertirPagoCommand
from ..modulos.pagos.aplicacion.queries import ObtenerEstadoPagoQuery
from ..modulos.pagos.aplicacion.handlers import ProcesarPagoHandler, ObtenerEstadoPagoHandler, RevertirPagoHandler
from ..modulos.pagos.infraestructura.adaptadores import RepositorioPagosSQLAlchemy, StripeAdapter
from ..modulos.pagos.infraestructura.outbox import OutboxProcessor

router = APIRouter(prefix="/pagos", tags=["pagos"])

# Dependencias
def get_repositorio_pagos():
    return RepositorioPagosSQLAlchemy()

def get_pasarela_pagos():
    return StripeAdapter()

def get_outbox_processor():
    return OutboxProcessor()

# DTOs para la API
class ProcesarPagoRequest(BaseModel):
    id_afiliado: str
    monto: float
    moneda: str
    referencia_pago: str

class ProcesarPagoResponse(BaseModel):
    id_pago: str
    id_afiliado: str
    monto: float
    moneda: str
    estado: str
    referencia_pago: str
    fecha_creacion: str
    mensaje: str

class RevertirPagoRequest(BaseModel):
    motivo: str
    saga_id: Optional[str] = None

class RevertirPagoResponse(BaseModel):
    id_pago: str
    estado: str
    mensaje: str

class EstadoPagoResponse(BaseModel):
    id: str
    id_afiliado: str
    monto: float
    moneda: str
    estado: str
    referencia_pago: str
    fecha_creacion: str
    fecha_procesamiento: Optional[str]
    mensaje_error: Optional[str]

class OutboxStatsResponse(BaseModel):
    total_eventos: int
    eventos_procesados: int
    eventos_pendientes: int

@router.post("/", response_model=ProcesarPagoResponse)
async def procesar_pago(
    request: ProcesarPagoRequest,
    repositorio: RepositorioPagosSQLAlchemy = Depends(get_repositorio_pagos),
    pasarela: StripeAdapter = Depends(get_pasarela_pagos)
):
    """
    Procesa un nuevo pago para un afiliado
    """
    try:
        # Crear comando
        comando = ProcesarPagoCommand(
            id_afiliado=request.id_afiliado,
            monto=request.monto,
            moneda=request.moneda,
            referencia_pago=request.referencia_pago
        )
        
        # Ejecutar comando
        handler = ProcesarPagoHandler(repositorio, pasarela)
        pago = handler.handle(comando)
        
        return ProcesarPagoResponse(
            id_pago=str(pago.id),
            id_afiliado=pago.id_afiliado,
            monto=pago.monto.monto,
            moneda=pago.monto.moneda.value,
            estado=pago.estado.value,
            referencia_pago=pago.referencia_pago,
            fecha_creacion=pago.fecha_creacion.isoformat(),
            mensaje="El pago sera procesado en poco tiempo"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{id_pago}", response_model=EstadoPagoResponse)
async def obtener_estado_pago(
    id_pago: str,
    repositorio: RepositorioPagosSQLAlchemy = Depends(get_repositorio_pagos)
):
    """
    Obtiene el estado actual de un pago
    """
    try:
        # Crear query
        query = ObtenerEstadoPagoQuery(id_pago=uuid.UUID(id_pago))
        
        # Ejecutar query
        handler = ObtenerEstadoPagoHandler(repositorio)
        resultado = handler.handle(query)
        
        if resultado.resultado is None:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        
        return EstadoPagoResponse(**resultado.resultado)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de pago inválido")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.patch("/{id_pago}/revertir", response_model=RevertirPagoResponse)
async def revertir_pago(
    id_pago: str,
    request: RevertirPagoRequest,
    repositorio: RepositorioPagosSQLAlchemy = Depends(get_repositorio_pagos)
):
    """Revertir un pago (compensación)"""
    try:
        comando = RevertirPagoCommand(
            id_pago=uuid.UUID(id_pago),
            motivo=request.motivo,
            saga_id=request.saga_id
        )
        
        handler = RevertirPagoHandler(repositorio)
        pago = handler.handle(comando)
        
        return RevertirPagoResponse(
            id_pago=str(pago.id),
            estado=pago.estado.value,
            mensaje=f"Pago revertido: {request.motivo}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/cleanup")
async def limpiar_pagos(
    repositorio: RepositorioPagosSQLAlchemy = Depends(get_repositorio_pagos)
):
    """Limpiar todos los pagos (solo para pruebas)"""
    try:
        # Obtener todos los pagos
        pagos = repositorio.obtener_todos()
        total_pagos = len(pagos)
        
        # Eliminar todos los pagos
        for pago in pagos:
            repositorio.eliminar(pago)
        
        return {
            "mensaje": f"Se eliminaron {total_pagos} pagos",
            "total_eliminados": total_pagos,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando pagos: {str(e)}"
        )

@router.get("/outbox/estadisticas", response_model=OutboxStatsResponse)
async def obtener_estadisticas_outbox(
    outbox_processor: OutboxProcessor = Depends(get_outbox_processor)
):
    """
    Obtiene estadísticas del outbox
    """
    try:
        stats = outbox_processor.obtener_estadisticas()
        return OutboxStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")