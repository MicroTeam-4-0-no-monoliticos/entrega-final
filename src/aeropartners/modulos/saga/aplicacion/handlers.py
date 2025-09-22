import logging
import uuid
from typing import Dict, Any
from ....seedwork.aplicacion.comandos import ComandoHandler
from ....seedwork.infraestructura.pulsar_producer import PulsarEventProducer
from ..dominio.entidades import Saga, TipoPaso, EstadoSaga
from ..dominio.eventos import (
    SagaIniciada, SagaCampañaCreada, SagaPagoProcesado, 
    SagaReporteGenerado, SagaCompletada, SagaFallida,
    SagaCompensacionIniciada, SagaCompensacionCompletada,
    SagaCompensacionFallida, SagaTimeout, SagaPasoEjecutado,
    SagaCompensacionEjecutada
)
from ..dominio.repositorios import RepositorioSaga
from .comandos import (
    IniciarSagaCommand, EjecutarPasoCommand, MarcarPasoExitosoCommand,
    MarcarPasoFallidoCommand, IniciarCompensacionCommand,
    EjecutarCompensacionCommand, MarcarCompensacionExitosaCommand,
    MarcarCompensacionFallidaCommand, CrearCampanaCompletaCommand,
    ProcesarTimeoutSagaCommand
)

logger = logging.getLogger(__name__)

class IniciarSagaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: IniciarSagaCommand):
        # Crear nueva SAGA
        saga = Saga(comando.tipo, comando.datos_iniciales)
        
        # Persistir SAGA
        self.repositorio.agregar(saga)
        
        # Publicar evento de SAGA iniciada
        evento = SagaIniciada(
            saga_id=str(saga.id),
            tipo=saga.tipo,
            datos_iniciales=saga.datos_iniciales
        )
        self.pulsar_producer.publish_event(
            event_type="SagaIniciada",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.info(f"SAGA {saga.id} iniciada: {saga.tipo}")
        return saga

class CrearCampanaCompletaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: CrearCampanaCompletaCommand):
        # Crear SAGA para campaña completa
        datos_iniciales = {
            "campana": comando.datos_campana,
            "pago": comando.datos_pago,
            "reporte": comando.datos_reporte
        }
        
        saga = Saga("CREAR_CAMPANA_COMPLETA", datos_iniciales)
        
        # Agregar pasos de la SAGA
        saga.agregar_paso(TipoPaso.CREAR_CAMPAÑA, comando.datos_campana)
        saga.agregar_paso(TipoPaso.PROCESAR_PAGO, comando.datos_pago)
        saga.agregar_paso(TipoPaso.GENERAR_REPORTE, comando.datos_reporte)
        
        # Persistir SAGA
        self.repositorio.agregar(saga)
        
        # Publicar evento de SAGA iniciada
        print(f"DEBUG HANDLER: saga.id = {saga.id}")
        print(f"DEBUG HANDLER: saga._id = {getattr(saga, '_id', 'NO EXISTE')}")
        evento = SagaIniciada(
            saga_id=str(saga.id),
            tipo=saga.tipo,
            datos_iniciales=saga.datos_iniciales
        )
        self.pulsar_producer.publish_event(
            event_type="SagaIniciada",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.info(f"SAGA de campaña completa {saga.id} iniciada")
        return saga

class EjecutarPasoHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: EjecutarPasoCommand):
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            raise ValueError(f"SAGA {comando.saga_id} no encontrada")
        
        # Buscar el paso
        paso = saga._buscar_paso_por_id(comando.paso_id)
        if not paso:
            raise ValueError(f"Paso {comando.paso_id} no encontrado en SAGA {comando.saga_id}")
        
        # Publicar evento de paso ejecutado
        evento = SagaPasoEjecutado(
            saga_id=comando.saga_id,
            paso_id=comando.paso_id,
            tipo_paso=comando.tipo_paso,
            datos=comando.datos
        )
        self.pulsar_producer.publish_event(
            event_type="SagaPasoEjecutado",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.info(f"Paso {comando.paso_id} de SAGA {comando.saga_id} ejecutado")
        return paso

class MarcarPasoExitosoHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: MarcarPasoExitosoCommand):
        logger.info(f"MarcarPasoExitosoHandler: Procesando comando {comando.__dict__}")
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            logger.error(f"SAGA {comando.saga_id} no encontrada")
            raise ValueError(f"SAGA {comando.saga_id} no encontrada")
        
        # Marcar paso como exitoso
        logger.info(f"Marcando paso {comando.paso_id} como exitoso")
        saga.marcar_paso_exitoso(comando.paso_id, comando.resultado)
        logger.info(f"Paso marcado como exitoso. Estado actual: {[(p.tipo.value, p.exitoso, p.error) for p in saga.pasos]}")
        
        # Actualizar SAGA en repositorio
        logger.info(f"Actualizando SAGA en repositorio")
        self.repositorio.actualizar(saga)
        logger.info(f"SAGA actualizada en repositorio")
        
        # Publicar eventos específicos según el tipo de paso
        paso = saga._buscar_paso_por_id(comando.paso_id)
        if paso:
            if paso.tipo == TipoPaso.CREAR_CAMPAÑA:
                evento = SagaCampañaCreada(
                    saga_id=comando.saga_id,
                    campana_id=comando.resultado.get("id"),
                    datos_campana=comando.resultado
                )
                self.pulsar_producer.publish_event(
                    event_type="SagaCampañaCreada",
                    event_data=evento.__dict__,
                    event_id=str(uuid.uuid4())
                )
            elif paso.tipo == TipoPaso.PROCESAR_PAGO:
                evento = SagaPagoProcesado(
                    saga_id=comando.saga_id,
                    pago_id=comando.resultado.get("id"),
                    datos_pago=comando.resultado
                )
                self.pulsar_producer.publish_event(
                    event_type="SagaPagoProcesado",
                    event_data=evento.__dict__,
                    event_id=str(uuid.uuid4())
                )
            elif paso.tipo == TipoPaso.GENERAR_REPORTE:
                evento = SagaReporteGenerado(
                    saga_id=comando.saga_id,
                    reporte_id=comando.resultado.get("id"),
                    datos_reporte=comando.resultado
                )
                self.pulsar_producer.publish_event(
                    event_type="SagaReporteGenerado",
                    event_data=evento.__dict__,
                    event_id=str(uuid.uuid4())
                )
        
        # Verificar si la SAGA está completa
        if saga.es_completa():
            evento = SagaCompletada(
                saga_id=comando.saga_id,
                resultado_final={"estado": "COMPLETADA"}
            )
            self.pulsar_producer.publish_event(
                event_type="SagaCompletada",
                event_data=evento.__dict__,
                event_id=str(uuid.uuid4())
            )
        
        logger.info(f"Paso {comando.paso_id} de SAGA {comando.saga_id} marcado como exitoso")
        return saga

class MarcarPasoFallidoHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: MarcarPasoFallidoCommand):
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            raise ValueError(f"SAGA {comando.saga_id} no encontrada")
        
        # Marcar paso como fallido
        saga.marcar_paso_fallido(comando.paso_id, comando.error)
        
        # Actualizar SAGA en repositorio
        self.repositorio.actualizar(saga)
        
        # Publicar evento de SAGA fallida
        evento = SagaFallida(
            saga_id=comando.saga_id,
            error=comando.error,
            paso_fallido=comando.paso_id
        )
        self.pulsar_producer.publish_event(
            event_type="SagaFallida",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.error(f"Paso {comando.paso_id} de SAGA {comando.saga_id} falló: {comando.error}")
        return saga

class IniciarCompensacionHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: IniciarCompensacionCommand):
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            raise ValueError(f"SAGA {comando.saga_id} no encontrada")
        
        # Iniciar compensación
        saga.iniciar_compensacion()
        
        # Crear compensaciones en orden inverso
        pasos_exitosos = [p for p in saga.pasos if p.exitoso]
        for paso in reversed(pasos_exitosos):
            if paso.tipo == TipoPaso.CREAR_CAMPAÑA:
                compensacion = saga.agregar_compensacion(
                    TipoPaso.COMPENSAR_CAMPAÑA,
                    {"campana_id": paso.resultado.get("id")}
                )
            elif paso.tipo == TipoPaso.PROCESAR_PAGO:
                compensacion = saga.agregar_compensacion(
                    TipoPaso.REVERTIR_PAGO,
                    {"pago_id": paso.resultado.get("id")}
                )
            elif paso.tipo == TipoPaso.GENERAR_REPORTE:
                compensacion = saga.agregar_compensacion(
                    TipoPaso.CANCELAR_REPORTE,
                    {"reporte_id": paso.resultado.get("id")}
                )
        
        # Actualizar SAGA en repositorio
        self.repositorio.actualizar(saga)
        
        # Publicar evento de compensación iniciada
        evento = SagaCompensacionIniciada(
            saga_id=comando.saga_id,
            paso_a_compensar=comando.paso_fallido
        )
        self.pulsar_producer.publish_event(
            event_type="SagaCompensacionIniciada",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.info(f"Compensación iniciada para SAGA {comando.saga_id}")
        return saga

class ProcesarTimeoutSagaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: ProcesarTimeoutSagaCommand):
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            return
        
        # Marcar SAGA como fallida por timeout
        saga.estado = EstadoSaga.FALLIDA
        saga.error_message = f"Timeout después de {comando.timeout_minutos} minutos"
        
        # Actualizar SAGA en repositorio
        self.repositorio.actualizar(saga)
        
        # Publicar evento de timeout
        evento = SagaTimeout(
            saga_id=comando.saga_id,
            timeout_minutos=comando.timeout_minutos
        )
        self.pulsar_producer.publish_event(
            event_type="SagaTimeout",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.warning(f"SAGA {comando.saga_id} timeout después de {comando.timeout_minutos} minutos")
        return saga

class EjecutarCompensacionHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: EjecutarCompensacionCommand):
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            raise ValueError(f"SAGA {comando.saga_id} no encontrada")
        
        # Buscar la compensación
        compensacion = saga._buscar_compensacion_por_id(comando.compensacion_id)
        if not compensacion:
            raise ValueError(f"Compensación {comando.compensacion_id} no encontrada en SAGA {comando.saga_id}")
        
        # Publicar evento de compensación ejecutada
        evento = SagaCompensacionEjecutada(
            saga_id=comando.saga_id,
            compensacion_id=comando.compensacion_id,
            tipo_compensacion=comando.tipo_compensacion,
            datos=comando.datos
        )
        self.pulsar_producer.publish_event(
            event_type="SagaCompensacionEjecutada",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.info(f"Compensación {comando.compensacion_id} de SAGA {comando.saga_id} ejecutada")
        return compensacion

class MarcarCompensacionExitosaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: MarcarCompensacionExitosaCommand):
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            raise ValueError(f"SAGA {comando.saga_id} no encontrada")
        
        # Marcar compensación como exitosa
        saga.marcar_compensacion_exitosa(comando.compensacion_id, comando.resultado)
        
        # Actualizar SAGA en repositorio
        self.repositorio.actualizar(saga)
        
        # Publicar evento de compensación completada
        evento = SagaCompensacionCompletada(
            saga_id=comando.saga_id,
            compensacion_id=comando.compensacion_id,
            resultado=comando.resultado
        )
        self.pulsar_producer.publish_event(
            event_type="SagaCompensacionCompletada",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.info(f"Compensación {comando.compensacion_id} de SAGA {comando.saga_id} marcada como exitosa")
        return saga

class MarcarCompensacionFallidaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioSaga, pulsar_producer: PulsarEventProducer):
        self.repositorio = repositorio
        self.pulsar_producer = pulsar_producer

    def handle(self, comando: MarcarCompensacionFallidaCommand):
        saga = self.repositorio.obtener_por_id(comando.saga_id)
        if not saga:
            raise ValueError(f"SAGA {comando.saga_id} no encontrada")
        
        # Marcar compensación como fallida
        saga.marcar_compensacion_fallida(comando.compensacion_id, comando.error)
        
        # Actualizar SAGA en repositorio
        self.repositorio.actualizar(saga)
        
        # Publicar evento de compensación fallida
        evento = SagaCompensacionFallida(
            saga_id=comando.saga_id,
            compensacion_id=comando.compensacion_id,
            error=comando.error
        )
        self.pulsar_producer.publish_event(
            event_type="SagaCompensacionFallida",
            event_data=evento.__dict__,
            event_id=str(uuid.uuid4())
        )
        
        logger.error(f"Compensación {comando.compensacion_id} de SAGA {comando.saga_id} falló: {comando.error}")
        return saga
