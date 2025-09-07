"""Mapeadores entre entidades de dominio y modelos de base de datos"""

from typing import Optional
from ..dominio.entidades import Pago, EstadoPago
from ..dominio.objetos_valor import Dinero, Moneda
from .modelos import PagoModel

class MapeadorPago:
    """Mapeador entre la entidad Pago y el modelo de base de datos"""
    
    def entidad_a_dto(self, modelo: PagoModel) -> Optional[Pago]:
        if modelo is None:
            return None
        
        dinero = Dinero(modelo.monto, Moneda(modelo.moneda))
        
        return Pago(
            id=modelo.id,
            id_afiliado=modelo.id_afiliado,
            monto=dinero,
            estado=EstadoPago(modelo.estado),
            referencia_pago=modelo.referencia_pago,
            fecha_creacion=modelo.fecha_creacion,
            fecha_actualizacion=modelo.fecha_actualizacion,
            fecha_procesamiento=modelo.fecha_procesamiento,
            mensaje_error=modelo.mensaje_error
        )
    
    def dto_a_entidad(self, entidad: Pago) -> PagoModel:
        return PagoModel(
            id=entidad.id,
            id_afiliado=entidad.id_afiliado,
            monto=entidad.monto.monto,
            moneda=entidad.monto.moneda.value,
            estado=entidad.estado.value,
            referencia_pago=entidad.referencia_pago,
            fecha_creacion=entidad.fecha_creacion,
            fecha_actualizacion=entidad.fecha_actualizacion,
            fecha_procesamiento=entidad.fecha_procesamiento,
            mensaje_error=entidad.mensaje_error
        )
