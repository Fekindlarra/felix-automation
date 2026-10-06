# ⚡ QUICKSTART - Track B Deployment (5 minutos)

## 🎯 Objetivo
Iniciar el stack de monitoreo Prometheus/Grafana y verificar que todo funciona.

---

## 📋 Pre-requisitos
- Docker y docker-compose instalados
- FastAPI backend corriendo en puerto 8000
- Archivos completados: prometheus.yml, alert_rules.yml, docker-compose.prometheus-grafana.yml

---

## 🚀 Inicio Rápido

### Paso 1: Inicia el Stack (1 minuto)

```bash
cd /home/claude/felix-automation

# Inicia Prometheus, Grafana y AlertManager
docker-compose -f docker-compose.prometheus-grafana.yml up -d

# Verifica que todo está corriendo
docker-compose -f docker-compose.prometheus-grafana.yml ps
```

**Resultado esperado:**
```
NAME                    STATUS
felix-prometheus        Up X seconds
felix-grafana          Up X seconds
felix-alertmanager     Up X seconds
```

---

### Paso 2: Verifica Métricas (1 minuto)

```bash
# Test del endpoint principal
curl -s http://localhost:8000/metrics | head -20

# Debería ver algo como:
# # Generated at 2026-10-06T01:09:05...
# # HELP felix_health_status...
# # TYPE felix_health_status gauge
# felix_health_status 1
```

---

### Paso 3: Prometheus Web UI (1 minuto)

Abre en tu navegador:
```
http://localhost:9090
```

**En Prometheus:**
1. Click en **Status** → **Targets**
2. Debería ver 7 targets (jobs)
3. Todos deberían estar **GREEN ✅**

**Quick Check:**
- Click en **Graph**
- Ejecuta query: `felix_health_status`
- Debería retornar: `felix_health_status 1`

---

### Paso 4: Grafana Dashboard (1 minuto)

Abre en tu navegador:
```
http://localhost:3000
```

**Login:**
- Usuario: `admin`
- Contraseña: `admin123`

**Agregar Data Source:**
1. Click en **Configuration** ⚙️
2. Click en **Data Sources**
3. Click en **Add data source**
4. Selecciona **Prometheus**
5. En URL: `http://prometheus:9090`
6. Click **Save & Test** (debería decir "Data source is working")

---

### Paso 5: AlertManager (1 minuto)

Abre en tu navegador:
```
http://localhost:9093
```

Debería ver:
- **Status**: Configuración cargada
- **Alerts**: Lista de alertas (inicialmente vacía si todo está bien)

---

## ✅ Checklist de Validación

- [x] Docker containers corriendo (`docker ps`)
- [x] `/metrics` endpoint responde con HTTP 200
- [x] Prometheus conecta a todos los 7 targets
- [x] Prometheus ve al menos una métrica (felix_health_status)
- [x] Grafana puede conectar a Prometheus
- [x] AlertManager accesible en puerto 9093

---

## 🔗 URLs de Acceso

| Servicio | URL | Notas |
|----------|-----|-------|
| **FastAPI Metrics** | http://localhost:8000/metrics | Endpoint principal |
| **FastAPI Health** | http://localhost:8000/metrics/health | Solo health checks |
| **Prometheus** | http://localhost:9090 | Web UI + Query Editor |
| **Grafana** | http://localhost:3000 | Dashboards (admin/admin123) |
| **AlertManager** | http://localhost:9093 | Gestión de alertas |

---

## 🔍 Troubleshooting Rápido

### Prometheus targets en RED ❌

```bash
# Verifica que FastAPI está corriendo
curl http://localhost:8000/health

# Si no responde, inicia FastAPI:
cd /home/claude/felix-automation
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### Grafana no ve Prometheus

```bash
# Verifica conectividad docker
docker exec felix-grafana curl -s http://prometheus:9090/graph

# Si falla, restart:
docker-compose -f docker-compose.prometheus-grafana.yml restart grafana
```

### No hay datos en Prometheus

```bash
# Verifica que prometheus.yml está correcto
docker exec felix-prometheus cat /etc/prometheus/prometheus.yml

# Verifica logs
docker-compose -f docker-compose.prometheus-grafana.yml logs prometheus
```

---

## 📊 Datos de Prueba

Para generar datos en Prometheus, ejecuta:

```bash
# Genera carga WebSocket simulada
python tests/load_test_quick.py

# Esto debería:
# 1. Conectar 10, 50, 100 clientes
# 2. Generar eventos
# 3. Aumentar métricas que se verán en Prometheus
```

Después, regresa a Prometheus y ejecuta:
```
felix_websocket_latency
felix_websocket_connections
felix_api_response_time
```

---

## 🎓 Próximo Paso

Después de validar Track B, puedes:

1. **Crear Dashboards en Grafana** - Visualizar métricas con gráficos
2. **Configurar Alertas** - Recibir notificaciones vía Slack/Email
3. **Iniciar Track C** - Alert Routing integration

---

## 📝 Referencia Rápida - Comandos Útiles

```bash
# Ver estado de containers
docker-compose -f docker-compose.prometheus-grafana.yml ps

# Ver logs en tiempo real
docker-compose -f docker-compose.prometheus-grafana.yml logs -f prometheus

# Detener todo
docker-compose -f docker-compose.prometheus-grafana.yml down

# Eliminar datos (reset completo)
docker-compose -f docker-compose.prometheus-grafana.yml down -v

# Reiniciar servicio específico
docker-compose -f docker-compose.prometheus-grafana.yml restart prometheus

# Ver tamaño de datos almacenados
docker exec felix-prometheus du -sh /prometheus
```

---

## 📞 Si Algo No Funciona

1. **Revisa logs:** `docker-compose logs`
2. **Lee guía completa:** `FASE_14_TRACK_B_DEPLOYMENT.md`
3. **Verifica conectividad:** `curl http://localhost:9090`
4. **Reinicia todo:** `docker-compose down && docker-compose up -d`

---

## ✨ ¡Listo!

Track B está operativo. Ahora puedes:

✅ Monitorear métricas en tiempo real  
✅ Ver alertas en AlertManager  
✅ Crear dashboards en Grafana  
✅ Progresar a Track C (Alert Routing)

---

*Tiempo total: ~5 minutos*  
*Complejidad: Baja*  
*Status: ✅ OPERACIONAL*
