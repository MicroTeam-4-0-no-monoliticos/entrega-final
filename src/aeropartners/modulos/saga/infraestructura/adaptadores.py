import json
import uuid
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)
from ....seedwork.infraestructura.db import SessionLocal
from ..dominio.entidades import Saga, EstadoSaga, TipoPaso, Paso
from ..dominio.repositorios import RepositorioSaga
from .modelos import SagaLogModel, SagaPasoModel, SagaCompensacionModel

class RepositorioSagaSQLAlchemy(RepositorioSaga):
    """Implementación del repositorio de SAGAs usando SQLAlchemy"""
    
    def agregar(self, saga: Saga) -> Saga:
        db = SessionLocal()
        try:
            print(f"DEBUG: saga.id = {saga.id}")
            print(f"DEBUG: saga._id = {getattr(saga, '_id', 'NO EXISTE')}")
            # Crear modelo de SAGA Log
            saga_model = SagaLogModel(
                id=uuid.UUID(str(saga.id)),
                tipo=saga.tipo,
                estado=saga.estado.value,
                pasos=self._serializar_pasos(saga.pasos),
                compensaciones=self._serializar_compensaciones(saga.compensaciones),
                datos_iniciales=saga.datos_iniciales,
                fecha_inicio=saga.fecha_inicio,
                fecha_fin=saga.fecha_fin,
                error_message=saga.error_message
            )
            db.add(saga_model)
            
            # Crear modelos de pasos
            for paso in saga.pasos:
                paso_model = SagaPasoModel(
                    id=uuid.UUID(paso.id),
                    saga_id=uuid.UUID(str(saga.id)),
                    tipo_paso=paso.tipo.value,
                    datos=paso.datos,
                    resultado=paso.resultado,
                    compensacion=paso.compensacion,
                    exitoso=paso.exitoso,
                    error=paso.error,
                    fecha_ejecucion=paso.fecha_ejecucion
                )
                db.add(paso_model)
            
            # Crear modelos de compensaciones
            for compensacion in saga.compensaciones:
                compensacion_model = SagaCompensacionModel(
                    id=uuid.UUID(compensacion.id),
                    saga_id=uuid.UUID(str(saga.id)),
                    paso_id=uuid.UUID(compensacion.id),  # ID del paso que se compensa
                    tipo_compensacion=compensacion.tipo.value,
                    datos=compensacion.datos,
                    resultado=compensacion.resultado,
                    exitoso=compensacion.exitoso,
                    error=compensacion.error,
                    fecha_ejecucion=compensacion.fecha_ejecucion
                )
                db.add(compensacion_model)
            
            db.commit()
            return saga
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def obtener_por_id(self, saga_id: str) -> Optional[Saga]:
        db = SessionLocal()
        try:
            saga_model = db.query(SagaLogModel).filter(
                SagaLogModel.id == uuid.UUID(saga_id)
            ).first()
            
            if not saga_model:
                return None
            
            # Obtener pasos
            pasos_models = db.query(SagaPasoModel).filter(
                SagaPasoModel.saga_id == uuid.UUID(saga_id)
            ).all()
            
            # Obtener compensaciones
            compensaciones_models = db.query(SagaCompensacionModel).filter(
                SagaCompensacionModel.saga_id == uuid.UUID(saga_id)
            ).all()
            
            # Reconstruir SAGA
            saga = self._reconstruir_saga(saga_model, pasos_models, compensaciones_models)
            return saga
            
        finally:
            db.close()
    
    def actualizar(self, saga: Saga) -> Saga:
        db = SessionLocal()
        try:
            # Actualizar modelo principal
            saga_model = db.query(SagaLogModel).filter(
                SagaLogModel.id == uuid.UUID(str(saga.id))
            ).first()
            
            if saga_model:
                saga_model.estado = saga.estado.value
                saga_model.pasos = self._serializar_pasos(saga.pasos)
                saga_model.compensaciones = self._serializar_compensaciones(saga.compensaciones)
                saga_model.fecha_fin = saga.fecha_fin
                saga_model.error_message = saga.error_message
                saga_model.updated_at = datetime.now()
            
            # Actualizar pasos
            db.query(SagaPasoModel).filter(
                SagaPasoModel.saga_id == uuid.UUID(str(saga.id))
            ).delete()
            
            for paso in saga.pasos:
                paso_model = SagaPasoModel(
                    id=uuid.UUID(paso.id),
                    saga_id=uuid.UUID(str(saga.id)),
                    tipo_paso=paso.tipo.value,
                    datos=paso.datos,
                    resultado=paso.resultado,
                    compensacion=paso.compensacion,
                    exitoso=paso.exitoso,
                    error=paso.error,
                    fecha_ejecucion=paso.fecha_ejecucion
                )
                db.add(paso_model)
            
            # Actualizar compensaciones
            db.query(SagaCompensacionModel).filter(
                SagaCompensacionModel.saga_id == uuid.UUID(str(saga.id))
            ).delete()
            
            for compensacion in saga.compensaciones:
                compensacion_model = SagaCompensacionModel(
                    id=uuid.UUID(compensacion.id),
                    saga_id=uuid.UUID(str(saga.id)),
                    paso_id=uuid.UUID(compensacion.id),
                    tipo_compensacion=compensacion.tipo.value,
                    datos=compensacion.datos,
                    resultado=compensacion.resultado,
                    exitoso=compensacion.exitoso,
                    error=compensacion.error,
                    fecha_ejecucion=compensacion.fecha_ejecucion
                )
                db.add(compensacion_model)
            
            db.commit()
            return saga
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def eliminar(self, saga_id: str) -> bool:
        db = SessionLocal()
        try:
            # Convertir saga_id a UUID si es necesario
            saga_uuid = saga_id if isinstance(saga_id, uuid.UUID) else uuid.UUID(saga_id)
            
            # Eliminar en cascada
            db.query(SagaPasoModel).filter(
                SagaPasoModel.saga_id == saga_uuid
            ).delete()
            
            db.query(SagaCompensacionModel).filter(
                SagaCompensacionModel.saga_id == saga_uuid
            ).delete()
            
            result = db.query(SagaLogModel).filter(
                SagaLogModel.id == saga_uuid
            ).delete()
            
            db.commit()
            return result > 0
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def obtener_por_estado(self, estado: str) -> List[Saga]:
        db = SessionLocal()
        try:
            sagas_models = db.query(SagaLogModel).filter(
                SagaLogModel.estado == estado
            ).all()
            
            sagas = []
            for saga_model in sagas_models:
                pasos_models = db.query(SagaPasoModel).filter(
                    SagaPasoModel.saga_id == saga_model.id
                ).all()
                
                compensaciones_models = db.query(SagaCompensacionModel).filter(
                    SagaCompensacionModel.saga_id == saga_model.id
                ).all()
                
                saga = self._reconstruir_saga(saga_model, pasos_models, compensaciones_models)
                sagas.append(saga)
            
            return sagas
            
        finally:
            db.close()
    
    def obtener_pendientes(self) -> List[Saga]:
        """Obtener SAGAs que no están completadas ni fallidas"""
        db = SessionLocal()
        try:
            sagas_models = db.query(SagaLogModel).filter(
                SagaLogModel.estado.in_([
                    EstadoSaga.INICIADA.value,
                    EstadoSaga.CAMPAÑA_CREADA.value,
                    EstadoSaga.PAGO_PROCESADO.value,
                    EstadoSaga.REPORTE_GENERADO.value,
                    EstadoSaga.COMPENSANDO.value
                ])
            ).all()
            
            sagas = []
            for saga_model in sagas_models:
                pasos_models = db.query(SagaPasoModel).filter(
                    SagaPasoModel.saga_id == saga_model.id
                ).all()
                
                compensaciones_models = db.query(SagaCompensacionModel).filter(
                    SagaCompensacionModel.saga_id == saga_model.id
                ).all()
                
                saga = self._reconstruir_saga(saga_model, pasos_models, compensaciones_models)
                sagas.append(saga)
            
            return sagas
            
        finally:
            db.close()
    
    def obtener_por_tipo(self, tipo: str) -> List[Saga]:
        db = SessionLocal()
        try:
            sagas_models = db.query(SagaLogModel).filter(
                SagaLogModel.tipo == tipo
            ).all()
            
            sagas = []
            for saga_model in sagas_models:
                pasos_models = db.query(SagaPasoModel).filter(
                    SagaPasoModel.saga_id == saga_model.id
                ).all()
                
                compensaciones_models = db.query(SagaCompensacionModel).filter(
                    SagaCompensacionModel.saga_id == saga_model.id
                ).all()
                
                saga = self._reconstruir_saga(saga_model, pasos_models, compensaciones_models)
                sagas.append(saga)
            
            return sagas
            
        finally:
            db.close()
    
    def obtener_por_rango_fechas(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Saga]:
        db = SessionLocal()
        try:
            sagas_models = db.query(SagaLogModel).filter(
                SagaLogModel.fecha_inicio >= fecha_inicio,
                SagaLogModel.fecha_inicio <= fecha_fin
            ).all()
            
            sagas = []
            for saga_model in sagas_models:
                pasos_models = db.query(SagaPasoModel).filter(
                    SagaPasoModel.saga_id == saga_model.id
                ).all()
                
                compensaciones_models = db.query(SagaCompensacionModel).filter(
                    SagaCompensacionModel.saga_id == saga_model.id
                ).all()
                
                saga = self._reconstruir_saga(saga_model, pasos_models, compensaciones_models)
                sagas.append(saga)
            
            return sagas
            
        finally:
            db.close()
    
    def _serializar_pasos(self, pasos: List[Paso]) -> List[dict]:
        return [
            {
                "id": paso.id,
                "tipo": paso.tipo.value,
                "datos": paso.datos,
                "resultado": paso.resultado,
                "compensacion": paso.compensacion,
                "exitoso": paso.exitoso,
                "error": paso.error,
                "fecha_ejecucion": paso.fecha_ejecucion.isoformat()
            }
            for paso in pasos
        ]
    
    def _serializar_compensaciones(self, compensaciones: List[Paso]) -> List[dict]:
        return [
            {
                "id": comp.id,
                "tipo": comp.tipo.value,
                "datos": comp.datos,
                "resultado": comp.resultado,
                "exitoso": comp.exitoso,
                "error": comp.error,
                "fecha_ejecucion": comp.fecha_ejecucion.isoformat()
            }
            for comp in compensaciones
        ]
    
    def _reconstruir_saga(self, saga_model: SagaLogModel, 
                         pasos_models: List[SagaPasoModel], 
                         compensaciones_models: List[SagaCompensacionModel]) -> Saga:
        # Crear SAGA
        saga = Saga(saga_model.tipo, saga_model.datos_iniciales or {})
        saga.id = saga_model.id  # Usar la propiedad id directamente
        saga.estado = EstadoSaga(saga_model.estado)
        saga.fecha_inicio = saga_model.fecha_inicio
        saga.fecha_fin = saga_model.fecha_fin
        saga.error_message = saga_model.error_message
        
        # Reconstruir pasos
        for paso_model in pasos_models:
            paso = Paso(
                tipo=TipoPaso(paso_model.tipo_paso),
                datos=paso_model.datos or {},
                resultado=paso_model.resultado,
                compensacion=paso_model.compensacion
            )
            paso.id = str(paso_model.id)
            paso.exitoso = paso_model.exitoso
            paso.error = paso_model.error
            paso.fecha_ejecucion = paso_model.fecha_ejecucion
            saga.pasos.append(paso)
        
        # Reconstruir compensaciones
        for comp_model in compensaciones_models:
            compensacion = Paso(
                tipo=TipoPaso(comp_model.tipo_compensacion),
                datos=comp_model.datos or {}
            )
            compensacion.id = str(comp_model.id)
            compensacion.exitoso = comp_model.exitoso
            compensacion.error = comp_model.error
            compensacion.fecha_ejecucion = comp_model.fecha_ejecucion
            saga.compensaciones.append(compensacion)
        
        return saga
    
    def obtener_todas(self) -> List[Saga]:
        """Obtener todas las SAGAs"""
        db = SessionLocal()
        try:
            sagas_models = db.query(SagaLogModel).order_by(SagaLogModel.fecha_inicio.desc()).all()
            sagas = []
            
            for saga_model in sagas_models:
                # Obtener pasos
                pasos_models = db.query(SagaPasoModel).filter(
                    SagaPasoModel.saga_id == saga_model.id
                ).all()
                
                # Obtener compensaciones
                compensaciones_models = db.query(SagaCompensacionModel).filter(
                    SagaCompensacionModel.saga_id == saga_model.id
                ).all()
                
                saga = self._reconstruir_saga(saga_model, pasos_models, compensaciones_models)
                sagas.append(saga)
            
            return sagas
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
