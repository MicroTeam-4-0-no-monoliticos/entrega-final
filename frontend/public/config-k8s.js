// Configuración para despliegue en Kubernetes (GKE)
// Este archivo contiene las URLs de los servicios desplegados en la nube

// Tipos de campaña válidos
const TIPOS_CAMPANA_VALIDOS = [
    'PROMOCIONAL',
    'FIDELIZACION', 
    'ADQUISICION',
    'RETENCION'
];

// Función para validar tipo de campaña
function validarTipoCampana(tipo) {
    return TIPOS_CAMPANA_VALIDOS.includes(tipo);
}

const API_CONFIG_K8S = {
    // Servicios principales
    sagas: 'http://34.10.122.141:8000',      // SAGA Orchestrator
    campaigns: 'http://34.10.122.141:8080',  // Campaigns Proxy
    payments: 'http://34.10.122.141:8000',   // Servicio de Pagos
    reporting: 'http://34.10.122.141:8000',  // Servicio de Reporting
    
    // Servicios de datos mock
    servicio_datos_v1: 'http://34.10.122.141:9001',  // Servicio Datos v1
    servicio_datos_v2: 'http://34.10.122.141:9002',  // Servicio Datos v2
    
    // Event Collector
    event_collector: 'http://34.10.122.141:8000',    // Event Collector BFF
};

// Función para obtener la configuración activa
function getApiConfig() {
    // Verificar si estamos en desarrollo local o en la nube
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        // Desarrollo local
        return {
            sagas: 'http://localhost:8090',
            campaigns: 'http://localhost:8080',
            payments: 'http://localhost:8000',
            reporting: 'http://localhost:8000',
            servicio_datos_v1: 'http://localhost:8001',
            servicio_datos_v2: 'http://localhost:8002',
            event_collector: 'http://localhost:8000'
        };
    } else {
        // Producción en la nube
        return API_CONFIG_K8S;
    }
}

// Exportar configuración
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG_K8S, getApiConfig };
}
