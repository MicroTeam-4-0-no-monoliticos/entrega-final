# AeroPartners Frontend

Frontend básico para la gestión de campañas y SAGAs del sistema AeroPartners.

## 🚀 Características

- **Dashboard** con métricas en tiempo real
- **Gestión de Campañas** - Ver, crear y administrar campañas
- **Gestión de SAGAs** - Monitorear y crear SAGAs completas
- **Gestión de Pagos** - Visualizar pagos y transacciones
- **Herramientas de Prueba** - Limpiar datos y crear datos de prueba
- **Interfaz Responsiva** - Funciona en desktop y móvil

## 🛠️ Tecnologías

- **HTML5** - Estructura semántica
- **CSS3** - Estilos modernos con gradientes y animaciones
- **JavaScript ES6+** - Funcionalidad interactiva
- **Font Awesome** - Iconos
- **Fetch API** - Comunicación con APIs

## 📋 Requisitos

- Servicios backend ejecutándose:
  - BFF de Campañas (puerto 8080)
  - SAGA Orchestrator (puerto 8090)
  - Servicio de Pagos (puerto 8000)

## 🚀 Instalación y Uso

### Opción 1: Servidor HTTP Simple
```bash
# Navegar al directorio frontend
cd frontend

# Usar servidor HTTP de Python
python -m http.server 3000

# O usar Node.js
npx serve .
```

### Opción 2: Live Server (VS Code)
1. Instalar extensión "Live Server"
2. Abrir `index.html` en VS Code
3. Click derecho → "Open with Live Server"

### Opción 3: Servidor Web Local
```bash
# Usar cualquier servidor web local
# Ejemplo con http-server
npm install -g http-server
http-server -p 3000
```

## 🌐 Acceso

Abrir en el navegador: `http://localhost:3000`

## 📱 Funcionalidades

### Dashboard
- Métricas de campañas activas
- Contador de SAGAs en proceso
- Pagos recientes
- Acciones rápidas

### Campañas
- Listar todas las campañas
- Ver detalles de campañas
- Crear nuevas campañas
- Cancelar campañas

### SAGAs
- Listar todas las SAGAs
- Crear SAGAs completas
- Ver detalles y estado
- Monitorear pasos y compensaciones

### Pagos
- Listar todos los pagos
- Ver detalles de pagos
- Filtrar por estado

### Herramientas
- Limpiar datos de prueba
- Crear SAGAs de prueba
- Crear múltiples SAGAs
- Limpiar todo el sistema

## 🔧 Configuración

### URLs de API
Las URLs de los servicios están configuradas en `script.js`:

```javascript
const API_CONFIG = {
    campaigns: 'http://localhost:8080',  // BFF de campañas
    sagas: 'http://localhost:8090',      // SAGA Orchestrator
    payments: 'http://localhost:8000'    // Servicio de pagos
};
```

### CORS
Asegúrate de que los servicios backend tengan CORS habilitado para el puerto del frontend.

## 🎨 Personalización

### Colores
Los colores principales están definidos en CSS:
- **Primario**: #667eea (azul)
- **Secundario**: #764ba2 (púrpura)
- **Éxito**: #28a745 (verde)
- **Error**: #dc3545 (rojo)
- **Advertencia**: #ffc107 (amarillo)

### Estilos
- Gradientes modernos
- Animaciones suaves
- Diseño responsivo
- Tarjetas con sombras
- Botones interactivos

## 🐛 Solución de Problemas

### Error de CORS
Si ves errores de CORS, verifica que los servicios backend tengan CORS habilitado.

### Servicios no disponibles
Verifica que todos los servicios estén ejecutándose:
- BFF de Campañas: `http://localhost:8080/health`
- SAGA Orchestrator: `http://localhost:8090/health`
- Servicio de Pagos: `http://localhost:8000/health`

### Datos no se cargan
- Verifica la consola del navegador para errores
- Asegúrate de que las URLs de API sean correctas
- Verifica que los servicios estén respondiendo

## 📝 Notas de Desarrollo

- El frontend es completamente estático
- No requiere compilación
- Funciona en cualquier servidor web
- Compatible con todos los navegadores modernos
- Diseño mobile-first

## 🔄 Actualizaciones

Para actualizar el frontend:
1. Modificar los archivos HTML, CSS o JS
2. Recargar la página en el navegador
3. Los cambios se aplican inmediatamente

## 📞 Soporte

Para problemas o preguntas:
1. Verificar la consola del navegador
2. Verificar que los servicios backend estén funcionando
3. Revisar la configuración de CORS
4. Verificar las URLs de API
