import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.aeropartners.modulos.saga.infraestructura.pulsar_consumer import SagaPulsarConsumer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SAGA Orchestrator",
    description="Orquestador de SAGAs para Aeropartners",
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

@app.get("/health")
async def health_check():
    """Health check del SAGA Orchestrator"""
    return {
        "status": "healthy",
        "service": "saga-orchestrator",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Información general del SAGA Orchestrator"""
    return {
        "mensaje": "SAGA Orchestrator - Aeropartners",
        "version": "1.0.0",
        "descripcion": "Orquestador de SAGAs para microservicios"
    }

@app.post("/sync-payment/{saga_id}/{payment_id}")
async def sync_payment_status(saga_id: str, payment_id: str):
    """Sincronizar manualmente el estado de un pago en una SAGA"""
    try:
        from src.aeropartners.modulos.saga.infraestructura.adaptadores import RepositorioSagaSQLAlchemy
        import httpx
        
        # Obtener la SAGA
        repo = RepositorioSagaSQLAlchemy()
        saga = repo.obtener_por_id(saga_id)
        
        if not saga:
            return {"error": f"SAGA {saga_id} no encontrada"}
        
        # Obtener el estado actual del pago
        try:
            response = httpx.get(f"http://aeropartners-app:8000/pagos/{payment_id}")
            if response.status_code == 200:
                payment_data = response.json()
                
                # Buscar el paso de pago en la SAGA
                for paso in saga.pasos:
                    if (paso.tipo.value == "PROCESAR_PAGO" and 
                        paso.resultado and 
                        paso.resultado.get('id_pago') == payment_id):
                        
                        # Actualizar el estado del pago en el resultado
                        paso.resultado['estado'] = payment_data['estado']
                        if payment_data.get('fecha_procesamiento'):
                            paso.resultado['fecha_procesamiento'] = payment_data['fecha_procesamiento']
                        
                        # Actualizar la SAGA en el repositorio
                        repo.actualizar(saga)
                        
                        return {
                            "success": True,
                            "message": f"Estado del pago {payment_id} sincronizado en SAGA {saga_id}",
                            "payment_status": payment_data['estado']
                        }
                
                return {"error": f"Paso de pago con ID {payment_id} no encontrado en SAGA {saga_id}"}
            else:
                return {"error": f"Error obteniendo estado del pago: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error consultando servicio de pagos: {str(e)}"}
            
    except Exception as e:
        return {"error": f"Error interno: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    
    # Iniciar el consumer de Pulsar en un hilo separado
    import threading
    
    def start_consumer():
        try:
            consumer = SagaPulsarConsumer()
            consumer.start_consuming()
        except Exception as e:
            logger.error(f"Error iniciando consumer de SAGA: {str(e)}")
    
    # Iniciar consumer en hilo separado
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    
    # Iniciar servidor FastAPI
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8091")),
        reload=False
    )
