# 🔄 UPGRADE & MIGRATION GUIDE - FELIX AUTOMATION

**Versión:** 11.0  
**Última actualización:** 2026-10-05  
**Criticidad:** 🟠 MEDIA - Actualizaciones de sistema

---

## 📋 ÍNDICE RÁPIDO

| Sección | Contenido | Tiempo |
|---------|-----------|--------|
| Upgrade Manual | Cómo actualizar ahora | 10 min |
| Verificar Updates | Ver versiones disponibles | 5 min |
| Migraciones BD | Esquema de datos | 15 min |
| Rollback | Deshacer cambios | 10 min |
| Troubleshooting | Solucionar problemas | 20 min |

---

## 🔍 VERIFICAR ACTUALIZACIONES

### Paso 1: Ver Versión Actual

```bash
cd /opt/felix-automation
cat .version
# Output: 11.0
```

### Paso 2: Verificar Versiones Disponibles

```bash
bash upgrade.sh check

# Output esperado:
# Versión actual:    11.0
# Versión disponible: 12.0
#
# Nueva versión disponible: 12.0
#
# Para actualizar ejecuta:
#   bash upgrade.sh 12.0
```

---

## ⬆️ UPGRADE MANUAL

### Opción 1: Upgrade a Versión Específica

```bash
cd /opt/felix-automation
bash upgrade.sh 12.0

# Output esperado:
# Versión actual:   11.0
# Actualizar a:     12.0
#
# ⚠️  Este proceso actualizará el sistema. Se creará un backup automático.
# ¿Proceder con el upgrade? Escribe 'SÍ' para continuar: SÍ
#
# Proceso automático:
# 1. ✅ Valida compatibilidad de versión
# 2. ✅ Verifica dependencias
# 3. ✅ Crea backup pre-upgrade
# 4. ✅ Actualiza código
# 5. ✅ Actualiza dependencias Python
# 6. ✅ Ejecuta migraciones de base de datos
# 7. ✅ Valida integridad
# 8. ✅ Reinicia servicios
# 9. ✅ Health check exitoso
# 10. ✅ Ejecuta tests
#
# Tiempo total: 15-30 minutos
```

### Opción 2: Shorthand (Directo)

```bash
# Atajo para upgrade.sh 12.0
bash upgrade.sh 12.0

# Idéntico a:
bash upgrade.sh upgrade 12.0
```

---

## 🧪 VERIFICAR ESTADO ANTES DE UPGRADE

### Checklist Pre-Upgrade (5 minutos)

```bash
# 1. Verificar servicios activos
sudo systemctl status felix-api
sudo systemctl status felix-scheduler

# 2. Verificar base de datos
curl https://localhost/health

# 3. Verificar espacio disponible
df -h /opt

# 4. Verificar últimos logs
tail -20 /var/log/felix/error.log

# 5. Crear backup manual (opcional)
cd /opt/felix-automation
bash backup.sh full
```

### Estado de Sistema Óptimo para Upgrade

✅ Servicios activos  
✅ Conexión a BD exitosa  
✅ 5GB+ espacio disponible en /opt  
✅ Sin errores en logs recientes  
✅ 15+ minutos sin interrupciones planificadas

---

## 🗄️ MIGRACIONES DE BASE DE DATOS

### Estado de Migraciones

```bash
cd /opt/felix-automation
bash migrate_database.sh status

# Output:
# Migraciones ejecutadas:
#  migration         | executed_at           | execution_time
# -----------------|-----------------------|---------------
#  20261001_100000_add_users_table        | 2026-10-01 10:00:00 | 2
#  20261002_140000_add_audit_logging      | 2026-10-02 14:00:00 | 5
#
# Migraciones totales: 15
# Migraciones aplicadas: 10
# Migraciones pendientes: 5
```

### Ver Migraciones Pendientes

```bash
bash migrate_database.sh pending

# Output:
# Migraciones pendientes:
#   → 20261005_100000_add_notifications_table
#   → 20261005_120000_add_email_templates
#   → 20261005_150000_optimize_indexes
#   → 20261006_080000_add_backup_retention_policy
#   → 20261006_100000_add_audit_trail
#
# 5 migración(es) pendiente(s)
```

### Ejecutar Migraciones Automáticamente

```bash
bash migrate_database.sh migrate

# Output esperado:
# EJECUTANDO MIGRACIONES
#
# ℹ️  Ejecutando: 20261005_100000_add_notifications_table
# ✅ 20261005_100000_add_notifications_table completada (2s)
#
# ℹ️  Ejecutando: 20261005_120000_add_email_templates
# ✅ 20261005_120000_add_email_templates completada (3s)
#
# ... (resto de migraciones)
#
# ═════════════════════════════════════════════════════════
# RESULTADO DE MIGRACIONES
# ═════════════════════════════════════════════════════════
# Exitosas: 5
# Fallidas: 0
# ✅ Todas las migraciones completadas
```

### Crear Nueva Migración

```bash
bash migrate_database.sh create add_notifications_table

# Output:
# ✅ Migración creada: /opt/felix-automation/migrations/20261005_143000_add_notifications_table.sql
# ℹ️  Rollback creado: /opt/felix-automation/migrations/20261005_143000_add_notifications_table_rollback.sql
# ℹ️  Edita ambos archivos antes de ejecutar

# Editar la migración
nano /opt/felix-automation/migrations/20261005_143000_add_notifications_table.sql

# Agregar en el archivo:
BEGIN;

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'unread',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE INDEX idx_notifications_client_unread ON notifications(client_id, status);

COMMIT;

# Editar el rollback
nano /opt/felix-automation/migrations/20261005_143000_add_notifications_table_rollback.sql

# Agregar:
BEGIN;

DROP TABLE IF EXISTS notifications;

COMMIT;

# Ejecutar
bash migrate_database.sh migrate
```

---

## ↩️ ROLLBACK

### Deshacer Última Migración

```bash
bash migrate_database.sh rollback

# Output:
# ═════════════════════════════════════════════════════════
# ROLLBACK DE MIGRACIÓN
# ═════════════════════════════════════════════════════════
#
# ⚠️  Última migración: 20261005_143000_add_notifications_table
# ¿Deshacer esta migración? Escribe 'SÍ' para confirmar: SÍ
#
# ℹ️  Ejecutando rollback...
# ✅ Rollback completado: 20261005_143000_add_notifications_table
```

### Rollback de Upgrade Automático

```bash
bash upgrade.sh rollback

# Output:
# ═════════════════════════════════════════════════════════
# ROLLBACK A VERSIÓN ANTERIOR
# ═════════════════════════════════════════════════════════
#
# ⚠️  Esto revertirá la instalación a la versión anterior
# ¿Estás seguro? Escribe 'SÍ' para continuar: SÍ
#
# ℹ️  Deteniendo servicios...
# ℹ️  Restaurando desde: /opt/felix-automation/upgrades/pre-upgrade-11.0-to-12.0_20261005_143000
# ℹ️  Reiniciando servicios...
# ✅ Rollback completado exitosamente
```

---

## 🚨 PROBLEMAS Y SOLUCIONES

### Problema 1: "Connection refused" durante Upgrade

**Síntoma:**
```
Error: could not connect to server: Connection refused
```

**Solución:**
```bash
# 1. Verificar PostgreSQL
sudo systemctl status postgresql

# 2. Si no está activo, iniciarlo
sudo systemctl start postgresql

# 3. Esperar 10 segundos
sleep 10

# 4. Reintentar upgrade
bash upgrade.sh 12.0
```

### Problema 2: "Permission denied" en archivos

**Síntoma:**
```
Error: Permission denied (os error 13)
```

**Solución:**
```bash
# 1. Verificar permisos
ls -la /opt/felix-automation/

# 2. Ajustar permisos
sudo chown -R felix:felix /opt/felix-automation
chmod 755 /opt/felix-automation/*.sh

# 3. Reintentar
bash upgrade.sh 12.0
```

### Problema 3: "Migration failed" durante BD migration

**Síntoma:**
```
ERROR: Migración falló: 20261005_120000_add_email_templates
```

**Solución:**
```bash
# 1. Ver logs
tail -50 /opt/felix-automation/migrations/migration_*.log

# 2. Reversar migración problemática
bash migrate_database.sh rollback

# 3. Verificar el archivo SQL
nano /opt/felix-automation/migrations/20261005_120000_add_email_templates.sql

# 4. Corregir errores SQL (sintaxis, tipos de datos, etc.)

# 5. Reintentar
bash migrate_database.sh migrate
```

### Problema 4: "Version mismatch" después de Upgrade

**Síntoma:**
```
⚠️  Versión en .version: 11.0
⚠️  Versión esperada en código: 12.0
```

**Solución:**
```bash
# 1. Actualizar archivo de versión
echo "12.0" > /opt/felix-automation/.version

# 2. Verificar
cat /opt/felix-automation/.version

# 3. Ejecutar health check
curl https://localhost/health
```

### Problema 5: "Out of disk space" durante Backup

**Síntoma:**
```
Error: No space left on device
```

**Solución:**
```bash
# 1. Ver espacio disponible
df -h

# 2. Limpiar backups antiguos
find /opt/felix-automation/backups -type f -mtime +30 -delete

# 3. Limpiar logs
rm /var/log/felix/error.log.*

# 4. Ver espacio nuevamente
df -h

# 5. Reintentar upgrade
bash upgrade.sh 12.0
```

---

## 📋 PROCEDIMIENTO COMPLETO DE UPGRADE

### Paso 1: Preparación (5 minutos)

```bash
# Verificar estado
bash upgrade.sh check

# Verificar sistema
sudo systemctl status felix-api
curl https://localhost/health
df -h /opt
```

### Paso 2: Backup (10 minutos)

```bash
cd /opt/felix-automation
bash backup.sh full
bash backup.sh verify

# Copiar backup a almacenamiento externo
aws s3 sync backups/ s3://tu-bucket/felix-backups/
```

### Paso 3: Upgrade (15-30 minutos)

```bash
bash upgrade.sh 12.0

# Confirmar con 'SÍ' cuando se pida
```

### Paso 4: Verificación (10 minutos)

```bash
# Health check
curl https://localhost/health

# Verificar servicios
sudo systemctl status felix-api
sudo systemctl status felix-scheduler

# Verificar migraciones
bash migrate_database.sh status

# Verificar logs
tail -50 /var/log/felix/error.log
```

### Paso 5: Rollback (si es necesario - 5 minutos)

```bash
# Si algo falla
bash upgrade.sh rollback

# Esperar 30 segundos
sleep 30

# Verificar rollback fue exitoso
curl https://localhost/health
```

---

## 🔄 AUTOMATIZAR UPGRADES

### Agendar Upgrades Automáticos (Recomendado)

```bash
# Conectar como usuario felix
sudo su - felix

# Editar crontab
crontab -e

# Agregar (upgrade cada domingo a las 3 AM):
0 3 * * 0 cd /opt/felix-automation && bash upgrade.sh check >> /var/log/felix/upgrade_check.log 2>&1

# Nota: Esto SOLO hace check, no ejecuta upgrade automáticamente
# Los upgrades requieren confirmación manual
```

### Notificaciones de Updates

```bash
# Crear script de notificación
cat > /opt/felix-automation/check_and_notify.sh << 'EOF'
#!/bin/bash
cd /opt/felix-automation
RESULT=$(bash upgrade.sh check 2>&1)

if echo "$RESULT" | grep -q "Nueva versión disponible"; then
    # Enviar email
    echo "$RESULT" | mail -s "Felix Automation: Nueva versión disponible" felipe@enbuenamesa.com
fi
EOF

# Hacer ejecutable
chmod +x /opt/felix-automation/check_and_notify.sh

# Agendar en crontab
0 9 * * 1 /opt/felix-automation/check_and_notify.sh
```

---

## 📊 HISTORIAL DE UPGRADES

### Ver Reportes de Upgrades

```bash
ls -lh /opt/felix-automation/upgrades/upgrade_report_*.txt

# Ver último reporte
cat /opt/felix-automation/upgrades/upgrade_report_*.txt | tail -1
```

### Ver Logs de Upgrades

```bash
ls -lh /opt/felix-automation/upgrades/upgrade_*.log

# Ver último log
tail -100 /opt/felix-automation/upgrades/upgrade_*.log | tail -1
```

### Mantener Histórico

```bash
# Crear archivo de histórico
cat /opt/felix-automation/upgrades/upgrade_report_*.txt > /opt/felix-automation/UPGRADE_HISTORY.txt

# Ver histórico
cat /opt/felix-automation/UPGRADE_HISTORY.txt
```

---

## 🎯 MEJORES PRÁCTICAS

✅ **HACER:**
- Verificar disponibilidad de updates regularmente
- Crear backup pre-upgrade automático
- Ejecutar en horario fuera de pico
- Verificar logs después de upgrade
- Mantener histórico de upgrades
- Tener rollback plan documentado
- Ejecutar tests post-upgrade

❌ **NO HACER:**
- Upgradear durante horas de trabajo críticas
- Omitir backups pre-upgrade
- Ignorar errores de migración
- Downgrade sin razón válida
- Modificar archivos de migración después de ejecutar
- Perder histórico de upgrades

---

## 📞 COMANDOS RÁPIDOS

### Upgrade

```bash
# Verificar updates disponibles
bash upgrade.sh check

# Actualizar a versión específica
bash upgrade.sh 12.0

# Ver ayuda de upgrade
bash upgrade.sh help

# Rollback
bash upgrade.sh rollback
```

### Migraciones

```bash
# Ver estado
bash migrate_database.sh status

# Ver pendientes
bash migrate_database.sh pending

# Ejecutar todas
bash migrate_database.sh migrate

# Crear nueva
bash migrate_database.sh create nombre

# Deshacer última
bash migrate_database.sh rollback

# Verificar integridad
bash migrate_database.sh verify

# Ver ayuda
bash migrate_database.sh help
```

---

## 🔐 CONSIDERACIONES DE SEGURIDAD

✅ **Implementado:**
- Backups automáticos pre-upgrade
- Confirmación manual requerida
- Validación de versión
- Verificación de dependencias
- Health checks post-upgrade
- Logs de auditoría completos
- Rollback automático en caso de error

---

## 📈 MONITOREO POST-UPGRADE

### Checklist de Post-Upgrade

```bash
# 1. Verificar servicios
sudo systemctl status felix-api
sudo systemctl status felix-scheduler

# 2. Health check
curl https://localhost/health

# 3. Revisar logs
tail -100 /var/log/felix/error.log
tail -100 /var/log/felix/access.log

# 4. Verificar migraciones
bash migrate_database.sh status

# 5. Tests básicos
cd /opt/felix-automation/tests
python3 -m pytest test_api.py -v

# 6. Verificar data
psql -U felix_user -d felix_prod -c "SELECT COUNT(*) FROM clients;"
```

---

**Última actualización:** 2026-10-05  
**Versión:** 11.0  
**Estado:** ✅ Ready for Production
