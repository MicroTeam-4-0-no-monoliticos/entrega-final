"""Excepciones de dominio reusables parte del seedwork del proyecto

En este archivo usted encontrará las excepciones de dominio reusables parte del seedwork del proyecto

"""

class ReglaNegocioExcepcion(Exception):
    def __init__(self, mensaje):
        self.__mensaje = mensaje
        super().__init__(self.__mensaje)

    @property
    def mensaje(self) -> str:
        return self.__mensaje

class IdDebeSerInmutableExcepcion(ReglaNegocioExcepcion):
    def __init__(self):
        super().__init__("El identificador de la entidad debe ser inmutable")
