from abc import ABC, abstractmethod
from typing import Optional
import uuid
from .entidades import Pago

class RepositorioPagos(ABC):
    @abstractmethod
    def obtener_por_id(self, id: uuid.UUID) -> Optional[Pago]:
        raise NotImplementedError()

    @abstractmethod
    def obtener_por_referencia(self, referencia: str) -> Optional[Pago]:
        raise NotImplementedError()

    @abstractmethod
    def agregar(self, pago: Pago):
        raise NotImplementedError()

    @abstractmethod
    def actualizar(self, pago: Pago):
        raise NotImplementedError()

    @abstractmethod
    def eliminar(self, pago: Pago):
        raise NotImplementedError()
    
    @abstractmethod
    def obtener_todos(self):
        raise NotImplementedError()