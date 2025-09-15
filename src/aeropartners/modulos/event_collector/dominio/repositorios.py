from abc import ABC, abstractmethod
from typing import Optional, Set, Dict, Any
from datetime import datetime

class RepositorioEventos(ABC):
    """Repositorio para gestionar el estado temporal de eventos en procesamiento"""
    
    @abstractmethod
    async def existe_evento(self, hash_evento: str) -> bool:
        """Verifica si un evento ya fue procesado (deduplicación)"""
        pass
    
    @abstractmethod
    async def guardar_evento_temporal(self, hash_evento: str, timestamp: datetime) -> None:
        """Guarda temporalmente un evento para deduplicación"""
        pass
    
    @abstractmethod
    async def limpiar_eventos_antiguos(self, max_antiguedad_horas: int = 24) -> int:
        """Limpia eventos temporales antiguos para gestión de memoria"""
        pass

class RepositorioAfiliados(ABC):
    """Repositorio para consultar información de afiliados"""
    
    @abstractmethod
    async def obtener_permisos_afiliado(self, id_afiliado: str) -> Optional[Set[str]]:
        """Obtiene los permisos de tracking del afiliado"""
        pass
    
    @abstractmethod
    async def obtener_limites_afiliado(self, id_afiliado: str) -> Dict[str, Any]:
        """Obtiene los límites de rate limiting del afiliado"""
        pass
    
    @abstractmethod
    async def afiliado_activo(self, id_afiliado: str) -> bool:
        """Verifica si el afiliado está activo"""
        pass

class RepositorioCampanas(ABC):
    """Repositorio para consultar información de campañas"""
    
    @abstractmethod
    async def campana_existe_y_activa(self, id_campana: str) -> bool:
        """Verifica si la campaña existe y está activa"""
        pass

class RepositorioRateLimiting(ABC):
    """Repositorio para gestionar rate limiting"""
    
    @abstractmethod
    async def incrementar_contador(self, id_afiliado: str, ventana_minutos: int = 1) -> int:
        """Incrementa contador de eventos para el afiliado en la ventana especificada"""
        pass
    
    @abstractmethod
    async def obtener_contador_actual(self, id_afiliado: str, ventana_minutos: int = 1) -> int:
        """Obtiene el contador actual de eventos del afiliado"""
        pass
    
    @abstractmethod
    async def resetear_contador(self, id_afiliado: str) -> None:
        """Resetea el contador del afiliado (uso administrativo)"""
        pass
