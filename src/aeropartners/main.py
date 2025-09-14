from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.pagos import router as pagos_router
from .api.campanas import router as campanas_router
from .seedwork.infraestructura.db import engine
from .modulos.pagos.infraestructura.modelos import Base
from .modulos.campanas.infraestructura.modelos import CampanaModel, EventInboxModel, OutboxCampanasModel

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aeropartners - Microservicios",
    description="Microservicios de pagos y campañas para la plataforma Aeropartners implementando DDD y Arquitectura Hexagonal",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(pagos_router)
app.include_router(campanas_router)

@app.get("/")
async def root():
    return {
        "mensaje": "Bienvenido a los Microservicios de Aeropartners",
        "version": "1.0.0",
        "servicios": {
            "pagos": {
                "procesar_pago": "POST /pagos/",
                "obtener_estado": "GET /pagos/{id_pago}",
                "estadisticas_outbox": "GET /pagos/outbox/estadisticas"
            },
            "campanas": {
                "crear_campana": "POST /campaigns/",
                "obtener_campana": "GET /campaigns/{id_campana}",
                "listar_campanas": "GET /campaigns/",
                "activar_campana": "PATCH /campaigns/{id_campana}/activate",
                "actualizar_presupuesto": "PATCH /campaigns/{id_campana}/budget",
                "metricas": "GET /campaigns/{id_campana}/metrics",
                "health": "GET /campaigns/health"
            }
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "aeropartners-microservices"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
