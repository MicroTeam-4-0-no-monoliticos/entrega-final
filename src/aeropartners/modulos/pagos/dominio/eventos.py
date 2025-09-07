from datetime import datetime
import uuid

class PagoExitoso:
    def __init__(self, id_pago: str, id_afiliado: str, monto: float, moneda: str, referencia_pago: str):
        self.id = uuid.uuid4()
        self.fecha_evento = datetime.now()
        self.id_pago = id_pago
        self.id_afiliado = id_afiliado
        self.monto = monto
        self.moneda = moneda
        self.referencia_pago = referencia_pago

class PagoFallido:
    def __init__(self, id_pago: str, id_afiliado: str, monto: float, moneda: str, referencia_pago: str, mensaje_error: str):
        self.id = uuid.uuid4()
        self.fecha_evento = datetime.now()
        self.id_pago = id_pago
        self.id_afiliado = id_afiliado
        self.monto = monto
        self.moneda = moneda
        self.referencia_pago = referencia_pago
        self.mensaje_error = mensaje_error