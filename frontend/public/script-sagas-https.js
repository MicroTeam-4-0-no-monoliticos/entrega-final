// Script de SAGAs para HTTPS - Frontend desplegado en Firebase
let currentData = {
    sagas: [],
    campaigns: [],
    payments: []
};

// Configuración de API para HTTPS
const API_CONFIG = API_CONFIG_HTTPS;

// Función para hacer requests con manejo de errores
async function apiRequest(endpoint, options = {}) {
    const url = `${API_CONFIG.baseURL}${endpoint}`;
    
    try {
        const response = await makeRequest(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error en ${endpoint}:`, error);
        throw error;
    }
}

// Cargar SAGAs
async function loadSagas() {
    try {
        showLoading();
        const sagas = await apiRequest(API_CONFIG.endpoints.sagas);
        currentData.sagas = sagas;
        displaySagas(sagas);
        hideLoading();
    } catch (error) {
        console.error('Error cargando SAGAs:', error);
        showError('Error cargando SAGAs: ' + error.message);
        hideLoading();
    }
}

// Mostrar SAGAs
function displaySagas(sagas) {
    const container = document.getElementById('sagas-list');
    
    if (!sagas || sagas.length === 0) {
        container.innerHTML = '<div class="empty-state">No hay SAGAs disponibles</div>';
        return;
    }
    
    const sagasHTML = sagas.map(saga => `
        <div class="saga-card" onclick="viewSaga('${saga.id}')">
            <div class="saga-header">
                <h3>${saga.tipo}</h3>
                <span class="status-badge status-${saga.estado.toLowerCase()}">${saga.estado}</span>
            </div>
            <div class="saga-info">
                <p><strong>ID:</strong> ${saga.id}</p>
                <p><strong>Fecha:</strong> ${new Date(saga.fecha_inicio).toLocaleString()}</p>
                ${saga.error_message ? `<p class="error"><strong>Error:</strong> ${saga.error_message}</p>` : ''}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = sagasHTML;
}

// Ver SAGA
async function viewSaga(sagaId) {
    try {
        showLoading();
        const saga = await apiRequest(`${API_CONFIG.endpoints.sagas}/${sagaId}/status`);
        showSagaDetails(saga);
        hideLoading();
    } catch (error) {
        console.error('Error cargando SAGA:', error);
        showError('Error cargando SAGA: ' + error.message);
        hideLoading();
    }
}

// Mostrar detalles de SAGA
function showSagaDetails(saga) {
    const modal = document.getElementById('modal-overlay');
    const modalBody = document.getElementById('modal-body');
    const modalTitle = document.getElementById('modal-title');
    
    modalTitle.textContent = `SAGA ${saga.id}`;
    
    const pasosHTML = saga.pasos.map(paso => {
        let estado = 'PENDIENTE';
        let claseEstado = 'paso-pendiente';
        
        if (paso.exitoso) {
            estado = 'EXITOSO';
            claseEstado = 'paso-exitoso';
        } else if (paso.error) {
            estado = 'FALLIDO';
            claseEstado = 'paso-fallido';
        }
        
        return `
            <div class="paso-item ${claseEstado}">
                <div class="paso-header">
                    <h4>${paso.tipo}</h4>
                    <span class="paso-estado">${estado}</span>
                </div>
                ${paso.error ? `<p class="paso-error">${paso.error}</p>` : ''}
                ${paso.resultado ? `<p class="paso-resultado">${JSON.stringify(paso.resultado, null, 2)}</p>` : ''}
            </div>
        `;
    }).join('');
    
    const compensacionesHTML = saga.compensaciones && saga.compensaciones.length > 0 
        ? saga.compensaciones.map(comp => `
            <div class="compensacion-item">
                <h4>${comp.tipo_compensacion}</h4>
                <p><strong>Exitoso:</strong> ${comp.exitoso ? 'Sí' : 'No'}</p>
                ${comp.error ? `<p class="error">${comp.error}</p>` : ''}
            </div>
        `).join('')
        : '<p>No hay compensaciones</p>';
    
    modalBody.innerHTML = `
        <div class="saga-details">
            <div class="saga-info">
                <p><strong>Estado:</strong> <span class="status-${saga.estado.toLowerCase()}">${saga.estado}</span></p>
                <p><strong>Tipo:</strong> ${saga.tipo}</p>
                <p><strong>Fecha Inicio:</strong> ${new Date(saga.fecha_inicio).toLocaleString()}</p>
                ${saga.fecha_fin ? `<p><strong>Fecha Fin:</strong> ${new Date(saga.fecha_fin).toLocaleString()}</p>` : ''}
                ${saga.error_message ? `<p class="error"><strong>Error:</strong> ${saga.error_message}</p>` : ''}
            </div>
            
            <div class="pasos-section">
                <h3>Pasos</h3>
                ${pasosHTML}
            </div>
            
            <div class="compensaciones-section">
                <h3>Compensaciones</h3>
                ${compensacionesHTML}
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
}

// Crear SAGA de prueba
async function createTestSaga() {
    const tiposValidos = ['PROMOCIONAL', 'FIDELIZACION', 'ADQUISICION', 'RETENCION'];
    const tipoAleatorio = tiposValidos[Math.floor(Math.random() * tiposValidos.length)];
    
    const sagaData = {
        tipo: tipoAleatorio,
        nombre: `Campaña Test ${tipoAleatorio}`,
        descripcion: `Campaña de prueba para ${tipoAleatorio}`,
        fecha_inicio: new Date().toISOString().split('T')[0],
        fecha_fin: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        presupuesto: Math.floor(Math.random() * 10000) + 1000,
        objetivo: `Objetivo ${tipoAleatorio}`,
        audiencia: `Audiencia ${tipoAleatorio}`,
        canal: `Canal ${tipoAleatorio}`,
        metrica: `Métrica ${tipoAleatorio}`,
        valor_objetivo: Math.floor(Math.random() * 1000) + 100
    };
    
    try {
        showLoading();
        const response = await apiRequest(`${API_CONFIG.endpoints.sagas}/crear-campana-completa`, {
            method: 'POST',
            body: JSON.stringify(sagaData)
        });
        
        console.log('SAGA creada:', response);
        showSuccess('SAGA creada exitosamente');
        loadSagas();
        hideLoading();
    } catch (error) {
        console.error('Error creando SAGA:', error);
        showError('Error creando SAGA: ' + error.message);
        hideLoading();
    }
}

// Mostrar formulario de creación
function showCreateSaga() {
    const modal = document.getElementById('modal-overlay');
    const modalBody = document.getElementById('modal-body');
    const modalTitle = document.getElementById('modal-title');
    
    modalTitle.textContent = 'Crear Nueva SAGA';
    
    modalBody.innerHTML = `
        <form id="saga-form" onsubmit="createSaga(event)">
            <div class="form-group">
                <label for="tipo">Tipo de Campaña:</label>
                <select id="tipo" name="tipo" required>
                    <option value="">Seleccionar tipo...</option>
                    <option value="PROMOCIONAL">PROMOCIONAL</option>
                    <option value="FIDELIZACION">FIDELIZACION</option>
                    <option value="ADQUISICION">ADQUISICION</option>
                    <option value="RETENCION">RETENCION</option>
                </select>
            </div>
            <div class="form-group">
                <label for="nombre">Nombre:</label>
                <input type="text" id="nombre" name="nombre" required>
            </div>
            <div class="form-group">
                <label for="descripcion">Descripción:</label>
                <textarea id="descripcion" name="descripcion" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label for="fecha_inicio">Fecha de Inicio:</label>
                <input type="date" id="fecha_inicio" name="fecha_inicio" required>
            </div>
            <div class="form-group">
                <label for="fecha_fin">Fecha de Fin:</label>
                <input type="date" id="fecha_fin" name="fecha_fin" required>
            </div>
            <div class="form-group">
                <label for="presupuesto">Presupuesto:</label>
                <input type="number" id="presupuesto" name="presupuesto" min="0" step="0.01" required>
            </div>
            <div class="form-group">
                <label for="objetivo">Objetivo:</label>
                <input type="text" id="objetivo" name="objetivo" required>
            </div>
            <div class="form-group">
                <label for="audiencia">Audiencia:</label>
                <input type="text" id="audiencia" name="audiencia" required>
            </div>
            <div class="form-group">
                <label for="canal">Canal:</label>
                <input type="text" id="canal" name="canal" required>
            </div>
            <div class="form-group">
                <label for="metrica">Métrica:</label>
                <input type="text" id="metrica" name="metrica" required>
            </div>
            <div class="form-group">
                <label for="valor_objetivo">Valor Objetivo:</label>
                <input type="number" id="valor_objetivo" name="valor_objetivo" min="0" step="0.01" required>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Crear SAGA</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
            </div>
        </form>
    `;
    
    modal.style.display = 'flex';
}

// Crear SAGA desde formulario
async function createSaga(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const sagaData = Object.fromEntries(formData.entries());
    
    // Validar tipo de campaña
    if (!validarTipoCampana(sagaData.tipo)) {
        showError('Tipo de campaña no válido');
        return;
    }
    
    try {
        showLoading();
        const response = await apiRequest(`${API_CONFIG.endpoints.sagas}/crear-campana-completa`, {
            method: 'POST',
            body: JSON.stringify(sagaData)
        });
        
        console.log('SAGA creada:', response);
        showSuccess('SAGA creada exitosamente');
        closeModal();
        loadSagas();
        hideLoading();
    } catch (error) {
        console.error('Error creando SAGA:', error);
        showError('Error creando SAGA: ' + error.message);
        hideLoading();
    }
}

// Funciones de UI
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    alert('Éxito: ' + message);
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 AeroPartners SAGAs iniciado (HTTPS)');
    console.log('📡 Conectando a:', API_CONFIG.baseURL);
    console.log('✅ Tipos de campaña válidos:', TIPOS_CAMPANA_VALIDOS);
    
    loadSagas();
});
