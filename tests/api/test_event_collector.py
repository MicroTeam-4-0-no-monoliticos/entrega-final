import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.aeropartners.api.event_collector import router
from src.aeropartners.modulos.event_collector.aplicacion.comandos import ProcesarEventoTrackingCommand
from src.aeropartners.modulos.event_collector.aplicacion.queries import (
    ObtenerEstadoEventoQuery, ObtenerEstadisticasProcessingQuery
)


test_app = FastAPI()
test_app.include_router(router)

@pytest.fixture
def client():
    return TestClient(test_app)


@pytest.fixture
def mock_handlers():
    with patch('src.aeropartners.modulos.event_collector.factory.get_procesar_evento_handler') as mock_proc, \
         patch('src.aeropartners.modulos.event_collector.factory.get_retry_handler') as mock_retry, \
         patch('src.aeropartners.modulos.event_collector.factory.get_estado_evento_handler') as mock_estado, \
         patch('src.aeropartners.modulos.event_collector.factory.get_estadisticas_handler') as mock_stats, \
         patch('src.aeropartners.modulos.event_collector.factory.get_eventos_fallidos_handler') as mock_fallidos, \
         patch('src.aeropartners.modulos.event_collector.factory.get_rate_limit_status_handler') as mock_rate:
        
        yield {
            'procesar_evento': mock_proc,
            'retry': mock_retry,
            'estado': mock_estado,
            'estadisticas': mock_stats,
            'fallidos': mock_fallidos,
            'rate_limit': mock_rate
        }


class TestEventCollectorHealthEndpoints:
    
    def test_health_check(self, client):
        response = client.get("/event-collector/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "event-collector-bff"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
    
    def test_readiness_check(self, client):
        response = client.get("/event-collector/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "dependencies" in data
        assert "timestamp" in data
        assert "pulsar" in data["dependencies"]
        assert "redis" in data["dependencies"]


class TestProcesarEventoEndpoint:
    
    def test_procesar_evento_exitoso(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'exito': True,
            'id_evento': str(uuid.uuid4()),
            'estado': 'PUBLICADO',
            'hash_evento': 'hash_123',
            'topic_destino': 'tracking.clicks'
        }
        mock_handlers['procesar_evento'].return_value = mock_handler
        
        evento_data = {
            "tipo_evento": "CLICK",
            "id_afiliado": "AFILIADO_001",
            "id_campana": str(uuid.uuid4()),
            "url": "https://example.com/landing",
            "datos_custom": {
                "producto_id": "P123",
                "categoria": "electronica"
            },
            "tipo_dispositivo": "DESKTOP",
            "fuente_evento": "WEB_TAG"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Session-ID": "test-session-123",
            "User-Agent": "Mozilla/5.0 (Test Browser)"
        }
        
        response = client.post(
            "/event-collector/events", 
            json=evento_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["exito"] is True
        assert "id_evento" in data
        assert data["estado"] == "PUBLICADO"
        assert data["mensaje"] == "Evento procesado exitosamente"
        assert "timestamp_procesamiento" in data
        
        mock_handler.handle.assert_called_once()
    
    def test_procesar_evento_validacion_fallida(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'exito': False,
            'id_evento': str(uuid.uuid4()),
            'estado': 'DESCARTADO',
            'razon': 'Validaciones fallidas: afiliado_activo'
        }
        mock_handlers['procesar_evento'].return_value = mock_handler
        
        evento_data = {
            "tipo_evento": "IMPRESSION", 
            "id_afiliado": "AFILIADO_INACTIVE",
            "tipo_dispositivo": "MOBILE",
            "fuente_evento": "MOBILE_SDK"
        }
        
        response = client.post("/event-collector/events", json=evento_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["exito"] is False
        assert data["estado"] == "DESCARTADO"
        assert "Validaciones fallidas" in data["mensaje"]
    
    def test_procesar_evento_error_validacion_input(self, client):
        evento_data = {
            "tipo_evento": "CLICK",
            "id_afiliado": "AFILIADO_001",
            "id_campana": "not-a-uuid",
            "fuente_evento": "WEB_TAG"
        }
        
        with patch('src.aeropartners.modulos.event_collector.factory.get_procesar_evento_handler') as mock_factory:
            mock_handler = AsyncMock()
            mock_handler.handle.side_effect = ValueError("ID de campaña debe ser un UUID válido")
            mock_factory.return_value = mock_handler
            
            response = client.post("/event-collector/events", json=evento_data)
            
            assert response.status_code == 400
            assert "ID de campaña debe ser un UUID válido" in response.json()["detail"]
    
    def test_procesar_evento_error_interno(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.side_effect = Exception("Error interno del handler")
        mock_handlers['procesar_evento'].return_value = mock_handler
        
        evento_data = {
            "tipo_evento": "CONVERSION",
            "id_afiliado": "AFILIADO_001",
            "valor_conversion": 99.99,
            "moneda": "USD"
        }
        
        response = client.post("/event-collector/events", json=evento_data)
        
        assert response.status_code == 500
        assert response.json()["detail"] == "Error interno del servidor"
    
    def test_procesar_evento_diferentes_tipos(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'exito': True,
            'id_evento': str(uuid.uuid4()),
            'estado': 'PUBLICADO'
        }
        mock_handlers['procesar_evento'].return_value = mock_handler
        
        tipos_evento = ["CLICK", "IMPRESSION", "CONVERSION", "PAGE_VIEW"]
        
        for tipo in tipos_evento:
            evento_data = {
                "tipo_evento": tipo,
                "id_afiliado": f"AFILIADO_{tipo}",
                "fuente_evento": "WEB_TAG"
            }
            
            response = client.post("/event-collector/events", json=evento_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["exito"] is True
    
    def test_procesar_evento_con_conversion(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'exito': True,
            'id_evento': str(uuid.uuid4()),
            'estado': 'PUBLICADO',
            'topic_destino': 'tracking.conversions'
        }
        mock_handlers['procesar_evento'].return_value = mock_handler
        
        evento_data = {
            "tipo_evento": "CONVERSION",
            "id_afiliado": "AFILIADO_ECOMMERCE",
            "id_campana": str(uuid.uuid4()),
            "datos_custom": {
                "order_id": "ORD-123",
                "customer_type": "premium"
            },
            "valor_conversion": 299.99,
            "moneda": "EUR",
            "tipo_dispositivo": "DESKTOP",
            "fuente_evento": "WEB_TAG"
        }
        
        response = client.post("/event-collector/events", json=evento_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["exito"] is True
        assert data["topic_destino"] == "tracking.conversions"


class TestReprocesarEventoEndpoint:
    
    def test_reprocesar_evento_exitoso(self, client, mock_handlers):
        id_evento = str(uuid.uuid4())
        
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'exito': True,
            'id_evento': id_evento,
            'razon': 'Evento reprocesado exitosamente'
        }
        mock_handlers['retry'].return_value = mock_handler
        
        request_data = {
            "id_evento": id_evento,
            "forzar_reproceso": False
        }
        
        response = client.post(
            f"/event-collector/events/{id_evento}/retry",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] is True
        assert data["id_evento"] == id_evento
        assert "reprocesado exitosamente" in data["mensaje"]
    
    def test_reprocesar_evento_forzado(self, client, mock_handlers):
        id_evento = str(uuid.uuid4())
        
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'exito': True,
            'id_evento': id_evento,
            'razon': 'Evento reprocesado forzadamente'
        }
        mock_handlers['retry'].return_value = mock_handler
        
        request_data = {
            "id_evento": id_evento,
            "forzar_reproceso": True
        }
        
        response = client.post(
            f"/event-collector/events/{id_evento}/retry",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] is True
    
    def test_reprocesar_evento_error(self, client, mock_handlers):
        id_evento = str(uuid.uuid4())
        
        mock_handler = AsyncMock()
        mock_handler.handle.side_effect = Exception("Error reprocesando evento")
        mock_handlers['retry'].return_value = mock_handler
        
        request_data = {"id_evento": id_evento}
        
        response = client.post(
            f"/event-collector/events/{id_evento}/retry",
            json=request_data
        )
        
        assert response.status_code == 500
        assert "Error reprocesando evento" in response.json()["detail"]


class TestEstadoEventoEndpoint:
    
    def test_obtener_estado_evento(self, client, mock_handlers):
        id_evento = str(uuid.uuid4())
        
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'id_evento': id_evento,
            'estado': 'PUBLICADO',
            'timestamp': datetime.now().isoformat(),
            'detalles': 'Evento procesado correctamente'
        }
        mock_handlers['estado'].return_value = mock_handler
        
        response = client.get(f"/event-collector/events/{id_evento}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id_evento'] == id_evento
        assert data['estado'] == 'PUBLICADO'
        assert 'timestamp' in data
    
    def test_obtener_estado_evento_error(self, client, mock_handlers):
        id_evento = str(uuid.uuid4())
        
        mock_handler = AsyncMock()
        mock_handler.handle.side_effect = Exception("Evento no encontrado")
        mock_handlers['estado'].return_value = mock_handler
        
        response = client.get(f"/event-collector/events/{id_evento}/status")
        
        assert response.status_code == 500
        assert "Evento no encontrado" in response.json()["detail"]


class TestEstadisticasEndpoint:
    
    def test_obtener_estadisticas_sin_filtros(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'estadisticas': 'EN_DESARROLLO',
            'mensaje': 'Estadísticas en desarrollo'
        }
        mock_handlers['estadisticas'].return_value = mock_handler
        
        response = client.get("/event-collector/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert 'estadisticas' in data
        assert 'mensaje' in data
    
    def test_obtener_estadisticas_con_filtros(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'total_eventos': 1500,
            'eventos_exitosos': 1425,
            'eventos_fallidos': 75,
            'tasa_exito': 95.0
        }
        mock_handlers['estadisticas'].return_value = mock_handler
        
        params = {
            'id_afiliado': 'AFILIADO_001',
            'tipo_evento': 'CLICK'
        }
        
        response = client.get("/event-collector/statistics", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_eventos' in data or 'estadisticas' in data


class TestEventosFallidosEndpoint:
    
    def test_obtener_eventos_fallidos(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'eventos_fallidos': [],
            'mensaje': 'Consulta de eventos fallidos en desarrollo'
        }
        mock_handlers['fallidos'].return_value = mock_handler
        
        response = client.get("/event-collector/failed-events")
        
        assert response.status_code == 200
        data = response.json()
        assert 'eventos_fallidos' in data
        assert 'mensaje' in data
    
    def test_obtener_eventos_fallidos_con_parametros(self, client, mock_handlers):
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'eventos_fallidos': [
                {
                    'id_evento': str(uuid.uuid4()),
                    'tipo_evento': 'CONVERSION',
                    'estado': 'FALLIDO',
                    'razon_fallo': 'Timeout de Pulsar'
                }
            ],
            'total': 1
        }
        mock_handlers['fallidos'].return_value = mock_handler
        
        params = {
            'id_afiliado': 'AFILIADO_001',
            'limite': 5,
            'solo_reintentables': 'true'
        }
        
        response = client.get("/event-collector/failed-events", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert 'eventos_fallidos' in data


class TestRateLimitEndpoint:
    
    def test_obtener_rate_limit_status(self, client, mock_handlers):
        id_afiliado = "AFILIADO_001"
        
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'id_afiliado': id_afiliado,
            'eventos_actuales': 50,
            'ventana_minutos': 1,
            'timestamp': datetime.now().isoformat()
        }
        mock_handlers['rate_limit'].return_value = mock_handler
        
        response = client.get(f"/event-collector/rate-limit/{id_afiliado}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id_afiliado'] == id_afiliado
        assert 'eventos_actuales' in data
        assert 'ventana_minutos' in data
        assert 'timestamp' in data
    
    def test_obtener_rate_limit_status_con_ventana(self, client, mock_handlers):
        id_afiliado = "AFILIADO_PREMIUM"
        
        mock_handler = AsyncMock()
        mock_handler.handle.return_value = {
            'id_afiliado': id_afiliado,
            'eventos_actuales': 250,
            'ventana_minutos': 5,
            'timestamp': datetime.now().isoformat()
        }
        mock_handlers['rate_limit'].return_value = mock_handler
        
        params = {'ventana_minutos': 5}
        response = client.get(f"/event-collector/rate-limit/{id_afiliado}", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data['ventana_minutos'] == 5


class TestEventCollectorIntegracion:
    
    def test_flujo_completo_evento_exitoso(self, client, mock_handlers):
        id_evento = str(uuid.uuid4())
        
        mock_proc_handler = AsyncMock()
        mock_proc_handler.handle.return_value = {
            'exito': True,
            'id_evento': id_evento,
            'estado': 'PUBLICADO'
        }
        mock_handlers['procesar_evento'].return_value = mock_proc_handler
        
        mock_estado_handler = AsyncMock()
        mock_estado_handler.handle.return_value = {
            'id_evento': id_evento,
            'estado': 'PUBLICADO',
            'timestamp': datetime.now().isoformat()
        }
        mock_handlers['estado'].return_value = mock_estado_handler
        
        evento_data = {
            "tipo_evento": "CLICK",
            "id_afiliado": "AFILIADO_INTEGRATION_TEST",
            "fuente_evento": "WEB_TAG"
        }
        
        proc_response = client.post("/event-collector/events", json=evento_data)
        assert proc_response.status_code == 201
        proc_data = proc_response.json()
        assert proc_data["exito"] is True
        
        estado_response = client.get(f"/event-collector/events/{id_evento}/status")
        assert estado_response.status_code == 200
        estado_data = estado_response.json()
        assert estado_data.get('estado') == 'PUBLICADO' or 'FUNCIONALIDAD_EN_DESARROLLO' in estado_data.get('estado', '')
    
    def test_flujo_evento_fallido_y_reintento(self, client, mock_handlers):
        id_evento = str(uuid.uuid4())
        
        mock_proc_handler = AsyncMock()
        mock_proc_handler.handle.return_value = {
            'exito': False,
            'id_evento': id_evento,
            'estado': 'FALLIDO',
            'razon': 'Error temporal de red'
        }
        mock_handlers['procesar_evento'].return_value = mock_proc_handler
        
        mock_retry_handler = AsyncMock()
        mock_retry_handler.handle.return_value = {
            'exito': True,
            'id_evento': id_evento,
            'razon': 'Evento reprocesado exitosamente'
        }
        mock_handlers['retry'].return_value = mock_retry_handler
        
        evento_data = {
            "tipo_evento": "CONVERSION",
            "id_afiliado": "AFILIADO_RETRY_TEST",
            "valor_conversion": 199.99,
            "moneda": "USD"
        }
        
        proc_response = client.post("/event-collector/events", json=evento_data)
        assert proc_response.status_code == 201
        proc_data = proc_response.json()
        assert proc_data["exito"] is False
        
        retry_data = {"id_evento": id_evento}
        retry_response = client.post(
            f"/event-collector/events/{id_evento}/retry",
            json=retry_data
        )
        assert retry_response.status_code == 200
        retry_result = retry_response.json()
        assert retry_result["exito"] is True