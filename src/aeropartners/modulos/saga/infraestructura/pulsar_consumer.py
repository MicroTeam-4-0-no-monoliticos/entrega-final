import os
import json
import logging
import uuid
import httpx
from typing import Dict, Any
from datetime import datetime
import pulsar
from pulsar import ConsumerType

from ....seedwork.infraestructura.db import SessionLocal
from ..dominio.repositorios import RepositorioSaga
from ..infraestructura.adaptadores import RepositorioSagaSQLAlchemy
from ..dominio.entidades import TipoPaso, EstadoSaga
from ..aplicacion.comandos import (
    MarcarPasoExitosoCommand, MarcarPasoFallidoCommand,
    IniciarCompensacionCommand, EjecutarCompensacionCommand,
    MarcarCompensacionExitosaCommand, MarcarCompensacionFallidaCommand
)
from ..aplicacion.handlers import (
    MarcarPasoExitosoHandler, MarcarPasoFallidoHandler,
    IniciarCompensacionHandler, EjecutarCompensacionHandler,
    MarcarCompensacionExitosaHandler, MarcarCompensacionFallidaHandler
)
from ....seedwork.infraestructura.pulsar_producer import PulsarEventProducer

logger = logging.getLogger(__name__)

class SagaPulsarConsumer:
    """Consumer de Pulsar para eventos de SAGA"""
    
    def __init__(
        self,
        pulsar_url: str = None,
        subscription_name: str = "saga-orchestrator",
        subscription_type: ConsumerType = ConsumerType.Failover
    ):
        self.pulsar_url = pulsar_url or os.getenv("PULSAR_URL", "pulsar://localhost:6650")
        self.subscription_name = subscription_name
        self.subscription_type = subscription_type
        
        # Repositorio y handlers
        self.repositorio: RepositorioSaga = RepositorioSagaSQLAlchemy()
        self.pulsar_producer = PulsarEventProducer(self.pulsar_url, "saga-events")
        
        # Handlers
        self.marcar_paso_exitoso_handler = MarcarPasoExitosoHandler(
            self.repositorio, self.pulsar_producer
        )
        self.marcar_paso_fallido_handler = MarcarPasoFallidoHandler(
            self.repositorio, self.pulsar_producer
        )
        self.iniciar_compensacion_handler = IniciarCompensacionHandler(
            self.repositorio, self.pulsar_producer
        )
        self.ejecutar_compensacion_handler = EjecutarCompensacionHandler(
            self.repositorio, self.pulsar_producer
        )
        self.marcar_compensacion_exitosa_handler = MarcarCompensacionExitosaHandler(
            self.repositorio, self.pulsar_producer
        )
        self.marcar_compensacion_fallida_handler = MarcarCompensacionFallidaHandler(
            self.repositorio, self.pulsar_producer
        )
        
        # Cliente HTTP para llamar a servicios
        self.http_client = httpx.Client(timeout=30.0)
        
        self.client = None
        self.consumer = None
        
        logger.info(f"Inicializando SagaPulsarConsumer")
    
    def start_consuming(self):
        """Iniciar el consumo de eventos de Pulsar"""
        try:
            # Crear cliente de Pulsar
            self.client = pulsar.Client(self.pulsar_url)
            
            # Crear consumer para saga-events
            self.consumer = self.client.subscribe(
                topic="saga-events",
                subscription_name=self.subscription_name,
                consumer_type=self.subscription_type,
                consumer_name=f"saga-orchestrator-{uuid.uuid4().hex[:8]}",
                initial_position=pulsar.InitialPosition.Earliest
            )
            
            # Crear consumer para pagos-events
            self.payment_consumer = self.client.subscribe(
                topic="pagos-events",
                subscription_name=f"{self.subscription_name}-payments",
                consumer_type=self.subscription_type,
                consumer_name=f"saga-orchestrator-payments-{uuid.uuid4().hex[:8]}",
                initial_position=pulsar.InitialPosition.Earliest
            )
            
            logger.info(f"🔥 SAGA Consumer iniciado: {self.subscription_name}")
            logger.info(f"📡 Escuchando topics: saga-events, pagos-events")
            
            # Bucle principal de consumo
            while True:
                try:
                    # Procesar mensajes de saga-events
                    try:
                        msg = self.consumer.receive(timeout_millis=1000)  # Timeout de 1 segundo
                        self._process_message(msg)
                    except pulsar.Timeout:
                        pass  # Timeout normal, continuar
                    
                    # Procesar mensajes de pagos-events
                    try:
                        msg = self.payment_consumer.receive(timeout_millis=1000)  # Timeout de 1 segundo
                        self._process_message(msg)
                    except pulsar.Timeout:
                        pass  # Timeout normal, continuar
                    
                except KeyboardInterrupt:
                    logger.info("Deteniendo SAGA consumer por interrupción del usuario")
                    break
                except Exception as e:
                    logger.error(f"Error en el bucle principal de SAGA: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error inicializando SAGA consumer: {str(e)}")
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
            
            logger.info(f"SAGA Consumer - corrId={correlation_id} eventId={event_id} eventType={event_type}")
            
            # Procesar según el tipo de evento
            if event_type == "SagaIniciada":
                self._handle_saga_iniciada(message_data, correlation_id)
            elif event_type == "SagaPasoEjecutado":
                self._handle_paso_ejecutado(message_data, correlation_id)
            elif event_type == "SagaCompensacionEjecutada":
                self._handle_compensacion_ejecutada(message_data, correlation_id)
            elif event_type == "PagoExitoso":
                self._handle_pago_exitoso(message_data, correlation_id)
            elif event_type == "PagoFallido":
                self._handle_pago_fallido(message_data, correlation_id)
            else:
                logger.warning(f"Evento no manejado: {event_type}")
            
            # Acknowledge del mensaje
            self.consumer.acknowledge(msg)
            
        except json.JSONDecodeError as e:
            logger.error(f"SAGA Consumer - corrId={correlation_id} eventId={event_id} error=invalid_json {str(e)}")
            self.consumer.negative_acknowledge(msg)
        except Exception as e:
            logger.error(f"SAGA Consumer - corrId={correlation_id} eventId={event_id} error={str(e)}")
            self.consumer.negative_acknowledge(msg)
    
    def _handle_saga_iniciada(self, message_data: Dict[str, Any], correlation_id: str):
        """Manejar evento de SAGA iniciada"""
        try:
            # Los datos están en message_data['data']
            data = message_data.get('data', {})
            saga_id = data.get('saga_id')
            tipo = data.get('tipo')
            datos_iniciales = data.get('datos_iniciales', {})
            
            logger.info(f"Procesando SAGA iniciada: saga={saga_id}, tipo={tipo}")
            
            # Obtener SAGA
            saga = self.repositorio.obtener_por_id(saga_id)
            if not saga:
                logger.error(f"SAGA {saga_id} no encontrada")
                return
            
            # Ejecutar primer paso
            self._ejecutar_siguiente_paso(saga)
            
        except Exception as e:
            logger.error(f"Error procesando SAGA iniciada: {str(e)}")

    def _ejecutar_siguiente_paso(self, saga):
        """Ejecutar el siguiente paso de la SAGA"""
        try:
            logger.info(f"Buscando siguiente paso en SAGA {saga.id}")
            logger.info(f"Pasos disponibles: {[(p.tipo.value, p.exitoso, p.error) for p in saga.pasos]}")
            
            # Buscar el primer paso no ejecutado
            paso_pendiente = None
            for paso in saga.pasos:
                if not paso.exitoso and not paso.error:
                    paso_pendiente = paso
                    break
            
            if not paso_pendiente:
                logger.info(f"No hay pasos pendientes en SAGA {saga.id}")
                return
            
            logger.info(f"Ejecutando paso: {paso_pendiente.tipo.value}")
            
            # Ejecutar el paso llamando al servicio correspondiente
            try:
                resultado = self._ejecutar_paso_servicio(paso_pendiente.tipo.value, paso_pendiente.datos)
                logger.info(f"Resultado del paso {paso_pendiente.tipo.value}: {resultado}")
            except Exception as e:
                logger.error(f"Error ejecutando paso {paso_pendiente.tipo.value}: {str(e)}")
                resultado = {"exitoso": False, "error": str(e)}
            
            if resultado and resultado.get('exitoso', False):
                # Marcar paso como exitoso
                comando = MarcarPasoExitosoCommand(
                    saga_id=str(saga.id),
                    paso_id=str(paso_pendiente.id),
                    resultado=resultado.get('datos', {})
                )
                logger.info(f"Marcando paso {paso_pendiente.tipo.value} como exitoso: {comando.__dict__}")
                self.marcar_paso_exitoso_handler.handle(comando)
                logger.info(f"Paso {paso_pendiente.tipo.value} ejecutado exitosamente")
                
                # Ejecutar siguiente paso si no es el último
                # Obtener la SAGA actualizada del repositorio
                saga_actualizada = self.repositorio.obtener_por_id(str(saga.id))
                if saga_actualizada:
                    self._ejecutar_siguiente_paso(saga_actualizada)
            else:
                # Marcar paso como fallido
                comando = MarcarPasoFallidoCommand(
                    saga_id=str(saga.id),
                    paso_id=str(paso_pendiente.id),
                    error=resultado.get('error', 'Error desconocido')
                )
                self.marcar_paso_fallido_handler.handle(comando)
                logger.error(f"Paso {paso_pendiente.tipo.value} falló: {resultado.get('error')}")
                
                # Ejecutar compensaciones para pasos exitosos anteriores
                # Obtener la SAGA actualizada del repositorio para asegurar el estado correcto
                saga_actualizada = self.repositorio.obtener_por_id(str(saga.id))
                if saga_actualizada:
                    self._ejecutar_compensaciones(saga_actualizada)
                
        except Exception as e:
            logger.error(f"Error ejecutando siguiente paso: {str(e)}")

    def _ejecutar_compensaciones(self, saga):
        """Ejecutar compensaciones para pasos exitosos anteriores"""
        try:
            logger.info(f"Iniciando compensaciones para SAGA {saga.id}")
            
            # Obtener pasos exitosos en orden inverso (del más reciente al más antiguo)
            pasos_exitosos = [p for p in saga.pasos if p.exitoso and p.resultado]
            pasos_exitosos.reverse()  # Compensar en orden inverso
            
            for paso in pasos_exitosos:
                logger.info(f"Ejecutando compensación para paso {paso.tipo.value}")
                
                # Determinar tipo de compensación basado en el paso
                tipo_compensacion = self._obtener_tipo_compensacion(paso.tipo.value)
                if not tipo_compensacion:
                    logger.warning(f"No hay compensación definida para {paso.tipo.value}")
                    continue
                
                # Crear compensación en la SAGA
                compensacion = saga.agregar_compensacion(paso.tipo, {
                    'saga_id': str(saga.id),
                    'paso_id': str(paso.id),
                    'tipo_compensacion': tipo_compensacion,
                    **paso.resultado
                })
                
                # Ejecutar compensación
                resultado = self._ejecutar_compensacion_servicio(tipo_compensacion, {
                    'saga_id': str(saga.id),
                    'paso_id': str(paso.id),
                    **paso.resultado
                })
                
                if resultado.get('exitoso', False):
                    # Marcar compensación como exitosa
                    saga.marcar_compensacion_exitosa(str(compensacion.id), resultado.get('datos', {}))
                    logger.info(f"Compensación {tipo_compensacion} ejecutada exitosamente")
                else:
                    # Marcar compensación como fallida
                    saga.marcar_compensacion_fallida(str(compensacion.id), resultado.get('error', 'Error desconocido'))
                    logger.error(f"Compensación {tipo_compensacion} falló: {resultado.get('error')}")
            
            # Actualizar la SAGA en el repositorio con las compensaciones
            self.repositorio.actualizar(saga)
            logger.info(f"SAGA {saga.id} actualizada con {len(saga.compensaciones)} compensaciones")
                    
        except Exception as e:
            logger.error(f"Error ejecutando compensaciones: {str(e)}")

    def _obtener_tipo_compensacion(self, tipo_paso: str) -> str:
        """Obtener el tipo de compensación para un paso"""
        compensaciones = {
            "CREAR_CAMPAÑA": "COMPENSAR_CAMPAÑA",
            "PROCESAR_PAGO": "REVERTIR_PAGO",
            "GENERAR_REPORTE": "CANCELAR_REPORTE"
        }
        return compensaciones.get(tipo_paso)

    def _handle_paso_ejecutado(self, message_data: Dict[str, Any], correlation_id: str):
        """Manejar evento de paso ejecutado"""
        try:
            # Los datos están en message_data['data']
            data = message_data.get('data', {})
            saga_id = data.get('saga_id')
            paso_id = data.get('paso_id')
            tipo_paso = data.get('tipo_paso')
            datos = data.get('datos', {})
            
            logger.info(f"Procesando paso ejecutado: sagaId={saga_id} pasoId={paso_id} tipo={tipo_paso}")
            
            # Ejecutar el paso llamando al servicio correspondiente
            resultado = self._ejecutar_paso_servicio(tipo_paso, datos)
            
            if resultado.get('exitoso', False):
                # Marcar paso como exitoso
                comando = MarcarPasoExitosoCommand(
                    saga_id=saga_id,
                    paso_id=paso_id,
                    resultado=resultado.get('datos', {})
                )
                self.marcar_paso_exitoso_handler.handle(comando)
                logger.info(f"Paso {paso_id} ejecutado exitosamente")
            else:
                # Marcar paso como fallido
                comando = MarcarPasoFallidoCommand(
                    saga_id=saga_id,
                    paso_id=paso_id,
                    error=resultado.get('error', 'Error desconocido')
                )
                self.marcar_paso_fallido_handler.handle(comando)
                
                # Iniciar compensación
                compensacion_comando = IniciarCompensacionCommand(
                    saga_id=saga_id,
                    paso_fallido=paso_id
                )
                self.iniciar_compensacion_handler.handle(compensacion_comando)
                logger.error(f"Paso {paso_id} falló: {resultado.get('error')}")
                
        except Exception as e:
            logger.error(f"Error manejando paso ejecutado: {str(e)}")
            raise
    
    def _handle_compensacion_ejecutada(self, message_data: Dict[str, Any], correlation_id: str):
        """Manejar evento de compensación ejecutada"""
        try:
            # Los datos están en message_data['data']
            data = message_data.get('data', {})
            saga_id = data.get('saga_id')
            compensacion_id = data.get('compensacion_id')
            tipo_compensacion = data.get('tipo_compensacion')
            datos = data.get('datos', {})
            
            logger.info(f"Procesando compensación: sagaId={saga_id} compId={compensacion_id} tipo={tipo_compensacion}")
            
            # Ejecutar la compensación llamando al servicio correspondiente
            resultado = self._ejecutar_compensacion_servicio(tipo_compensacion, datos)
            
            if resultado.get('exitoso', False):
                # Marcar compensación como exitosa
                comando = MarcarCompensacionExitosaCommand(
                    saga_id=saga_id,
                    compensacion_id=compensacion_id,
                    resultado=resultado.get('datos', {})
                )
                self.marcar_compensacion_exitosa_handler.handle(comando)
                logger.info(f"Compensación {compensacion_id} ejecutada exitosamente")
            else:
                # Marcar compensación como fallida
                comando = MarcarCompensacionFallidaCommand(
                    saga_id=saga_id,
                    compensacion_id=compensacion_id,
                    error=resultado.get('error', 'Error desconocido')
                )
                self.marcar_compensacion_fallida_handler.handle(comando)
                logger.error(f"Compensación {compensacion_id} falló: {resultado.get('error')}")
                
        except Exception as e:
            logger.error(f"Error manejando compensación: {str(e)}")
            raise
    
    def _ejecutar_paso_servicio(self, tipo_paso: str, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar un paso llamando al servicio correspondiente"""
        try:
            if tipo_paso == "CREAR_CAMPAÑA":
                # Llamar al proxy de campañas
                response = self.http_client.post(
                    "http://campaigns-proxy:8080/api/campaigns/",
                    json=datos
                )
                if response.status_code == 200:
                    return {"exitoso": True, "datos": response.json()}
                else:
                    return {"exitoso": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            elif tipo_paso == "PROCESAR_PAGO":
                # Llamar al servicio de pagos
                response = self.http_client.post(
                    "http://aeropartners-app:8000/pagos/",
                    json=datos
                )
                if response.status_code == 200:
                    return {"exitoso": True, "datos": response.json()}
                else:
                    return {"exitoso": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            elif tipo_paso == "GENERAR_REPORTE":
                # Llamar al servicio de reporting
                response = self.http_client.post(
                    "http://aeropartners-app:8000/reporting/report",
                    json=datos
                )
                if response.status_code == 200:
                    return {"exitoso": True, "datos": response.json()}
                else:
                    return {"exitoso": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            else:
                return {"exitoso": False, "error": f"Tipo de paso no soportado: {tipo_paso}"}
                
        except Exception as e:
            return {"exitoso": False, "error": str(e)}
    
    def _ejecutar_compensacion_servicio(self, tipo_compensacion: str, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar una compensación llamando al servicio correspondiente"""
        try:
            if tipo_compensacion == "COMPENSAR_CAMPAÑA":
                # Llamar al proxy de campañas para cancelar
                campana_id = datos.get("id")  # El ID de la campaña está en 'id' del resultado
                response = self.http_client.patch(
                    f"http://campaigns-proxy:8080/api/campaigns/{campana_id}/cancel",
                    json={"motivo": "SAGA_FALLIDA", "saga_id": datos.get('saga_id')}
                )
                if response.status_code == 200:
                    return {"exitoso": True, "datos": response.json()}
                else:
                    return {"exitoso": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            elif tipo_compensacion == "REVERTIR_PAGO":
                # Llamar al servicio de pagos para revertir
                pago_id = datos.get("id_pago")  # El ID del pago está en 'id_pago' del resultado
                response = self.http_client.patch(
                    f"http://aeropartners-app:8000/pagos/{pago_id}/revertir",
                    json={"motivo": "SAGA_FALLIDA", "saga_id": datos.get('saga_id')}
                )
                if response.status_code == 200:
                    return {"exitoso": True, "datos": response.json()}
                else:
                    return {"exitoso": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            elif tipo_compensacion == "CANCELAR_REPORTE":
                # Los reportes no necesitan compensación (son solo consultas)
                return {"exitoso": True, "datos": {"mensaje": "Reporte no requiere compensación"}}
            
            else:
                return {"exitoso": False, "error": f"Tipo de compensación no soportado: {tipo_compensacion}"}
                
        except Exception as e:
            return {"exitoso": False, "error": str(e)}
    
    def _cleanup(self):
        """Limpiar recursos"""
        try:
            if self.consumer:
                self.consumer.close()
                logger.info("SAGA Consumer cerrado")
            
            if hasattr(self, 'payment_consumer') and self.payment_consumer:
                self.payment_consumer.close()
                logger.info("Payment Consumer cerrado")
            
            if self.client:
                self.client.close()
                logger.info("Cliente Pulsar cerrado")
                
        except Exception as e:
            logger.error(f"Error en cleanup de SAGA: {str(e)}")

    def _handle_pago_exitoso(self, message_data: Dict[str, Any], correlation_id: str):
        """Manejar evento de pago exitoso y actualizar SAGA correspondiente"""
        try:
            data = message_data.get('data', {})
            id_pago = data.get('id_pago')
            
            logger.info(f"Procesando pago exitoso: {id_pago}")
            
            # Buscar SAGAs que tengan un paso de pago con este ID
            sagas = self.repositorio.obtener_todas()
            for saga in sagas:
                for paso in saga.pasos:
                    if (paso.tipo == TipoPaso.PROCESAR_PAGO and 
                        paso.resultado and 
                        paso.resultado.get('id_pago') == id_pago):
                        
                        logger.info(f"Actualizando paso de pago en SAGA {saga.id}")
                        
                        # Actualizar el resultado del paso con el estado final
                        paso.resultado['estado'] = 'EXITOSO'
                        paso.resultado['fecha_procesamiento'] = data.get('fecha_procesamiento')
                        
                        # Actualizar la SAGA en el repositorio
                        self.repositorio.actualizar(saga)
                        logger.info(f"SAGA {saga.id} actualizada con estado final del pago")
                        return
                        
        except Exception as e:
            logger.error(f"Error procesando pago exitoso: {str(e)}")

    def _handle_pago_fallido(self, message_data: Dict[str, Any], correlation_id: str):
        """Manejar evento de pago fallido y actualizar SAGA correspondiente"""
        try:
            data = message_data.get('data', {})
            id_pago = data.get('id_pago')
            mensaje_error = data.get('mensaje_error', 'Error desconocido')
            
            logger.info(f"Procesando pago fallido: {id_pago}")
            
            # Buscar SAGAs que tengan un paso de pago con este ID
            sagas = self.repositorio.obtener_todas()
            for saga in sagas:
                for paso in saga.pasos:
                    if (paso.tipo == TipoPaso.PROCESAR_PAGO and 
                        paso.resultado and 
                        paso.resultado.get('id_pago') == id_pago):
                        
                        logger.info(f"Actualizando paso de pago fallido en SAGA {saga.id}")
                        
                        # Marcar el paso como fallido
                        paso.marcar_fallido(mensaje_error)
                        saga.estado = EstadoSaga.FALLIDA
                        saga.error_message = mensaje_error
                        saga.fecha_fin = datetime.now()
                        
                        # Actualizar la SAGA en el repositorio
                        self.repositorio.actualizar(saga)
                        logger.info(f"SAGA {saga.id} marcada como fallida por pago fallido")
                        return
                        
        except Exception as e:
            logger.error(f"Error procesando pago fallido: {str(e)}")

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y iniciar consumer
    consumer = SagaPulsarConsumer()
    consumer.start_consuming()
