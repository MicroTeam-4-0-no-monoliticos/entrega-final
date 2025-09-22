# 🚀 Frontend AeroPartners - Despliegue en Kubernetes

Este frontend está configurado para conectarse a los servicios desplegados en Google Kubernetes Engine (GKE).

## 🌐 URLs de Servicios

### Servicios Principales
- **SAGA Orchestrator**: `http://34.10.122.141:8000`
- **Campaigns Proxy**: `http://34.10.122.141:8080`
- **Servicio de Pagos**: `http://34.10.122.141:8000`
- **Servicio de Reporting**: `http://34.10.122.141:8000`

### Servicios de Datos Mock
- **Servicio Datos v1**: `http://34.10.122.141:9001`
- **Servicio Datos v2**: `http://34.10.122.141:9002`

### Event Collector
- **Event Collector BFF**: `http://34.10.122.141:8000`

## 📁 Archivos del Frontend

### Archivos Principales
- `index.html` - Frontend original (localhost)
- `index-k8s.html` - Frontend para Kubernetes
- `test-k8s-connectivity.html` - Test de conectividad
- `config-k8s.js` - Configuración para K8s

### Archivos de Configuración
- `script-sagas.js` - Lógica de SAGAs (actualizado para K8s)
- `script.js` - Lógica general (actualizado para K8s)
- `styles.css` - Estilos CSS

## 🚀 Cómo Usar

### Opción 1: Servidor Web Local
```bash
# Usar Python
cd frontend
python -m http.server 3000

# O usar Live Server en VS Code
# Instalar extensión "Live Server" y hacer clic derecho en index-k8s.html
```

### Opción 2: Test de Conectividad
```bash
# Abrir directamente en el navegador
open frontend/test-k8s-connectivity.html
```

## 🔧 Configuración

### Tipos de Campaña Válidos
El frontend solo permite crear SAGAs con los siguientes tipos de campaña:
- **PROMOCIONAL** - Campañas promocionales
- **FIDELIZACION** - Campañas de fidelización
- **ADQUISICION** - Campañas de adquisición
- **RETENCION** - Campañas de retención

### Variables de Configuración
```javascript
const API_CONFIG = {
    sagas: 'http://34.10.122.141:8000',      // SAGA Orchestrator
    campaigns: 'http://34.10.122.141:8080',  // Campaigns Proxy
    payments: 'http://34.10.122.141:8000',   // Servicio de Pagos
    reporting: 'http://34.10.122.141:8000',  // Servicio de Reporting
    servicio_datos_v1: 'http://34.10.122.141:9001',  // Servicio Datos v1
    servicio_datos_v2: 'http://34.10.122.141:9002',  // Servicio Datos v2
    event_collector: 'http://34.10.122.141:8000'     // Event Collector
};
```

### Detección Automática de Entorno
El archivo `config-k8s.js` incluye detección automática:
- **Localhost**: Usa URLs locales
- **Otros dominios**: Usa URLs de Kubernetes

## 🧪 Testing

### Test de Conectividad
1. Abrir `test-k8s-connectivity.html`
2. Hacer clic en "Probar Todos los Servicios"
3. Verificar que todos los servicios respondan

### Test de SAGAs
1. Abrir `index-k8s.html`
2. Hacer clic en "SAGA Test"
3. Verificar que se cree una SAGA exitosamente

## 🐛 Solución de Problemas

### Error de CORS
```
Access to fetch at 'http://34.10.122.141:8000/saga/' from origin 'http://localhost:3000' has been blocked by CORS policy
```
**Solución**: Los servicios ya tienen CORS configurado. Verificar que estén funcionando.

### Servicios No Disponibles
```
Error loading SAGAs: TypeError: Failed to fetch
```
**Solución**: 
1. Verificar que los pods estén corriendo: `kubectl get pods -n aeropartners`
2. Verificar conectividad: `curl http://34.10.122.141:8000/health`

### SAGAs No Se Cargan
**Solución**: 
1. Verificar conexión con `http://34.10.122.141:8000/health`
2. Verificar que haya SAGAs en el sistema
3. Revisar la consola del navegador para errores

## 📊 Monitoreo

### Health Checks
- **SAGA Orchestrator**: `http://34.10.122.141:8000/health`
- **Campaigns Proxy**: `http://34.10.122.141:8080/health`
- **Servicio Datos v1**: `http://34.10.122.141:9001/health`
- **Servicio Datos v2**: `http://34.10.122.141:9002/health`

### Logs de Kubernetes
```bash
# Ver logs del SAGA Orchestrator
kubectl logs -n aeropartners deployment/saga-orchestrator-deployment

# Ver logs del consumer de SAGAs
kubectl logs -n aeropartners deployment/consumers-deployment -c saga-consumer

# Ver logs de la aplicación principal
kubectl logs -n aeropartners deployment/aeropartners-deployment
```

## 🔄 Actualización de URLs

Si las IPs cambian, actualizar en:
1. `script-sagas.js` - Línea 3
2. `script.js` - Línea 3
3. `config-k8s.js` - Línea 4-11
4. `test-k8s-connectivity.html` - Línea 15-22

## 📱 Funcionalidades Disponibles

### SAGAs
- ✅ **Listar SAGAs** - Ver todas las SAGAs
- ✅ **Crear SAGA** - Crear nueva SAGA completa
- ✅ **Ver Detalles** - Ver estado detallado de SAGA
- ✅ **SAGA Test** - Crear SAGA de prueba automática

### Estado en Tiempo Real
- ✅ **Indicadores de Estado** - Visual para cada paso
- ✅ **Actualización Automática** - Refresh de datos
- ✅ **Manejo de Errores** - Mensajes informativos

## 🎯 Próximos Pasos

1. **Desplegar Frontend en Firebase Hosting** (recomendado)
2. **Configurar Dominio Personalizado**
3. **Implementar HTTPS**
4. **Agregar Autenticación**

## 📞 Soporte

Para problemas con el frontend:
1. Verificar conectividad con `test-k8s-connectivity.html`
2. Revisar logs de Kubernetes
3. Verificar configuración de CORS en los servicios
