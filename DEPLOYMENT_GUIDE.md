# 🚀 GUÍA DE DESPLIEGUE A PRODUCCIÓN
## Felix Automation - Complete Sales Automation Platform

**Versión:** FASE 11 Complete  
**Fecha:** 2026-10-05  
**Estado:** Ready for Deployment  

---

## 📋 ÍNDICE

1. [Pre-Requisitos](#pre-requisitos)
2. [Variables de Entorno](#variables-de-entorno)
3. [Setup de Base de Datos](#setup-de-base-de-datos)
4. [Configuración de Servicios](#configuración-de-servicios)
5. [Despliegue Backend](#despliegue-backend)
6. [Despliegue Frontend](#despliegue-frontend)
7. [Verificación de Producción](#verificación-de-producción)
8. [Monitoreo y Alertas](#monitoreo-y-alertas)
9. [Rollback de Emergencia](#rollback-de-emergencia)

---

## PRE-REQUISITOS

### 1. Servidor/Host
```
- Mínimo: 2 CPU, 4GB RAM
- Recomendado: 4 CPU, 8GB RAM
- SO: Linux (Ubuntu 20.04+) o Docker
- Acceso SSH con sudo
```

### 2. Software Requerido
```bash
# Python
python3 --version  # >= 3.10

# Package Manager
pip install --upgrade pip

# Git
git --version

# Database (PostgreSQL)
psql --version  # >= 12

# Docker (opcional pero recomendado)
docker --version
```

### 3. Cuentas de Servicio Externo
- ✅ SendGrid (API key)
- ✅ Shopify App (OAuth credentials)
- ✅ Jumpseller API (API key + secret)
- ✅ GitHub (para CI/CD)

---

## VARIABLES DE ENTORNO

### 1. Crear archivo `.env`

```bash
# Base de Datos
DATABASE_URL=postgresql://user:password@localhost:5432/felix_prod
DATABASE_POOL_SIZE=20
DATABASE_ECHO=false

# Backend API
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_WORKERS=4
BACKEND_LOG_LEVEL=INFO

# Seguridad
SECRET_KEY=<generar con: python -c "import secrets; print(secrets.token_urlsafe(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Admin
ADMIN_EMAIL=felipe@enbuenamesa.com
ADMIN_PASSWORD=<usar variable de entorno, no hardcodear>

# SendGrid
SENDGRID_API_KEY=<tu-api-key>
SENDGRID_FROM_EMAIL=sales@enbuenamesa.com
SENDGRID_FROM_NAME="En Buena Mesa"

# Shopify
SHOPIFY_API_KEY=<tu-api-key>
SHOPIFY_API_SECRET=<tu-api-secret>
SHOPIFY_API_VERSION=2024-01

# Jumpseller
JUMPSELLER_API_KEY=<tu-api-key>
JUMPSELLER_API_SECRET=<tu-api-secret>

# White-Box Audits
WHITEBOX_MASTER_KEY=<generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
WHITEBOX_TTL_SECONDS=3600
WHITEBOX_CLEANUP_INTERVAL=30

# Analytics
ANALYTICS_RETENTION_DAYS=365
ANALYTICS_BATCH_SIZE=100

# WebSocket
WEBSOCKET_ENABLED=true
WEBSOCKET_PING_INTERVAL=30

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 2. Proteger el archivo
```bash
chmod 600 .env
```

### 3. Variables en CI/CD (GitHub Actions, etc.)
```
Copiar valores sensibles a CI/CD secrets, NO al archivo .env
```

---

## SETUP DE BASE DE DATOS

### 1. Instalar PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Crear Base de Datos
```bash
# Conectar como postgres
sudo -u postgres psql

# SQL Commands:
CREATE USER felix_user WITH PASSWORD 'strong_password_here';
CREATE DATABASE felix_prod OWNER felix_user;
GRANT ALL PRIVILEGES ON DATABASE felix_prod TO felix_user;

# Salir
\q
```

### 3. Migrar datos desde SQLite
```bash
# Desde directorio del proyecto
python scripts/migrate_sqlite_to_postgres.py \
  --source database.sqlite \
  --target postgresql://felix_user:password@localhost:5432/felix_prod
```

### 4. Verificar conexión
```bash
psql postgresql://felix_user:password@localhost:5432/felix_prod -c "SELECT version();"
```

---

## CONFIGURACIÓN DE SERVICIOS

### 1. SendGrid

```bash
# Verificar API key
curl -X GET https://api.sendgrid.com/v3/mail/send/validate \
  -H "Authorization: Bearer $SENDGRID_API_KEY"

# Crear lista de contactos para feedback
# (En interfaz web de SendGrid)
```

### 2. Shopify OAuth

```
Settings > Apps and integrations > App & sales channel settings

Configurar redirect URIs:
- https://tu-dominio.com/auth/shopify/callback
- https://api.tu-dominio.com/auth/shopify/callback
```

### 3. Jumpseller API

```
Store Admin > Advanced > Integrations > API

Generar credenciales:
- API Key: [guardar en variable de entorno]
- API Secret: [guardar en variable de entorno]
- API Version: 2.0
```

---

## DESPLIEGUE BACKEND

### 1. Clonar Repositorio
```bash
cd /opt
git clone https://github.com/tu-repo/felix-automation.git
cd felix-automation

# Cambiar a rama production
git checkout production
```

### 2. Crear Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt

# Verificar instalación
pip list | grep -E "fastapi|sqlalchemy|sendgrid"
```

### 4. Crear archivo de configuración
```bash
cp .env.example .env
# Editar .env con valores reales
nano .env
```

### 5. Inicializar base de datos
```bash
python scripts/init_db.py
python scripts/seed_data.py  # Si hay datos iniciales
```

### 6. Crear servicio systemd

```bash
sudo nano /etc/systemd/system/felix-api.service
```

Contenido:
```ini
[Unit]
Description=Felix Automation API
After=network.target postgresql.service

[Service]
Type=notify
User=felix
WorkingDirectory=/opt/felix-automation
Environment="PATH=/opt/felix-automation/venv/bin"
EnvironmentFile=/opt/felix-automation/.env
ExecStart=/opt/felix-automation/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /var/log/felix/access.log \
    --error-logfile /var/log/felix/error.log \
    backend.app:app

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 7. Crear directorios de logs
```bash
sudo mkdir -p /var/log/felix
sudo chown felix:felix /var/log/felix
sudo chmod 755 /var/log/felix
```

### 8. Iniciar servicio
```bash
sudo systemctl daemon-reload
sudo systemctl start felix-api
sudo systemctl enable felix-api
sudo systemctl status felix-api
```

### 9. Verificar que está corriendo
```bash
curl http://localhost:8000/health

# Esperado:
# {"status":"🟢 OK","service":"Felix Automation API","version":"11.0"}
```

---

## DESPLIEGUE FRONTEND

### 1. Compilar assets (si aplica)
```bash
cd dashboards
npm install
npm run build

# O si usas Python puro
python scripts/build_dashboards.py
```

### 2. Servir con Nginx (recomendado)

```bash
sudo nano /etc/nginx/sites-available/felix-automation
```

Contenido:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
    
    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy a API Backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
        proxy_connect_timeout 60;
    }
    
    # Servir dashboards estáticos
    location /dashboards {
        alias /opt/felix-automation/dashboards;
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }
    
    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
    
    # Root
    location / {
        root /opt/felix-automation/dashboards;
        try_files $uri $uri/ /index.html;
    }
}
```

### 3. Activar sitio
```bash
sudo ln -s /etc/nginx/sites-available/felix-automation \
    /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl restart nginx
```

### 4. Configurar SSL (Let's Encrypt)
```bash
sudo apt-get install certbot python3-certbot-nginx

sudo certbot certonly --nginx -d tu-dominio.com

# Auto-renew
sudo systemctl enable certbot.timer
```

---

## VERIFICACIÓN DE PRODUCCIÓN

### 1. Health Checks
```bash
# API Health
curl https://tu-dominio.com/health

# Database Connection
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
    https://tu-dominio.com/api/dashboard/kpis

# White-Box Routes
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
    https://tu-dominio.com/api/whitebox/credentials/status
```

### 2. Ejecutar Test Suite
```bash
cd /opt/felix-automation
source venv/bin/activate

# Correr tests contra producción
python -m pytest tests/ -v --tb=short

# O el test end-to-end
python test_end_to_end_complete.py
```

### 3. Validar Logs
```bash
# Verificar que no hay errores
sudo tail -f /var/log/felix/error.log

# Logs de éxito
sudo tail -f /var/log/felix/access.log
```

---

## MONITOREO Y ALERTAS

### 1. Setup de Logging Centralizado (ELK Stack)

```bash
# Instalar Filebeat
sudo apt-get install filebeat

# Configurar filebeat.yml
sudo nano /etc/filebeat/filebeat.yml
```

### 2. Métricas de Performance (Prometheus)

```bash
# Instalar prometheus
sudo apt-get install prometheus

# Config: prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'felix-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 3. Alertas (Alertmanager)

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'email'
  repeat_interval: 4h

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@enbuenamesa.com'
        from: 'alerts@enbuenamesa.com'
        smarthost: 'smtp.sendgrid.net:587'
        auth_username: 'apikey'
        auth_password: $SENDGRID_API_KEY
```

### 4. Monitoreo de Uptime
```bash
# Usar servicio como Uptime Kuma, Pingdom, etc.
curl https://tu-dominio.com/health -I
```

---

## ROLLBACK DE EMERGENCIA

### 1. Mantener versión anterior
```bash
cd /opt/felix-automation

# Crear backup de versión actual
git tag production-v11-backup
git push origin production-v11-backup

# Cambiar a versión anterior
git checkout production-v10
git pull origin production-v10
```

### 2. Revertir cambios en BD
```bash
# Backup de BD actual
pg_dump -U felix_user felix_prod > /backups/felix_prod_v11.sql

# Restaurar desde backup anterior
psql -U felix_user felix_prod < /backups/felix_prod_v10.sql
```

### 3. Reiniciar servicio
```bash
sudo systemctl stop felix-api
sudo systemctl start felix-api
sudo systemctl status felix-api
```

### 4. Verificar rollback
```bash
curl https://tu-dominio.com/health
```

---

## CHECKLIST PRE-DEPLOYMENT

- [ ] Base de datos migrada y verificada
- [ ] Variables de entorno configuradas (.env)
- [ ] SendGrid API key funcional
- [ ] Shopify OAuth configurado
- [ ] Jumpseller API credentials validadas
- [ ] White-Box master key generada y guardada
- [ ] SSL certificates instalados
- [ ] Nginx configurado y testeado
- [ ] Servicio systemd creado y funcional
- [ ] Tests ejecutados localmente (100% pasando)
- [ ] Test E2E ejecutado en staging
- [ ] Backups de BD creados
- [ ] Plan de rollback documentado
- [ ] Monitoreo configurado
- [ ] Alertas configuradas
- [ ] Logs centralizados
- [ ] Documentación de producción actualizada
- [ ] Equipo notificado del deployment

---

## COMANDO RÁPIDO PARA DESPLIEGUE

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Iniciando despliegue..."

# 1. Backup
pg_dump -U felix_user felix_prod > /backups/felix_prod_$(date +%Y%m%d_%H%M%S).sql

# 2. Actualizar código
cd /opt/felix-automation
git pull origin production

# 3. Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# 4. Ejecutar migraciones (si aplica)
python scripts/migrate_db.py

# 5. Reiniciar servicio
sudo systemctl restart felix-api

# 6. Verificar
sleep 2
curl https://tu-dominio.com/health

echo "✅ Despliegue completado exitosamente"
```

---

## CONTACTO Y SOPORTE

- **Admin:** felipe@enbuenamesa.com
- **Documentación:** /opt/felix-automation/docs/
- **Logs:** /var/log/felix/
- **Backups:** /backups/

---

**Última actualización:** 2026-10-05  
**Versión:** FASE 11 Production Ready

