import json
import os
import logging
from typing import List
from datetime import datetime
import uuid
from ....seedwork.infraestructura.db import SessionLocal
from ....seedwork.infraestructura.pulsar_producer import PulsarEventProducer
from .modelos import OutboxCampanasModel

logger = logging.getLogger(__name__)

class OutboxCampanasProcessor:
    """Procesador de eventos del outbox para campañas con integración a Apache Pulsar"""
    
    def __init__(self, pulsar_url: str = None):
        self.pulsar_url = pulsar_url or os.getenv("PULSAR_URL", "pulsar://localhost:6650")
        self.pulsar_producer = None
        
    def _get_pulsar_producer(self, topic: str) -> PulsarEventProducer:
        """Obtener o crear un productor de Pulsar para el topic específico"""
        if not self.pulsar_producer:
            self.pulsar_producer = PulsarEventProducer(self.pulsar_url, topic)
        return self.pulsar_producer
    
    def procesar_eventos_pendientes(self) -> int:
        """
        Procesa todos los eventos pendientes en el outbox de campañas
        Retorna el número de eventos procesados
        """
        db = SessionLocal()
        eventos_procesados = 0
        
        try:
            # Obtener eventos no procesados
            eventos_pendientes = db.query(OutboxCampanasModel).filter(
                OutboxCampanasModel.processed == False
            ).all()
            
            logger.info(f"Procesando {len(eventos_pendientes)} eventos pendientes del outbox de campañas")
            
            for evento in eventos_pendientes:
                try:
                    # Procesar el evento
                    self._procesar_evento(evento)
                    
                    # Marcar como procesado
                    evento.processed = True
                    evento.processed_at = datetime.now()
                    eventos_procesados += 1
                    
                    logger.info(f"Evento {evento.id} procesado exitosamente")
                    
                except Exception as e:
                    logger.error(f"Error procesando evento {evento.id}: {str(e)}")
                    # En un escenario real, podrías implementar retry logic aquí
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error en el procesamiento del outbox de campañas: {str(e)}")
        finally:
            db.close()
        
        if eventos_procesados > 0:
            logger.info(f"Se procesaron {eventos_procesados} eventos del outbox de campañas")
        
        return eventos_procesados
    
    def _procesar_evento(self, evento: OutboxCampanasModel):
        """
        Procesa un evento individual y lo publica a Pulsar
        """
        try:
            # Obtener el productor para el topic específico
            producer = self._get_pulsar_producer(evento.topic)
            
            # Preparar los datos del evento
            event_data = evento.event_data
            event_id = str(evento.id)
            
            # Publicar evento a Pulsar
            producer.publish_event(
                event_type=evento.event_type,
                event_data=event_data,
                event_id=event_id
            )
            
            logger.info(f"📤 Evento publicado a Pulsar: {evento.event_type} -> {evento.topic} (ID: {event_id})")
            
        except Exception as e:
            logger.error(f"Error publicando evento {evento.id} a Pulsar: {str(e)}")
            raise
    
    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas del outbox de campañas"""
        db = SessionLocal()
        try:
            total_eventos = db.query(OutboxCampanasModel).count()
            eventos_pendientes = db.query(OutboxCampanasModel).filter(
                OutboxCampanasModel.processed == False
            ).count()
            eventos_procesados = total_eventos - eventos_pendientes
            
            # Estadísticas por tipo de evento
            tipos_eventos = db.query(
                OutboxCampanasModel.event_type,
                db.func.count(OutboxCampanasModel.id).label('count')
            ).group_by(OutboxCampanasModel.event_type).all()
            
            distribucion_tipos = {tipo: count for tipo, count in tipos_eventos}
            
            return {
                "total_eventos": total_eventos,
                "eventos_procesados": eventos_procesados,
                "eventos_pendientes": eventos_pendientes,
                "distribucion_por_tipo": distribucion_tipos
            }
        finally:
            db.close()
    
    def close(self):
        """Cierra la conexión con Pulsar"""
        if self.pulsar_producer:
            self.pulsar_producer.close()
            self.pulsar_producer = None
