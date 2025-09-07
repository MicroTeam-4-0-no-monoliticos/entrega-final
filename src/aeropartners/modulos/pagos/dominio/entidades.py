"""Entidades del dominio de pagos"""

from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

from ....seedwork.dominio.entidades import AgregacionRaiz
from ....seedwork.dominio.objetos_valor import Dinero, Moneda
from .eventos import PagoExitoso, PagoFallido
from .reglas import PagoNoPuedeSerProcesadoSiYaEstaProcesando, PagoNoPuedeSerProcesadoSiYaEstaExitoso, PagoNoPuedeSerProcesadoSiYaEstaFallido

class EstadoPago(Enum):
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    EXITOSO = "EXITOSO"
    FALLIDO = "FALLIDO"

@dataclass
class Pago(AgregacionRaiz):
    id_afiliado: str
    monto: Dinero
    estado: EstadoPago = field(default=EstadoPago.PENDIENTE)
    referencia_pago: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_procesamiento: datetime = field(default=None)
    mensaje_error: str = field(default=None)

    def procesar(self, pasarela_pagos):
        """Procesa el pago a través de la pasarela de pagos"""
        # Validar reglas de negocio
        self.validar_regla(PagoNoPuedeSerProcesadoSiYaEstaProcesando(self))
        self.validar_regla(PagoNoPuedeSerProcesadoSiYaEstaExitoso(self))
        self.validar_regla(PagoNoPuedeSerProcesadoSiYaEstaFallido(self))
        
        # Cambiar estado a procesando
        self.estado = EstadoPago.PROCESANDO
        self.fecha_procesamiento = datetime.now()
        
        try:
            # Llamar a la pasarela de pagos
            resultado = pasarela_pagos.procesar_pago(
                referencia=self.referencia_pago,
                monto=self.monto.monto,
                moneda=self.monto.moneda.value,
                id_afiliado=self.id_afiliado
            )
            
            if resultado.exitoso:
                self.estado = EstadoPago.EXITOSO
                self.agregar_evento(PagoExitoso(
                    id_pago=self.id,
                    id_afiliado=self.id_afiliado,
                    monto=self.monto.monto,
                    moneda=self.monto.moneda.value,
                    referencia_pago=self.referencia_pago
                ))
            else:
                self.estado = EstadoPago.FALLIDO
                self.mensaje_error = resultado.mensaje_error
                self.agregar_evento(PagoFallido(
                    id_pago=self.id,
                    id_afiliado=self.id_afiliado,
                    monto=self.monto.monto,
                    moneda=self.monto.moneda.value,
                    referencia_pago=self.referencia_pago,
                    mensaje_error=resultado.mensaje_error
                ))
                
        except Exception as e:
            self.estado = EstadoPago.FALLIDO
            self.mensaje_error = str(e)
            self.agregar_evento(PagoFallido(
                id_pago=self.id,
                id_afiliado=self.id_afiliado,
                monto=self.monto.monto,
                moneda=self.monto.moneda.value,
                referencia_pago=self.referencia_pago,
                mensaje_error=str(e)
            ))
