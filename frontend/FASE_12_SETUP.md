# FASE 12 - Setup y Testing

## ✅ Estado Actual

### Archivos Implementados
- ✅ `frontend/login.html` - Página unificada de autenticación
- ✅ `frontend/dashboard/` - Dashboard interno (admin)
  - index.html, css/, js/ (api.js, app.js, charts.js, pipeline.js)
- ✅ `frontend/portal/` - Portal cliente
  - index.html, css/style.css, js/ (api.js, app.js)
- ✅ `backend/app.py` - API FastAPI con 8+ endpoints
- ✅ `backend/auth.py` - Gestión de tokens JWT
- ✅ `backend/config.py` - Configuración centralizada

---

## 🚀 Inicio Rápido

### 1. Instalar Dependencias Backend

```bash
cd /home/claude/felix-automation/backend
pip install -r requirements.txt
```

### 2. Iniciar Backend API

```bash
python app.py
```

Debería ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3. Servir Frontend (en otra terminal)

```bash
# Opción A: Simple HTTP Server (Python)
cd /home/claude/felix-automation/frontend
python -m http.server 3000

# Opción B: Con live-server (si tienes npm)
# npm install -g live-server
# live-server --port=3000
```

### 4. Acceder al Sistema

- **Acceso Admin:** http://localhost:3000/login.html
  - Email: `felipe@enbuenamesa.com`
  - Contraseña: `admin123`
  - Redirección: http://localhost:3000/dashboard/

- **Acceso Cliente:** http://localhost:3000/login.html
  - Cambiar a pestaña "Portal Cliente"
  - Email: Cualquier email registrado en la BD
  - Redirección: http://localhost:3000/portal/

---

## 🧪 Testing Checklist

### Dashboard Admin
- [ ] Login con email/contraseña funciona
- [ ] Token se guarda en localStorage
- [ ] Página redirige a `/dashboard/`
- [ ] Header muestra nombre del usuario
- [ ] Sidebar navega entre 5 secciones
- [ ] KPI cards cargan correctamente
- [ ] Gráficos se renderizan (Chart.js)
- [ ] Pipeline drag-drop funciona
- [ ] Búsqueda de clientes filtra
- [ ] Logout limpia tokens

### Portal Cliente
- [ ] Login con solo email funciona
- [ ] Redirección a `/portal/`
- [ ] Muestra datos del cliente correcto
- [ ] Auditorías se cargan
- [ ] Propuesta se renderiza
- [ ] Timeline del pipeline actualizada
- [ ] Contacto muestra info
- [ ] Mobile nav funciona en mobile
- [ ] Dark mode activado en preferencias

### Autenticación
- [ ] Token admin expira en 24 horas
- [ ] Token cliente expira en 1 hora
- [ ] Logout invalida token
- [ ] URL protegidas redirigen a login

---

## 📊 Endpoints API Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login` | Admin login (email+pass) |
| POST | `/api/auth/portal-access` | Cliente acceso (email) |
| GET | `/api/auth/verify` | Verificar token válido |
| GET | `/api/dashboard/kpis` | KPIs del dashboard |
| GET | `/api/dashboard/clients` | Listado paginado de clientes |
| GET | `/api/dashboard/pipeline` | Estado pipeline |
| GET | `/api/clients/{id}` | Detalles cliente |
| GET | `/api/clients/{id}/audits` | Auditorías cliente |
| GET | `/api/portal/me` | Datos portal (cliente) |

---

## 🔧 Configuración Importante

### Backend (`config.py`)

```python
# Cambiar en PRODUCCIÓN
SECRET_KEY = "tu-clave-secreta-aqui"  # Usar variable de entorno
ADMIN_EMAIL = "felipe@enbuenamesa.com"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # Admin (24 horas)
PORTAL_TOKEN_EXPIRE_MINUTES = 60    # Cliente (1 hora)
```

### CORS

```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
```

Agregar dominio de producción cuando esté listo.

---

## 📝 Usuario Demo

**Admin:**
```
Email: felipe@enbuenamesa.com
Contraseña: admin123
Tipo: Admin (24hr token)
```

**Cliente (Crear primero en BD):**
```
Email: cliente@ejemplo.com
Nombre: Nombre Cliente
Empresa: Empresa Ejemplo
Score: 75
Stage: prospecto
```

---

## 🐛 Troubleshooting

### Error: "No se puede conectar al servidor API"
- ✅ Verificar que backend está corriendo en `http://localhost:8000`
- ✅ Verificar CORS en `config.py`
- ✅ Frontend debe estar en puerto 3000

### Error: "Token inválido"
- ✅ Verificar `SECRET_KEY` es igual en backend
- ✅ Verificar token no está expirado
- ✅ Limpiar localStorage y reintentar login

### Gráficos no se renderizan
- ✅ Verificar Chart.js se carga desde CDN
- ✅ Verificar consola del navegador para errores
- ✅ Verificar datos KPI se retornan correctamente

### Portal cliente no muestra datos
- ✅ Verificar cliente existe en BD
- ✅ Verificar endpoint `/api/portal/me` retorna datos
- ✅ Verificar token cliente es válido

---

## 📦 Estructura Final

```
/home/claude/felix-automation/
├── frontend/
│   ├── login.html                    ← Autenticación unificada
│   ├── FASE_12_SETUP.md             ← Este archivo
│   ├── dashboard/
│   │   ├── index.html               ← Admin dashboard
│   │   ├── css/ (style.css, responsive.css, dashboard.css)
│   │   └── js/ (api.js, app.js, charts.js, pipeline.js)
│   └── portal/
│       ├── index.html               ← Cliente portal
│       ├── css/style.css            ← Portal estilos
│       └── js/ (api.js, app.js)
├── backend/
│   ├── app.py                       ← FastAPI main
│   ├── auth.py                      ← Autenticación JWT
│   ├── config.py                    ← Configuración
│   └── requirements.txt
├── data/
│   └── pipeline.db                  ← SQLite (del orchestrator)
└── orchestrator.py                  ← Sistema principal (FASE 9)
```

---

## 🚀 Deployment Próximos Pasos

### Para Producción
1. Cambiar `SECRET_KEY` a valor seguro
2. Cambiar demo credentials
3. Configurar CORS para dominio real
4. Usar HTTPS
5. Usar PostgreSQL en lugar de SQLite
6. Variables de entorno para configuración sensible
7. Rate limiting activado
8. Logging centralizado

---

## 📞 Soporte

Si algo no funciona:
1. Verificar logs en consola (backend + frontend)
2. Revisar Network tab (browser DevTools)
3. Revisar database si datos existen
4. Contactar a Felipe: felipe@enbuenamesa.com

---

**Estado:** ✅ FASE 12 Completada - Lista para Testing
**Última actualización:** 2026-10-05
**Próxima fase:** FASE 13 - Integraciones Avanzadas
