from dataclasses import dataclass, field
import uuid
from datetime import datetime

from .objetos_valor import Dinero, Moneda
from .eventos import PagoExitoso, PagoFallido
from .enums import EstadoPago
from .reglas import PagoNoPuedeSerProcesadoSiYaEstaProcesando, PagoNoPuedeSerProcesadoSiYaEstaExitoso, PagoNoPuedeSerProcesadoSiYaEstaFallido

class Pago:
    def __init__(self, id_afiliado: str, monto: Dinero, referencia_pago: str = None):
        self.id = uuid.uuid4()
        self.id_afiliado = id_afiliado
        self.monto = monto
        self.estado = EstadoPago.PENDIENTE
        self.referencia_pago = referencia_pago or str(uuid.uuid4())
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = datetime.now()
        self.fecha_procesamiento = None
        self.mensaje_error = None
        self.eventos = []

    def agregar_evento(self, evento):
        self.eventos.append(evento)
    
    def limpiar_eventos(self):
        self.eventos = []
    
    def validar_regla(self, regla):
        if not regla.es_valido():
            raise Exception(regla.mensaje)

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
