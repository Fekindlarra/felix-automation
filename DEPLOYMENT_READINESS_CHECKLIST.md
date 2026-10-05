# 🚀 CHECKLIST DE DESPLIEGUE A PRODUCCIÓN
## Felix Automation FASE 11 - Production Ready

**Versión:** 11.0  
**Fecha:** 2026-10-05  
**Estado:** ✅ Listo para Despliegue  
**Duración Estimada:** 2-3 horas desde servidor vacío

---

## 📋 ÍNDICE

1. [Pre-Despliegue: Checklist de Preparación](#pre-despliegue-checklist-de-preparación)
2. [Fase 1: Preparación del Servidor](#fase-1-preparación-del-servidor)
3. [Fase 2: Ejecución del Setup](#fase-2-ejecución-del-setup)
4. [Fase 3: Configuración de Entorno](#fase-3-configuración-de-entorno)
5. [Fase 4: Verificación Post-Deployment](#fase-4-verificación-post-deployment)
6. [Fase 5: Monitoreo y Validación](#fase-5-monitoreo-y-validación)
7. [Troubleshooting Rápido](#troubleshooting-rápido)

---

## PRE-DESPLIEGUE: CHECKLIST DE PREPARACIÓN

### ✅ CONFIRMACIONES ANTES DE COMENZAR

- [ ] **DigitalOcean droplet creado y activo**
  - [ ] IP asignada
  - [ ] SSH acceso verificado
  - [ ] Root password seguro (cambiar en primera conexión)
  - [ ] Firewall configurado (puertos 22, 80, 443 abiertos)

- [ ] **GitHub Repository listo**
  - [ ] Repositorio clone-able vía HTTPS o SSH
  - [ ] `.env.example` presente en raíz
  - [ ] `setup.sh` presente en raíz
  - [ ] `requirements.txt` actualizado con todas las dependencias

- [ ] **Credenciales de Servicios Externos preparadas**
  - [ ] SendGrid API key disponible
  - [ ] Shopify API credentials (si se usará White-Box)
  - [ ] Jumpseller API key (si se usará White-Box)
  - [ ] GitHub personal access token (si es repositorio privado)

- [ ] **Configuración de Dominio**
  - [ ] Dominio registrado
  - [ ] DNS apuntando al IP de DigitalOcean
  - [ ] Propagación de DNS verificada (puede tardar 24h)
  - [ ] Email para Certbot preparado

- [ ] **Documentación descargada localmente**
  - [ ] `GUIA_RAPIDA_DESPLIEGUE.md`
  - [ ] `DEPLOYMENT_GUIDE.md`
  - [ ] `MONITORING_PLAN.md`
  - [ ] `setup.sh`
  - [ ] `config.yaml`

### ⏱️ TIEMPO ESTIMADO

| Fase | Tiempo | Notas |
|------|--------|-------|
| Pre-Despliegue (esta sección) | 30 min | Verificaciones |
| Conexión SSH y Setup | 45 min | Ejecución de setup.sh |
| Configuración de Entorno | 30 min | Edición de .env |
| Verificación Post-Deploy | 30 min | Tests y health checks |
| Monitoreo y SSL | 30 min | Certbot + Uptime Kuma |
| **TOTAL** | **2.5-3 horas** | Primer deployment |

---

## FASE 1: PREPARACIÓN DEL SERVIDOR

### PASO 1.1: Conectar al Servidor

```bash
# Reemplazar con IP real de DigitalOcean
ssh root@<DROPLET_IP>

# En primera conexión, cambiar contraseña
passwd
```

**✓ Verificación:**
```bash
# Debe mostrar Ubuntu 20.04 o superior
uname -a
cat /etc/os-release
```

### PASO 1.2: Crear Usuario No-Root (Seguridad)

```bash
# Crear usuario con sudo
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy

# Copiar SSH key (opcional pero recomendado)
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy chmod 700 /home/deploy/.ssh

# Desde tu máquina local:
# ssh-copy-id -i ~/.ssh/id_rsa.pub deploy@<DROPLET_IP>
```

**✓ Verificación:**
```bash
su - deploy
sudo whoami  # Debe retornar 'root'
```

### PASO 1.3: Actualizar Sistema

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

**✓ Verificación:**
```bash
sudo apt-get upgrade -y --simulate  # No debe haber actualizaciones pendientes
```

### PASO 1.4: Clonar Repositorio

```bash
cd /home/deploy
git clone <REPO_URL> felix-automation
cd felix-automation

# Verificar que has clonado correctamente
ls -la | grep -E "(setup.sh|requirements.txt|.env.example)"
```

**✓ Verificación:**
```bash
# Debe existir:
# - setup.sh
# - requirements.txt
# - .env.example
# - backend/app.py
ls -la
```

---

## FASE 2: EJECUCIÓN DEL SETUP

### PASO 2.1: Revisar setup.sh

```bash
# Revisar el contenido (es seguro)
less setup.sh

# O verifica que tiene 18 pasos
grep "^log_info" setup.sh | wc -l  # Debe mostrar ~18
```

### PASO 2.2: Ejecutar Setup Automatizado

```bash
# Desde /home/deploy/felix-automation
cd /home/deploy/felix-automation

# Ejecutar setup (requiere sudo)
sudo bash setup.sh

# IMPORTANTE: Este script:
# - Actualiza el SO
# - Instala Python 3.10, PostgreSQL, Nginx
# - Crea usuario 'felix'
# - Crea virtual environment
# - Configura PostgreSQL
# - Configura Nginx con SSL
# - Crea servicios systemd
# - Tarda 15-30 minutos
```

**✓ Esperado al final:**
```
================================
[✓] SETUP COMPLETADO EXITOSAMENTE ✓
================================

PRÓXIMOS PASOS:
1. Editar variables de entorno: nano /opt/felix-automation/.env
2. Verificar estado: systemctl status felix-api
3. ...
```

### PASO 2.3: Verificar Servicios Creados

```bash
# Listar servicios
sudo systemctl list-unit-files | grep felix

# Debe mostrar:
# - felix-api.service
# - felix-scheduler.service (optional)
```

**✓ Verificación:**
```bash
sudo systemctl is-enabled felix-api.service  # Debe retornar 'enabled'
```

---

## FASE 3: CONFIGURACIÓN DE ENTORNO

### PASO 3.1: Generar Claves de Seguridad

```bash
# SECRET_KEY para JWT
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Guardar output

# WHITEBOX_MASTER_KEY para encriptación Fernet
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Guardar output

# Nota: Si usas python3 sin versión y tienes 3.10+, está bien
# Si no, usa: python3.10 -c "..."
```

### PASO 3.2: Editar Archivo .env

```bash
sudo nano /opt/felix-automation/.env

# Editar estos valores:
```

```ini
# ================== BASE DE DATOS ==================
DATABASE_URL=postgresql://felix_user:STRONG_PASSWORD@localhost:5432/felix_prod

# ================== API & SEGURIDAD ==================
SECRET_KEY=<pegar output del paso 3.1>
WHITEBOX_MASTER_KEY=<pegar segundo output del paso 3.1>

# ================== EMAIL (SendGrid) ==================
SENDGRID_API_KEY=<tu-api-key-de-sendgrid>
SENDGRID_FROM_EMAIL=sales@enbuenamesa.com
SENDGRID_FROM_NAME=En Buena Mesa

# ================== ADMIN ==================
ADMIN_EMAIL=felipe@enbuenamesa.com

# ================== ENVIRONMENT ==================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**Guardar:** `Ctrl+X`, `Y`, `Enter`

### PASO 3.3: Obtener Contraseña de PostgreSQL

El script creó un usuario temporalmente. Necesitas cambiar la contraseña:

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# En la consola psql:
ALTER USER felix_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
\q
```

**Importante:** Use la misma contraseña que en DATABASE_URL del .env

### PASO 3.4: Cambiar Permisos del .env

```bash
# Asegurar que solo el usuario 'felix' pueda leer
sudo chown felix:felix /opt/felix-automation/.env
sudo chmod 600 /opt/felix-automation/.env

# Verificar
ls -la /opt/felix-automation/.env
# Debe mostrar: -rw------- 1 felix felix
```

**✓ Verificación:**
```bash
sudo -u felix cat /opt/felix-automation/.env | head -5
# Debe retornar las primeras líneas del .env
```

---

## FASE 4: VERIFICACIÓN POST-DEPLOYMENT

### PASO 4.1: Iniciar Servicios

```bash
# Felix API
sudo systemctl start felix-api.service
sleep 3

# Verificar estado
sudo systemctl status felix-api.service
```

**✓ Esperado:**
```
Active: active (running)
```

### PASO 4.2: Verificar Health Check

```bash
# Desde local (el servidor aún no tiene SSL configurado)
curl http://localhost:8000/health

# Esperado:
# {"status":"🟢 OK","service":"Felix Automation API","version":"11.0"}
```

**Si falla:**
```bash
# Ver logs
sudo tail -50 /var/log/felix/error.log

# Reintentar
sudo systemctl restart felix-api.service
sleep 2
curl http://localhost:8000/health
```

### PASO 4.3: Verificar Conexión a PostgreSQL

```bash
# Conectar como felix user
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "SELECT COUNT(*) FROM clients;"

# Debería retornar:
# count
# -------
#     0
# (1 row)
```

### PASO 4.4: Ejecutar Test End-to-End

```bash
cd /opt/felix-automation
sudo -u felix source venv/bin/activate

# Ejecutar test
python test_end_to_end_complete.py

# Esperado: 9/10 tests pasando (90% éxito)
```

**Salida esperada:**
```
PASO 1: Inicializar Orchestrador        ✅ PASSED
PASO 2: Seleccionar Cliente             ✅ PASSED
PASO 3: Ejecutar Auditorías             ✅ PASSED
...
PASO 10: Reporte Final                  ✅ PASSED
TASA DE ÉXITO: 90% (9/10)
```

### PASO 4.5: Verificar Nginx

```bash
# Verificar configuración
sudo nginx -t
# Esperado: nginx: configuration file test is successful

# Verificar que está corriendo
sudo systemctl status nginx

# Desde local (HTTP será redirigido a HTTPS)
curl -I http://localhost/
# Esperado: 301 redirection
```

---

## FASE 5: MONITOREO Y VALIDACIÓN

### PASO 5.1: Configurar SSL con Certbot

```bash
# Instalar certificado para tu dominio
sudo certbot certonly --nginx -d tu-dominio.com

# Te pedirá:
# - Email de contacto
# - Aceptar términos
# - Verificar DNS (este proceso tarda)

# Certificado se instala en:
# /etc/letsencrypt/live/tu-dominio.com/
```

**✓ Verificación:**
```bash
sudo ls -la /etc/letsencrypt/live/tu-dominio.com/
# Debe mostrar: fullchain.pem y privkey.pem
```

### PASO 5.2: Actualizar Nginx con SSL

```bash
# Editar configuración de Nginx
sudo nano /etc/nginx/sites-available/felix-automation

# Descomenta estas líneas (líneas 411-412):
# ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

# Reemplazar tu-dominio.com con tu dominio real
```

**Guardar:** `Ctrl+X`, `Y`, `Enter`

```bash
# Verificar configuración
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx
```

**✓ Verificación:**
```bash
# Probar con HTTPS
curl -I https://tu-dominio.com/health
# Esperado: HTTP/2 200
```

### PASO 5.3: Configurar Auto-Renewal de SSL

```bash
# Certbot automáticamente configura renewal via systemd timer
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Verificar
sudo systemctl status certbot.timer
sudo systemctl list-timers --all | grep certbot
```

**✓ Test de renewal:**
```bash
# Simular renewal (sin ejecutar realmente)
sudo certbot renew --dry-run
# Esperado: The following errors were reported... (es normal en dry-run)
```

### PASO 5.4: Configurar Monitoreo con Uptime Kuma (Opción Básica)

```bash
# Instalación rápida en el mismo servidor
sudo docker run -d \
  --name uptime-kuma \
  --restart always \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:latest

# Acceder: https://tu-dominio.com:3001
```

**Nota:** Si Docker no está instalado, ver MONITORING_PLAN.md para Prometheus + Grafana

### PASO 5.5: Verificación Final del Sistema

```bash
# 1. Verificar todos los servicios
sudo systemctl status felix-api.service
sudo systemctl status felix-scheduler.service || echo "Scheduler no configurado"
sudo systemctl status nginx
sudo systemctl status postgresql

# 2. Verificar logs
sudo tail -20 /var/log/felix/error.log

# 3. Verificar endpoints key
curl -s https://tu-dominio.com/health | jq
curl -s https://tu-dominio.com/api/clients | jq

# 4. Verificar base de datos
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "\dt"
# Debe mostrar: 5 tablas (clients, pipeline, audits, email_logs, followups)

# 5. Verificar espacio en disco
df -h /
# Asegurarse de tener >50% libre

# 6. Verificar memoria y CPU
free -h
uptime
```

---

## CHECKLIST FINAL DE DESPLIEGUE

Marcar cada item conforme se completa:

### Infraestructura
- [ ] Droplet DigitalOcean creado y activo
- [ ] SSH acceso verificado
- [ ] Firewall configurado (22, 80, 443)
- [ ] Dominio DNS apuntando correctamente
- [ ] Propagación de DNS completada

### Setup Automatizado
- [ ] Repositorio clonado en /home/deploy/felix-automation
- [ ] setup.sh ejecutado exitosamente
- [ ] 18 pasos completados sin errores críticos
- [ ] Servicios systemd creados (felix-api, felix-scheduler)
- [ ] Nginx instalado y configurado

### Configuración
- [ ] .env editado con valores correctos
- [ ] SECRET_KEY generada e insertada
- [ ] WHITEBOX_MASTER_KEY generada e insertada
- [ ] SENDGRID_API_KEY configurada
- [ ] PostgreSQL password actualizada
- [ ] Permisos .env establecidos (600)

### Verificaciones Post-Deploy
- [ ] Health check retorna 200 OK
- [ ] PostgreSQL conecta correctamente
- [ ] Test end-to-end ejecutado (90%+ éxito)
- [ ] Nginx responde correctamente
- [ ] Logs sin errores críticos
- [ ] Todos los servicios en estado "running"

### SSL y Seguridad
- [ ] Certbot instalado y certificado emitido
- [ ] Nginx actualizado con SSL paths
- [ ] Redirección HTTP→HTTPS funcionando
- [ ] SSL auto-renewal configurado
- [ ] HSTS header presente en respuestas

### Monitoreo
- [ ] Uptime Kuma instalado (o Prometheus)
- [ ] Health check monitor configurado
- [ ] Email alerts configuradas para Felipe
- [ ] Logs rotación configurada (14 días)
- [ ] Dashboard accesible

### Post-Deploy Importante
- [ ] Guardar contraseña de PostgreSQL en lugar seguro
- [ ] Guardar SSH keys en lugar seguro
- [ ] Documentar cualquier cambio realizado
- [ ] Realizar primer backup manual
- [ ] Informar a Felipe que sistema está live
- [ ] Configurar alertas por email

---

## TROUBLESHOOTING RÁPIDO

### "Connection refused" a PostgreSQL
```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Reiniciar
sudo systemctl restart postgresql

# Verificar que usuario existe
sudo -u postgres psql -c "\du"
```

### "Port 8000 already in use"
```bash
# Encontrar proceso
sudo lsof -i :8000

# Matar si es necesario (o reiniciar servicio)
sudo systemctl restart felix-api
```

### Setup.sh falló a mitad
```bash
# No hay problema, puede ejecutarse de nuevo
sudo bash setup.sh

# El script es idempotente (safe de ejecutar múltiples veces)
```

### SSL Certificate not found
```bash
# Rerun certbot
sudo certbot certonly --nginx -d tu-dominio.com --force-renewal

# Verificar ruta
sudo ls -la /etc/letsencrypt/live/tu-dominio.com/

# Editar Nginx si es necesario
sudo nano /etc/nginx/sites-available/felix-automation
# Verificar que ssl_certificate paths son correctos
```

### API retorna errores 500
```bash
# Ver logs detallados
sudo tail -100 /var/log/felix/error.log

# Posibles causas:
# - Variables de entorno incompletas (ver .env)
# - PostgreSQL no conecta (verificar DATABASE_URL)
# - Módulos Python no instalados (pip install -r requirements.txt)

# Reiniciar después de fix
sudo systemctl restart felix-api
```

### Nginx no inicia
```bash
# Verificar sintaxis
sudo nginx -t

# Ver errors
sudo systemctl status nginx

# Verificar logs
sudo tail -20 /var/log/nginx/error.log

# Reintentar
sudo systemctl restart nginx
```

---

## DOCUMENTACIÓN DE REFERENCIA

| Documento | Usar Para |
|-----------|-----------|
| `GUIA_RAPIDA_DESPLIEGUE.md` | 10 pasos manuales del deployment |
| `DEPLOYMENT_GUIDE.md` | Guía detallada de configuración |
| `MONITORING_PLAN.md` | Configuración avanzada de monitoreo |
| `PRODUCTION_READY_SUMMARY.md` | Resumen de todo lo que está implementado |
| `PERFORMANCE_TESTING.md` | Cómo ejecutar load tests |
| `.github/workflows/production.yml` | CI/CD pipeline para deployments futuros |

---

## COMANDOS ÚTILES POST-DEPLOYMENT

```bash
# Ver status de todos los servicios
sudo systemctl status felix-* postgresql nginx

# Ver logs en tiempo real
sudo journalctl -u felix-api -f

# Reiniciar la aplicación
sudo systemctl restart felix-api

# Ejecutar test sin validación
cd /opt/felix-automation && python test_end_to_end_complete.py

# Backup de base de datos
sudo -u postgres pg_dump felix_prod > ~/felix_prod_backup_$(date +%Y%m%d).sql

# Actualizar código (git pull)
cd /opt/felix-automation && git pull && pip install -r requirements.txt && sudo systemctl restart felix-api

# Ver conexiones PostgreSQL
sudo -u postgres psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

---

## CONTACTO Y SOPORTE

- **Email:** felipe@enbuenamesa.com
- **Repositorio:** Ver GitHub en CI/CD settings
- **Logs:** `/var/log/felix/`
- **Configuración:** `/opt/felix-automation/.env`

---

**Estado:** ✅ Listo para Despliegue  
**Última Actualización:** 2026-10-05  
**Versión:** 11.0 Production Ready  

