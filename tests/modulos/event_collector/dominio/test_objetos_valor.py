import pytest
import uuid
from datetime import datetime

from src.aeropartners.modulos.event_collector.dominio.objetos_valor import (
    MetadatosEvento, ContextoEvento, DatosDispositivo, FirmaEvento, PayloadEvento
)
from src.aeropartners.modulos.event_collector.dominio.enums import TipoDispositivo, FuenteEvento


class TestMetadatosEvento:
    
    def test_creacion_metadatos_validos(self):
        metadatos = MetadatosEvento(
            ip_origen="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timestamp=datetime.now(),
            session_id="session-abc123",
            referrer="https://google.com"
        )
        
        assert metadatos.ip_origen == "192.168.1.100"
        assert "Mozilla/5.0" in metadatos.user_agent
        assert metadatos.session_id == "session-abc123"
        assert metadatos.referrer == "https://google.com"
        assert metadatos.timestamp is not None
    
    def test_creacion_metadatos_campos_opcionales(self):
        metadatos = MetadatosEvento(
            ip_origen="10.0.0.1",
            user_agent="Test Agent/1.0",
            timestamp=datetime.now()
        )
        
        assert metadatos.session_id is None
        assert metadatos.referrer is None
    
    def test_validacion_ip_requerida(self):
        with pytest.raises(ValueError, match="IP de origen es requerida"):
            MetadatosEvento(
                ip_origen="",
                user_agent="Test Agent",
                timestamp=datetime.now()
            )
    
    def test_validacion_user_agent_requerido(self):
        with pytest.raises(ValueError, match="User-Agent es requerido"):
            MetadatosEvento(
                ip_origen="192.168.1.1",
                user_agent="",
                timestamp=datetime.now()
            )
    
    def test_validacion_timestamp_requerido(self):
        with pytest.raises(ValueError, match="Timestamp es requerido"):
            MetadatosEvento(
                ip_origen="192.168.1.1",
                user_agent="Test Agent",
                timestamp=None
            )
    
    def test_objeto_valor_inmutable(self):
        metadatos = MetadatosEvento(
            ip_origen="192.168.1.1",
            user_agent="Test Agent",
            timestamp=datetime.now()
        )
        
        with pytest.raises(AttributeError):
            metadatos.ip_origen = "10.0.0.1"


class TestContextoEvento:
    
    def test_creacion_contexto_valido(self):
        contexto = ContextoEvento(
            id_afiliado="AFILIADO_001",
            id_campana=str(uuid.uuid4()),
            id_oferta="OFERTA_123",
            url="https://example.com/landing",
            parametros_tracking={"utm_source": "google", "utm_medium": "cpc"}
        )
        
        assert contexto.id_afiliado == "AFILIADO_001"
        assert contexto.id_oferta == "OFERTA_123"
        assert contexto.url == "https://example.com/landing"
        assert contexto.parametros_tracking["utm_source"] == "google"
    
    def test_creacion_contexto_minimo(self):
        contexto = ContextoEvento(id_afiliado="AFILIADO_002")
        
        assert contexto.id_afiliado == "AFILIADO_002"
        assert contexto.id_campana is None
        assert contexto.id_oferta is None
        assert contexto.url is None
        assert contexto.parametros_tracking is None
    
    def test_validacion_afiliado_requerido(self):
        with pytest.raises(ValueError, match="ID de afiliado es requerido"):
            ContextoEvento(id_afiliado="")
    
    def test_validacion_uuid_campana(self):
        with pytest.raises(ValueError, match="ID de campaña debe ser un UUID válido"):
            ContextoEvento(
                id_afiliado="AFILIADO_001",
                id_campana="not-a-uuid"
            )
    
    def test_uuid_campana_valido(self):
        uuid_valido = str(uuid.uuid4())
        contexto = ContextoEvento(
            id_afiliado="AFILIADO_001",
            id_campana=uuid_valido
        )
        
        assert contexto.id_campana == uuid_valido


class TestDatosDispositivo:
    
    def test_creacion_dispositivo_completo(self):
        dispositivo = DatosDispositivo(
            tipo=TipoDispositivo.MOBILE,
            identificador="device-uuid-123",
            so="Android 11",
            navegador="Chrome Mobile 91",
            resolucion="1080x2340"
        )
        
        assert dispositivo.tipo == TipoDispositivo.MOBILE
        assert dispositivo.identificador == "device-uuid-123"
        assert dispositivo.so == "Android 11"
        assert dispositivo.navegador == "Chrome Mobile 91"
        assert dispositivo.resolucion == "1080x2340"
    
    def test_creacion_dispositivo_minimo(self):
        dispositivo = DatosDispositivo(tipo=TipoDispositivo.DESKTOP)
        
        assert dispositivo.tipo == TipoDispositivo.DESKTOP
        assert dispositivo.identificador is None
        assert dispositivo.so is None
        assert dispositivo.navegador is None
        assert dispositivo.resolucion is None
    
    def test_validacion_tipo_requerido(self):
        with pytest.raises(ValueError, match="Tipo de dispositivo es requerido"):
            DatosDispositivo(tipo=None)
    
    def test_todos_tipos_dispositivo(self):
        for tipo in TipoDispositivo:
            dispositivo = DatosDispositivo(tipo=tipo)
            assert dispositivo.tipo == tipo


class TestFirmaEvento:
    
    def test_creacion_firma_web_tag(self):
        firma = FirmaEvento(
            fuente=FuenteEvento.WEB_TAG,
            hash_validacion="sha256-hash-here"
        )
        
        assert firma.fuente == FuenteEvento.WEB_TAG
        assert firma.hash_validacion == "sha256-hash-here"
        assert firma.api_key is None
    
    def test_creacion_firma_api_direct(self):
        firma = FirmaEvento(
            fuente=FuenteEvento.API_DIRECT,
            api_key="api-key-123"
        )
        
        assert firma.fuente == FuenteEvento.API_DIRECT
        assert firma.api_key == "api-key-123"
    
    def test_validacion_fuente_requerida(self):
        with pytest.raises(ValueError, match="Fuente del evento es requerida"):
            FirmaEvento(fuente=None)
    
    def test_validacion_api_key_requerida_para_direct(self):
        with pytest.raises(ValueError, match="API Key es requerida para llamadas directas"):
            FirmaEvento(fuente=FuenteEvento.API_DIRECT)
    
    def test_api_key_no_requerida_para_otras_fuentes(self):
        firma = FirmaEvento(fuente=FuenteEvento.WEB_TAG)
        assert firma.fuente == FuenteEvento.WEB_TAG
        assert firma.api_key is None
    
    def test_todas_fuentes_evento(self):
        firma_web = FirmaEvento(fuente=FuenteEvento.WEB_TAG)
        assert firma_web.fuente == FuenteEvento.WEB_TAG
        
        firma_sdk = FirmaEvento(fuente=FuenteEvento.MOBILE_SDK)
        assert firma_sdk.fuente == FuenteEvento.MOBILE_SDK
        
        firma_api = FirmaEvento(fuente=FuenteEvento.API_DIRECT, api_key="test-key")
        assert firma_api.fuente == FuenteEvento.API_DIRECT
        
        firma_webhook = FirmaEvento(fuente=FuenteEvento.WEBHOOK)
        assert firma_webhook.fuente == FuenteEvento.WEBHOOK


class TestPayloadEvento:
    
    def test_creacion_payload_completo(self):
        payload = PayloadEvento(
            datos_custom={"producto_id": "P123", "categoria": "electronica"},
            valor_conversion=99.99,
            moneda="USD"
        )
        
        assert payload.datos_custom["producto_id"] == "P123"
        assert payload.datos_custom["categoria"] == "electronica"
        assert payload.valor_conversion == 99.99
        assert payload.moneda == "USD"
    
    def test_creacion_payload_sin_conversion(self):
        payload = PayloadEvento(
            datos_custom={"click_id": "click_123"}
        )
        
        assert payload.datos_custom["click_id"] == "click_123"
        assert payload.valor_conversion is None
        assert payload.moneda is None
    
    def test_creacion_payload_vacio(self):
        payload = PayloadEvento(datos_custom=None)
        
        assert payload.datos_custom == {}
    
    def test_validacion_moneda_requerida_con_valor(self):
        with pytest.raises(ValueError, match="Si se especifica valor de conversión, la moneda es requerida"):
            PayloadEvento(
                datos_custom={"order_id": "ORD123"},
                valor_conversion=50.00
            )
    
    def test_payload_sin_valor_conversion_permite_sin_moneda(self):
        payload = PayloadEvento(
            datos_custom={"event_type": "impression"}
        )
        
        assert payload.datos_custom["event_type"] == "impression"
        assert payload.valor_conversion is None
        assert payload.moneda is None
    
    def test_payload_con_datos_custom_complejos(self):
        datos_complejos = {
            "producto": {
                "id": "P123",
                "nombre": "Laptop Gaming",
                "precio": 1299.99,
                "especificaciones": {
                    "cpu": "Intel i7",
                    "ram": "16GB",
                    "gpu": "RTX 3080"
                }
            },
            "usuario": {
                "id": "U456",
                "segmento": "premium"
            },
            "evento": {
                "pagina": "/productos/laptops",
                "accion": "view_product",
                "timestamp": "2023-10-15T10:30:00Z"
            }
        }
        
        payload = PayloadEvento(datos_custom=datos_complejos)
        
        assert payload.datos_custom["producto"]["id"] == "P123"
        assert payload.datos_custom["producto"]["especificaciones"]["cpu"] == "Intel i7"
        assert payload.datos_custom["usuario"]["segmento"] == "premium"


class TestObjetosValorIntegracion:
    
    def test_conjunto_objetos_valor_validos(self):
        metadatos = MetadatosEvento(
            ip_origen="203.0.113.45",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            timestamp=datetime.now(),
            session_id="sess_789abc",
            referrer="https://search.engine.com"
        )
        
        contexto = ContextoEvento(
            id_afiliado="PARTNER_PREMIUM_001",
            id_campana=str(uuid.uuid4()),
            id_oferta="BLACK_FRIDAY_2023",
            url="https://store.example.com/black-friday",
            parametros_tracking={
                "utm_source": "email",
                "utm_medium": "newsletter",
                "utm_campaign": "black-friday-2023",
                "custom_param": "vip_customer"
            }
        )
        
        dispositivo = DatosDispositivo(
            tipo=TipoDispositivo.DESKTOP,
            identificador="cookie_987xyz",
            so="macOS 12.6",
            navegador="Safari 16.0",
            resolucion="2560x1440"
        )
        
        firma = FirmaEvento(
            fuente=FuenteEvento.WEB_TAG,
            hash_validacion="sha256_tracking_verification_hash"
        )
        
        payload = PayloadEvento(
            datos_custom={
                "product_category": "electronics",
                "product_subcategory": "laptops", 
                "brand": "TechBrand",
                "model": "UltraBook Pro",
                "price_range": "1000-1500",
                "promotion_applied": True
            },
            valor_conversion=1299.99,
            moneda="USD"
        )
        
        assert metadatos.ip_origen == "203.0.113.45"
        assert contexto.id_afiliado == "PARTNER_PREMIUM_001"
        assert dispositivo.tipo == TipoDispositivo.DESKTOP
        assert firma.fuente == FuenteEvento.WEB_TAG
        assert payload.valor_conversion == 1299.99
        
        with pytest.raises(AttributeError):
            metadatos.ip_origen = "different_ip"
            
        with pytest.raises(AttributeError):
            contexto.id_afiliado = "different_affiliate"
    
    def test_escenarios_diferentes_fuentes(self):
        firma_mobile = FirmaEvento(
            fuente=FuenteEvento.MOBILE_SDK,
            hash_validacion="mobile_sdk_hash"
        )
        
        dispositivo_mobile = DatosDispositivo(
            tipo=TipoDispositivo.MOBILE,
            identificador="advertising_id_abc123",
            so="iOS 16.1",
            navegador="In-App Browser"
        )
        
        firma_api = FirmaEvento(
            fuente=FuenteEvento.API_DIRECT,
            api_key="sk_prod_abc123def456"
        )
        
        firma_webhook = FirmaEvento(
            fuente=FuenteEvento.WEBHOOK,
            hash_validacion="webhook_signature_verification"
        )
        
        assert firma_mobile.fuente == FuenteEvento.MOBILE_SDK
        assert firma_api.api_key == "sk_prod_abc123def456"
        assert firma_webhook.fuente == FuenteEvento.WEBHOOK
        assert dispositivo_mobile.tipo == TipoDispositivo.MOBILE