from typing import List, Optional
import uuid
import json
import logging
from sqlalchemy.orm import Session
from ....seedwork.infraestructura.db import SessionLocal
from ..dominio.entidades import Campana
from ..dominio.repositorios import RepositorioCampanas
from .modelos import CampanaModel, OutboxCampanasModel
from .mapeadores import MapeadorCampana

logger = logging.getLogger(__name__)

class RepositorioCampanasSQLAlchemy(RepositorioCampanas):
    """Implementación del repositorio de campañas usando SQLAlchemy"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session or SessionLocal()
        self._debe_cerrar_sesion = db_session is None
    
    def __del__(self):
        if self._debe_cerrar_sesion and self.db_session:
            self.db_session.close()
    
    def agregar(self, campana: Campana) -> None:
        """Agregar una nueva campaña"""
        try:
            # Convertir entidad a modelo
            modelo = MapeadorCampana.entidad_a_modelo(campana)
            
            # Agregar a la sesión
            self.db_session.add(modelo)
            
            # Procesar eventos de dominio (patrón Outbox)
            self._procesar_eventos_dominio(campana)
            
            # Confirmar transacción
            self.db_session.commit()
            
            # Limpiar eventos después de procesarlos
            campana.limpiar_eventos()
            
            logger.info(f"Campaña {campana.id} agregada exitosamente")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error agregando campaña {campana.id}: {str(e)}")
            raise
    
    def actualizar(self, campana: Campana) -> None:
        """Actualizar una campaña existente"""
        try:
            # Buscar el modelo existente
            modelo = self.db_session.query(CampanaModel).filter(
                CampanaModel.id == campana.id
            ).first()
            
            if not modelo:
                raise ValueError(f"Campaña con ID {campana.id} no encontrada")
            
            # Actualizar el modelo con los datos de la entidad
            MapeadorCampana.actualizar_modelo_desde_entidad(modelo, campana)
            
            # Procesar eventos de dominio (patrón Outbox)
            self._procesar_eventos_dominio(campana)
            
            # Confirmar transacción
            self.db_session.commit()
            
            # Limpiar eventos después de procesarlos
            campana.limpiar_eventos()
            
            logger.info(f"Campaña {campana.id} actualizada exitosamente")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error actualizando campaña {campana.id}: {str(e)}")
            raise
    
    def obtener_por_id(self, id_campana: uuid.UUID) -> Optional[Campana]:
        """Obtener una campaña por su ID"""
        try:
            modelo = self.db_session.query(CampanaModel).filter(
                CampanaModel.id == id_campana
            ).first()
            
            if not modelo:
                return None
            
            return MapeadorCampana.modelo_a_entidad(modelo)
            
        except Exception as e:
            logger.error(f"Error obteniendo campaña {id_campana}: {str(e)}")
            raise
    
    def obtener_por_afiliado(self, id_afiliado: str, limit: int = 50, offset: int = 0) -> List[Campana]:
        """Obtener campañas de un afiliado específico"""
        try:
            modelos = self.db_session.query(CampanaModel).filter(
                CampanaModel.id_afiliado == id_afiliado
            ).offset(offset).limit(limit).all()
            
            return [MapeadorCampana.modelo_a_entidad(modelo) for modelo in modelos]
            
        except Exception as e:
            logger.error(f"Error obteniendo campañas del afiliado {id_afiliado}: {str(e)}")
            raise
    
    def listar(self, limit: int = 50, offset: int = 0) -> List[Campana]:
        """Listar todas las campañas con paginación"""
        try:
            modelos = self.db_session.query(CampanaModel).offset(offset).limit(limit).all()
            return [MapeadorCampana.modelo_a_entidad(modelo) for modelo in modelos]
            
        except Exception as e:
            logger.error(f"Error listando campañas: {str(e)}")
            raise
    
    def eliminar(self, id_campana: uuid.UUID) -> bool:
        """Eliminar una campaña por su ID"""
        try:
            modelo = self.db_session.query(CampanaModel).filter(
                CampanaModel.id == id_campana
            ).first()
            
            if not modelo:
                return False
            
            self.db_session.delete(modelo)
            self.db_session.commit()
            
            logger.info(f"Campaña {id_campana} eliminada exitosamente")
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error eliminando campaña {id_campana}: {str(e)}")
            raise
    
    def obtener_todas(self) -> List[Campana]:
        """Obtener todas las campañas"""
        try:
            modelos = self.db_session.query(CampanaModel).all()
            return [MapeadorCampana.modelo_a_entidad(modelo) for modelo in modelos]
        except Exception as e:
            logger.error(f"Error obteniendo todas las campañas: {str(e)}")
            raise
    
    def _procesar_eventos_dominio(self, campana: Campana):
        """Procesar eventos de dominio usando el patrón Outbox"""
        for evento in campana.eventos:
            # Determinar el topic basado en el tipo de evento
            topic = self._obtener_topic_para_evento(type(evento).__name__)
            
            # Crear entrada en el outbox
            outbox_entry = OutboxCampanasModel(
                event_type=type(evento).__name__,
                event_data=self._serializar_evento(evento),
                topic=topic
            )
            
            self.db_session.add(outbox_entry)
            
            logger.debug(f"Evento {type(evento).__name__} agregado al outbox para topic {topic}")
    
    def _obtener_topic_para_evento(self, tipo_evento: str) -> str:
        """Determinar el topic de Pulsar basado en el tipo de evento"""
        mapping = {
            'CampanaCreada': 'campaigns.evt.created',
            'CampanaActualizada': 'campaigns.evt.updated',
            'CampanaActivada': 'campaigns.evt.activated',
            'PresupuestoCampanaActualizado': 'campaigns.evt.budget_updated',
            'MetricasCampanaActualizadas': 'campaigns.evt.metrics_updated'
        }
        return mapping.get(tipo_evento, 'campaigns.evt.generic')
    
    def _serializar_evento(self, evento) -> dict:
        """Serializar un evento de dominio a diccionario"""
        evento_dict = {
            'event_id': str(evento.id),
            'event_type': type(evento).__name__,
            'timestamp': evento.fecha_evento.isoformat(),
            'data': {}
        }
        
        # Copiar todos los atributos del evento (excepto los metadatos)
        for key, value in evento.__dict__.items():
            if not key.startswith('_') and key not in ['id', 'fecha_evento']:
                if hasattr(value, 'isoformat'):  # datetime
                    evento_dict['data'][key] = value.isoformat()
                elif hasattr(value, '__str__'):  # otros objetos
                    evento_dict['data'][key] = str(value)
                else:
                    evento_dict['data'][key] = value
        
        return evento_dict
