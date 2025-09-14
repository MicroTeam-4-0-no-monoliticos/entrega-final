from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from .entidades import Campana

class RepositorioCampanas(ABC):
    """Puerto para el repositorio de campañas"""
    
    @abstractmethod
    def agregar(self, campana: Campana) -> None:
        """Agregar una nueva campaña"""
        pass
    
    @abstractmethod
    def actualizar(self, campana: Campana) -> None:
        """Actualizar una campaña existente"""
        pass
    
    @abstractmethod
    def obtener_por_id(self, id_campana: uuid.UUID) -> Optional[Campana]:
        """Obtener una campaña por su ID"""
        pass
    
    @abstractmethod
    def obtener_por_afiliado(self, id_afiliado: str, limit: int = 50, offset: int = 0) -> List[Campana]:
        """Obtener campañas de un afiliado específico"""
        pass
    
    @abstractmethod
    def listar(self, limit: int = 50, offset: int = 0) -> List[Campana]:
        """Listar todas las campañas con paginación"""
        pass
    
    @abstractmethod
    def eliminar(self, id_campana: uuid.UUID) -> bool:
        """Eliminar una campaña por su ID"""
        pass
