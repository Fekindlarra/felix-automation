# Felix Automation - MVP (Opción C)

**Sistema automatizado de ventas para Pymes e-commerce Chile**

---

## 🎯 Qué es Felix Automation

Sistema que automatiza **100% del pipeline de ventas**:
1. ✅ Auditoría gratis multi-plataforma (Web + Facebook Ads + Google Ads)
2. ✅ Lead scoring automático
3. ✅ Envío de auditorías y propuestas por email
4. ✅ Tracking del embudo de ventas en tiempo real
5. ✅ Booking de calls en 15 minutos integrado
6. ✅ Dashboard interno con métricas y forecast

---

## 🚀 Quick Start

### 1. Setup

```bash
cd /home/claude/felix-automation

# Instalar dependencias
pip install -r requirements.txt

# Crear BD e inicializar
python scripts/init_db.py

# Generar auditorías de clientes base
python scripts/seed_data.py
```

### 2. Ejecutar Agentes

```bash
# Orquestador (estado del sistema)
python orchestrator.py

# Auditar clientes
python agents/multi_platform_auditor_agent.py

# Calificar leads
python agents/lead_scorer_agent.py

# Enviar emails de auditoría
python agents/email_sender_agent.py

# Gestionar pipeline
python agents/sales_pipeline_agent.py
```

### 3. Acceder a Dashboards

- **Landing Page:** https://claude.ai/artifact/1KHBCrkWQstyZUL58ZPo8M
- **Dashboard Interno:** https://claude.ai/artifact/3edyNdyuiKv9ddPCnL3nLk

---

## 🏗️ Arquitectura

```
CLIENTES (CSV/DB)
    ↓
[MULTI-PLATFORM AUDITOR] → Audita en paralelo
    ↓ (web_audit.json, facebook_audit.json, google_audit.json)
[LEAD SCORER] → Scores y ranking
    ↓ (leads_scored.csv)
[EMAIL SENDER] → Envía reporte + CTA
    ↓ (email_log)
[LANDING PAGE] → Call booking
    ↓ (booking_data)
[SALES PIPELINE] → Tracking embudo
    ↓ (pipeline.db)
[DASHBOARD] → Métricas en tiempo real
```

---

## 📊 Pipeline de Ventas (4 Etapas)

```
PROSPECTO
  ↓ (Email: "Tu auditoría está lista")
PROPUESTA
  ↓ (Email: "Propuesta personalizada + presupuesto")
NEGOCIACIÓN
  ↓ (Email: "Ajustes finales y detalles")
CERRADO
  ✓ Cliente activo
```

---

## 🔧 Agentes Disponibles

### 1. **Multi-Platform Auditor Agent**
- Audita Web, Facebook Ads, Google Ads en paralelo
- Genera scores 0-100 por plataforma
- Input: `client_id`
- Output: `audit_results.json`

```bash
python agents/multi_platform_auditor_agent.py
```

### 2. **Lead Scorer Agent**
- Califica leads por potencial (Alto/Medio/Bajo)
- Criteria: scores auditoría + tipo negocio + tamaño
- Output: `leads_scored.csv` (con recomendaciones)

```bash
python agents/lead_scorer_agent.py
```

### 3. **Email Sender Agent**
- Envía auditorías y propuestas por SendGrid
- Templates personalizados por tipo de cliente
- Registra aperturas y clicks

```bash
python agents/email_sender_agent.py
```

### 4. **Sales Pipeline Agent**
- Mueve clientes entre etapas (Prospecto → Propuesta → Negociación → Cerrado)
- Calcula tasas de conversión
- Forecasta revenue basado en pipeline

```bash
python agents/sales_pipeline_agent.py
```

---

## 📈 Datos de Ejemplo

### Clientes en BD

| ID | Nombre | Email | Negocio | Tamaño | Score |
|----|--------|-------|---------|--------|-------|
| 1 | Raíces de Cauquenes | info@raices.cl | plants | pyme | 81 |
| 2 | TechShop Premium | admin@techshop.cl | ecommerce | pyme | 83 |
| 3 | ConsultorLabs | hello@consultorlabs.cl | services | startup | 79 |

### Scores de Leads (leads_scored.csv)

```
client_id,web_score,facebook_score,google_score,overall_score,ranking,recommendation
2,72,97,88,83,🟢 ALTO,Contacto inmediato - Alto potencial - Prioridad 1
1,72,97,88,81,🟢 ALTO,Contacto inmediato - Alto potencial - Prioridad 1
3,72,97,88,79,🟡 MEDIO,Contacto estándar - Potencial medio
```

---

## 💰 Modelo de Pricing (Configurable)

```yaml
# Por defecto: CLP/mes
pyme:
  base: $3,000
  setup_fee: $1,500
  services:
    - Auditoría completa
    - Optimización Ads (Facebook + Google)
    - Tracking + Analytics

startup:
  base: $2,000
  setup_fee: $1,000
  
empresa:
  base: $6,000
  setup_fee: $3,000
```

---

## 📧 Email Sequences

### Sequence 1: Lead Captado (Día 0)
```
Subject: Tu auditoría de presencia digital - 81/100
Body: Reporte + Score + CTA: Agendar call
```

### Sequence 2: Propuesta (Día 2)
```
Subject: Tu propuesta de mejora - TechShop Premium
Body: Desglose de servicios + presupuesto + timeline
```

### Sequence 3: Seguimiento (Día 4)
```
Subject: ¿Viste tu auditoría?
Body: Recordatorio + Datos competidores + CTA
```

### Sequence 4: Urgencia (Día 7)
```
Subject: Último dato: ROI potencial
Body: Números de mejora típica + Call CTA final
```

---

## 🔗 Integraciones Requeridas

### Producción

- **SendGrid**: Envío de emails masivo
  - Setup: `config.yaml` → `sendgrid.api_key`
  - Templates personalizables

- **Calendly/Cal.com**: Booking de calls
  - Integración en landing page
  - 15 minutos automáticos

- **Zapier**: Automación de workflows
  - Email → Create prospect in CRM
  - Call booked → Add to pipeline
  - Deal closed → Invoice automático

### Demo Mode (Actual)
- ✅ Todos los agentes funcionan
- 🎯 Modo DEMO: Sin email real
- 📊 Métricas en JSON

---

## 🎯 MVP Flujo Completo (5 Min)

```bash
# 1. Visitar landing page
curl https://claude.ai/artifact/1KHBCrkWQstyZUL58ZPo8M

# 2. Llenar "Auditoría Gratis + Agendar Call"
# → Triggerear script:

python -c "
from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from agents.lead_scorer_agent import LeadScorerAgent
from agents.email_sender_agent import EmailSenderAgent
from agents.sales_pipeline_agent import SalesPipelineAgent

orch = FelixAutomationOrchestrator()
orch.connect_database()

# Auditar
auditor = MultiPlatformAuditorAgent(orch)
auditor.audit_client(1)  # Raíces de Cauquenes

# Calificar
scorer = LeadScorerAgent(orch)
scorer.score_all_clients()

# Enviar email
emailer = EmailSenderAgent(orch)
audits = orch.get_client_audits(1)
if audits:
    emailer.send_audit_report(1, {'average_score': 81, 'platforms': ['web', 'facebook_ads', 'google_ads']})

# Agregar al pipeline
pipeline = SalesPipelineAgent(orch)
pipeline.move_to_stage(1, 'prospecto', notes='Lead from landing page')

# Ver estado
print(orch.get_system_status())

orch.close_database()
"

# 3. Revisar Dashboard
curl https://claude.ai/artifact/3edyNdyuiKv9ddPCnL3nLk
```

---

## 📋 Checklist Completado (FASE 13 ✅)

**FASE 1-8 (MVP Completa):**
- [x] Landing page con auditoría gratis
- [x] Multi-Platform Auditor Agent
- [x] Lead Scorer Agent
- [x] Email Sender Agent
- [x] Sales Pipeline Agent
- [x] Dashboard interno
- [x] Booking de call integrado
- [x] Auditoría Web (Performance, Security, Tracking, Tech)

**FASE 13 (Advanced Integrations - ✅ COMPLETADA 2026-10-05):**
- [x] Facebook Ads Live Auditor (Graph API v18.0 + OAuth 2.0)
- [x] Google Ads Live Auditor (Google Ads API + OAuth 2.0)
- [x] Email Sender Agent mejorado (SendGrid + tracking)
- [x] Report Generator Agent (PDF profesionales + branding)
- [x] Analytics Agent (Benchmarking vs industria)
- [x] Multi-Platform Orchestration
- [x] Credentials Manager (Encriptación Fernet + TTL)

---

## 🎓 Próximos Pasos (FASE 14+)

### Fase 14 (En Desarrollo)
- [ ] WebSocket Real-Time Updates
- [ ] Shopify Analytics App Integration
- [ ] Machine Learning Predictions
- [ ] Email A/B Testing Advanced
- [ ] Mobile App Dashboard
- [ ] Integración Pipedrive CRM

### Fase 15+
- [ ] White-Box Audit completo (Shopify/Jumpseller/Code SSH)
- [ ] Advanced Analytics Dashboard
- [ ] Predicciones de conversión
- [ ] Automatización de propuestas dinámicas

---

## 🆘 Troubleshooting

### Error: "No database"
```bash
python scripts/init_db.py
```

### Error: "SendGrid key not configured"
- Add to `config.yaml`:
```yaml
sendgrid:
  api_key: "SG.xxxxxxx"
  from_email: "noreply@enbuenamesa.com"
```

### Error: "Client not found"
```bash
python scripts/seed_data.py
```

---

## 📞 Support

Felipe: felipe@enbuenamesa.com

---

## 📝 Config Sample

```yaml
# config.yaml
database:
  path: "./data/felix.db"

sendgrid:
  api_key: "DEMO_MODE"
  from_email: "noreply@felix.enbuenamesa.com"

calendly:
  api_key: "DEMO_MODE"
  username: "felix"

pricing:
  pyme:
    base: 3000
    setup_fee: 1500
  startup:
    base: 2000
    setup_fee: 1000
```

---

**¡Felix está listo para escalar tu pipeline de ventas!** 🚀
