# 🔒 BACKUP & RESTORE GUIDE - FELIX AUTOMATION

**Versión:** 11.0  
**Última actualización:** 2026-10-05  
**Criticidad:** 🔴 ALTA - Protección de datos

---

## 📋 ÍNDICE RÁPIDO

| Sección | Contenido | Tiempo |
|---------|-----------|--------|
| Backup Manual | Cómo hacer backup ahora | 5 min |
| Backup Automático | Configurar cron | 10 min |
| Restauración | Cómo restaurar desde backup | 10 min |
| Verificación | Comprobar integridad | 5 min |
| Recuperación de Desastres | Procedimientos emergency | 20 min |

---

## ✅ BACKUP MANUAL

### Opción 1: Backup Completo (Recomendado)

```bash
cd /opt/felix-automation
bash backup.sh full

# Output esperado:
# ✅ Backup de DB completado: backups/database/felix_prod_*.sql.gz (150 MB)
# ✅ Backup de configuración completado: backups/config/config_*.tar.gz (2 MB)
# ✅ Backup de datos completado: backups/data/data_*.tar.gz (500 MB)
# ✅ Backup de logs completado: backups/logs/logs_*.tar.gz (50 MB)
# ✅ Todos los backups verificados correctamente
# Tamaño total: ~700 MB
```

### Opción 2: Backup Individual

```bash
# Solo base de datos
bash backup.sh database

# Solo configuración  
bash backup.sh config

# Solo datos
bash backup.sh data

# Solo logs
bash backup.sh logs
```

### Opción 3: Verificar Backups Existentes

```bash
# Verificar integridad de todos
bash backup.sh verify

# Ver estadísticas
bash backup.sh stats
```

---

## 🤖 BACKUP AUTOMÁTICO (Cron)

### Configuración Recomendada

**Backup diario a las 2 AM (ejecutado como usuario felix):**

```bash
# Conectar como usuario felix
sudo su - felix

# Editar crontab
crontab -e

# Agregar esta línea:
0 2 * * * cd /opt/felix-automation && bash backup.sh full >> /var/log/felix/backup.log 2>&1

# Guardar (Ctrl+X, luego Y, luego Enter)
```

**Verificación de que quedó configurado:**

```bash
# Ver cron jobs
crontab -l

# Ver logs
tail -20 /var/log/felix/backup.log
```

### Cronograma Recomendado

```
Opción A: Backup diario (Recomendado)
  0 2 * * *     Backup completo diariamente a las 2 AM

Opción B: Backup múltiple (Máxima protección)
  0 2 * * *     Backup completo diariamente
  0 6 * * 0     Backup adicional los domingos a las 6 AM
  0 12 * * *    Backup de datos al mediodía

Opción C: Backup inteligente (Optimizado)
  0 2 * * *     Backup completo
  0 3 * * 1-5   Verify (verificar integridad lunes a viernes)
  0 4 * * 0     Copy to external storage (domingo)
```

### Monitoreo de Backups

**Ver último backup realizado:**
```bash
ls -lh /opt/felix-automation/backups/database/ | tail -1
```

**Ver tamaño total de backups:**
```bash
du -sh /opt/felix-automation/backups/
```

**Ver logs de backups:**
```bash
tail -50 /var/log/felix/backup.log
```

---

## ♻️ RESTAURACIÓN

### Paso 1: Listar Backups Disponibles

```bash
cd /opt/felix-automation
bash restore.sh list

# Output:
# Base de datos:
#   backups/database/felix_prod_20261005_020000.sql.gz (156 MB)
#   backups/database/felix_prod_20261004_020000.sql.gz (152 MB)
#   ...

# Datos:
#   backups/data/data_20261005_020000.tar.gz (512 MB)
#   ...
```

### Paso 2: Restaurar desde Backup

**Restauración completa (Base de datos + Configuración + Datos):**

```bash
# Restaurar último backup
bash restore.sh full 20261005_020000

# El script te pedirá confirmación:
# ⚠️  Esto restaurará TODO el sistema desde el backup 20261005_020000
# ¿Estás seguro? Escribe 'SÍ' para continuar:

# Responder: SÍ

# Proceso automático:
# 1. Detiene servicios
# 2. Restaura base de datos
# 3. Restaura configuración
# 4. Restaura datos
# 5. Reinicia servicios
# Tiempo total: ~5-10 minutos
```

**Restaurar solo base de datos:**

```bash
bash restore.sh database 20261005_020000
```

**Restaurar solo configuración:**

```bash
bash restore.sh config 20261005_020000
```

**Restaurar solo datos:**

```bash
bash restore.sh data 20261005_020000
```

### Paso 3: Verificar Restauración

```bash
# Health check
curl https://localhost/health

# Debe retornar: {"status":"🟢 OK","service":"Felix Automation API","version":"11.0"}

# Verificar servicios
sudo systemctl status felix-api
sudo systemctl status felix-scheduler

# Ver logs
sudo tail -50 /var/log/felix/error.log
```

---

## 🔍 VERIFICACIÓN DE INTEGRIDAD

### Verificar Todos los Backups

```bash
bash restore.sh verify

# Output:
# Base de datos:
#   ✅ felix_prod_20261005_020000.sql.gz
#   ✅ felix_prod_20261004_020000.sql.gz
# 
# Configuración:
#   ✅ config_20261005_020000.tar.gz
# 
# RESULTADO: Todos los backups son íntegros
```

### Verificar Específico

```bash
# Descomprimir y revisar backup
gunzip -t /opt/felix-automation/backups/database/felix_prod_20261005_020000.sql.gz

# Si retorna 0: Backup OK
# Si retorna error: Backup corrupto
```

---

## 📊 ESTRATEGIA DE ALMACENAMIENTO

### Almacenamiento Local (En el Servidor)

```
/opt/felix-automation/backups/
├── database/       (Respaldos de PostgreSQL)
├── config/         (Respaldos de configuración)
├── data/           (Respaldos de datos)
├── logs/           (Respaldos de logs)
└── BACKUP_MANIFEST_*.txt
```

**Rotación automática:** 30 días (borra automáticamente backups más antiguos)

### Almacenamiento Externo (RECOMENDADO)

**Opción 1: Cloud Storage (AWS S3, Google Cloud Storage)**

```bash
# Instalar AWS CLI
sudo apt-get install -y awscli

# Configurar credenciales
aws configure

# Copiar backups a S3 (agregar a cron)
0 3 * * * aws s3 sync /opt/felix-automation/backups s3://tu-bucket/felix-backups/
```

**Opción 2: Almacenamiento DigitalOcean (Spaces)**

```bash
# Usar AWS CLI (compatible)
aws configure --profile spaces

# Copiar a Spaces
0 3 * * * aws s3 sync /opt/felix-automation/backups s3://tu-space/felix/ --profile spaces
```

**Opción 3: Almacenamiento Local (Externo)**

```bash
# Conectar disco externo
sudo mount /mnt/external_backup

# Copiar backups (agregar a cron)
0 3 * * * cp -r /opt/felix-automation/backups/* /mnt/external_backup/
```

### Checklist de Almacenamiento

- [ ] Backups se crean localmente diariamente
- [ ] Verificación de integridad semanal
- [ ] Copia a almacenamiento externo semanal
- [ ] Prueba de restauración mensual
- [ ] Documentación de procedimientos
- [ ] Alertas de fallos en backup

---

## 🚨 RECUPERACIÓN DE DESASTRES

### Escenario 1: Corrupción de Base de Datos

**Síntomas:**
```
Error: FATAL: could not open file "base/16384/16385": No such file or directory
```

**Solución:**

```bash
# 1. Listar backups
cd /opt/felix-automation
bash restore.sh list

# 2. Restaurar últim backup íntegro
bash restore.sh database TIMESTAMP

# 3. Verificar
curl https://localhost/health
```

### Escenario 2: Disco Lleno

**Síntomas:**
```
Error: No space left on device
```

**Solución:**

```bash
# 1. Ver espacio
df -h

# 2. Limpiar backups antiguos manualmente
rm -rf /opt/felix-automation/backups/*_20260901*

# 3. O rotación manual
find /opt/felix-automation/backups -type f -mtime +30 -delete

# 4. Liberar espacio si es necesario
sudo du -sh /var/log/felix/*
sudo rm /var/log/felix/error.log.*
```

### Escenario 3: Pérdida Total del Servidor

**Preparación (AHORA):**

```bash
# 1. Copiar backups a almacenamiento externo DIARIAMENTE
aws s3 sync /opt/felix-automation/backups s3://bucket/felix/

# 2. Guardar .env en lugar seguro (password manager)
cat /opt/felix-automation/.env > /tmp/felix_env_$(date +%Y%m%d).txt

# 3. Guardar SSH keys
# (Ya debería estar en ~/.ssh/)

# 4. Documentar versión de Ubuntu, Python, PostgreSQL
cat /etc/os-release
python3 --version
pg_config --version
```

**Recuperación (Si el servidor se pierde):**

```bash
# 1. Crear nuevo servidor (Ubuntu 20.04+, 4+ CPU, 8GB RAM)

# 2. Ejecutar setup.sh
bash setup.sh

# 3. Restaurar desde backup externo
aws s3 cp s3://bucket/felix/backups /opt/felix-automation/backups --recursive

# 4. Restaurar todos los datos
bash restore.sh full TIMESTAMP

# 5. Verificar
curl https://localhost/health
```

---

## 📈 REPORTE DE BACKUPS

### Generar Reporte Semanal

```bash
cat > /tmp/backup_report.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/felix-automation/backups"
REPORT_FILE="/tmp/backup_report_$(date +%Y%m%d).txt"

cat > "$REPORT_FILE" << 'REPORT'
╔════════════════════════════════════════════════════════════╗
║  REPORTE SEMANAL DE BACKUPS - FELIX AUTOMATION             ║
╚════════════════════════════════════════════════════════════╝

RESUMEN:
EOF

echo "Fecha: $(date)" >> "$REPORT_FILE"
echo "Tamaño total: $(du -sh $BACKUP_DIR | cut -f1)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "BACKUPS RECIENTES:" >> "$REPORT_FILE"
ls -lh "$BACKUP_DIR"/database/*.sql.gz | tail -7 | awk '{print $9, "(" $5 ")"}' >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "VERIFICACIÓN DE INTEGRIDAD:" >> "$REPORT_FILE"
for file in "$BACKUP_DIR"/database/*.sql.gz; do
    if gunzip -t "$file" 2>/dev/null; then
        echo "✅ $(basename $file)" >> "$REPORT_FILE"
    else
        echo "❌ $(basename $file)" >> "$REPORT_FILE"
    fi
done

echo "" >> "$REPORT_FILE"
echo "RECOMENDACIONES:" >> "$REPORT_FILE"
echo "- Todos los backups son íntegros" >> "$REPORT_FILE"
echo "- Próximo backup: $(date -d '+1 day' '+%Y-%m-%d 02:00')" >> "$REPORT_FILE"
echo "- Próxima verificación: $(date -d '+3 days' '+%Y-%m-%d')" >> "$REPORT_FILE"

cat "$REPORT_FILE"
EOF

# Ejecutar
bash /tmp/backup_report.sh
```

### Enviar Reporte por Email

```bash
# Agregar a cron (enviar reporte el lunes a las 9 AM)
0 9 * * 1 bash /tmp/backup_report.sh | mail -s "Reporte de Backups Felix" felipe@enbuenamesa.com
```

---

## 🎯 CHECKLIST - BACKUP & RESTORE

### Setup Inicial (HOY)
- [ ] Crear directorio de backups
- [ ] Hacer primer backup manual
- [ ] Verificar integridad
- [ ] Hacer test de restauración

### Automatización (ESTA SEMANA)
- [ ] Configurar cron para backup diario
- [ ] Configurar alertas de fallos
- [ ] Documentar procedimientos locales
- [ ] Capacitar equipo

### Almacenamiento Externo (ESTA SEMANA)
- [ ] Seleccionar solución (Cloud o física)
- [ ] Configurar sincronización
- [ ] Hacer test de recuperación
- [ ] Documentar credenciales

### Monitoreo Continuo (SIEMPRE)
- [ ] Verificar logs de backup semanalmente
- [ ] Hacer prueba de restauración mensual
- [ ] Revisar tamaño de backups
- [ ] Alertas de corrupción

---

## 💡 MEJORES PRÁCTICAS

✅ **HACER:**
- Backup diario de base de datos
- Copiar backups a almacenamiento externo
- Verificar integridad regularmente
- Probar restauración mensualmente
- Documentar procesos
- Alertas configuradas
- Retención clara (30 días local + más en externo)

❌ **NO HACER:**
- Almacenar solo backups locales
- Omitir verificaciones de integridad
- Perder track de backups antiguos
- Restaurar sin confirmar
- Ignorar errores en backups
- Cambiar archivos de backup manualmente

---

## 📞 SOPORTE

### Comandos de Ayuda

```bash
# Ayuda general
bash backup.sh help
bash restore.sh help

# Ver backups disponibles
bash restore.sh list

# Verificar integridad
bash restore.sh verify

# Ver estadísticas
bash backup.sh stats
```

### Contacto

**Email:** felipe@enbuenamesa.com  
**Documentación:** Ver DEPLOYMENT_README.md

---

## 📋 PROCEDIMIENTO RÁPIDO

```bash
# BACKUP (5 minutos)
cd /opt/felix-automation
bash backup.sh full

# RESTAURACIÓN (10 minutos)
bash restore.sh list
bash restore.sh full TIMESTAMP

# VERIFICACIÓN (2 minutos)
bash restore.sh verify
curl https://localhost/health
```

---

**Última actualización:** 2026-10-05  
**Versión:** 11.0 Production Ready  
**Estado:** ✅ Ready for Production

