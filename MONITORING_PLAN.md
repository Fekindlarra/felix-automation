# 📊 PLAN DE MONITOREO Y ALERTAS - Felix Automation

**Versión:** FASE 11 Production Ready  
**Fecha:** 2026-10-05  
**Objetivo:** Monitoreo 24/7 de Felix Automation en producción

---

## 🎯 ESTRATEGIA GENERAL

```
Métricas              Logs                WebSocket            Dashboards
     ↓                 ↓                      ↓                    ↓
[Prometheus]      [Loki/ELK]          [Real-time]          [Grafana]
     ↓                 ↓                      ↓                    ↓
Alertas ← ← ← [Alertmanager] → → → [Email/Slack/SMS]
```

### Tres Niveles de Monitoreo

1. **Básico (Recomendado para empezar)**
   - Uptime Kuma + Email alerts
   - Logs locales rotados
   - Healthchecks cada 5 min
   
2. **Intermediario**
   - Prometheus + Grafana
   - Loki para logs
   - AlertManager
   
3. **Avanzado**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Prometheus + Thanos (long-term storage)
   - Custom dashboards
   - APM (Application Performance Monitoring)

---

## 📈 MÉTRICAS CLAVE

### Aplicación

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Response Time P95 | > 2000ms | Alert |
| Error Rate | > 1% | Alert CRÍTICO |
| Request/sec | > 1000 | Monitor |
| Active Connections | > 100 | Monitor |
| Task Queue Size | > 1000 | Alert |
| Failed Agents | > 0 | Alert CRÍTICO |

### Base de Datos

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Connection Pool Usage | > 80% | Alert |
| Query Time P95 | > 5000ms | Alert |
| Slow Queries | > 10/min | Alert |
| Replication Lag | > 10s | Alert CRÍTICO |
| Disk Usage | > 80% | Alert |
| Lock Contention | > 5% | Monitor |

### Sistema

| Métrica | Umbral | Acción |
|---------|--------|--------|
| CPU Usage | > 80% | Alert |
| Memory Usage | > 85% | Alert |
| Disk Usage | > 90% | Alert CRÍTICO |
| Load Average | > CPU cores | Alert |
| Network I/O | > 100Mbps | Monitor |
| File Handles | > 80% limit | Alert |

### Email/SendGrid

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Bounces | > 5% | Alert |
| Spam Reports | > 1% | Alert CRÍTICO |
| Delivery Rate | < 99% | Alert |
| Queue Time | > 60s | Alert |

### Pipeline de Ventas

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Conversion Rate | Drop > 20% | Alert |
| Average Stage Time | Increase > 50% | Monitor |
| Lead Quality Score | Drop > 10% | Alert |
| Proposal Generation Time | > 120s | Alert |
| Email Open Rate | Drop > 30% | Monitor |

---

## 🏗️ STACK RECOMENDADO (OPCIÓN 1: BÁSICO)

### Uptime Kuma + Email Alerts

**Instalación (5 minutos):**

```bash
# En un servidor separado o en el mismo
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:latest
```

**Configurar Monitors:**
1. HTTP Check: `https://tu-dominio.com/health`
2. Intervalo: 5 minutos
3. Notificación: Email a Felipe
4. Retry: 3 intentos

**Ventajas:**
- ✅ Fácil de instalar
- ✅ Interfaz web bonita
- ✅ Bajo overhead
- ✅ Perfecto para empezar

**Limitaciones:**
- ❌ No hay métricas detalladas
- ❌ Solo uptime/downtime

---

## 🏗️ STACK RECOMENDADO (OPCIÓN 2: INTERMEDIARIO)

### Prometheus + Grafana + AlertManager

**Arquitectura:**
```
Felix API
    ↓
Prometheus scrape /metrics
    ↓
Grafana visualization
    ↓
AlertManager
    ↓
Email/Slack
```

### Instalación

#### 1. Instalar Prometheus

```bash
# En el servidor o separado
sudo apt-get install -y prometheus prometheus-node-exporter

# Configurar /etc/prometheus/prometheus.yml
cat > /etc/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - '/etc/prometheus/rules.yml'

scrape_configs:
  - job_name: 'felix-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
EOF

sudo systemctl restart prometheus
```

#### 2. Instalar PostgreSQL Exporter

```bash
# Exportador de métricas PostgreSQL
sudo apt-get install -y postgres-exporter

# Configurar conexión en /etc/default/postgres-exporter
DATABASE_URL="postgresql://felix_user:password@localhost:5432/felix_prod"

sudo systemctl restart postgres-exporter
```

#### 3. Instalar Grafana

```bash
sudo apt-get install -y grafana-server

# Iniciar
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Acceder en http://localhost:3000
# Usuario: admin / Password: admin (CAMBIAR!)
```

#### 4. Agregar Data Source en Grafana

- URL: `http://localhost:9090`
- Type: Prometheus
- Save & Test

#### 5. Crear Dashboards

**Dashboard 1: System Overview**
- CPU, Memory, Disk usage
- Network I/O
- Load average

**Dashboard 2: Felix API**
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Active connections
- Task queue

**Dashboard 3: Database**
- Connection pool usage
- Query performance
- Slow queries
- Replication lag
- Table sizes

**Dashboard 4: Business Metrics**
- Leads by stage
- Conversion rate
- Email send/open rates
- Revenue forecast

### Reglas de Alertas (Prometheus)

```yaml
# /etc/prometheus/rules.yml

groups:
  - name: felix_alerts
    interval: 30s
    rules:
      
      # API Alerts
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on Felix API"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API response time high"

      # Database Alerts
      - alert: HighDatabaseLoad
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL connection pool near limit"
          
      - alert: SlowQueries
        expr: rate(pg_slow_queries_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow queries detected"

      # System Alerts
      - alert: HighCPUUsage
        expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
          
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 10m
        labels:
          severity: warning
          
      - alert: DiskNearCapacity
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes) < 0.1
        for: 10m
        labels:
          severity: critical

      # Email/SendGrid Alerts
      - alert: HighBounceRate
        expr: sendgrid_bounce_rate > 0.05
        for: 5m
        labels:
          severity: critical
          
      - alert: LowDeliveryRate
        expr: sendgrid_delivery_rate < 0.99
        for: 5m
        labels:
          severity: warning

      # Business Alerts
      - alert: ConversionRateDrop
        expr: increase(leads_converted[1h]) / increase(leads_total[1h]) < 0.15
        for: 1h
        labels:
          severity: warning
```

### AlertManager Configuration

```yaml
# /etc/alertmanager/config.yml

global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      repeat_interval: 1h
    - match:
        severity: warning
      receiver: 'warning'
      repeat_interval: 12h

receivers:
  - name: 'default'
    email_configs:
      - to: 'felipe@enbuenamesa.com'
        from: 'alerts@enbuenamesa.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'tu-email@gmail.com'
        auth_password: 'tu-app-password'
        headers:
          Subject: 'Felix Alert: {{ .GroupLabels.alertname }}'

  - name: 'critical'
    email_configs:
      - to: 'felipe@enbuenamesa.com'
        from: 'alerts@enbuenamesa.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'tu-email@gmail.com'
        auth_password: 'tu-app-password'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts-critical'

  - name: 'warning'
    email_configs:
      - to: 'felipe@enbuenamesa.com'
```

---

## 🏗️ STACK RECOMENDADO (OPCIÓN 3: AVANZADO)

### ELK Stack (Elasticsearch, Logstash, Kibana)

**Para producción con miles de eventos/min**

```bash
# Docker Compose
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    ports:
      - "5000:5000"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    environment:
      - LS_JAVA_OPTS=-Xmx256m -Xms256m

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  elasticsearch_data:
```

**Logstash Config para Felix:**

```
input {
  file {
    path => "/var/log/felix/sistema.log"
    start_position => "beginning"
  }
}

filter {
  json {
    source => "message"
  }
  
  if [level] == "ERROR" {
    mutate {
      add_tag => ["error", "critical"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "felix-%{+YYYY.MM.dd}"
  }
  
  if "critical" in [tags] {
    email {
      to => "felipe@enbuenamesa.com"
      subject => "CRÍTICO: Error en Felix Automation"
    }
  }
}
```

---

## 📝 LOGGING STRATEGY

### Levels por Componente

```yaml
root: INFO
orchestrator: DEBUG
agents: INFO
auditors: DEBUG
database: WARNING
email: INFO
whitebox: INFO
api: INFO
```

### Formato de Logs

**JSON Structured Logging:**

```json
{
  "timestamp": "2026-10-05T16:09:00Z",
  "level": "INFO",
  "component": "lead_scorer_agent",
  "client_id": 123,
  "message": "Lead scored successfully",
  "score": 87,
  "duration_ms": 245,
  "trace_id": "abc123def456"
}
```

### Retención de Logs

```yaml
Logs:
  root: 30 days
  application: 90 days
  errors: 180 days
  security: 365 days
```

---

## 🚨 RUNBOOK DE TROUBLESHOOTING

### Problema: Error Rate > 1%

**Investigación:**
1. Revisar últimos 100 errores en logs:
   ```bash
   tail -100 /var/log/felix/error.log | grep ERROR | tail -20
   ```

2. Verificar database:
   ```bash
   systemctl status postgresql
   psql -U felix_user -d felix_prod -c "SELECT COUNT(*) FROM clients;"
   ```

3. Revisar SendGrid API:
   ```bash
   curl -s "https://api.sendgrid.com/v3/stats" \
     -H "Authorization: Bearer $SENDGRID_API_KEY"
   ```

4. Reiniciar servicio si es necesario:
   ```bash
   systemctl restart felix-api
   ```

### Problema: High Memory Usage

**Investigación:**
1. Top processes:
   ```bash
   ps aux --sort=-%mem | head -10
   ```

2. Memory leaks en Python:
   ```bash
   python -m tracemalloc [script]
   ```

3. Cache cleanup:
   ```bash
   rm -rf /var/lib/felix/cache/*
   ```

### Problema: Database Slow Queries

**Investigación:**
1. Ver queries lentas:
   ```sql
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 10;
   ```

2. Crear índices si es necesario:
   ```sql
   CREATE INDEX idx_clients_stage ON clients(stage);
   CREATE INDEX idx_audits_client_date ON audits(client_id, created_at);
   ```

3. Vacuum + Analyze:
   ```bash
   sudo -u postgres vacuumdb -d felix_prod -a
   sudo -u postgres analyzedb -d felix_prod
   ```

### Problema: API No Responde

**Checklist:**
- [ ] ¿Está el servicio activo? `systemctl status felix-api`
- [ ] ¿Puertos abiertos? `netstat -tlnp | grep 8000`
- [ ] ¿Logs muestran errores? `tail -50 /var/log/felix/error.log`
- [ ] ¿Conexión a BD? `psql -U felix_user -d felix_prod -c "\dt"`
- [ ] ¿Espacio en disco? `df -h | grep -v 100%`

---

## 📊 DASHBOARDS IMPORTANTES

### Dashboard 1: Health Check (CRÍTICO)

```
┌─────────────────────────────────────────┐
│  FELIX AUTOMATION - HEALTH DASHBOARD    │
├─────────────────────────────────────────┤
│                                         │
│  Status: 🟢 OK       Uptime: 99.95%    │
│                                         │
│  API Response:  145ms  │████            │
│  Error Rate:    0.02%  │                │
│  CPU Usage:     42%    │███             │
│  Memory Usage:  61%    │█████           │
│  DB Connections: 12/40│███             │
│                                         │
│  Last Error: None                      │
│  Last Restart: 48h ago                 │
│                                         │
└─────────────────────────────────────────┘
```

### Dashboard 2: Pipeline Performance

```
┌─────────────────────────────────────────┐
│  SALES PIPELINE - PERFORMANCE          │
├─────────────────────────────────────────┤
│                                         │
│  Stage Breakdown:                       │
│  Prospecto:    45 (20%)  ▓▓▓▓░          │
│  Propuesta:    120 (55%)  ▓▓▓▓▓▓▓▓▓    │
│  Negociación:  42 (19%)  ▓▓▓░           │
│  Cerrado:      18 (8%)   ▓░             │
│                                         │
│  Conversion Rate: 18% (vs target 20%)  │
│  Avg Stage Time:  5.2 days             │
│  Revenue Forecast: $45,000/month       │
│                                         │
└─────────────────────────────────────────┘
```

### Dashboard 3: Agent Performance

```
┌──────────────────────────────────────────┐
│  AGENTS PERFORMANCE STATUS              │
├──────────────────────────────────────────┤
│                                          │
│  Multi-Platform Auditor   ✅ 100%        │
│  Lead Scorer Agent        ✅ 100%        │
│  Proposal Generator       ✅ 99.8%       │
│  Email Sender             ⚠️  95% (3 err)│
│  Follow-up Agent          ✅ 100%        │
│  Sales Pipeline           ✅ 100%        │
│  Funnel Management        ✅ 100%        │
│                                          │
│  Overall Success Rate: 99.1%            │
│  Failed Tasks (24h): 3                  │
│                                          │
└──────────────────────────────────────────┘
```

---

## 📞 ESCALATION POLICY

### CRÍTICO (Response: <15 min)

- API no responde
- Database desconectada
- Disk full
- Error rate > 5%
- SendGrid bounce rate > 10%

**Contactar:** Felipe URGENTE (SMS + Email + Slack)

### WARNING (Response: <1 hora)

- Response time alta
- Memory/CPU > 80%
- Slow queries
- Email bounce rate 5-10%
- Conversion rate drop > 20%

**Contactar:** Felipe vía Email + Slack

### INFO (Response: <4 horas)

- Logs de eventos normales
- Métricas de utilización
- Performance trends

**Acción:** Solo logging, monitoreo

---

## 🔄 MANTENIMIENTO PREVENTIVO

### Diario
- [ ] Revisar errores en logs
- [ ] Verificar uptime (debe ser > 99.9%)
- [ ] Checar conversion rate (cambios significativos?)

### Semanal
- [ ] Revisar métricas de performance
- [ ] Limpiar cache local
- [ ] Generar reporte de alertas
- [ ] Verificar disk usage

### Mensual
- [ ] Full backup de BD
- [ ] Analyze queries (pg_stat_statements)
- [ ] Actualizar índices si es necesario
- [ ] Revisar security logs
- [ ] Plan de capacity planning

### Trimestral
- [ ] Disaster recovery test
- [ ] Performance benchmarking
- [ ] Security audit
- [ ] Stack upgrade evaluation

---

## 📱 CONFIGURACIÓN DE ALERTAS

### Email Alerts

```bash
# Configurar SMTP con Gmail
# 1. Habilitar 2FA en Gmail
# 2. Generar App Password:
#    https://myaccount.google.com/apppasswords
# 3. Copiar contraseña a config de AlertManager
```

### Slack Integration

```bash
# 1. Crear Webhook en Slack:
#    https://api.slack.com/apps → Create New App
#    Incoming Webhooks → Add New Webhook to Workspace

# 2. Copiar URL a AlertManager config:
#    https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

# 3. Testear:
#    curl -X POST -H 'Content-type: application/json' \
#      --data '{"text":"Test"}' \
#      $SLACK_WEBHOOK_URL
```

### SMS Alerts (Twilio - Opcional)

```bash
# Para alertas CRÍTICAS vía SMS
# Requiere configuración en AlertManager + webhook externo

# Instalación:
pip install twilio

# Script en /opt/felix-automation/scripts/sms_alert.py
```

---

## 📚 REFERENCIAS

| Herramienta | Documentación | Setup Time |
|-------------|---------------|-----------|
| Uptime Kuma | https://uptime.kuma.pet | 5 min |
| Prometheus | https://prometheus.io/docs | 30 min |
| Grafana | https://grafana.com/docs | 30 min |
| ELK Stack | https://www.elastic.co/guide | 2-3 horas |
| AlertManager | https://prometheus.io/docs/alerting | 1 hora |

---

## ✅ CHECKLIST POST-DEPLOYMENT

- [ ] Uptime Kuma instalado y configurado
- [ ] Health checks activos cada 5 min
- [ ] Email alerts funcionando
- [ ] Logs rotando correctamente
- [ ] Prometheus scrapeando métricas (si aplica)
- [ ] Grafana dashboards creados (si aplica)
- [ ] AlertManager configurado (si aplica)
- [ ] Escalation policy definida
- [ ] Runbook de troubleshooting disponible
- [ ] Equipo capacitado en monitoreo
- [ ] Backup strategy implementada
- [ ] Disaster recovery plan probado

---

**Responsable:** Felipe (@enbuenamesa.com)  
**Revisado:** 2026-10-05  
**Próxima actualización:** 2026-11-05
