import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Set, Dict, Any
import redis
import json

from ..dominio.repositorios import (
    RepositorioEventos, RepositorioAfiliados, 
    RepositorioCampanas, RepositorioRateLimiting
)

logger = logging.getLogger(__name__)

class RedisRepositorioEventos(RepositorioEventos):
    """
    Implementación Redis del repositorio de eventos para deduplicación
    Usa TTL para limpiar automáticamente eventos antiguos
    """
    
    def __init__(self, redis_client: redis.Redis, ttl_horas: int = 24):
        self.redis = redis_client
        self.ttl_segundos = ttl_horas * 3600
        self.prefix = "event_collector:eventos:"
    
    async def existe_evento(self, hash_evento: str) -> bool:
        """Verifica si un evento ya fue procesado"""
        try:
            key = f"{self.prefix}{hash_evento}"
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error verificando existencia de evento {hash_evento}: {str(e)}")
            return False
    
    async def guardar_evento_temporal(self, hash_evento: str, timestamp: datetime) -> None:
        """Guarda temporalmente un evento para deduplicación"""
        try:
            key = f"{self.prefix}{hash_evento}"
            valor = {
                'timestamp': timestamp.isoformat(),
                'processed_at': datetime.now().isoformat()
            }
            self.redis.setex(key, self.ttl_segundos, json.dumps(valor))
        except Exception as e:
            logger.error(f"Error guardando evento temporal {hash_evento}: {str(e)}")
            raise
    
    async def limpiar_eventos_antiguos(self, max_antiguedad_horas: int = 24) -> int:
        """Limpia eventos temporales antiguos (Redis maneja esto automáticamente con TTL)"""
        try:
            # Redis limpia automáticamente con TTL, pero podemos hacer scan manual si es necesario
            pattern = f"{self.prefix}*"
            keys = self.redis.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"Error consultando eventos: {str(e)}")
            return 0

class MockRepositorioAfiliados(RepositorioAfiliados):
    """
    Implementación mock del repositorio de afiliados para desarrollo
    En producción se conectaría a la BD de afiliados
    """
    
    # Datos mock para desarrollo
    AFILIADOS_MOCK = {
        "afiliado_test_1": {
            "activo": True,
            "permisos": {"evento_click", "evento_impression", "evento_conversion", "evento_page_view"},
            "limites": {"eventos_por_minuto": 1000, "eventos_por_hora": 50000}
        },
        "afiliado_test_2": {
            "activo": True,
            "permisos": {"evento_click", "evento_impression"},
            "limites": {"eventos_por_minuto": 100, "eventos_por_hora": 5000}
        },
        "afiliado_vip": {
            "activo": True,
            "permisos": {"evento_click", "evento_impression", "evento_conversion", "evento_page_view"},
            "limites": {"eventos_por_minuto": 10000, "eventos_por_hora": 500000}
        }
    }
    
    async def obtener_permisos_afiliado(self, id_afiliado: str) -> Optional[Set[str]]:
        """Obtiene los permisos de tracking del afiliado"""
        afiliado_data = self.AFILIADOS_MOCK.get(id_afiliado)
        if afiliado_data and afiliado_data["activo"]:
            return afiliado_data["permisos"]
        return None
    
    async def obtener_limites_afiliado(self, id_afiliado: str) -> Dict[str, Any]:
        """Obtiene los límites de rate limiting del afiliado"""
        afiliado_data = self.AFILIADOS_MOCK.get(id_afiliado)
        if afiliado_data:
            return afiliado_data["limites"]
        return {"eventos_por_minuto": 100, "eventos_por_hora": 1000}  # Límites por defecto
    
    async def afiliado_activo(self, id_afiliado: str) -> bool:
        """Verifica si el afiliado está activo"""
        afiliado_data = self.AFILIADOS_MOCK.get(id_afiliado)
        return afiliado_data is not None and afiliado_data["activo"]

class MockRepositorioCampanas(RepositorioCampanas):
    """
    Implementación mock del repositorio de campañas para desarrollo
    En producción se conectaría al servicio de campañas
    """
    
    # Campañas mock para desarrollo
    CAMPANAS_MOCK = {
        "campaign_123": {"activa": True, "nombre": "Campaña Test 1"},
        "campaign_456": {"activa": True, "nombre": "Campaña Test 2"},
        "campaign_789": {"activa": False, "nombre": "Campaña Inactiva"}
    }
    
    async def campana_existe_y_activa(self, id_campana: str) -> bool:
        """Verifica si la campaña existe y está activa"""
        campana = self.CAMPANAS_MOCK.get(id_campana)
        return campana is not None and campana["activa"]

class RedisRepositorioRateLimiting(RepositorioRateLimiting):
    """
    Implementación Redis del repositorio de rate limiting
    Usa ventanas deslizantes para controlar la frecuencia de eventos
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "event_collector:rate_limit:"
    
    async def incrementar_contador(self, id_afiliado: str, ventana_minutos: int = 1) -> int:
        """Incrementa contador de eventos para el afiliado en la ventana especificada"""
        try:
            key = self._generar_key(id_afiliado, ventana_minutos)
            
            # Usar pipeline para operaciones atómicas
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ventana_minutos * 60)  # TTL en segundos
            resultados = pipe.execute()
            
            return resultados[0]  # Valor después del incremento
            
        except Exception as e:
            logger.error(f"Error incrementando contador para {id_afiliado}: {str(e)}")
            raise
    
    async def obtener_contador_actual(self, id_afiliado: str, ventana_minutos: int = 1) -> int:
        """Obtiene el contador actual de eventos del afiliado"""
        try:
            key = self._generar_key(id_afiliado, ventana_minutos)
            contador = self.redis.get(key)
            return int(contador) if contador else 0
        except Exception as e:
            logger.error(f"Error obteniendo contador para {id_afiliado}: {str(e)}")
            return 0
    
    async def resetear_contador(self, id_afiliado: str) -> None:
        """Resetea el contador del afiliado (uso administrativo)"""
        try:
            pattern = f"{self.prefix}{id_afiliado}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Contadores reseteados para afiliado {id_afiliado}")
        except Exception as e:
            logger.error(f"Error reseteando contadores para {id_afiliado}: {str(e)}")
            raise
    
    def _generar_key(self, id_afiliado: str, ventana_minutos: int) -> str:
        """Genera clave Redis para la ventana temporal"""
        # Usar timestamp redondeado para crear ventanas fijas
        ahora = datetime.now()
        ventana_timestamp = int(ahora.timestamp() // (ventana_minutos * 60))
        return f"{self.prefix}{id_afiliado}:{ventana_minutos}m:{ventana_timestamp}"

class InMemoryRepositorioEventos(RepositorioEventos):
    """
    Implementación en memoria para desarrollo/testing
    """
    
    def __init__(self, ttl_horas: int = 24):
        self.eventos = {}  # hash_evento -> timestamp
        self.ttl_horas = ttl_horas
    
    async def existe_evento(self, hash_evento: str) -> bool:
        """Verifica si un evento ya fue procesado"""
        await self._limpiar_antiguos()
        return hash_evento in self.eventos
    
    async def guardar_evento_temporal(self, hash_evento: str, timestamp: datetime) -> None:
        """Guarda temporalmente un evento para deduplicación"""
        self.eventos[hash_evento] = timestamp
    
    async def limpiar_eventos_antiguos(self, max_antiguedad_horas: int = 24) -> int:
        """Limpia eventos temporales antiguos"""
        return await self._limpiar_antiguos(max_antiguedad_horas)
    
    async def _limpiar_antiguos(self, max_horas: int = None) -> int:
        """Limpia eventos antiguos"""
        max_horas = max_horas or self.ttl_horas
        limite = datetime.now() - timedelta(hours=max_horas)
        
        eventos_antiguos = [
            hash_evento for hash_evento, timestamp in self.eventos.items()
            if timestamp < limite
        ]
        
        for hash_evento in eventos_antiguos:
            del self.eventos[hash_evento]
        
        return len(eventos_antiguos)

class InMemoryRepositorioRateLimiting(RepositorioRateLimiting):
    """
    Implementación en memoria para desarrollo/testing
    """
    
    def __init__(self):
        self.contadores = {}  # key -> (contador, timestamp_ventana)
    
    async def incrementar_contador(self, id_afiliado: str, ventana_minutos: int = 1) -> int:
        """Incrementa contador de eventos para el afiliado en la ventana especificada"""
        key = self._generar_key(id_afiliado, ventana_minutos)
        ahora = datetime.now()
        ventana_timestamp = int(ahora.timestamp() // (ventana_minutos * 60))
        
        if key not in self.contadores or self.contadores[key][1] != ventana_timestamp:
            # Nueva ventana
            self.contadores[key] = (1, ventana_timestamp)
            return 1
        else:
            # Incrementar en ventana actual
            contador_actual = self.contadores[key][0] + 1
            self.contadores[key] = (contador_actual, ventana_timestamp)
            return contador_actual
    
    async def obtener_contador_actual(self, id_afiliado: str, ventana_minutos: int = 1) -> int:
        """Obtiene el contador actual de eventos del afiliado"""
        key = self._generar_key(id_afiliado, ventana_minutos)
        ahora = datetime.now()
        ventana_timestamp = int(ahora.timestamp() // (ventana_minutos * 60))
        
        if key not in self.contadores or self.contadores[key][1] != ventana_timestamp:
            return 0
        
        return self.contadores[key][0]
    
    async def resetear_contador(self, id_afiliado: str) -> None:
        """Resetea el contador del afiliado"""
        keys_a_eliminar = [key for key in self.contadores.keys() if key.startswith(f"{id_afiliado}:")]
        for key in keys_a_eliminar:
            del self.contadores[key]
    
    def _generar_key(self, id_afiliado: str, ventana_minutos: int) -> str:
        """Genera clave para la ventana temporal"""
        return f"{id_afiliado}:{ventana_minutos}m"
