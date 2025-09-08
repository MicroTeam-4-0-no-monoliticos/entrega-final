import pytest
import requests
import time
import uuid

BASE_URL = "http://localhost:8000"
MAX_WAIT_TIME = 60  # Segundos máximo para esperar procesamiento
POLL_INTERVAL = 2   # Segundos entre verificaciones


class TestPagosAPI:
    """Clase de pruebas para la API de pagos"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup que se ejecuta antes de cada prueba"""
        # Verificar que el servicio esté funcionando
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code != 200:
                pytest.skip("Servicio no disponible")
        except requests.exceptions.RequestException:
            pytest.skip("No se puede conectar al servicio")
    
    def test_health_check(self):
        """Prueba que el health check funcione correctamente"""
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'service' in data
    
    def test_procesar_pago_creacion(self):
        """Prueba que se pueda crear un pago correctamente"""
        payload = {
            "id_afiliado": f"afiliado_{uuid.uuid4().hex[:8]}",
            "monto": 150.75,
            "moneda": "USD",
            "referencia_pago": f"ref_{uuid.uuid4().hex[:8]}"
        }
        
        response = requests.post(f"{BASE_URL}/pagos/", json=payload, timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estructura de respuesta
        assert 'id_pago' in data
        assert 'estado' in data
        assert 'referencia_pago' in data
        assert 'monto' in data
        assert 'moneda' in data
        
        # Validar valores
        assert data['estado'] == 'PENDIENTE'
        assert data['monto'] == 150.75
        assert data['moneda'] == 'USD'
        assert data['referencia_pago'] == payload['referencia_pago']
        
        # Validar que el ID sea un UUID válido
        assert len(data['id_pago']) == 36  # UUID tiene 36 caracteres
        assert data['id_pago'].count('-') == 4  # UUID tiene 4 guiones
    
    def test_obtener_estado_pago(self):
        """Prueba que se pueda obtener el estado de un pago"""
        # Primero crear un pago
        payload = {
            "id_afiliado": f"afiliado_{uuid.uuid4().hex[:8]}",
            "monto": 200.50,
            "moneda": "EUR",
            "referencia_pago": f"ref_{uuid.uuid4().hex[:8]}"
        }
        
        create_response = requests.post(f"{BASE_URL}/pagos/", json=payload, timeout=10)
        assert create_response.status_code == 200
        
        pago_data = create_response.json()
        pago_id = pago_data['id_pago']
        
        # Ahora obtener el estado
        response = requests.get(f"{BASE_URL}/pagos/{pago_id}", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estructura de respuesta
        assert 'id' in data
        assert 'estado' in data
        assert 'monto' in data
        assert 'moneda' in data
        assert 'fecha_creacion' in data
        
        # Validar valores
        assert data['id'] == pago_id
        assert data['estado'] == 'PENDIENTE'  # Estado inicial
        assert data['monto'] == 200.50
        assert data['moneda'] == 'EUR'
    
    def test_estadisticas_outbox(self):
        """Prueba que se puedan obtener las estadísticas del outbox"""
        response = requests.get(f"{BASE_URL}/pagos/outbox/estadisticas", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estructura de respuesta
        assert 'total_eventos' in data
        assert 'eventos_procesados' in data
        assert 'eventos_pendientes' in data
        
        # Validar que los valores sean números enteros
        assert isinstance(data['total_eventos'], int)
        assert isinstance(data['eventos_procesados'], int)
        assert isinstance(data['eventos_pendientes'], int)
        
        # Validar lógica de negocio
        assert data['eventos_procesados'] + data['eventos_pendientes'] == data['total_eventos']
        assert data['total_eventos'] >= 0
        assert data['eventos_procesados'] >= 0
        assert data['eventos_pendientes'] >= 0
    
    def test_procesar_pago_flujo_completo(self):
        """Prueba el flujo completo: crear pago y esperar procesamiento"""
        # Crear pago
        payload = {
            "id_afiliado": f"afiliado_{uuid.uuid4().hex[:8]}",
            "monto": 100.00,
            "moneda": "USD",
            "referencia_pago": f"ref_{uuid.uuid4().hex[:8]}"
        }
        
        create_response = requests.post(f"{BASE_URL}/pagos/", json=payload, timeout=10)
        assert create_response.status_code == 200
        
        pago_data = create_response.json()
        pago_id = pago_data['id_pago']
        
        # Verificar estado inicial
        assert pago_data['estado'] == 'PENDIENTE'
        
        # Esperar procesamiento
        start_time = time.time()
        procesado = False
        
        while time.time() - start_time < MAX_WAIT_TIME:
            response = requests.get(f"{BASE_URL}/pagos/{pago_id}", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            estado = data['estado']
            
            if estado in ['EXITOSO', 'FALLIDO']:
                procesado = True
                break
            
            time.sleep(POLL_INTERVAL)
        
        # Verificar que el pago fue procesado
        assert procesado, f"El pago no fue procesado en {MAX_WAIT_TIME} segundos"
        
        # Verificar estado final
        final_response = requests.get(f"{BASE_URL}/pagos/{pago_id}", timeout=10)
        assert final_response.status_code == 200
        
        final_data = final_response.json()
        assert final_data['estado'] in ['EXITOSO', 'FALLIDO']
        
        # Si es exitoso, verificar que no hay mensaje de error
        if final_data['estado'] == 'EXITOSO':
            assert final_data.get('mensaje_error') is None
        else:
            # Si falló, debe haber un mensaje de error
            assert final_data.get('mensaje_error') is not None
    
    def test_pago_con_datos_invalidos(self):
        """Prueba que se manejen correctamente los datos inválidos"""
        # Pago con monto negativo
        payload_invalid = {
            "id_afiliado": f"afiliado_{uuid.uuid4().hex[:8]}",
            "monto": -100.00,  # Monto negativo
            "moneda": "USD",
            "referencia_pago": f"ref_{uuid.uuid4().hex[:8]}"
        }
        
        response = requests.post(f"{BASE_URL}/pagos/", json=payload_invalid, timeout=10)
        
        # Debería fallar con 422 (Unprocessable Entity) o similar
        assert response.status_code in [400, 422]
    
    def test_obtener_pago_inexistente(self):
        """Prueba que se maneje correctamente un pago que no existe"""
        pago_id_inexistente = str(uuid.uuid4())
        
        response = requests.get(f"{BASE_URL}/pagos/{pago_id_inexistente}", timeout=10)
        
        # Debería retornar 404 (Not Found)
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
