from abc import ABC, abstractmethod
from typing import Optional, List
from ..dominio.entidades import Saga

class RepositorioSaga(ABC):
    """Repositorio abstracto para SAGAs"""
    
    @abstractmethod
    def agregar(self, saga: Saga) -> Saga:
        """Agregar una nueva SAGA"""
        pass
    
    @abstractmethod
    def obtener_por_id(self, saga_id: str) -> Optional[Saga]:
        """Obtener una SAGA por su ID"""
        pass
    
    @abstractmethod
    def actualizar(self, saga: Saga) -> Saga:
        """Actualizar una SAGA existente"""
        pass
    
    @abstractmethod
    def eliminar(self, saga_id: str) -> bool:
        """Eliminar una SAGA"""
        pass
    
    @abstractmethod
    def obtener_por_estado(self, estado: str) -> List[Saga]:
        """Obtener SAGAs por estado"""
        pass
    
    @abstractmethod
    def obtener_pendientes(self) -> List[Saga]:
        """Obtener SAGAs pendientes de procesamiento"""
        pass
    
    @abstractmethod
    def obtener_por_tipo(self, tipo: str) -> List[Saga]:
        """Obtener SAGAs por tipo"""
        pass
    
    @abstractmethod
    def obtener_por_rango_fechas(self, fecha_inicio, fecha_fin) -> List[Saga]:
        """Obtener SAGAs por rango de fechas"""
        pass
    
    @abstractmethod
    def obtener_todas(self) -> List[Saga]:
        """Obtener todas las SAGAs"""
        pass
