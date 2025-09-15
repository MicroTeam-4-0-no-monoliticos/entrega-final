import os
import json
import logging
import uuid
import time
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal

import pulsar
from pulsar import ConsumerType

from ....seedwork.infraestructura.db import SessionLocal
from .modelos import EventInboxModel
from .adaptadores import RepositorioCampanasSQLAlchemy
from ..aplicacion.comandos import ActualizarMetricasCampanaCommand
from ..aplicacion.handlers import ActualizarMetricasCampanaHandler

logger = logging.getLogger(__name__)

class PulsarCampanasConsumer:
    """Consumer de Pulsar para eventos de campañas con FAILOVER subscription"""
    
    def __init__(
        self,
        pulsar_url: str = None,
        subscription_name: str = "campaigns-failover",
        subscription_type: ConsumerType = ConsumerType.Failover,
        dlq_topic: str = "campaigns.DLQ"
    ):
        self.pulsar_url = pulsar_url or os.getenv("PULSAR_URL", "pulsar://localhost:6650")
        self.subscription_name = subscription_name
        self.subscription_type = subscription_type
        self.dlq_topic = dlq_topic
        
        # Configuración de reintentos y DLQ
        self.max_redeliver_count = int(os.getenv("MAX_REDELIVER_COUNT", "3"))
        self.ack_timeout_millis = int(os.getenv("ACK_TIMEOUT_MILLIS", "30000"))  # 30 segundos
        self.negative_ack_redelivery_delay_millis = int(os.getenv("NEGATIVE_ACK_REDELIVERY_DELAY_MILLIS", "5000"))  # 5 segundos
        
        self.client = None
        self.consumer = None
        self.service_name = os.getenv("SERVICE_NAME", "campaigns-svc")
        
        logger.info(f"Inicializando PulsarCampanasConsumer para servicio: {self.service_name}")
    
    def start_consuming(self):
        """Iniciar el consumo de eventos de Pulsar"""
        try:
            # Crear cliente de Pulsar
            self.client = pulsar.Client(self.pulsar_url)
            
            # Configurar Dead Letter Policy
            dlq_policy = pulsar.ConsumerDeadLetterPolicy(
                max_redeliver_count=self.max_redeliver_count,
                dead_letter_topic=self.dlq_topic
            )
            
            # Crear consumer con FAILOVER subscription
            self.consumer = self.client.subscribe(
                topic="payments.evt.completed",
                subscription_name=self.subscription_name,
                consumer_type=self.subscription_type,
                consumer_name=f"{self.service_name}-consumer-{uuid.uuid4().hex[:8]}",
                ack_timeout_millis=self.ack_timeout_millis,
                negative_ack_redelivery_delay_millis=self.negative_ack_redelivery_delay_millis,
                dead_letter_policy=dlq_policy,
                initial_position=pulsar.InitialPosition.Earliest
            )
            
            logger.info(f"🔥 Consumer iniciado con FAILOVER subscription: {self.subscription_name}")
            logger.info(f"📡 Escuchando topic: payments.evt.completed")
            logger.info(f"💀 DLQ configurado: {self.dlq_topic}")
            logger.info(f"🔄 Max reintentos: {self.max_redeliver_count}")
            
            # Bucle principal de consumo
            while True:
                try:
                    msg = self.consumer.receive()
                    self._process_message(msg)
                    
                except KeyboardInterrupt:
                    logger.info("Deteniendo consumer por interrupción del usuario")
                    break
                except Exception as e:
                    logger.error(f"Error en el bucle principal de consumo: {str(e)}")
                    time.sleep(5)  # Esperar antes de reintentar
                    
        except Exception as e:
            logger.error(f"Error inicializando consumer: {str(e)}")
            raise
        finally:
            self._cleanup()
    
    def _process_message(self, msg):
        """Procesar un mensaje individual de Pulsar"""
        correlation_id = str(uuid.uuid4())
        event_id = None
        
        try:
            # Parsear el mensaje
            message_data = json.loads(msg.data().decode('utf-8'))
            event_id = message_data.get('event_id', str(uuid.uuid4()))
            event_type = message_data.get('event_type', 'unknown')
            
            logger.info(f"service={self.service_name} corrId={correlation_id} eventId={event_id} action=received eventType={event_type}")
            
            # Verificar idempotencia
            if self._is_event_already_processed(event_id):
                logger.info(f"service={self.service_name} corrId={correlation_id} eventId={event_id} action=skipped reason=already_processed")
                self.consumer.acknowledge(msg)
                return
            
            # Procesar el evento según su tipo
            processed = False
            if event_type == "PagoExitoso":
                processed = self._process_payment_completed_event(message_data, correlation_id)
            else:
                logger.warning(f"service={self.service_name} corrId={correlation_id} eventId={event_id} action=ignored reason=unknown_event_type")
                processed = True  # Ignorar eventos desconocidos
            
            if processed:
                # Marcar como procesado en el inbox
                self._mark_event_as_processed(event_id, event_type, message_data)
                
                # Acknowledge del mensaje
                self.consumer.acknowledge(msg)
                
                logger.info(f"service={self.service_name} corrId={correlation_id} eventId={event_id} action=processed ts={datetime.now().isoformat()}")
            else:
                # NACK del mensaje para reintento
                self.consumer.negative_acknowledge(msg)
                logger.warning(f"service={self.service_name} corrId={correlation_id} eventId={event_id} action=nacked reason=processing_failed")
                
        except json.JSONDecodeError as e:
            logger.error(f"service={self.service_name} corrId={correlation_id} eventId={event_id} action=dlq reason=invalid_json error={str(e)}")
            self.consumer.negative_acknowledge(msg)  # Enviará a DLQ después de max reintentos
            
        except Exception as e:
            logger.error(f"service={self.service_name} corrId={correlation_id} eventId={event_id} action=error error={str(e)}")
            self.consumer.negative_acknowledge(msg)
    
    def _is_event_already_processed(self, event_id: str) -> bool:
        """Verificar si un evento ya fue procesado (idempotencia)"""
        db = SessionLocal()
        try:
            existing = db.query(EventInboxModel).filter(
                EventInboxModel.event_id == uuid.UUID(event_id)
            ).first()
            return existing is not None
        except Exception as e:
            logger.error(f"Error verificando idempotencia para evento {event_id}: {str(e)}")
            return False
        finally:
            db.close()
    
    def _mark_event_as_processed(self, event_id: str, event_type: str, payload: Dict[str, Any]):
        """Marcar un evento como procesado en el inbox"""
        db = SessionLocal()
        try:
            inbox_entry = EventInboxModel(
                event_id=uuid.UUID(event_id),
                event_type=event_type,
                payload=payload,
                processed_at=datetime.now()
            )
            db.add(inbox_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error marcando evento {event_id} como procesado: {str(e)}")
            raise
        finally:
            db.close()
    
    def _process_payment_completed_event(self, event_data: Dict[str, Any], correlation_id: str) -> bool:
        """Procesar evento de pago completado"""
        try:
            # Extraer datos del evento
            payment_data = event_data.get('data', {})
            payment_id = payment_data.get('id_pago')
            affiliate_id = payment_data.get('id_afiliado')
            amount = payment_data.get('monto', 0)
            
            if not payment_id or not affiliate_id:
                logger.warning(f"Evento de pago incompleto: {event_data}")
                return True  # Considerar como procesado para evitar reintentos infinitos
            
            logger.info(f"Procesando pago completado: paymentId={payment_id} affiliateId={affiliate_id} amount={amount}")
            
            # Aquí podrías implementar lógica de negocio específica
            # Por ejemplo, actualizar métricas de campañas del afiliado
            self._update_campaign_metrics_for_affiliate(affiliate_id, Decimal(str(amount)))
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando evento de pago: {str(e)}")
            return False
    
    def _update_campaign_metrics_for_affiliate(self, affiliate_id: str, payment_amount: Decimal):
        """Actualizar métricas de campañas activas del afiliado"""
        try:
            repositorio = RepositorioCampanasSQLAlchemy()
            
            # Obtener campañas activas del afiliado
            campanas_activas = repositorio.obtener_por_afiliado(affiliate_id, limit=100)
            campanas_activas = [c for c in campanas_activas if c.estado.value == "ACTIVA"]
            
            if not campanas_activas:
                logger.info(f"No hay campañas activas para afiliado {affiliate_id}")
                return
            
            # Simular actualización de métricas (en un caso real, habría lógica más compleja)
            for campana in campanas_activas:
                try:
                    # Incrementar conversiones como ejemplo
                    comando = ActualizarMetricasCampanaCommand(
                        id_campana=campana.id,
                        conversiones=campana.metricas.conversiones + 1,
                        gasto_actual=campana.metricas.gasto_actual + (payment_amount * Decimal('0.1'))  # 10% del pago como gasto simulado
                    )
                    
                    handler = ActualizarMetricasCampanaHandler(repositorio)
                    handler.handle(comando)
                    
                    logger.info(f"Métricas actualizadas para campaña {campana.id}")
                    
                except Exception as e:
                    logger.error(f"Error actualizando métricas de campaña {campana.id}: {str(e)}")
                    # Continuar con otras campañas
                    
        except Exception as e:
            logger.error(f"Error actualizando métricas para afiliado {affiliate_id}: {str(e)}")
            raise
    
    def _cleanup(self):
        """Limpiar recursos"""
        try:
            if self.consumer:
                self.consumer.close()
                logger.info("Consumer cerrado")
            
            if self.client:
                self.client.close()
                logger.info("Cliente Pulsar cerrado")
                
        except Exception as e:
            logger.error(f"Error en cleanup: {str(e)}")

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y iniciar consumer
    consumer = PulsarCampanasConsumer()
    consumer.start_consuming()
