import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from ....seedwork.dominio.entidades import AgregacionRaiz

class EstadoSaga(Enum):
    INICIADA = "INICIADA"
    CAMPAÑA_CREADA = "CAMPAÑA_CREADA"
    PAGO_PROCESADO = "PAGO_PROCESADO"
    REPORTE_GENERADO = "REPORTE_GENERADO"
    COMPLETADA = "COMPLETADA"
    FALLIDA = "FALLIDA"
    COMPENSANDO = "COMPENSANDO"
    COMPENSADA = "COMPENSADA"

class TipoPaso(Enum):
    CREAR_CAMPAÑA = "CREAR_CAMPAÑA"
    PROCESAR_PAGO = "PROCESAR_PAGO"
    GENERAR_REPORTE = "GENERAR_REPORTE"
    COMPENSAR_CAMPAÑA = "COMPENSAR_CAMPAÑA"
    REVERTIR_PAGO = "REVERTIR_PAGO"
    CANCELAR_REPORTE = "CANCELAR_REPORTE"

class Paso:
    def __init__(self, tipo: TipoPaso, datos: Dict[str, Any], 
                 resultado: Optional[Dict[str, Any]] = None, 
                 compensacion: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())
        self.tipo = tipo
        self.datos = datos
        self.resultado = resultado
        self.compensacion = compensacion
        self.fecha_ejecucion = datetime.now()
        self.exitoso = False
        self.error = None

    def marcar_exitoso(self, resultado: Dict[str, Any]):
        self.exitoso = True
        self.resultado = resultado

    def marcar_fallido(self, error: str):
        self.exitoso = False
        self.error = error

    def agregar_compensacion(self, compensacion: Dict[str, Any]):
        self.compensacion = compensacion

class Saga:
    def __init__(self, tipo: str, datos_iniciales: Dict[str, Any]):
        self.id = uuid.uuid4()
        self.tipo = tipo
        self.datos_iniciales = datos_iniciales
        self.estado = EstadoSaga.INICIADA
        self.pasos: List[Paso] = []
        self.compensaciones: List[Paso] = []
        self.fecha_inicio = datetime.now()
        self.fecha_fin: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.eventos: List = []  # Para compatibilidad con AgregacionRaiz

    def agregar_paso(self, tipo: TipoPaso, datos: Dict[str, Any]) -> Paso:
        paso = Paso(tipo, datos)
        self.pasos.append(paso)
        return paso

    def marcar_paso_exitoso(self, paso_id: str, resultado: Dict[str, Any]):
        paso = self._buscar_paso_por_id(paso_id)
        if paso:
            paso.marcar_exitoso(resultado)
            self._actualizar_estado()

    def marcar_paso_fallido(self, paso_id: str, error: str):
        paso = self._buscar_paso_por_id(paso_id)
        if paso:
            paso.marcar_fallido(error)
            self.estado = EstadoSaga.FALLIDA
            self.error_message = error

    def agregar_compensacion(self, tipo: TipoPaso, datos: Dict[str, Any]) -> Paso:
        compensacion = Paso(tipo, datos)
        self.compensaciones.append(compensacion)
        return compensacion

    def marcar_compensacion_exitosa(self, compensacion_id: str, resultado: Dict[str, Any]):
        compensacion = self._buscar_compensacion_por_id(compensacion_id)
        if compensacion:
            compensacion.marcar_exitoso(resultado)

    def marcar_compensacion_fallida(self, compensacion_id: str, error: str):
        compensacion = self._buscar_compensacion_por_id(compensacion_id)
        if compensacion:
            compensacion.marcar_fallido(error)

    def _buscar_paso_por_id(self, paso_id: str) -> Optional[Paso]:
        return next((p for p in self.pasos if p.id == paso_id), None)

    def _buscar_compensacion_por_id(self, compensacion_id: str) -> Optional[Paso]:
        return next((c for c in self.compensaciones if c.id == compensacion_id), None)

    def _actualizar_estado(self):
        if not self.pasos:
            return

        # Verificar si todos los pasos están completos
        pasos_exitosos = [p for p in self.pasos if p.exitoso]
        
        if len(pasos_exitosos) == len(self.pasos):
            if len(self.pasos) == 1:
                self.estado = EstadoSaga.CAMPAÑA_CREADA
            elif len(self.pasos) == 2:
                self.estado = EstadoSaga.PAGO_PROCESADO
            elif len(self.pasos) == 3:
                self.estado = EstadoSaga.REPORTE_GENERADO
                self.estado = EstadoSaga.COMPLETADA
                self.fecha_fin = datetime.now()

    def iniciar_compensacion(self):
        self.estado = EstadoSaga.COMPENSANDO

    def completar_compensacion(self):
        self.estado = EstadoSaga.COMPENSADA
        self.fecha_fin = datetime.now()

    def obtener_pasos_pendientes(self) -> List[Paso]:
        return [p for p in self.pasos if not p.exitoso and not p.error]

    def obtener_compensaciones_pendientes(self) -> List[Paso]:
        return [c for c in self.compensaciones if not c.exitoso and not c.error]

    def es_completa(self) -> bool:
        return self.estado == EstadoSaga.COMPLETADA

    def es_fallida(self) -> bool:
        return self.estado == EstadoSaga.FALLIDA

    def necesita_compensacion(self) -> bool:
        return self.estado == EstadoSaga.FALLIDA and len(self.pasos) > 0
