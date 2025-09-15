# Definición de Eventos por Escenario de Calidad - Aeropartners

## 1. Definición de Eventos por Escenario de Calidad

### Escenario #2: Confiabilidad (Zero-Downtime Failover)

**Tipo de Evento**: **Eventos de Integración CON CARGA DE ESTADO COMPLETA**

**Justificación**:
- La réplica del servicio de campañas necesita reconstruir su estado interno completo ante fallos
- El servicio de pagos debe tener toda la información necesaria para procesar transacciones sin consultas adicionales
- Garantiza recuperación ante fallos sin pérdida de datos críticos

**Esquema de Evento**:
```json
{
  "event_type": "CampanaEstadoCompleto",
  "event_id": "uuid",
  "timestamp": "2024-01-01T10:00:00Z",
  "schema_version": "v1",
  "data": {
    "id_campana": "string",
    "estado": "ACTIVE",
    "presupuesto_monto": 10000.00,
    "metricas_actuales": {
      "impresiones": 15000,
      "clicks": 450,
      "conversiones": 23
    },
    "configuracion_completa": {...},
    "metadatos_confiabilidad": {
      "version_esquema": "v1",
      "checksum_datos": "sha256_hash",
      "requiere_reconstruccion_estado": true
    }
  }
}
```

### Escenario #3: Procesamiento Único (Idempotencia)

**Tipo de Evento**: **Eventos de Integración CON CARGA MÍNIMA + IDEMPOTENCIA**

**Justificación**:
- Solo necesita información suficiente para detectar duplicados y garantizar procesamiento único
- Optimiza rendimiento al evitar transferir datos innecesarios
- Garantiza idempotencia mediante claves de idempotencia

**Esquema de Evento**:
```json
{
  "event_type": "PagoProcesado",
  "event_id": "uuid",
  "idempotency_key": "pago_123_20240101_afiliado_456",
  "data": {
    "id_pago": "string",
    "id_afiliado": "string",
    "monto": 100.50,
    "estado": "EXITOSO",
    "metadatos_idempotencia": {
      "hash_contenido": "sha256_hash",
      "intentos_procesamiento": 1,
      "ventana_idempotencia_segundos": 3600
    }
  }
}
```

### Escenario #9: Mantenibilidad (Version Switch)

**Tipo de Evento**: **Eventos de Integración CON VERSIONADO DINÁMICO**

**Justificación**:
- Permite evolución independiente de servicios sin afectar versiones existentes
- Facilita migración gradual entre versiones (v1 ↔ v2)
- Mantiene compatibilidad hacia atrás para servicios legacy

**Esquema de Evento**:
```json
{
  "event_type": "ReporteSolicitado",
  "event_id": "uuid",
  "schema_version": "v1",
  "compatibility_level": "BACKWARD",
  "data": {
    "id_solicitud": "string",
    "version_servicio_datos": "v2",
    "parametros": {...},
    "metadatos_versionado": {
      "compatibilidad_versiones": ["v1", "v1.1", "v2"],
      "deprecation_warning": false,
      "migration_path": "v1->v2"
    }
  }
}
```

## 2. Tecnología de Serialización: Avro vs Protobuf

### Decisión: **Apache Avro**

**Justificación**:

#### Ventajas de Avro:
- **Schema Evolution**: Soporte nativo para evolución de esquemas con compatibilidad hacia atrás y hacia adelante
- **Performance**: Serialización binaria más eficiente que JSON (30-50% mejor compresión)
- **Type Safety**: Validación de tipos en tiempo de compilación
- **Pulsar Integration**: Soporte nativo en Apache Pulsar con `AvroSchema`
- **Self-Describing**: Los esquemas se incluyen en los mensajes

#### Por qué NO Protobuf:
- **Menos flexibilidad** en evolución de esquemas
- **Requiere recompilación** para cambios de esquema
- **Menor integración** con el ecosistema Pulsar
- **Complejidad adicional** para desarrollo en Python

### Esquema Avro Implementado:

```json
{
  "type": "record",
  "name": "CampanaEstadoCompleto",
  "namespace": "com.aeropartners.confiabilidad.v1",
  "fields": [
    {"name": "event_type", "type": "string"},
    {"name": "event_id", "type": "string"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "schema_version", "type": "string"},
    {"name": "data", "type": {
      "type": "record",
      "name": "CampanaData",
      "fields": [
        {"name": "id_campana", "type": "string"},
        {"name": "estado", "type": "string"},
        {"name": "presupuesto_monto", "type": "double"},
        {"name": "metricas_actuales", "type": {
          "type": "record",
          "name": "Metricas",
          "fields": [
            {"name": "impresiones", "type": "int"},
            {"name": "clicks", "type": "int"},
            {"name": "conversiones", "type": "int"}
          ]
        }},
        {"name": "metadatos_confiabilidad", "type": {
          "type": "record",
          "name": "MetadatosConfiabilidad",
          "fields": [
            {"name": "version_esquema", "type": "string"},
            {"name": "checksum_datos", "type": "string"},
            {"name": "requiere_reconstruccion_estado", "type": "boolean"}
          ]
        }}
      ]
    }}
  ]
}
```

## 3. Event Stream Versioning Strategy

### Estrategia: **Schema Evolution con Versionado Semántico**

#### Niveles de Versionado:

1. **Schema Version** (v1, v1.1, v2)
2. **Service Version** (campaigns-svc-v1, campaigns-svc-v2)
3. **API Version** (api-v1, api-v2)

#### Reglas de Compatibilidad por Escenario:

| Escenario | Compatibilidad | Justificación |
|-----------|----------------|---------------|
| **#2 Confiabilidad** | FULL | Cambios solo aditivos, campos existentes nunca se eliminan |
| **#3 Idempotencia** | BACKWARD | Nuevos campos opcionales, campos existentes pueden volverse opcionales |
| **#9 Mantenibilidad** | BACKWARD | Soporte múltiples versiones simultáneas, migración gradual |

#### Implementación de Schema Registry:

```python
class SchemaRegistry:
    def __init__(self):
        self.compatibility_rules = {
            "confiabilidad": "FULL",
            "idempotencia": "BACKWARD", 
            "mantenibilidad": "BACKWARD"
        }
    
    def register_schema(self, namespace: str, version: str, schema: dict, compatibility: str):
        """Registra esquema con validación de compatibilidad"""
        if not self._validate_compatibility(namespace, version, schema, compatibility):
            raise IncompatibleSchemaError(f"Schema {namespace}:{version} no es compatible")
        
        self.schemas[f"{namespace}:{version}"] = schema
        return True
```

### Topics de Pulsar con Versionado:

```
# Escenario #2: Confiabilidad
confiabilidad.campanas.estado-completo.v1
confiabilidad.pagos.estado-completo.v1

# Escenario #3: Idempotencia  
idempotencia.pagos.procesado.v1
idempotencia.campanas.creada.v1

# Escenario #9: Mantenibilidad
mantenibilidad.reportes.solicitado.v1
mantenibilidad.reportes.solicitado.v2
mantenibilidad.reportes.solicitado.latest
```

### Configuración de Pulsar:

```python
# Producer con schema Avro
producer = client.create_producer(
    topic="confiabilidad.campanas.estado-completo.v1",
    schema=AvroSchema(CampanaEstadoCompleto),
    send_timeout_millis=30000,
    batching_enabled=True
)

# Consumer con failover
consumer = client.subscribe(
    topic="confiabilidad.campanas.estado-completo.v1",
    subscription_name="campaigns-failover",
    subscription_type=SubscriptionType.Failover,
    schema=AvroSchema(CampanaEstadoCompleto)
)
```

## 4. Justificaciones de Decisión

### **Eventos con Carga de Estado vs Integración**:

- **Confiabilidad**: Requiere **carga de estado completa** para reconstrucción ante fallos
- **Idempotencia**: Usa **carga mínima** con claves de idempotencia para eficiencia
- **Mantenibilidad**: Implementa **versionado dinámico** para evolución independiente

### **Avro sobre Protobuf**:

- **Mejor integración** con Apache Pulsar
- **Evolución de esquemas** más flexible
- **Menor complejidad** de implementación en Python
- **Performance superior** en serialización binaria

### **Event Stream Versioning**:

- **Estrategia híbrida** según necesidades de cada escenario
- **Compatibilidad diferenciada** por tipo de evento
- **Migración gradual** sin downtime
- **Schema Registry** para gestión centralizada