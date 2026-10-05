# 🚀 FASE 12 - INICIO RÁPIDO

## ✅ Estado: TODO LISTO PARA USAR

### 18 Archivos Implementados
```
✅ backend/app.py
✅ backend/auth.py
✅ backend/config.py
✅ backend/requirements.txt

✅ frontend/login.html
✅ frontend/dashboard/index.html
✅ frontend/dashboard/css/ (3 archivos)
✅ frontend/dashboard/js/ (4 archivos)
✅ frontend/portal/index.html
✅ frontend/portal/css/style.css
✅ frontend/portal/js/ (2 archivos)

✅ Documentación (FASE_12_STATUS.md, FASE_12_SETUP.md)
```

---

## ⚡ Inicio en 5 Minutos

### Terminal 1: Backend API
```bash
cd /home/claude/felix-automation/backend
pip install -r requirements.txt
python app.py
```
✅ Verás: `Uvicorn running on http://127.0.0.1:8000`

### Terminal 2: Servir Frontend
```bash
cd /home/claude/felix-automation/frontend
python -m http.server 3000
```
✅ Verás: `Serving HTTP on 0.0.0.0 port 3000`

### Browser: Acceder
```
http://localhost:3000/login.html
```

---

## 👤 Credenciales Demo

### Admin Dashboard
```
Email:    felipe@enbuenamesa.com
Password: admin123
↓
Acceso:   http://localhost:3000/dashboard/
Token:    24 horas
```

### Cliente Portal
```
Email:    cliente@ejemplo.com (o cualquier registrado)
↓
Acceso:   http://localhost:3000/portal/
Token:    1 hora
```

---

## 🎯 Qué Puedes Hacer

### Dashboard Admin (5 opciones)
- 📊 Ver KPIs en tiempo real
- 👥 Gestionar clientes
- 🎯 Pipeline drag-drop
- 🔍 Ver auditorías
- 📈 Generar reportes

### Portal Cliente (5 opciones)
- 📌 Ver tu progreso
- 🔍 Revisar auditorías
- 📄 Leer propuesta
- 🎯 Ver dónde estás
- 💬 Contactar equipo

---

## 📱 Responsive

Funciona en:
- ✅ Desktop (1024px+)
- ✅ Tablet (768px)
- ✅ Mobile (480px)

Dark mode automático según preferencia del SO.

---

## 🔐 Seguridad

- JWT tokens (no cookies)
- Passwords con bcrypt
- CORS configurado
- Tokens expiración automática
- Logout limpia datos

---

## 📊 Estructura

```
localhost:3000/login.html
├── Admin → /dashboard/
│   ├── Dashboard (KPIs + gráficos)
│   ├── Clientes (tabla + búsqueda)
│   ├── Pipeline (drag-drop)
│   ├── Auditorías (por cliente)
│   └── Reportes
└── Cliente → /portal/
    ├── Resumen (datos + score)
    ├── Auditorías (todas)
    ├── Propuesta (personalizada)
    ├── Progreso (timeline)
    └── Contacto
```

---

## 🆘 Si Algo No Funciona

### Error: "Cannot connect to API"
```bash
# 1. Verificar backend corre
lsof -i :8000

# 2. Verificar CORS
# En backend/config.py ver CORS_ORIGINS

# 3. Reiniciar backend
# Matar y volver a ejecutar python app.py
```

### Error: "Invalid token"
```bash
# 1. Limpiar localStorage
# DevTools → Console → localStorage.clear()

# 2. Reintentar login

# 3. Verificar SECRET_KEY en config.py
```

### Gráficos no aparecen
```bash
# 1. Abrir DevTools (F12)
# 2. Ver Console tab
# 3. Buscar errores
# 4. Verificar endpoint /api/dashboard/kpis retorna datos
```

---

## 🚀 Próximo Nivel

Cuando esté funcionando:
1. Agregar más clientes en BD
2. Crear auditorías para cada uno
3. Probar mobile view
4. Probar dark mode
5. Testear drag-drop pipeline

---

## 📚 Documentación Completa

- `FASE_12_STATUS.md` - Resumen completo del proyecto
- `FASE_12_SETUP.md` - Setup detallado y troubleshooting
- Este archivo - Inicio rápido

---

**¡Listo para comenzar!**

```
                   🎉
                 Backend
                 http://8000
                    ↕
              [FastAPI+JWT]
                    ↕
                 Frontend
                 http://3000
              ┌─────┴─────┐
          Admin         Cliente
          /dashboard/   /portal/
```

Ejecuta los comandos de arriba y ¡bienvenido a FASE 12! 🚀
