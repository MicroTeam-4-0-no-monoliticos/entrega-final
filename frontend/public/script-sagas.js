// API Configuration - Cloud Run Proxy (HTTPS)
const API_CONFIG = {
    sagas: 'https://saga-proxy-557335216999.us-central1.run.app'      // SAGA Proxy (Cloud Run)
};

// Global state
let currentData = {
    sagas: []
};

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

    const sagasHtml = sagas.map(saga => {
        const statusClass = getStatusClass(saga.estado);
        const statusIcon = getStatusIcon(saga.estado);
        
        return `
            <div class="saga-card">
                <div class="saga-header">
                    <h3>SAGA ${saga.saga_id.substring(0, 8)}...</h3>
                    <span class="status-badge ${statusClass}">
                        <i class="fas ${statusIcon}"></i> ${saga.estado}
                    </span>
                </div>
                <div class="saga-details">
                    <p><strong>Tipo:</strong> ${saga.tipo}</p>
                    <p><strong>Inicio:</strong> ${formatDate(saga.fecha_inicio)}</p>
                    ${saga.fecha_fin ? `<p><strong>Fin:</strong> ${formatDate(saga.fecha_fin)}</p>` : ''}
                    ${saga.error_message ? `<p><strong>Error:</strong> ${saga.error_message}</p>` : ''}
                </div>
                <div class="saga-actions">
                    <button onclick="viewSaga('${saga.saga_id}')" class="btn btn-primary">
                        <i class="fas fa-eye"></i> Ver Detalles
                    </button>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = sagasHtml;
}

function getStatusClass(status) {
    switch (status) {
        case 'COMPLETADA': return 'status-success';
        case 'FALLIDA': return 'status-error';
        case 'INICIADA': return 'status-warning';
        default: return 'status-info';
    }
}

function getStatusIcon(status) {
    switch (status) {
        case 'COMPLETADA': return 'fa-check-circle';
        case 'FALLIDA': return 'fa-times-circle';
        case 'INICIADA': return 'fa-clock';
        default: return 'fa-info-circle';
    }
}

// Modal Functions
function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('modal-overlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

// SAGA Creation
function showCreateSaga() {
    const content = `
        <form id="create-saga-form" onsubmit="createSaga(event)">
            <div class="form-group">
                <label for="campana-nombre">Nombre de la Campaña:</label>
                <input type="text" id="campana-nombre" name="campana-nombre" required>
            </div>
            <div class="form-group">
                <label for="campana-descripcion">Descripción:</label>
                <textarea id="campana-descripcion" name="campana-descripcion" required></textarea>
            </div>
            <div class="form-group">
                <label for="campana-tipo">Tipo:</label>
                <select id="campana-tipo" name="campana-tipo" required>
                    <option value="PROMOCIONAL">Promocional</option>
                    <option value="FIDELIZACION">Fidelización</option>
                    <option value="ADQUISICION">Adquisición</option>
                    <option value="RETENCION">Retención</option>
                </select>
            </div>
            <div class="form-group">
                <label for="campana-presupuesto">Presupuesto (USD):</label>
                <input type="number" id="campana-presupuesto" name="campana-presupuesto" min="0" step="0.01" required>
            </div>
            <div class="form-group">
                <label for="pago-monto">Monto del Pago (USD):</label>
                <input type="number" id="pago-monto" name="pago-monto" min="0" step="0.01" required>
            </div>
            <div class="form-group">
                <label for="pago-referencia">Referencia de Pago:</label>
                <input type="text" id="pago-referencia" name="pago-referencia" required>
            </div>
            <div class="form-group">
                <label for="reporte-tipo">Tipo de Reporte:</label>
                <select id="reporte-tipo" name="reporte-tipo" required>
                    <option value="metricas_generales">Métricas Generales</option>
                    <option value="metricas_detalladas">Métricas Detalladas</option>
                    <option value="analisis_rendimiento">Análisis de Rendimiento</option>
                </select>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Crear SAGA
                </button>
                <button type="button" onclick="closeModal()" class="btn btn-secondary">
                    <i class="fas fa-times"></i> Cancelar
                </button>
            </div>
        </form>
    `;
    
    showModal('Crear Nueva SAGA', content);
}

async function createSaga(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const campanaPresupuesto = parseFloat(formData.get('campana-presupuesto'));
    const pagoMonto = parseFloat(formData.get('pago-monto'));
    const campanaTipo = formData.get('campana-tipo');
    
    // Validar tipo de campaña
    if (!validarTipoCampana(campanaTipo)) {
        alert(`Tipo de campaña inválido: ${campanaTipo}. Tipos válidos: ${TIPOS_CAMPANA_VALIDOS.join(', ')}`);
        return;
    }
    
    const sagaData = {
        campana: {
            nombre: formData.get('campana-nombre'),
            descripcion: formData.get('campana-descripcion'),
            tipo: campanaTipo,
            presupuesto: {
                monto: campanaPresupuesto,
                moneda: "USD"
            },
            fecha_inicio: "2025-01-01T00:00:00",
            fecha_fin: "2025-12-31T23:59:59",
            id_afiliado: `afiliado_${Date.now()}`
        },
        pago: {
            monto: pagoMonto,
            moneda: "USD",
            id_afiliado: `afiliado_${Date.now()}`,
            referencia_pago: formData.get('pago-referencia')
        },
        reporte: {
            fecha_inicio: "2025-01-01",
            fecha_fin: "2025-12-31",
            tipo_reporte: formData.get('reporte-tipo')
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
            showNotification('SAGA creada exitosamente', 'success');
            closeModal();
            loadSagas(); // Reload the list
        } else {
            showNotification(`Error creando SAGA: ${result.detail || 'Error desconocido'}`, 'error');
        }
    } catch (error) {
        console.error('Error creating SAGA:', error);
        showNotification('Error creando SAGA', 'error');
    } finally {
        hideLoading();
    }
}

// Test SAGA Creation
async function createTestSaga() {
    // Seleccionar un tipo de campaña válido aleatorio
    const tipoAleatorio = TIPOS_CAMPANA_VALIDOS[Math.floor(Math.random() * TIPOS_CAMPANA_VALIDOS.length)];
    
    const testData = {
        campana: {
            nombre: `Campaña Test Frontend - ${tipoAleatorio}`,
            descripcion: `Campaña de prueba desde el frontend (${tipoAleatorio})`,
            tipo: tipoAleatorio,
            presupuesto: {
                monto: 1000.0,
                moneda: "USD"
            },
            fecha_inicio: "2025-01-01T00:00:00",
            fecha_fin: "2025-12-31T23:59:59",
            id_afiliado: `afiliado_test_${Date.now()}`
        },
        pago: {
            monto: 1000.0,
            moneda: "USD",
            id_afiliado: `afiliado_test_${Date.now()}`,
            referencia_pago: `test_${Date.now()}`
        },
        reporte: {
            fecha_inicio: "2025-01-01",
            fecha_fin: "2025-12-31",
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
            showNotification('SAGA de prueba creada exitosamente', 'success');
            loadSagas();
        } else {
            showNotification(`Error creando SAGA de prueba: ${result.detail || 'Error desconocido'}`, 'error');
        }
    } catch (error) {
        console.error('Error creating test SAGA:', error);
        showNotification('Error creando SAGA de prueba', 'error');
    } finally {
        hideLoading();
    }
}


// View Functions
async function viewSaga(sagaId) {
    const saga = currentData.sagas.find(s => s.saga_id === sagaId);
    if (!saga) return;
    
    // Obtener datos actualizados del endpoint de status
    try {
        const statusData = await fetchData(`${API_CONFIG.sagas}/saga/${sagaId}/status`);
        console.log('SAGA status data:', statusData);
        
        // Usar los datos actualizados del status
        const sagaActualizada = statusData;
        
        // Debug: mostrar datos de la SAGA actualizada
        console.log('SAGA actualizada:', sagaActualizada);
        console.log('Pasos actualizados:', sagaActualizada.pasos);
        sagaActualizada.pasos.forEach((paso, index) => {
            console.log(`Paso ${index}:`, {
                tipo: paso.tipo,
                exitoso: paso.exitoso,
                resultado: paso.resultado,
                error: paso.error
            });
        });
        
        mostrarDetallesSaga(sagaActualizada);
    } catch (error) {
        console.error('Error obteniendo status de SAGA:', error);
        // Fallback a los datos locales si falla el endpoint
        mostrarDetallesSaga(saga);
    }
}

function mostrarDetallesSaga(saga) {
    
    const content = `
        <div class="saga-details">
            <h3>SAGA ${saga.saga_id}</h3>
            <p><strong>Estado:</strong> ${saga.estado}</p>
            <p><strong>Tipo:</strong> ${saga.tipo}</p>
            <p><strong>Inicio:</strong> ${formatDate(saga.fecha_inicio)}</p>
            ${saga.fecha_fin ? `<p><strong>Fin:</strong> ${formatDate(saga.fecha_fin)}</p>` : ''}
            ${saga.error_message ? `<p><strong>Error:</strong> ${saga.error_message}</p>` : ''}
            
            <h4>Pasos:</h4>
            <ul>
                ${saga.pasos.map(paso => {
                    let estado = '';
                    let icono = '';
                    let infoAdicional = '';
                    
                    // Lógica corregida basada en el estado de la SAGA y los pasos
                    if (paso.tipo === 'PROCESAR_PAGO') {
                        // Para pagos, verificar el estado en el resultado
                        if (paso.resultado && paso.resultado.estado) {
                            if (paso.resultado.estado === 'EXITOSO') {
                                estado = 'Exitoso';
                                icono = '✅';
                            } else if (paso.resultado.estado === 'FALLIDO') {
                                estado = 'Fallido';
                                icono = '❌';
                            } else {
                                estado = 'Pendiente';
                                icono = '⏳';
                                infoAdicional = ' (Esperando resolución del pago - 10-15 segundos)';
                            }
                        } else {
                            // Si no hay resultado, está pendiente
                            estado = 'Pendiente';
                            icono = '⏳';
                            infoAdicional = ' (Esperando resolución del pago - 10-15 segundos)';
                        }
                    } else if (paso.tipo === 'GENERAR_REPORTE') {
                        // Para reportes, verificar el estado de la SAGA y el pago
                        const pasoPago = saga.pasos.find(p => p.tipo === 'PROCESAR_PAGO');
                        
                        // Si la SAGA está fallida, el reporte también está fallido
                        if (saga.estado === 'FALLIDA') {
                            estado = 'Fallido';
                            icono = '❌';
                            infoAdicional = ' (SAGA fallida - pago no procesado)';
                        }
                        // Si el pago falló, el reporte no se ejecuta (fallido)
                        else if (pasoPago && pasoPago.resultado && pasoPago.resultado.estado === 'FALLIDO') {
                            estado = 'Fallido';
                            icono = '❌';
                            infoAdicional = ' (No se ejecuta - pago fallido)';
                        }
                        // Si el pago está pendiente, el reporte está pendiente
                        else if (!pasoPago || !pasoPago.resultado || !pasoPago.resultado.estado) {
                            estado = 'Pendiente';
                            icono = '⏳';
                            infoAdicional = ' (Esperando que el pago se complete)';
                        }
                        // Si el pago fue exitoso, verificar el estado del reporte
                        else if (pasoPago.resultado.estado === 'EXITOSO') {
                            if (paso.exitoso === true) {
                                estado = 'Exitoso';
                                icono = '✅';
                            } else if (paso.exitoso === false) {
                                estado = 'Fallido';
                                icono = '❌';
                            } else {
                                estado = 'Pendiente';
                                icono = '⏳';
                                infoAdicional = ' (Esperando ejecución)';
                            }
                        }
                    } else {
                        // Para otros pasos (CREAR_CAMPAÑA), usar la lógica normal
                        if (paso.exitoso === true) {
                            estado = 'Exitoso';
                            icono = '✅';
                        } else if (paso.exitoso === false) {
                            estado = 'Fallido';
                            icono = '❌';
                        } else {
                            estado = 'Pendiente';
                            icono = '⏳';
                        }
                    }
                    
                    // Determinar la clase CSS basada en el estado calculado
                    let claseCSS = 'paso-pendiente'; // Por defecto pendiente
                    if (estado === 'Exitoso') {
                        claseCSS = 'paso-exitoso';
                    } else if (estado === 'Fallido') {
                        claseCSS = 'paso-fallido';
                    }
                    
                    return `
                        <li class="paso-item ${claseCSS}">
                            <strong>${paso.tipo}:</strong> 
                            ${icono} ${estado}
                            ${paso.error ? ` - ${paso.error}` : ''}
                            ${paso.resultado && paso.resultado.estado ? ` (${paso.resultado.estado})` : ''}
                            ${infoAdicional}
                        </li>
                    `;
                }).join('')}
            </ul>
            
            ${saga.compensaciones && saga.compensaciones.length > 0 ? `
                <h4>Compensaciones:</h4>
                <ul>
                    ${saga.compensaciones.map(comp => {
                        let estado = '';
                        let icono = '';
                        let infoAdicional = '';
                        
                        if (comp.exitoso === true) {
                            estado = 'Exitoso';
                            icono = '✅';
                        } else if (comp.exitoso === false) {
                            estado = 'Fallido';
                            icono = '❌';
                        } else {
                            estado = 'Pendiente';
                            icono = '⏳';
                        }
                        
                        // Información adicional para compensaciones
                        if (comp.tipo === 'CANCELAR_CAMPAÑA') {
                            infoAdicional = ' (Campaña marcada como CANCELADA)';
                        } else if (comp.tipo === 'REVERTIR_PAGO') {
                            infoAdicional = ' (Pago marcado como REVERSADO)';
                        }
                        
                        return `
                            <li class="paso-item ${estado === 'Exitoso' ? 'paso-exitoso' : estado === 'Fallido' ? 'paso-fallido' : 'paso-pendiente'}">
                                <strong>${comp.tipo}:</strong> 
                                ${icono} ${estado}
                                ${comp.error ? ` - ${comp.error}` : ''}
                                ${infoAdicional}
                            </li>
                        `;
                    }).join('')}
                </ul>
            ` : ''}
        </div>
    `;
    
    showModal(`SAGA ${saga.saga_id ? saga.saga_id.substring(0, 8) : sagaId.substring(0, 8)}...`, content);
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
        minute: '2-digit',
        second: '2-digit'
    });
}

function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Simple notification system
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    if (type === 'success') notification.style.backgroundColor = '#4CAF50';
    else if (type === 'error') notification.style.backgroundColor = '#f44336';
    else if (type === 'warning') notification.style.backgroundColor = '#ff9800';
    else notification.style.backgroundColor = '#2196F3';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
