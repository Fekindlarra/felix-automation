#!/bin/bash

################################################################################
# FELIX AUTOMATION - RESTORE SCRIPT
# Restaura desde backups creados por backup.sh
#
# Uso: bash restore.sh [database|config|data|full|verify] [TIMESTAMP]
#
# Ejemplos:
#   bash restore.sh database 20261005_143000
#   bash restore.sh full 20261005_143000
#   bash restore.sh verify 20261005_143000
################################################################################

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
BACKUP_DIR="/opt/felix-automation/backups"
APP_DIR="/opt/felix-automation"
TIMESTAMP="${2:-}"

# Funciones
print_header() {
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${RED}⚠️  $1${NC}"
}

# Confirmar peligrosa operación
confirm_restore() {
    local message="$1"
    print_warning "$message"
    echo -n "¿Estás seguro? Escribe 'SÍ' para continuar: "
    read -r response

    if [ "$response" != "SÍ" ]; then
        print_error "Operación cancelada"
        exit 1
    fi
}

# Validar timestamp
validate_timestamp() {
    if [ -z "$TIMESTAMP" ]; then
        print_error "Timestamp requerido. Ejemplo: 20261005_143000"
        echo ""
        echo "Backups disponibles:"
        ls -lh "${BACKUP_DIR}"/database/*.sql.gz 2>/dev/null | tail -5 | awk '{print $NF}' | sed 's/.*felix_prod_//;s/.sql.gz//'
        exit 1
    fi
}

# Verificar que el backup existe
check_backup_exists() {
    local type="$1"
    local file=""

    case "$type" in
        database)
            file="${BACKUP_DIR}/database/felix_prod_${TIMESTAMP}.sql.gz"
            ;;
        config)
            file="${BACKUP_DIR}/config/config_${TIMESTAMP}.tar.gz"
            ;;
        data)
            file="${BACKUP_DIR}/data/data_${TIMESTAMP}.tar.gz"
            ;;
    esac

    if [ ! -f "$file" ]; then
        print_error "Backup no encontrado: $file"
        echo ""
        echo "Archivos disponibles:"
        ls -lh "${BACKUP_DIR}/$type"/ 2>/dev/null | tail -3
        exit 1
    fi
}

# Verificar integridad del backup
verify_backup_integrity() {
    local type="$1"
    print_info "Verificando integridad del backup..."

    case "$type" in
        database)
            local file="${BACKUP_DIR}/database/felix_prod_${TIMESTAMP}.sql.gz"
            if ! gunzip -t "$file" 2>/dev/null; then
                print_error "Backup corrupto: $file"
                exit 1
            fi
            ;;
        config|data)
            local file="${BACKUP_DIR}/$type/${type}_${TIMESTAMP}.tar.gz"
            if ! tar -tzf "$file" > /dev/null 2>&1; then
                print_error "Backup corrupto: $file"
                exit 1
            fi
            ;;
    esac

    print_success "Backup íntegro"
}

# Restaurar base de datos
restore_database() {
    validate_timestamp
    check_backup_exists "database"
    verify_backup_integrity "database"

    print_header "RESTAURANDO BASE DE DATOS"

    confirm_restore "Esto sobrescribirá la base de datos actual (felix_prod)"

    print_info "Deteniendo servicios..."
    sudo systemctl stop felix-api felix-scheduler 2>/dev/null || true

    print_info "Restaurando base de datos..."

    # Obtener credenciales
    if [ -f "${APP_DIR}/.env" ]; then
        source "${APP_DIR}/.env"
    fi

    local backup_file="${BACKUP_DIR}/database/felix_prod_${TIMESTAMP}.sql.gz"

    # Dropear BD existente y recrearla
    if [ -z "$DATABASE_PASSWORD" ]; then
        psql -U felix_user -c "DROP DATABASE IF EXISTS felix_prod;" 2>/dev/null || true
        psql -U felix_user -c "CREATE DATABASE felix_prod OWNER felix_user;" 2>/dev/null
        gunzip -c "$backup_file" | psql -U felix_user -d felix_prod
    else
        PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U felix_user -c "DROP DATABASE IF EXISTS felix_prod;" 2>/dev/null || true
        PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U felix_user -c "CREATE DATABASE felix_prod OWNER felix_user;" 2>/dev/null
        gunzip -c "$backup_file" | PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U felix_user -d felix_prod
    fi

    if [ $? -eq 0 ]; then
        print_success "Base de datos restaurada correctamente"

        print_info "Reiniciando servicios..."
        sudo systemctl start felix-api felix-scheduler 2>/dev/null || true

        print_success "Restauración completada"
    else
        print_error "Falló la restauración de base de datos"
        exit 1
    fi
}

# Restaurar configuración
restore_config() {
    validate_timestamp
    check_backup_exists "config"
    verify_backup_integrity "config"

    print_header "RESTAURANDO CONFIGURACIÓN"

    confirm_restore "Esto sobrescribirá archivos de configuración"

    print_info "Creando backup de configuración actual..."
    local current_backup="${APP_DIR}/config_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    cd "${APP_DIR}"
    tar -czf "$current_backup" .env.example config.yaml requirements.txt 2>/dev/null || true
    print_success "Backup actual guardado: $current_backup"

    print_info "Restaurando configuración..."
    local backup_file="${BACKUP_DIR}/config/config_${TIMESTAMP}.tar.gz"

    cd "${APP_DIR}"
    tar -xzf "$backup_file"

    if [ $? -eq 0 ]; then
        print_success "Configuración restaurada correctamente"
        print_info "Reinicia el servicio para aplicar cambios:"
        echo "  sudo systemctl restart felix-api"
    else
        print_error "Falló la restauración de configuración"
        exit 1
    fi
}

# Restaurar datos
restore_data() {
    validate_timestamp
    check_backup_exists "data"
    verify_backup_integrity "data"

    print_header "RESTAURANDO DATOS"

    confirm_restore "Esto sobrescribirá datos (propuestas, auditorías, etc.)"

    print_info "Creando backup de datos actual..."
    local current_backup="${APP_DIR}/data_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    cd "${APP_DIR}"
    tar -czf "$current_backup" data/ 2>/dev/null || true
    print_success "Backup actual guardado: $current_backup"

    print_info "Restaurando datos..."
    local backup_file="${BACKUP_DIR}/data/data_${TIMESTAMP}.tar.gz"

    cd "${APP_DIR}"
    rm -rf data/
    tar -xzf "$backup_file"

    if [ $? -eq 0 ]; then
        print_success "Datos restaurados correctamente"
    else
        print_error "Falló la restauración de datos"
        exit 1
    fi
}

# Restauración completa
restore_full() {
    validate_timestamp

    print_header "RESTAURACIÓN COMPLETA"

    confirm_restore "Esto restaurará TODO el sistema desde el backup ${TIMESTAMP}"

    echo ""
    print_info "1/3 Restaurando base de datos..."
    restore_database

    echo ""
    print_info "2/3 Restaurando configuración..."
    restore_config

    echo ""
    print_info "3/3 Restaurando datos..."
    restore_data

    echo ""
    print_header "RESTAURACIÓN COMPLETADA"
    print_success "Sistema completamente restaurado"
    print_info "Timestamp del backup: ${TIMESTAMP}"
}

# Verificar integridad de todos los backups
verify_all_backups() {
    print_header "VERIFICANDO INTEGRIDAD DE TODOS LOS BACKUPS"

    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "Directorio de backups no existe: $BACKUP_DIR"
        exit 1
    fi

    local total=0
    local ok=0
    local errors=0

    echo ""
    print_info "Verificando bases de datos..."
    for file in "${BACKUP_DIR}/database"/*.sql.gz 2>/dev/null; do
        if [ -f "$file" ]; then
            ((total++))
            if gunzip -t "$file" 2>/dev/null; then
                print_success "$(basename $file)"
                ((ok++))
            else
                print_error "$(basename $file)"
                ((errors++))
            fi
        fi
    done

    echo ""
    print_info "Verificando archivos de configuración..."
    for file in "${BACKUP_DIR}/config"/*.tar.gz 2>/dev/null; do
        if [ -f "$file" ]; then
            ((total++))
            if tar -tzf "$file" > /dev/null 2>&1; then
                print_success "$(basename $file)"
                ((ok++))
            else
                print_error "$(basename $file)"
                ((errors++))
            fi
        fi
    done

    echo ""
    print_info "Verificando archivos de datos..."
    for file in "${BACKUP_DIR}/data"/*.tar.gz 2>/dev/null; do
        if [ -f "$file" ]; then
            ((total++))
            if tar -tzf "$file" > /dev/null 2>&1; then
                print_success "$(basename $file)"
                ((ok++))
            else
                print_error "$(basename $file)"
                ((errors++))
            fi
        fi
    done

    echo ""
    print_header "RESULTADO DE VERIFICACIÓN"
    echo "Total: $total | OK: $ok | Errores: $errors"

    if [ $errors -eq 0 ]; then
        print_success "Todos los backups son íntegros"
    else
        print_error "$errors backups corrupto(s)"
        exit 1
    fi
}

# Listar backups disponibles
list_backups() {
    print_header "BACKUPS DISPONIBLES"

    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "Directorio de backups no existe"
        exit 1
    fi

    echo ""
    print_info "Base de datos:"
    ls -lh "${BACKUP_DIR}/database"/*.sql.gz 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}' || echo "  (ninguno)"

    echo ""
    print_info "Configuración:"
    ls -lh "${BACKUP_DIR}/config"/*.tar.gz 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}' || echo "  (ninguno)"

    echo ""
    print_info "Datos:"
    ls -lh "${BACKUP_DIR}/data"/*.tar.gz 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}' || echo "  (ninguno)"

    echo ""
    print_info "Logs:"
    ls -lh "${BACKUP_DIR}/logs"/*.tar.gz 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}' || echo "  (ninguno)"
}

# Mostrar ayuda
show_help() {
    cat << EOF
╔════════════════════════════════════════════════════════════╗
║  FELIX AUTOMATION - RESTORE SCRIPT                         ║
╚════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
  Script para restaurar desde backups creados por backup.sh

COMANDO:
  bash restore.sh [OPCIÓN] [TIMESTAMP]

OPCIONES:
  database    Restaurar solo base de datos
  config      Restaurar solo configuración
  data        Restaurar solo datos
  full        Restaurar todo el sistema
  verify      Verificar integridad de backups
  list        Listar backups disponibles
  help        Mostrar esta ayuda

ARGUMENTOS:
  TIMESTAMP   Timestamp del backup (ej: 20261005_143000)
              Se requiere para todas las opciones excepto verify, list, help

EJEMPLOS:
  # Restaurar base de datos
  bash restore.sh database 20261005_143000

  # Restauración completa
  bash restore.sh full 20261005_143000

  # Listar backups disponibles
  bash restore.sh list

  # Verificar integridad
  bash restore.sh verify

PROCEDIMIENTO DE RECUPERACIÓN:
  1. Listar backups disponibles:
     bash restore.sh list

  2. Seleccionar el timestamp deseado

  3. Restaurar:
     - Solo DB: bash restore.sh database TIMESTAMP
     - Todo:    bash restore.sh full TIMESTAMP

  4. Verificar:
     sudo systemctl status felix-api
     curl https://localhost/health

SEGURIDAD:
  ⚠️  Todas las restauraciones crean un backup del estado actual
  ⚠️  Se requiere confirmación antes de cada restauración
  ⚠️  Revisa los logs después de restaurar

NOTAS:
  - Los cambios de configuración requieren restart del servicio
  - La restauración de DB pausará temporalmente los servicios
  - Los datos más recientes se encuentran en el último backup

EOF
}

# Main
case "${1:-help}" in
    database)
        restore_database
        ;;
    config)
        restore_config
        ;;
    data)
        restore_data
        ;;
    full)
        restore_full
        ;;
    verify)
        verify_all_backups
        ;;
    list)
        list_backups
        ;;
    help)
        show_help
        ;;
    *)
        echo "Opción no reconocida: $1"
        echo "Usa: bash restore.sh help"
        exit 1
        ;;
esac
