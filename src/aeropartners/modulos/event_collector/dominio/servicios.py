from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from .enums import TipoEvento
from .objetos_valor import ContextoEvento, PayloadEvento

class ServicioPublicacionEventos(ABC):
    """Servicio de dominio para publicar eventos a topics de Pulsar"""
    
    @abstractmethod
    async def publicar_evento(
        self, 
        tipo_evento: TipoEvento,
        contexto: ContextoEvento,
        payload: PayloadEvento,
        metadatos: Dict[str, Any]
    ) -> str:
        """
        Publica un evento al topic correspondiente
        Retorna: ID de mensaje o confirmación de publicación
        """
        pass
    
    @abstractmethod
    def obtener_topic_destino(self, tipo_evento: TipoEvento) -> str:
        """Obtiene el nombre del topic destino para un tipo de evento"""
        pass
    
    @abstractmethod
    def generar_partition_key(self, contexto: ContextoEvento) -> str:
        """Genera la clave de partición para garantizar orden de eventos"""
        pass

class ServicioValidacionEventos:
    """Servicio de dominio para validar eventos según reglas de negocio"""
    
    def __init__(self, repo_eventos, repo_afiliados, repo_campanas, repo_rate_limiting):
        self.repo_eventos = repo_eventos
        self.repo_afiliados = repo_afiliados
        self.repo_campanas = repo_campanas  
        self.repo_rate_limiting = repo_rate_limiting
    
    async def validar_evento_completo(
        self,
        hash_evento: str,
        tipo_evento: TipoEvento,
        contexto: ContextoEvento,
        payload: PayloadEvento,
        timestamp: datetime
    ) -> Dict[str, bool]:
        """
        Ejecuta todas las validaciones de negocio para un evento
        Retorna diccionario con el resultado de cada validación
        """
        validaciones = {}
        
        # Validar deduplicación
        validaciones['no_duplicado'] = not await self.repo_eventos.existe_evento(hash_evento)
        
        # Validar afiliado activo
        validaciones['afiliado_activo'] = await self.repo_afiliados.afiliado_activo(contexto.id_afiliado)
        
        # Validar permisos del afiliado
        permisos = await self.repo_afiliados.obtener_permisos_afiliado(contexto.id_afiliado)
        validaciones['tiene_permisos'] = f"evento_{tipo_evento.value.lower()}" in (permisos or set())
        
        # Validar rate limiting
        contador_actual = await self.repo_rate_limiting.obtener_contador_actual(contexto.id_afiliado)
        limites = await self.repo_afiliados.obtener_limites_afiliado(contexto.id_afiliado)
        limite_maximo = limites.get('eventos_por_minuto', 1000)
        validaciones['dentro_rate_limit'] = contador_actual < limite_maximo
        
        # Validar campaña si se especifica
        if contexto.id_campana:
            validaciones['campana_valida'] = await self.repo_campanas.campana_existe_y_activa(contexto.id_campana)
        else:
            validaciones['campana_valida'] = True
        
        # Validaciones específicas por tipo de evento
        if tipo_evento == TipoEvento.CONVERSION:
            validaciones['conversion_valida'] = (
                payload.valor_conversion is not None and 
                payload.valor_conversion > 0 and
                payload.moneda is not None
            )
        else:
            validaciones['conversion_valida'] = True
        
        return validaciones
    
    def todas_validaciones_pasaron(self, validaciones: Dict[str, bool]) -> bool:
        """Verifica si todas las validaciones pasaron"""
        return all(validaciones.values())

class ServicioGeneracionHash:
    """Servicio de dominio para generar hashes únicos de eventos (deduplicación)"""
    
    @staticmethod
    def generar_hash_evento(
        tipo_evento: TipoEvento,
        contexto: ContextoEvento, 
        timestamp: datetime,
        datos_custom: Dict[str, Any]
    ) -> str:
        """
        Genera un hash único del evento basado en sus características inmutables
        Usado para deduplicación
        """
        import hashlib
        import json
        
        # Campos que determinan la unicidad del evento
        elementos_hash = {
            'tipo': tipo_evento.value,
            'id_afiliado': contexto.id_afiliado,
            'id_campana': contexto.id_campana,
            'id_oferta': contexto.id_oferta,
            'url': contexto.url,
            'timestamp': timestamp.isoformat(),
            'datos_custom': sorted(datos_custom.items()) if datos_custom else []
        }
        
        # Crear hash SHA-256
        contenido = json.dumps(elementos_hash, sort_keys=True)
        return hashlib.sha256(contenido.encode()).hexdigest()

class ServicioFormateadorEventos:
    """Servicio de dominio para formatear eventos según el schema de destino"""
    
    @staticmethod
    def formatear_para_tracking(
        id_evento: str,
        tipo_evento: TipoEvento,
        contexto: ContextoEvento,
        payload: PayloadEvento,
        timestamp: datetime,
        metadatos_sistema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Formatea el evento para envío al servicio de tracking
        Siguiendo el schema definido para tracking.commands.RegisterEvent.v1
        """
        return {
            'id_evento': id_evento,
            'tipo_evento': tipo_evento.value,
            'timestamp': timestamp.isoformat(),
            'contexto': {
                'id_afiliado': contexto.id_afiliado,
                'id_campana': contexto.id_campana,
                'id_oferta': contexto.id_oferta,
                'url': contexto.url,
                'parametros_tracking': contexto.parametros_tracking or {},
            },
            'payload': {
                'datos_custom': payload.datos_custom,
                'valor_conversion': payload.valor_conversion,
                'moneda': payload.moneda
            },
            'metadatos_sistema': metadatos_sistema
        }
