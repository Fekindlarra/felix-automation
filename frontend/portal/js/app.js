/**
 * Portal Cliente - Aplicación
 * FASE 12 Frontend
 */

console.log('🚀 Portal Cliente iniciando...');

let portalData = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Portal cargando...');

    try {
        showLoading(true);

        // Load portal data
        portalData = await getPortalData();

        if (portalData) {
            console.log('✅ Datos del portal cargados');
            populatePortal();
            setupEventListeners();
        }

        showLoading(false);
    } catch (error) {
        console.error('❌ Portal initialization error:', error);
        showError('Error al cargar el portal');
        showLoading(false);
    }
});

// ============================================================================
// DATA POPULATION
// ============================================================================

function populatePortal() {
    const client = portalData.client;
    const audits = portalData.audits || [];

    // Update client info
    document.getElementById('clientName').textContent = client.name || '-';
    document.getElementById('clientCompany').textContent = client.company || '-';
    document.getElementById('clientEmail').textContent = client.email || '-';
    document.getElementById('clientIndustry').textContent = client.industry || '-';
    document.getElementById('clientScore').textContent = Math.round(client.score) || 0;

    // Update stage status
    updateStageStatus(client.stage);

    // Update latest audit
    if (audits.length > 0) {
        const latestAudit = audits[0];
        renderLatestAudit(latestAudit);
    }

    // Render all audits
    renderAudits(audits);

    // Render propuesta (if available)
    if (portalData.propuesta) {
        renderPropuesta(portalData.propuesta);
    }

    // Render pipeline status
    renderPipelineStatus(client.stage, client.name);
}

// ============================================================================
// STAGE STATUS
// ============================================================================

function updateStageStatus(stage) {
    const stageNames = {
        'prospecto': '📋 Prospecto',
        'propuesta': '📄 Propuesta',
        'negociacion': '💬 Negociación',
        'cerrado': '✅ Cerrado'
    };

    const stageStatus = document.getElementById('stageStatus');
    stageStatus.innerHTML = `<span class="stage-name">${stageNames[stage] || stage}</span>`;

    // Update timeline
    const stages = ['prospecto', 'propuesta', 'negociacion', 'cerrado'];
    const currentIndex = stages.indexOf(stage);

    stages.forEach((s, index) => {
        const step = document.getElementById(`step${index + 1}`);
        if (index < currentIndex) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else if (index === currentIndex) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });
}

// ============================================================================
// AUDIT RENDERING
// ============================================================================

function renderLatestAudit(audit) {
    const container = document.getElementById('latestAuditContent');

    const scoreClass = audit.score >= 75 ? 'high' : audit.score >= 50 ? 'medium' : 'low';

    container.innerHTML = `
        <div class="audit-item" style="flex-direction: row; gap: 1rem; padding: 1.5rem;">
            <div style="flex: 1;">
                <div class="audit-platform">${audit.platform.toUpperCase()}</div>
                <div class="audit-type">${audit.audit_type}</div>
            </div>
            <div class="audit-score ${scoreClass}" style="font-size: 2rem;">
                ${audit.score}
            </div>
        </div>
        <p style="margin-top: 1rem; font-size: 0.875rem; color: var(--gray-600);">
            Última auditoría: ${formatDate(audit.created_at || new Date())}
        </p>
    `;
}

function renderAudits(audits) {
    const container = document.getElementById('auditsContent');

    if (audits.length === 0) {
        container.innerHTML = '<p class="text-center">Sin auditorías disponibles aún</p>';
        return;
    }

    let html = '';

    audits.forEach(audit => {
        const scoreClass = audit.score >= 75 ? 'high' : audit.score >= 50 ? 'medium' : 'low';

        html += `
            <div class="audit-group">
                <div class="audit-group-header">
                    <div class="audit-group-title">${audit.platform.toUpperCase()}</div>
                    <div class="audit-group-title" style="font-size: 0.875rem; margin-top: 0.5rem;">
                        ${audit.audit_type}
                    </div>
                </div>
                <div class="audit-group-items">
                    <div class="audit-item">
                        <span style="flex: 1;">Puntuación</span>
                        <div class="audit-score ${scoreClass}">${audit.score}</div>
                    </div>
                    <div class="audit-item" style="font-size: 0.875rem;">
                        <span style="flex: 1;">Fecha:</span>
                        <span>${formatDate(audit.created_at || new Date())}</span>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ============================================================================
// PROPUESTA RENDERING
// ============================================================================

function renderPropuesta(propuesta) {
    const container = document.getElementById('propuestaContent');

    if (!propuesta) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <p style="font-size: 1.1rem; margin-bottom: 1rem;">
                    📋 Tu propuesta está siendo preparada
                </p>
                <p style="color: var(--gray-600);">
                    Nuestro equipo está analizando tus datos y preparando un plan personalizado.
                    Te notificaremos cuando esté lista.
                </p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="propuesta-container">
            <div style="background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: var(--spacing-lg);">
                <h2>${propuesta.title || 'Propuesta de Servicios'}</h2>
                <p style="margin-top: var(--spacing-md); color: var(--gray-600);">
                    ${propuesta.description || 'Plan personalizado basado en tus auditorías'}
                </p>

                <div style="margin-top: var(--spacing-xl);">
                    <h3>Servicios Incluidos</h3>
                    <ul style="margin-top: var(--spacing-md); list-style: none; padding: 0;">
    `;

    if (propuesta.services && Array.isArray(propuesta.services)) {
        propuesta.services.forEach(service => {
            html += `
                <li style="padding: var(--spacing-md); border-bottom: 1px solid var(--border-color); display: flex; gap: var(--spacing-md);">
                    <span style="font-size: 1.5rem;">✓</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${service.name || 'Servicio'}</div>
                        <div style="font-size: 0.875rem; color: var(--gray-600);">${service.description || ''}</div>
                    </div>
                </li>
            `;
        });
    }

    html += `
                    </ul>
                </div>

                <div style="margin-top: var(--spacing-xl); padding-top: var(--spacing-xl); border-top: 2px solid var(--border-color);">
                    <h3>Inversión</h3>
                    <div style="display: flex; align-items: baseline; gap: var(--spacing-md); margin-top: var(--spacing-md);">
                        <span style="font-size: 2rem; font-weight: 700; color: var(--primary);">
                            ${formatCurrency(propuesta.investment || 0)}
                        </span>
                        <span style="color: var(--gray-600); font-size: 0.875rem;">
                            ${propuesta.frequency || 'por mes'}
                        </span>
                    </div>
                </div>

                <div style="margin-top: var(--spacing-xl); padding: var(--spacing-lg); background: var(--bg); border-radius: var(--radius-md); border-left: 4px solid var(--primary);">
                    <p style="font-size: 0.875rem;">
                        <strong>Próximos Pasos:</strong><br>
                        Si estás interesado en esta propuesta, por favor contáctanos. Nuestro equipo está listo para responder todas tus preguntas y comenzar la implementación.
                    </p>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// ============================================================================
// PIPELINE STATUS
// ============================================================================

function renderPipelineStatus(stage, clientName) {
    const container = document.getElementById('pipelineStatus');

    const stageInfo = {
        'prospecto': {
            emoji: '📋',
            title: 'Prospecto',
            description: 'Tu negocio ha sido identificado como potencial cliente'
        },
        'propuesta': {
            emoji: '📄',
            title: 'Propuesta',
            description: 'Estamos preparando una propuesta personalizada para ti'
        },
        'negociacion': {
            emoji: '💬',
            title: 'Negociación',
            description: 'Estamos discutiendo los términos y ajustes del proyecto'
        },
        'cerrado': {
            emoji: '✅',
            title: 'Cerrado',
            description: 'El contrato ha sido finalizado. ¡Estamos comenzando tu transformación!'
        }
    };

    const info = stageInfo[stage] || stageInfo['prospecto'];

    container.innerHTML = `
        <div style="text-align: center; padding: var(--spacing-xl);">
            <div style="font-size: 3rem; margin-bottom: var(--spacing-lg);">${info.emoji}</div>
            <h3 style="font-size: 1.5rem; margin-bottom: var(--spacing-sm);">${info.title}</h3>
            <p style="color: var(--gray-600); margin-bottom: var(--spacing-xl);">${info.description}</p>

            <div style="display: inline-block; background: var(--bg); padding: var(--spacing-md) var(--spacing-lg); border-radius: var(--radius-md); border: 1px solid var(--border-color);">
                <p style="font-size: 0.875rem; color: var(--gray-600);">
                    <strong>${clientName}</strong><br>
                    Última actualización: ${formatDate(new Date())}
                </p>
            </div>
        </div>
    `;
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // Navigation tabs
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', handleNavigation);
    });

    // Mobile navigation
    document.querySelectorAll('.mobile-nav-item').forEach(item => {
        item.addEventListener('click', handleMobileNavigation);
    });

    // Contact form
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContactForm);
    }

    console.log('✅ Event listeners configurados');
}

function handleNavigation(e) {
    e.preventDefault();

    // Get section from onclick attribute
    const match = e.target.getAttribute('onclick')?.match(/showSection\('(\w+)'\)/);
    if (match) {
        const sectionName = match[1];
        showSection(sectionName);

        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        e.target.classList.add('active');
    }
}

function handleMobileNavigation(e) {
    const match = e.currentTarget.getAttribute('onclick')?.match(/showSection\('(\w+)'\)/);
    if (match) {
        const sectionName = match[1];
        showSection(sectionName);

        // Update active mobile nav item
        document.querySelectorAll('.mobile-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        e.currentTarget.classList.add('active');
    }
}

function handleContactForm(e) {
    e.preventDefault();

    const subject = document.getElementById('messageSubject').value;
    const message = document.getElementById('messageBody').value;

    // Prepare email link
    const emailBody = `Mensaje del Portal Cliente:\n\n${message}\n\nCliente: ${CLIENT_EMAIL}`;
    const mailtoLink = `mailto:felipe@enbuenamesa.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(emailBody)}`;

    // Show notification
    showNotification('📧 Abriendo tu cliente de email...');

    // Open email
    setTimeout(() => {
        window.location.href = mailtoLink;
        document.getElementById('contactForm').reset();
    }, 500);
}

// ============================================================================
// SECTION NAVIGATION
// ============================================================================

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
        window.scrollTo(0, 0);
    }
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

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
// LOGOUT
// ============================================================================

function logout() {
    if (confirm('¿Estás seguro que deseas salir?')) {
        logoutClient();
    }
}

// ============================================================================
// LOGGING
// ============================================================================

console.log('✅ portal/js/app.js cargado correctamente');
console.log(`
╔════════════════════════════════════════════════════════════════╗
║            FELIX AUTOMATION - PORTAL CLIENTE                  ║
║              FASE 12: Frontend Web Dashboard                  ║
╚════════════════════════════════════════════════════════════════╝
`);
