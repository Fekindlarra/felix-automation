/**
 * API Client - Portal Cliente
 * Acceso solo lectura a datos del cliente
 * FASE 12 Frontend
 */

const API_BASE_URL = 'http://localhost:8000/api';
let PORTAL_TOKEN = localStorage.getItem('portal_token') || null;
let CLIENT_EMAIL = localStorage.getItem('client_email') || null;

// ============================================================================
// AUTHENTICATION
// ============================================================================

async function ensurePortalAuthenticated() {
    if (!PORTAL_TOKEN) {
        PORTAL_TOKEN = localStorage.getItem('portal_token');
    }

    if (!PORTAL_TOKEN) {
        window.location.href = '/login.html';
        return false;
    }

    // Verify token is still valid
    const isValid = await verifyPortalToken(PORTAL_TOKEN);
    if (!isValid) {
        logoutClient();
        return false;
    }

    return true;
}

async function verifyPortalToken(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify?token=${token}`);
        const data = await response.json();
        return data.valid;
    } catch (error) {
        console.error('❌ Token verification error:', error);
        return false;
    }
}

function logoutClient() {
    PORTAL_TOKEN = null;
    localStorage.removeItem('portal_token');
    localStorage.removeItem('client_email');
    localStorage.removeItem('user_type');
    window.location.href = '/login.html';
}

// ============================================================================
// PORTAL REQUESTS
// ============================================================================

async function getPortalData() {
    try {
        const response = await fetch(`${API_BASE_URL}/portal/me?token=${PORTAL_TOKEN}`);

        if (!response.ok) {
            if (response.status === 401) {
                logoutClient();
                return null;
            }
            throw new Error('Error fetching portal data');
        }

        return await response.json();
    } catch (error) {
        console.error('❌ Portal data fetch error:', error);
        showError('Error al cargar datos del portal');
        throw error;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showError(message) {
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = '⚠️ ' + message;
    errorModal.style.display = 'flex';
}

function closeErrorModal() {
    const errorModal = document.getElementById('errorModal');
    errorModal.style.display = 'none';
}

function showLoading(show = true) {
    const loading = document.getElementById('loading');
    if (loading) {
        if (show) {
            loading.classList.add('show');
        } else {
            loading.classList.remove('show');
        }
    }
}

function formatCurrency(value) {
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatNumber(value) {
    return new Intl.NumberFormat('es-CL').format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Portal Cliente cargando...');

    const isAuthenticated = await ensurePortalAuthenticated();
    if (!isAuthenticated) {
        return;
    }

    console.log('✅ Autenticación verificada');

    // Update user info display
    const userInfo = document.getElementById('userInfo');
    if (userInfo && CLIENT_EMAIL) {
        userInfo.textContent = CLIENT_EMAIL;
    }
});

console.log('✅ portal/js/api.js cargado correctamente');
