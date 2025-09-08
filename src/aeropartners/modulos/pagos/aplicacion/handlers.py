from typing import Optional
from ....seedwork.aplicacion.comandos import ComandoHandler
from ....seedwork.aplicacion.queries import QueryHandler, QueryResultado
from ....seedwork.dominio.objetos_valor import Dinero, Moneda
from ..dominio.entidades import Pago
from ..dominio.eventos import PagoPendiente
from ..dominio.repositorios import RepositorioPagos
from ..dominio.servicios import PasarelaDePagos
from .comandos import ProcesarPagoCommand
from .queries import ObtenerEstadoPagoQuery
from sqlalchemy.orm import Session

class ProcesarPagoHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioPagos, pasarela: PasarelaDePagos):
        self.repositorio = repositorio
        self.pasarela = pasarela

    def handle(self, comando: ProcesarPagoCommand):
        # Crear el agregado Pago en estado PENDIENTE
        dinero = Dinero(comando.monto, Moneda(comando.moneda))
        pago = Pago(
            id_afiliado=comando.id_afiliado,
            monto=dinero,
            referencia_pago=comando.referencia_pago
        )
        
        # NO procesar el pago aquí, solo crear el evento para Pulsar
        pago.agregar_evento(PagoPendiente(
            id_pago=str(pago.id),
            id_afiliado=pago.id_afiliado,
            monto=pago.monto.monto,
            moneda=pago.monto.moneda.value,
            referencia_pago=pago.referencia_pago
        ))
        
        # Persistir el pago y sus eventos
        self.repositorio.agregar(pago)
        
        return pago

class ObtenerEstadoPagoHandler(QueryHandler):
    def __init__(self, repositorio: RepositorioPagos):
        self.repositorio = repositorio

    def handle(self, query: ObtenerEstadoPagoQuery) -> QueryResultado:
        pago = self.repositorio.obtener_por_id(query.id_pago)
        
        if pago is None:
            return QueryResultado(resultado=None)
        
        resultado = {
            "id": str(pago.id),
            "id_afiliado": pago.id_afiliado,
            "monto": pago.monto.monto,
            "moneda": pago.monto.moneda.value,
            "estado": pago.estado.value,
            "referencia_pago": pago.referencia_pago,
            "fecha_creacion": pago.fecha_creacion.isoformat(),
            "fecha_procesamiento": pago.fecha_procesamiento.isoformat() if pago.fecha_procesamiento else None,
            "mensaje_error": pago.mensaje_error
        }
        
        return QueryResultado(resultado=resultado)
