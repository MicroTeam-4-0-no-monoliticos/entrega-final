"""
Servicio de Datos Mock v1
Simula un servicio de datos externo para el servicio de reporting
"""
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Servicio de Datos v1")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "v1"}

@app.get("/api/v1/pagos/report")
async def report_pagos():
    return {
        "version": "v1",
        "pagos": [
            {
                "id": "pago_001",
                "monto": 100.50,
                "moneda": "USD",
                "fecha": "2024-01-15T10:30:00Z",
                "estado": "exitoso",
                "afiliado_id": "aff_001"
            }
        ],
        "total_pagos": 1,
        "monto_total": 100.50
    }

@app.get("/api/v1/campanas/report")
async def report_campanas():
    return {
        "version": "v1",
        "campanas": [
            {
                "id": "camp_001",
                "nombre": "Campaña Invierno 2024",
                "estado": "activa",
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-03-31"
            }
        ],
        "total_campanas": 1
    }

@app.get("/api/v1/metricas/report")
async def report_metricas():
    return {
        "version": "v1",
        "metricas": {
            "total_ingresos": 1500.75,
            "total_pagos": 25,
            "campanas_activas": 3,
            "afiliados_activos": 15
        }
    }

# Endpoints adicionales que necesita el servicio de reportes
@app.get("/campaigns/")
async def campaigns_list():
    """Endpoint para listar campañas activas"""
    return {
        "version": "v1",
        "campanas": [
            {
                "id": "camp_001",
                "nombre": "Campaña Invierno 2024",
                "estado": "activa",
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-03-31",
                "presupuesto": {"monto": 10000.0}
            },
            {
                "id": "camp_002", 
                "nombre": "Campaña Primavera 2024",
                "estado": "activa",
                "fecha_inicio": "2024-03-01",
                "fecha_fin": "2024-05-31",
                "presupuesto": {"monto": 5000.0}
            }
        ],
        "total_campanas": 2
    }

@app.get("/campaigns/stats/general")
async def campaigns_stats_general():
    """Endpoint para estadísticas generales de campañas"""
    return {
        "version": "v1",
        "total_campanas": 2,
        "distribucion_por_estado": {
            "activa": 2,
            "inactiva": 0,
            "pausada": 0
        },
        "resumen": {
            "presupuesto_total": 15000.0,
            "gasto_total": 7500.0
        }
    }

@app.get("/pagos/outbox/estadisticas")
async def pagos_outbox_estadisticas():
    """Endpoint para estadísticas de pagos del outbox"""
    return {
        "version": "v1",
        "total_eventos": 15,
        "eventos_procesados": 12,
        "eventos_pendientes": 3,
        "eventos_fallidos": 0,
        "ultima_actualizacion": "2024-01-15T10:30:00Z"
    }

@app.get("/pagos/")
async def pagos_list():
    """Endpoint para listar pagos"""
    return [
        {
            "id": "pago_001",
            "monto": 100.50,
            "moneda": "USD",
            "fecha_creacion": "2024-01-15T10:30:00Z",
            "estado": "exitoso",
            "id_afiliado": "aff_001"
        },
        {
            "id": "pago_002",
            "monto": 250.75,
            "moneda": "USD", 
            "fecha_creacion": "2024-01-16T11:15:00Z",
            "estado": "exitoso",
            "id_afiliado": "aff_002"
        }
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
