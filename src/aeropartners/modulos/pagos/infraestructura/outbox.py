import json
import os
import logging
from typing import List
from datetime import datetime
from ....seedwork.infraestructura.db import SessionLocal
from ....seedwork.infraestructura.pulsar_producer import PulsarEventProducer
from .modelos import OutboxModel

logger = logging.getLogger(__name__)

class OutboxProcessor:
    """Procesador de eventos del outbox (versión simple sin Pulsar)"""
    
    def procesar_eventos_pendientes(self) -> int:
        """
        Procesa todos los eventos pendientes en el outbox
        Retorna el número de eventos procesados
        """
        db = SessionLocal()
        eventos_procesados = 0
        
        try:
            # Obtener eventos no procesados
            eventos_pendientes = db.query(OutboxModel).filter(
                OutboxModel.procesado == False
            ).all()
            
            for evento in eventos_pendientes:
                try:
                    # Procesar el evento (en este caso, solo imprimirlo)
                    self._procesar_evento(evento)
                    
                    # Marcar como procesado
                    evento.procesado = True
                    evento.fecha_procesamiento = datetime.now()
                    eventos_procesados += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando evento {evento.id}: {str(e)}")
                    # En un escenario real, podrías implementar retry logic aquí
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error en el procesamiento del outbox: {str(e)}")
        finally:
            db.close()
        
        return eventos_procesados
    
    def _procesar_evento(self, evento: OutboxModel):
        """
        Procesa un evento individual
        En un escenario real, aquí se publicaría al bus de mensajes
        """
        datos = json.loads(evento.datos_evento)
        
        logger.info(f"📤 Publicando evento: {evento.tipo_evento}")
        logger.info(f"   ID: {evento.id}")
        logger.info(f"   Datos: {json.dumps(datos, indent=2)}")
        logger.info(f"   Fecha: {evento.fecha_creacion}")
        
    
    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas del outbox"""
        db = SessionLocal()
        try:
            total_eventos = db.query(OutboxModel).count()
            eventos_pendientes = db.query(OutboxModel).filter(
                OutboxModel.procesado == False
            ).count()
            eventos_procesados = total_eventos - eventos_pendientes
            
            return {
                "total_eventos": total_eventos,
                "eventos_procesados": eventos_procesados,
                "eventos_pendientes": eventos_pendientes
            }
        finally:
            db.close()


class PulsarOutboxProcessor(OutboxProcessor):
    """Procesador de eventos del outbox con integración a Apache Pulsar"""
    
    def __init__(self, pulsar_url: str = None, topic: str = "pagos-events"):
        super().__init__()
        self.pulsar_producer = PulsarEventProducer(pulsar_url, topic)
    
    def _procesar_evento(self, evento: OutboxModel):
        """
        Procesa un evento individual y lo publica a Pulsar
        """
        try:
            datos = json.loads(evento.datos_evento)
            
            # Publicar evento a Pulsar
            self.pulsar_producer.publish_event(
                event_type=evento.tipo_evento,
                event_data=datos,
                event_id=str(evento.id)
            )
            
            logger.info(f"Evento publicado a Pulsar: {evento.tipo_evento} - {evento.id}")
            
        except Exception as e:
            logger.error(f"Error publicando evento a Pulsar {evento.id}: {str(e)}")
            raise
    
    def close(self):
        """Cierra la conexión con Pulsar"""
        if self.pulsar_producer:
            self.pulsar_producer.close()
