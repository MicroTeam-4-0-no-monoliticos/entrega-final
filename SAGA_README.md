# SAGA Orchestrator - Aeropartners

## Descripción

El SAGA Orchestrator es un componente que implementa el patrón SAGA para orquestar transacciones distribuidas entre los microservicios de Aeropartners. Permite crear campañas completas que involucran múltiples servicios de forma atómica con compensaciones automáticas.

## Arquitectura

### Patrón SAGA Orquestada

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cliente       │───►│  BFF (Event      │───►│  SAGA           │
│                 │    │   Collector)     │    │  Orchestrator   │
└─────────────────┘    └──────────────────┘    └─────────┬───────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Proxy          │◄───│  Campañas        │◄───│  Paso 1:        │
│  Campañas       │    │  Service         │    │  Crear Campaña  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Pagos          │◄───│  Aeropartners    │◄───│  Paso 2:        │
│  Service        │    │  App             │    │  Procesar Pago  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Reporting      │◄───│  Aeropartners    │◄───│  Paso 3:        │
│  Service        │    │  App             │    │  Generar Reporte│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Flujo de Compensación

Si cualquier paso falla, se ejecutan las compensaciones en orden inverso:

1. **Cancelar Reporte** (si se generó)
2. **Revertir Pago** (si se procesó)
3. **Cancelar Campaña** (si se creó)

## Componentes

### 1. SAGA Orchestrator Service
- **Puerto**: 8091
- **Responsabilidades**:
  - Orquestar los pasos de la SAGA
  - Manejar compensaciones automáticas
  - Persistir estado en SAGA Log
  - Comunicarse con Pulsar

### 2. SAGA Log (PostgreSQL)
- **Tablas**:
  - `saga_log`: Estado general de las SAGAs
  - `saga_pasos`: Pasos individuales ejecutados
  - `saga_compensaciones`: Compensaciones ejecutadas
  - `saga_events`: Eventos publicados a Pulsar

### 3. Eventos de Pulsar
- **Topic**: `saga-events`
- **Eventos**:
  - `SagaIniciada`
  - `SagaPasoEjecutado`
  - `SagaCampañaCreada`
  - `SagaPagoProcesado`
  - `SagaReporteGenerado`
  - `SagaCompletada`
  - `SagaFallida`
  - `SagaCompensacionIniciada`
  - `SagaCompensacionCompletada`

## API Endpoints

### BFF (Puerto 8090)

#### Crear Campaña Completa
```http
POST /saga/crear-campana-completa
Content-Type: application/json

{
  "campana": {
    "nombre": "Campaña Test",
    "tipo": "PROMOCIONAL",
    "presupuesto": {
      "monto": 1000.0,
      "moneda": "USD"
    },
    "fecha_inicio": "2025-01-01T00:00:00",
    "fecha_fin": "2025-12-31T23:59:59",
    "id_afiliado": "afiliado_test",
    "descripcion": "Campaña de prueba"
  },
  "pago": {
    "id_afiliado": "afiliado_test",
    "monto": 1000.0,
    "moneda": "USD",
    "referencia_pago": "ref_test"
  },
  "reporte": {
    "tipo_reporte": "metricas_generales",
    "filtros": {
      "fecha_inicio": "2025-01-01",
      "fecha_fin": "2025-12-31"
    }
  },
  "timeout_minutos": 30
}
```

#### Obtener Estado de SAGA
```http
GET /saga/{saga_id}/status
```

#### Listar SAGAs
```http
GET /saga/?estado=COMPLETADA&pagina=1&limite=10
```

### SAGA Orchestrator (Puerto 8091)

#### Health Check
```http
GET /health
```

## Estados de SAGA

- **INICIADA**: SAGA creada, esperando ejecución
- **CAMPAÑA_CREADA**: Paso 1 completado
- **PAGO_PROCESADO**: Paso 2 completado
- **REPORTE_GENERADO**: Paso 3 completado
- **COMPLETADA**: Todos los pasos exitosos
- **FALLIDA**: Algún paso falló
- **COMPENSANDO**: Ejecutando compensaciones
- **COMPENSADA**: Compensaciones completadas

## Compensaciones

### Crear Campaña → Cancelar Campaña
- **Endpoint**: `PATCH /api/campaigns/{id}/cancel`
- **Acción**: Marcar campaña como "CANCELADA"

### Procesar Pago → Revertir Pago
- **Endpoint**: `PATCH /pagos/{id}/revertir`
- **Acción**: Marcar pago como "REVERTIDO"

### Generar Reporte → Cancelar Reporte
- **Endpoint**: `PATCH /reporting/{id}/cancel`
- **Acción**: Marcar reporte como "CANCELADO"

## Uso

### 1. Iniciar Servicios
```bash
docker-compose up -d
```

### 2. Verificar Health Checks
```bash
curl http://localhost:8090/health  # BFF
curl http://localhost:8091/health  # SAGA Orchestrator
```

### 3. Probar SAGA
```bash
python scripts/test_saga.py
```

### 4. Monitorear Logs
```bash
docker logs saga-orchestrator -f
docker logs event-collector-bff -f
```

## Configuración

### Variables de Entorno

#### SAGA Orchestrator
- `DATABASE_URL`: URL de PostgreSQL
- `PULSAR_URL`: URL de Apache Pulsar
- `PORT`: Puerto del servicio (default: 8091)

#### BFF
- `DATABASE_URL`: URL de PostgreSQL
- `PULSAR_URL`: URL de Apache Pulsar

## Monitoreo

### Logs Importantes
- **SAGA Iniciada**: `SAGA {id} iniciada: {tipo}`
- **Paso Ejecutado**: `Paso {paso_id} de SAGA {saga_id} ejecutado exitosamente`
- **Paso Fallido**: `Paso {paso_id} de SAGA {saga_id} falló: {error}`
- **Compensación**: `Compensación iniciada para SAGA {saga_id}`

### Métricas
- Total de SAGAs por estado
- Tiempo promedio de ejecución
- Tasa de éxito/fallo
- Compensaciones ejecutadas

## Troubleshooting

### Problemas Comunes

1. **SAGA no inicia**
   - Verificar conexión a PostgreSQL
   - Verificar conexión a Pulsar
   - Revisar logs del SAGA Orchestrator

2. **Paso falla**
   - Verificar que el servicio destino esté disponible
   - Revisar logs del servicio específico
   - Verificar formato de datos

3. **Compensación falla**
   - Verificar que el servicio soporte la operación de compensación
   - Revisar logs de la compensación
   - Verificar estado de los datos

### Comandos de Debug

```bash
# Ver estado de SAGAs
curl "http://localhost:8090/saga/?estado=FALLIDA"

# Ver logs de SAGA específica
curl "http://localhost:8090/saga/{saga_id}/status"

# Ver logs del orchestrator
docker logs saga-orchestrator --tail 50

# Ver logs de Pulsar
docker logs aeropartners-pulsar --tail 20
```

## Desarrollo

### Estructura del Código
```
src/aeropartners/modulos/saga/
├── aplicacion/
│   ├── comandos.py          # Comandos de SAGA
│   └── handlers.py          # Handlers de comandos
├── dominio/
│   ├── entidades.py         # Entidades de dominio
│   ├── eventos.py           # Eventos de dominio
│   └── repositorios.py      # Interfaces de repositorio
└── infraestructura/
    ├── adaptadores.py       # Implementación de repositorio
    ├── modelos.py           # Modelos de base de datos
    └── pulsar_consumer.py   # Consumer de Pulsar
```

### Agregar Nuevo Paso

1. Agregar tipo en `TipoPaso` enum
2. Implementar lógica en `_ejecutar_paso_servicio`
3. Agregar compensación en `_ejecutar_compensacion_servicio`
4. Actualizar handlers de eventos

### Agregar Nueva Compensación

1. Agregar tipo en `TipoPaso` enum
2. Implementar endpoint en servicio destino
3. Agregar lógica en `_ejecutar_compensacion_servicio`
4. Actualizar `IniciarCompensacionHandler`
