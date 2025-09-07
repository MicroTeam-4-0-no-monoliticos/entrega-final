"""Reglas de negocio reusables parte del seedwork del proyecto

En este archivo usted encontrará las reglas de negocio reusables parte del seedwork del proyecto

"""

from abc import ABC, abstractmethod

class ReglaNegocio(ABC):
    __mensaje: str = ""

    def __init__(self, mensaje):
        self.__mensaje = mensaje

    def mensaje(self) -> str:
        return self.__mensaje

    @abstractmethod
    def es_valido(self) -> bool:
        ...

class IdEntidadEsInmutable(ReglaNegocio):
    __entidad: 'Entidad'

    def __init__(self, entidad):
        super().__init__("El identificador de la entidad debe ser inmutable")
        self.__entidad = entidad

    def es_valido(self) -> bool:
        return self.__entidad._id is None
