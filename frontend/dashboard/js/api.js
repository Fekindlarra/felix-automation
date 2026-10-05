/**
 * API Client - Felix Dashboard
 * Handles all backend API calls
 * FASE 12 Frontend
 */

const API_BASE_URL = 'http://localhost:8000/api';
let AUTH_TOKEN = localStorage.getItem('auth_token') || null;

// ============================================================================
// AUTH REQUESTS
// ============================================================================

async function loginAdmin(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            throw new Error('Login fallido');
        }

        const data = await response.json();
        AUTH_TOKEN = data.access_token;
        localStorage.setItem('auth_token', AUTH_TOKEN);
        localStorage.setItem('user_name', data.user.name);

        return data;
    } catch (error) {
        console.error('❌ Login error:', error);
        throw error;
    }
}

async function verifyToken(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify?token=${token}`);
        const data = await response.json();
        return data.valid;
    } catch (error) {
        console.error('❌ Verify token error:', error);
        return false;
    }
}

function logout() {
    AUTH_TOKEN = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_name');
    window.location.href = '/login.html';
}

// ============================================================================
// DASHBOARD REQUESTS
// ============================================================================

async function getDashboardKPIs() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/kpis?token=${AUTH_TOKEN}`);

        if (!response.ok) {
            throw new Error('Error fetching KPIs');
        }

        return await response.json();
    } catch (error) {
        console.error('❌ KPI fetch error:', error);
        showError('Error al cargar KPIs');
        throw error;
    }
}

async function getAllClients(skip = 0, limit = 50) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/dashboard/clients?token=${AUTH_TOKEN}&skip=${skip}&limit=${limit}`
        );

        if (!response.ok) {
            throw new Error('Error fetching clients');
        }

        return await response.json();
    } catch (error) {
        console.error('❌ Clients fetch error:', error);
        showError('Error al cargar clientes');
        throw error;
    }
}

async function getPipelineStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/pipeline?token=${AUTH_TOKEN}`);

        if (!response.ok) {
            throw new Error('Error fetching pipeline');
        }

        return await response.json();
    } catch (error) {
        console.error('❌ Pipeline fetch error:', error);
        showError('Error al cargar pipeline');
        throw error;
    }
}

// ============================================================================
// CLIENT REQUESTS
// ============================================================================

async function getClientById(clientId) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/clients/${clientId}?token=${AUTH_TOKEN}`
        );

        if (!response.ok) {
            throw new Error('Error fetching client');
        }

        return await response.json();
    } catch (error) {
        console.error('❌ Get client error:', error);
        showError('Error al obtener cliente');
        throw error;
    }
}

async function getClientAudits(clientId) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/clients/${clientId}/audits?token=${AUTH_TOKEN}`
        );

        if (!response.ok) {
            throw new Error('Error fetching audits');
        }

        return await response.json();
    } catch (error) {
        console.error('❌ Get audits error:', error);
        showError('Error al obtener auditorías');
        throw error;
    }
}

async function updateClientStage(clientId, newStage) {
    try {
        const response = await fetch(`${API_BASE_URL}/pipeline/${clientId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            },
            body: JSON.stringify({ stage: newStage })
        });

        if (!response.ok) {
            throw new Error('Error updating client stage');
        }

        return await response.json();
    } catch (error) {
        console.error('❌ Update stage error:', error);
        showError('Error al actualizar etapa del cliente');
        throw error;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showError(message) {
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorModal.style.display = 'flex';
}

function closeErrorModal() {
    const errorModal = document.getElementById('errorModal');
    errorModal.style.display = 'none';
}

function showLoading(show = true) {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = show ? 'flex' : 'none';
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

// ============================================================================
// HEALTH CHECK
// ============================================================================

async function checkAPIHealth() {
    try {
        const response = await fetch(`http://localhost:8000/health`);
        if (response.ok) {
            console.log('✅ API Health: OK');
            return true;
        }
    } catch (error) {
        console.error('❌ API Health Check failed:', error);
        showError('No se puede conectar al servidor API. Verifica que esté corriendo en localhost:8000');
        return false;
    }
}

// ============================================================================
// AUTHENTICATION CHECKS
// ============================================================================

async function ensureAuthenticated() {
    if (!AUTH_TOKEN) {
        // Try to get stored token
        AUTH_TOKEN = localStorage.getItem('auth_token');
    }

    if (!AUTH_TOKEN) {
        window.location.href = '/login.html';
        return false;
    }

    // Verify token is still valid
    const isValid = await verifyToken(AUTH_TOKEN);
    if (!isValid) {
        logout();
        return false;
    }

    return true;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', async () => {
    const isHealthy = await checkAPIHealth();
    if (!isHealthy) {
        showError('No se puede conectar al servidor. Por favor verifica que FastAPI esté corriendo en puerto 8000.');
        return;
    }

    const isAuthenticated = await ensureAuthenticated();
    if (!isAuthenticated) {
        return;
    }

    // Update UI with user info
    const userName = localStorage.getItem('user_name');
    if (userName) {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) {
            userInfo.textContent = userName;
        }
    }
});
