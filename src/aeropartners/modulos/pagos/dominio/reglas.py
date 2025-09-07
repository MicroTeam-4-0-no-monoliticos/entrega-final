from ....seedwork.dominio.reglas import ReglaNegocio
from .enums import EstadoPago

class PagoNoPuedeSerProcesadoSiYaEstaProcesando(ReglaNegocio):
    def __init__(self, pago):
        super().__init__("Un pago no puede ser procesado si ya está en estado procesando")
        self.pago = pago

    def es_valido(self) -> bool:
        return self.pago.estado != EstadoPago.PROCESANDO

class PagoNoPuedeSerProcesadoSiYaEstaExitoso(ReglaNegocio):
    def __init__(self, pago):
        super().__init__("Un pago no puede ser procesado si ya está exitoso")
        self.pago = pago

    def es_valido(self) -> bool:
        return self.pago.estado != EstadoPago.EXITOSO

class PagoNoPuedeSerProcesadoSiYaEstaFallido(ReglaNegocio):
    def __init__(self, pago):
        super().__init__("Un pago no puede ser procesado si ya está fallido")
        self.pago = pago

    def es_valido(self) -> bool:
        return self.pago.estado != EstadoPago.FALLIDO
