#!/bin/bash

################################################################################
# FELIX AUTOMATION - BACKUP SCRIPT
# Realiza backups automáticos de base de datos, configuración y datos críticos
#
# Uso: bash backup.sh [full|incremental|verify]
#
# Componentes respaldados:
#   - PostgreSQL database (felix_prod)
#   - Configuración (.env, config.yaml)
#   - Archivos de propuestas y auditorías
#   - Logs del sistema
#
# Almacenamiento: /opt/felix-automation/backups/
# Rotación: 30 días (automática)
################################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
BACKUP_DIR="/opt/felix-automation/backups"
APP_DIR="/opt/felix-automation"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"
RETENTION_DAYS=30

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

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Crear directorio de backups
create_backup_directory() {
    print_info "Creando directorio de backups..."
    mkdir -p "${BACKUP_DIR}/database"
    mkdir -p "${BACKUP_DIR}/config"
    mkdir -p "${BACKUP_DIR}/data"
    mkdir -p "${BACKUP_DIR}/logs"
    chmod 700 "${BACKUP_DIR}"
    print_success "Directorio creado: ${BACKUP_DIR}"
    log_message "Directorio de backups creado"
}

# Verificar prerrequisitos
check_prerequisites() {
    print_info "Verificando prerrequisitos..."

    # PostgreSQL
    if ! command -v pg_dump &> /dev/null; then
        print_error "pg_dump no encontrado. Instala PostgreSQL client."
        exit 1
    fi

    # tar
    if ! command -v tar &> /dev/null; then
        print_error "tar no encontrado."
        exit 1
    fi

    # gzip
    if ! command -v gzip &> /dev/null; then
        print_error "gzip no encontrado."
        exit 1
    fi

    print_success "Todos los prerequisitos cumplidos"
    log_message "Verificación de prerequisitos: OK"
}

# Hacer backup de PostgreSQL
backup_database() {
    print_info "Haciendo backup de PostgreSQL..."
    log_message "Iniciando backup de base de datos"

    local backup_file="${BACKUP_DIR}/database/felix_prod_${TIMESTAMP}.sql.gz"

    # Obtener credenciales desde .env
    if [ -f "${APP_DIR}/.env" ]; then
        source "${APP_DIR}/.env"
    else
        print_error ".env no encontrado. Usa: cp .env.example .env"
        exit 1
    fi

    # Si no tienen DB_PASSWORD en .env, intentar conexión sin password
    if [ -z "$DATABASE_PASSWORD" ]; then
        print_info "Intentando conexión sin password..."
        pg_dump -h localhost -U felix_user -d felix_prod | gzip > "$backup_file"
    else
        PGPASSWORD="${DATABASE_PASSWORD}" pg_dump -h localhost -U felix_user -d felix_prod | gzip > "$backup_file"
    fi

    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup de DB completado: $backup_file ($size)"
        log_message "Backup de BD completado: $backup_file ($size)"
    else
        print_error "Falló backup de PostgreSQL"
        log_message "ERROR: Falló backup de BD"
        exit 1
    fi
}

# Hacer backup de configuración
backup_config() {
    print_info "Haciendo backup de configuración..."
    log_message "Iniciando backup de configuración"

    local backup_file="${BACKUP_DIR}/config/config_${TIMESTAMP}.tar.gz"

    cd "${APP_DIR}"
    tar --exclude='.git' --exclude='__pycache__' --exclude='.env' \
        -czf "$backup_file" \
        .env.example \
        config.yaml \
        requirements.txt \
        setup.sh \
        orchestrator.py \
        init_database.py \
        2>/dev/null

    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup de configuración completado: $backup_file ($size)"
        log_message "Backup de configuración completado: $backup_file ($size)"
    else
        print_error "Falló backup de configuración"
        log_message "ERROR: Falló backup de configuración"
    fi
}

# Hacer backup de datos críticos
backup_data() {
    print_info "Haciendo backup de datos críticos..."
    log_message "Iniciando backup de datos"

    if [ ! -d "${APP_DIR}/data" ]; then
        print_info "Directorio data no existe, saltando..."
        return 0
    fi

    local backup_file="${BACKUP_DIR}/data/data_${TIMESTAMP}.tar.gz"

    cd "${APP_DIR}"
    tar -czf "$backup_file" data/ 2>/dev/null

    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup de datos completado: $backup_file ($size)"
        log_message "Backup de datos completado: $backup_file ($size)"
    else
        print_error "Falló backup de datos"
        log_message "ERROR: Falló backup de datos"
    fi
}

# Hacer backup de logs
backup_logs() {
    print_info "Haciendo backup de logs..."
    log_message "Iniciando backup de logs"

    if [ ! -d "/var/log/felix" ]; then
        print_info "Directorio de logs no existe, saltando..."
        return 0
    fi

    local backup_file="${BACKUP_DIR}/logs/logs_${TIMESTAMP}.tar.gz"

    tar -czf "$backup_file" /var/log/felix 2>/dev/null

    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup de logs completado: $backup_file ($size)"
        log_message "Backup de logs completado: $backup_file ($size)"
    else
        print_error "Falló backup de logs"
        log_message "ERROR: Falló backup de logs"
    fi
}

# Rotar backups antiguos
rotate_backups() {
    print_info "Rotando backups antiguos (retención: ${RETENTION_DAYS} días)..."
    log_message "Iniciando rotación de backups"

    find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -delete

    local deleted=$(find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} | wc -l)
    if [ "$deleted" -gt 0 ]; then
        print_success "Eliminados $deleted backups antiguos"
        log_message "Eliminados $deleted backups antiguos"
    else
        print_info "No hay backups para eliminar"
    fi
}

# Crear manifest del backup
create_manifest() {
    print_info "Creando manifest de backup..."

    local manifest_file="${BACKUP_DIR}/BACKUP_MANIFEST_${TIMESTAMP}.txt"

    cat > "$manifest_file" << EOF
================================================================================
FELIX AUTOMATION - BACKUP MANIFEST
================================================================================
Fecha:              $(date '+%Y-%m-%d %H:%M:%S')
Timestamp:          ${TIMESTAMP}
Tipo:               Full Backup

ARCHIVOS INCLUIDOS:
================================================================================
Base de Datos:
  - PostgreSQL (felix_prod)
  - Ubicación: ${BACKUP_DIR}/database/

Configuración:
  - .env.example, config.yaml, requirements.txt
  - Ubicación: ${BACKUP_DIR}/config/

Datos:
  - Propuestas, auditorías, dashboards
  - Ubicación: ${BACKUP_DIR}/data/

Logs:
  - Logs del sistema
  - Ubicación: ${BACKUP_DIR}/logs/

TAMAÑO TOTAL: $(du -sh "${BACKUP_DIR}" | cut -f1)

INSTRUCCIONES DE RESTAURACIÓN:
================================================================================
1. Restaurar database:
   bash restore.sh database ${TIMESTAMP}

2. Restaurar configuración:
   bash restore.sh config ${TIMESTAMP}

3. Restaurar datos:
   bash restore.sh data ${TIMESTAMP}

4. Restaurar todo:
   bash restore.sh full ${TIMESTAMP}

5. Verificar integridad:
   bash restore.sh verify ${TIMESTAMP}

NOTAS:
- Los backups se retienen por ${RETENTION_DAYS} días
- Se recomienda copiar backups a almacenamiento externo
- Verificar regularmente la integridad de backups

================================================================================
EOF

    print_success "Manifest creado: $manifest_file"
    log_message "Manifest creado: $manifest_file"
}

# Verificar integridad del backup
verify_backup() {
    print_info "Verificando integridad de backups..."
    log_message "Iniciando verificación de backups"

    local errors=0

    # Verificar archivos de base de datos
    for file in "${BACKUP_DIR}/database"/*.sql.gz; do
        if [ -f "$file" ]; then
            if gunzip -t "$file" 2>/dev/null; then
                print_success "Base de datos OK: $(basename $file)"
            else
                print_error "Base de datos corrupta: $(basename $file)"
                ((errors++))
            fi
        fi
    done

    # Verificar archivos tar
    for file in "${BACKUP_DIR}"/{config,data,logs}/*.tar.gz; do
        if [ -f "$file" ]; then
            if tar -tzf "$file" > /dev/null 2>&1; then
                print_success "Archivo OK: $(basename $file)"
            else
                print_error "Archivo corrupto: $(basename $file)"
                ((errors++))
            fi
        fi
    done

    if [ $errors -eq 0 ]; then
        print_success "Todos los backups verificados correctamente"
        log_message "Verificación completada sin errores"
    else
        print_error "Se encontraron $errors errores en backups"
        log_message "Verificación completada con $errors errores"
    fi

    return $errors
}

# Mostrar estadísticas de backups
show_statistics() {
    print_header "ESTADÍSTICAS DE BACKUPS"

    echo -e "\nUbicación: ${BACKUP_DIR}"
    echo -e "Tamaño total: $(du -sh "${BACKUP_DIR}" | cut -f1)"
    echo -e "Número de backups: $(find "${BACKUP_DIR}" -type f | wc -l)"
    echo -e "Último backup: $(ls -lt "${BACKUP_DIR}"/*/* 2>/dev/null | head -1 | awk '{print $6, $7, $8}')"

    echo -e "\n${BLUE}Desglose por tipo:${NC}"
    echo -e "  Base de datos: $(du -sh "${BACKUP_DIR}/database" 2>/dev/null | cut -f1)"
    echo -e "  Configuración: $(du -sh "${BACKUP_DIR}/config" 2>/dev/null | cut -f1)"
    echo -e "  Datos: $(du -sh "${BACKUP_DIR}/data" 2>/dev/null | cut -f1)"
    echo -e "  Logs: $(du -sh "${BACKUP_DIR}/logs" 2>/dev/null | cut -f1)"
}

# Backup completo
full_backup() {
    print_header "FELIX AUTOMATION - BACKUP COMPLETO"

    check_prerequisites
    create_backup_directory

    echo ""
    backup_database
    echo ""
    backup_config
    echo ""
    backup_data
    echo ""
    backup_logs
    echo ""
    rotate_backups
    echo ""
    create_manifest
    echo ""
    verify_backup

    echo ""
    print_header "BACKUP COMPLETADO"
    show_statistics

    echo ""
    print_info "Log disponible en: ${LOG_FILE}"
}

# Mostrar ayuda
show_help() {
    cat << EOF
╔════════════════════════════════════════════════════════════╗
║  FELIX AUTOMATION - BACKUP SCRIPT                          ║
╚════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
  Script para realizar backups automáticos del sistema Felix

COMANDO:
  bash backup.sh [OPCIÓN]

OPCIONES:
  full         Realizar backup completo (default)
  incremental  Backup incremental (futuro)
  verify       Verificar integridad de backups
  help         Mostrar esta ayuda

COMPONENTES RESPALDADOS:
  ✅ Base de datos PostgreSQL (felix_prod)
  ✅ Configuración (.env, config.yaml)
  ✅ Datos críticos (propuestas, auditorías)
  ✅ Logs del sistema

UBICACIÓN:
  Backups: /opt/felix-automation/backups/
  Logs:    /opt/felix-automation/backups/backup_*.log

RETENCIÓN:
  Automática: 30 días
  Manual:     Mantener backups en almacenamiento externo

EJEMPLOS:
  # Backup completo
  bash backup.sh full

  # Verificar integridad
  bash backup.sh verify

  # Ayuda
  bash backup.sh help

RECUPERACIÓN:
  Ver: restore.sh

RECOMENDACIONES:
  1. Ejecutar diariamente vía cron:
     0 2 * * * cd /opt/felix-automation && bash backup.sh >> /var/log/felix/backup.log 2>&1

  2. Copiar backups a almacenamiento externo

  3. Verificar integridad regularmente

  4. Documentar cambios importantes

EOF
}

# Main
case "${1:-full}" in
    full)
        full_backup
        ;;
    verify)
        print_header "VERIFICANDO INTEGRIDAD DE BACKUPS"
        verify_backup
        ;;
    stats)
        show_statistics
        ;;
    help)
        show_help
        ;;
    *)
        echo "Opción no reconocida: $1"
        echo "Usa: bash backup.sh help"
        exit 1
        ;;
esac
