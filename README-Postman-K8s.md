# 🚀 Aeropartners - Colección Postman para Kubernetes

Esta colección de Postman está configurada para probar todos los microservicios de Aeropartners desplegados en Google Kubernetes Engine (GKE).

## 📋 Archivos Incluidos

- `Aeropartners-K8s.postman_collection.json` - Colección principal con todos los endpoints
- `Aeropartners-K8s.postman_environment.json` - Variables de entorno para K8s
- `README-Postman-K8s.md` - Este archivo de instrucciones

## 🌐 URLs del Despliegue K8s

| Servicio | URL | Puerto | Descripción |
|----------|-----|--------|-------------|
| **Aeropartners Principal** | `http://34.10.122.141:8000` | 8000 | API principal con todos los microservicios |
| **Campaigns Proxy** | `http://34.10.122.141:8080` | 8080 | Proxy de campañas con failover |
| **Servicio Datos v1** | `http://34.10.122.141:9001` | 9001 | Mock de datos versión 1 |
| **Servicio Datos v2** | `http://34.10.122.141:9002` | 9002 | Mock de datos versión 2 |

## 🔧 Configuración en Postman

### 1. Importar la Colección
1. Abre Postman
2. Click en "Import"
3. Selecciona `Aeropartners-K8s.postman_collection.json`
4. Click "Import"

### 2. Importar el Environment
1. Click en "Import"
2. Selecciona `Aeropartners-K8s.postman_environment.json`
3. Click "Import"
4. Selecciona el environment "Aeropartners - Kubernetes Environment"

## 📚 Estructura de la Colección

### 🏥 Health Checks
- **Aeropartners Principal** - Verificar estado de la aplicación principal
- **SAGA Orchestrator** - Verificar estado del orquestador de SAGAs
- **Campaigns Proxy** - Verificar estado del proxy de campañas
- **Servicio Datos v1** - Verificar estado del mock de datos v1
- **Servicio Datos v2** - Verificar estado del mock de datos v2

### 🔄 SAGA Orchestrator
- **Crear Campaña Completa** - Crear una SAGA completa (campaña + pago + reporte)
- **Listar SAGAs** - Ver todas las SAGAs
- **Obtener Estado SAGA** - Ver el estado detallado de una SAGA específica
- **Eliminar SAGA** - Eliminar una SAGA específica
- **Limpiar SAGAs** - Limpiar todas las SAGAs
- **Limpiar Todo** - Limpiar todos los datos (SAGAs, campañas, pagos)

### 💳 Pagos
- **Procesar Pago** - Crear un nuevo pago
- **Obtener Estado Pago** - Ver el estado de un pago específico
- **Revertir Pago** - Revertir un pago (compensación)
- **Limpiar Pagos** - Limpiar todos los pagos
- **Estadísticas Outbox Pagos** - Ver estadísticas del outbox de pagos

### 📢 Campañas
- **Crear Campaña** - Crear una nueva campaña
- **Listar Campañas** - Ver todas las campañas con paginación
- **Obtener Campaña** - Ver una campaña específica
- **Actualizar Presupuesto** - Modificar el presupuesto de una campaña
- **Activar Campaña** - Activar una campaña
- **Pausar Campaña** - Pausar una campaña
- **Cancelar Campaña** - Cancelar una campaña
- **Estadísticas Generales** - Ver estadísticas de campañas
- **Limpiar Campañas** - Limpiar todas las campañas

### 📊 Reporting
- **Generar Reporte** - Crear un nuevo reporte
- **Obtener Reporte** - Ver un reporte específico
- **Listar Reportes** - Ver todos los reportes
- **Actualizar Servicio Datos** - Cambiar el servicio de datos activo
- **Obtener Configuración** - Ver la configuración actual
- **Verificar Servicio** - Verificar conectividad de un servicio

### 📡 Event Collector BFF
- **Procesar Evento Tracking** - Enviar un evento de tracking
- **Obtener Estado Evento** - Ver el estado de un evento
- **Reprocesar Evento Fallido** - Reintentar un evento fallido
- **Estadísticas Processing** - Ver estadísticas de procesamiento
- **Eventos Fallidos** - Ver eventos que fallaron
- **Rate Limit Status** - Ver estado del rate limiting

### 🎭 Servicios de Datos Mock
- **Servicio Datos v1 - Generar Datos** - Generar datos con el servicio v1
- **Servicio Datos v2 - Generar Datos** - Generar datos con el servicio v2
- **Servicio Datos v1 - Listar Datos** - Ver datos generados por v1
- **Servicio Datos v2 - Listar Datos** - Ver datos generados por v2

### 📖 Documentación API
- **OpenAPI JSON** - Ver la especificación OpenAPI completa
- **Swagger UI** - Interfaz web de documentación

## 🚀 Flujo de Pruebas Recomendado

### 1. Verificar Salud del Sistema
```
Health Checks → Aeropartners Principal - Health
Health Checks → SAGA Orchestrator - Health
Health Checks → Servicio Datos v1 - Health
Health Checks → Servicio Datos v2 - Health
```

### 2. Probar SAGA Completa
```
SAGA Orchestrator → Crear Campaña Completa
SAGA Orchestrator → Listar SAGAs
SAGA Orchestrator → Obtener Estado SAGA (usar saga_id de la respuesta anterior)
```

### 3. Probar Servicios Individuales
```
Pagos → Procesar Pago
Campañas → Crear Campaña
Reporting → Generar Reporte
Event Collector BFF → Procesar Evento Tracking
```

### 4. Probar Cambio de Servicio de Datos
```
Reporting → Obtener Configuración
Reporting → Actualizar Servicio Datos (cambiar a v2)
Reporting → Verificar Servicio
Reporting → Generar Reporte
```

## 🔧 Variables de Entorno

La colección incluye las siguientes variables:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `aeropartners_k8s_url` | `http://34.10.122.141:8000` | URL base de la aplicación principal |
| `campaigns_proxy_k8s_url` | `http://34.10.122.141:8080` | URL del proxy de campañas |
| `servicio_datos_v1_k8s_url` | `http://34.10.122.141:9001` | URL del servicio de datos v1 |
| `servicio_datos_v2_k8s_url` | `http://34.10.122.141:9002` | URL del servicio de datos v2 |
| `saga_id` | (dinámico) | ID de SAGA para pruebas |
| `pago_id` | (dinámico) | ID de pago para pruebas |
| `campana_id` | (dinámico) | ID de campaña para pruebas |
| `reporte_id` | (dinámico) | ID de reporte para pruebas |
| `evento_id` | (dinámico) | ID de evento para pruebas |

## 📝 Notas Importantes

1. **IP Externa**: La IP `34.10.122.141` es la IP externa del LoadBalancer de GKE
2. **Puertos**: Cada servicio está expuesto en un puerto diferente
3. **Variables Dinámicas**: Los IDs se llenan automáticamente en las respuestas
4. **Timeouts**: Las SAGAs pueden tomar 10-15 segundos para completarse
5. **Limpieza**: Usa los endpoints de limpieza para resetear el estado entre pruebas

## 🐛 Troubleshooting

### Si un endpoint no responde:
1. Verifica que el pod esté corriendo: `kubectl get pods -n aeropartners`
2. Verifica el health check del servicio
3. Revisa los logs: `kubectl logs -n aeropartners deployment/[nombre-deployment]`

### Si las SAGAs no progresan:
1. Verifica que Pulsar esté funcionando
2. Revisa los logs del SAGA Orchestrator
3. Verifica que los consumers estén corriendo

## 🎯 Próximos Pasos

1. **Importar** la colección y environment en Postman
2. **Ejecutar** los Health Checks para verificar conectividad
3. **Probar** la creación de una SAGA completa
4. **Explorar** los diferentes endpoints según tus necesidades
5. **Monitorear** el progreso de las SAGAs en tiempo real

¡Disfruta probando el sistema Aeropartners en Kubernetes! 🚀
