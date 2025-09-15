import logging
from typing import Dict, Any
from datetime import datetime

from .comandos import ProcesarEventoTrackingCommand, ReprocesarEventoFallidoCommand
from .queries import (
    ObtenerEstadoEventoQuery, ObtenerEstadisticasProcessingQuery,
    ObtenerEventosFallidosQuery, ObtenerRateLimitStatusQuery
)
from ..dominio.entidades import EventoTracking
from ..dominio.enums import TipoEvento, TipoDispositivo, FuenteEvento
from ..dominio.objetos_valor import (
    MetadatosEvento, ContextoEvento, DatosDispositivo, 
    FirmaEvento, PayloadEvento
)
from ..dominio.repositorios import (
    RepositorioEventos, RepositorioAfiliados, 
    RepositorioCampanas, RepositorioRateLimiting
)
from ..dominio.servicios import ServicioPublicacionEventos, ServicioValidacionEventos

logger = logging.getLogger(__name__)

class ProcesarEventoTrackingHandler:
    
    def __init__(
        self,
        servicio_publicacion: ServicioPublicacionEventos,
        servicio_validacion: ServicioValidacionEventos,
        repo_eventos: RepositorioEventos,
        repo_rate_limiting: RepositorioRateLimiting
    ):
        self.servicio_publicacion = servicio_publicacion
        self.servicio_validacion = servicio_validacion
        self.repo_eventos = repo_eventos
        self.repo_rate_limiting = repo_rate_limiting
    
    async def handle(self, comando: ProcesarEventoTrackingCommand) -> Dict[str, Any]:
        """
        Procesa un evento de tracking siguiendo el pipeline DDD
        """
        logger.info(f"Procesando evento de tracking - Tipo: {comando.tipo_evento}, Afiliado: {comando.id_afiliado}")
        
        try:
            # 1. Crear el agregado EventoTracking
            evento_tracking = self._crear_evento_tracking(comando)
            
            # 2. Ejecutar validaciones de negocio
            validaciones = await self.servicio_validacion.validar_evento_completo(
                hash_evento=evento_tracking.hash_evento,
                tipo_evento=evento_tracking.tipo_evento,
                contexto=evento_tracking.contexto,
                payload=evento_tracking.payload,
                timestamp=evento_tracking.metadatos.timestamp
            )
            
            # 3. Procesar resultado de validaciones
            if not evento_tracking.validar_evento(validaciones):
                logger.warning(f"Evento descartado - ID: {evento_tracking.id}, Razón: {evento_tracking.razon_fallo}")
                return {
                    'exito': False,
                    'id_evento': str(evento_tracking.id),
                    'estado': evento_tracking.estado.value,
                    'razon': evento_tracking.razon_fallo,
                    'validaciones': validaciones
                }
            
            # 4. Incrementar rate limiting (después de validaciones exitosas)
            await self.repo_rate_limiting.incrementar_contador(comando.id_afiliado)
            
            # 5. Guardar en caché de deduplicación
            await self.repo_eventos.guardar_evento_temporal(
                evento_tracking.hash_evento, 
                evento_tracking.fecha_creacion
            )
            
            # 6. Iniciar procesamiento
            evento_tracking.iniciar_procesamiento()
            
            # 7. Publicar al topic de Pulsar
            try:
                datos_publicacion = evento_tracking.obtener_datos_para_publicacion()
                partition_key = self.servicio_publicacion.generar_partition_key(evento_tracking.contexto)
                
                mensaje_id = await self.servicio_publicacion.publicar_evento(
                    tipo_evento=evento_tracking.tipo_evento,
                    contexto=evento_tracking.contexto,
                    payload=evento_tracking.payload,
                    metadatos=datos_publicacion
                )
                
                # 8. Marcar como publicado exitosamente
                topic_destino = self.servicio_publicacion.obtener_topic_destino(evento_tracking.tipo_evento)
                evento_tracking.marcar_como_publicado(topic_destino, mensaje_id, partition_key)
                
                logger.info(f"Evento publicado exitosamente - ID: {evento_tracking.id}, Topic: {topic_destino}")
                
                return {
                    'exito': True,
                    'id_evento': str(evento_tracking.id),
                    'estado': evento_tracking.estado.value,
                    'topic_destino': topic_destino,
                    'mensaje_id': mensaje_id,
                    'hash_evento': evento_tracking.hash_evento
                }
                
            except Exception as e:
                # 9. Manejar fallo en publicación
                evento_tracking.marcar_como_fallido(str(e), "PUBLICATION_ERROR")
                logger.error(f"Error publicando evento - ID: {evento_tracking.id}, Error: {str(e)}")
                
                return {
                    'exito': False,
                    'id_evento': str(evento_tracking.id),
                    'estado': evento_tracking.estado.value,
                    'razon': str(e),
                    'puede_reintentar': evento_tracking.puede_ser_reintentado()
                }
        
        except Exception as e:
            logger.error(f"Error crítico procesando evento - Comando: {comando}, Error: {str(e)}")
            return {
                'exito': False,
                'error_critico': True,
                'razon': str(e)
            }
    
    def _crear_evento_tracking(self, comando: ProcesarEventoTrackingCommand) -> EventoTracking:
        """Crea el agregado EventoTracking desde el comando"""
        
        # Convertir strings a enums
        try:
            tipo_evento = TipoEvento(comando.tipo_evento.upper())
        except ValueError:
            raise ValueError(f"Tipo de evento no válido: {comando.tipo_evento}")
        
        try:
            tipo_dispositivo = TipoDispositivo(comando.tipo_dispositivo.upper())
        except ValueError:
            tipo_dispositivo = TipoDispositivo.OTHER
        
        try:
            fuente_evento = FuenteEvento(comando.fuente_evento.upper())
        except ValueError:
            fuente_evento = FuenteEvento.WEB_TAG
        
        # Crear objetos de valor
        metadatos = MetadatosEvento(
            ip_origen=comando.ip_origen,
            user_agent=comando.user_agent,
            timestamp=comando.timestamp,
            session_id=comando.session_id,
            referrer=comando.referrer
        )
        
        contexto = ContextoEvento(
            id_afiliado=comando.id_afiliado,
            id_campana=comando.id_campana,
            id_oferta=comando.id_oferta,
            url=comando.url,
            parametros_tracking=comando.parametros_tracking
        )
        
        dispositivo = DatosDispositivo(
            tipo=tipo_dispositivo,
            identificador=comando.identificador_dispositivo,
            so=comando.sistema_operativo,
            navegador=comando.navegador,
            resolucion=comando.resolucion_pantalla
        )
        
        firma = FirmaEvento(
            fuente=fuente_evento,
            api_key=comando.api_key,
            hash_validacion=comando.hash_validacion
        )
        
        payload = PayloadEvento(
            datos_custom=comando.datos_custom or {},
            valor_conversion=comando.valor_conversion,
            moneda=comando.moneda
        )
        
        return EventoTracking(
            tipo_evento=tipo_evento,
            contexto=contexto,
            payload=payload,
            metadatos=metadatos,
            dispositivo=dispositivo,
            firma=firma
        )

class ReprocesarEventoFallidoHandler:
    
    def __init__(
        self,
        handler_principal: ProcesarEventoTrackingHandler,
        # Aquí se añadiría repositorio para recuperar eventos fallidos
    ):
        self.handler_principal = handler_principal
    
    async def handle(self, comando: ReprocesarEventoFallidoCommand) -> Dict[str, Any]:
        """Reprocesa un evento fallido"""
        logger.info(f"Reprocesando evento fallido - ID: {comando.id_evento}")
        
        # TODO: Implementar lógica para recuperar evento fallido y convertirlo a comando
        # Por ahora, devolver respuesta de que la funcionalidad está en desarrollo
        return {
            'exito': False,
            'razon': 'Funcionalidad de reproceso en desarrollo',
            'id_evento': comando.id_evento
        }

class ObtenerEstadoEventoHandler:
    
    async def handle(self, query: ObtenerEstadoEventoQuery) -> Dict[str, Any]:
        """Obtiene el estado de un evento específico"""
        # TODO: Implementar con repositorio de consultas
        return {
            'id_evento': query.id_evento,
            'estado': 'FUNCIONALIDAD_EN_DESARROLLO',
            'mensaje': 'Consulta de estado en desarrollo'
        }

class ObtenerEstadisticasProcessingHandler:
    
    async def handle(self, query: ObtenerEstadisticasProcessingQuery) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento de eventos"""
        # TODO: Implementar con repositorio de métricas
        return {
            'estadisticas': 'EN_DESARROLLO',
            'mensaje': 'Estadísticas en desarrollo'
        }

class ObtenerEventosFallidosHandler:
    
    async def handle(self, query: ObtenerEventosFallidosQuery) -> Dict[str, Any]:
        """Obtiene la lista de eventos fallidos"""
        # TODO: Implementar con repositorio de eventos fallidos
        return {
            'eventos_fallidos': [],
            'mensaje': 'Consulta de eventos fallidos en desarrollo'
        }

class ObtenerRateLimitStatusHandler:
    
    def __init__(self, repo_rate_limiting: RepositorioRateLimiting):
        self.repo_rate_limiting = repo_rate_limiting
    
    async def handle(self, query: ObtenerRateLimitStatusQuery) -> Dict[str, Any]:
        """Obtiene el estado actual del rate limiting para un afiliado"""
        try:
            contador_actual = await self.repo_rate_limiting.obtener_contador_actual(
                query.id_afiliado, 
                query.ventana_minutos
            )
            
            return {
                'id_afiliado': query.id_afiliado,
                'eventos_actuales': contador_actual,
                'ventana_minutos': query.ventana_minutos,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo rate limit status - Afiliado: {query.id_afiliado}, Error: {str(e)}")
            return {
                'error': True,
                'mensaje': str(e)
            }
