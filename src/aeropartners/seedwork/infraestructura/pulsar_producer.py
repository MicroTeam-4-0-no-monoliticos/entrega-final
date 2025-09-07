"""Productor de eventos para Apache Pulsar"""

import os
import json
import logging
from typing import Dict, Any
from pulsar import Client, Producer

logger = logging.getLogger(__name__)

class PulsarEventProducer:
    """Productor de eventos para Apache Pulsar"""
    
    def __init__(self, pulsar_url: str = None, topic: str = "pagos-events"):
        self.pulsar_url = pulsar_url or os.getenv("PULSAR_URL", "pulsar://localhost:6650")
        self.topic = topic
        self.client = None
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Establece conexión con Pulsar"""
        try:
            self.client = Client(self.pulsar_url)
            self.producer = self.client.create_producer(
                self.topic,
                send_timeout_millis=30000,
                batching_enabled=True,
                batching_max_messages=100,
                batching_max_publish_delay_ms=10
            )
            logger.info(f"Conectado a Pulsar en {self.pulsar_url}, topic: {self.topic}")
        except Exception as e:
            logger.error(f"Error conectando a Pulsar: {e}")
            raise
    
    def publish_event(self, event_type: str, event_data: Dict[str, Any], event_id: str = None):
        """
        Publica un evento en Pulsar
        
        Args:
            event_type: Tipo del evento (ej: PagoExitoso, PagoFallido)
            event_data: Datos del evento
            event_id: ID único del evento (opcional)
        """
        try:
            # Crear mensaje con metadatos
            message = {
                "event_type": event_type,
                "event_id": event_id,
                "timestamp": event_data.get("fecha_evento"),
                "data": event_data
            }
            
            # Serializar mensaje
            message_json = json.dumps(message, default=str)
            
            # Publicar mensaje
            self.producer.send(
                message_json.encode('utf-8'),
                properties={
                    "event_type": event_type,
                    "event_id": event_id or "",
                    "source": "aeropartners-pagos"
                }
            )
            
            logger.info(f"Evento publicado: {event_type} - {event_id}")
            
        except Exception as e:
            logger.error(f"Error publicando evento {event_type}: {e}")
            raise
    
    def close(self):
        """Cierra la conexión con Pulsar"""
        try:
            if self.producer:
                self.producer.close()
            if self.client:
                self.client.close()
            logger.info("Conexión con Pulsar cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión con Pulsar: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
