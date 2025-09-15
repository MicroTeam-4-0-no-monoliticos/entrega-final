import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from src.aeropartners.modulos.event_collector.dominio.entidades import EventoTracking
from src.aeropartners.modulos.event_collector.dominio.enums import (
    TipoEvento, EstadoEvento, TipoDispositivo, FuenteEvento
)
from src.aeropartners.modulos.event_collector.dominio.objetos_valor import (
    MetadatosEvento, ContextoEvento, DatosDispositivo, FirmaEvento, PayloadEvento
)
from src.aeropartners.modulos.event_collector.dominio.eventos import (
    EventoRecibido, EventoValidado, EventoDescartado, EventoFallido, EventoPublicado
)


class TestEventoTracking:
    
    @pytest.fixture
    def metadatos_validos(self):
        return MetadatosEvento(
            ip_origen="192.168.1.1",
            user_agent="Mozilla/5.0 (Test Browser)",
            timestamp=datetime.now(),
            session_id="session-123",
            referrer="https://google.com"
        )
    
    @pytest.fixture
    def contexto_valido(self):
        return ContextoEvento(
            id_afiliado="AFILIADO_001",
            id_campana=str(uuid.uuid4()),
            id_oferta="OFERTA_001",
            url="https://example.com/landing",
            parametros_tracking={"utm_source": "google", "utm_medium": "cpc"}
        )
    
    @pytest.fixture
    def dispositivo_valido(self):
        return DatosDispositivo(
            tipo=TipoDispositivo.DESKTOP,
            identificador="device-123",
            so="Windows 10",
            navegador="Chrome 91",
            resolucion="1920x1080"
        )
    
    @pytest.fixture
    def firma_valida(self):
        return FirmaEvento(
            fuente=FuenteEvento.WEB_TAG,
            hash_validacion="hash-123"
        )
    
    @pytest.fixture
    def payload_valido(self):
        return PayloadEvento(
            datos_custom={"producto_id": "P123", "categoria": "electronica"},
            valor_conversion=25.99,
            moneda="USD"
        )
    
    @pytest.fixture
    def evento_tracking(self, metadatos_validos, contexto_valido, dispositivo_valido, 
                        firma_valida, payload_valido):
        return EventoTracking(
            tipo_evento=TipoEvento.CLICK,
            contexto=contexto_valido,
            payload=payload_valido,
            metadatos=metadatos_validos,
            dispositivo=dispositivo_valido,
            firma=firma_valida
        )
    
    def test_creacion_evento_tracking_exitosa(self, evento_tracking):
        assert evento_tracking.id is not None
        assert isinstance(evento_tracking.id, uuid.UUID)
        assert evento_tracking.tipo_evento == TipoEvento.CLICK
        assert evento_tracking.estado == EstadoEvento.RECIBIDO
        assert evento_tracking.fecha_creacion is not None
        assert evento_tracking.intentos_procesamiento == 0
        assert evento_tracking.hash_evento is not None
        
        assert len(evento_tracking.eventos) == 1
        assert isinstance(evento_tracking.eventos[0], EventoRecibido)
    
    def test_creacion_con_id_personalizado(self, metadatos_validos, contexto_valido, 
                                          dispositivo_valido, firma_valida, payload_valido):
        id_custom = uuid.uuid4()
        evento = EventoTracking(
            id_evento=id_custom,
            tipo_evento=TipoEvento.IMPRESSION,
            contexto=contexto_valido,
            payload=payload_valido,
            metadatos=metadatos_validos,
            dispositivo=dispositivo_valido,
            firma=firma_valida
        )
        
        assert evento.id == id_custom
        assert evento.tipo_evento == TipoEvento.IMPRESSION
    
    def test_validacion_evento_exitosa(self, evento_tracking):
        validaciones = {
            "afiliado_activo": True,
            "tiene_permisos": True,
            "campana_valida": True,
            "rate_limit_ok": True
        }
        
        resultado = evento_tracking.validar_evento(validaciones)
        
        assert resultado is True
        assert evento_tracking.estado == EstadoEvento.VALIDADO
        assert evento_tracking.intentos_procesamiento == 1
        
        eventos_validados = [e for e in evento_tracking.eventos if isinstance(e, EventoValidado)]
        assert len(eventos_validados) == 1
    
    def test_validacion_evento_fallida(self, evento_tracking):
        validaciones = {
            "afiliado_activo": False,
            "tiene_permisos": True,
            "campana_valida": False
        }
        
        resultado = evento_tracking.validar_evento(validaciones)
        
        assert resultado is False
        assert evento_tracking.estado == EstadoEvento.DESCARTADO
        assert "afiliado_activo" in evento_tracking.razon_fallo
        assert "campana_valida" in evento_tracking.razon_fallo
        
        eventos_descartados = [e for e in evento_tracking.eventos if isinstance(e, EventoDescartado)]
        assert len(eventos_descartados) == 1
    
    def test_iniciar_procesamiento_exitoso(self, evento_tracking):
        evento_tracking.validar_evento({"test": True})
        
        evento_tracking.iniciar_procesamiento()
        
        assert evento_tracking.estado == EstadoEvento.PROCESANDO
    
    def test_iniciar_procesamiento_estado_invalido(self, evento_tracking):
        with pytest.raises(ValueError, match="No se puede procesar evento en estado"):
            evento_tracking.iniciar_procesamiento()
    
    def test_marcar_como_publicado(self, evento_tracking):
        evento_tracking.validar_evento({"test": True})
        evento_tracking.iniciar_procesamiento()
        
        topic = "tracking.clicks"
        mensaje_id = "msg-123"
        partition_key = "partition-1"
        
        evento_tracking.marcar_como_publicado(topic, mensaje_id, partition_key)
        
        assert evento_tracking.estado == EstadoEvento.PUBLICADO
        assert evento_tracking.topic_destino == topic
        assert evento_tracking.mensaje_id_pulsar == mensaje_id
        
        eventos_publicados = [e for e in evento_tracking.eventos if isinstance(e, EventoPublicado)]
        assert len(eventos_publicados) == 1
        assert eventos_publicados[0].topic_destino == topic
    
    def test_marcar_como_publicado_estado_invalido(self, evento_tracking):
        with pytest.raises(ValueError, match="No se puede marcar como publicado"):
            evento_tracking.marcar_como_publicado("topic", "msg", "key")
    
    def test_marcar_como_fallido(self, evento_tracking):
        razon = "Error de conexión"
        codigo = "CONN_ERROR"
        
        evento_tracking.marcar_como_fallido(razon, codigo)
        
        assert evento_tracking.estado == EstadoEvento.FALLIDO
        assert evento_tracking.razon_fallo == razon
        assert evento_tracking.codigo_error == codigo
        
        eventos_fallidos = [e for e in evento_tracking.eventos if isinstance(e, EventoFallido)]
        assert len(eventos_fallidos) == 1
        assert eventos_fallidos[0].razon_fallo == razon
    
    def test_puede_ser_reintentado(self, evento_tracking):
        assert not evento_tracking.puede_ser_reintentado()
        
        evento_tracking.marcar_como_fallido("Error", "ERR_001")
        assert evento_tracking.puede_ser_reintentado()
        
        evento_tracking.intentos_procesamiento = 5
        assert not evento_tracking.puede_ser_reintentado(max_intentos=3)
    
    def test_es_evento_critico(self, evento_tracking):
        assert not evento_tracking.es_evento_critico()
        
        evento_tracking.tipo_evento = TipoEvento.CONVERSION
        assert evento_tracking.es_evento_critico()
        
        evento_tracking.payload = PayloadEvento(datos_custom={})
        assert not evento_tracking.es_evento_critico()
    
    def test_obtener_datos_para_publicacion(self, evento_tracking):
        datos = evento_tracking.obtener_datos_para_publicacion()
        
        assert "id_evento" in datos
        assert "tipo_evento" in datos
        assert "contexto" in datos
        assert "payload" in datos
        assert "timestamp" in datos
        assert "metadatos_sistema" in datos
        
        metadatos = datos["metadatos_sistema"]
        assert "hash_evento" in metadatos
        assert "dispositivo" in metadatos
        assert metadatos["fuente"] == "WEB_TAG"
    
    def test_limpieza_eventos(self, evento_tracking):
        assert len(evento_tracking.eventos) == 1
        
        evento_tracking.limpiar_eventos()
        
        assert len(evento_tracking.eventos) == 0
    
    def test_agregar_evento(self, evento_tracking):
        eventos_iniciales = len(evento_tracking.eventos)
        
        evento_personalizado = EventoValidado(
            id_evento_tracking=str(evento_tracking.id),
            tipo_evento=evento_tracking.tipo_evento.value,
            id_afiliado="test",
            validaciones_pasadas={}
        )
        
        evento_tracking.agregar_evento(evento_personalizado)
        
        assert len(evento_tracking.eventos) == eventos_iniciales + 1
        assert evento_personalizado in evento_tracking.eventos


class TestEventoTrackingIntegracion:
    
    @pytest.fixture
    def evento_completo(self):
        return EventoTracking(
            tipo_evento=TipoEvento.CONVERSION,
            contexto=ContextoEvento(
                id_afiliado="AFILIADO_001",
                id_campana=str(uuid.uuid4()),
                url="https://shop.example.com/success"
            ),
            payload=PayloadEvento(
                datos_custom={"order_id": "ORD123", "product": "Widget"},
                valor_conversion=99.99,
                moneda="USD"
            ),
            metadatos=MetadatosEvento(
                ip_origen="203.0.113.1",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
                timestamp=datetime.now()
            ),
            dispositivo=DatosDispositivo(
                tipo=TipoDispositivo.MOBILE,
                so="iOS 14.6",
                navegador="Safari"
            ),
            firma=FirmaEvento(
                fuente=FuenteEvento.MOBILE_SDK,
                hash_validacion="sdk-hash-456"
            )
        )
    
    def test_flujo_completo_exitoso(self, evento_completo):
        assert evento_completo.estado == EstadoEvento.RECIBIDO
        assert len(evento_completo.eventos) == 1
        
        validaciones = {"afiliado_activo": True, "campana_valida": True}
        assert evento_completo.validar_evento(validaciones) is True
        assert evento_completo.estado == EstadoEvento.VALIDADO
        
        evento_completo.iniciar_procesamiento()
        assert evento_completo.estado == EstadoEvento.PROCESANDO
        
        evento_completo.marcar_como_publicado("tracking.conversions", "msg-789", "key-123")
        assert evento_completo.estado == EstadoEvento.PUBLICADO
        
        tipos_eventos = [type(e).__name__ for e in evento_completo.eventos]
        assert "EventoRecibido" in tipos_eventos
        assert "EventoValidado" in tipos_eventos
        assert "EventoPublicado" in tipos_eventos
    
    def test_flujo_completo_con_fallo(self, evento_completo):
        assert evento_completo.estado == EstadoEvento.RECIBIDO
        
        validaciones = {"afiliado_activo": False}
        assert evento_completo.validar_evento(validaciones) is False
        assert evento_completo.estado == EstadoEvento.DESCARTADO
        
        with pytest.raises(ValueError):
            evento_completo.iniciar_procesamiento()
    
    def test_flujo_reintento(self, evento_completo):
        evento_completo.validar_evento({"test": True})
        evento_completo.iniciar_procesamiento()
        evento_completo.marcar_como_fallido("Network timeout", "TIMEOUT_ERROR")
        
        assert evento_completo.estado == EstadoEvento.FALLIDO
        assert evento_completo.puede_ser_reintentado()
        
        evento_completo.estado = EstadoEvento.PROCESANDO
        evento_completo.marcar_como_publicado("retry.topic", "retry-msg", "retry-key")
        
        assert evento_completo.estado == EstadoEvento.PUBLICADO