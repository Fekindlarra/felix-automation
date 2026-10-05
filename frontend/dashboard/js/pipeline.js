/**
 * Pipeline Management Module - Felix Dashboard
 * Handles pipeline visualization and drag-drop
 * FASE 12 Frontend
 */

let pipelineData = {};
let draggedElement = null;

/**
 * Initialize pipeline view
 */
async function initializePipeline() {
    try {
        showLoading(true);
        const data = await getPipelineStatus();
        pipelineData = data.pipeline;
        renderPipeline(pipelineData);
    } catch (error) {
        console.error('❌ Pipeline initialization error:', error);
    } finally {
        showLoading(false);
    }
}

/**
 * Render pipeline with client cards
 */
function renderPipeline(pipeline) {
    const stages = ['prospecto', 'propuesta', 'negociacion', 'cerrado'];

    stages.forEach(stage => {
        const stageContainer = document.getElementById(`stage-${stage}`);
        if (!stageContainer) return;

        stageContainer.innerHTML = ''; // Clear existing

        const clients = pipeline[stage] || [];

        if (clients.length === 0) {
            stageContainer.innerHTML = '<div class="empty-stage">Sin clientes</div>';
            return;
        }

        clients.forEach(client => {
            const card = createClientCard(client, stage);
            stageContainer.appendChild(card);
        });
    });
}

/**
 * Create a client card element
 */
function createClientCard(client, stage) {
    const card = document.createElement('div');
    card.className = 'client-card';
    card.draggable = true;
    card.dataset.clientId = client.id;
    card.dataset.stage = stage;

    const scoreClass = client.score >= 75 ? 'high' : client.score >= 50 ? 'medium' : 'low';

    card.innerHTML = `
        <div class="client-card-name">${client.name}</div>
        <div class="client-card-company">${client.company}</div>
        <span class="client-card-score">${client.score}/100</span>
    `;

    // Drag events
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);

    // Click to expand
    card.addEventListener('click', () => showClientDetails(client.id));

    return card;
}

/**
 * Handle drag start
 */
function handleDragStart(e) {
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

/**
 * Handle drag end
 */
function handleDragEnd(e) {
    this.classList.remove('dragging');

    // Remove drag-over classes from all stages
    document.querySelectorAll('.stage-clients').forEach(stage => {
        stage.classList.remove('drag-over');
    });
}

/**
 * Setup drop zones
 */
function setupDropZones() {
    document.querySelectorAll('.stage-clients').forEach(zone => {
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('drop', handleDrop);
        zone.addEventListener('dragleave', handleDragLeave);
    });
}

/**
 * Handle drag over
 */
function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
}

/**
 * Handle drag leave
 */
function handleDragLeave(e) {
    if (e.target === this) {
        this.classList.remove('drag-over');
    }
}

/**
 * Handle drop
 */
async function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    this.classList.remove('drag-over');

    if (!draggedElement) return;

    const clientId = parseInt(draggedElement.dataset.clientId);
    const oldStage = draggedElement.dataset.stage;
    const newStage = this.id.replace('stage-', '');

    // Prevent dropping in the same stage
    if (oldStage === newStage) {
        draggedElement = null;
        return;
    }

    // Update on server
    try {
        showLoading(true);
        await updateClientStage(clientId, newStage);

        // Update local data
        pipelineData[oldStage] = pipelineData[oldStage].filter(c => c.id !== clientId);
        const client = draggedElement.cloneNode(true);
        draggedElement.remove();

        // Re-render
        await initializePipeline();

        showNotification(`Cliente movido a ${newStage.toUpperCase()}`);
    } catch (error) {
        console.error('❌ Drop error:', error);
        showError('Error al mover cliente');
    } finally {
        showLoading(false);
        draggedElement = null;
    }
}

/**
 * Show client details modal
 */
async function showClientDetails(clientId) {
    try {
        showLoading(true);

        const client = await getClientById(clientId);
        const audits = await getClientAudits(clientId);

        const modal = createClientDetailsModal(client, audits.audits);
        document.body.appendChild(modal);

        modal.style.display = 'flex';

        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

    } catch (error) {
        console.error('❌ Details error:', error);
        showError('Error al cargar detalles del cliente');
    } finally {
        showLoading(false);
    }
}

/**
 * Create client details modal
 */
function createClientDetailsModal(client, audits) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'clientDetailsModal';

    const auditsHTML = audits.map(audit => `
        <div class="audit-item">
            <div class="audit-platform">${audit.platform.toUpperCase()}</div>
            <div class="audit-score ${audit.score >= 75 ? 'high' : audit.score >= 50 ? 'medium' : 'low'}">
                ${audit.score}
            </div>
            <div class="audit-type">${audit.audit_type}</div>
        </div>
    `).join('');

    modal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>${client.name}</h2>

            <div class="client-detail-section">
                <h3>Información</h3>
                <p><strong>Empresa:</strong> ${client.company}</p>
                <p><strong>Email:</strong> ${client.email}</p>
                <p><strong>Industria:</strong> ${client.industry || 'N/A'}</p>
                <p><strong>Etapa:</strong> <span class="badge badge-${client.stage}">${client.stage}</span></p>
                <p><strong>Score:</strong> ${client.score}/100</p>
            </div>

            <div class="client-detail-section">
                <h3>Auditorías</h3>
                <div class="audit-group-items">
                    ${auditsHTML || '<p>Sin auditorías</p>'}
                </div>
            </div>

            <div class="modal-actions">
                <button class="btn-primary" onclick="this.parentElement.parentElement.parentElement.remove()">Cerrar</button>
            </div>
        </div>
    `;

    return modal;
}

/**
 * Filter pipeline by search term
 */
function filterPipeline(searchTerm) {
    const cards = document.querySelectorAll('.client-card');

    cards.forEach(card => {
        const name = card.querySelector('.client-card-name').textContent.toLowerCase();
        const company = card.querySelector('.client-card-company').textContent.toLowerCase();

        if (name.includes(searchTerm.toLowerCase()) || company.includes(searchTerm.toLowerCase())) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Get pipeline statistics
 */
function getPipelineStats() {
    const stats = {
        prospecto: pipelineData.prospecto?.length || 0,
        propuesta: pipelineData.propuesta?.length || 0,
        negociacion: pipelineData.negociacion?.length || 0,
        cerrado: pipelineData.cerrado?.length || 0,
        total: 0
    };

    stats.total = Object.values(stats).reduce((a, b) => a + b, 0) - 1; // Exclude total

    return stats;
}

/**
 * Export pipeline as CSV
 */
function exportPipelineAsCSV() {
    let csv = 'Cliente,Empresa,Etapa,Score\n';

    Object.entries(pipelineData).forEach(([stage, clients]) => {
        clients.forEach(client => {
            csv += `${client.name},${client.company},${stage},${client.score}\n`;
        });
    });

    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = 'pipeline.csv';
    link.click();
}

/**
 * Show notification
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background-color: ${type === 'success' ? '#10B981' : '#EF4444'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

/**
 * Initialize pipeline on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    setupDropZones();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializePipeline,
        renderPipeline,
        setupDropZones,
        getPipelineStats,
        exportPipelineAsCSV
    };
}
