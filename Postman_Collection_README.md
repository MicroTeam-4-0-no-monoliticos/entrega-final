# 📋 Colección de Postman - Aeropartners SAGA API

## 🚀 Descripción
Colección completa de Postman para probar la SAGA de campaña completa con verificación individual y operaciones de limpieza.

## 📁 Archivos
- `SAGA_Postman_Collection_Complete.json` - Colección completa actualizada
- `SAGA_Postman_Collection.json` - Colección original

## 🔧 Cómo Importar
1. Abre Postman
2. Click en "Import"
3. Selecciona el archivo `SAGA_Postman_Collection_Complete.json`
4. Click en "Import"

## 📊 Estructura de la Colección

### 1. **Health Checks** 🏥
Verificar que todos los servicios estén funcionando:
- **BFF Health** - `GET http://localhost:8090/health`
- **SAGA Orchestrator Health** - `GET http://localhost:8091/health`
- **Campaigns Proxy Health** - `GET http://localhost:8080/health`
- **Main App Health** - `GET http://localhost:8000/health`

### 2. **SAGA Operations** 🔄
Operaciones principales de la SAGA:
- **Create Complete Campaign SAGA** - Crear una SAGA completa
- **Get SAGA Status** - Verificar estado de una SAGA específica
- **List All SAGAs** - Listar todas las SAGAs
- **Delete Individual SAGA** - Eliminar una SAGA específica
- **Cleanup All SAGAs** - Limpiar todas las SAGAs
- **Cleanup Everything** - Limpiar todo (SAGAs + campañas + pagos)

### 3. **Campaign Operations** 📢
Operaciones con campañas:
- **Create Campaign Direct** - Crear campaña directamente
- **Get Campaign by ID** - Verificar campaña por ID
- **List All Campaigns** - Listar todas las campañas
- **Cancel Campaign** - Cancelar campaña (compensación)
- **Cleanup All Campaigns** - Limpiar todas las campañas

### 4. **Payment Operations** 💳
Operaciones con pagos:
- **Create Payment Direct** - Crear pago directamente
- **Get Payment by ID** - Verificar pago por ID
- **Revert Payment** - Revertir pago (compensación)
- **Cleanup All Payments** - Limpiar todos los pagos

### 5. **Report Operations** 📊
Operaciones con reportes:
- **Generate Report Direct** - Generar reporte directamente

### 6. **Testing Scenarios** 🧪
Escenarios de prueba predefinidos:
- **Test Successful SAGA** - SAGA que debe completarse exitosamente
- **Test Failed SAGA** - SAGA que falla para probar compensaciones

## 🔍 Variables de Entorno
La colección incluye variables para facilitar el uso:
- `{{saga_id}}` - ID de la SAGA
- `{{campaign_id}}` - ID de la campaña
- `{{payment_id}}` - ID del pago
- `{{$timestamp}}` - Timestamp automático para referencias únicas

## 📝 Cómo Usar

### 1. **Verificar Salud de Servicios**
```
1. Ejecutar todos los Health Checks
2. Verificar que todos retornen 200 OK
```

### 2. **Probar SAGA Exitosa**
```
1. Ejecutar "Test Successful SAGA"
2. Copiar el saga_id de la respuesta
3. Ejecutar "Get SAGA Status" con el ID
4. Verificar que el estado sea "COMPLETADA"
5. Verificar que no haya compensaciones
```

### 3. **Probar SAGA con Compensaciones**
```
1. Ejecutar "Test Failed SAGA" (usará referencia duplicada)
2. Copiar el saga_id de la respuesta
3. Ejecutar "Get SAGA Status" con el ID
4. Verificar que el estado sea "FALLIDA"
5. Verificar que haya compensaciones en el arreglo
6. Verificar que la campaña esté "CANCELADA"
7. Verificar que el pago esté "REVERSADO"
```

### 4. **Verificar Recursos Individuales**
```
1. Usar "Get Campaign by ID" con el campaign_id
2. Usar "Get Payment by ID" con el payment_id
3. Verificar estados: "BORRADOR"/"CANCELADA" y "EXITOSO"/"REVERSADO"
```

### 5. **Limpiar Datos de Prueba**
```
1. Usar "Cleanup Everything" para limpiar todo
2. O usar limpiezas individuales:
   - "Cleanup All SAGAs"
   - "Cleanup All Campaigns"
   - "Cleanup All Payments"
```

## 🎯 Flujo de Prueba Recomendado

### **Prueba Completa:**
1. **Health Checks** → Verificar servicios
2. **Test Successful SAGA** → Probar SAGA exitosa
3. **Get SAGA Status** → Verificar estado
4. **Get Campaign by ID** → Verificar campaña
5. **Get Payment by ID** → Verificar pago
6. **Test Failed SAGA** → Probar compensaciones
7. **Get SAGA Status** → Verificar compensaciones
8. **Get Campaign by ID** → Verificar cancelación
9. **Get Payment by ID** → Verificar reversión
10. **Cleanup Everything** → Limpiar datos

## ⚠️ Notas Importantes

- **Referencias de Pago**: Usar `{{$timestamp}}` para evitar duplicados
- **IDs**: Los IDs se generan automáticamente, copiarlos de las respuestas
- **Compensaciones**: Solo se ejecutan cuando hay fallos
- **Estados**: 
  - Campañas: `BORRADOR` → `CANCELADA`
  - Pagos: `PENDIENTE` → `EXITOSO` → `REVERSADO`
  - SAGAs: `INICIADA` → `COMPLETADA`/`FALLIDA`

## 🚨 Troubleshooting

### **Error 500 en SAGA:**
- Verificar que todos los servicios estén funcionando
- Revisar logs del SAGA Orchestrator

### **SAGA no se ejecuta:**
- Verificar que Pulsar esté funcionando
- Revisar logs del SAGA Orchestrator

### **Compensaciones no se ejecutan:**
- Verificar que los endpoints de compensación existan
- Revisar logs del SAGA Orchestrator

## 📞 Soporte
Para problemas o dudas, revisar los logs de los servicios:
- SAGA Orchestrator: `docker logs saga-orchestrator`
- BFF: `docker logs event-collector-bff`
- Campaigns Proxy: `docker logs campaigns-proxy`
- Main App: `docker logs aeropartners-app`
