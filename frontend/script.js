// API Configuration
const API_CONFIG = {
    sagas: 'http://localhost:8090'      // SAGA Orchestrator
};

// Global state
let currentData = {
    sagas: []
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('AeroPartners SAGA Frontend initialized');
    checkServicesStatus();
    loadSagas();
});

// Service Status Check
async function checkServicesStatus() {
    const services = [
        { name: 'sagas', url: `${API_CONFIG.sagas}/health` }
    ];

    for (const service of services) {
        try {
            const response = await fetch(service.url);
            const statusDot = document.getElementById(`${service.name}-status`);
            if (response.ok) {
                statusDot.classList.add('online');
            } else {
                statusDot.classList.remove('online');
            }
        } catch (error) {
            console.error(`Error checking ${service.name} service:`, error);
            document.getElementById(`${service.name}-status`).classList.remove('online');
        }
    }
}

// Navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionName).classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Load data for the section
    switch(sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'campaigns':
            loadCampaigns();
            break;
        case 'sagas':
            loadSagas();
            break;
        case 'payments':
            loadPayments();
            break;
    }
}

// Dashboard Functions
async function loadDashboard() {
    try {
        // Load all data in parallel
        const [campaignsData, sagasData, paymentsData] = await Promise.all([
            fetchData(`${API_CONFIG.campaigns}/api/campaigns/`),
            fetchData(`${API_CONFIG.sagas}/saga/`),
            fetchData(`${API_CONFIG.payments}/pagos/`)
        ]);

        // Update metrics
        document.getElementById('active-campaigns').textContent = 
            campaignsData.campaigns ? campaignsData.campaigns.length : 0;
        
        document.getElementById('active-sagas').textContent = 
            sagasData.sagas ? sagasData.sagas.length : 0;
        
        document.getElementById('recent-payments').textContent = 
            paymentsData.pagos ? paymentsData.pagos.length : 0;

        // Store data
        currentData.campaigns = campaignsData.campaigns || [];
        currentData.sagas = sagasData.sagas || [];
        currentData.payments = paymentsData.pagos || [];

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Error cargando el dashboard', 'error');
    }
}

// Campaign Functions
async function loadCampaigns() {
    showLoading();
    try {
        const data = await fetchData(`${API_CONFIG.campaigns}/api/campaigns/`);
        currentData.campaigns = data.campaigns || [];
        displayCampaigns(currentData.campaigns);
    } catch (error) {
        console.error('Error loading campaigns:', error);
        showNotification('Error cargando campañas', 'error');
        document.getElementById('campaigns-list').innerHTML = 
            '<div class="loading">Error cargando campañas</div>';
    } finally {
        hideLoading();
    }
}

function displayCampaigns(campaigns) {
    const container = document.getElementById('campaigns-list');
    
    if (!campaigns || campaigns.length === 0) {
        container.innerHTML = '<div class="loading">No hay campañas disponibles</div>';
        return;
    }

    const html = campaigns.map(campaign => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">${campaign.nombre}</div>
                <div class="card-status status-${campaign.estado.toLowerCase()}">${campaign.estado}</div>
            </div>
            <div class="card-body">
                <div class="card-meta">
                    <div class="meta-item">
                        <div class="meta-label">Tipo</div>
                        <div class="meta-value">${campaign.tipo}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Presupuesto</div>
                        <div class="meta-value">$${campaign.presupuesto.monto} ${campaign.presupuesto.moneda}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Afiliado</div>
                        <div class="meta-value">${campaign.id_afiliado}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Fecha Creación</div>
                        <div class="meta-value">${formatDate(campaign.fecha_creacion)}</div>
                    </div>
                </div>
                <p class="mb-3">${campaign.descripcion}</p>
            </div>
            <div class="card-actions">
                <button onclick="viewCampaign('${campaign.id}')" class="btn btn-primary">
                    <i class="fas fa-eye"></i> Ver Detalles
                </button>
                <button onclick="cancelCampaign('${campaign.id}')" class="btn btn-warning">
                    <i class="fas fa-ban"></i> Cancelar
                </button>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// SAGA Functions
async function loadSagas() {
    showLoading();
    try {
        const data = await fetchData(`${API_CONFIG.sagas}/saga/`);
        currentData.sagas = data.sagas || [];
        displaySagas(currentData.sagas);
    } catch (error) {
        console.error('Error loading SAGAs:', error);
        showNotification('Error cargando SAGAs', 'error');
        document.getElementById('sagas-list').innerHTML = 
            '<div class="loading">Error cargando SAGAs</div>';
    } finally {
        hideLoading();
    }
}

function displaySagas(sagas) {
    const container = document.getElementById('sagas-list');
    
    if (!sagas || sagas.length === 0) {
        container.innerHTML = '<div class="loading">No hay SAGAs disponibles</div>';
        return;
    }

    const html = sagas.map(saga => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">SAGA ${saga.saga_id.substring(0, 8)}...</div>
                <div class="card-status status-${saga.estado.toLowerCase()}">${saga.estado}</div>
            </div>
            <div class="card-body">
                <div class="card-meta">
                    <div class="meta-item">
                        <div class="meta-label">Tipo</div>
                        <div class="meta-value">${saga.tipo}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Pasos</div>
                        <div class="meta-value">${saga.pasos ? saga.pasos.length : 0}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Compensaciones</div>
                        <div class="meta-value">${saga.compensaciones ? saga.compensaciones.length : 0}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Fecha Inicio</div>
                        <div class="meta-value">${formatDate(saga.fecha_inicio)}</div>
                    </div>
                </div>
                ${saga.error_message ? `<p class="text-danger"><strong>Error:</strong> ${saga.error_message}</p>` : ''}
            </div>
            <div class="card-actions">
                <button onclick="viewSaga('${saga.saga_id}')" class="btn btn-primary">
                    <i class="fas fa-eye"></i> Ver Detalles
                </button>
                <button onclick="viewSagaStatus('${saga.saga_id}')" class="btn btn-secondary">
                    <i class="fas fa-info-circle"></i> Estado
                </button>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// Payment Functions
async function loadPayments() {
    showLoading();
    try {
        const data = await fetchData(`${API_CONFIG.payments}/pagos/`);
        currentData.payments = data.pagos || [];
        displayPayments(currentData.payments);
    } catch (error) {
        console.error('Error loading payments:', error);
        showNotification('Error cargando pagos', 'error');
        document.getElementById('payments-list').innerHTML = 
            '<div class="loading">Error cargando pagos</div>';
    } finally {
        hideLoading();
    }
}

function displayPayments(payments) {
    const container = document.getElementById('payments-list');
    
    if (!payments || payments.length === 0) {
        container.innerHTML = '<div class="loading">No hay pagos disponibles</div>';
        return;
    }

    const html = payments.map(payment => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">Pago ${payment.id.substring(0, 8)}...</div>
                <div class="card-status status-${payment.estado.toLowerCase()}">${payment.estado}</div>
            </div>
            <div class="card-body">
                <div class="card-meta">
                    <div class="meta-item">
                        <div class="meta-label">Monto</div>
                        <div class="meta-value">$${payment.monto} ${payment.moneda}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Afiliado</div>
                        <div class="meta-value">${payment.id_afiliado}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Referencia</div>
                        <div class="meta-value">${payment.referencia_pago}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Fecha Creación</div>
                        <div class="meta-value">${formatDate(payment.fecha_creacion)}</div>
                    </div>
                </div>
                ${payment.mensaje_error ? `<p class="text-danger"><strong>Error:</strong> ${payment.mensaje_error}</p>` : ''}
            </div>
            <div class="card-actions">
                <button onclick="viewPayment('${payment.id}')" class="btn btn-primary">
                    <i class="fas fa-eye"></i> Ver Detalles
                </button>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// Modal Functions
function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

// Create SAGA Modal
function showCreateSaga() {
    const content = `
        <form id="create-saga-form">
            <div class="form-row">
                <div class="form-group">
                    <label for="campaign-name">Nombre de Campaña</label>
                    <input type="text" id="campaign-name" required>
                </div>
                <div class="form-group">
                    <label for="affiliate-id">ID Afiliado</label>
                    <input type="text" id="affiliate-id" value="afiliado_test_${Date.now()}" required>
                </div>
            </div>
            <div class="form-group">
                <label for="campaign-desc">Descripción</label>
                <textarea id="campaign-desc" rows="3" required></textarea>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label for="budget">Presupuesto (USD)</label>
                    <input type="number" id="budget" min="100" max="10000" value="1000" required>
                </div>
                <div class="form-group">
                    <label for="payment-amount">Monto Pago (USD)</label>
                    <input type="number" id="payment-amount" min="100" max="10000" value="1000" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label for="start-date">Fecha Inicio</label>
                    <input type="date" id="start-date" required>
                </div>
                <div class="form-group">
                    <label for="end-date">Fecha Fin</label>
                    <input type="date" id="end-date" required>
                </div>
            </div>
            <div class="form-actions">
                <button type="button" onclick="closeModal()" class="btn btn-secondary">Cancelar</button>
                <button type="submit" class="btn btn-primary">Crear SAGA</button>
            </div>
        </form>
    `;
    
    showModal('Crear SAGA Completa', content);
    
    // Set default dates
    const today = new Date();
    const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, today.getDate());
    document.getElementById('start-date').value = today.toISOString().split('T')[0];
    document.getElementById('end-date').value = nextMonth.toISOString().split('T')[0];
    
    // Handle form submission
    document.getElementById('create-saga-form').addEventListener('submit', createSaga);
}

// Create SAGA Function
async function createSaga(event) {
    event.preventDefault();
    
    const sagaData = {
        campana: {
            nombre: document.getElementById('campaign-name').value,
            descripcion: document.getElementById('campaign-desc').value,
            tipo: "PROMOCIONAL",
            presupuesto: {
                monto: parseFloat(document.getElementById('budget').value),
                moneda: "USD"
            },
            fecha_inicio: document.getElementById('start-date').value + "T00:00:00",
            fecha_fin: document.getElementById('end-date').value + "T23:59:59",
            id_afiliado: document.getElementById('affiliate-id').value
        },
        pago: {
            monto: parseFloat(document.getElementById('payment-amount').value),
            moneda: "USD",
            id_afiliado: document.getElementById('affiliate-id').value,
            referencia_pago: `test_${Date.now()}`
        },
        reporte: {
            fecha_inicio: document.getElementById('start-date').value,
            fecha_fin: document.getElementById('end-date').value,
            tipo_reporte: "metricas_generales"
        }
    };
    
    showLoading();
    try {
        const response = await fetch(`${API_CONFIG.sagas}/saga/crear-campana-completa`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sagaData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(`SAGA creada exitosamente: ${result.saga_id}`, 'success');
            closeModal();
            loadSagas();
            loadDashboard();
        } else {
            showNotification(`Error creando SAGA: ${result.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error creating SAGA:', error);
        showNotification('Error de conexión al crear SAGA', 'error');
    } finally {
        hideLoading();
    }
}

// Test Functions
async function createTestSaga() {
    const testData = {
        campana: {
            nombre: `Campaña Test ${Date.now()}`,
            descripcion: "Campaña de prueba generada automáticamente",
            tipo: "PROMOCIONAL",
            presupuesto: {
                monto: Math.floor(Math.random() * 2000) + 500,
                moneda: "USD"
            },
            fecha_inicio: new Date().toISOString().split('T')[0] + "T00:00:00",
            fecha_fin: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] + "T23:59:59",
            id_afiliado: `afiliado_test_${Date.now()}`
        },
        pago: {
            monto: Math.floor(Math.random() * 2000) + 500,
            moneda: "USD",
            id_afiliado: `afiliado_test_${Date.now()}`,
            referencia_pago: `test_${Date.now()}`
        },
        reporte: {
            fecha_inicio: new Date().toISOString().split('T')[0],
            fecha_fin: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            tipo_reporte: "metricas_generales"
        }
    };
    
    showLoading();
    try {
        const response = await fetch(`${API_CONFIG.sagas}/saga/crear-campana-completa`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(`SAGA de prueba creada: ${result.saga_id}`, 'success');
            loadSagas();
            loadDashboard();
        } else {
            showNotification(`Error creando SAGA de prueba: ${result.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error creating test SAGA:', error);
        showNotification('Error de conexión', 'error');
    } finally {
        hideLoading();
    }
}

async function createMultipleSagas() {
    showLoading();
    let successCount = 0;
    let errorCount = 0;
    
    for (let i = 0; i < 5; i++) {
        try {
            await createTestSaga();
            successCount++;
            await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second between requests
        } catch (error) {
            errorCount++;
        }
    }
    
    showNotification(`Creadas ${successCount} SAGAs, ${errorCount} errores`, successCount > 0 ? 'success' : 'error');
    hideLoading();
}

// Cleanup Functions
async function cleanupCampaigns() {
    if (!confirm('¿Estás seguro de que quieres eliminar todas las campañas?')) return;
    
    showLoading();
    try {
        const response = await fetch(`${API_CONFIG.campaigns}/api/campaigns/cleanup/`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        showNotification(result.mensaje || 'Campañas eliminadas', 'success');
        loadCampaigns();
        loadDashboard();
    } catch (error) {
        console.error('Error cleaning campaigns:', error);
        showNotification('Error eliminando campañas', 'error');
    } finally {
        hideLoading();
    }
}

async function cleanupSagas() {
    if (!confirm('¿Estás seguro de que quieres eliminar todas las SAGAs?')) return;
    
    showLoading();
    try {
        const response = await fetch(`${API_CONFIG.sagas}/saga/cleanup`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        showNotification(result.mensaje || 'SAGAs eliminadas', 'success');
        loadSagas();
        loadDashboard();
    } catch (error) {
        console.error('Error cleaning SAGAs:', error);
        showNotification('Error eliminando SAGAs', 'error');
    } finally {
        hideLoading();
    }
}

async function cleanupPayments() {
    if (!confirm('¿Estás seguro de que quieres eliminar todos los pagos?')) return;
    
    showLoading();
    try {
        const response = await fetch(`${API_CONFIG.payments}/pagos/cleanup`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        showNotification(result.mensaje || 'Pagos eliminados', 'success');
        loadPayments();
        loadDashboard();
    } catch (error) {
        console.error('Error cleaning payments:', error);
        showNotification('Error eliminando pagos', 'error');
    } finally {
        hideLoading();
    }
}

async function cleanupAll() {
    if (!confirm('¿Estás seguro de que quieres eliminar TODOS los datos?')) return;
    
    showLoading();
    try {
        await Promise.all([
            cleanupCampaigns(),
            cleanupSagas(),
            cleanupPayments()
        ]);
        showNotification('Todos los datos han sido eliminados', 'success');
    } catch (error) {
        console.error('Error cleaning all data:', error);
        showNotification('Error eliminando datos', 'error');
    } finally {
        hideLoading();
    }
}

// View Functions
function viewCampaign(campaignId) {
    const campaign = currentData.campaigns.find(c => c.id === campaignId);
    if (!campaign) return;
    
    const content = `
        <div class="card">
            <h4>${campaign.nombre}</h4>
            <p><strong>Descripción:</strong> ${campaign.descripcion}</p>
            <p><strong>Estado:</strong> <span class="status-${campaign.estado.toLowerCase()}">${campaign.estado}</span></p>
            <p><strong>Tipo:</strong> ${campaign.tipo}</p>
            <p><strong>Presupuesto:</strong> $${campaign.presupuesto.monto} ${campaign.presupuesto.moneda}</p>
            <p><strong>Afiliado:</strong> ${campaign.id_afiliado}</p>
            <p><strong>Fecha Creación:</strong> ${formatDate(campaign.fecha_creacion)}</p>
        </div>
    `;
    
    showModal(`Campaña: ${campaign.nombre}`, content);
}

function viewSaga(sagaId) {
    const saga = currentData.sagas.find(s => s.saga_id === sagaId);
    if (!saga) return;
    
    const stepsHtml = saga.pasos ? saga.pasos.map(step => `
        <div class="card mb-2">
            <div class="card-header">
                <strong>${step.tipo}</strong>
                <span class="card-status status-${step.exitoso ? 'success' : 'failed'}">
                    ${step.exitoso ? 'Exitoso' : 'Fallido'}
                </span>
            </div>
            ${step.resultado ? `<div class="card-body"><pre>${JSON.stringify(step.resultado, null, 2)}</pre></div>` : ''}
        </div>
    `).join('') : '<p>No hay pasos disponibles</p>';
    
    const content = `
        <div class="card">
            <h4>SAGA ${saga.saga_id}</h4>
            <p><strong>Estado:</strong> <span class="status-${saga.estado.toLowerCase()}">${saga.estado}</span></p>
            <p><strong>Tipo:</strong> ${saga.tipo}</p>
            <p><strong>Fecha Inicio:</strong> ${formatDate(saga.fecha_inicio)}</p>
            ${saga.fecha_fin ? `<p><strong>Fecha Fin:</strong> ${formatDate(saga.fecha_fin)}</p>` : ''}
            ${saga.error_message ? `<p class="text-danger"><strong>Error:</strong> ${saga.error_message}</p>` : ''}
            <h5>Pasos:</h5>
            ${stepsHtml}
        </div>
    `;
    
    showModal(`SAGA: ${saga.saga_id.substring(0, 8)}...`, content);
}

function viewSagaStatus(sagaId) {
    window.open(`${API_CONFIG.sagas}/saga/${sagaId}/status`, '_blank');
}

function viewPayment(paymentId) {
    const payment = currentData.payments.find(p => p.id === paymentId);
    if (!payment) return;
    
    const content = `
        <div class="card">
            <h4>Pago ${payment.id}</h4>
            <p><strong>Estado:</strong> <span class="status-${payment.estado.toLowerCase()}">${payment.estado}</span></p>
            <p><strong>Monto:</strong> $${payment.monto} ${payment.moneda}</p>
            <p><strong>Afiliado:</strong> ${payment.id_afiliado}</p>
            <p><strong>Referencia:</strong> ${payment.referencia_pago}</p>
            <p><strong>Fecha Creación:</strong> ${formatDate(payment.fecha_creacion)}</p>
            ${payment.fecha_procesamiento ? `<p><strong>Fecha Procesamiento:</strong> ${formatDate(payment.fecha_procesamiento)}</p>` : ''}
            ${payment.mensaje_error ? `<p class="text-danger"><strong>Error:</strong> ${payment.mensaje_error}</p>` : ''}
        </div>
    `;
    
    showModal(`Pago: ${payment.id.substring(0, 8)}...`, content);
}

// Utility Functions
async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 3000;
        animation: slideIn 0.3s ease;
        max-width: 400px;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .form-actions {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
        margin-top: 20px;
    }
`;
document.head.appendChild(style);
