import pytest
import uuid
from datetime import datetime, timedelta

from src.aeropartners.modulos.event_collector.aplicacion.comandos import (
    ProcesarEventoTrackingCommand, ReprocesarEventoFallidoCommand
)


class TestProcesarEventoTrackingCommand:
    
    def test_creacion_comando_basico(self):
        comando = ProcesarEventoTrackingCommand(
            tipo_evento="CLICK",
            id_afiliado="AFILIADO_001",
            timestamp=datetime.now(),
            ip_origen="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)"
        )
        
        assert comando.tipo_evento == "CLICK"
        assert comando.id_afiliado == "AFILIADO_001"
        assert comando.timestamp is not None
        assert comando.ip_origen == "192.168.1.100"
        assert comando.user_agent == "Mozilla/5.0 (Test Browser)"
        
        assert comando.tipo_dispositivo == "OTHER"
        assert comando.fuente_evento == "WEB_TAG"
        assert comando.id_campana is None
        assert comando.datos_custom is None
    
    def test_creacion_comando_completo(self):
        timestamp_evento = datetime.now()
        
        comando = ProcesarEventoTrackingCommand(
            tipo_evento="CONVERSION",
            id_afiliado="AFILIADO_PREMIUM_001",
            timestamp=timestamp_evento,
            
            id_campana=str(uuid.uuid4()),
            id_oferta="BLACK_FRIDAY_2023",
            url="https://store.example.com/checkout/success",
            parametros_tracking={
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "black-friday",
                "custom_param": "vip_user"
            },
            
            datos_custom={
                "order_id": "ORD-12345",
                "product_category": "electronics",
                "customer_segment": "premium"
            },
            valor_conversion=299.99,
            moneda="USD",
            
            ip_origen="203.0.113.45",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            session_id="sess_abc123xyz",
            referrer="https://google.com/search",
            
            tipo_dispositivo="DESKTOP",
            identificador_dispositivo="cookie_device_123",
            sistema_operativo="macOS 12.6",
            navegador="Chrome 108",
            resolucion_pantalla="2560x1440",
            
            fuente_evento="WEB_TAG",
            hash_validacion="sha256_verification_hash"
        )
        
        assert comando.tipo_evento == "CONVERSION"
        assert comando.id_afiliado == "AFILIADO_PREMIUM_001"
        assert comando.timestamp == timestamp_evento
        
        assert comando.id_campana is not None
        assert comando.id_oferta == "BLACK_FRIDAY_2023"
        assert "store.example.com" in comando.url
        assert comando.parametros_tracking["utm_source"] == "google"
        assert comando.parametros_tracking["custom_param"] == "vip_user"
        
        assert comando.datos_custom["order_id"] == "ORD-12345"
        assert comando.valor_conversion == 299.99
        assert comando.moneda == "USD"
        
        assert comando.ip_origen == "203.0.113.45"
        assert "Mozilla/5.0" in comando.user_agent
        assert comando.session_id == "sess_abc123xyz"
        
        assert comando.tipo_dispositivo == "DESKTOP"
        assert comando.sistema_operativo == "macOS 12.6"
        assert comando.navegador == "Chrome 108"
        
        assert comando.fuente_evento == "WEB_TAG"
        assert comando.hash_validacion == "sha256_verification_hash"
    
    def test_comando_diferentes_tipos_evento(self):
        tipos_evento = ["CLICK", "IMPRESSION", "CONVERSION", "PAGE_VIEW"]
        base_timestamp = datetime.now()
        
        for i, tipo in enumerate(tipos_evento):
            comando = ProcesarEventoTrackingCommand(
                tipo_evento=tipo,
                id_afiliado=f"AFILIADO_{tipo}",
                timestamp=base_timestamp + timedelta(seconds=i),
                ip_origen=f"192.168.1.{100 + i}",
                user_agent=f"TestAgent/{i+1}.0"
            )
            
            assert comando.tipo_evento == tipo
            assert comando.id_afiliado == f"AFILIADO_{tipo}"
            assert comando.ip_origen == f"192.168.1.{100 + i}"
    
    def test_comando_diferentes_fuentes(self):
        configuraciones_fuente = [
            ("WEB_TAG", None),
            ("MOBILE_SDK", None),
            ("API_DIRECT", "api_key_123"),
            ("WEBHOOK", None)
        ]
        
        for fuente, api_key in configuraciones_fuente:
            comando = ProcesarEventoTrackingCommand(
                tipo_evento="CLICK",
                id_afiliado="AFILIADO_MULTI_SOURCE",
                timestamp=datetime.now(),
                ip_origen="10.0.0.1",
                user_agent="Multi Source Agent",
                fuente_evento=fuente,
                api_key=api_key
            )
            
            assert comando.fuente_evento == fuente
            if fuente == "API_DIRECT":
                assert comando.api_key == api_key
            else:
                assert comando.api_key == api_key
    
    def test_comando_diferentes_tipos_dispositivo(self):
        configuraciones_dispositivo = [
            ("DESKTOP", "Windows 10", "Chrome 108", "1920x1080"),
            ("MOBILE", "iOS 16.1", "Safari Mobile", "375x812"),
            ("TABLET", "iPadOS 16.1", "Safari", "1024x768"),
            ("OTHER", "Smart TV OS", "TV Browser", "3840x2160")
        ]
        
        for tipo, so, navegador, resolucion in configuraciones_dispositivo:
            comando = ProcesarEventoTrackingCommand(
                tipo_evento="IMPRESSION",
                id_afiliado="AFILIADO_MULTI_DEVICE",
                timestamp=datetime.now(),
                ip_origen="203.0.113.100",
                user_agent=f"User Agent for {tipo}",
                tipo_dispositivo=tipo,
                sistema_operativo=so,
                navegador=navegador,
                resolucion_pantalla=resolucion
            )
            
            assert comando.tipo_dispositivo == tipo
            assert comando.sistema_operativo == so
            assert comando.navegador == navegador
            assert comando.resolucion_pantalla == resolucion
    
    def test_comando_con_conversion(self):
        comando = ProcesarEventoTrackingCommand(
            tipo_evento="CONVERSION",
            id_afiliado="AFILIADO_ECOMMERCE",
            timestamp=datetime.now(),
            ip_origen="198.51.100.50",
            user_agent="E-commerce User Agent",
            
            datos_custom={
                "transaction_id": "TXN_789ABC",
                "product_ids": ["P001", "P002", "P003"],
                "category": "fashion",
                "customer_type": "returning"
            },
            valor_conversion=149.99,
            moneda="EUR",
            
            id_campana=str(uuid.uuid4()),
            parametros_tracking={
                "utm_source": "facebook",
                "utm_medium": "social",
                "utm_campaign": "summer-sale"
            }
        )
        
        assert comando.tipo_evento == "CONVERSION"
        assert comando.valor_conversion == 149.99
        assert comando.moneda == "EUR"
        assert "transaction_id" in comando.datos_custom
        assert "TXN_789ABC" == comando.datos_custom["transaction_id"]
        assert len(comando.datos_custom["product_ids"]) == 3
        assert comando.parametros_tracking["utm_source"] == "facebook"
    
    def test_comando_hereda_de_comando_base(self):
        comando = ProcesarEventoTrackingCommand(
            tipo_evento="CLICK",
            id_afiliado="TEST_AFILIADO",
            timestamp=datetime.now(),
            ip_origen="127.0.0.1",
            user_agent="Test Agent"
        )
        
        assert hasattr(comando, 'fecha_creacion')
        assert comando.fecha_creacion is not None


class TestReprocesarEventoFallidoCommand:
    
    def test_creacion_comando_basico(self):
        id_evento = str(uuid.uuid4())
        
        comando = ReprocesarEventoFallidoCommand(
            id_evento=id_evento
        )
        
        assert comando.id_evento == id_evento
        assert comando.forzar_reproceso is False
    
    def test_creacion_comando_con_forzar_reproceso(self):
        id_evento = str(uuid.uuid4())
        
        comando = ReprocesarEventoFallidoCommand(
            id_evento=id_evento,
            forzar_reproceso=True
        )
        
        assert comando.id_evento == id_evento
        assert comando.forzar_reproceso is True
    
    def test_comando_con_diferentes_ids(self):
        ids_evento = [
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4())
        ]
        
        for id_evento in ids_evento:
            comando = ReprocesarEventoFallidoCommand(id_evento=id_evento)
            assert comando.id_evento == id_evento
            
            uuid.UUID(comando.id_evento)
    
    def test_comando_scenarios_reproceso(self):
        escenarios = [
            (False, "Reproceso normal con límites"),
            (True, "Reproceso forzado ignorando límites")
        ]
        
        for forzar, descripcion in escenarios:
            comando = ReprocesarEventoFallidoCommand(
                id_evento=str(uuid.uuid4()),
                forzar_reproceso=forzar
            )
            
            assert comando.forzar_reproceso == forzar
            assert comando.id_evento is not None
    
    def test_comando_hereda_de_comando_base(self):
        comando = ReprocesarEventoFallidoCommand(
            id_evento=str(uuid.uuid4())
        )
        
        assert hasattr(comando, 'fecha_creacion')
        assert comando.fecha_creacion is not None


class TestComandosIntegracion:
    
    def test_flujo_comando_procesamiento_y_reintento(self):
        timestamp_original = datetime.now() - timedelta(minutes=5)
        
        comando_inicial = ProcesarEventoTrackingCommand(
            tipo_evento="CONVERSION",
            id_afiliado="AFILIADO_RETRY_TEST",
            timestamp=timestamp_original,
            ip_origen="192.0.2.50",
            user_agent="Retry Test Browser",
            datos_custom={"retry_test": True},
            valor_conversion=99.99,
            moneda="USD"
        )
        
        id_evento_generado = str(uuid.uuid4())
        
        comando_reintento = ReprocesarEventoFallidoCommand(
            id_evento=id_evento_generado,
            forzar_reproceso=False
        )
        
        assert comando_inicial.tipo_evento == "CONVERSION"
        assert comando_inicial.valor_conversion == 99.99
        assert comando_reintento.id_evento == id_evento_generado
        assert comando_reintento.forzar_reproceso is False
        
        assert comando_inicial.fecha_creacion <= comando_reintento.fecha_creacion
    
    def test_multiples_comandos_diferentes_afiliados(self):
        afiliados = ["AFILIADO_BASIC", "AFILIADO_PREMIUM", "AFILIADO_ENTERPRISE"]
        tipos_evento = ["CLICK", "IMPRESSION", "CONVERSION"]
        
        comandos_procesamiento = []
        comandos_reintento = []
        
        for i, (afiliado, tipo) in enumerate(zip(afiliados, tipos_evento)):
            comando_proc = ProcesarEventoTrackingCommand(
                tipo_evento=tipo,
                id_afiliado=afiliado,
                timestamp=datetime.now() + timedelta(seconds=i),
                ip_origen=f"10.0.{i}.100",
                user_agent=f"Agent for {afiliado}"
            )
            comandos_procesamiento.append(comando_proc)
            
            comando_retry = ReprocesarEventoFallidoCommand(
                id_evento=str(uuid.uuid4()),
                forzar_reproceso=(i == 2)
            )
            comandos_reintento.append(comando_retry)
        
        assert len(comandos_procesamiento) == 3
        assert len(comandos_reintento) == 3
        
        for i, comando in enumerate(comandos_procesamiento):
            assert comando.id_afiliado == afiliados[i]
            assert comando.tipo_evento == tipos_evento[i]
        
        assert comandos_reintento[0].forzar_reproceso is False
        assert comandos_reintento[1].forzar_reproceso is False
        assert comandos_reintento[2].forzar_reproceso is True
    
    def test_comandos_con_diferentes_contextos_temporales(self):
        base_time = datetime.now()
        
        contextos_temporales = [
            ("Evento actual", base_time),
            ("Evento reciente", base_time - timedelta(minutes=5)),
            ("Evento de hace una hora", base_time - timedelta(hours=1)),
            ("Evento de ayer", base_time - timedelta(days=1))
        ]
        
        for descripcion, timestamp in contextos_temporales:
            comando = ProcesarEventoTrackingCommand(
                tipo_evento="CLICK",
                id_afiliado=f"AFILIADO_{descripcion.replace(' ', '_').upper()}",
                timestamp=timestamp,
                ip_origen="172.16.0.100",
                user_agent=f"Browser for {descripcion}"
            )
            
            assert comando.timestamp == timestamp
            assert descripcion.replace(' ', '_').upper() in comando.id_afiliado
            
            assert comando.fecha_creacion >= timestamp