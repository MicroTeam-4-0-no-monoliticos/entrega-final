"""
Servicio de Datos Mock v2
Simula un servicio de datos externo mejorado para el servicio de reporting
"""
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Servicio de Datos v2")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "v2"}

@app.get("/api/v2/payments/report")
async def report_payments():
    return {
        "version": "v2",
        "data": {
            "payments": [
                {
                    "payment_id": "pago_001",
                    "amount": 100.50,
                    "currency": "USD",
                    "created_at": "2024-01-15T10:30:00Z",
                    "status": "completed",
                    "affiliate_id": "aff_001",
                    "campaign_id": "camp_001",
                    "commission_rate": 0.15
                }
            ],
            "summary": {
                "total_payments": 1,
                "total_amount": 100.50,
                "average_amount": 100.50,
                "success_rate": 1.0
            }
        },
        "metadata": {
            "generated_at": "2024-01-15T10:30:00Z"
        }
    }

@app.get("/api/v2/campaigns/report")
async def report_campaigns():
    return {
        "version": "v2",
        "data": {
            "campaigns": [
                {
                    "campaign_id": "camp_001",
                    "name": "Winter Campaign 2024",
                    "status": "active",
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31",
                    "budget": 10000.00,
                    "spent": 7500.00
                }
            ],
            "summary": {
                "total_campaigns": 1,
                "active_campaigns": 1,
                "total_budget": 10000.00
            }
        },
        "metadata": {
            "generated_at": "2024-01-15T10:30:00Z"
        }
    }

@app.get("/api/v2/metrics/report")
async def report_metrics():
    return {
        "version": "v2",
        "data": {
            "metrics": {
                "total_revenue": 1500.75,
                "total_payments": 25,
                "active_campaigns": 3,
                "active_affiliates": 15,
                "conversion_rate": 0.12,
                "average_order_value": 60.03
            },
            "trends": {
                "revenue_growth": 0.15,
                "payment_growth": 0.08
            }
        },
        "metadata": {
            "generated_at": "2024-01-15T10:30:00Z"
        }
    }

@app.get("/campaigns/")
async def campaigns_list():
    """Endpoint para listar campañas activas"""
    return {
        "version": "v2",
        "data": {
            "campaigns": [
                {
                    "id": "camp_001",
                    "nombre": "Winter Campaign 2024",
                    "tipo": "PROMOCIONAL",
                    "estado": "ACTIVA",
                    "presupuesto": 10000.00,
                    "gasto_actual": 7500.00,
                    "fecha_inicio": "2024-01-01",
                    "fecha_fin": "2024-03-31",
                    "clicks": 1500,
                    "conversiones": 180,
                    "ingresos": 1500.75
                },
                {
                    "id": "camp_002",
                    "nombre": "Spring Sale 2024",
                    "tipo": "FIDELIZACION",
                    "estado": "ACTIVA",
                    "presupuesto": 5000.00,
                    "gasto_actual": 2500.00,
                    "fecha_inicio": "2024-03-01",
                    "fecha_fin": "2024-05-31",
                    "clicks": 800,
                    "conversiones": 95,
                    "ingresos": 750.25
                }
            ],
            "total": 2,
            "activas": 2,
            "presupuesto_total": 15000.00,
            "gasto_total": 10000.00
        },
        "metadata": {
            "generated_at": "2024-01-15T10:30:00Z"
        }
    }

@app.get("/pagos/outbox/estadisticas")
async def pagos_outbox_estadisticas():
    """Endpoint para estadísticas de pagos del outbox"""
    return {
        "version": "v2",
        "data": {
            "total_eventos": 25,
            "eventos_procesados": 22,
            "eventos_pendientes": 3,
            "eventos_fallidos": 0,
            "ultima_actualizacion": "2024-01-15T10:30:00Z",
            "estadisticas_por_periodo": {
                "2024-01": {
                    "total_pagos": 8,
                    "monto_total": 1250.50,
                    "moneda": "USD",
                    "estado": "procesado"
                },
                "2024-02": {
                    "total_pagos": 12,
                    "monto_total": 2100.75,
                    "moneda": "USD",
                    "estado": "procesado"
                },
                "2024-03": {
                    "total_pagos": 5,
                    "monto_total": 750.25,
                    "moneda": "USD",
                    "estado": "pendiente"
                }
            },
            "resumen": {
                "total_pagos": 25,
                "monto_total": 4101.50,
                "tasa_procesamiento": 0.88,
                "moneda_principal": "USD"
            }
        },
        "metadata": {
            "generated_at": "2024-01-15T10:30:00Z"
        }
    }

@app.get("/campaigns/stats/general")
async def campaigns_stats_general():
    """Endpoint que espera el servicio de reportes"""
    return {
        "version": "v2",
        "data": {
            "campaigns": [
                {
                    "campaign_id": "camp_001",
                    "name": "Winter Campaign 2024",
                    "status": "active",
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31",
                    "budget": 10000.00,
                    "spent": 7500.00,
                    "clicks": 1500,
                    "conversions": 180,
                    "revenue": 1500.75
                }
            ],
            "summary": {
                "total_campaigns": 1,
                "active_campaigns": 1,
                "total_budget": 10000.00,
                "total_spent": 7500.00,
                "total_clicks": 1500,
                "total_conversions": 180,
                "total_revenue": 1500.75,
                "conversion_rate": 0.12,
                "roi": 0.20
            }
        },
        "metadata": {
            "generated_at": "2024-01-15T10:30:00Z"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
