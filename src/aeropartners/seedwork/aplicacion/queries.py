from functools import singledispatch
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


class Query(ABC):
    fecha_creacion: datetime = field(default_factory=datetime.now, kw_only=True)

@dataclass
class QueryResultado:
    resultado: None

class QueryHandler(ABC):
    @abstractmethod
    def handle(self, query: Query) -> QueryResultado:
        raise NotImplementedError()

@singledispatch
def ejecutar_query(query):
    raise NotImplementedError(f'No existe implementación para el query de tipo {type(query).__name__}')
