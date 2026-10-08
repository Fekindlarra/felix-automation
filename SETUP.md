# FELIX Audit Report System — Setup & Deployment

## 📋 Contenido

- **generate_audit_reports.py** — Motor de generación de PDFs con branding Nothing Aesthetic
- **api_server.py** — API REST Flask para gestión de reportes
- **dashboard.html** — Interfaz web para generación y gestión
- **requirements.txt** — Dependencias Python

## 🚀 Quick Start

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno (opcional)
```bash
export SENDER_EMAIL="felix@enbuenamesa.com"
export SENDER_PASSWORD="tu_password_gmail"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
```

### 3. Iniciar API Server
```bash
python api_server.py
```

Server escucha en `http://localhost:5000`

### 4. Abrir Dashboard
```bash
# Opción 1: Abrir en navegador
open dashboard.html

# Opción 2: Usar servidor HTTP local
python -m http.server 8000
# Luego ir a http://localhost:8000/dashboard.html
```

---

## 📡 API Endpoints

### 1. **Generar Reporte Individual**
```bash
POST /api/reports/generate
Content-Type: application/json

{
  "client_name": "Tienda Online ABC",
  "client_email": "abc@example.com",
  "score": 81,
  "processes": 47,
  "apis": 12,
  "hours": 4.2,
  "platforms": "Web • Google Ads • Facebook Ads",
  "send_email": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Reporte generado para Tienda Online ABC",
  "report_id": 1,
  "filename": "reporte_Tienda_Online_ABC_20261008_152000.pdf",
  "email_sent": false,
  "download_url": "/api/reports/download/1"
}
```

### 2. **Procesar Múltiples Reportes (Batch)**
```bash
POST /api/reports/batch
Content-Type: application/json

{
  "reports": [
    {"client_name": "Cliente 1", "client_email": "email1@example.com", "score": 81, "processes": 47, "apis": 12, "hours": 4.2},
    {"client_name": "Cliente 2", "client_email": "email2@example.com", "score": 72, "processes": 23, "apis": 8, "hours": 3.1}
  ],
  "send_emails": false
}
```

### 3. **Listar Reportes**
```bash
GET /api/reports

Response:
{
  "status": "success",
  "total": 5,
  "reports": [...]
}
```

### 4. **Obtener Detalles de Reporte**
```bash
GET /api/reports/{id}
```

### 5. **Descargar Reporte PDF**
```bash
GET /api/reports/download/{id}
```

---

## 💻 Uso desde CLI

### Generar un único reporte
```bash
python generate_audit_reports.py \
  --client "Tienda Online ABC" \
  --email "abc@example.com" \
  --score 81 \
  --processes 47 \
  --apis 12 \
  --hours 4.2 \
  --output "mi_reporte.pdf"
```

### Usar API desde cURL
```bash
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Mi Cliente",
    "client_email": "cliente@example.com",
    "score": 85,
    "processes": 30,
    "apis": 10,
    "hours": 3.5,
    "send_email": false
  }'
```

---

## 📧 Email Configuration

Para enviar reportes automáticamente por email:

### Con Gmail
1. Habilitar "Contraseñas de aplicación" en tu cuenta Google
2. Configurar variables de entorno:
```bash
export SENDER_EMAIL="tu_email@gmail.com"
export SENDER_PASSWORD="tu_app_password"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
```

### Con otro proveedor SMTP
Reemplazar SMTP_SERVER y SMTP_PORT según tu proveedor.

---

## 🔄 Batch Processing

### JSON para procesar 3 clientes
```json
[
  {
    "client_name": "Tienda Online ABC",
    "client_email": "abc@example.com",
    "score": 81,
    "processes": 47,
    "apis": 12,
    "hours": 4.2,
    "platforms": "Web • Google Ads • Facebook Ads • Shopify"
  },
  {
    "client_name": "SaaS Tech Startup",
    "client_email": "cto@tech.io",
    "score": 72,
    "processes": 23,
    "apis": 8,
    "hours": 3.1,
    "platforms": "Web • GA4 • Meta Ads"
  },
  {
    "client_name": "Agencia de Marketing",
    "client_email": "ops@agencia.mx",
    "score": 91,
    "processes": 67,
    "apis": 18,
    "hours": 6.5,
    "platforms": "Web • Google Ads • Facebook Ads • Instagram • GA4 • GSC"
  }
]
```

---

## 📂 Estructura de Archivos

```
/home/claude/felix-automation/
├── generate_audit_reports.py      # Motor de generación
├── api_server.py                   # API REST Flask
├── dashboard.html                  # Interfaz web
├── requirements.txt                # Dependencias
├── SETUP.md                        # Este archivo
├── reports/                        # Carpeta de reportes generados
│   ├── reporte_*.pdf              # Archivos PDF
│   └── reports_registry.json      # Base de datos de reportes
└── reports_registry.json          # Registro de reportes
```

---

## 🔧 Troubleshooting

### Error: ModuleNotFoundError: No module named 'flask'
```bash
pip install -r requirements.txt
```

### Error: Port 5000 already in use
```bash
# Usar otro puerto
python -c "from api_server import app; app.run(port=5001)"
```

### Error: Email not sending
1. Verificar SMTP_SERVER y SMTP_PORT
2. Verificar credenciales en variables de entorno
3. Revisar logs del servidor API

### PDFs se generan pero no se ven bien
- Verificar que WeasyPrint esté instalado: `pip install weasyprint`
- Revisar que las fuentes IBM Plex carguen desde Google Fonts

---

## 📊 Monitoreo

El API genera un archivo `reports_registry.json` que registra todos los reportes:

```json
{
  "reports": [
    {
      "id": 1,
      "client_name": "Tienda Online ABC",
      "client_email": "abc@example.com",
      "score": 81,
      "created_at": "2026-10-08T12:00:00",
      "filename": "reporte_...",
      "status": "generated",
      "email_sent": false
    }
  ]
}
```

---

## 🚀 Próximos Pasos

1. **Integración con Dashboard de Auditoría** — Conectar con el dashboard interactivo FELIX
2. **Webhooks** — Generar reportes automáticamente al completar una auditoría
3. **Base de datos** — Migrar de JSON a PostgreSQL/Supabase
4. **Autenticación** — Agregar API keys para acceso seguro
5. **White-labeling** — Customizar branding por cliente

---

**Versión:** 1.0  
**Última actualización:** 2026-10-08  
**Mantenedor:** FELIX Team
