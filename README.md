# Aeropartners - Plataforma de Microservicios

## Descripción del Sistema

Esta plataforma implementa una **arquitectura de microservicios** completa para "Aeropartners", siguiendo los principios de **Domain-Driven Design (DDD)**, **Arquitectura Hexagonal** y **Event-Driven Architecture**. El sistema incluye servicios de pagos, gestión de campañas, reportes en tiempo real y un BFF (Backend for Frontend) para la recolección de eventos.

### Escenarios de Calidad Implementados

#### Escenario #2: Zero-Downtime cuando un microservicio falla
En la operación normal, el servicio de partner puede fallar en uno de sus pods, el sistema debe ser capaz de seguir recibiendo request sin afectación del servicio y de los demás servicios que dependen de Campañas. El sistema mantiene un 99.99% de disponibilidad, cero perdida de eventos y recuperación en menos de 2 minutos.

#### Escenario #3: Procesamiento único y sin duplicados en transacciones financieras
En la operación normal, los partners envían eventos de pago o conversión que, por fallas de red, pueden llegar duplicados o desordenados. El sistema debe procesarlos una sola vez, evitando pagos o comisiones repetidas y manteniendo la trazabilidad en tiempo real, incluso bajo alta carga.

#### Escenario #9: Zero-Downtime Version Switch en Reportes
El servicio de reportes permite cambiar entre versiones (v1 simple, v2 detallada) sin interrumpir el servicio, garantizando disponibilidad continua mientras se despliegan nuevas funcionalidades.

## Arquitectura y Componentes

### 1. Microservicio de Pagos

**Bounded Context:** Procesamiento de pagos a afiliados

**Agregados Principales:**
- `Pago`: Modela el ciclo de vida completo con estados `PENDIENTE`, `PROCESANDO`, `EXITOSO`, `FALLIDO`
- Protege invariantes de negocio (no reprocesamiento)
- Genera eventos de dominio (`PagoExitoso`, `PagoFallido`)

**Objetos de Valor:**
- `Dinero`: Encapsula monto y moneda con validaciones
- `Moneda`: Enum con monedas soportadas (USD, EUR, COP)

**Puertos y Adaptadores:**
- `PasarelaDePagos` (Puerto): Interfaz para pasarelas externas
- `StripeAdapter` (Adaptador): Implementación con simulación de latencia y fallos

### 2. Microservicio de Campañas

**Bounded Context:** Gestión de campañas publicitarias

**Características:**
- Creación y gestión de campañas con presupuestos
- Estados de campaña (CREATED, ACTIVE, PAUSED, COMPLETED)
- Métricas y seguimiento de rendimiento
- Failover automático con réplicas

**Implementación:**
- Servicio primario y réplica con proxy de failover
- Consumer pattern para procesamiento de eventos
- Outbox pattern para consistencia eventual

### 3. Servicio de Reportes

**Bounded Context:** Reporting y analytics en tiempo real

**Características Clave:**
- **Zero-Downtime Version Switch**: Cambio v1 ↔ v2 sin reiniciar
- **Read Model CQRS**: Proyección optimizada desde eventos de Pulsar
- **Real-Time Updates**: Actualización automática desde eventos
- **Feature Flags**: Control de versiones dinámico

**Versiones Disponibles:**
- **v1**: Reporte simple con totales básicos
- **v2**: Reporte detallado con breakdowns y métricas avanzadas (compatible hacia atrás)

**Topics Monitoreados:**
- `payments.evt.pending/completed/failed`
- `campaigns.evt.created/activated/updated`

### 4. Event Collector BFF

**Bounded Context:** Backend for Frontend para recolección de eventos

**Características:**
- Agregación de eventos desde múltiples fuentes
- Normalización y validación de datos
- Enrutamiento inteligente a servicios backend
- Cache y optimización de consultas

## Stack Tecnológico

- **Lenguaje:** Python 3.11+
- **Framework:** FastAPI
- **Base de Datos:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Migraciones:** Alembic
- **Message Broker:** Apache Pulsar 3.1.0
- **Contenerización:** Docker y Docker Compose
- **Patrones:** DDD, CQRS, Event Sourcing, Outbox Pattern

## Estructura del Proyecto

```
src/aeropartners/
├── api/                    # Capa de presentación
│   ├── pagos.py           
│   ├── campanas.py 
│   ├── event_collector.py        
│   └── reportes.py        
├── modulos/
│   ├── pagos/               # Bounded context de pagos
│   │   ├── aplicacion/      # CQS (comandos, queries, handlers)
│   │   ├── dominio/         # DDD (entidades, eventos, reglas)
│   │   └── infraestructura/ # Adaptadores, outbox, consumer
│   ├── campanas/            # Bounded context de campañas
│   │   ├── aplicacion/
│   │   ├── dominio/
│   │   └── infraestructura/
│   └── reportes/          # Bounded context de reportes
│       ├── aplicacion/
│       │   ├── queries.py
│       │   └── handlers_v1_v2.py
│       ├── dominio/
│       │   ├── modelos.py
│       │   └── repositorios.py
│       └── infraestructura/
│           ├── modelos.py
│           ├── repos.py
│           └── pulsar_consumer.py
├── seedwork/              # Código compartido
│   ├── aplicacion/        # Base classes para CQS
│   ├── dominio/           # Base classes para DDD
│   └── infraestructura/   # DB, Pulsar producer
└── main.py               # Punto de entrada principal
```

## Arquitectura de Servicios

El sistema despliega los siguientes contenedores:

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `aeropartners-app` | 8000 | API principal (FastAPI) |
| `campaigns-proxy` | 8080 | Proxy con failover para campañas |
| `event-collector-bff` | 8090 | BFF para recolección de eventos |
| `campaigns-svc` | 8001 | Servicio de campañas primario |
| `campaigns-svc-replica` | 8002 | Servicio de campañas réplica |
| `servicio-datos-v1` | 9001 | Mock service v1 |
| `servicio-datos-v2` | 9002 | Mock service v2 |
| `aeropartners-postgres` | 5433 | Base de datos PostgreSQL |
| `aeropartners-pulsar` | 6650, 8081 | Apache Pulsar (broker + admin) |

## Endpoints Principales

### API de Pagos
```
POST /pagos/                    # Procesar nuevo pago
GET  /pagos/{id_pago}           # Obtener estado del pago
GET  /pagos/outbox/estadisticas # Estadísticas del outbox
```

### API de Campañas
```
POST /campaigns/               # Crear campaña
GET  /campaigns/               # Listar campañas
GET  /campaigns/{id}           # Obtener campaña específica
PATCH /campaigns/{id}/activate # Activar campaña
PATCH /campaigns/{id}/budget   # Actualizar presupuesto
GET  /campaigns/{id}/metrics   # Métricas de campaña
```

### API de Reportes
```
GET  /api/reports/payments     # Endpoint único (v1/v2 dinámico)
GET  /api/reports/version      # Obtener versión activa
PUT  /api/reports/version      # Cambiar versión sin downtime
GET  /api/reports/health       # Health check
```

### Event Collector BFF
```
GET  /event-collector/health   # Health check del BFF
POST /event-collector/events   # Recolectar eventos
```

## Guía de Despliegue

### Prerrequisitos

#### Opción A: Docker Desktop (Recomendado)
Descargar desde: https://www.docker.com/products/docker-desktop/

#### Opción B: Colima (macOS alternativo)
```bash
# Instalar Homebrew si no está instalado
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Colima y Docker
brew install colima docker docker-compose

# Iniciar Colima
colima start

# Verificar instalación
docker --version
docker-compose --version
```

### Despliegue con Docker Compose

```bash
# Navegar al directorio del proyecto
cd entrega-final

# Verificar que Docker esté corriendo
docker ps

# Levantar todos los servicios
docker-compose up -d --build

# Verificar estado de los servicios
docker-compose ps
```

### Servicios Desplegados

Después del despliegue deberían estar corriendo:
- `aeropartners-postgres` (Base de datos)
- `aeropartners-pulsar` (Message broker)
- `aeropartners-app` (API principal)
- `campaigns-svc` + `campaigns-svc-replica` (Servicios de campañas)
- `campaigns-proxy` (Proxy con failover)
- `event-collector-bff` (BFF)
- `servicio-datos-v1` + `servicio-datos-v2` (Mock services)
- Múltiples consumers y processors

## Pruebas del Sistema

### Colección de Postman (Recomendado)

Para probar todos los microservicios de manera integrada, importa la colección de Postman incluida en el proyecto:

**Archivo:** `Aeropartners.postman_collection.json`

#### Importar la Colección:

1. **Abrir Postman**
2. **Importar** → **Upload Files** → Seleccionar `Aeropartners.postman_collection.json`
3. **Import** para cargar la colección completa

#### Estructura de la Colección:

```
Aeropartners - Complete API Collection
├── Health Checks (todos los servicios)
├── Event Collector BFF
├── Servicio de Pagos
├── Servicio de Campañas
└── Servicio de Reportes
```

#### Variables Configuradas:

La colección incluye variables pre-configuradas para todos los servicios:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `aeropartners_url` | `http://localhost:8000` | API principal |
| `event_collector_bff_url` | `http://localhost:8090` | Event Collector BFF |
| `campaigns_proxy_url` | `http://localhost:8080` | Proxy de campañas |
| `campaigns_primary_url` | `http://localhost:8001` | Campañas primario |
| `campaigns_replica_url` | `http://localhost:8002` | Campañas réplica |
| `servicio_datos_v1_url` | `http://localhost:9001` | Mock service v1 |
| `servicio_datos_v2_url` | `http://localhost:9002` | Mock service v2 |

#### Flujo de Prueba Recomendado:

1. **Health Checks** → Verificar que todos los servicios estén corriendo
2. **Event Collector BFF** → Generar eventos de prueba
3. **Pagos** → Crear pagos que generen eventos
4. **Reportes v1** → Ver reportes básicos
5. **Reportes v2** → Cambiar versión sin downtime
6. **Campañas** → Gestionar campañas
7. **Rate Limiting** → Probar límites del BFF

#### Características Avanzadas:

- **Scripts Automáticos**: Extracción automática de IDs entre requests
- **Variables Dinámicas**: Timestamps y UUIDs únicos
- **Tests Integrados**: Validación automática de respuestas
- **Headers Realistas**: User-Agent, Session-ID, Webhook signatures


### URLs de Servicios

| Servicio | URL | Descripción |
|----------|-----|-------------|
| API Principal | http://localhost:8000 | Documentación: `/docs` |
| Proxy Campañas | http://localhost:8080 | Con failover automático |
| Event Collector BFF | http://localhost:8090 | Backend for Frontend |
| Pulsar Admin | http://localhost:8081 | Interfaz administrativa |
| Mock Service v1 | http://localhost:9001 | Servicio de datos v1 |
| Mock Service v2 | http://localhost:9002 | Servicio de datos v2 |

### Verificar Logs

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs específicos
docker-compose logs -f aeropartners-app
docker-compose logs -f event-collector-bff
docker-compose logs -f campaigns-proxy
```

### Verificar Base de Datos

```bash
# Conectar a PostgreSQL
docker exec -it aeropartners-postgres psql -U postgres -d aeropartners

# Ver todas las tablas
\dt

# Ver cada uno de los registros
SELECT * FROM <<tabla>>;

# Salir
\q
```


## Características Destacadas

### Zero-Downtime Version Switch
- Cambio instantáneo entre versiones de reportes
- Sin reinicio de contenedores
- Compatibilidad hacia atrás garantizada

### Event-Driven Architecture
- Apache Pulsar para messaging confiable
- Outbox pattern para consistencia
- Procesamiento asíncrono de eventos

### Microservicios con DDD
- Bounded contexts bien definidos
- Agregados que protegen invariantes
- Separación clara de responsabilidades

### Failover y Resilencia
- Proxy con failover automático
- Réplicas de servicios críticos
- Health checks y monitoreo

### Observabilidad
- Logs estructurados
- Health checks en todos los servicios
- Métricas de Pulsar disponibles

## Despliegue en Kubernetes (GKE)

### Prerrequisitos para K8s

- **Google Cloud SDK** instalado y configurado
- **kubectl** configurado para el cluster GKE
- **Docker** para construir imágenes
- **Google Artifact Registry** configurado

### Configuración del Cluster

```bash
# Crear cluster GKE
gcloud container clusters create aeropartners-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5

# Configurar kubectl
gcloud container clusters get-credentials aeropartners-cluster --zone=us-central1-a
```

### Despliegue de Servicios

```bash
# Aplicar configuraciones base
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-secret.yaml

# Desplegar base de datos
kubectl apply -f k8s/04-postgres-deployment.yaml
kubectl apply -f k8s/05-postgres-service.yaml

# Desplegar Pulsar
kubectl apply -f k8s/06-pulsar-deployment.yaml
kubectl apply -f k8s/07-pulsar-service.yaml

# Desplegar aplicación principal
kubectl apply -f k8s/08-main-deployment.yaml
kubectl apply -f k8s/09-main-service.yaml

# Desplegar servicios de datos
kubectl apply -f k8s/10-servicio-datos-v1-deployment.yaml
kubectl apply -f k8s/11-servicio-datos-v2-deployment.yaml

# Desplegar consumers
kubectl apply -f k8s/12-consumers-deployment.yaml

# Exponer servicios
kubectl apply -f k8s/13-ingress.yaml
```

### URLs de Producción

| Servicio | URL | Descripción |
|----------|-----|-------------|
| API Principal | http://34.10.122.141:8000 | Backend principal |
| Frontend | https://misw-4406-entrega-final.web.app | Aplicación web |
| Cloud Run Proxy | https://saga-proxy-557335216999.us-central1.run.app | Proxy HTTPS para SAGAs |

### Verificar Despliegue

```bash
# Ver estado de pods
kubectl get pods -n aeropartners

# Ver logs de servicios
kubectl logs -n aeropartners deployment/aeropartners-deployment -c aeropartners-main

# Verificar servicios
kubectl get svc -n aeropartners
```

## Frontend (Firebase Hosting)

### Estructura del Frontend

```
frontend/
├── public/
│   ├── index.html              # Página principal
│   ├── script-sagas.js         # Lógica de SAGAs
│   ├── styles.css              # Estilos
│   └── config-https.js         # Configuración HTTPS
└── firebase.json               # Configuración Firebase
```

### Características del Frontend

- **Interfaz de SAGAs**: Creación y monitoreo de SAGAs
- **Validación de Tipos**: Solo permite tipos válidos de campañas
- **Monitoreo en Tiempo Real**: Estado de SAGAs y compensaciones
- **Proxy HTTPS**: Comunicación segura con backend K8s
- **Responsive Design**: Compatible con dispositivos móviles

### Despliegue a Firebase

```bash
# Instalar Firebase CLI
npm install -g firebase-tools

# Iniciar sesión
firebase login

# Inicializar proyecto
firebase init hosting

# Desplegar
firebase deploy --hosting
```

### Configuración de CORS

El backend está configurado para aceptar requests desde:
- `https://misw-4406-entrega-final.web.app` (Producción)
- `http://localhost:5500` (Desarrollo local)
- `http://127.0.0.1:5500` (Desarrollo local)

## SAGA Orchestrator

### Características del SAGA

- **Orquestación Completa**: Campañas → Pagos → Reportes
- **Compensaciones Automáticas**: Rollback en caso de fallos
- **Estados Granulares**: INICIADA, COMPLETADA, FALLIDA
- **Monitoreo en Tiempo Real**: Estado de cada paso
- **Persistencia**: Base de datos PostgreSQL

### Tipos de Campañas Soportadas

- `PROMOCIONAL`
- `FIDELIZACION` 
- `ADQUISICION`
- `RETENCION`

### Endpoints de SAGA

```
POST /saga/crear-campana-completa    # Crear nueva SAGA
GET  /saga/                          # Listar todas las SAGAs
GET  /saga/{id}/status               # Estado detallado de SAGA
```

### Ejemplo de Uso

```bash
# Crear SAGA
curl -X POST "https://saga-proxy-557335216999.us-central1.run.app/saga/crear-campana-completa" \
  -H "Content-Type: application/json" \
  -d '{
    "campana": {
      "tipo": "PROMOCIONAL",
      "nombre": "Campaña Test",
      "descripcion": "Prueba del sistema",
      "fecha_inicio": "2025-01-01",
      "fecha_fin": "2025-12-31",
      "presupuesto": 10000
    },
    "pago": {
      "afiliado_id": "afiliado_001",
      "monto": 5000,
      "metodo_pago": "TARJETA_CREDITO",
      "numero_tarjeta": "4111111111111111",
      "fecha_vencimiento": "2025-12-31",
      "cvv": "123"
    },
    "reporte": {
      "tipo": "CAMPAÑA_COMPLETA",
      "filtros": {
        "fecha_inicio": "2025-01-01",
        "fecha_fin": "2025-12-31"
      }
    }
  }'

# Ver estado de SAGA
curl "https://saga-proxy-557335216999.us-central1.run.app/saga/{saga_id}/status"
```

## Detener el Sistema

### Docker Compose (Desarrollo Local)

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Limpiar imágenes no utilizadas
docker system prune -f
```

### Kubernetes (Producción)

```bash
# Eliminar namespace completo
kubectl delete namespace aeropartners

# Eliminar cluster (cuidado!)
gcloud container clusters delete aeropartners-cluster --zone=us-central1-a
```