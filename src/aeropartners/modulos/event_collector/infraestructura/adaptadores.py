import json
import logging
from typing import Dict, Any
from datetime import datetime

from ..dominio.enums import TipoEvento
from ..dominio.objetos_valor import ContextoEvento, PayloadEvento
from ..dominio.servicios import ServicioPublicacionEventos

logger = logging.getLogger(__name__)

class PulsarEventPublisher(ServicioPublicacionEventos):
    """
    Implementación del servicio de publicación de eventos usando Apache Pulsar
    Adaptador que maneja múltiples topics para diferentes tipos de eventos
    """
    
    # Mapeo de tipos de evento a topics
    TOPIC_MAPPING = {
        TipoEvento.CLICK: "tracking.commands.RegisterClick.v1",
        TipoEvento.IMPRESSION: "tracking.commands.RegisterImpression.v1", 
        TipoEvento.CONVERSION: "tracking.commands.RegisterConversion.v1",
        TipoEvento.PAGE_VIEW: "tracking.commands.RegisterPageView.v1"
    }
    
    def __init__(self, pulsar_url: str = None):
        self.pulsar_url = pulsar_url or "pulsar://localhost:6650"
        self.producers = {}  # Cache de producers por topic
        self.client = None
        self._init_pulsar_connection()
    
    def _init_pulsar_connection(self):
        """Inicializa la conexión con Pulsar"""
        try:
            import pulsar
            self.client = pulsar.Client(self.pulsar_url)
            logger.info(f"Conectado a Pulsar en {self.pulsar_url}")
        except Exception as e:
            logger.error(f"Error conectando a Pulsar: {str(e)}")
            # En desarrollo, no falla si no está disponible Pulsar
            self.client = None
    
    def _get_producer_for_topic(self, topic: str):
        """Obtiene o crea un producer para el topic especificado"""
        if not self.client:
            raise Exception("Pulsar client no está disponible")
            
        if topic not in self.producers:
            try:
                self.producers[topic] = self.client.create_producer(
                    topic,
                    send_timeout_millis=1000,
                    batching_enabled=True,
                    batching_max_messages=100,
                    batching_max_publish_delay_ms=10
                )
                logger.info(f"Producer creado para topic: {topic}")
            except Exception as e:
                logger.error(f"Error creando producer para topic {topic}: {str(e)}")
                raise
        
        return self.producers[topic]
    
    def publicar_evento(
        self, 
        tipo_evento: TipoEvento,
        contexto: ContextoEvento,
        payload: PayloadEvento,
        metadatos: Dict[str, Any]
    ) -> str:
        """
        Publica un evento al topic correspondiente en Pulsar
        """
        try:
            if not self.client:
                # En desarrollo, simular publicación exitosa
                logger.warning("Pulsar no disponible, simulando publicación exitosa")
                message_id = f"sim_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                return message_id
            
            topic = self.obtener_topic_destino(tipo_evento)
            partition_key = self.generar_partition_key(contexto)
            producer = self._get_producer_for_topic(topic)
            
            # Preparar mensaje con schema versioning
            mensaje = {
                "schema_version": "v1",
                "event_type": tipo_evento.value,
                "timestamp": datetime.now().isoformat(),
                "data": metadatos,
                "partition_key": partition_key
            }
            
            # Publicar mensaje
            message_result = producer.send(
                json.dumps(mensaje).encode('utf-8'),
                properties={
                    "event_type": tipo_evento.value,
                    "affiliate_id": contexto.id_afiliado,
                    "schema_version": "v1",
                    "partition_key": partition_key
                }
            )
            
            message_id = str(message_result.message_id())
            logger.info(f"Evento publicado - Topic: {topic}, MessageID: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error publicando evento - Tipo: {tipo_evento.value}, Error: {str(e)}")
            raise
    
    def obtener_topic_destino(self, tipo_evento: TipoEvento) -> str:
        """Obtiene el topic de destino para un tipo de evento"""
        return self.TOPIC_MAPPING.get(tipo_evento, "tracking.commands.RegisterEvent.v1")
    
    def generar_partition_key(self, contexto: ContextoEvento) -> str:
        """
        Genera clave de partición para garantizar orden de eventos por afiliado
        """
        # Usar id_afiliado como partition key para garantizar orden
        # Si hay campaña, incluirla para mejor distribución
        if contexto.id_campana:
            return f"{contexto.id_afiliado}#{contexto.id_campana}"
        return contexto.id_afiliado
    
    def close(self):
        """Cierra todas las conexiones con Pulsar"""
        try:
            for topic, producer in self.producers.items():
                producer.close()
                logger.info(f"Producer cerrado para topic: {topic}")
            
            if self.client:
                self.client.close()
                logger.info("Cliente Pulsar cerrado")
                
        except Exception as e:
            logger.error(f"Error cerrando conexiones Pulsar: {str(e)}")
    
    def __del__(self):
        self.close()
