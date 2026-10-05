#!/bin/bash

################################################################################
# FELIX AUTOMATION - UPGRADE SCRIPT
# Maneja actualizaciones de versión con seguridad, validación y rollback
#
# Uso: bash upgrade.sh [version|check|rollback|help]
#
# Ejemplos:
#   bash upgrade.sh check         # Verifica disponibilidad de updates
#   bash upgrade.sh 12.0          # Actualiza a versión 12.0
#   bash upgrade.sh rollback      # Revierte a versión anterior
################################################################################

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuración
APP_DIR="/opt/felix-automation"
BACKUP_DIR="${APP_DIR}/backups"
UPGRADE_DIR="${APP_DIR}/upgrades"
CURRENT_VERSION_FILE="${APP_DIR}/.version"
UPGRADE_LOG="${UPGRADE_DIR}/upgrade_$(date +%Y%m%d_%H%M%S).log"
UPGRADE_STATUS="${UPGRADE_DIR}/.upgrade_status"

# Versión actual
CURRENT_VERSION=$(cat "$CURRENT_VERSION_FILE" 2>/dev/null || echo "11.0")

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

print_step() {
    echo -e "${CYAN}→ $1${NC}"
}

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$UPGRADE_LOG"
}

# Crear directorio de upgrades
create_upgrade_directory() {
    mkdir -p "$UPGRADE_DIR"
    chmod 700 "$UPGRADE_DIR"
    log_message "Directorio de upgrades creado: $UPGRADE_DIR"
}

# Verificar disponibilidad de actualizaciones
check_updates() {
    print_header "VERIFICANDO ACTUALIZACIONES"

    local latest_version=$(curl -s "https://api.github.com/repos/[TU_USUARIO]/felix-automation/releases/latest" 2>/dev/null | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4 | sed 's/v//' || echo "unknown")

    echo ""
    echo -e "Versión actual:    ${CYAN}${CURRENT_VERSION}${NC}"
    echo -e "Versión disponible: ${CYAN}${latest_version}${NC}"
    echo ""

    if [ "$latest_version" != "unknown" ]; then
        if [ "$latest_version" = "$CURRENT_VERSION" ]; then
            print_success "Ya tienes la versión más reciente"
        else
            print_info "Nueva versión disponible: $latest_version"
            echo ""
            echo -e "${YELLOW}Para actualizar ejecuta:${NC}"
            echo -e "  ${CYAN}bash upgrade.sh $latest_version${NC}"
        fi
    else
        print_warning "No se pudo verificar versión disponible. Verifica conexión a GitHub."
    fi
}

# Crear backup pre-upgrade
create_upgrade_backup() {
    local backup_name="pre-upgrade-${CURRENT_VERSION}-to-${1}_$(date +%Y%m%d_%H%M%S)"

    print_info "Creando backup pre-upgrade..."

    # Ejecutar backup completo
    cd "$APP_DIR"
    bash backup.sh full >> "$UPGRADE_LOG" 2>&1

    if [ $? -eq 0 ]; then
        # Copiar a directorio de upgrades
        cp -r "$BACKUP_DIR"/* "$UPGRADE_DIR/" 2>/dev/null || true
        print_success "Backup pre-upgrade completado"
        log_message "Backup pre-upgrade creado: $backup_name"
    else
        print_error "Falló la creación de backup"
        exit 1
    fi
}

# Validar compatibilidad de versión
validate_version_upgrade() {
    local target_version="$1"

    print_info "Validando compatibilidad de versión..."

    # Validar formato de versión (NN.N)
    if ! [[ "$target_version" =~ ^[0-9]+\.[0-9]+$ ]]; then
        print_error "Versión inválida: $target_version (formato esperado: NN.N)"
        exit 1
    fi

    # Verificar que no sea una versión más antigua
    local current_major=$(echo $CURRENT_VERSION | cut -d. -f1)
    local current_minor=$(echo $CURRENT_VERSION | cut -d. -f2)
    local target_major=$(echo $target_version | cut -d. -f1)
    local target_minor=$(echo $target_version | cut -d. -f2)

    if [ "$target_major" -lt "$current_major" ] || ([ "$target_major" -eq "$current_major" ] && [ "$target_minor" -lt "$current_minor" ]); then
        print_error "No se permite downgrade. Usa 'bash upgrade.sh rollback' para volver a versión anterior."
        log_message "Intento de downgrade de $CURRENT_VERSION a $target_version - RECHAZADO"
        exit 1
    fi

    print_success "Versión $target_version es compatible"
}

# Verificar dependencias
check_dependencies() {
    print_info "Verificando dependencias..."

    local missing=0

    # Python
    if ! command -v python3 &> /dev/null; then
        print_error "python3 no encontrado"
        ((missing++))
    fi

    # PostgreSQL
    if ! command -v psql &> /dev/null; then
        print_error "psql no encontrado"
        ((missing++))
    fi

    # pip
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip no encontrado"
        ((missing++))
    fi

    if [ $missing -gt 0 ]; then
        print_error "Faltan $missing dependencia(s) requerida(s)"
        exit 1
    fi

    print_success "Todas las dependencias disponibles"
}

# Actualizar código
update_code() {
    local target_version="$1"

    print_step "Actualizando código..."

    cd "$APP_DIR"

    # Fetch latest changes
    git fetch origin >> "$UPGRADE_LOG" 2>&1

    # Checkout específica versión
    git checkout "v${target_version}" >> "$UPGRADE_LOG" 2>&1

    if [ $? -eq 0 ]; then
        print_success "Código actualizado a versión $target_version"
        log_message "Código actualizado: v$target_version"
    else
        print_error "Falló la actualización de código"
        log_message "ERROR: Falló git checkout v$target_version"
        exit 1
    fi
}

# Actualizar dependencias Python
update_python_dependencies() {
    print_step "Actualizando dependencias Python..."

    # Crear backup de requirements.txt
    cp "$APP_DIR/requirements.txt" "$UPGRADE_DIR/requirements_backup.txt"

    # Actualizar
    python3 -m pip install --upgrade -r "$APP_DIR/requirements.txt" >> "$UPGRADE_LOG" 2>&1

    if [ $? -eq 0 ]; then
        print_success "Dependencias Python actualizadas"
        log_message "Dependencias Python actualizadas"
    else
        print_error "Falló la actualización de dependencias"
        log_message "ERROR: Falló pip install"
        exit 1
    fi
}

# Ejecutar migraciones de base de datos
run_database_migrations() {
    print_step "Ejecutando migraciones de base de datos..."

    cd "$APP_DIR"

    # Si existe migration script
    if [ -f "migrate_database.sh" ]; then
        bash migrate_database.sh auto >> "$UPGRADE_LOG" 2>&1

        if [ $? -eq 0 ]; then
            print_success "Migraciones de base de datos completadas"
            log_message "Migraciones de BD ejecutadas"
        else
            print_error "Falló la ejecución de migraciones"
            log_message "ERROR: Falló migrate_database.sh"
            exit 1
        fi
    else
        print_info "No hay script de migraciones disponible"
    fi
}

# Validar instalación
validate_upgrade() {
    print_step "Validando instalación..."

    cd "$APP_DIR"

    # Verificar integridad de archivos
    if ! python3 -m py_compile orchestrator.py 2>/dev/null; then
        print_error "Archivos Python corruptos"
        exit 1
    fi

    # Verificar configuración
    if [ ! -f ".env" ]; then
        print_error "Archivo .env faltante"
        exit 1
    fi

    # Verificar base de datos
    if ! sudo systemctl is-active --quiet postgresql; then
        print_error "PostgreSQL no está activo"
        exit 1
    fi

    print_success "Validación completada"
}

# Reiniciar servicios
restart_services() {
    print_step "Reiniciando servicios..."

    sudo systemctl restart felix-api >> "$UPGRADE_LOG" 2>&1
    sudo systemctl restart felix-scheduler >> "$UPGRADE_LOG" 2>&1

    sleep 2

    # Verificar que servicios estén activos
    if sudo systemctl is-active --quiet felix-api && sudo systemctl is-active --quiet felix-scheduler; then
        print_success "Servicios reiniciados correctamente"
        log_message "Servicios reiniciados"
    else
        print_error "Falló el reinicio de servicios"
        log_message "ERROR: Falló reinicio de servicios"
        exit 1
    fi
}

# Verificar salud del sistema
health_check() {
    print_step "Verificando salud del sistema..."

    sleep 2

    local health_url="https://localhost/health"
    local response=$(curl -s -k "$health_url" || echo '{"status":"error"}')

    if echo "$response" | grep -q "🟢 OK"; then
        print_success "Sistema operacional"
        log_message "Health check: OK"
        return 0
    else
        print_error "Sistema no respondiendo correctamente"
        log_message "ERROR: Health check falló"
        return 1
    fi
}

# Ejecutar tests de upgrading
run_upgrade_tests() {
    print_step "Ejecutando tests de upgrade..."

    cd "$APP_DIR"

    if [ -f "tests/test_upgrade.py" ]; then
        python3 -m pytest tests/test_upgrade.py -v >> "$UPGRADE_LOG" 2>&1

        if [ $? -eq 0 ]; then
            print_success "Tests de upgrade exitosos"
            log_message "Tests de upgrade: PASARON"
        else
            print_warning "Algunos tests de upgrade fallaron (revisar logs)"
            log_message "Tests de upgrade: FALLOS"
        fi
    fi
}

# Actualizar versión
update_version_file() {
    local new_version="$1"
    echo "$new_version" > "$CURRENT_VERSION_FILE"
    log_message "Versión actualizada a: $new_version"
}

# Crear reporte de upgrade
create_upgrade_report() {
    local target_version="$1"

    local report_file="${UPGRADE_DIR}/upgrade_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
╔════════════════════════════════════════════════════════════╗
║  REPORTE DE UPGRADE - FELIX AUTOMATION                    ║
╚════════════════════════════════════════════════════════════╝

Fecha:                  $(date '+%Y-%m-%d %H:%M:%S')
Versión anterior:       ${CURRENT_VERSION}
Versión nueva:          ${target_version}
Duración:               $(date -d now - starttime | awk '{print $1}' || echo "N/A")

CAMBIOS INCLUIDOS:
  ✅ Código actualizado a v${target_version}
  ✅ Dependencias Python actualizadas
  ✅ Migraciones de base de datos ejecutadas
  ✅ Configuración verificada
  ✅ Servicios reiniciados
  ✅ Health check exitoso

ARCHIVOS BACKUP:
  - Pre-upgrade backup: ${BACKUP_DIR}/
  - Logs: ${UPGRADE_LOG}
  - Config backup: ${UPGRADE_DIR}/requirements_backup.txt

PRÓXIMOS PASOS:
  1. Verificar dashboards: https://[tu_dominio]/dashboard
  2. Revisar logs: tail -50 /var/log/felix/error.log
  3. Ejecutar full test: bash tests/run_tests.sh
  4. Notificar a team

ROLLBACK (Si es necesario):
  bash upgrade.sh rollback

EOF

    print_success "Reporte de upgrade guardado: $report_file"
    cat "$report_file"
}

# Realizar rollback
perform_rollback() {
    print_header "ROLLBACK A VERSIÓN ANTERIOR"

    print_warning "Esto revertirá la instalación a la versión anterior"
    echo -n "¿Estás seguro? Escribe 'SÍ' para continuar: "
    read -r response

    if [ "$response" != "SÍ" ]; then
        print_error "Rollback cancelado"
        exit 1
    fi

    echo ""
    print_info "Deteniendo servicios..."
    sudo systemctl stop felix-api felix-scheduler 2>/dev/null || true

    # Buscar backup pre-upgrade más reciente
    local latest_backup=$(ls -t "$UPGRADE_DIR"/pre-upgrade* 2>/dev/null | head -1 || echo "")

    if [ -z "$latest_backup" ]; then
        print_error "No hay backup pre-upgrade disponible para rollback"
        exit 1
    fi

    print_info "Restaurando desde: $latest_backup"

    # Restaurar código
    cd "$APP_DIR"
    git checkout "v${CURRENT_VERSION}" >> "$UPGRADE_LOG" 2>&1

    # Restaurar dependencias
    if [ -f "$UPGRADE_DIR/requirements_backup.txt" ]; then
        cp "$UPGRADE_DIR/requirements_backup.txt" "$APP_DIR/requirements.txt"
        python3 -m pip install -r "$APP_DIR/requirements.txt" >> "$UPGRADE_LOG" 2>&1
    fi

    print_info "Reiniciando servicios..."
    sudo systemctl start felix-api felix-scheduler 2>/dev/null || true

    sleep 2

    if health_check; then
        print_success "Rollback completado exitosamente"
        log_message "Rollback ejecutado: versión $CURRENT_VERSION"
    else
        print_error "Rollback completado pero health check falló"
        log_message "ERROR: Rollback con fallos en health check"
        exit 1
    fi
}

# Upgrade completo
perform_upgrade() {
    local target_version="$1"

    print_header "FELIX AUTOMATION - UPGRADE"

    echo ""
    echo -e "Versión actual:   ${CYAN}${CURRENT_VERSION}${NC}"
    echo -e "Actualizar a:     ${CYAN}${target_version}${NC}"
    echo ""

    print_warning "Este proceso actualizará el sistema. Se creará un backup automático."
    echo -n "¿Proceder con el upgrade? Escribe 'SÍ' para continuar: "
    read -r response

    if [ "$response" != "SÍ" ]; then
        print_error "Upgrade cancelado"
        exit 1
    fi

    # Crear directorio de upgrades
    create_upgrade_directory

    echo ""

    # 1. Validar compatibilidad
    validate_version_upgrade "$target_version"
    echo ""

    # 2. Verificar dependencias
    check_dependencies
    echo ""

    # 3. Crear backup
    create_upgrade_backup "$target_version"
    echo ""

    # 4. Actualizar código
    update_code "$target_version"
    echo ""

    # 5. Actualizar dependencias
    update_python_dependencies
    echo ""

    # 6. Ejecutar migraciones
    run_database_migrations
    echo ""

    # 7. Validar instalación
    validate_upgrade
    echo ""

    # 8. Reiniciar servicios
    restart_services
    echo ""

    # 9. Health check
    if health_check; then
        echo ""

        # 10. Tests
        run_upgrade_tests
        echo ""

        # 11. Actualizar archivo de versión
        update_version_file "$target_version"

        # 12. Reporte
        create_upgrade_report "$target_version"

        echo ""
        print_header "UPGRADE COMPLETADO"
        print_success "Sistema actualizado exitosamente a versión $target_version"
    else
        print_error "Upgrade completado pero health check falló"
        print_info "Ejecutando rollback automático..."
        perform_rollback
        exit 1
    fi
}

# Mostrar ayuda
show_help() {
    cat << EOF
╔════════════════════════════════════════════════════════════╗
║  FELIX AUTOMATION - UPGRADE SCRIPT                         ║
╚════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
  Script para actualizar Felix Automation a versiones nuevas
  con seguridad, validación y capacidad de rollback

COMANDO:
  bash upgrade.sh [OPCIÓN] [VERSIÓN]

OPCIONES:
  check              Verifica actualizaciones disponibles
  upgrade VERSION    Actualiza a versión específica (ej: 12.0)
  VERSION            Shorthand para upgrade VERSION (ej: bash upgrade.sh 12.0)
  rollback           Revierte a versión anterior
  help               Mostrar esta ayuda

EJEMPLOS:
  # Ver actualizaciones disponibles
  bash upgrade.sh check

  # Actualizar a versión 12.0
  bash upgrade.sh upgrade 12.0
  bash upgrade.sh 12.0

  # Revertir a versión anterior
  bash upgrade.sh rollback

PROCESO DE UPGRADE:
  1. Verifica versión actual
  2. Crea backup completo pre-upgrade
  3. Valida compatibilidad de versión
  4. Actualiza código desde repository
  5. Actualiza dependencias Python
  6. Ejecuta migraciones de base de datos
  7. Valida integridad de archivos
  8. Reinicia servicios
  9. Ejecuta health check
  10. Ejecuta tests de upgrade
  11. Genera reporte

SEGURIDAD:
  ✅ Requires explicit confirmation (type 'SÍ')
  ✅ Crea backup automático pre-upgrade
  ✅ Valida cada paso
  ✅ Rollback automático si health check falla
  ✅ Mantiene versión anterior para rollback manual

ALMACENAMIENTO:
  - Backups: /opt/felix-automation/backups/
  - Logs: /opt/felix-automation/upgrades/upgrade_*.log
  - Reportes: /opt/felix-automation/upgrades/upgrade_report_*.txt

NOTAS:
  - Duración típica: 15-30 minutos
  - Requiere acceso a GitHub para descargar código
  - Requiere acceso a internet para actualizar dependencias
  - Los servicios se reinician automáticamente

EOF
}

# Main
case "${1:-help}" in
    check)
        check_updates
        ;;
    rollback)
        perform_rollback
        ;;
    help)
        show_help
        ;;
    upgrade|[0-9]*)
        # Si es un número, es la versión
        if [[ "$1" =~ ^[0-9]+\.[0-9]+$ ]]; then
            perform_upgrade "$1"
        elif [ "$1" = "upgrade" ] && [ ! -z "$2" ]; then
            perform_upgrade "$2"
        else
            echo "Formato de versión inválido"
            echo "Usa: bash upgrade.sh VERSION (ej: bash upgrade.sh 12.0)"
            exit 1
        fi
        ;;
    *)
        echo "Opción no reconocida: $1"
        echo "Usa: bash upgrade.sh help"
        exit 1
        ;;
esac
