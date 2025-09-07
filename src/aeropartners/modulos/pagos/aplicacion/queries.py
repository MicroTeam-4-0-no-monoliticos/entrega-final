"""Queries de la aplicación de pagos"""

from dataclasses import dataclass
import uuid
from ....seedwork.aplicacion.queries import Query

@dataclass
class ObtenerEstadoPagoQuery(Query):
    id_pago: uuid.UUID
