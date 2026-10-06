# FASE 14 - Monitoring Integration Guide

## 📋 Resumen

La integración de monitoreo en `orchestrator.py` está **COMPLETA**. El sistema ahora captura métricas en tiempo real de:

- ✅ Operaciones de base de datos (tiempos de conexión, queries)
- ✅ Transiciones de pipeline (etapas de clientes)
- ✅ Creación de auditorías (plataformas, scores)
- ✅ Generación de propuestas (cantidad, valores)
- ✅ Envío de emails (tipos, cantidades)
- ✅ Eventos WebSocket (emisiones, errores)

## 🚀 Inicialización

### Opción 1: Inicialización Simple (Recomendado para desarrollo)

```python
# main.py o entry point de tu aplicación
from backend.monitoring_startup import initialize_monitoring

if __name__ == "__main__":
    # Inicializar monitoreo
    monitoring = initialize_monitoring()
    
    # Resto de tu código de aplicación...
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()
    
    # ... ejecutar agentes, procesar clientes, etc.
```

### Opción 2: Inicialización con Background Tasks (Producción)

```python
# main.py
from backend.monitoring_startup import initialize_monitoring, start_monitoring_background_tasks

if __name__ == "__main__":
    # Inicializar monitoreo
    monitoring = initialize_monitoring()
    
    # Iniciar health checks en background (cada 30 segundos)
    health_thread = start_monitoring_background_tasks()
    
    # Resto de tu código...
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()
    
    # ... ejecutar agentes
```

### Opción 3: Con API REST (Full Production)

```python
# flask_app.py o fastapi_app.py
from flask import Flask, jsonify
from backend.monitoring_startup import initialize_monitoring, get_monitoring_status

app = Flask(__name__)

# Inicializar al startup
initialize_monitoring()

@app.route('/api/monitoring/health')
def health():
    """Health check endpoint"""
    return jsonify(get_monitoring_status())

@app.route('/api/monitoring/dashboard')
def dashboard():
    """Monitoring dashboard endpoint"""
    status = get_monitoring_status()
    return jsonify(status)

if __name__ == "__main__":
    app.run(debug=False, port=5000)
```

## 📊 Métricas Capturadas

### Database Operations
- `database_connection_time_ms` - Tiempo conexión a BD (timer)
- `database_connection_errors` - Errores de conexión (counter)

### Pipeline Management
- `pipeline_stage_transitions` - Transiciones de etapa (counter, labeled por from_stage/to_stage)

### Audits
- `audits_created` - Auditorías creadas (counter, labeled por platform)
- `audit_score` - Scores de auditorías (gauge, labeled por platform)

### Proposals
- `proposals_created` - Propuestas creadas (counter)
- `proposal_estimated_value` - Valores estimados de propuestas (gauge, en USD)

### Emails
- `emails_sent` - Emails enviados (counter, labeled por email_type)

### WebSocket Events
- `websocket_events_emitted` - Eventos WebSocket emitidos (counter, labeled por event_type)
- `websocket_event_errors` - Errores al emitir eventos (counter, labeled por event_type)
- `proposal_value_emitted` - Valores de propuesta emitidos (gauge, en USD)

### Performance
- `database.get_client` - Tiempo query de cliente individual
- `database.get_all_clients` - Tiempo query de todos los clientes
- `pipeline.update_stage` - Tiempo actualización de etapa
- `audit.save` - Tiempo guardado de auditoría
- `audit.create` - Tiempo creación de auditoría
- `proposal.create` - Tiempo creación de propuesta
- `email.log` - Tiempo logging de email
- `websocket.pipeline_event` - Tiempo emisión evento pipeline
- `websocket.audit_event` - Tiempo emisión evento auditoría
- `websocket.email_event` - Tiempo emisión evento email
- `websocket.proposal_event` - Tiempo emisión evento propuesta

## 🔍 Acceder a Métricas Recolectadas

```python
from backend.monitoring import get_metrics_collector, get_monitoring_dashboard

# Opción 1: Acceder a métricas directas
collector = get_metrics_collector()

# Obtener historial de los últimos 60 minutos
latencies = collector.get_metric_history("database.get_client", minutes=60)
print(f"Client query latencies (last 60min): {latencies}")

# Obtener última métrica registrada
latest = collector.get_latest("websocket_events_emitted")
print(f"Last WebSocket event: {latest}")

# Obtener estadísticas (min, max, avg, p50, p95, p99)
stats = collector.get_stats("database_connection_time_ms", minutes=60)
print(f"DB connection stats: {stats}")

# Opción 2: Acceder a dashboard agregado
dashboard = get_monitoring_dashboard()
dashboard_data = dashboard.get_dashboard_data()
print(f"Full dashboard: {dashboard_data}")
```

## ⚠️ Health Checks Configurados

El sistema de salud evalúa automáticamente:

1. **WebSocket Latency** (<100ms target, >200ms critical)
2. **API Response Time** (<500ms target, >2000ms critical)
3. **Cache Hit Rate** (>80% target, <50% critical)
4. **WebSocket Connections** (>0 target for active system)
5. **Prediction Generation Time** (<1000ms target, >5000ms critical)
6. **Database Connection Pool** (active connections)
7. **Error Rate** (<1% target, >5% critical)
8. **Offline Users** (tracking disconnections)

Estado general: `healthy`, `degraded`, o `unhealthy`

## 🔧 Gracias Degradadas

Si monitoreo NO está disponible:

```python
from orchestrator import MONITORING_ENABLED

if MONITORING_ENABLED:
    print("Monitoring is active")
else:
    print("Monitoring is disabled - application continues normally")
```

La aplicación funciona 100% normal incluso sin monitoreo. Las métricas son opcionales.

## 📈 Próximos Pasos (Semana 2)

1. **Integración API REST** - Endpoints `/api/monitoring/health`, `/api/monitoring/dashboard`
2. **Prometheus/Grafana** - Exportar métricas a Prometheus para visualización
3. **Alert Configuration** - Slack, PagerDuty, email para alertas críticas
4. **Load Testing** - Usar load tester para validar bajo estrés

## 🧪 Testing

Para verificar que monitoreo funciona:

```bash
cd /home/claude/felix-automation

# Test 1: Verificar imports funcionan
python3 -c "from backend.monitoring_startup import initialize_monitoring; print('✓ Imports OK')"

# Test 2: Inicializar y verificar
python3 -c "from backend.monitoring_startup import initialize_monitoring; m = initialize_monitoring(); print('✓ Monitoring initialized')"

# Test 3: Verificar orchestrator con monitoring
python3 -c "
from orchestrator import FelixAutomationOrchestrator, MONITORING_ENABLED
from backend.monitoring_startup import initialize_monitoring
initialize_monitoring()
o = FelixAutomationOrchestrator('data/pipeline.db')
print(f'✓ Monitoring enabled: {MONITORING_ENABLED}')
print('✓ Orchestrator ready')
"
```

## 📝 Archivos Modificados/Creados

**MODIFICADOS:**
- `orchestrator.py` - Instrumentación de 10+ métodos

**NUEVOS:**
- `backend/monitoring_startup.py` - Initialization y startup helpers
- `MONITORING_INTEGRATION_GUIDE.md` - Esta guía

## ✅ Estado

- ✅ Monitoring imports added to orchestrator.py
- ✅ Database operations instrumented (9 methods)
- ✅ WebSocket events instrumented (4 methods)
- ✅ Performance profiling added (15 operations)
- ✅ Graceful degradation implemented
- ✅ Initialization helpers created
- ✅ Documentation complete

**NEXT CRITICAL TASK:** Integrate API endpoints to expose monitoring data
- POST /api/monitoring/initialize
- GET /api/monitoring/health
- GET /api/monitoring/dashboard
- GET /api/monitoring/metrics/<metric_name>
