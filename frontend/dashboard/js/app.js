/**
 * Main Application - Felix Dashboard
 * FASE 12 Frontend
 */

console.log('🚀 Felix Dashboard iniciando...');

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Documento cargado');

    // Check API connection
    const isHealthy = await checkAPIHealth();
    if (!isHealthy) {
        showError('No se puede conectar al servidor API. Asegúrate de que FastAPI esté corriendo en localhost:8000');
        return;
    }

    // Check authentication
    const isAuthenticated = await ensureAuthenticated();
    if (!isAuthenticated) {
        return;
    }

    console.log('✅ Autenticación verificada');

    // Setup event listeners
    setupEventListeners();

    // Load dashboard
    await loadDashboard();

    console.log('🎉 Dashboard listo');
});

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // Section navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', handleNavigation);
    });

    // Search functionality
    const searchInput = document.getElementById('searchClients');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterPipeline(e.target.value);
        });
    }

    // Logout button
    const logoutBtn = document.querySelector('.btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('¿Estás seguro que deseas salir?')) {
                logout();
            }
        });
    }

    console.log('✅ Event listeners configurados');
}

// ============================================================================
// NAVIGATION
// ============================================================================

function handleNavigation(e) {
    e.preventDefault();

    // Get section from onclick attribute
    const match = e.target.getAttribute('onclick')?.match(/showSection\('(\w+)'\)/);
    if (match) {
        const sectionName = match[1];
        showSection(sectionName);
    }
}

function showSection(sectionName) {
    console.log(`📑 Mostrando sección: ${sectionName}`);

    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const section = document.getElementById(sectionName);
    if (section) {
        section.classList.add('active');
    }

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    const activeNav = document.querySelector(`.nav-item[onclick*="${sectionName}"]`);
    if (activeNav) {
        activeNav.classList.add('active');
    }

    // Load section-specific data
    switch (sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'clients':
            loadClientsTable();
            break;
        case 'pipeline':
            loadPipelineView();
            break;
        case 'audits':
            loadAuditsView();
            break;
        case 'reports':
            loadReportsView();
            break;
    }
}

// ============================================================================
// DASHBOARD SECTION
// ============================================================================

async function loadDashboard() {
    try {
        showLoading(true);

        // Initialize charts and KPIs
        await initializeCharts();

        showLoading(false);
    } catch (error) {
        console.error('❌ Dashboard load error:', error);
        showError('Error al cargar el dashboard');
    }
}

// ============================================================================
// CLIENTS SECTION
// ============================================================================

async function loadClientsTable() {
    try {
        showLoading(true);

        const data = await getAllClients(0, 50);
        const tbody = document.getElementById('clientsTableBody');

        if (!tbody) return;

        tbody.innerHTML = ''; // Clear

        if (data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No hay clientes</td></tr>';
            return;
        }

        data.data.forEach(client => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${client.id}</td>
                <td><strong>${client.name}</strong></td>
                <td>${client.company}</td>
                <td>${client.email}</td>
                <td><span class="badge badge-${client.stage}">${client.stage}</span></td>
                <td><strong>${client.score}/100</strong></td>
                <td>
                    <button class="btn-small" onclick="showClientDetails(${client.id})">Ver</button>
                </td>
            `;
            tbody.appendChild(row);
        });

        showLoading(false);
    } catch (error) {
        console.error('❌ Clients load error:', error);
        showError('Error al cargar clientes');
    }
}

// ============================================================================
// PIPELINE SECTION
// ============================================================================

async function loadPipelineView() {
    try {
        showLoading(true);
        await initializePipeline();
        showLoading(false);
    } catch (error) {
        console.error('❌ Pipeline load error:', error);
        showError('Error al cargar pipeline');
    }
}

// ============================================================================
// AUDITS SECTION
// ============================================================================

async function loadAuditsView() {
    try {
        showLoading(true);

        const data = await getAllClients(0, 100);
        const content = document.getElementById('auditsContent');

        if (!content) return;

        let html = '<div class="audits-list">';

        for (const client of data.data) {
            try {
                const audits = await getClientAudits(client.id);

                const auditsHTML = audits.audits.map(audit => `
                    <div class="audit-item">
                        <div class="audit-platform">${audit.platform.toUpperCase()}</div>
                        <div class="audit-score ${audit.score >= 75 ? 'high' : audit.score >= 50 ? 'medium' : 'low'}">
                            ${audit.score}
                        </div>
                        <div class="audit-type">${audit.audit_type}</div>
                    </div>
                `).join('');

                html += `
                    <div class="audit-group">
                        <div class="audit-group-header">
                            <div class="audit-group-title">${client.name}</div>
                            <div class="audit-group-title" style="font-size: 0.875rem;">${client.company}</div>
                        </div>
                        <div class="audit-group-items">
                            ${auditsHTML || '<p>Sin auditorías</p>'}
                        </div>
                    </div>
                `;
            } catch (error) {
                console.warn(`Error fetching audits for client ${client.id}:`, error);
            }
        }

        html += '</div>';
        content.innerHTML = html;

        showLoading(false);
    } catch (error) {
        console.error('❌ Audits load error:', error);
        showError('Error al cargar auditorías');
    }
}

// ============================================================================
// REPORTS SECTION
// ============================================================================

function loadReportsView() {
    // Reports functionality
    console.log('📋 Reports section loaded');
}

function generateReport(type) {
    console.log(`📊 Generating ${type} report...`);
    showNotification(`Reporte ${type.toUpperCase()} generado exitosamente`);
}

// ============================================================================
// UTILITY FUNCTIONS (additional to api.js)
// ============================================================================

function closeErrorModal() {
    const errorModal = document.getElementById('errorModal');
    if (errorModal) {
        errorModal.style.display = 'none';
    }
}

function showNotification(message, type = 'success', duration = 3000) {
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
    }, duration);
}

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K: Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('searchClients');
        if (searchInput) {
            searchInput.focus();
        }
    }

    // Escape: Close modal
    if (e.key === 'Escape') {
        closeErrorModal();
    }
});

// ============================================================================
// LOGGING
// ============================================================================

console.log('✅ app.js cargado correctamente');
console.log(`
╔════════════════════════════════════════════════════════════════╗
║         FELIX AUTOMATION - DASHBOARD FRONTEND                 ║
║         FASE 12: Dashboard Interno + Portal Cliente           ║
╚════════════════════════════════════════════════════════════════╝
`);
