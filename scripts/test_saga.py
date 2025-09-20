#!/usr/bin/env python3
"""
Script de prueba para la SAGA de creación de campaña completa
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuración
BFF_URL = "http://localhost:8090"
SAGA_URL = "http://localhost:8091"

def test_saga_campana_completa():
    """Probar la SAGA de creación de campaña completa"""
    
    print("🚀 Iniciando prueba de SAGA de campaña completa...")
    
    # Datos de prueba
    datos_campana = {
        "nombre": "Campaña SAGA Test",
        "tipo": "PROMOCIONAL",
        "presupuesto": {
            "monto": 1000.0,
            "moneda": "USD"
        },
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-12-31T23:59:59",
        "id_afiliado": "afiliado_saga_test",
        "descripcion": "Campaña de prueba para SAGA"
    }
    
    datos_pago = {
        "id_afiliado": "afiliado_saga_test",
        "monto": 1000.0,
        "moneda": "USD",
        "referencia_pago": "saga_test_payment"
    }
    
    datos_reporte = {
        "tipo_reporte": "metricas_generales",
        "filtros": {
            "fecha_inicio": "2025-01-01",
            "fecha_fin": "2025-12-31"
        }
    }
    
    # 1. Crear SAGA de campaña completa
    print("\n📝 Paso 1: Creando SAGA de campaña completa...")
    
    payload = {
        "campana": datos_campana,
        "pago": datos_pago,
        "reporte": datos_reporte,
        "timeout_minutos": 30
    }
    
    try:
        response = requests.post(
            f"{BFF_URL}/saga/crear-campana-completa",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            saga_data = response.json()
            saga_id = saga_data["saga_id"]
            print(f"✅ SAGA creada exitosamente: {saga_id}")
            print(f"   Estado inicial: {saga_data['estado']}")
        else:
            print(f"❌ Error creando SAGA: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error en la petición: {str(e)}")
        return
    
    # 2. Monitorear el estado de la SAGA
    print(f"\n👀 Paso 2: Monitoreando estado de SAGA {saga_id}...")
    
    max_intentos = 30  # 5 minutos máximo
    intento = 0
    
    while intento < max_intentos:
        try:
            response = requests.get(f"{BFF_URL}/saga/{saga_id}/status")
            
            if response.status_code == 200:
                status = response.json()
                estado = status["estado"]
                pasos = status["pasos"]
                compensaciones = status["compensaciones"]
                
                print(f"   Estado actual: {estado}")
                print(f"   Pasos ejecutados: {len(pasos)}")
                print(f"   Compensaciones: {len(compensaciones)}")
                
                # Mostrar detalles de pasos
                for i, paso in enumerate(pasos, 1):
                    estado_paso = "✅" if paso["exitoso"] else "❌" if paso["error"] else "⏳"
                    print(f"     Paso {i} ({paso['tipo']}): {estado_paso}")
                    if paso["error"]:
                        print(f"       Error: {paso['error']}")
                
                # Verificar si la SAGA está completa o fallida
                if estado in ["COMPLETADA", "FALLIDA", "COMPENSADA"]:
                    print(f"\n🏁 SAGA finalizada con estado: {estado}")
                    if estado == "COMPLETADA":
                        print("✅ ¡SAGA completada exitosamente!")
                    elif estado == "FALLIDA":
                        print("❌ SAGA falló")
                    elif estado == "COMPENSADA":
                        print("🔄 SAGA compensada")
                    break
                
            else:
                print(f"❌ Error obteniendo estado: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error monitoreando SAGA: {str(e)}")
        
        intento += 1
        time.sleep(10)  # Esperar 10 segundos entre verificaciones
    
    if intento >= max_intentos:
        print("⏰ Timeout: La SAGA no se completó en el tiempo esperado")
    
    # 3. Listar SAGAs
    print(f"\n📋 Paso 3: Listando SAGAs...")
    
    try:
        response = requests.get(f"{BFF_URL}/saga/")
        
        if response.status_code == 200:
            sagas_data = response.json()
            print(f"   Total de SAGAs: {sagas_data['total']}")
            
            for saga in sagas_data["sagas"][:5]:  # Mostrar solo las primeras 5
                print(f"   - SAGA {saga['saga_id'][:8]}... ({saga['estado']})")
        else:
            print(f"❌ Error listando SAGAs: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error listando SAGAs: {str(e)}")

def test_health_checks():
    """Probar health checks de los servicios"""
    
    print("🏥 Verificando health checks...")
    
    services = [
        ("BFF", f"{BFF_URL}/health"),
        ("SAGA Orchestrator", f"{SAGA_URL}/health"),
        ("Campaigns Proxy", "http://localhost:8080/health"),
        ("Aeropartners App", "http://localhost:8000/health")
    ]
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: OK")
            else:
                print(f"   ❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Error - {str(e)}")

if __name__ == "__main__":
    print("🧪 Iniciando pruebas de SAGA...")
    print("=" * 50)
    
    # Verificar health checks primero
    test_health_checks()
    
    print("\n" + "=" * 50)
    
    # Probar SAGA
    test_saga_campana_completa()
    
    print("\n🏁 Pruebas completadas")
