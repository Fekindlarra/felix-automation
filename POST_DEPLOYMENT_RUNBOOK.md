# 📋 RUNBOOK POST-DEPLOYMENT
## Felix Automation - Operación y Mantenimiento en Producción

**Versión:** 11.0  
**Fecha:** 2026-10-05  
**Audiencia:** Felipe y equipo de operaciones

---

## 🎯 PROPÓSITO

Este documento proporciona procedimientos para el monitoreo diario, mantenimiento, y resolución de problemas de Felix Automation en producción.

---

## 📊 CHECKLIST DIARIO (5 min)

Ejecutar cada mañana:

```bash
#!/bin/bash
# Verificación rápida de salud

echo "=== ESTADO DE SERVICIOS ==="
sudo systemctl status felix-api | grep Active

echo "=== HEALTH CHECK ==="
curl -s https://tu-dominio.com/health | jq '.status'

echo "=== CONEXIÓN A BD ==="
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "SELECT NOW();"

echo "=== ESPACIO EN DISCO ==="
df -h / | tail -1

echo "=== MEMORIA ==="
free -h | grep Mem

echo "=== CONEXIONES ACTIVAS ==="
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | tail -1

echo "✓ Revisión completada"
```

**Acciones si algo falla:**
- ❌ Servicio no running: `sudo systemctl restart felix-api`
- ❌ Health check falla: Ver logs → `sudo tail -50 /var/log/felix/error.log`
- ❌ BD no conecta: `sudo systemctl restart postgresql`
- ❌ Disco <20% libre: Aumentar almacenamiento DigitalOcean

---

## 🔍 VERIFICACIÓN SEMANAL (30 min)

**Cada lunes a las 8 AM:**

### 1. Revisar Logs
```bash
# Errores de la semana
sudo grep -i error /var/log/felix/error.log | tail -20

# Patrones de error
sudo grep -i "exception\|error\|failed" /var/log/felix/error.log | sort | uniq -c | sort -rn | head -10
```

**Acciones:**
- Investigar cualquier error repetido
- Crear issue en GitHub si es necesario
- Documentar en `TROUBLESHOOTING_LOG.md`

### 2. Revisar Métricas de Base de Datos
```bash
# Tamaño de BD
sudo -u postgres psql -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database ORDER BY pg_database_size DESC;"

# Tabla más grande
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size DESC LIMIT 10;"
```

**Acciones:**
- Si BD crece > 50%, revisar políticas de retention
- Ejecutar VACUUM si está fragmentada

### 3. Revisar Performance
```bash
# Queries lentas (PostgreSQL log)
sudo grep "duration:" /var/log/postgresql/postgresql.log | grep -oP "duration: \K[0-9]+\.[0-9]+" | awk '{if($1 > 5000) print}' | wc -l

# Requests lentos (Nginx)
sudo awk '{print $NF}' /var/log/nginx/felix_access.log | sort -rn | head -20
```

**Acciones:**
- Si hay queries lentas: Añadir índices
- Si hay requests lentos: Revisar qué endpoint es

### 4. Revisar Logs de Uptime Kuma
```bash
# Acceder a: https://tu-dominio.com:3001
# Revisar que el health check no tuvo downtime
# Si hay downtime: investigar qué pasó ese momento
```

### 5. Backup Manual
```bash
# Crear backup
sudo -u postgres pg_dump felix_prod > ~/backup/felix_$(date +%Y%m%d_%H%M%S).sql

# Verificar que se creó
ls -lh ~/backup/*.sql | tail -5

# Copiar a lugar seguro (USB, Dropbox, etc.)
```

---

## 🛠️ PROCEDIMIENTOS DE MANTENIMIENTO

### Actualizar Código Segura (Cada 2-4 semanas)

```bash
# 1. Hacer backup
sudo -u postgres pg_dump felix_prod > ~/backup/felix_pre_update.sql

# 2. Verificar cambios pendientes
cd /opt/felix-automation
git status
git diff

# 3. Actualizar código (fuera de horas pico)
git pull origin main

# 4. Instalar nuevas dependencias (si las hay)
source venv/bin/activate
pip install -r requirements.txt

# 5. Ejecutar migraciones (si existen)
# python scripts/migrate_to_postgresql.py <DATABASE_URL>

# 6. Reiniciar servicios
sudo systemctl restart felix-api

# 7. Verificar que funciona
curl -s https://tu-dominio.com/health | jq
```

**Rollback si falla:**
```bash
git checkout main~1
pip install -r requirements.txt
sudo systemctl restart felix-api
# Restaurar BD si fue migración:
# pg_restore -U felix_user -d felix_prod ~/backup/felix_pre_update.sql
```

### Limpiar Logs Antiguos (Cada 30 días)

```bash
# Logs automáticamente se rotan, pero verificar:
ls -lah /var/log/felix/

# Si hay muchos logs viejos:
sudo find /var/log/felix -name "*.log.*" -mtime +30 -delete

# O forzar rotación:
sudo logrotate -f /etc/logrotate.d/felix
```

### Optimizar Base de Datos (Cada mes)

```bash
# VACUUM (libera espacio)
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "VACUUM ANALYZE;"

# Revisar índices
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "\d+ clients"

# Si hay índices no usados:
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
ORDER BY pg_relation_size DESC;"
```

### Renovar Certificado SSL (Automático, pero verificar)

```bash
# Certbot debería auto-renovar 30 días antes de expiración
# Verificar que está activo:
sudo systemctl status certbot.timer

# Ver próxima renovación:
sudo systemctl list-timers --all | grep certbot

# Probar manual (dry-run):
sudo certbot renew --dry-run

# Si falla, ver logs:
sudo journalctl -u certbot -n 20
```

---

## 🚨 PROCEDIMIENTOS DE EMERGENCIA

### Sistema Completamente Down

```bash
# 1. Verificar qué está offline
sudo systemctl status felix-api | grep Active
sudo systemctl status postgresql | grep Active
sudo systemctl status nginx | grep Active

# 2. Reiniciar uno por uno (en orden)
sudo systemctl restart postgresql
sleep 5
sudo systemctl restart felix-api
sudo systemctl restart nginx

# 3. Verificar
curl -s https://tu-dominio.com/health

# 4. Si sigue fallando: Ver logs
sudo tail -100 /var/log/felix/error.log
sudo tail -100 /var/log/postgresql/postgresql.log

# 5. Última opción: Reboot del servidor
# sudo reboot
# (Evitar si es posible, servicios se inician automáticamente)
```

### Base de Datos Corrupta

```bash
# 1. Detener aplicación
sudo systemctl stop felix-api

# 2. Intentar reparar
sudo -u postgres psql -d felix_prod -c "CHECK DATABASE;"

# 3. Si sigue fallando, restaurar desde backup
sudo -u postgres dropdb felix_prod
sudo -u postgres createdb -O felix_user felix_prod

# 4. Restaurar datos
sudo -u postgres pg_restore -d felix_prod ~/backup/felix_YYYYMMDD.sql

# 5. Reiniciar aplicación
sudo systemctl start felix-api

# 6. Verificar
curl -s https://tu-dominio.com/health
```

### Disco Lleno

```bash
# 1. Identificar qué ocupa espacio
sudo du -sh /opt/felix-automation/* | sort -rh

# 2. Limpiar logs viejos
sudo find /var/log/felix -type f -mtime +30 -delete

# 3. Limpiar cache de Python
sudo find /opt/felix-automation -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# 4. Si sigue lleno:
# - Añadir volumen en DigitalOcean
# - O reducir retention de logs en /etc/logrotate.d/felix
```

### Alto Uso de CPU/Memoria

```bash
# 1. Identificar proceso
top -b -n 1 | head -20

# 2. Si es felix-api que consume mucho:
sudo systemctl restart felix-api
sleep 5
top -b -n 1 | grep felix

# 3. Si persiste, revisar si hay query infinita:
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "\x" -c "SELECT pid, query, query_start FROM pg_stat_activity WHERE state = 'active' AND query NOT LIKE '%pg_stat%' LIMIT 5;"

# 4. Si hay query loca, matarla:
# sudo -u postgres psql -c "SELECT pg_terminate_backend(<pid>);"

# 5. Revisar logs de errores
sudo tail -100 /var/log/felix/error.log
```

### Pérdida de Email Enviado

```bash
# Felix guarda registro de todos los emails en BD
# Buscar en tabla email_logs:

sudo -u felix psql -h localhost -U felix_user -d felix_prod << EOF
SELECT id, client_id, email, status, created_at 
FROM email_logs 
WHERE created_at > NOW() - INTERVAL '1 day'
ORDER BY created_at DESC 
LIMIT 20;

-- Si necesitas re-enviar:
-- UPDATE email_logs SET status = 'pending' WHERE id = <email_id>;
