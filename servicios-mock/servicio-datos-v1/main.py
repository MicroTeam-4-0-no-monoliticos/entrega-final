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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
