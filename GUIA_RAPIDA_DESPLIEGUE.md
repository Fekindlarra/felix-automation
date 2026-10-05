# ⚡ GUÍA RÁPIDA DE DESPLIEGUE - Felix Automation

**Versión:** FASE 11 Production Ready  
**Fecha:** 2026-10-05  
**Tiempo Estimado:** 4-6 horas  

---

## 🎯 CHECKLIST RÁPIDO

**Antes de Empezar:**
- [ ] Servidor Linux (Ubuntu 20.04+) con SSH acceso
- [ ] 4+ CPU, 8GB+ RAM mínimo
- [ ] Dominio configurado con DNS
- [ ] Email SendGrid API key lista
- [ ] Repositorio GitHub accesible

---

## 📋 PASOS DEL DESPLIEGUE

### PASO 1: Preparar Servidor (30 min)

```bash
# Conectar al servidor
ssh ubuntu@your-server.com

# Actualizar sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias
sudo apt-get install -y \
    python3.10 python3-pip python3-venv \
    postgresql postgresql-contrib \
    nginx \
    git \
    certbot python3-certbot-nginx

# Crear usuario para la aplicación
sudo useradd -m -s /bin/bash felix
sudo su - felix
```

### PASO 2: Clonar Repositorio (15 min)

```bash
# Clonar proyecto
cd /opt
sudo git clone https://github.com/tu-repo/felix-automation.git
sudo chown -R felix:felix felix-automation
cd felix-automation

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### PASO 3: Configurar Base de Datos (30 min)

```bash
# Conectar como postgres
sudo -u postgres psql

# Ejecutar en psql:
CREATE USER felix_user WITH PASSWORD 'strong_password_here';
CREATE DATABASE felix_prod OWNER felix_user;
GRANT ALL PRIVILEGES ON DATABASE felix_prod TO felix_user;
\q

# Verificar conexión
psql postgresql://felix_user:password@localhost:5432/felix_prod -c "SELECT version();"
```

### PASO 4: Configurar Variables de Entorno (15 min)

```bash
# Generar claves
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Crear .env
cp .env.example .env
nano .env

# Editar con estos valores:
DATABASE_URL=postgresql://felix_user:password@localhost:5432/felix_prod
SECRET_KEY=<tu-clave-generada>
WHITEBOX_MASTER_KEY=<tu-fernet-key>
SENDGRID_API_KEY=<tu-api-key>
ADMIN_EMAIL=felipe@enbuenamesa.com
ENVIRONMENT=production
DEBUG=false

# Proteger archivo
chmod 600 .env
```

### PASO 5: Inicializar Base de Datos (10 min)

```bash
# Conectar a la aplicación
cd /opt/felix-automation
source venv/bin/activate

# Inicializar BD
python scripts/init_db.py

# Verificar
python << 'EOF'
from orchestrator import FelixAutomationOrchestrator
orch = FelixAutomationOrchestrator(db_path="data/pipeline.db")
orch.connect_database()
clients = orch.get_all_clients()
print(f"✅ BD inicializada con {len(clients)} clientes")
orch.close_database()
EOF
```

### PASO 6: Crear Servicio Systemd (15 min)

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/felix-api.service

# Copiar contenido:
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
    backend.app:app

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

# Crear directorio de logs
sudo mkdir -p /var/log/felix
sudo chown felix:felix /var/log/felix

# Habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable felix-api
sudo systemctl start felix-api
sudo systemctl status felix-api
```

### PASO 7: Configurar Nginx (20 min)

```bash
# Crear configuración
sudo nano /etc/nginx/sites-available/felix-automation

# Copiar contenido básico:
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000" always;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }

    location / {
        root /opt/felix-automation/dashboards;
        try_files $uri $uri/ /index.html;
    }
}

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/felix-automation \
    /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### PASO 8: Obtener SSL Certificate (10 min)

```bash
# Con Certbot
sudo certbot certonly --nginx -d tu-dominio.com

# Auto-renew
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### PASO 9: Verificar Instalación (10 min)

```bash
# Health check
curl https://tu-dominio.com/health

# Esperado:
# {"status":"🟢 OK","service":"Felix Automation API","version":"11.0"}

# Verificar logs
sudo tail -f /var/log/felix/error.log
```

### PASO 10: Configurar Monitoreo (30 min)

```bash
# Opción 1: Simple (recomendado para empezar)
# Usar servicio externo como Uptime Kuma
# https://uptime.kuma.pet - instalar y configurar

# Opción 2: ELK Stack (avanzado)
# Seguir guía en DEPLOYMENT_GUIDE.md

# Opción 3: CloudWatch (AWS)
# Configurar agente de CloudWatch
```

---

## 🧪 VALIDACIÓN POST-DESPLIEGUE

```bash
# 1. Verificar servicio
sudo systemctl status felix-api

# 2. Verificar API
curl -s https://tu-dominio.com/health | jq

# 3. Verificar logs
sudo tail -50 /var/log/felix/error.log

# 4. Verificar database
psql postgresql://felix_user:password@localhost:5432/felix_prod \
    -c "SELECT COUNT(*) FROM clients;"

# 5. Ejecutar test básico
cd /opt/felix-automation
source venv/bin/activate
python test_end_to_end_complete.py
```

---

## ⚠️ TROUBLESHOOTING RÁPIDO

### Error: "Connection refused" a base de datos
```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Reiniciar si es necesario
sudo systemctl restart postgresql
```

### Error: "Permission denied" archivos
```bash
# Fijar permisos
sudo chown -R felix:felix /opt/felix-automation
chmod 755 /opt/felix-automation
chmod 600 /opt/felix-automation/.env
```

### Error: "Port 8000 already in use"
```bash
# Encontrar proceso
sudo lsof -i :8000

# Matar si es necesario
sudo kill -9 <PID>
```

### Error: "SSL certificate not found"
```bash
# Regenerar
sudo certbot renew --force-renewal

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 🔄 ROLLBACK DE EMERGENCIA

```bash
# Detener servicio
sudo systemctl stop felix-api

# Revertir código
cd /opt/felix-automation
git checkout production-v10

# Reinstalar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Restaurar BD (desde backup)
pg_restore -U felix_user felix_prod < /backups/felix_prod_v10.sql

# Reiniciar
sudo systemctl start felix-api
curl https://tu-dominio.com/health
```

---

## 📊 RECURSOS ÚTILES

| Recurso | Ubicación |
|---------|-----------|
| Deployment Completo | `DEPLOYMENT_GUIDE.md` |
| Test End-to-End | `test_end_to_end_complete.py` |
| Configuración Ejemplo | `.env.example` |
| Logs de Aplicación | `/var/log/felix/` |
| Documentación Técnica | `docs/` |
| API Reference | `backend/routes/` |

---

## ✅ CHECKLIST FINAL

- [ ] Servidor configurado
- [ ] Repositorio clonado
- [ ] Base de datos creada
- [ ] Variables de entorno configuradas
- [ ] Servicio systemd activo
- [ ] Nginx configurado
- [ ] SSL certificate instalado
- [ ] Health check pasando
- [ ] Logs sin errores
- [ ] Monitoreo configurado
- [ ] Backup plan en lugar
- [ ] Equipo notificado

---

**Soporte:** Felipe (@enbuenamesa.com)  
**En caso de problemas:** Consultar DEPLOYMENT_GUIDE.md o logs del servidor

---

*Tiempo total estimado: 4-6 horas (incluyendo certificados SSL y configuración)*
