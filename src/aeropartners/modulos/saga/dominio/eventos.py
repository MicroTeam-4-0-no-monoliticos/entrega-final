from datetime import datetime
from typing import Dict, Any, Optional
from ....seedwork.dominio.eventos import EventoDominio

class SagaIniciada(EventoDominio):
    def __init__(self, saga_id: str, tipo: str, datos_iniciales: Dict[str, Any]):
        super().__init__()
        self.saga_id = saga_id
        self.tipo = tipo
        self.datos_iniciales = datos_iniciales
        self.fecha_evento = datetime.now()

class SagaCampañaCreada(EventoDominio):
    def __init__(self, saga_id: str, campana_id: str, datos_campana: Dict[str, Any]):
        super().__init__()
        self.saga_id = saga_id
        self.campana_id = campana_id
        self.datos_campana = datos_campana
        self.fecha_evento = datetime.now()

class SagaPagoProcesado(EventoDominio):
    def __init__(self, saga_id: str, pago_id: str, datos_pago: Dict[str, Any]):
        super().__init__()
        self.saga_id = saga_id
        self.pago_id = pago_id
        self.datos_pago = datos_pago
        self.fecha_evento = datetime.now()

class SagaReporteGenerado(EventoDominio):
    def __init__(self, saga_id: str, reporte_id: str, datos_reporte: Dict[str, Any]):
        super().__init__()
        self.saga_id = saga_id
        self.reporte_id = reporte_id
        self.datos_reporte = datos_reporte
        self.fecha_evento = datetime.now()

class SagaCompletada(EventoDominio):
    def __init__(self, saga_id: str, resultado_final: Dict[str, Any]):
        super().__init__()
        self.saga_id = saga_id
        self.resultado_final = resultado_final
        self.fecha_evento = datetime.now()

class SagaFallida(EventoDominio):
    def __init__(self, saga_id: str, error: str, paso_fallido: str):
        super().__init__()
        self.saga_id = saga_id
        self.error = error
        self.paso_fallido = paso_fallido
        self.fecha_evento = datetime.now()

class SagaCompensacionIniciada(EventoDominio):
    def __init__(self, saga_id: str, paso_a_compensar: str):
        super().__init__()
        self.saga_id = saga_id
        self.paso_a_compensar = paso_a_compensar
        self.fecha_evento = datetime.now()

class SagaCompensacionCompletada(EventoDominio):
    def __init__(self, saga_id: str, compensacion_id: str, resultado: Dict[str, Any]):
        super().__init__()
        self.saga_id = saga_id
        self.compensacion_id = compensacion_id
        self.resultado = resultado
        self.fecha_evento = datetime.now()

class SagaCompensacionFallida(EventoDominio):
    def __init__(self, saga_id: str, compensacion_id: str, error: str):
        super().__init__()
        self.saga_id = saga_id
        self.compensacion_id = compensacion_id
        self.error = error
        self.fecha_evento = datetime.now()

class SagaTimeout(EventoDominio):
    def __init__(self, saga_id: str, timeout_minutos: int):
        super().__init__()
        self.saga_id = saga_id
        self.timeout_minutos = timeout_minutos
        self.fecha_evento = datetime.now()

class SagaPasoEjecutado(EventoDominio):
    def __init__(self, saga_id: str, paso_id: str, tipo_paso: str, 
                 datos: Dict[str, Any], resultado: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None):
        super().__init__()
        self.saga_id = saga_id
        self.paso_id = paso_id
        self.tipo_paso = tipo_paso
        self.datos = datos
        self.resultado = resultado
        self.error = error
        self.fecha_evento = datetime.now()

class SagaCompensacionEjecutada(EventoDominio):
    def __init__(self, saga_id: str, compensacion_id: str, tipo_compensacion: str,
                 datos: Dict[str, Any], resultado: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None):
        super().__init__()
        self.saga_id = saga_id
        self.compensacion_id = compensacion_id
        self.tipo_compensacion = tipo_compensacion
        self.datos = datos
        self.resultado = resultado
        self.error = error
        self.fecha_evento = datetime.now()
