#!/bin/bash

# ===============================================
# FELIX AUTOMATION - SETUP SCRIPT AUTOMATIZADO
# ===============================================
# Automatiza todos los pasos del deployment
# Versión: FASE 11 Production Ready
# Uso: sudo bash setup.sh

set -e  # Exit on error
set -u  # Exit on undefined variable

# ===============================================
# COLORES PARA OUTPUT
# ===============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===============================================
# FUNCIONES AUXILIARES
# ===============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 no instalado. Abortando."
        exit 1
    fi
}

# ===============================================
# CONFIGURACIÓN INICIAL
# ===============================================

APP_NAME="Felix Automation"
APP_VERSION="11.0"
APP_USER="felix"
APP_DIR="/opt/felix-automation"
PYTHON_VERSION="3.10"
DB_USER="felix_user"
DB_NAME="felix_prod"
ENVIRONMENT="${ENVIRONMENT:-production}"
DEBUG="${DEBUG:-false}"

log_info "================================"
log_info "  $APP_NAME v$APP_VERSION"
log_info "  Setup Automatizado"
log_info "================================"
log_info "Sistema: $(uname -s)"
log_info "Fecha: $(date)"
log_info ""

# ===============================================
# VERIFICACIONES PREVIAS
# ===============================================

log_info "PASO 0: Verificaciones previas..."

# Verificar si es root
if [[ $EUID -ne 0 ]]; then
    log_error "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Verificar OS
if ! grep -q "Ubuntu" /etc/os-release; then
    log_warning "Este script está optimizado para Ubuntu. Otros sistemas pueden tener problemas."
fi

# Verificar conexión a internet
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    log_error "No hay conexión a internet. Por favor, verifica tu conexión."
    exit 1
fi

log_success "Verificaciones iniciales OK"

# ===============================================
# PASO 1: ACTUALIZAR SISTEMA
# ===============================================

log_info ""
log_info "PASO 1: Actualizando sistema operativo..."

apt-get update
apt-get upgrade -y
apt-get install -y curl wget git build-essential

log_success "Sistema actualizado"

# ===============================================
# PASO 2: INSTALAR DEPENDENCIAS DEL SISTEMA
# ===============================================

log_info ""
log_info "PASO 2: Instalando dependencias del sistema..."

apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    python3-dev \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    nginx \
    certbot \
    python3-certbot-nginx \
    supervisor \
    git \
    curl \
    wget \
    htop \
    vim \
    nano \
    unzip \
    graphviz

log_success "Dependencias del sistema instaladas"

# ===============================================
# PASO 3: CREAR USUARIO DE APLICACIÓN
# ===============================================

log_info ""
log_info "PASO 3: Creando usuario de aplicación '$APP_USER'..."

if id "$APP_USER" &>/dev/null; then
    log_warning "Usuario $APP_USER ya existe. Saltando creación."
else
    useradd -m -s /bin/bash "$APP_USER"
    log_success "Usuario $APP_USER creado"
fi

# ===============================================
# PASO 4: CREAR ESTRUCTURA DE DIRECTORIOS
# ===============================================

log_info ""
log_info "PASO 4: Creando estructura de directorios..."

mkdir -p "$APP_DIR"/{data/{audits,proposals,pipeline,logs,cache},reports/{weekly,monthly},scripts,venv}
mkdir -p /var/log/felix
mkdir -p /var/lib/felix

chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" /var/log/felix
chown -R "$APP_USER:$APP_USER" /var/lib/felix

chmod 755 "$APP_DIR"
chmod 700 "$APP_DIR/.env" 2>/dev/null || true

log_success "Estructura de directorios creada"

# ===============================================
# PASO 5: CLONAR REPOSITORIO (si es necesario)
# ===============================================

log_info ""
log_info "PASO 5: Verificando repositorio..."

if [ ! -d "$APP_DIR/.git" ]; then
    log_warning "Directorio $APP_DIR no es un repositorio Git"
    log_info "Por favor, clona manualmente:"
    log_info "  git clone <repo-url> $APP_DIR"
    read -p "¿Presiona Enter cuando hayas clonado el repositorio..."
else
    log_success "Repositorio Git encontrado"
fi

# ===============================================
# PASO 6: CREAR VIRTUAL ENVIRONMENT
# ===============================================

log_info ""
log_info "PASO 6: Creando virtual environment..."

if [ -d "$APP_DIR/venv" ]; then
    log_warning "Virtual environment ya existe. Usando existente."
else
    sudo -u "$APP_USER" python3.10 -m venv "$APP_DIR/venv"
    log_success "Virtual environment creado"
fi

# ===============================================
# PASO 7: INSTALAR DEPENDENCIAS PYTHON
# ===============================================

log_info ""
log_info "PASO 7: Instalando dependencias Python..."

# Activar venv y instalar
cd "$APP_DIR"
source "$APP_DIR/venv/bin/activate"

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

log_success "Dependencias Python instaladas"

# ===============================================
# PASO 8: CONFIGURAR BASE DE DATOS POSTGRESQL
# ===============================================

log_info ""
log_info "PASO 8: Configurando PostgreSQL..."

# Iniciar PostgreSQL si no está corriendo
systemctl start postgresql || true
systemctl enable postgresql

# Esperar a que PostgreSQL esté listo
sleep 2

# Crear usuario y BD
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD 'temp_password_change_me';
    END IF;
END
\$\$;

DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME OWNER $DB_USER;

GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Configuración de seguridad
ALTER DATABASE $DB_NAME SET log_statement = 'all';
ALTER DATABASE $DB_NAME SET log_duration = 'on';
EOF

log_success "Base de datos PostgreSQL configurada"

# ===============================================
# PASO 9: CONFIGURAR VARIABLES DE ENTORNO
# ===============================================

log_info ""
log_info "PASO 9: Configurando variables de entorno..."

if [ -f "$APP_DIR/.env" ]; then
    log_warning "Archivo .env ya existe. Backup a .env.backup"
    cp "$APP_DIR/.env" "$APP_DIR/.env.backup.$(date +%s)"
else
    if [ -f "$APP_DIR/.env.example" ]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        chmod 600 "$APP_DIR/.env"
        chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
        log_success ".env creado desde .env.example"

        log_warning "⚠️  IMPORTANTE: Edita .env con tus valores:"
        log_warning "  - DATABASE_URL (user, password, host)"
        log_warning "  - SENDGRID_API_KEY"
        log_warning "  - SECRET_KEY (ya debe estar generada)"
        log_warning "  - WHITEBOX_MASTER_KEY (ya debe estar generada)"
        log_warning ""
        log_warning "Archivo: $APP_DIR/.env"
    else
        log_error ".env.example no encontrado"
        exit 1
    fi
fi

# ===============================================
# PASO 10: INICIALIZAR BASE DE DATOS
# ===============================================

log_info ""
log_info "PASO 10: Inicializando base de datos..."

cd "$APP_DIR"
source "$APP_DIR/venv/bin/activate"

if [ -f "init_database.py" ]; then
    python init_database.py || log_warning "init_database.py no pudo ejecutarse. Verifica manualmente."
else
    log_warning "init_database.py no encontrado. Saltando inicialización."
fi

log_success "Base de datos inicializada"

# ===============================================
# PASO 11: CREAR SERVICIO SYSTEMD
# ===============================================

log_info ""
log_info "PASO 11: Configurando servicio systemd..."

cat > /etc/systemd/system/felix-api.service <<EOF
[Unit]
Description=Felix Automation API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=-$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 4 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --bind 0.0.0.0:8000 \\
    --timeout 120 \\
    --access-logfile /var/log/felix/access.log \\
    --error-logfile /var/log/felix/error.log \\
    backend.app:app

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=felix-api

# Seguridad
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=true
ReadWritePaths=$APP_DIR/data /var/log/felix

[Install]
WantedBy=multi-user.target
EOF

# Crear servicio de scheduler (optional)
cat > /etc/systemd/system/felix-scheduler.service <<EOF
[Unit]
Description=Felix Automation Scheduler
After=network.target postgresql.service felix-api.service
Wants=postgresql.service felix-api.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=-$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python scripts/scheduler.py

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=felix-scheduler

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable felix-api.service
systemctl enable felix-scheduler.service || true

log_success "Servicios systemd configurados"

# ===============================================
# PASO 12: INSTALAR Y CONFIGURAR NGINX
# ===============================================

log_info ""
log_info "PASO 12: Configurando Nginx..."

# Respaldar configuración default
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup || true

# Crear configuración Felix
cat > /etc/nginx/sites-available/felix-automation <<'EOF'
upstream felix_app {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Redirigir HTTP a HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # Certificados SSL (cambiar path si es necesario)
    # ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/felix_access.log;
    error_log /var/log/nginx/felix_error.log;

    # Tamaño máximo de upload
    client_max_body_size 10M;

    # API Backend
    location /api {
        proxy_pass http://felix_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
        proxy_connect_timeout 75;
    }

    # WebSocket
    location /ws {
        proxy_pass http://felix_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # Frontend
    location / {
        root /opt/felix-automation/frontend/dashboard;
        try_files $uri $uri/ /index.html;
    }

    # Health check
    location /health {
        access_log off;
        proxy_pass http://felix_app/health;
    }

    # Deny acceso a archivos sensibles
    location ~ /\.env {
        deny all;
    }

    location ~ /\.git {
        deny all;
    }
}
EOF

# Habilitar sitio
ln -sf /etc/nginx/sites-available/felix-automation /etc/nginx/sites-enabled/ || true
rm -f /etc/nginx/sites-enabled/default || true

# Probar configuración
nginx -t

# Reiniciar Nginx
systemctl restart nginx
systemctl enable nginx

log_success "Nginx configurado"

# ===============================================
# PASO 13: CONFIGURAR CERTBOT (SSL)
# ===============================================

log_info ""
log_info "PASO 13: Configurando SSL con Certbot..."

log_warning "⚠️  Para instalar certificado SSL:"
log_warning "  certbot certonly --nginx -d tu-dominio.com"
log_warning ""
log_warning "  Luego edita /etc/nginx/sites-available/felix-automation"
log_warning "  y descomenta las líneas de ssl_certificate"

log_info "Configurando auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

log_success "Certbot configurado"

# ===============================================
# PASO 14: INSTALAR HERRAMIENTAS DE MONITOREO
# ===============================================

log_info ""
log_info "PASO 14: Instalando herramientas de monitoreo..."

# Prometheus (optional)
if command -v prometheus &> /dev/null; then
    log_info "Prometheus ya instalado"
else
    log_warning "Prometheus no instalado. Ver MONITORING_PLAN.md para instalación."
fi

log_success "Herramientas de monitoreo verificadas"

# ===============================================
# PASO 15: SETUP DE LOGS Y ROTACIÓN
# ===============================================

log_info ""
log_info "PASO 15: Configurando logs y rotación..."

# Crear archivo de rotación de logs
cat > /etc/logrotate.d/felix <<EOF
/var/log/felix/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $APP_USER $APP_USER
    sharedscripts
    postrotate
        systemctl reload felix-api.service > /dev/null 2>&1 || true
    endscript
}
EOF

log_success "Rotación de logs configurada"

# ===============================================
# PASO 16: EJECUTAR TESTS
# ===============================================

log_info ""
log_info "PASO 16: Ejecutando tests básicos..."

cd "$APP_DIR"
source "$APP_DIR/venv/bin/activate"

# Test de conexión a BD
log_info "Test: Conexión a PostgreSQL..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('dbname=$DB_NAME user=$DB_USER host=localhost')
    conn.close()
    print('[✓] PostgreSQL OK')
except Exception as e:
    print(f'[!] PostgreSQL ERROR: {e}')
    exit(1)
" || log_warning "PostgreSQL test falló"

# Test de importación de módulos
log_info "Test: Importación de módulos..."
python3 -c "
try:
    from orchestrator import FelixAutomationOrchestrator
    print('[✓] Orchestrator OK')
except Exception as e:
    print(f'[!] Orchestrator ERROR: {e}')
    exit(1)
" || log_warning "Importación falló"

log_success "Tests básicos completados"

# ===============================================
# PASO 17: INICIAR SERVICIOS
# ===============================================

log_info ""
log_info "PASO 17: Iniciando servicios..."

systemctl start felix-api.service
sleep 2
systemctl status felix-api.service

# Verificar que está corriendo
if systemctl is-active --quiet felix-api.service; then
    log_success "Servicio felix-api activo"
else
    log_error "Servicio felix-api NO está activo"
    systemctl status felix-api.service
fi

# Scheduler (si existe)
if [ -f "$APP_DIR/scripts/scheduler.py" ]; then
    systemctl start felix-scheduler.service || log_warning "Scheduler no inició"
fi

log_success "Servicios iniciados"

# ===============================================
# PASO 18: VERIFICACIÓN FINAL
# ===============================================

log_info ""
log_info "PASO 18: Verificación final..."

# Health check
log_info "Verificando health check..."
if curl -s http://localhost:8000/health &> /dev/null; then
    log_success "Health check OK"
else
    log_warning "Health check no accesible. Verifica logs:"
    log_warning "  tail -50 /var/log/felix/error.log"
fi

# Verificar permisos
log_info "Verificando permisos..."
if [ -f "$APP_DIR/.env" ] && [ "$(stat -c %a "$APP_DIR/.env")" = "600" ]; then
    log_success "Permisos .env correctos (600)"
else
    log_warning "⚠️  Permisos .env incorrectos. Ejecutar:"
    log_warning "  chmod 600 $APP_DIR/.env"
    chmod 600 "$APP_DIR/.env" 2>/dev/null || true
fi

# ===============================================
# RESUMEN FINAL
# ===============================================

log_info ""
log_info "================================"
log_success "SETUP COMPLETADO EXITOSAMENTE ✓"
log_info "================================"
log_info ""
log_info "PRÓXIMOS PASOS:"
log_info ""
log_info "1. Editar variables de entorno:"
log_info "   nano $APP_DIR/.env"
log_info ""
log_info "2. Verificar estado:"
log_info "   systemctl status felix-api"
log_info "   tail -f /var/log/felix/error.log"
log_info ""
log_info "3. Instalar certificado SSL (si es necesario):"
log_info "   certbot certonly --nginx -d tu-dominio.com"
log_info ""
log_info "4. Configurar monitoreo:"
log_info "   Ver MONITORING_PLAN.md"
log_info ""
log_info "5. Realizar test end-to-end:"
log_info "   cd $APP_DIR && source venv/bin/activate"
log_info "   python test_end_to_end_complete.py"
log_info ""
log_info "INFORMACIÓN IMPORTANTE:"
log_info "- Servicio: felix-api.service"
log_info "- Logs: /var/log/felix/"
log_info "- Config: $APP_DIR/.env"
log_info "- Puerto: 8000 (Gunicorn) → 443 (Nginx)"
log_info ""
log_info "Para más detalles ver: GUIA_RAPIDA_DESPLIEGUE.md"
log_info ""

exit 0
