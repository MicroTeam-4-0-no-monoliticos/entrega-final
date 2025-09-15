from enum import Enum

class TipoEvento(Enum):
    """Tipos de eventos que puede procesar el BFF"""
    CLICK = "CLICK"
    IMPRESSION = "IMPRESSION"
    CONVERSION = "CONVERSION"
    PAGE_VIEW = "PAGE_VIEW"

class EstadoEvento(Enum):
    """Estados del ciclo de vida de un evento en el BFF"""
    RECIBIDO = "RECIBIDO"
    VALIDADO = "VALIDADO"
    PROCESANDO = "PROCESANDO"
    PUBLICADO = "PUBLICADO"
    FALLIDO = "FALLIDO"
    DESCARTADO = "DESCARTADO"

class TipoDispositivo(Enum):
    """Tipos de dispositivo desde donde se origina el evento"""
    DESKTOP = "DESKTOP"
    MOBILE = "MOBILE"
    TABLET = "TABLET"
    OTHER = "OTHER"

class FuenteEvento(Enum):
    """Fuentes posibles para los eventos de tracking"""
    WEB_TAG = "WEB_TAG"
    MOBILE_SDK = "MOBILE_SDK"
    API_DIRECT = "API_DIRECT"
    WEBHOOK = "WEBHOOK"
