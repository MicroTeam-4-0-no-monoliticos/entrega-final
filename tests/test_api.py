#!/usr/bin/env python3
"""
Script de prueba para la API del microservicio de pagos
"""

import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

def test_procesar_pago():
    """Prueba el endpoint de procesar pago"""
    print("🧪 Probando procesar pago...")
    
    payload = {
        "id_afiliado": f"afiliado_{uuid.uuid4().hex[:8]}",
        "monto": 150.75,
        "moneda": "USD"
    }
    
    response = requests.post(f"{BASE_URL}/pagos/", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Pago procesado exitosamente:")
        print(f"   ID: {data['id_pago']}")
        print(f"   Estado: {data['estado']}")
        print(f"   Referencia: {data['referencia_pago']}")
        return data['id_pago']
    else:
        print(f"❌ Error procesando pago: {response.status_code}")
        print(response.text)
        return None

def test_obtener_estado_pago(id_pago):
    """Prueba el endpoint de obtener estado de pago"""
    print(f"🧪 Probando obtener estado del pago {id_pago}...")
    
    response = requests.get(f"{BASE_URL}/pagos/{id_pago}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Estado obtenido:")
        print(f"   Estado: {data['estado']}")
        print(f"   Monto: {data['monto']} {data['moneda']}")
        if data['mensaje_error']:
            print(f"   Error: {data['mensaje_error']}")
    else:
        print(f"❌ Error obteniendo estado: {response.status_code}")
        print(response.text)

def test_procesar_outbox():
    """Prueba el endpoint de procesar outbox"""
    print("🧪 Probando procesar outbox...")
    
    response = requests.post(f"{BASE_URL}/pagos/outbox/procesar")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Outbox procesado:")
        print(f"   {data['mensaje']}")
    else:
        print(f"❌ Error procesando outbox: {response.status_code}")
        print(response.text)

def test_estadisticas_outbox():
    """Prueba el endpoint de estadísticas del outbox"""
    print("🧪 Probando estadísticas del outbox...")
    
    response = requests.get(f"{BASE_URL}/pagos/outbox/estadisticas")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Estadísticas obtenidas:")
        print(f"   Total eventos: {data['total_eventos']}")
        print(f"   Procesados: {data['eventos_procesados']}")
        print(f"   Pendientes: {data['eventos_pendientes']}")
    else:
        print(f"❌ Error obteniendo estadísticas: {response.status_code}")
        print(response.text)

def test_health_check():
    """Prueba el endpoint de health check"""
    print("🧪 Probando health check...")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check exitoso: {data['status']}")
    else:
        print(f"❌ Error en health check: {response.status_code}")

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de la API del microservicio de pagos")
    print("=" * 60)
    
    # Verificar que el servicio esté funcionando
    try:
        test_health_check()
        print()
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servicio. Asegúrate de que esté ejecutándose en http://localhost:8000")
        return
    
    # Procesar varios pagos
    ids_pagos = []
    for i in range(3):
        print(f"--- Procesando pago {i+1} ---")
        id_pago = test_procesar_pago()
        if id_pago:
            ids_pagos.append(id_pago)
        print()
        time.sleep(1)
    
    # Consultar estados de los pagos
    for i, id_pago in enumerate(ids_pagos):
        print(f"--- Consultando estado del pago {i+1} ---")
        test_obtener_estado_pago(id_pago)
        print()
    
    # Procesar outbox
    test_procesar_outbox()
    print()
    
    # Obtener estadísticas
    test_estadisticas_outbox()
    print()
    
    print("🎉 Pruebas completadas!")

if __name__ == "__main__":
    main()
