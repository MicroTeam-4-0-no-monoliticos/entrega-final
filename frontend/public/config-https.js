// Configuración para HTTPS - Frontend desplegado en Firebase
const API_CONFIG_HTTPS = {
    baseURL: 'https://cors-anywhere.herokuapp.com/http://34.10.122.141:8000',
    endpoints: {
        sagas: '/saga',
        campaigns: '/campaigns',
        payments: '/pagos',
        reporting: '/reporting'
    }
};

// Tipos de campaña válidos
const TIPOS_CAMPANA_VALIDOS = ['PROMOCIONAL', 'FIDELIZACION', 'ADQUISICION', 'RETENCION'];

// Función para validar tipo de campaña
function validarTipoCampana(tipo) {
    return TIPOS_CAMPANA_VALIDOS.includes(tipo);
}

// Función para hacer requests con headers CORS
async function makeRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        return response;
    } catch (error) {
        console.error('Error en request:', error);
        throw error;
    }
}
