# 🚀 Felix Automation MVP - Setup & Start

**Sistema de Automatización de Ventas para Pymes e-commerce (Chile)**

---

## ✅ Estado: MVP COMPLETADO

### Componentes Entregados

#### 1. **Landing Page** (Público)
- ✅ Diseño nothing.tech moderno
- ✅ Auditoría gratis sin formularios complejos
- ✅ Call booking en 15 minutos integrado
- ✅ Lead capture optimizado
- 🔗 [Ver landing page](https://claude.ai/artifact/1KHBCrkWQstyZUL58ZPo8M)

#### 2. **Dashboard Interno** (Para Felipe)
- ✅ Métricas en tiempo real del pipeline
- ✅ Revenue forecast
- ✅ Leads de alto potencial
- ✅ Estadísticas de email
- ✅ Deals estancados (alertas)
- 🔗 [Ver dashboard](https://claude.ai/artifact/3edyNdyuiKv9ddPCnL3nLk)

#### 3. **Agentes de Automatización**

| Agente | Estado | Función |
|--------|--------|---------|
| Multi-Platform Auditor | ✅ Listo | Audita Web + Facebook + Google Ads en paralelo |
| Lead Scorer | ✅ Listo | Califica leads por potencial (Alto/Medio/Bajo) |
| Email Sender | ✅ Listo | Envía auditorías y propuestas (SendGrid ready) |
| Sales Pipeline | ✅ Listo | Gestiona embudo (Prospecto → Cerrado) |
| Proposal Generator | 📝 Pronto | Genera propuestas PDF personalizadas |
| Follow-up | 📝 Pronto | Secuencias de seguimiento automáticas |
| Funnel Management | 📝 Pronto | Dashboard dual (interno + cliente) |

#### 4. **Base de Datos**
- ✅ Tablas: Clientes, Auditorías, Leads, Propuestas, Pipeline, Emails, Funnel
- ✅ Relaciones con FK
- ✅ Logs de agentes

#### 5. **Data de Ejemplo**
- ✅ 3 clientes iniciales (Raíces, TechShop, ConsultorLabs)
- ✅ Auditorías multi-plataforma para cada uno
- ✅ Lead scores calculados
- ✅ Pipeline inicializado

---

## 🎯 Cómo Usar

### Opción 1: Setup Automático (Recomendado - 2 minutos)

```bash
cd /home/claude/felix-automation

# 1. Crear BD e inicializar tablas
python scripts/init_db.py

# 2. Seed datos de ejemplo
python scripts/seed_data.py

# 3. Ver estado del sistema
python orchestrator.py
```

### Opción 2: Setup Manual

```bash
# 1. Solo crear BD (sin datos)
python scripts/init_db.py

# 2. Agregar clientes manualmente
python -c "
from orchestrator import FelixAutomationOrchestrator, Client

orch = FelixAutomationOrchestrator()
orch.connect_database()

client = Client(
    name='Mi Empresa',
    email='contacto@empresa.cl',
    business_type='ecommerce',
    company_size='pyme'
)
client_id = orch.add_client(client)
print(f'Cliente agregado: ID {client_id}')

orch.close_database()
"
```

---

## 🔄 Flujo End-to-End (5 minutos)

### Paso 1: Cliente visita landing page
→ Completa formulario de auditoría gratis + booking

### Paso 2: Ejecutar agentes (automático en producción)
```bash
# Auditar cliente
python -c "
from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent

orch = FelixAutomationOrchestrator()
orch.connect_database()
auditor = MultiPlatformAuditorAgent(orch)
result = auditor.audit_client(1)  # Cliente ID 1
print(result)
orch.close_database()
"

# Calificar lead
python agents/lead_scorer_agent.py

# Enviar email con auditoría
python -c "
from orchestrator import FelixAutomationOrchestrator
from agents.email_sender_agent import EmailSenderAgent

orch = FelixAutomationOrchestrator()
orch.connect_database()
emailer = EmailSenderAgent(orch)
result = emailer.send_audit_report(1, {'average_score': 81, 'platforms': ['web', 'facebook_ads', 'google_ads']})
print(result)
orch.close_database()
"

# Mover a pipeline
python -c "
from orchestrator import FelixAutomationOrchestrator
from agents.sales_pipeline_agent import SalesPipelineAgent

orch = FelixAutomationOrchestrator()
orch.connect_database()
pipeline = SalesPipelineAgent(orch)
result = pipeline.move_to_stage(1, 'prospecto', notes='Lead from landing page')
print(result)
orch.close_database()
"
```

### Paso 3: Ver resultados en Dashboard
→ [Dashboard interno](https://claude.ai/artifact/3edyNdyuiKv9ddPCnL3nLk)

---

## 📊 Datos de Ejemplo

### Clientes
```
1. Raíces de Cauquenes (info@raices.cl)
   - Negocio: Plants/Retail
   - Tamaño: Pyme
   - Score: 81/100 (🟢 ALTO)

2. TechShop Premium (admin@techshop.cl)
   - Negocio: Ecommerce
   - Tamaño: Pyme
   - Score: 83/100 (🟢 ALTO)

3. ConsultorLabs (hello@consultorlabs.cl)
   - Negocio: Services/Consulting
   - Tamaño: Startup
   - Score: 79/100 (🟡 MEDIO)
```

### Scores por Plataforma
```
Web Score:      72/100  (Performance, Security, Tracking)
Facebook Ads:   97/100  (Estructura, Contenido, Targeting)
Google Ads:     88/100  (Keywords, Quality Score, Tracking)
```

---

## ⚙️ Configuración

### config.yaml (Actual - Demo Mode)
```yaml
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
  empresa:
    base: 6000
    setup_fee: 3000
```

### Para Producción (Proximas)
```yaml
# Agregar:
sendgrid:
  api_key: "SG.xxxxxxxxxxxxx"  # Get from SendGrid

calendly:
  api_key: "xxxxxxxxxxxx"  # Get from Calendly
  username: "felix"

webhooks:
  booking_received: "https://felix.enbuenamesa.com/webhooks/booking"
  email_opened: "https://felix.enbuenamesa.com/webhooks/email_opened"
```

---

## 📈 Pipeline (4 Etapas)

```
┌──────────────┐
│   PROSPECTO  │  ← Lead captado desde landing page
└──────┬───────┘
       │ (Email: Auditoría)
       ↓
┌──────────────┐
│  PROPUESTA   │  ← Propuesta enviada
└──────┬───────┘
       │ (Email: Presupuesto + detalles)
       ↓
┌──────────────────┐
│  NEGOCIACIÓN     │  ← Ajustes y términos finales
└──────┬───────────┘
       │ (Email: Confirmación de términos)
       ↓
┌──────────────┐
│   CERRADO    │  ✓ Cliente activo
└──────────────┘
```

### Tasas de Conversión (Predeterminadas)
- Prospecto → Propuesta: 50%
- Propuesta → Negociación: 40%
- Negociación → Cerrado: 70%

---

## 💰 Modelo de Revenue

### Cálculo Automático
```
Total Expected = 
  (Prospectos × Tasa₁) × Precio +
  (Propuestas × Tasa₂) × Precio +
  (Negociaciones × Tasa₃) × Precio +
  (Cerrados × 1.0) × Precio

Ejemplo con 3 clientes @ $3,000 CLP/mes:
  • 1 Prospecto × 50% = $1,500
  • 1 Propuesta × 40% = $1,200
  • 1 Negociación × 70% = $2,100
  ─────────────────────────────
  Total Esperado = $4,800 CLP
```

---

## 🔗 Integraciones Listas

### ✅ Listas en Demo
- Email sending (SendGrid - Mock mode)
- Client database (SQLite)
- Agent logging
- CSV export (leads_scored.csv)

### 📝 Pendientes de Setup Real
- **SendGrid**: Obtener API key (5 min)
- **Calendly**: Obtener API key (5 min)
- **Zapier**: Configurar workflows (10 min)
- **CRM** (Pipedrive/HubSpot): Sync (15 min)

---

## 🚨 Troubleshooting

### Error: "No such table: clients"
```bash
python scripts/init_db.py
```

### Error: "Client not found"
```bash
python scripts/seed_data.py
```

### Error: "SendGrid API key invalid"
→ Modo DEMO está activado. Para enviar emails reales, agregar a `config.yaml`:
```yaml
sendgrid:
  api_key: "SG.tu_api_key_aqui"
```

### Error: "Database locked"
→ Cerrar otros procesos que accedan a `./data/felix.db`

---

## 📞 Próximos Pasos

### Hoy (Setup)
- [ ] Ejecutar `init_db.py` + `seed_data.py`
- [ ] Revisar landing page
- [ ] Revisar dashboard

### Esta Semana (Integración)
- [ ] Setup SendGrid API real
- [ ] Setup Calendly booking
- [ ] Test end-to-end con cliente real

### Próxima Semana (Escalado)
- [ ] Proposal Generator Agent (PDF)
- [ ] Follow-up Agent (secuencias)
- [ ] CRM integration (Pipedrive)

### Mes 2 (Advanced)
- [ ] White-Box Audit (credenciales)
- [ ] Funnel Management Dashboard
- [ ] Analytics avanzado

---

## 📚 Archivos Importantes

```
/felix-automation/
├── orchestrator.py              # Hub central
├── config.yaml                  # Configuración
├── README.md                    # Este documento
├── SETUP_MVP.md                 # Setup guide
│
├── agents/
│   ├── multi_platform_auditor_agent.py
│   ├── lead_scorer_agent.py
│   ├── email_sender_agent.py
│   ├── sales_pipeline_agent.py
│   └── proposal_generator_agent.py  (próximo)
│
├── scripts/
│   ├── init_db.py               # Crear BD
│   └── seed_data.py             # Datos de ejemplo
│
└── data/
    ├── felix.db                 # Base de datos
    ├── leads_scored.csv         # Export de leads
    ├── logs/
    │   └── orchestrator.log
    └── proposals/               # PDFs generados
```

---

## ✅ Checklist de Verificación

### Setup Completado
- [ ] BD inicializada (`./data/felix.db`)
- [ ] Datos de ejemplo insertados (3 clientes)
- [ ] Landing page accesible
- [ ] Dashboard cargando datos
- [ ] Logs generándose en `./data/logs/orchestrator.log`

### Flujo Testeable
- [ ] Multi-Platform Auditor ejecutándose
- [ ] Lead Scorer generando scores
- [ ] Email Sender en modo DEMO
- [ ] Sales Pipeline tracking clientes
- [ ] CSV export funcionando

### Próximas Integraciones
- [ ] SendGrid API key configurada
- [ ] Calendly booking integrado
- [ ] Webhooks funcionando
- [ ] CRM sincronizado

---

## 🎉 ¡Listo!

**Felix Automation MVP está completamente funcional.**

Próximo paso: Enviar primer cliente a través de la landing page y ver todo el sistema en acción.

```bash
# Verificar estado actual
python orchestrator.py
```

---

**¿Preguntas o cambios?** → felipe@enbuenamesa.com

**Documentación:** 
- Landing page: https://claude.ai/artifact/1KHBCrkWQstyZUL58ZPo8M
- Dashboard: https://claude.ai/artifact/3edyNdyuiKv9ddPCnL3nLk
