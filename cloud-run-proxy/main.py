import functions_framework
import requests
from flask import jsonify, request
from flask_cors import CORS
import json

@functions_framework.http
def proxy_sagas(request):
    """
    Proxy HTTPS para los endpoints de SAGAs
    Maneja: GET /saga/, POST /saga/crear-campana-completa, GET /saga/{id}/status
    """
    
    # URL base del backend K8s
    BACKEND_URL = "http://34.10.122.141:8000"
    
    # Configurar CORS headers
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Manejar preflight OPTIONS
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        return add_cors_headers(response)
    
    try:
        # Extraer el path y método
        path = request.path
        method = request.method
        
        print(f"Procesando: {method} {path}")
        
        # GET /saga/ (listar todas las SAGAs)
        if method == 'GET' and path == '/saga/':
            print("Listando SAGAs...")
            response = requests.get(f'{BACKEND_URL}/saga/')
            response.raise_for_status()
            result = jsonify(response.json())
            return add_cors_headers(result)
        
        # POST /saga/crear-campana-completa (crear nueva SAGA)
        elif method == 'POST' and path == '/saga/crear-campana-completa':
            print("Creando SAGA...")
            data = request.get_json()
            print(f"Datos recibidos: {data}")
            response = requests.post(f'{BACKEND_URL}/saga/crear-campana-completa', json=data)
            response.raise_for_status()
            result = jsonify(response.json())
            return add_cors_headers(result)
        
        # GET /saga/{id}/status (ver detalle de SAGA)
        elif method == 'GET' and path.startswith('/saga/') and path.endswith('/status'):
            saga_id = path.split('/')[2]  # Extraer ID de la URL
            print(f"Obteniendo detalle de SAGA: {saga_id}")
            response = requests.get(f'{BACKEND_URL}/saga/{saga_id}/status')
            response.raise_for_status()
            result = jsonify(response.json())
            return add_cors_headers(result)
        
        # Método/Path no soportado
        else:
            result = jsonify({
                "error": "Endpoint no soportado",
                "method": method,
                "path": path
            })
            result.status_code = 404
            return add_cors_headers(result)
            
    except requests.exceptions.RequestException as e:
        print(f"Error en request al backend: {e}")
        result = jsonify({
            "error": "Error conectando con el backend",
            "details": str(e)
        })
        result.status_code = 500
        return add_cors_headers(result)
        
    except Exception as e:
        print(f"Error interno: {e}")
        result = jsonify({
            "error": "Error interno del servidor",
            "details": str(e)
        })
        result.status_code = 500
        return add_cors_headers(result)
