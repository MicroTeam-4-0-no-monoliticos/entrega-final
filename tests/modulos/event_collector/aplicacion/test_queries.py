import pytest
import uuid
from datetime import datetime, timedelta

from src.aeropartners.modulos.event_collector.aplicacion.queries import (
    ObtenerEstadoEventoQuery, ObtenerEstadisticasProcessingQuery,
    ObtenerEventosFallidosQuery, ObtenerRateLimitStatusQuery
)


class TestObtenerEstadoEventoQuery:
    
    def test_creacion_query_basica(self):
        id_evento = str(uuid.uuid4())
        
        query = ObtenerEstadoEventoQuery(id_evento=id_evento)
        
        assert query.id_evento == id_evento
    
    def test_query_con_diferentes_ids(self):
        ids_evento = [
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4())
        ]
        
        for id_evento in ids_evento:
            query = ObtenerEstadoEventoQuery(id_evento=id_evento)
            assert query.id_evento == id_evento
            
            uuid.UUID(query.id_evento)
    
    def test_query_hereda_de_query_base(self):
        query = ObtenerEstadoEventoQuery(id_evento=str(uuid.uuid4()))
        
        assert hasattr(query, 'fecha_creacion')
        assert query.fecha_creacion is not None


class TestObtenerEstadisticasProcessingQuery:
    
    def test_creacion_query_sin_filtros(self):
        query = ObtenerEstadisticasProcessingQuery()
        
        assert query.id_afiliado is None
        assert query.desde is None
        assert query.hasta is None
        assert query.tipo_evento is None
    
    def test_creacion_query_con_afiliado(self):
        query = ObtenerEstadisticasProcessingQuery(
            id_afiliado="AFILIADO_PREMIUM_001"
        )
        
        assert query.id_afiliado == "AFILIADO_PREMIUM_001"
        assert query.desde is None
        assert query.hasta is None
        assert query.tipo_evento is None
    
    def test_creacion_query_con_rango_temporal(self):
        desde = datetime.now() - timedelta(days=7)
        hasta = datetime.now()
        
        query = ObtenerEstadisticasProcessingQuery(
            desde=desde,
            hasta=hasta
        )
        
        assert query.desde == desde
        assert query.hasta == hasta
        assert query.id_afiliado is None
        assert query.tipo_evento is None
    
    def test_creacion_query_con_tipo_evento(self):
        query = ObtenerEstadisticasProcessingQuery(
            tipo_evento="CONVERSION"
        )
        
        assert query.tipo_evento == "CONVERSION"
        assert query.id_afiliado is None
        assert query.desde is None
        assert query.hasta is None
    
    def test_creacion_query_completa(self):
        desde = datetime.now() - timedelta(days=30)
        hasta = datetime.now() - timedelta(days=1)
        
        query = ObtenerEstadisticasProcessingQuery(
            id_afiliado="AFILIADO_ENTERPRISE_001",
            desde=desde,
            hasta=hasta,
            tipo_evento="CLICK"
        )
        
        assert query.id_afiliado == "AFILIADO_ENTERPRISE_001"
        assert query.desde == desde
        assert query.hasta == hasta
        assert query.tipo_evento == "CLICK"
    
    def test_diferentes_tipos_evento(self):
        tipos_evento = ["CLICK", "IMPRESSION", "CONVERSION", "PAGE_VIEW"]
        
        for tipo in tipos_evento:
            query = ObtenerEstadisticasProcessingQuery(tipo_evento=tipo)
            assert query.tipo_evento == tipo
    
    def test_diferentes_rangos_temporales(self):
        base_time = datetime.now()
        
        rangos_temporales = [
            ("Última hora", base_time - timedelta(hours=1), base_time),
            ("Último día", base_time - timedelta(days=1), base_time),
            ("Última semana", base_time - timedelta(days=7), base_time),
            ("Último mes", base_time - timedelta(days=30), base_time),
            ("Rango personalizado", base_time - timedelta(days=15), base_time - timedelta(days=5))
        ]
        
        for descripcion, desde, hasta in rangos_temporales:
            query = ObtenerEstadisticasProcessingQuery(
                desde=desde,
                hasta=hasta
            )
            
            assert query.desde == desde
            assert query.hasta == hasta
            assert query.desde <= query.hasta


class TestObtenerEventosFallidosQuery:
    
    def test_creacion_query_con_valores_defecto(self):
        query = ObtenerEventosFallidosQuery()
        
        assert query.id_afiliado is None
        assert query.desde is None
        assert query.limite == 100
        assert query.solo_reintentables is True
    
    def test_creacion_query_con_afiliado(self):
        query = ObtenerEventosFallidosQuery(
            id_afiliado="AFILIADO_PROBLEMATIC"
        )
        
        assert query.id_afiliado == "AFILIADO_PROBLEMATIC"
        assert query.limite == 100
        assert query.solo_reintentables is True
    
    def test_creacion_query_con_fecha(self):
        desde = datetime.now() - timedelta(hours=6)
        
        query = ObtenerEventosFallidosQuery(
            desde=desde
        )
        
        assert query.desde == desde
        assert query.id_afiliado is None
        assert query.limite == 100
        assert query.solo_reintentables is True
    
    def test_creacion_query_con_limite_personalizado(self):
        query = ObtenerEventosFallidosQuery(
            limite=50
        )
        
        assert query.limite == 50
        assert query.id_afiliado is None
        assert query.desde is None
        assert query.solo_reintentables is True
    
    def test_creacion_query_incluir_no_reintentables(self):
        query = ObtenerEventosFallidosQuery(
            solo_reintentables=False
        )
        
        assert query.solo_reintentables is False
        assert query.limite == 100
        assert query.id_afiliado is None
        assert query.desde is None
    
    def test_creacion_query_completa(self):
        desde = datetime.now() - timedelta(days=3)
        
        query = ObtenerEventosFallidosQuery(
            id_afiliado="AFILIADO_HIGH_FAILURE_RATE",
            desde=desde,
            limite=25,
            solo_reintentables=False
        )
        
        assert query.id_afiliado == "AFILIADO_HIGH_FAILURE_RATE"
        assert query.desde == desde
        assert query.limite == 25
        assert query.solo_reintentables is False
    
    def test_diferentes_limites(self):
        limites = [10, 50, 100, 500, 1000]
        
        for limite in limites:
            query = ObtenerEventosFallidosQuery(limite=limite)
            assert query.limite == limite
    
    def test_query_para_diferentes_escenarios(self):
        escenarios = [
            ("Solo reintentables último día", datetime.now() - timedelta(days=1), True, 100),
            ("Todos los fallos última hora", datetime.now() - timedelta(hours=1), False, 50),
            ("Top 10 fallos recientes", datetime.now() - timedelta(hours=2), True, 10),
            ("Análisis completo semanal", datetime.now() - timedelta(days=7), False, 500)
        ]
        
        for descripcion, desde, solo_reintentables, limite in escenarios:
            query = ObtenerEventosFallidosQuery(
                desde=desde,
                solo_reintentables=solo_reintentables,
                limite=limite
            )
            
            assert query.desde == desde
            assert query.solo_reintentables == solo_reintentables
            assert query.limite == limite


class TestObtenerRateLimitStatusQuery:
    
    def test_creacion_query_basica(self):
        query = ObtenerRateLimitStatusQuery(
            id_afiliado="AFILIADO_HIGH_VOLUME"
        )
        
        assert query.id_afiliado == "AFILIADO_HIGH_VOLUME"
        assert query.ventana_minutos == 1
    
    def test_creacion_query_con_ventana_personalizada(self):
        query = ObtenerRateLimitStatusQuery(
            id_afiliado="AFILIADO_CUSTOM_WINDOW",
            ventana_minutos=5
        )
        
        assert query.id_afiliado == "AFILIADO_CUSTOM_WINDOW"
        assert query.ventana_minutos == 5
    
    def test_diferentes_ventanas_tiempo(self):
        ventanas = [1, 5, 15, 60]
        
        for ventana in ventanas:
            query = ObtenerRateLimitStatusQuery(
                id_afiliado="AFILIADO_TESTING",
                ventana_minutos=ventana
            )
            
            assert query.ventana_minutos == ventana
    
    def test_diferentes_afiliados(self):
        afiliados = [
            "AFILIADO_BASIC",
            "AFILIADO_PREMIUM", 
            "AFILIADO_ENTERPRISE",
            "AFILIADO_HIGH_VOLUME_SPECIAL"
        ]
        
        for afiliado in afiliados:
            query = ObtenerRateLimitStatusQuery(id_afiliado=afiliado)
            assert query.id_afiliado == afiliado
    
    def test_configuraciones_monitoreo(self):
        configuraciones = [
            ("Monitoreo tiempo real", 1),
            ("Monitoreo cada 5 minutos", 5),
            ("Monitoreo cada 15 minutos", 15),
            ("Monitoreo cada hora", 60)
        ]
        
        for descripcion, ventana in configuraciones:
            query = ObtenerRateLimitStatusQuery(
                id_afiliado="AFILIADO_MONITORING",
                ventana_minutos=ventana
            )
            
            assert query.ventana_minutos == ventana
            assert query.id_afiliado == "AFILIADO_MONITORING"


class TestQueriesIntegracion:
    
    def test_flujo_monitoreo_completo(self):
        id_afiliado = "AFILIADO_MONITORING_COMPLETE"
        id_evento_problema = str(uuid.uuid4())
        base_time = datetime.now()
        
        query_estado = ObtenerEstadoEventoQuery(id_evento=id_evento_problema)
        
        query_estadisticas = ObtenerEstadisticasProcessingQuery(
            id_afiliado=id_afiliado,
            desde=base_time - timedelta(days=1),
            hasta=base_time
        )
        
        query_fallos = ObtenerEventosFallidosQuery(
            id_afiliado=id_afiliado,
            desde=base_time - timedelta(hours=6),
            limite=50,
            solo_reintentables=True
        )
        
        query_rate_limit = ObtenerRateLimitStatusQuery(
            id_afiliado=id_afiliado,
            ventana_minutos=5
        )
        
        assert query_estado.id_evento == id_evento_problema
        assert query_estadisticas.id_afiliado == id_afiliado
        assert query_fallos.id_afiliado == id_afiliado
        assert query_rate_limit.id_afiliado == id_afiliado
        
        assert query_estadisticas.desde < query_estadisticas.hasta
        assert query_fallos.desde > base_time - timedelta(days=1)
    
    def test_queries_para_diferentes_tipos_analisis(self):
        base_time = datetime.now()
        
        query_diario = ObtenerEstadisticasProcessingQuery(
            desde=base_time - timedelta(days=1),
            hasta=base_time,
            tipo_evento="CONVERSION"
        )
        
        query_problemas = ObtenerEventosFallidosQuery(
            desde=base_time - timedelta(hours=2),
            limite=100,
            solo_reintentables=False
        )
        
        query_monitoring = ObtenerRateLimitStatusQuery(
            id_afiliado="AFILIADO_ANALYSIS",
            ventana_minutos=1
        )
        
        assert query_diario.tipo_evento == "CONVERSION"
        assert query_problemas.solo_reintentables is False
        assert query_monitoring.ventana_minutos == 1
    
    def test_queries_para_diferentes_niveles_afiliado(self):
        configuraciones_nivel = [
            ("BASIC", 10, 1, True),
            ("PREMIUM", 50, 5, False),
            ("ENTERPRISE", 200, 15, False)
        ]
        
        for nivel, limite_fallos, ventana_rate, solo_reintentables in configuraciones_nivel:
            id_afiliado = f"AFILIADO_{nivel}"
            
            query_fallos = ObtenerEventosFallidosQuery(
                id_afiliado=id_afiliado,
                limite=limite_fallos,
                solo_reintentables=solo_reintentables
            )
            
            query_rate = ObtenerRateLimitStatusQuery(
                id_afiliado=id_afiliado,
                ventana_minutos=ventana_rate
            )
            
            assert query_fallos.limite == limite_fallos
            assert query_fallos.solo_reintentables == solo_reintentables
            assert query_rate.ventana_minutos == ventana_rate
            assert query_fallos.id_afiliado == query_rate.id_afiliado
    
    def test_queries_con_diferentes_horizontes_temporales(self):
        base_time = datetime.now()
        
        horizontes = [
            ("Tiempo real", timedelta(minutes=5)),
            ("Corto plazo", timedelta(hours=1)),
            ("Mediano plazo", timedelta(days=1)),
            ("Largo plazo", timedelta(days=7)),
            ("Análisis histórico", timedelta(days=30))
        ]
        
        for descripcion, delta in horizontes:
            query_stats = ObtenerEstadisticasProcessingQuery(
                desde=base_time - delta,
                hasta=base_time
            )
            
            query_fallos = ObtenerEventosFallidosQuery(
                desde=base_time - delta,
                limite=50
            )
            
            assert query_stats.desde == query_fallos.desde
            assert query_stats.hasta == base_time
            assert query_stats.desde < base_time