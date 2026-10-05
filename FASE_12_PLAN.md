# FASE 12 - FRONTEND WEB DASHBOARD

## 📋 PLAN ESTRATÉGICO

**Objetivo:** Crear interfaz web profesional (Dashboard Interno + Portal Cliente) que transforme el sistema de automatización en producto SaaS visible.

**Duración estimada:** 5-7 días  
**Inicio:** 2026-10-05  
**Status:** 🚀 EN INICIO

---

## 🎯 DELIVERABLES

### 1. Backend API REST (FastAPI)
- Endpoints para Dashboard Interno (Felipe)
- Endpoints para Portal Cliente (clientes)
- Autenticación JWT + API Keys
- CORS habilitado para frontend

### 2. Dashboard Interno (Felipe)
- **Header**: Logo, perfil, logout
- **KPI Cards**: 
  - Total clientes, conversiones, revenue forecast
  - Score promedio, leads por etapa
- **Pipeline Visual**: 4 etapas con drag-drop (Prospecto → Propuesta → Negociación → Cerrado)
- **Tabla de Clientes**: Con filtros, búsqueda, estado
- **Auditorías**: Vista detallada de audits por cliente
- **Reportes**: Generación PDF de reportes

### 3. Portal Cliente (por cliente)
- **Autenticación**: Email + token (sin contraseña)
- **Dashboard Personalizado**:
  - Auditoría resumida (web/ads/shopify/jumpseller/code)
  - Propuesta descargable
  - Timeline de implementación
  - Estado actual en pipeline
- **Responsive**: Mobile-first design

---

## 🏗️ ARQUITECTURA

### Stack Tecnológico

```
Frontend:
├── HTML5 + CSS3 + JavaScript (vanilla)
├── Charts.js para gráficos
├── Socket.io para actualizaciones en tiempo real (opcional)
└── Mobile-responsive (Tailwind CSS)

Backend:
├── FastAPI (Python)
├── SQLite3 (ya existe)
├── JWT para autenticación
└── CORS habilitado

Database:
└── data/pipeline.db (ya existe)
```

### Estructura de Carpetas

```
/felix-automation/
├── backend/
│   ├── app.py                      # App principal FastAPI
│   ├── requirements.txt            # Dependencias
│   ├── config.py                   # Configuración
│   ├── auth.py                     # Autenticación JWT
│   └── routes/
│       ├── __init__.py
│       ├── dashboard.py            # Dashboard interno
│       ├── clients.py              # Gestión clientes
│       ├── audits.py               # Auditorías
│       ├── pipeline.py             # Pipeline management
│       └── portal.py               # Portal cliente
│
├── frontend/
│   ├── dashboard/                  # Dashboard Interno
│   │   ├── index.html
│   │   ├── css/
│   │   │   ├── style.css
│   │   │   ├── dashboard.css
│   │   │   └── responsive.css
│   │   ├── js/
│   │   │   ├── app.js
│   │   │   ├── api.js              # Llamadas a backend
│   │   │   ├── charts.js           # Gráficos y visualizaciones
│   │   │   ├── pipeline.js         # Manejo del pipeline
│   │   │   └── utils.js
│   │   └── assets/
│   │       ├── logo.svg
│   │       └── favicon.ico
│   │
│   └── portal/                     # Portal Cliente
│       ├── index.html
│       ├── css/
│       │   ├── style.css
│       │   └── responsive.css
│       ├── js/
│       │   ├── app.js
│       │   ├── api.js
│       │   └── utils.js
│       └── assets/
│
└── docs/
    └── FASE_12_API.md             # Documentación API
```

---

## 🔄 FASE 12: PLAN DE IMPLEMENTACIÓN (5-7 DÍAS)

### Día 1-2: Backend API Fundación
**Archivos a crear:**
- `backend/app.py` - App FastAPI base
- `backend/config.py` - Configuración
- `backend/auth.py` - JWT authentication
- `backend/requirements.txt` - Dependencias

**Endpoints básicos:**
```python
POST   /api/auth/login              # Login Felipe
GET    /api/auth/verify             # Verificar token
POST   /api/auth/portal-access      # Acceso portal cliente (email)

GET    /api/dashboard/kpis          # KPIs para dashboard interno
GET    /api/dashboard/clients       # Lista clientes
GET    /api/dashboard/pipeline      # Estado pipeline
GET    /api/dashboard/stats         # Estadísticas

GET    /api/clients/{id}            # Detalle cliente
GET    /api/clients/{id}/audits     # Auditorías cliente
GET    /api/clients/{id}/proposal   # Propuesta cliente

PATCH  /api/pipeline/{client_id}    # Mover cliente en pipeline

GET    /api/portal/{client_id}      # Portal data cliente
GET    /api/portal/{client_id}/audit/{audit_id}  # Detalle audit
```

### Día 2-3: Dashboard Interno Frontend
**Archivos a crear:**
- `frontend/dashboard/index.html`
- `frontend/dashboard/css/style.css`
- `frontend/dashboard/js/app.js`
- `frontend/dashboard/js/api.js`
- `frontend/dashboard/js/charts.js`
- `frontend/dashboard/js/pipeline.js`

**Componentes:**
- Header con logo, usuario, logout
- KPI cards (4 cards principales)
- Gráfico de conversión (funnels por etapa)
- Tabla de clientes con filtros/búsqueda
- Pipeline visual con drag-drop
- Sidebar navegación

### Día 3-4: Portal Cliente Frontend
**Archivos a crear:**
- `frontend/portal/index.html`
- `frontend/portal/css/style.css`
- `frontend/portal/js/app.js`

**Componentes:**
- Login simple (email únicamente)
- Dashboard cliente personalizado
- Resumen auditoría (web/ads/shopify/jumpseller/code)
- Propuesta PDF descargable
- Timeline implementación

### Día 4-5: Integración y Realtime
- WebSocket para actualizaciones en tiempo real
- Cargar datos desde orchestrator.py
- Testing de endpoints
- Manejo de errores y edge cases

### Día 5-6: Testing y Optimización
- Tests unitarios de API endpoints
- Tests de frontend (integración)
- Performance optimization
- Mobile responsiveness verification

### Día 6-7: Deployment y Documentación
- Setup deployment (local/production)
- Documentación de endpoints (OpenAPI/Swagger)
- Guía de usuario (Felipe y clientes)
- Versión inicial lista para producción

---

## 📊 DATOS Y ENDPOINTS PRINCIPALES

### Dashboard Interno - KPIs
```json
{
  "total_clientes": 25,
  "clientes_activos": 18,
  "conversion_rate": 72,
  "revenue_forecast_monthly": 450000,
  "pipeline": {
    "prospecto": 8,
    "propuesta": 5,
    "negociacion": 3,
    "cerrado": 9
  },
  "score_promedio": 74,
  "audits_pendientes": 2
}
```

### Cliente en Portal
```json
{
  "id": 1,
  "name": "Raíces de Cauquenes",
  "email": "contacto@raicesdecauquenes.cl",
  "stage": "propuesta",
  "audits": [
    {
      "platform": "web",
      "score": 72,
      "audit_type": "blackbox",
      "timestamp": "2026-10-05T10:30:00"
    },
    {
      "platform": "shopify",
      "score": 79,
      "audit_type": "whitebox",
      "timestamp": "2026-10-05T11:00:00"
    }
  ],
  "proposal": {
    "status": "sent",
    "sent_at": "2026-10-05T09:00:00",
    "estimated_cost": 2500000,
    "estimated_duration": "4 semanas"
  }
}
```

---

## 🔐 SEGURIDAD

### Autenticación
- **Interno**: JWT token (Felipe - acceso completo)
- **Cliente**: Email token (acceso solo a datos del cliente)
- No se requiere contraseña para portal cliente (email verification)

### Autorización
- Felipe: Acceso a todos los datos
- Cliente: Solo datos de su empresa

### CORS
- Permitir localhost para desarrollo
- Dominios específicos para producción

---

## 📈 MÉTRICAS DE ÉXITO

- ✅ API funcionando 100% (todos endpoints testeados)
- ✅ Dashboard Interno cargando datos en <2 segundos
- ✅ Portal Cliente accesible y responsive
- ✅ Autenticación funcionando
- ✅ Gráficos actualizando en tiempo real
- ✅ Pipeline drag-drop operacional
- ✅ Documentación API completa
- ✅ Zero error logs en producción

---

## 🚀 SIGUIENTES PASOS (FASE 13+)

Después de FASE 12:
1. **FASE 13**: Integraciones Externas (Zapier/Make webhooks)
2. **FASE 14**: Analytics & Reporting (reportes automáticos)
3. **FASE 15**: Escalabilidad (PostgreSQL, Redis cache)

---

## 📝 NOTAS

- Reutilizar config.yaml y orchestrator.py existentes
- Mantener 100% backward compatibility con OPCIÓN C
- Frontend minimalista pero profesional (no sobredesignar)
- Priorizar funcionalidad sobre estética
- Todos los gráficos/datos en tiempo real

---

**Status:** 🟡 PLANIFICADO  
**Inicio estimado:** HOY (2026-10-05)  
**Next Update:** Después de crear Backend API (Día 1-2)
