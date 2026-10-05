# ⚡ Performance Testing & Load Validation Guide

**Versión:** FASE 11  
**Fecha:** 2026-10-05  
**Propósito:** Validar capacidad y rendimiento del sistema  

---

## 📊 Métricas de Éxito

| Métrica | Target | Crítico | Aviso |
|---------|--------|---------|-------|
| Health Check Response | < 100ms | > 500ms | > 200ms |
| Concurrent Requests Success Rate | > 95% | < 80% | 80-95% |
| Database Query Avg | < 50ms | > 200ms | 50-200ms |
| Pipeline per Client | < 1000ms | > 5000ms | 1000-5000ms |
| Email Throughput | > 5 emails/s | < 1/s | 1-5/s |
| P99 Database Query | < 200ms | > 1000ms | 200-1000ms |

---

## 🏃 Ejecutar Load Tests

### Opción 1: Test Básico (Recomendado)

```bash
cd /home/claude/felix-automation
source venv/bin/activate

# Ejecutar sin parámetros (usa http://localhost:8000)
python scripts/load_test.py

# Esperado:
# ============================================================
# FELIX AUTOMATION - LOAD TESTING & PERFORMANCE VALIDATION
# ============================================================
# ✓ PASS - Health Check
# ✓ PASS - Concurrent Requests
# ✓ PASS - Database Performance
# ✓ PASS - Pipeline Execution
# ✓ PASS - Email Throughput
# ============================================================
# ✓ ALL TESTS PASSED!
```

### Opción 2: Test Contra Servidor Remoto

```bash
python scripts/load_test.py http://your-domain.com
```

### Opción 3: Test Automatizado (Cron)

```bash
# Agregar a crontab para ejecutar diariamente
crontab -e

# Agregar línea:
0 2 * * * cd /home/claude/felix-automation && source venv/bin/activate && python scripts/load_test.py >> data/logs/load_test_cron.log 2>&1
```

---

## 📈 Análisis de Resultados

### Después de cada test, revisar:

```bash
# Ver últimos resultados JSON
tail -20 data/logs/load_test_*.json

# Ver CSV para análisis
cat data/logs/load_test_*.csv

# Extraer métricas específicas
cat data/logs/load_test_YYYYMMDD_HHMMSS.json | jq '.tests[] | {test: .test, status: .status, avg_ms: .avg_ms}'
```

---

## 🎯 Interpretación de Tests

### TEST 1: Health Check
Valida que el servidor responde rápidamente a requests simples.

```
Salida esperada:
  Request 1/10: 12.45ms
  Request 2/10: 11.23ms
  ...
  Avg: 13.21ms ✓ PASS (< 100ms)
```

**Qué significa:**
- **< 50ms** - Excelente
- **50-100ms** - Bueno
- **100-200ms** - Aceptable pero revisar
- **> 200ms** - Problema de rendimiento

---

### TEST 2: Concurrent Requests
Valida que el sistema maneja múltiples requests simultáneamente.

```
Salida esperada:
  Completed 10/50 requests
  Completed 20/50 requests
  ...
  Total Requests: 50
  Successful: 48
  Failed: 2
  Avg Response: 45.32ms
  Throughput: 123 req/s ✓ PASS (success rate > 95%)
```

**Qué significa:**
- **Success Rate > 95%** - Sistema estable
- **Success Rate 80-95%** - Revisar logs de errores
- **Success Rate < 80%** - Problema crítico

---

### TEST 3: Database Performance
Valida que las queries a la BD son rápidas.

```
Salida esperada:
  Executed 20/100 queries
  ...
  Avg Query: 23.45ms
  P95 Query: 87.23ms
  P99 Query: 156.78ms ✓ PASS (avg < 50ms)
```

**Qué significa:**
- **Avg < 30ms** - Excelente
- **Avg 30-50ms** - Bueno
- **Avg 50-100ms** - Revisar indexes
- **Avg > 100ms** - Optimizar queries urgentemente

---

### TEST 4: Pipeline Execution
Valida que el pipeline completo ejecuta eficientemente.

```
Salida esperada:
  Pipeline 1/10: 123.45ms
  Pipeline 2/10: 145.67ms
  ...
  Avg per client: 156.78ms
  Clients/minute: 384 ✓ PASS (avg < 1000ms)
```

**Qué significa:**
- Simula auditoría → scoring → propuesta → email completo
- **< 500ms** - Excelente (puede procesar > 120 clientes/min)
- **500-1000ms** - Bueno (> 60 clientes/min)
- **> 1000ms** - Revisar paso específico

---

### TEST 5: Email Throughput
Valida velocidad de envío de emails.

```
Salida esperada:
  Sent 20/100 emails
  ...
  Total time: 18.23s
  Avg per email: 182.3ms
  Throughput: 5.48 emails/sec ✓ PASS (> 5 emails/sec)
```

**Qué significa:**
- **> 10 emails/sec** - Excelente (límite SendGrid es ~600/min = 10/sec)
- **5-10 emails/sec** - Bueno
- **1-5 emails/sec** - Aceptable pero revisar queue
- **< 1 email/sec** - Problema crítico

---

## 🔍 Troubleshooting de Performance

### Problema: Health Check lento (> 200ms)

```bash
# 1. Verificar si API está corriendo
curl -v http://localhost:8000/health

# 2. Revisar logs de aplicación
sudo tail -50 /var/log/felix/error.log

# 3. Verificar CPU y memoria
top -b -n 1 | head -20

# 4. Revisar número de conexiones
netstat -an | grep ESTABLISHED | wc -l
```

**Soluciones:**
- Aumentar workers Gunicorn: `--workers 8` (del 4 por defecto)
- Aumentar timeout: `--timeout 120` (default 120s)
- Restart del servicio: `sudo systemctl restart felix-api`

---

### Problema: Concurrent Requests con baja success rate (< 80%)

```bash
# 1. Verificar logs de aplicación
sudo tail -100 /var/log/felix/error.log | grep -i error

# 2. Revisar database connections
psql -U felix_user -d felix_prod -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Revisar qué procesos usan CPU
ps aux --sort -%cpu | head -10
```

**Soluciones:**
- Aumentar pool de conexiones DB: `max_connections` en PostgreSQL
- Revisar queries lentas: `SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;`
- Optimizar índices

---

### Problema: Database queries lentas (> 100ms)

```bash
# 1. Ver queries más lentas
psql -U felix_user -d felix_prod << 'SQL'
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
SQL

# 2. Ver índices faltantes
psql -U felix_user -d felix_prod << 'SQL'
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'public';
\d+ clients
SQL

# 3. Analizar plan de ejecución
EXPLAIN ANALYZE SELECT * FROM pipeline WHERE stage = 'propuesta';
```

**Soluciones:**
- Crear índices: `CREATE INDEX idx_pipeline_stage ON pipeline(stage);`
- Vacuum de BD: `VACUUM ANALYZE;`
- Ajustar work_mem: `SET work_mem = '256MB';`

---

### Problema: Pipeline lento (> 1000ms)

```bash
# Identificar paso lento:
# 1. Audit (web, facebook, google ads)
# 2. Scoring
# 3. Proposal generation
# 4. Email sending

# Revisar logs específicos
tail -50 data/logs/auditors.log
tail -50 data/logs/agents.log

# Perfilar ejecución
python -m cProfile -s cumtime scripts/load_test.py 2>&1 | head -50
```

**Soluciones por paso:**
- **Audits lento**: Revisar timeouts en config.yaml, aumentar si es necesario
- **Scoring lento**: Optimizar cálculo de scores, revisar queries
- **Proposal lento**: Revisar generación PDF/HTML, considerar caché
- **Email lento**: Revisar queue de SendGrid, aumentar batch size

---

### Problema: Email throughput bajo (< 1 emails/sec)

```bash
# Revisar logs de email
tail -50 data/logs/email.log

# Verificar estado de SendGrid API
curl -X GET https://api.sendgrid.com/v3/user/account \
  -H "Authorization: Bearer $SENDGRID_API_KEY"

# Revisar queue de emails pendientes
psql -U felix_user -d felix_prod -c "SELECT COUNT(*) FROM email_logs WHERE status='pending';"
```

**Soluciones:**
- Aumentar batch_size en config.yaml: `batch_size: 50` (default 10)
- Aumentar workers de email: `max_workers: 10`
- Verificar API key de SendGrid no está limitada
- Revisar si hay retry delays en queue

---

## 📊 Comparar Resultados Históricos

```bash
# Crear reporte comparativo
python << 'PYTHON'
import json
from pathlib import Path
from datetime import datetime

logs_dir = Path('data/logs')
test_files = sorted(logs_dir.glob('load_test_*.json'))[-5:]  # Últimos 5

print("HISTORICAL PERFORMANCE COMPARISON")
print("="*60)

for file in test_files:
    with open(file) as f:
        data = json.load(f)
        timestamp = data['timestamp']
        duration = data['duration_seconds']
        
        print(f"\n{timestamp}:")
        print(f"  Duration: {duration:.2f}s")
        
        for test in data['tests']:
            test_name = test.get('test', 'Unknown')
            status = test.get('status', 'Unknown')
            avg = test.get('avg_ms', 'N/A')
            
            if isinstance(avg, (int, float)):
                print(f"    {status} {test_name}: {avg:.2f}ms")
            else:
                print(f"    {status} {test_name}")

print("\n" + "="*60)
PYTHON
```

---

## 📈 Escalado y Capacidad

### Estimaciones de Capacidad (1 servidor)

| Métrica | Capacidad |
|---------|-----------|
| Auditorías/minuto | ~60 (1 por segundo) |
| Clientes en pipeline | ~500-1000 |
| Email/minuto (SendGrid limit) | ~600 |
| Concurrent connections | ~100-200 |
| Daily email capacity | ~250k (sendgrid enterprise) |

### Cuándo Escalar

- **CPU > 80%** continuamente: Aumentar workers/threads
- **Memory > 85%** continuamente: Aumentar RAM o optimizar
- **DB connections > 80%** de max: Aumentar pool size
- **Response time > 2000ms**: Revisar bottleneck específico

---

## ✅ Pre-Production Checklist

- [ ] Todos los tests pasan
- [ ] P99 response time < 500ms
- [ ] Email throughput > 5/sec
- [ ] Success rate > 95%
- [ ] Database connections optimizadas
- [ ] Índices creados
- [ ] Memory usage < 80%
- [ ] CPU usage < 70% durante carga normal
- [ ] Backup strategy validado
- [ ] Monitoring y alertas configuradas

---

**Soporte:** Felipe (@enbuenamesa.com)
