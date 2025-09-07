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
        
        pago = Pago(
            id_afiliado=modelo.id_afiliado,
            monto=dinero,
            referencia_pago=modelo.referencia_pago
        )
        pago.id = modelo.id
        pago.estado = EstadoPago(modelo.estado)
        pago.fecha_creacion = modelo.fecha_creacion
        pago.fecha_actualizacion = modelo.fecha_actualizacion
        pago.fecha_procesamiento = modelo.fecha_procesamiento
        pago.mensaje_error = modelo.mensaje_error
        return pago
    
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
