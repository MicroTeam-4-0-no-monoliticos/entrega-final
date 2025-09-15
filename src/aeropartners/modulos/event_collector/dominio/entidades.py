import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .enums import TipoEvento, EstadoEvento, FuenteEvento
from .objetos_valor import MetadatosEvento, ContextoEvento, DatosDispositivo, FirmaEvento, PayloadEvento
from .eventos import (
    EventoRecibido, EventoValidado, EventoPublicado, 
    EventoFallido, EventoDescartado, EventoLimiteProcesamiento
)
from .reglas import (
    EventoDebeSerReciente, EventoDebeSerFuturoValido, 
    AfiliadoDebeTenerPermisosEvento, EventoNoDebeSerDuplicado,
    RateLimitingNoDebeExcederLimite, PayloadDebeSerValido,
    ConversionDebeSerPositiva, CampanaDebeExistir
)
from .servicios import ServicioGeneracionHash, ServicioFormateadorEventos

class EventoTracking:
    
    def __init__(
        self,
        tipo_evento: TipoEvento,
        contexto: ContextoEvento,
        payload: PayloadEvento,
        metadatos: MetadatosEvento,
        dispositivo: DatosDispositivo,
        firma: FirmaEvento,
        id_evento: Optional[uuid.UUID] = None
    ):
        self.id = id_evento or uuid.uuid4()
        self.tipo_evento = tipo_evento
        self.contexto = contexto
        self.payload = payload
        self.metadatos = metadatos
        self.dispositivo = dispositivo
        self.firma = firma
        
        self.estado = EstadoEvento.RECIBIDO
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = datetime.now()
        
        self.hash_evento = ServicioGeneracionHash.generar_hash_evento(
            tipo_evento, contexto, metadatos.timestamp, payload.datos_custom
        )
        
        self.intentos_procesamiento = 0
        self.razon_fallo: Optional[str] = None
        self.codigo_error: Optional[str] = None
        self.topic_destino: Optional[str] = None
        self.mensaje_id_pulsar: Optional[str] = None
        
        self.eventos: List = []
        
        self.agregar_evento(EventoRecibido(
            id_evento_tracking=str(self.id),
            tipo_evento=self.tipo_evento.value,
            id_afiliado=self.contexto.id_afiliado,
            timestamp_recepcion=self.fecha_creacion,
            fuente=self.firma.fuente.value,
            ip_origen=self.metadatos.ip_origen
        ))
    
    def agregar_evento(self, evento):
        self.eventos.append(evento)
        self.fecha_actualizacion = datetime.now()
    
    def limpiar_eventos(self):
        self.eventos = []
    
    def validar_regla(self, regla):
        if not regla.es_valido():
            raise ValueError(regla.mensaje)
    
    def validar_evento(self, validaciones_resultado: Dict[str, bool]) -> bool:
        self.intentos_procesamiento += 1
        
        try:
            if not all(validaciones_resultado.values()):
                validaciones_fallidas = [
                    nombre for nombre, resultado in validaciones_resultado.items() 
                    if not resultado
                ]
                
                self.estado = EstadoEvento.DESCARTADO
                self.razon_fallo = f"Validaciones fallidas: {', '.join(validaciones_fallidas)}"
                
                self.agregar_evento(EventoDescartado(
                    id_evento_tracking=str(self.id),
                    tipo_evento=self.tipo_evento.value,
                    razon_descarte=self.razon_fallo,
                    regla_violada=validaciones_fallidas[0]
                ))
                
                return False
            
            self.estado = EstadoEvento.VALIDADO
            self.agregar_evento(EventoValidado(
                id_evento_tracking=str(self.id),
                tipo_evento=self.tipo_evento.value,
                id_afiliado=self.contexto.id_afiliado,
                validaciones_pasadas=validaciones_resultado
            ))
            
            return True
            
        except Exception as e:
            self.estado = EstadoEvento.FALLIDO
            self.razon_fallo = str(e)
            self.codigo_error = "VALIDATION_ERROR"
            
            self.agregar_evento(EventoFallido(
                id_evento_tracking=str(self.id),
                tipo_evento=self.tipo_evento.value,
                razon_fallo=self.razon_fallo,
                codigo_error=self.codigo_error,
                intentos_realizados=self.intentos_procesamiento
            ))
            
            return False
    
    def iniciar_procesamiento(self):
        if self.estado != EstadoEvento.VALIDADO:
            raise ValueError(f"No se puede procesar evento en estado {self.estado.value}")
        
        self.estado = EstadoEvento.PROCESANDO
        self.fecha_actualizacion = datetime.now()
    
    def marcar_como_publicado(
        self, 
        topic_destino: str, 
        mensaje_id: str, 
        partition_key: str
    ):
        if self.estado != EstadoEvento.PROCESANDO:
            raise ValueError(f"No se puede marcar como publicado un evento en estado {self.estado.value}")
        
        self.estado = EstadoEvento.PUBLICADO
        self.topic_destino = topic_destino
        self.mensaje_id_pulsar = mensaje_id
        self.fecha_actualizacion = datetime.now()
        
        self.agregar_evento(EventoPublicado(
            id_evento_tracking=str(self.id),
            tipo_evento=self.tipo_evento.value,
            topic_destino=topic_destino,
            partition_key=partition_key,
            timestamp_publicacion=self.fecha_actualizacion
        ))
    
    def marcar_como_fallido(self, razon: str, codigo_error: str):
        self.estado = EstadoEvento.FALLIDO
        self.razon_fallo = razon
        self.codigo_error = codigo_error
        self.fecha_actualizacion = datetime.now()
        
        self.agregar_evento(EventoFallido(
            id_evento_tracking=str(self.id),
            tipo_evento=self.tipo_evento.value,
            razon_fallo=razon,
            codigo_error=codigo_error,
            intentos_realizados=self.intentos_procesamiento
        ))
    
    def obtener_datos_para_publicacion(self) -> Dict[str, Any]:
        metadatos_sistema = {
            'hash_evento': self.hash_evento,
            'fuente': self.firma.fuente.value,
            'ip_origen': self.metadatos.ip_origen,
            'user_agent': self.metadatos.user_agent,
            'session_id': self.metadatos.session_id,
            'referrer': self.metadatos.referrer,
            'dispositivo': {
                'tipo': self.dispositivo.tipo.value,
                'identificador': self.dispositivo.identificador,
                'so': self.dispositivo.so,
                'navegador': self.dispositivo.navegador,
                'resolucion': self.dispositivo.resolucion
            }
        }
        
        return ServicioFormateadorEventos.formatear_para_tracking(
            id_evento=str(self.id),
            tipo_evento=self.tipo_evento,
            contexto=self.contexto,
            payload=self.payload,
            timestamp=self.metadatos.timestamp,
            metadatos_sistema=metadatos_sistema
        )
    
    def puede_ser_reintentado(self, max_intentos: int = 3) -> bool:
        return (
            self.estado == EstadoEvento.FALLIDO and 
            self.intentos_procesamiento < max_intentos
        )
    
    def es_evento_critico(self) -> bool:
        return (
            self.tipo_evento == TipoEvento.CONVERSION and 
            self.payload.valor_conversion is not None and 
            self.payload.valor_conversion > 0
        )