import os
import json
import logging
import signal
from typing import Dict, Any, Callable
from pulsar import Client, ConsumerType, InitialPosition, Message

logger = logging.getLogger(__name__)

class PulsarEventConsumer:
    """Consumidor de eventos de Apache Pulsar"""
    
    def __init__(self, pulsar_url: str = None, topic: str = "pagos-events", 
                 subscription_name: str = "aeropartners-consumer"):
        self.pulsar_url = pulsar_url or os.getenv("PULSAR_URL", "pulsar://pulsar:6650")
        self.topic = topic
        self.subscription_name = subscription_name
        self.client = None
        self.consumer = None
        self.running = False
        
        # Manejadores de eventos
        self.event_handlers: Dict[str, Callable] = {
            "PagoExitoso": self._handle_pago_exitoso,
            "PagoFallido": self._handle_pago_fallido
        }
        
        # Configurar manejo de señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de terminación"""
        logger.info(f"Recibida señal {signum}, iniciando shutdown...")
        self.stop_consuming()
    
    def _connect(self):
        """Establece conexión con Pulsar"""
        try:
            self.client = Client(self.pulsar_url)
            self.consumer = self.client.subscribe(
                self.topic,
                subscription_name=self.subscription_name,
                consumer_type=ConsumerType.Shared,
                initial_position=InitialPosition.Latest
            )
            logger.info(f"Conectado a Pulsar en {self.pulsar_url}, topic: {self.topic}")
        except Exception as e:
            logger.error(f"Error conectando a Pulsar: {e}")
            raise
    
    def start_consuming(self):
        """Inicia el consumo de eventos"""
        try:
            self._connect()
            self.running = True
            
            logger.info("🚀 Iniciando consumo de eventos de Pulsar...")
            
            while self.running:
                try:
                    # Recibir mensaje con timeout
                    msg = self.consumer.receive(timeout_millis=1000)
                    
                    if msg:
                        self._process_message(msg)
                        self.consumer.acknowledge(msg)
                        
                except Exception as e:
                    if self.running:  # Solo loggear si no estamos en shutdown
                        logger.error(f"Error procesando mensaje: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado recibida")
        except Exception as e:
            logger.error(f"Error en el consumidor: {e}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Detiene el consumo de eventos"""
        self.running = False
        
        try:
            if self.consumer:
                self.consumer.close()
            if self.client:
                self.client.close()
            logger.info("✅ Consumidor de Pulsar cerrado correctamente")
        except Exception as e:
            logger.error(f"Error cerrando consumidor: {e}")
    
    def _process_message(self, message: Message):
        """Procesa un mensaje recibido de Pulsar"""
        try:
            # Decodificar mensaje
            message_data = json.loads(message.data().decode('utf-8'))
            
            event_type = message_data.get("event_type")
            event_data = message_data.get("data", {})
            event_id = message_data.get("event_id")
            
            logger.info(f"📥 Evento recibido: {event_type} - {event_id}")
            
            # Procesar evento según su tipo
            if event_type in self.event_handlers:
                self.event_handlers[event_type](event_data)
            else:
                logger.warning(f"⚠️  Tipo de evento no manejado: {event_type}")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            raise
    
    def _handle_pago_exitoso(self, event_data: Dict[str, Any]):
        """Maneja eventos de pago exitoso"""
        logger.info("💰 Pago exitoso procesado:")
        logger.info(f"   ID Pago: {event_data.get('id_pago')}")
        logger.info(f"   Afiliado: {event_data.get('id_afiliado')}")
        logger.info(f"   Monto: {event_data.get('monto')} {event_data.get('moneda')}")
        logger.info(f"   Referencia: {event_data.get('referencia_pago')}")
        
        # Aquí podrías implementar lógica adicional como:
        # - Enviar notificaciones
        # - Actualizar dashboards
        # - Disparar otros procesos de negocio
        # - Integrar con sistemas externos
    
    def _handle_pago_fallido(self, event_data: Dict[str, Any]):
        """Maneja eventos de pago fallido"""
        logger.warning("❌ Pago fallido procesado:")
        logger.warning(f"   ID Pago: {event_data.get('id_pago')}")
        logger.warning(f"   Afiliado: {event_data.get('id_afiliado')}")
        logger.warning(f"   Monto: {event_data.get('monto')} {event_data.get('moneda')}")
        logger.warning(f"   Error: {event_data.get('mensaje_error')}")
        
        # Aquí podrías implementar lógica adicional como:
        # - Enviar alertas
        # - Programar reintentos
        # - Notificar al equipo de soporte
        # - Registrar en sistemas de monitoreo
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Agrega un manejador personalizado para un tipo de evento"""
        self.event_handlers[event_type] = handler
        logger.info(f"Manejador agregado para evento: {event_type}")
    
    def remove_event_handler(self, event_type: str):
        """Remueve un manejador de evento"""
        if event_type in self.event_handlers:
            del self.event_handlers[event_type]
            logger.info(f"Manejador removido para evento: {event_type}")


def main():
    """Función principal para ejecutar el consumidor"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y ejecutar consumidor
    consumer = PulsarEventConsumer()
    consumer.start_consuming()


if __name__ == "__main__":
    main()
