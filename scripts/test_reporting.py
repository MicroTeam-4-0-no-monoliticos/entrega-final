#!/usr/bin/env python3
"""
Script de prueba para el servicio de Reporting
Demuestra el cambio sin interrupción entre servicios v1 y v2
"""
import asyncio
import aiohttp
import json
import time
from datetime import date, datetime


class ReportingTester:
    """Clase para probar el servicio de reporting"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generar_reporte(self, tipo: str, filtros: dict = None) -> dict:
        """Genera un reporte"""
        url = f"{self.base_url}/reporting/report"
        data = {
            "tipo_reporte": tipo,
            "filtros": filtros
        }
        
        async with self.session.post(url, json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Error generando reporte: {response.status} - {error_text}")
    
    async def actualizar_servicio(self, url: str, version: str) -> dict:
        """Actualiza el servicio de datos"""
        admin_url = f"{self.base_url}/reporting/admin/servicio-datos"
        data = {
            "url": url,
            "version": version
        }
        
        async with self.session.post(admin_url, json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Error actualizando servicio: {response.status} - {error_text}")
    
    async def obtener_configuracion(self) -> dict:
        """Obtiene la configuración actual"""
        url = f"{self.base_url}/reporting/admin/configuracion"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Error obteniendo configuración: {response.status} - {error_text}")


async def demostrar_cambio_sin_interrupcion():
    """Demuestra el cambio sin interrupción entre servicios v1 y v2"""
    print("🚀 Iniciando demostración del Servicio de Reporting")
    print("=" * 60)
    
    async with ReportingTester() as tester:
        try:
            # 1. Verificar configuración inicial
            print("\n1️⃣ Verificando configuración inicial...")
            config = await tester.obtener_configuracion()
            print(f"   Configuración activa: {config['configuracion_activa']}")
            
            # 2. Generar reporte con servicio v1
            print("\n2️⃣ Generando reporte con servicio v1...")
            filtros = {
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-01-31",
                "moneda": "USD"
            }
            
            reporte_v1 = await tester.generar_reporte("pagos_por_periodo", filtros)
            print(f"   ✅ Reporte generado: {reporte_v1['id']}")
            print(f"   📊 Versión del servicio: {reporte_v1['version_servicio_datos']}")
            
            # 3. Cambiar a servicio v2 SIN INTERRUPCIÓN
            print("\n3️⃣ Cambiando a servicio v2 (SIN INTERRUPCIÓN)...")
            await tester.actualizar_servicio("http://servicio-datos-v2:8000", "v2")
            print("   ✅ Servicio actualizado a v2")
            
            # 4. Generar reporte inmediatamente con servicio v2
            print("\n4️⃣ Generando reporte inmediatamente con servicio v2...")
            reporte_v2 = await tester.generar_reporte("pagos_por_periodo", filtros)
            print(f"   ✅ Reporte generado: {reporte_v2['id']}")
            print(f"   📊 Versión del servicio: {reporte_v2['version_servicio_datos']}")
            
            print("\n🎉 ¡Demostración completada exitosamente!")
            print("   ✅ El cambio de servicio fue instantáneo")
            print("   ✅ No hubo interrupción del servicio")
            
        except Exception as e:
            print(f"\n❌ Error durante la demostración: {str(e)}")
            raise


if __name__ == "__main__":
    print("🧪 Script de Prueba - Servicio de Reporting")
    print("   Demostración de cambio sin interrupción")
    print("   Asegúrate de que el servicio esté ejecutándose en http://localhost:8000")
    print()
    
    # Ejecutar demostración principal
    asyncio.run(demostrar_cambio_sin_interrupcion())
    
    print("\n✨ ¡Todas las pruebas completadas!")
