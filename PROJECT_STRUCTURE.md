# 📊 ESTRUCTURA DEL PROYECTO - Felix Automation FASE 11

**Versión:** Production Ready (11.0)  
**Fecha:** 2026-10-05  
**Estado:** ✅ Completo y Verificado  

---

## 🏗️ ARQUITECTURA GLOBAL

```
Felix Automation (FASE 11 - Production Ready)
    │
    ├─ SISTEMA CORE (7 Agentes + Orquestador)
    │   ├─ Agentes de Venta (automatización end-to-end)
    │   ├─ Auditorías Multi-plataforma (Web, Facebook Ads, Google Ads)
    │   ├─ Pipeline de 4 etapas (Prospecto → Propuesta → Negociación → Cerrado)
    │   ├─ Dashboards Duales (interno + cliente)
    │   └─ White-Box Audits (Shopify, Jumpseller, Code analysis)
    │
    ├─ BACKEND API (FastAPI + PostgreSQL)
    │   ├─ REST API endpoints
    │   ├─ WebSocket real-time updates
    │   ├─ Webhook integrations
    │   └─ Authentication & Security
    │
    └─ FRONTEND (Dashboard + Portal)
        ├─ Internal Dashboard (Felipe)
        ├─ Client Portal (Clientes)
        └─ Real-time visualizations
```

---

## 📁 ESTRUCTURA DE DIRECTORIOS

### Raíz del Proyecto
```
/felix-automation/
├── README.md                          # Documentación principal
├── requirements.txt                   # Dependencias Python
├── config.yaml                        # Configuración centralizada
├── .env.example                       # Variables de entorno (template)
├── orchestrator.py                    # Orquestador principal (punto de entrada)
├── init_database.py                   # Inicialización de BD
├── setup.sh                           # Script de setup automatizado (NUEVO)
│
├── agents/                            # 7 AGENTES DE VENTA
│   ├── __init__.py
│   ├── multi_platform_auditor_agent.py       # Audita Web, FB Ads, Google Ads
│   ├── lead_scorer_agent.py                  # Califica leads (0-100)
│   ├── proposal_generator_agent.py           # Genera propuestas HTML/PDF
│   ├── email_sender_agent.py                 # Envía vía SendGrid
│   ├── followup_agent.py                     # Automatiza seguimiento
│   ├── sales_pipeline_agent.py               # Gestiona pipeline 4 etapas
│   ├── funnel_management_agent.py            # Dashboards duales
│   ├── analytics_agent.py                    # Análisis de datos
│   ├── report_generator_agent.py             # Reportes automáticos
│   └── email_queue_agent.py                  # Cola de emails
│
├── auditors/                          # MÓDULOS DE AUDITORÍA
│   ├── __init__.py
│   ├── web_auditor.py                        # Performance, Security, Tracking, Tech
│   ├── facebook_ads_auditor.py               # Estructura, Contenido, Targeting
│   └── google_ads_auditor.py                 # Estructura, Keywords, Quality Score
│
├── whitebox/                          # WHITE-BOX AUDIT (Credenciales)
│   ├── __init__.py
│   ├── credentials_manager.py                # Encriptación Fernet + TTL
│   ├── shopify_auditor.py                    # Auditoría profunda Shopify
│   ├── jumpseller_auditor.py                 # Auditoría profunda Jumpseller
│   └── code_auditor.py                       # Análisis de código (SSH/FTP)
│
├── backend/                           # BACKEND API (FastAPI)
│   ├── __init__.py
│   ├── app.py                                # Aplicación principal
│   ├── config.py                             # Configuración backend
│   ├── auth.py                               # Autenticación
│   ├── events.py                             # Event handling
│   ├── notifications.py                      # Sistema de notificaciones
│   ├── websocket_manager.py                  # WebSocket connections
│   ├── report_scheduler.py                   # Scheduling de reportes
│   │
│   └── routes/                               # API Endpoints
│       ├── __init__.py
│       ├── api_enhancement_routes.py         # Rutas API extendidas
│       ├── scheduler_routes.py               # Scheduling endpoints
│       ├── websocket_routes.py               # WebSocket handlers
│       └── whitebox_routes.py                # White-box audit endpoints
│
├── frontend/                          # DASHBOARDS Y PORTAL
│   ├── dashboard/                            # Dashboard interno (Felipe)
│   │   ├── index.html
│   │   ├── css/
│   │   ├── js/
│   │   └── assets/
│   │
│   └── portal/                               # Portal cliente
│       ├── index.html
│       ├── css/
│       ├── js/
│       └── assets/
│
├── core/                              # CÓDIGO BASE EXISTENTE
│   ├── __init__.py
│   ├── audit_kit_cloud_ready.py              # Kit de auditoría
│   ├── audit_cloud_enterprise.py             # Sistema 3 modos
│   ├── generate_audit_reports_pdf.py         # Generador reportes PDF
│   └── audit_kit_business_friendly.py        # Traductor negocio
│
├── analytics/                         # MÓDULO DE ANALYTICS
│   ├── __init__.py
│   └── analytics_engine.py                   # Motor de análisis
│
├── data/                              # ALMACENAMIENTO DE DATOS
│   ├── pipeline.db                           # Base de datos SQLite local
│   ├── audits/                               # JSONs de auditorías
│   │   ├── web/
│   │   ├── facebook_ads/
│   │   └── google_ads/
│   ├── proposals/                            # Propuestas generadas
│   │   ├── html/
│   │   └── pdf/
│   ├── pipeline/                             # Estado del embudo
│   ├── dashboards/                           # Dashboards HTML
│   ├── logs/                                 # Logs de aplicación
│   │   ├── sistema.log
│   │   ├── agents.log
│   │   ├── auditors.log
│   │   ├── email.log
│   │   ├── pipeline.log
│   │   └── whitebox.log
│   └── cache/                                # Cache temporal
│
├── reports/                           # REPORTES GENERADOS
│   ├── weekly/
│   └── monthly/
│
├── scripts/                           # SCRIPTS DE UTILIDAD
│   ├── __init__.py
│   ├── init_db.py                            # Inicializa base de datos
│   ├── cleanup.py                            # Limpieza de datos
│   └── monitoring.py                         # Monitoreo básico
│
├── dashboards/                        # ARCHIVOS HTML DE DASHBOARDS
│   ├── internal_dashboard.html
│   └── client_dashboard.html
│
├── test*.py                           # TESTS (end-to-end)
│   ├── test_end_to_end_complete.py
│   ├── test_fase*.py
│   └── [otros tests específicos]
│
└── DOCUMENTACIÓN/                     # Documentación de Fases
    ├── GUIA_RAPIDA_DESPLIEGUE.md      # ← PRINCIPAL (deployment)
    ├── DEPLOYMENT_GUIDE.md
    ├── FASE_11_QUICK_REFERENCE.md
    ├── FASE_11_WHITE_BOX_AUDITS.md
    ├── PRODUCTION_READY_SUMMARY.md
    └── [docs de fases anteriores]
```

---

## 🎯 COMPONENTES CLAVE

### 1. **ORQUESTADOR PRINCIPAL** (`orchestrator.py`)
- Punto de entrada único para toda la automatización
- Gestiona instancias de 7 agentes
- Maneja base de datos y estado del pipeline
- Coordina ejecución paralela
- **Interfaz:**
  ```python
  orchestrator = FelixAutomationOrchestrator()
  orchestrator.run_full_pipeline(client_list)
  ```

### 2. **SIETE AGENTES DE VENTA**

| Agente | Responsabilidad | Output |
|--------|-----------------|--------|
| Multi-Platform Auditor | Audita web + FB Ads + Google Ads | `*_audit.json` |
| Lead Scorer | Califica por potencial (0-100) | `leads_scored.csv` |
| Proposal Generator | Crea propuestas personalizadas | `proposal_*.pdf` |
| Email Sender | Envía vía SendGrid | `email_log.json` |
| Follow-up | Secuencia de seguimientos | `followup_log.json` |
| Sales Pipeline | Gestiona 4 etapas | `pipeline.db` |
| Funnel Management | Dashboards internos + cliente | `*.html` |

### 3. **AUDITORÍAS MULTI-PLATAFORMA**

**Web Audit** (existente):
- Performance: PageSpeed, tamaño, Load Time
- Security: HTTPS, headers, SSL
- Tracking: Google Analytics, GTM, pixels
- Technology: Stack detectado

**Facebook Ads Audit** (NUEVO):
- Estructura: Campañas, AdSets, Ads
- Contenido: Copy, imágenes, CTA
- Targeting: Audiencias, placements, horarios
- Tracking: Pixel, conversion tracking

**Google Ads Audit** (NUEVO):
- Estructura: Campañas, AdGroups, Keywords
- Keywords: Match types, relevancia
- Quality Score: CTR, landing page quality
- Tracking: Conversion tags, UTMs

### 4. **WHITE-BOX AUDITS** (Credenciales)

```
Shopify:
  ├─ Configuración tienda
  ├─ Analytics y performance
  ├─ Security settings
  ├─ Apps instaladas
  └─ SEO configuration

Jumpseller:
  ├─ Configuración plataforma
  ├─ Gestión de productos
  ├─ Transacciones y pagos
  ├─ Integraciones
  └─ Security

Code Analysis:
  ├─ Arquitectura (SSH/FTP)
  ├─ Vulnerabilidades
  ├─ Performance
  ├─ Best practices
  └─ Dependencias
```

### 5. **PIPELINE DE 4 ETAPAS**

```
PROSPECTO
    ↓ [Email de presentación]
PROPUESTA
    ↓ [Follow-ups día 2, 4, 7]
NEGOCIACIÓN
    ↓ [Acuerdo de servicios]
CERRADO
    ├─ Contrato firmado ✅
    └─ Contrato rechazado ❌
```

**Métricas:**
- Tasa de conversión por etapa
- Tiempo promedio por etapa
- Forecast de ingresos
- Performance de agentes

### 6. **DASHBOARDS DUALES**

**Internal Dashboard (Felipe):**
- Métricas completas del pipeline
- Conversiones por etapa
- Revenue forecast
- Performance de agentes
- Scoring distribution
- Health check del sistema

**Client Dashboard (por cliente):**
- Progreso en el embudo
- Resumen de auditorías
- Estado de propuesta
- Timeline de implementación
- (No ve datos de otros clientes)

### 7. **BACKEND API** (FastAPI)

**Endpoints Principales:**
```
POST   /api/clients              # Crear cliente
GET    /api/clients              # Listar clientes
GET    /api/clients/{id}         # Detalles cliente
POST   /api/audits               # Iniciar auditoría
GET    /api/pipeline/{id}        # Estado en pipeline
POST   /api/proposals            # Generar propuesta
GET    /api/dashboard/internal   # Dashboard Felipe
GET    /api/dashboard/client/{id}# Dashboard cliente
WS     /ws/updates               # WebSocket real-time
```

**Características:**
- Autenticación JWT
- WebSocket para updates en tiempo real
- Webhooks para integraciones
- CORS configurado
- Error handling robusto

---

## 📊 FLUJO DE DATOS (End-to-End)

```
1. ENTRADA
   Clientes (CSV) → Orquestador

2. AUDITORÍA (Paralela)
   Multi-Platform Auditor
   ├─ Web Audit → web_audit.json
   ├─ Facebook Ads → fb_audit.json
   └─ Google Ads → ga_audit.json

3. SCORING
   Lead Scorer Agent
   ├─ Combina 3 auditorías
   ├─ Calcula score 0-100
   └─ Genera leads_scored.csv

4. PROPUESTA
   Proposal Generator
   ├─ Lee auditoría + score
   ├─ Genera HTML personalizado
   └─ Exporta PDF

5. EMAIL
   Email Sender Agent
   ├─ Envía propuesta vía SendGrid
   ├─ Registra open rates
   └─ email_log.json

6. PIPELINE
   Sales Pipeline Agent
   ├─ Registra estado (Prospecto)
   ├─ Actualiza BD
   └─ pipeline.db

7. SEGUIMIENTO
   Follow-up Agent
   ├─ Día 2: Email 1
   ├─ Día 4: Email 2
   ├─ Día 7: Email 3
   └─ followup_log.json

8. DASHBOARDS
   Funnel Management Agent
   ├─ Actualiza internal_dashboard.html
   ├─ Actualiza client_dashboard.html
   └─ Envía WebSocket updates

9. REPORTES
   Report Generator Agent
   ├─ Semanal: resumen conversiones
   ├─ Mensual: forecast
   └─ PDF + email Felipe
```

---

## 🔒 SEGURIDAD

### Encriptación
- **Credenciales:** Fernet (AES-128-CBC)
- **Master Key:** Variable de entorno `WHITEBOX_MASTER_KEY`
- **Almacenamiento:** TTL-based (1 hora por defecto)

### Autenticación
- **API:** JWT tokens
- **Database:** PostgreSQL con password fuerte
- **SSH:** Ed25519 keys (servidor)

### Permisos
- **.env:** chmod 600 (read/write owner only)
- **Database:** User-specific permissions
- **Logs:** No logging de credenciales sin encriptar

### Limpieza
- Credentials TTL: 3600 segundos
- Logs retention: 90 días
- Cache retention: 30 días

---

## 📦 DEPENDENCIAS PRINCIPALES

```yaml
Core:
  - python-dotenv (config)
  - PyYAML (configuration)
  - requests (HTTP)

Database:
  - PostgreSQL (production)
  - sqlite3 (development)

Email:
  - sendgrid (SendGrid integration)
  - python-dateutil (date handling)

Scheduling:
  - APScheduler (task scheduling)

Data Processing:
  - pandas (data analysis)
  - numpy (numerical computing)

PDF/Reports:
  - WeasyPrint (PDF generation)
  - reportlab (PDF alternative)

Scraping/Audits:
  - beautifulsoup4 (HTML parsing)
  - selenium (browser automation)
  - requests-html (web scraping)

APIs:
  - shopify (Shopify SDK)

Security:
  - cryptography (encryption)
  - paramiko (SSH)
  - pysftp (SFTP)

Web:
  - flask (alternative API)
  - flask-cors (CORS)

Utilities:
  - python-slugify (slug generation)
  - tqdm (progress bars)
  - python-json-logger (structured logging)

Auth:
  - PyJWT (JWT tokens)
```

---

## 🧪 TESTING

```
tests/
├── test_end_to_end_complete.py    # Pipeline completo
├── test_fase13_day4_integration.py # Integración multi-plataforma
├── test_fase5.py                   # Auditorías
├── test_analytics_scheduler.py      # Scheduling
└── [otros tests específicos]

Ejecutar: python -m pytest tests/
```

---

## 📈 ESTADOS DE DESARROLLO

| Fase | Estado | Descripción |
|------|--------|-------------|
| Fase 1-4 | ✅ Completo | Auditorías base |
| Fase 5 | ✅ Completo | Lead scoring |
| Fase 6 | ✅ Completo | White-box Shopify |
| Fase 7 | ✅ Completo | Facebook Ads audit |
| Fase 8 | ✅ Completo | Google Ads audit |
| Fase 9 | ✅ Completo | White-box integrado |
| Fase 10 | ✅ Completo | Pipeline optimizado |
| Fase 11 | ✅ **ACTUAL** | Production-ready |
| Fase 12 | 📅 Planned | API REST avanzada |
| Fase 13 | 📅 Planned | IA/ML predictions |

---

## 🚀 DESPLIEGUE

**Checklist pre-deployment:**
- [ ] Todos los agentes testeados
- [ ] Base de datos migrada a PostgreSQL
- [ ] Variables de entorno configuradas
- [ ] SSL certificate instalado
- [ ] Monitoreo configurado
- [ ] Backups definidos
- [ ] Runbook de disasters prepared

**Stack recomendado:**
- **Servidor:** Ubuntu 20.04+ (DigitalOcean, AWS, etc.)
- **Python:** 3.10+
- **Database:** PostgreSQL 13+
- **Server:** Gunicorn + Nginx
- **Monitoring:** Prometheus + Grafana (o similar)
- **Logging:** ELK Stack o CloudWatch

---

## 📞 SOPORTE

**Documentación Completa:**
- `GUIA_RAPIDA_DESPLIEGUE.md` ← Empezar aquí
- `DEPLOYMENT_GUIDE.md` → Detalles completos
- `MONITORING_PLAN.md` ← Nuevo (en preparación)
- `setup.sh` ← Script automatizado (en preparación)

**Contacto:** Felipe (@enbuenamesa.com)

---

**Última actualización:** 2026-10-05  
**Versión:** 11.0 (Production Ready)
