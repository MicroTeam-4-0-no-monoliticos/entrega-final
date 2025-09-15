from datetime import datetime, timedelta
from typing import Optional
from ....seedwork.dominio.reglas import ReglaNegocio

class EventoDebeSerReciente(ReglaNegocio):
    """Regla: Los eventos no pueden ser anteriores a X horas"""
    
    def __init__(self, timestamp_evento: datetime, max_horas_antiguedad: int = 24):
        self.timestamp_evento = timestamp_evento
        self.max_horas_antiguedad = max_horas_antiguedad
        super().__init__(f"Evento no puede ser anterior a {max_horas_antiguedad} horas")
    
    def es_valido(self) -> bool:
        ahora = datetime.now()
        limite_antiguo = ahora - timedelta(hours=self.max_horas_antiguedad)
        return self.timestamp_evento >= limite_antiguo

class EventoDebeSerFuturoValido(ReglaNegocio):
    """Regla: Los eventos no pueden ser del futuro más allá de un margen"""
    
    def __init__(self, timestamp_evento: datetime, max_minutos_futuro: int = 5):
        self.timestamp_evento = timestamp_evento
        self.max_minutos_futuro = max_minutos_futuro
        super().__init__(f"Evento no puede ser del futuro más de {max_minutos_futuro} minutos")
    
    def es_valido(self) -> bool:
        ahora = datetime.now()
        limite_futuro = ahora + timedelta(minutes=self.max_minutos_futuro)
        return self.timestamp_evento <= limite_futuro

class AfiliadoDebeTenerPermisosEvento(ReglaNegocio):
    """Regla: El afiliado debe tener permisos para generar este tipo de evento"""
    
    def __init__(self, id_afiliado: str, tipo_evento: str, permisos_afiliado: set):
        self.id_afiliado = id_afiliado
        self.tipo_evento = tipo_evento
        self.permisos_afiliado = permisos_afiliado or set()
        super().__init__(f"Afiliado {id_afiliado} no tiene permisos para evento {tipo_evento}")
    
    def es_valido(self) -> bool:
        return f"evento_{self.tipo_evento.lower()}" in self.permisos_afiliado

class EventoNoDebeSerDuplicado(ReglaNegocio):
    """Regla: No se permite procesar eventos duplicados"""
    
    def __init__(self, hash_evento: str, hash_existente: Optional[str]):
        self.hash_evento = hash_evento
        self.hash_existente = hash_existente
        super().__init__(f"Evento duplicado detectado: {hash_evento}")
    
    def es_valido(self) -> bool:
        return self.hash_existente != self.hash_evento

class RateLimitingNoDebeExcederLimite(ReglaNegocio):
    """Regla: No se debe exceder el rate limit por afiliado"""
    
    def __init__(self, id_afiliado: str, eventos_actuales: int, limite_maximo: int):
        self.id_afiliado = id_afiliado
        self.eventos_actuales = eventos_actuales
        self.limite_maximo = limite_maximo
        super().__init__(f"Rate limit excedido para afiliado {id_afiliado}: {eventos_actuales}/{limite_maximo}")
    
    def es_valido(self) -> bool:
        return self.eventos_actuales < self.limite_maximo

class PayloadDebeSerValido(ReglaNegocio):
    """Regla: El payload debe contener los campos requeridos para el tipo de evento"""
    
    def __init__(self, tipo_evento: str, payload: dict, campos_requeridos: set):
        self.tipo_evento = tipo_evento
        self.payload = payload or {}
        self.campos_requeridos = campos_requeridos or set()
        super().__init__(f"Payload inválido para evento {tipo_evento}")
    
    def es_valido(self) -> bool:
        return all(campo in self.payload for campo in self.campos_requeridos)

class ConversionDebeSerPositiva(ReglaNegocio):
    """Regla: Los valores de conversión deben ser positivos"""
    
    def __init__(self, valor_conversion: Optional[float]):
        self.valor_conversion = valor_conversion
        super().__init__("Valor de conversión debe ser positivo")
    
    def es_valido(self) -> bool:
        if self.valor_conversion is None:
            return True  # No hay valor, no se aplica la regla
        return self.valor_conversion > 0

class CampanaDebeExistir(ReglaNegocio):
    """Regla: Si se especifica una campaña, debe existir y estar activa"""
    
    def __init__(self, id_campana: Optional[str], campana_existe: bool):
        self.id_campana = id_campana
        self.campana_existe = campana_existe
        super().__init__(f"Campaña {id_campana} no existe o no está activa")
    
    def es_valido(self) -> bool:
        if not self.id_campana:
            return True  # No hay campaña especificada, es válido
        return self.campana_existe
