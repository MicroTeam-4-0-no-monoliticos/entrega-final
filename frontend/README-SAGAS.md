# 🚀 AeroPartners SAGA Frontend

Frontend simplificado para gestionar SAGAs del sistema AeroPartners.

## 🎯 Características

- **Gestión de SAGAs**: Crear, visualizar y monitorear SAGAs
- **Interfaz Simplificada**: Solo funcionalidades de SAGAs
- **Creación de Pruebas**: Botones para crear SAGAs de prueba
- **Monitoreo en Tiempo Real**: Estado de servicios y SAGAs
- **Limpieza de Datos**: Herramientas para limpiar datos de prueba

## 🚀 Cómo Usar

### 1. Iniciar el Frontend

```bash
# Navegar al directorio frontend
cd frontend

# Iniciar servidor web (opción 1)
python3 -m http.server 3000

# O usar Live Server en VS Code (opción 2)
# Instalar extensión "Live Server" y hacer clic derecho en index.html
```

### 2. Acceder al Frontend

- **URL**: `http://localhost:3000` (Python) o `http://127.0.0.1:5500` (Live Server)
- **Puerto**: 3000 (Python) o 5500 (Live Server)

### 3. Funcionalidades Disponibles

#### 📋 Listar SAGAs
- **Botón**: "Actualizar"
- **Función**: Carga todas las SAGAs del sistema
- **Endpoint**: `GET /saga/`

#### ➕ Crear SAGA
- **Botón**: "Crear SAGA"
- **Función**: Formulario para crear una SAGA completa
- **Endpoint**: `POST /saga/crear-campana-completa`

#### 🧪 SAGA de Prueba
- **Botón**: "SAGA Test"
- **Función**: Crea una SAGA de prueba con datos predefinidos
- **Datos**: Campaña promocional de $1000 USD


## 🔧 Configuración

### Servicios Requeridos

El frontend necesita que estén funcionando:

1. **SAGA Orchestrator** (Puerto 8090)
   - URL: `http://localhost:8090`
   - Health: `GET /health`

### Variables de Configuración

```javascript
const API_CONFIG = {
    sagas: 'http://localhost:8090'      // SAGA Orchestrator
};
```

## 📱 Interfaz de Usuario

### Header
- **Título**: AeroPartners SAGA Orchestrator
- **Estado**: Indicador de conexión con servicios
- **Navegación**: Solo botón de SAGAs

### Sección Principal
- **Lista de SAGAs**: Tarjetas con información de cada SAGA
- **Botones de Acción**: Crear, actualizar, SAGA test
- **Estado Visual**: Colores según el estado de la SAGA

### Modal de Creación
- **Formulario**: Datos de campaña, pago y reporte
- **Validación**: Campos requeridos
- **Envío**: Creación asíncrona de SAGA

## 🎨 Estados de SAGA

| Estado | Color | Icono | Descripción |
|--------|-------|-------|-------------|
| `INICIADA` | Amarillo | ⏰ | SAGA en proceso |
| `COMPLETADA` | Verde | ✅ | SAGA exitosa |
| `FALLIDA` | Rojo | ❌ | SAGA fallida |

## 🔍 Monitoreo

### Indicadores de Estado
- **Punto Verde**: Servicio conectado
- **Punto Gris**: Servicio desconectado

### Información de SAGA
- **ID**: Identificador único
- **Estado**: Estado actual
- **Tipo**: Tipo de SAGA
- **Fechas**: Inicio y fin
- **Pasos**: Lista de pasos ejecutados
- **Compensaciones**: Compensaciones realizadas
- **Botón**: "Ver Detalles" para información completa

## 🚨 Solución de Problemas

### Error de CORS
```
Access to fetch at 'http://localhost:8090/saga/' from origin 'http://127.0.0.1:5500' has been blocked by CORS policy
```
**Solución**: El SAGA Orchestrator ya tiene CORS configurado. Verificar que esté funcionando.

### Servicio No Disponible
```
Error loading SAGAs: TypeError: Failed to fetch
```
**Solución**: Verificar que el SAGA Orchestrator esté funcionando en el puerto 8090.

### SAGAs No Se Cargan
**Solución**: 
1. Verificar conexión con `http://localhost:8090/health`
2. Verificar que haya SAGAs en el sistema
3. Revisar la consola del navegador para errores

## 📁 Estructura de Archivos

```
frontend/
├── index.html          # Página principal
├── styles.css          # Estilos CSS
├── script-sagas.js     # JavaScript para SAGAs
├── README-SAGAS.md     # Este archivo
└── README.md           # README original
```

## 🔄 Flujo de Trabajo

1. **Iniciar Frontend**: Servidor web en puerto 3000 o 5500
2. **Verificar Servicios**: Estado de conexión en el header
3. **Cargar SAGAs**: Botón "Actualizar" para ver SAGAs existentes
4. **Crear SAGA**: Botón "Crear SAGA" para nueva SAGA
5. **SAGA Test**: Botón "SAGA Test" para crear SAGA de prueba
6. **Monitorear**: Ver estado y progreso de SAGAs
7. **Ver Detalles**: Botón "Ver Detalles" en cada SAGA

## 🎯 Próximos Pasos

- [ ] Agregar filtros por estado de SAGA
- [ ] Implementar actualización automática
- [ ] Agregar gráficos de estadísticas
- [ ] Implementar notificaciones push
- [ ] Agregar exportación de datos

---

**Desarrollado para AeroPartners SAGA Orchestrator** 🚀
