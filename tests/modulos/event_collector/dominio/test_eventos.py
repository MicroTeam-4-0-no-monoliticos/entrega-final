import pytest
import uuid
from datetime import datetime

from src.aeropartners.modulos.event_collector.dominio.eventos import (
    EventoRecibido, EventoValidado, EventoPublicado, EventoFallido, 
    EventoDescartado, EventoLimiteProcesamiento
)


class TestEventoRecibido:
    
    def test_creacion_evento_recibido(self):
        evento = EventoRecibido(
            id_evento_tracking=str(uuid.uuid4()),
            tipo_evento="CLICK",
            id_afiliado="AFILIADO_001",
            timestamp_recepcion=datetime.now(),
            fuente="WEB_TAG",
            ip_origen="192.168.1.100"
        )
        
        assert evento.id_evento_tracking is not None
        assert evento.tipo_evento == "CLICK"
        assert evento.id_afiliado == "AFILIADO_001"
        assert evento.fuente == "WEB_TAG"
        assert evento.ip_origen == "192.168.1.100"
        assert evento.timestamp_recepcion is not None
        
        assert hasattr(evento, 'fecha_ocurrencia')
        assert evento.fecha_ocurrencia is not None
    
    def test_eventos_recibidos_diferentes_tipos(self):
        tipos_evento = ["CLICK", "IMPRESSION", "CONVERSION", "PAGE_VIEW"]
        
        for tipo in tipos_evento:
            evento = EventoRecibido(
                id_evento_tracking=str(uuid.uuid4()),
                tipo_evento=tipo,
                id_afiliado=f"AFILIADO_{tipo}",
                timestamp_recepcion=datetime.now(),
                fuente="WEB_TAG",
                ip_origen="203.0.113.1"
            )
            
            assert evento.tipo_evento == tipo
            assert evento.id_afiliado == f"AFILIADO_{tipo}"


class TestEventoValidado:
    
    def test_creacion_evento_validado(self):
        validaciones = {
            "afiliado_activo": True,
            "tiene_permisos": True,
            "campana_valida": True,
            "rate_limit_ok": True
        }
        
        evento = EventoValidado(
            id_evento_tracking=str(uuid.uuid4()),
            tipo_evento="CONVERSION",
            id_afiliado="AFILIADO_PREMIUM",
            validaciones_pasadas=validaciones
        )
        
        assert evento.id_evento_tracking is not None
        assert evento.tipo_evento == "CONVERSION"
        assert evento.id_afiliado == "AFILIADO_PREMIUM"
        assert evento.validaciones_pasadas == validaciones
        assert len(evento.validaciones_pasadas) == 4
        assert all(evento.validaciones_pasadas.values())
    
    def test_evento_validado_con_validaciones_parciales(self):
        validaciones_minimas = {
            "afiliado_activo": True,
            "campana_valida": True
        }
        
        evento = EventoValidado(
            id_evento_tracking=str(uuid.uuid4()),
            tipo_evento="IMPRESSION",
            id_afiliado="AFILIADO_BASIC",
            validaciones_pasadas=validaciones_minimas
        )
        
        assert len(evento.validaciones_pasadas) == 2
        assert evento.validaciones_pasadas["afiliado_activo"] is True
        assert evento.validaciones_pasadas["campana_valida"] is True


class TestEventoPublicado:
    
    def test_creacion_evento_publicado(self):
        timestamp_pub = datetime.now()
        
        evento = EventoPublicado(
            id_evento_tracking=str(uuid.uuid4()),
            tipo_evento="CLICK",
            topic_destino="tracking.clicks",
            partition_key="partition-key-123",
            timestamp_publicacion=timestamp_pub
        )
        
        assert evento.id_evento_tracking is not None
        assert evento.tipo_evento == "CLICK"
        assert evento.topic_destino == "tracking.clicks"
        assert evento.partition_key == "partition-key-123"
        assert evento.timestamp_publicacion == timestamp_pub
    
    def test_eventos_publicados_diferentes_topics(self):
        configuraciones_topics = [
            ("CLICK", "tracking.clicks"),
            ("IMPRESSION", "tracking.impressions"),
            ("CONVERSION", "tracking.conversions"),
            ("PAGE_VIEW", "tracking.page_views")
        ]
        
        for tipo_evento, topic in configuraciones_topics:
            evento = EventoPublicado(
                id_evento_tracking=str(uuid.uuid4()),
                tipo_evento=tipo_evento,
                topic_destino=topic,
                partition_key=f"key-{tipo_evento.lower()}",
                timestamp_publicacion=datetime.now()
            )
            
            assert evento.tipo_evento == tipo_evento
            assert evento.topic_destino == topic
            assert evento.partition_key == f"key-{tipo_evento.lower()}"


class TestEventoFallido:
    
    def test_creacion_evento_fallido(self):
        evento = EventoFallido(
            id_evento_tracking=str(uuid.uuid4()),
            tipo_evento="CONVERSION",
            razon_fallo="Error de conexión con Pulsar",
            codigo_error="PULSAR_CONN_ERROR",
            intentos_realizados=2
        )
        
        assert evento.id_evento_tracking is not None
        assert evento.tipo_evento == "CONVERSION"
        assert evento.razon_fallo == "Error de conexión con Pulsar"
        assert evento.codigo_error == "PULSAR_CONN_ERROR"
        assert evento.intentos_realizados == 2
    
    def test_eventos_fallidos_diferentes_errores(self):
        errores_comunes = [
            ("Network timeout", "NETWORK_TIMEOUT", 1),
            ("Invalid payload format", "PAYLOAD_ERROR", 1),
            ("Rate limit exceeded", "RATE_LIMIT_ERROR", 0),
            ("Authentication failed", "AUTH_ERROR", 1),
            ("Topic not found", "TOPIC_ERROR", 2)
        ]
        
        for razon, codigo, intentos in errores_comunes:
            evento = EventoFallido(
                id_evento_tracking=str(uuid.uuid4()),
                tipo_evento="CLICK",
                razon_fallo=razon,
                codigo_error=codigo,
                intentos_realizados=intentos
            )
            
            assert evento.razon_fallo == razon
            assert evento.codigo_error == codigo
            assert evento.intentos_realizados == intentos


class TestEventoDescartado:
    
    def test_creacion_evento_descartado(self):
        evento = EventoDescartado(
            id_evento_tracking=str(uuid.uuid4()),
            tipo_evento="IMPRESSION",
            razon_descarte="Afiliado no activo",
            regla_violada="afiliado_activo"
        )
        
        assert evento.id_evento_tracking is not None
        assert evento.tipo_evento == "IMPRESSION"
        assert evento.razon_descarte == "Afiliado no activo"
        assert evento.regla_violada == "afiliado_activo"
    
    def test_eventos_descartados_diferentes_reglas(self):
        reglas_violadas = [
            ("afiliado_activo", "Afiliado no está activo"),
            ("tiene_permisos", "Afiliado sin permisos para este tipo de evento"),
            ("campana_valida", "Campaña no existe o está inactiva"),
            ("rate_limit_ok", "Excedido el límite de eventos por minuto"),
            ("payload_valido", "Payload del evento es inválido"),
            ("evento_reciente", "Evento demasiado antiguo para procesar")
        ]
        
        for regla, razon in reglas_violadas:
            evento = EventoDescartado(
                id_evento_tracking=str(uuid.uuid4()),
                tipo_evento="CONVERSION",
                razon_descarte=razon,
                regla_violada=regla
            )
            
            assert evento.regla_violada == regla
            assert evento.razon_descarte == razon


class TestEventoLimiteProcesamiento:
    
    def test_creacion_evento_limite(self):
        evento = EventoLimiteProcesamiento(
            id_afiliado="AFILIADO_HIGH_VOLUME",
            limite_alcanzado="1000 eventos/minuto",
            eventos_bloqueados=150,
            ventana_tiempo="60 segundos"
        )
        
        assert evento.id_afiliado == "AFILIADO_HIGH_VOLUME"
        assert evento.limite_alcanzado == "1000 eventos/minuto"
        assert evento.eventos_bloqueados == 150
        assert evento.ventana_tiempo == "60 segundos"
    
    def test_diferentes_tipos_limite(self):
        tipos_limite = [
            ("100 eventos/minuto", 25, "60 segundos"),
            ("500 eventos/hora", 50, "3600 segundos"),
            ("10000 eventos/día", 1000, "86400 segundos"),
            ("50 conversiones/minuto", 10, "60 segundos")
        ]
        
        for limite, bloqueados, ventana in tipos_limite:
            evento = EventoLimiteProcesamiento(
                id_afiliado="AFILIADO_TEST",
                limite_alcanzado=limite,
                eventos_bloqueados=bloqueados,
                ventana_tiempo=ventana
            )
            
            assert evento.limite_alcanzado == limite
            assert evento.eventos_bloqueados == bloqueados
            assert evento.ventana_tiempo == ventana


class TestEventosDominioIntegracion:
    
    def test_flujo_completo_eventos_exitoso(self):
        id_evento = str(uuid.uuid4())
        timestamp_inicio = datetime.now()
        
        evento_recibido = EventoRecibido(
            id_evento_tracking=id_evento,
            tipo_evento="CONVERSION",
            id_afiliado="AFILIADO_VIP",
            timestamp_recepcion=timestamp_inicio,
            fuente="MOBILE_SDK",
            ip_origen="203.0.113.50"
        )
        
        evento_validado = EventoValidado(
            id_evento_tracking=id_evento,
            tipo_evento="CONVERSION", 
            id_afiliado="AFILIADO_VIP",
            validaciones_pasadas={
                "afiliado_activo": True,
                "tiene_permisos": True,
                "campana_valida": True,
                "payload_valido": True
            }
        )
        
        evento_publicado = EventoPublicado(
            id_evento_tracking=id_evento,
            tipo_evento="CONVERSION",
            topic_destino="tracking.conversions",
            partition_key="conversion-key",
            timestamp_publicacion=datetime.now()
        )
        
        assert evento_recibido.id_evento_tracking == id_evento
        assert evento_validado.id_evento_tracking == id_evento  
        assert evento_publicado.id_evento_tracking == id_evento
        
        assert evento_recibido.fecha_ocurrencia <= evento_validado.fecha_ocurrencia
        assert evento_validado.fecha_ocurrencia <= evento_publicado.fecha_ocurrencia
    
    def test_flujo_completo_eventos_fallido(self):
        id_evento = str(uuid.uuid4())
        
        evento_recibido = EventoRecibido(
            id_evento_tracking=id_evento,
            tipo_evento="CLICK",
            id_afiliado="AFILIADO_SUSPENDED",
            timestamp_recepcion=datetime.now(),
            fuente="WEB_TAG",
            ip_origen="192.0.2.100"
        )
        
        evento_descartado = EventoDescartado(
            id_evento_tracking=id_evento,
            tipo_evento="CLICK",
            razon_descarte="Afiliado suspendido por violación de términos",
            regla_violada="afiliado_activo"
        )
        
        assert evento_recibido.id_evento_tracking == evento_descartado.id_evento_tracking
        assert evento_recibido.tipo_evento == evento_descartado.tipo_evento
        
        assert evento_recibido.fecha_ocurrencia <= evento_descartado.fecha_ocurrencia
    
    def test_flujo_reintento_eventos(self):
        id_evento = str(uuid.uuid4())
        
        evento_fallido_1 = EventoFallido(
            id_evento_tracking=id_evento,
            tipo_evento="CONVERSION",
            razon_fallo="Timeout connecting to Pulsar",
            codigo_error="PULSAR_TIMEOUT",
            intentos_realizados=1
        )
        
        evento_fallido_2 = EventoFallido(
            id_evento_tracking=id_evento,
            tipo_evento="CONVERSION",
            razon_fallo="Pulsar broker unavailable", 
            codigo_error="PULSAR_UNAVAILABLE",
            intentos_realizados=2
        )
        
        evento_publicado = EventoPublicado(
            id_evento_tracking=id_evento,
            tipo_evento="CONVERSION",
            topic_destino="tracking.conversions",
            partition_key="retry-success",
            timestamp_publicacion=datetime.now()
        )
        
        assert evento_fallido_1.intentos_realizados == 1
        assert evento_fallido_2.intentos_realizados == 2
        assert evento_fallido_1.intentos_realizados < evento_fallido_2.intentos_realizados
        
        assert (evento_fallido_1.id_evento_tracking == 
                evento_fallido_2.id_evento_tracking == 
                evento_publicado.id_evento_tracking)
    
    def test_evento_limite_procesamiento_por_afiliado(self):
        afiliados_con_limite = [
            ("AFILIADO_BASIC", "100 eventos/minuto"),
            ("AFILIADO_PREMIUM", "1000 eventos/minuto"), 
            ("AFILIADO_ENTERPRISE", "10000 eventos/minuto")
        ]
        
        for id_afiliado, limite in afiliados_con_limite:
            evento_limite = EventoLimiteProcesamiento(
                id_afiliado=id_afiliado,
                limite_alcanzado=limite,
                eventos_bloqueados=50,
                ventana_tiempo="60 segundos"
            )
            
            assert evento_limite.id_afiliado == id_afiliado
            assert limite in evento_limite.limite_alcanzado
            
            assert evento_limite.fecha_ocurrencia is not None