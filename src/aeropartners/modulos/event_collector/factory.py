"""
Factory para crear instancias de los servicios del Event Collector
Implementa inyección de dependencias siguiendo principios DDD
"""

import os
import logging
from typing import Optional

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dominio
from .dominio.servicios import ServicioValidacionEventos

# Aplicación  
from .aplicacion.handlers import (
    ProcesarEventoTrackingHandler, ReprocesarEventoFallidoHandler,
    ObtenerEstadoEventoHandler, ObtenerEstadisticasProcessingHandler,
    ObtenerEventosFallidosHandler, ObtenerRateLimitStatusHandler
)

# Infraestructura
from .infraestructura.adaptadores import PulsarEventPublisher
from .infraestructura.repositorios import (
    InMemoryRepositorioEventos, MockRepositorioAfiliados,
    MockRepositorioCampanas, InMemoryRepositorioRateLimiting,
    RedisRepositorioEventos, RedisRepositorioRateLimiting
)

class EventCollectorFactory:
    """
    Factory para crear instancias configuradas de los servicios del Event Collector
    Maneja la configuración de infraestructura y la inyección de dependencias
    """
    
    def __init__(self):
        self._handlers_cache = {}
        self._services_cache = {}
        self._repositories_cache = {}
        
    def crear_handler_procesar_evento(self) -> ProcesarEventoTrackingHandler:
        if 'event_processing' not in self._handlers_cache:
            
            # Crear repositorios
            repo_eventos = self._create_eventos_repository()
            repo_afiliados = self._create_afiliados_repository()
            repo_campanas = self._create_campanas_repository()
            repo_rate_limiting = self._create_rate_limiting_repository()
            
            # Crear servicios de dominio
            servicio_publicacion = self._create_publicacion_service()
            servicio_validacion = ServicioValidacionEventos(
                repo_eventos, repo_afiliados, repo_campanas, repo_rate_limiting
            )
            
            # Crear handler
            self._handlers_cache['event_processing'] = ProcesarEventoTrackingHandler(
                servicio_publicacion=servicio_publicacion,
                servicio_validacion=servicio_validacion,
                repo_eventos=repo_eventos,
                repo_rate_limiting=repo_rate_limiting
            )
            
        return self._handlers_cache['event_processing']
    
    def crear_handler_reprocesar_evento(self) -> ReprocesarEventoFallidoHandler:
        if 'retry' not in self._handlers_cache:
            main_handler = self.crear_handler_procesar_evento()
            self._handlers_cache['retry'] = ReprocesarEventoFallidoHandler(main_handler)
            
        return self._handlers_cache['retry']
    
    def create_estado_evento_handler(self) -> ObtenerEstadoEventoHandler:
        if 'estado_evento' not in self._handlers_cache:
            self._handlers_cache['estado_evento'] = ObtenerEstadoEventoHandler()
            
        return self._handlers_cache['estado_evento']
    
    def create_estadisticas_handler(self) -> ObtenerEstadisticasProcessingHandler:
        if 'estadisticas' not in self._handlers_cache:
            self._handlers_cache['estadisticas'] = ObtenerEstadisticasProcessingHandler()
            
        return self._handlers_cache['estadisticas']
    
    def create_eventos_fallidos_handler(self) -> ObtenerEventosFallidosHandler:
        if 'eventos_fallidos' not in self._handlers_cache:
            self._handlers_cache['eventos_fallidos'] = ObtenerEventosFallidosHandler()
            
        return self._handlers_cache['eventos_fallidos']
    
    def create_rate_limit_status_handler(self) -> ObtenerRateLimitStatusHandler:
        if 'rate_limit_status' not in self._handlers_cache:
            repo_rate_limiting = self._create_rate_limiting_repository()
            self._handlers_cache['rate_limit_status'] = ObtenerRateLimitStatusHandler(repo_rate_limiting)
            
        return self._handlers_cache['rate_limit_status']
    
    # Métodos privados para crear servicios de infraestructura
    
    def _create_eventos_repository(self):
        """Crea repositorio de eventos según configuración"""
        if 'eventos' not in self._repositories_cache:
            use_redis = os.getenv('USE_REDIS', 'false').lower() == 'true'
            
            if use_redis:
                try:
                    import redis
                    redis_client = redis.Redis(
                        host=os.getenv('REDIS_HOST', 'localhost'),
                        port=int(os.getenv('REDIS_PORT', 6379)),
                        decode_responses=True
                    )
                    self._repositories_cache['eventos'] = RedisRepositorioEventos(redis_client)
                    logger.info("Usando RedisRepositorioEventos")
                except ImportError:
                    logger.warning("Redis no disponible, usando repositorio en memoria")
                    self._repositories_cache['eventos'] = InMemoryRepositorioEventos()
            else:
                self._repositories_cache['eventos'] = InMemoryRepositorioEventos()
                logger.info("Usando InMemoryRepositorioEventos")
                
        return self._repositories_cache['eventos']
    
    def _create_afiliados_repository(self):
        """Crea repositorio de afiliados"""
        if 'afiliados' not in self._repositories_cache:
            self._repositories_cache['afiliados'] = MockRepositorioAfiliados()
            logger.info("Usando MockRepositorioAfiliados")
            
        return self._repositories_cache['afiliados']
    
    def _create_campanas_repository(self):
        """Crea repositorio de campañas"""
        if 'campanas' not in self._repositories_cache:
            self._repositories_cache['campanas'] = MockRepositorioCampanas()
            logger.info("Usando MockRepositorioCampanas")
            
        return self._repositories_cache['campanas']
    
    def _create_rate_limiting_repository(self):
        """Crea repositorio de rate limiting según configuración"""
        if 'rate_limiting' not in self._repositories_cache:
            use_redis = os.getenv('USE_REDIS', 'false').lower() == 'true'
            
            if use_redis:
                try:
                    import redis
                    redis_client = redis.Redis(
                        host=os.getenv('REDIS_HOST', 'localhost'),
                        port=int(os.getenv('REDIS_PORT', 6379)),
                        decode_responses=True
                    )
                    self._repositories_cache['rate_limiting'] = RedisRepositorioRateLimiting(redis_client)
                    logger.info("Usando RedisRepositorioRateLimiting")
                except ImportError:
                    logger.warning("Redis no disponible, usando repositorio en memoria")
                    self._repositories_cache['rate_limiting'] = InMemoryRepositorioRateLimiting()
            else:
                self._repositories_cache['rate_limiting'] = InMemoryRepositorioRateLimiting()
                logger.info("Usando InMemoryRepositorioRateLimiting")
                
        return self._repositories_cache['rate_limiting']
    
    def _create_publicacion_service(self):
        """Crea servicio de publicación de eventos"""
        if 'publicacion' not in self._services_cache:
            pulsar_url = os.getenv('PULSAR_URL', 'pulsar://localhost:6650')
            self._services_cache['publicacion'] = PulsarEventPublisher(pulsar_url)
            logger.info(f"Usando PulsarEventPublisher con URL: {pulsar_url}")
            
        return self._services_cache['publicacion']

# Instancia global del factory
event_collector_factory = EventCollectorFactory()

# Funciones de dependencias para FastAPI
def get_procesar_evento_handler() -> ProcesarEventoTrackingHandler:
    return event_collector_factory.crear_handler_procesar_evento()

def get_retry_handler() -> ReprocesarEventoFallidoHandler:
    """Dependency provider para el handler de retry"""
    return event_collector_factory.crear_handler_reprocesar_evento()

def get_estado_evento_handler() -> ObtenerEstadoEventoHandler:
    """Dependency provider para consultas de estado"""
    return event_collector_factory.create_estado_evento_handler()

def get_estadisticas_handler() -> ObtenerEstadisticasProcessingHandler:
    """Dependency provider para estadísticas"""
    return event_collector_factory.create_estadisticas_handler()

def get_eventos_fallidos_handler() -> ObtenerEventosFallidosHandler:
    """Dependency provider para eventos fallidos"""
    return event_collector_factory.create_eventos_fallidos_handler()

def get_rate_limit_status_handler() -> ObtenerRateLimitStatusHandler:
    """Dependency provider para rate limiting"""
    return event_collector_factory.create_rate_limit_status_handler()
