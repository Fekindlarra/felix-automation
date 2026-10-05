# ✅ FELIX AUTOMATION - DEPLOYMENT CHECKLIST

**Sistema:** Felix Automation - Sales Pipeline Automation  
**Versión:** 11.0  
**Fases Completadas:** 1-9 (White-Box Audit Integration)  
**Estado:** 🟢 Production-Ready  
**Última Actualización:** 2026-10-05

---

## 📋 PRE-DEPLOYMENT (Antes de ir a Producción)

### Infraestructura
- [ ] Servidor Ubuntu 20.04+ con 4+ CPU, 8GB RAM mínimo
- [ ] PostgreSQL 12+ instalado y corriendo
- [ ] Python 3.11+ con pip y virtualenv
- [ ] 50GB+ disco disponible para backups y datos
- [ ] Conexión a internet estable (HTTP/HTTPS)

### Configuración del Sistema
- [ ] Clonar repositorio en `/opt/felix-automation`
- [ ] Crear usuario `felix` con permisos en directorio
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Generar WHITEBOX_MASTER_KEY para encriptación
  ```bash
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  export WHITEBOX_MASTER_KEY=<key generada>
  ```

### Base de Datos
- [ ] Ejecutar `scripts/init_db.py` para crear schema
- [ ] Ejecutar `bash migrate_database.sh status` para verificar migraciones
- [ ] Crear usuario PostgreSQL `felix_user` con contraseña
- [ ] Crear base de datos `felix_prod`
- [ ] Configurar variables de entorno:
  ```bash
  export DATABASE_URL="postgresql://felix_user:PASSWORD@localhost/felix_prod"
  export SENDGRID_API_KEY="<tu_api_key>"
  export WHITEBOX_MASTER_KEY="<tu_master_key>"
  ```

### Email (SendGrid)
- [ ] Crear cuenta SendGrid y obtener API key
- [ ] Configurar sender email domain verification
- [ ] Probar envío de emails: `python scripts/test_email.py`
- [ ] Configurar variables de entorno

### Seguridad
- [ ] Habilitar HTTPS en el servidor
- [ ] Configurar firewall (puertos 22, 80, 443)
- [ ] Generar SSL certificates
- [ ] Configurar backup automático a almacenamiento externo
- [ ] Revisar logs de seguridad en `/var/log/felix/`

### Monitoreo
- [ ] Configurar alertas por email para errores críticos
- [ ] Configurar rotación de logs (30 días)
- [ ] Verificar Dashboard Administrativo accesible
- [ ] Configura health checks cron job:
  ```bash
  0 * * * * cd /opt/felix-automation && curl https://localhost/health
  ```

---

## 🚀 STARTUP (Iniciar Sistema)

### Fase 1: Inicialización
```bash
cd /opt/felix-automation

# 1. Verificar status
python3 orchestrator.py

# 2. Verificar database
bash migrate_database.sh status

# 3. Verificar integraciones
python3 -c "from whitebox.credentials_manager import CredentialsManager; print('✅ Credentials Manager OK')"
```

### Fase 2: Cargar Datos Iniciales
```bash
# Crear clientes demo
python3 scripts/seed_data.py

# Ejecutar auditorías iniciales
python3 agents/multi_platform_auditor_agent.py
```

### Fase 3: Services
```bash
# Felix API
systemctl start felix-api
systemctl start felix-scheduler

# Verificar
sudo systemctl status felix-api
sudo systemctl status felix-scheduler
```

### Fase 4: Verificar Dashboards
- [ ] Dashboard Interno: `https://localhost:8000/dashboard-interno`
- [ ] Dashboard Cliente: `https://localhost:8000/dashboard-cliente/1`
- [ ] Admin Dashboard: Ver `dashboard.html`

---

## 🔄 OPERACIONES DIARIAS

### Backup Automático (ya configurado)
```bash
# Verificar último backup
ls -lh /opt/felix-automation/backups/database/ | tail -1

# Si necesario, crear backup manual
cd /opt/felix-automation && bash backup.sh full
```

### Monitoreo
- [ ] Revisar Dashboard Administrativo cada mañana
- [ ] Verificar logs de errores: `tail -50 /var/log/felix/error.log`
- [ ] Revisar emails enviados: `tail -20 data/logs/email.log`

### Maintenance
- [ ] Ejecutar health checks cada 4 horas
- [ ] Verificar espacio en disco (df -h)
- [ ] Revisar performance del sistema

---

## 🆙 UPGRADES (Cuando haya nuevas versiones)

### Antes de Upgradear
```bash
# 1. Verificar updates disponibles
bash upgrade.sh check

# 2. Crear backup pre-upgrade
bash backup.sh full

# 3. Verificar sistema
curl https://localhost/health
sudo systemctl status felix-api
```

### Ejecutar Upgrade
```bash
# Upgrade a versión específica
bash upgrade.sh 12.0

# Confirmar con 'SÍ' cuando se pida
```

### Post-Upgrade Validation
```bash
# Verificar health
curl https://localhost/health

# Verificar servicios
sudo systemctl status felix-api
sudo systemctl status felix-scheduler

# Si hay problemas:
bash upgrade.sh rollback
```

---

## 🔐 SEGURIDAD & CREDENCIALES

### White-Box Audits (con acceso a cliente)
1. Cliente proporciona credenciales de manera segura
2. Sistema encripta y almacena en memoria (máx 1 hora)
3. Auditor realiza análisis profundo
4. Credenciales se eliminan automáticamente después
5. Reporte técnico se genera

**IMPORTANTE:** NUNCA loguear credenciales sin encriptar

### Backup de Credenciales
- [ ] Guardar WHITEBOX_MASTER_KEY en password manager
- [ ] Guardar DATABASE_URL de forma segura
- [ ] Guardar SENDGRID_API_KEY de forma segura
- [ ] Copiar variables de entorno a lugar seguro

---

## 📊 MÉTRICAS DE ÉXITO

### Sistema Operativo
- ✅ Todos los servicios online
- ✅ Database connection exitosa
- ✅ 0 errores no-resueltos en logs
- ✅ Disk usage < 80%

### Pipeline de Ventas
- ✅ Auditorías se completan en < 5 segundos
- ✅ Email delivery rate > 95%
- ✅ Lead scoring accuracy > 85%
- ✅ Dashboard actualiza cada hora

### Seguridad
- ✅ Backups automáticos diarios
- ✅ Credenciales siempre encriptadas
- ✅ TTL de credenciales < 1 hora
- ✅ Logs auditados y rotados

---

## 🆘 TROUBLESHOOTING RÁPIDO

### Error: "Connection refused"
```bash
sudo systemctl start postgresql
sleep 10
curl https://localhost/health
```

### Error: "No space left on device"
```bash
df -h
find /opt/felix-automation/backups -mtime +30 -delete
```

### Error: "Permission denied"
```bash
sudo chown -R felix:felix /opt/felix-automation
chmod 755 /opt/felix-automation/*.sh
```

### Sistema lento
```bash
# Verificar proceso CPU
top
# Verificar disk I/O
iostat
# Revisar DB queries lento
tail -50 /var/log/felix/database.log
```

---

## 📞 CONTACTO & SOPORTE

**Email:** felipe@enbuenamesa.com  
**Documentación:** Ver DEPLOYMENT_README.md para detalles completos

---

## ✅ CHECKLIST FINAL (Antes de "Go Live")

- [ ] Infraestructura verified (servidor, DB, discos)
- [ ] Configuración completada (env vars, SSL, firewall)
- [ ] Datos iniciales cargados (clientes demo)
- [ ] Todos los tests pasados (✅ test_end_to_end_complete.py)
- [ ] Backups funcionando
- [ ] Dashboards accesibles
- [ ] Emails se envían correctamente
- [ ] Health checks OK
- [ ] Documentación leída y entendida
- [ ] Equipo capacitado
- [ ] Plan de rollback revisado

---

**🟢 ESTADO: LISTO PARA PRODUCCIÓN**

Toda la infraestructura, seguridad, monitoring y documentación está en place.  
El sistema está completamente automatizado y preparado para escalar.

