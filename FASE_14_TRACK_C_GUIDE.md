# 🚨 FASE 14 Week 2 - Track C: Alert Routing
## Guía de Implementación - Slack, PagerDuty, Email, Webhooks

**Estado:** ✅ Implementación Inicial Completa  
**Timeline:** 3-4 días  
**Complejidad:** Media-Alta  
**Effort:** 40-50 horas

---

## 📋 Lo que se Implementa

### Track C incluye:

1. **AlertManager Configuration** (`alertmanager.yml`)
   - Receiver definitions (Slack, PagerDuty, Email)
   - Routing rules by severity/component
   - Alert grouping & deduplication
   - Inhibition rules (suppress redundant alerts)

2. **Backend API Routes** (`alert_routing_routes.py`)
   - Receiver management (CRUD)
   - Route management (CRUD)
   - Active/Resolved alerts querying
   - Alert statistics & analytics
   - Webhook handlers (Slack, PagerDuty, Custom)

3. **FastAPI Integration**
   - New `/api/alerts/*` endpoints
   - Webhook endpoints for integrations
   - Alert status queries

4. **Integration Setup**
   - Slack webhook configuration
   - PagerDuty service keys
   - SendGrid email setup
   - Custom webhook handlers

---

## 🎯 Objetivo Final

```
Prometheus Alert → AlertManager → Routes & Groups
                                   ├→ Slack (channel)
                                   ├→ PagerDuty (incident)
                                   ├→ Email (notification)
                                   └→ Custom Webhooks
```

---

## 📝 Archivos Generados - Track C

```
/home/claude/felix-automation/
├── alertmanager.yml                    [NEW, ~2 KB]
│   ├── Global config (SMTP, Slack URL)
│   ├── Routes (7 main routes)
│   ├── Receivers (7 receivers)
│   ├── Inhibition rules (3 rules)
│   └── Templates (Slack, PagerDuty, Email)
│
├── backend/routes/
│   └── alert_routing_routes.py         [NEW, ~6 KB]
│       ├── Models (SlackConfig, PagerDutyConfig, etc.)
│       ├── Receiver endpoints (GET, POST, PUT, DELETE)
│       ├── Route endpoints (GET, POST)
│       ├── Active alerts query
│       ├── Webhook handlers (AlertManager, Slack, PagerDuty)
│       └── Statistics endpoint
│
├── backend/app.py                      [MODIFIED]
│   ├── Import: alert_routing_router (line 50)
│   └── Register: app.include_router() (line 113)
│
├── TRACK_C_CONFIG_EXAMPLE.env          [NEW]
│   ├── Slack webhook URLs
│   ├── PagerDuty service keys
│   ├── SendGrid API key
│   ├── Email configuration
│   └── Setup instructions
│
└── FASE_14_TRACK_C_GUIDE.md           [Este archivo]
    └── Complete implementation guide
```

**Total archivos:** 5  
**Total líneas código:** 500+ (alertmanager.yml + routes)  
**Backend endpoints:** 11 new endpoints  
**Integrations:** 3 (Slack, PagerDuty, Email)

---

## 🚀 Implementación - Paso a Paso

### PASO 1: Slack Integration (1-2 días)

#### 1.1 Crear Slack Workspace y Canales

```bash
# En Slack:
1. Create workspace: "Felix Automation Monitoring"
2. Create channels:
   - #felix-alerts-critical     (for critical alerts)
   - #felix-alerts-warnings     (for warnings)
   - #felix-alerts-websocket    (for WebSocket component)
   - #felix-alerts-api          (for API component)
   - #felix-alerts-cache        (for Cache component)
   - #felix-alerts-system       (for System alerts)
```

#### 1.2 Configurar Webhook de Slack

```bash
# 1. Go to: https://api.slack.com/apps
# 2. Click "Create New App" → "From scratch"
# 3. Name: "Felix Alert Manager"
# 4. Workspace: Select your workspace
# 5. Click "Create App"

# 6. Left sidebar → "Incoming Webhooks"
# 7. Toggle "Activate Incoming Webhooks" to ON

# 8. Click "Add New Webhook to Workspace"
# 9. Select channel: #felix-alerts-critical
# 10. Click "Allow"

# 11. Copy webhook URL (format: https://hooks.slack.com/services/...)
# 12. Repeat steps 8-11 for each channel (7 total)
```

#### 1.3 Configurar alertmanager.yml

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

receivers:
  - name: 'critical-team'
    slack_configs:
      - channel: '#felix-alerts-critical'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        # ... (ver alertmanager.yml completo)
```

#### 1.4 Actualizar Docker Compose

```yaml
# docker-compose.prometheus-grafana.yml
alertmanager:
  volumes:
    - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro  # ← ADD THIS
    - alertmanager_data:/alertmanager

# Restart AlertManager:
docker-compose -f docker-compose.prometheus-grafana.yml restart alertmanager
```

#### 1.5 Testear Slack Integration

```bash
# Trigger a test alert en Prometheus:
# 1. Ir a http://localhost:9090
# 2. Alerts tab
# 3. Esperar a que una alerta se dispare
# 4. Verificar que aparece en #felix-alerts-critical en Slack

# O crear manualmente un webhook test:
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-type: application/json' \
  -d '{
    "text": "Test alert from Felix",
    "color": "danger"
  }'
```

---

### PASO 2: PagerDuty Integration (1 día)

#### 2.1 Setup PagerDuty Account

```bash
# 1. Ir a: https://www.pagerduty.com
# 2. Sign up o login a existing account
# 3. Go to Dashboard
```

#### 2.2 Crear Service para Felix

```bash
# 1. Services → "New Service"
# 2. Name: "Felix Automation Monitoring"
# 3. Escalation Policy: Select existing or create new
# 4. Alert Creation: "Create incidents for every alert"
# 5. Create

# 6. Go to service → Integrations tab
# 7. Add Integration → Search "Prometheus"
# 8. Select "Prometheus"
# 9. Copy Integration Key (formato: PXXXXXX...)
```

#### 2.3 Configurar alertmanager.yml

```yaml
pagerduty_configs:
  - service_key: 'YOUR_INTEGRATION_KEY'
    description: '{{ .GroupLabels.alertname }}'
```

#### 2.4 Testear PagerDuty

```bash
# 1. Trigger an alert in Prometheus
# 2. Go to PagerDuty dashboard
# 3. Should see incident created
# 4. Acknowledge incident to silence alert
```

---

### PASO 3: SendGrid Email Integration (1 día)

#### 3.1 Setup SendGrid Account

```bash
# 1. Go to: https://sendgrid.com
# 2. Sign up or login
# 3. Go to Settings → API Keys
# 4. Create API Key (give it full access)
# 5. Copy key (format: SG.xxxxxxxxxxxx...)
```

#### 3.2 Verify Sender Email

```bash
# 1. Go to Settings → Sender Authentication
# 2. Add sender email: alerts@enbuenamesa.com
# 3. Click verify link in email
```

#### 3.3 Configurar alertmanager.yml

```yaml
global:
  smtp_smarthost: 'smtp.sendgrid.net:587'
  smtp_auth_username: 'apikey'
  smtp_auth_password: 'SG.YOUR_API_KEY'
  smtp_from: 'alerts@enbuenamesa.com'

receivers:
  - name: 'critical-team'
    email_configs:
      - to: 'critical-alerts@enbuenamesa.com'
```

#### 3.4 Testear Email

```bash
# Trigger alert y verificar email recibido
# Check spam folder if not in inbox
```

---

### PASO 4: Custom Webhook Handlers (1 día)

#### 4.1 Backend Routes Disponibles

```python
# POST /api/alerts/webhooks/alertmanager
# Handle incoming AlertManager webhooks

# POST /api/alerts/webhooks/slack
# Handle Slack action buttons (acknowledge, etc.)

# POST /api/alerts/webhooks/pagerduty
# Handle PagerDuty incident updates

# GET /api/alerts/active
# Get currently active alerts

# GET /api/alerts/stats/summary
# Get alert statistics
```

#### 4.2 Implementar Custom Handlers

Ver `alert_routing_routes.py` para ejemplos de:
- Parsing webhook payloads
- Routing based on alert attributes
- Database logging
- Custom business logic

---

## ⚙️ Configuración Final

### alertmanager.yml - Estructura

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: '...'
  smtp_smarthost: 'smtp.sendgrid.net:587'
  smtp_auth_username: 'apikey'
  smtp_auth_password: '...'

templates: [...]  # Email templates

route:
  receiver: 'default-receiver'
  group_by: ['alertname', 'severity', 'service']
  
  routes:
    - match: {severity: critical}
      receiver: 'critical-team'    # Slack + PagerDuty + Email
    
    - match: {component: websocket}
      receiver: 'websocket-team'   # Slack + PagerDuty
    
    - match: {severity: warning}
      receiver: 'warning-receiver' # Slack only

receivers:
  - name: 'critical-team'
    slack_configs: [...]           # #felix-alerts-critical
    pagerduty_configs: [...]       # Create incident
    email_configs: [...]           # Send email

  - name: 'warning-receiver'
    slack_configs: [...]           # #felix-alerts-warnings

inhibit_rules:
  # Suppress WARNING when CRITICAL is active
  - source_match: {severity: critical}
    target_match: {severity: warning}
    equal: ['alertname', 'service']
```

### Backend Routes - API Endpoints

```
GET  /api/alerts/receivers         - List all receivers
POST /api/alerts/receivers         - Create new receiver
PUT  /api/alerts/receivers/{name}  - Update receiver
DEL  /api/alerts/receivers/{name}  - Delete receiver

GET  /api/alerts/routes            - List routing rules
POST /api/alerts/routes            - Create routing rule

GET  /api/alerts/active            - Get active alerts
GET  /api/alerts/resolved          - Get resolved alerts

POST /api/alerts/webhooks/alertmanager  - AlertManager webhook
POST /api/alerts/webhooks/slack         - Slack webhook
POST /api/alerts/webhooks/pagerduty     - PagerDuty webhook

GET  /api/alerts/stats/summary     - Alert statistics
```

---

## 🧪 Testing Checklist

### Pre-Deployment

- [ ] alertmanager.yml validates (YAML syntax)
- [ ] Slack webhooks respond (curl test)
- [ ] PagerDuty service key valid
- [ ] SendGrid API key valid
- [ ] Email sender verified in SendGrid
- [ ] Backend routes import without errors
- [ ] Docker Compose mounts alertmanager.yml
- [ ] AlertManager container starts successfully

### Post-Deployment

- [ ] Prometheus alerts trigger normally
- [ ] AlertManager receives alerts (check logs)
- [ ] Slack notification appears in correct channel
- [ ] PagerDuty incident created
- [ ] Email received
- [ ] Multiple critical alerts group correctly
- [ ] Alert deduplication works
- [ ] Warning suppressed when critical active
- [ ] Resolve notification sent to all channels
- [ ] Alert re-sent after 12h if not resolved

### Integration Testing

- [ ] API GET /api/alerts/active returns current alerts
- [ ] API POST /api/alerts/receivers creates new receiver
- [ ] Webhook /api/alerts/webhooks/alertmanager accepts payload
- [ ] API GET /api/alerts/stats/summary calculates correctly

---

## 🔍 Troubleshooting

### Slack Alerts No Llegan

```bash
# Check AlertManager logs
docker logs felix-alertmanager

# Verify webhook URL
curl -X POST YOUR_WEBHOOK_URL -d '{}'

# Check AlertManager config loaded
curl http://localhost:9093/api/v1/status

# Test route match
# In Prometheus, manually create an alert that matches your rules
```

### PagerDuty No Crea Incidents

```bash
# Verify service key is correct
grep "service_key" alertmanager.yml

# Check PagerDuty service integration enabled
# Go to PagerDuty → Service → Integrations tab

# Test API directly (if needed)
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key": "YOUR_SERVICE_KEY",
    "event_action": "trigger",
    "payload": {
      "summary": "Test alert",
      "severity": "critical",
      "source": "Felix"
    }
  }'
```

### Email No Se Envía

```bash
# Verify SendGrid API key
echo $SENDGRID_API_KEY

# Check sender verified in SendGrid
# Go to Settings → Sender Authentication

# Test SMTP connection
telnet smtp.sendgrid.net 587

# Check AlertManager logs for SMTP errors
docker logs felix-alertmanager | grep -i "smtp\|email"
```

### Alertas No Se Agrupan

```bash
# Verify grouping in alertmanager.yml
# Check group_by matches alert labels

# Verify alert has required labels
# In Prometheus: /api/v1/targets → Check labels

# Test grouping manually
curl http://localhost:9093/api/v1/alerts
# Should see alerts grouped by group_labels
```

---

## 📊 Monitoreo de Track C

### Métricas Clave

| Métrica | Objetivo | Validación |
|---------|----------|-----------|
| Slack latency | <5s | Alert appears in <5 seconds |
| PagerDuty latency | <10s | Incident created in <10s |
| Email latency | <30s | Email received |
| Alert grouping | 90%+ | Alerts grouped by labels |
| Deduplication rate | >80% | Fewer duplicates sent |
| Resolve accuracy | 100% | Resolved alerts acknowledged |

---

## 🔐 Seguridad - Best Practices

1. **Never commit secrets to Git**
   ```bash
   # .gitignore
   .env
   alertmanager.yml  # If contains real keys
   ```

2. **Use environment variables for sensitive data**
   ```bash
   export SLACK_WEBHOOK_URL='https://...'
   export SENDGRID_API_KEY='SG...'
   ```

3. **Rotate API keys regularly**
   - PagerDuty: Monthly
   - SendGrid: Every 90 days
   - Slack: When suspecting compromise

4. **Use Secret Management in Production**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets
   - Docker Secrets

5. **Validate webhook payloads**
   - Check HMAC signatures (Slack)
   - Validate routing keys (PagerDuty)
   - Rate limit webhook handlers

---

## 📋 Próximos Pasos

### Después de Track C:

**Track D - E2E Testing** (Semana 3-4)
- [ ] End-to-end test suite for alert flows
- [ ] Performance regression testing
- [ ] Alert accuracy validation

**Track E - Mobile Optimization** (Semana 4-5)
- [ ] Responsive dashboard
- [ ] PWA support
- [ ] Offline caching

**Track F - Advanced Features** (Semana 6+)
- [ ] Alert dashboard in admin panel
- [ ] Alert history & analytics
- [ ] Custom alert templates
- [ ] On-call schedule integration

---

## 📚 Referencia Rápida

**Archivos importantes:**
- `alertmanager.yml` - Main configuration
- `backend/routes/alert_routing_routes.py` - Backend API
- `TRACK_C_CONFIG_EXAMPLE.env` - Example env vars

**URLs de servicios:**
- AlertManager: http://localhost:9093
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

**Logs útiles:**
```bash
docker logs felix-alertmanager
docker logs felix-prometheus
# O montar logs con docker-compose logs -f
```

---

**Status Track C:** ✅ LISTO PARA IMPLEMENTACIÓN  
**Estimated Duration:** 3-4 días  
**Difficulty:** Media  
**Impact:** Alto (Notificaciones en tiempo real)

*Last Updated: 2026-10-06*
