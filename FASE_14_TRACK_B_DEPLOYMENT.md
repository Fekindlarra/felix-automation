# 📊 FASE 14 Week 2 - Track B (Prometheus/Grafana)
## Guía de Despliegue y Validación

**Estado:** ✅ IMPLEMENTACIÓN COMPLETA  
**Última actualización:** 2026-10-06  
**Responsable:** Felipe & Claude  

---

## 📋 Checklist de Implementación

### Backend (Python/FastAPI)
- ✅ **PrometheusExporter** (`backend/prometheus_exporter.py`)
  - Clase singleton con métodos de exportación
  - Integración con MetricsCollector, HealthChecker, PerformanceProfiler
  - Genera métricas en formato Prometheus text v0.0.4
  - 1,673+ bytes por exportación

- ✅ **Prometheus Routes** (`backend/routes/prometheus_routes.py`)
  - 6 endpoints REST para exposición de métricas:
    - `GET /metrics` - Métricas completas
    - `GET /metrics/health` - Solo health checks
    - `GET /metrics/alerts` - Métricas de alertas
    - `GET /metrics/performance` - Performance profiling
    - `GET /metrics/websocket` - Métricas WebSocket
    - `GET /metrics/config` - Configuración recomendada

- ✅ **FastAPI Integration** (`backend/app.py`)
  - ✅ Import: `from backend.routes.prometheus_routes import router as prometheus_router`
  - ✅ Register: `app.include_router(prometheus_router)`
  - ✅ Listo para iniciar servidor

### Configuración de Prometheus
- ✅ **prometheus.yml** (2.7 KB)
  - Scrape interval: 15 segundos (global)
  - Evaluation interval: 15 segundos
  - 7 scrape jobs configurados:
    1. `prometheus` - Métricas de Prometheus (port 9090)
    2. `felix-automation` - Métricas generales (15s, port 8000)
    3. `felix-health` - Health checks (10s, más frecuente)
    4. `felix-alerts` - Métricas de alertas (30s)
    5. `felix-performance` - Performance metrics (30s)
    6. `felix-websocket` - WebSocket metrics (20s)
    7. (Node Exporter - opcional, comentado)
  - AlertManager configurado en localhost:9093
  - Rule files: `alert_rules.yml`

### Reglas de Alerta
- ✅ **alert_rules.yml** (8.9 KB)
  - 18 reglas de alerta en 2 grupos principales:
    - **felix_alerts** (18 reglas)
    - **felix_recording_rules** (3 reglas de grabación)

#### Alertas Configuradas:

**System Health (2 alertas)**
- `FelixSystemUnhealthy` - Sistema no saludable por >5m (CRÍTICA)
- `FelixSystemDegraded` - Sistema degradado por >10m (WARNING)

**WebSocket (4 alertas)**
- `HighWebSocketLatency` - Latencia >200ms por 5m (WARNING)
- `CriticalWebSocketLatency` - Latencia >500ms por 2m (CRÍTICA)
- `LowWebSocketConnections` - <1 conexión activa por 10m (WARNING)
- `HighWebSocketErrorRate` - Error rate >5% por 5m (WARNING)

**API Performance (2 alertas)**
- `HighAPIResponseTime` - Respuesta >1000ms por 5m (WARNING)
- `CriticalAPIResponseTime` - Respuesta >5000ms por 2m (CRÍTICA)

**Cache & Performance (2 alertas)**
- `LowCacheHitRate` - Hit rate <70% por 15m (WARNING)
- `CriticalCacheHitRate` - Hit rate <50% por 5m (CRÍTICA)

**Error Rate (2 alertas)**
- `HighErrorRate` - Error rate >5% por 10m (WARNING)
- `CriticalErrorRate` - Error rate >10% por 5m (CRÍTICA)

**Alert Escalation (2 alertas)**
- `MultipleActiveAlerts` - Múltiples alertas críticas activas (CRÍTICA)
- `WarningAlertsEscalating` - Conteo de warnings aumentando (WARNING)

**System Uptime & Health (4 alertas)**
- `SystemRestartDetected` - Reinicio detectado (WARNING)
- `WebSocketLatencyHealthCheck` - Health check fallido (WARNING)
- `CacheHitRateHealthCheck` - Health check fallido (WARNING)
- `DatabaseConnectionPoolHealthCheck` - Pool crítico (CRÍTICA)

### Docker Compose Stack
- ✅ **docker-compose.prometheus-grafana.yml** (2.0 KB)
  - **Prometheus** (v latest)
    - Port: 9090
    - Volume: `prometheus_data:/prometheus`
    - Retention: 30 días
    - Healthcheck implícito

  - **Grafana** (v latest)
    - Port: 3000
    - Credenciales: admin / admin123
    - Volume: `grafana_data:/var/lib/grafana`
    - Provisioning: `./grafana-provisioning` (readonly)
    - Plugins: grafana-piechart-panel

  - **AlertManager** (v latest)
    - Port: 9093
    - Volume: `alertmanager_data:/alertmanager`
    - Config: `./alertmanager.yml`

  - Network: `felix-monitoring` (bridge)
  - Restart policy: `unless-stopped`

---

## 🚀 Instrucciones de Despliegue

### Paso 1: Iniciar Stack de Monitoreo

```bash
cd /home/claude/felix-automation

# Iniciar servicios en background
docker-compose -f docker-compose.prometheus-grafana.yml up -d

# Verificar servicios iniciados
docker-compose -f docker-compose.prometheus-grafana.yml ps

# Esperado:
# NAME                    STATUS
# felix-prometheus        Up 2 minutes
# felix-grafana          Up 2 minutes  
# felix-alertmanager     Up 2 minutes
```

### Paso 2: Verificar Métricas desde FastAPI

```bash
# Endpoint principal (todas las métricas)
curl -s http://localhost:8000/metrics | head -30

# Esperado: Formato Prometheus con HELP, TYPE, y valores
# # Generated at 2026-10-06T01:09:05.805510+00:00
# # HELP felix_health_status Overall system health...
# # TYPE felix_health_status gauge
# felix_health_status 1
```

### Paso 3: Acceso a Prometheus Web UI

```
URL: http://localhost:9090
```

**Validaciones en Prometheus:**

1. **Status → Targets**
   - Debería mostrar 7 targets (jobs)
   - Estado esperado: GREEN ✅ para todos

2. **Status → Service Discovery**
   - Listar todos los targets configurados
   - Verificar que felix-automation está UP

3. **Graph**
   - Ejecutar query de ejemplo: `felix_health_status`
   - Debería retornar: `felix_health_status 1`

4. **Alerts**
   - Ver todas las reglas de alerta
   - Estado inicial: INACTIVE (normal si no hay problemas)

### Paso 4: Acceso a Grafana

```
URL: http://localhost:3000
Usuario: admin
Contraseña: admin123
```

**Configuración Inicial:**

1. **Agregar Data Source Prometheus**
   ```
   Name: Prometheus
   URL: http://prometheus:9090
   Access: Server (default)
   ```

2. **Importar Dashboards** (opcional en esta fase)
   - Grafana tiene dashboards de ejemplo
   - Crear dashboard personalizado con las métricas:
     - felix_health_status
     - felix_websocket_latency
     - felix_api_response_time
     - felix_cache_hit_rate
     - felix_error_rate

### Paso 5: Validar AlertManager

```
URL: http://localhost:9093
```

**Verificaciones:**

1. **Status**
   - Configuration: Debería cargar alertmanager.yml
   
2. **Alerts**
   - Ver alertas activas (si las hay)
   - Verificar clustering status

---

## 🔍 Testing & Validación

### Test 1: Métricas Endpoint Funcional

```bash
# Test cada endpoint
for endpoint in metrics metrics/health metrics/alerts metrics/performance metrics/websocket metrics/config; do
  echo "Testing: /metrics/$endpoint"
  curl -s http://localhost:8000/$endpoint -o /dev/null -w "Status: %{http_code}\n"
done

# Esperado: Status: 200 para todos
```

### Test 2: Formato Prometheus Válido

```bash
# Obtener métricas y validar formato
curl -s http://localhost:8000/metrics > metrics_dump.txt

# Verificaciones:
grep "^# HELP" metrics_dump.txt | wc -l  # Debería ser >10 HELP lines
grep "^# TYPE" metrics_dump.txt | wc -l  # Debería ser >10 TYPE lines
grep "^felix_" metrics_dump.txt | wc -l  # Debería ser >50 metric lines
```

### Test 3: Prometheus Scrape Success

```bash
# En Prometheus: Status → Targets
# Verificar que "felix-automation" target está UP
# Verificar que todos los endpoints responden rápido (<500ms)
```

### Test 4: Alert Rules Valid

```bash
# Prometheus debería cargar todas las reglas sin errores
# Status → Rules: Debería mostrar 18 alert rules + 3 recording rules
# No debería haber warning icon rojo ❌
```

---

## 📊 Métricas Disponibles (Muestra)

### Health Metrics
- `felix_health_status` - Estado general (1=healthy, 0=degraded, -1=unhealthy)
- `felix_health_check{check="..."}` - Health checks por componente

### WebSocket Metrics
- `felix_websocket_latency` - Latencia en ms
- `felix_websocket_connections` - Conexiones activas
- `felix_websocket_events_emitted` - Eventos enviados
- `felix_websocket_errors` - Errores total

### API Metrics
- `felix_api_response_time` - Tiempo de respuesta en ms
- `felix_api_requests_total` - Total de requests

### Cache Metrics
- `felix_cache_hit_rate` - Hit rate en %
- `felix_cache_operations` - Operaciones cache

### System Metrics
- `felix_error_rate` - Error rate en %
- `felix_uptime_seconds` - Uptime del sistema
- `felix_alerts_active{severity="..."}` - Alertas activas por severidad

---

## 🔧 Troubleshooting

### Prometheus No Conecta con FastAPI

**Síntoma:** Target "felix-automation" en estado RED/DOWN

```bash
# Verificar que FastAPI esté corriendo
curl http://localhost:8000/metrics

# Si no responde, iniciar FastAPI:
cd /home/claude/felix-automation
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### Prometheus No Persiste Datos

**Síntoma:** Métrica en Prometheus UI pero diciendo "No data"

```bash
# Verificar volumen de datos
docker exec felix-prometheus du -sh /prometheus

# Si está vacío, verificar permisos y restart
docker-compose -f docker-compose.prometheus-grafana.yml restart prometheus
```

### Alertas No Se Disparan

**Síntoma:** Alert status siempre INACTIVE

```bash
# Verificar que alert_rules.yml está cargado
curl http://localhost:9090/api/v1/rules

# Verificar métricas cumplan condiciones de alerta
# Ej: para HighWebSocketLatency necesita felix_websocket_latency > 200
curl http://localhost:8000/metrics | grep websocket_latency
```

### Grafana No Ve Prometheus

**Síntoma:** Data source error en Grafana

```bash
# Verificar conectividad docker entre servicios
docker exec felix-grafana curl -s http://prometheus:9090/graph

# Si falla, revisar docker-compose network configuration
docker network inspect felix-monitoring
```

---

## 📈 Métricas de Éxito

| Métrica | Esperado | Validación |
|---------|----------|-----------|
| Prometheus Targets UP | 7/7 | Status → Targets |
| Latencia Scrape | <500ms | Status → Targets (Scrape Duration) |
| Alert Rules Loaded | 18 + 3 | Status → Rules |
| Data Points Collected | >100 | Graph → `count(felix_*)` |
| Grafana Data Source OK | Connected | Configuration → Data Sources |
| AlertManager Connected | 1 instance | AlertManager Status page |

---

## 🎯 Próximas Fases

### Track C (Semana 3): Alert Routing
- [ ] Slack integration para alerts
- [ ] PagerDuty integration
- [ ] Email notifications
- [ ] Webhook handlers

### Track D (Semana 3-4): E2E Testing
- [ ] End-to-end test suite
- [ ] Performance regression testing
- [ ] Alert accuracy validation

### Track E (Semana 4-5): Mobile Optimization
- [ ] Responsive dashboard
- [ ] PWA support
- [ ] Offline capability

---

## 📝 Archivos Generados - Track B

```
/home/claude/felix-automation/
├── backend/
│   ├── prometheus_exporter.py          [9.7 KB] ✅ Nuevo
│   ├── routes/
│   │   └── prometheus_routes.py        [5.3 KB] ✅ Nuevo
│   └── app.py                          [Modified] ✅ Integrado
│
├── prometheus.yml                      [2.7 KB] ✅ Nuevo
├── alert_rules.yml                     [8.9 KB] ✅ Nuevo
├── docker-compose.prometheus-grafana.yml [2.0 KB] ✅ Nuevo
├── alertmanager.yml                    [Pendiente] (opcional)
├── grafana-provisioning/               [Pendiente] (optional dashboards)
│
└── FASE_14_TRACK_B_DEPLOYMENT.md      [Este archivo] ✅ Nuevo
```

---

## ✅ Checklist Final

Antes de pasar a Track C:

- [ ] Docker Compose stack inicia sin errores
- [ ] 6 endpoints de métricas responden con HTTP 200
- [ ] Prometheus scraper ve 7/7 targets en estado UP
- [ ] Alerts cargan sin errores (Status → Rules)
- [ ] Grafana puede conectar a Prometheus
- [ ] Al menos una métrica visible en Prometheus UI
- [ ] AlertManager accesible en puerto 9093
- [ ] No hay errors en logs de contenedores

```bash
# Quick validation script
docker-compose -f docker-compose.prometheus-grafana.yml ps
curl -s http://localhost:8000/metrics | head -5
curl -s http://localhost:9090/api/v1/targets | grep "status"
```

---

**Estado:** ✅ LISTO PARA DESPLEGAR  
**Tiempo estimado setup:** 5-10 minutos  
**Soporte:** Revisar troubleshooting section si hay issues
