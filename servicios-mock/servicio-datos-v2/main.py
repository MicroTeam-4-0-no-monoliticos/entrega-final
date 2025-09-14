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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
