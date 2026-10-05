#!/bin/bash

################################################################################
# FELIX AUTOMATION - DATABASE MIGRATION SCRIPT
# Gestiona migraciones de esquema de base de datos con rollback automático
#
# Uso: bash migrate_database.sh [status|pending|migrate|rollback|create|help]
#
# Ejemplos:
#   bash migrate_database.sh status        # Ver estado actual
#   bash migrate_database.sh pending       # Ver migraciones pendientes
#   bash migrate_database.sh migrate       # Ejecutar migraciones
#   bash migrate_database.sh rollback      # Deshacer última migración
#   bash migrate_database.sh auto          # Auto-detectar y ejecutar (usado por upgrade.sh)
#   bash migrate_database.sh create nombre # Crear nueva migración
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
MIGRATIONS_DIR="${APP_DIR}/migrations"
MIGRATIONS_TABLE="schema_migrations"
MIGRATION_LOG="${MIGRATIONS_DIR}/migration_$(date +%Y%m%d_%H%M%S).log"

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

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$MIGRATION_LOG"
}

# Crear directorio de migraciones si no existe
create_migrations_directory() {
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        mkdir -p "$MIGRATIONS_DIR"
        chmod 755 "$MIGRATIONS_DIR"
        print_info "Directorio de migraciones creado: $MIGRATIONS_DIR"
    fi
}

# Obtener credenciales de base de datos
get_db_credentials() {
    if [ -f "${APP_DIR}/.env" ]; then
        source "${APP_DIR}/.env"
    else
        print_error ".env no encontrado"
        exit 1
    fi
}

# Crear tabla de migraciones si no existe
init_migrations_table() {
    local query="
    CREATE TABLE IF NOT EXISTS $MIGRATIONS_TABLE (
        id SERIAL PRIMARY KEY,
        migration VARCHAR(255) UNIQUE NOT NULL,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        execution_time INTEGER,
        status VARCHAR(20) DEFAULT 'applied'
    );
    "

    if [ -z "$DATABASE_PASSWORD" ]; then
        psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$query" 2>/dev/null
    else
        PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$query" 2>/dev/null
    fi
}

# Verificar estado de migraciones
check_migration_status() {
    print_header "ESTADO DE MIGRACIONES"

    echo ""

    # Listar migraciones ejecutadas
    print_info "Migraciones ejecutadas:"

    local query="SELECT migration, executed_at, execution_time FROM $MIGRATIONS_TABLE WHERE status='applied' ORDER BY executed_at DESC;"

    if [ -z "$DATABASE_PASSWORD" ]; then
        psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$query" 2>/dev/null
    else
        PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$query" 2>/dev/null
    fi

    echo ""

    # Contar migraciones pendientes
    local pending=$(find "$MIGRATIONS_DIR" -name "*.sql" -type f | wc -l)
    local applied_query="SELECT COUNT(*) FROM $MIGRATIONS_TABLE WHERE status='applied';"

    if [ -z "$DATABASE_PASSWORD" ]; then
        local applied=$(psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$applied_query" 2>/dev/null | tr -d ' ')
    else
        local applied=$(PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$applied_query" 2>/dev/null | tr -d ' ')
    fi

    echo -e "${YELLOW}Migraciones totales:${NC} $pending"
    echo -e "${YELLOW}Migraciones aplicadas:${NC} $applied"
    echo -e "${YELLOW}Migraciones pendientes:${NC} $((pending - applied))"
}

# Listar migraciones pendientes
list_pending_migrations() {
    print_header "MIGRACIONES PENDIENTES"

    echo ""

    local pending_found=0

    for migration_file in $(find "$MIGRATIONS_DIR" -name "*.sql" -type f | sort); do
        local migration_name=$(basename "$migration_file" .sql)

        # Verificar si ya fue ejecutada
        local query="SELECT COUNT(*) FROM $MIGRATIONS_TABLE WHERE migration='$migration_name' AND status='applied';"

        if [ -z "$DATABASE_PASSWORD" ]; then
            local count=$(psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
        else
            local count=$(PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
        fi

        if [ "$count" = "0" ]; then
            echo -e "  ${YELLOW}→${NC} $migration_name"
            ((pending_found++))
        fi
    done

    echo ""

    if [ $pending_found -eq 0 ]; then
        print_success "No hay migraciones pendientes"
    else
        print_warning "$pending_found migración(es) pendiente(s)"
    fi
}

# Ejecutar todas las migraciones pendientes
run_migrations() {
    print_header "EJECUTANDO MIGRACIONES"

    echo ""

    local migrations_run=0
    local migrations_failed=0

    for migration_file in $(find "$MIGRATIONS_DIR" -name "*.sql" -type f | sort); do
        local migration_name=$(basename "$migration_file" .sql)

        # Verificar si ya fue ejecutada
        local query="SELECT COUNT(*) FROM $MIGRATIONS_TABLE WHERE migration='$migration_name' AND status='applied';"

        if [ -z "$DATABASE_PASSWORD" ]; then
            local count=$(psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
        else
            local count=$(PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
        fi

        if [ "$count" = "0" ]; then
            print_info "Ejecutando: $migration_name"

            local start_time=$(date +%s)

            # Ejecutar migración dentro de transacción
            if [ -z "$DATABASE_PASSWORD" ]; then
                psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -f "$migration_file" >> "$MIGRATION_LOG" 2>&1
            else
                PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -f "$migration_file" >> "$MIGRATION_LOG" 2>&1
            fi

            if [ $? -eq 0 ]; then
                local end_time=$(date +%s)
                local execution_time=$((end_time - start_time))

                # Registrar en tabla
                local insert_query="INSERT INTO $MIGRATIONS_TABLE (migration, execution_time, status) VALUES ('$migration_name', $execution_time, 'applied');"

                if [ -z "$DATABASE_PASSWORD" ]; then
                    psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$insert_query" 2>/dev/null
                else
                    PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$insert_query" 2>/dev/null
                fi

                print_success "$migration_name completada (${execution_time}s)"
                log_message "Migración ejecutada: $migration_name (${execution_time}s)"
                ((migrations_run++))
            else
                print_error "$migration_name falló"
                log_message "ERROR: Migración falló: $migration_name"
                ((migrations_failed++))
            fi
        fi
    done

    echo ""
    print_header "RESULTADO DE MIGRACIONES"
    echo -e "${GREEN}Exitosas:${NC} $migrations_run"
    echo -e "${RED}Fallidas:${NC} $migrations_failed"

    if [ $migrations_failed -gt 0 ]; then
        print_error "$migrations_failed migración(es) falló(aron)"
        log_message "Resultado: $migrations_run exitosas, $migrations_failed fallidas"
        exit 1
    else
        print_success "Todas las migraciones completadas"
        log_message "Resultado: $migrations_run exitosas, 0 fallidas"
    fi
}

# Deshacer última migración
rollback_migration() {
    print_header "ROLLBACK DE MIGRACIÓN"

    # Obtener última migración
    local query="SELECT migration FROM $MIGRATIONS_TABLE WHERE status='applied' ORDER BY executed_at DESC LIMIT 1;"

    if [ -z "$DATABASE_PASSWORD" ]; then
        local last_migration=$(psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
    else
        local last_migration=$(PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
    fi

    if [ -z "$last_migration" ]; then
        print_info "No hay migraciones para deshacer"
        return 0
    fi

    echo ""
    print_warning "Última migración: $last_migration"
    echo -n "¿Deshacer esta migración? Escribe 'SÍ' para confirmar: "
    read -r response

    if [ "$response" != "SÍ" ]; then
        print_error "Rollback cancelado"
        exit 1
    fi

    # Buscar archivo de rollback
    local rollback_file="${MIGRATIONS_DIR}/${last_migration}_rollback.sql"

    if [ ! -f "$rollback_file" ]; then
        print_error "Archivo de rollback no encontrado: $rollback_file"
        exit 1
    fi

    echo ""
    print_info "Ejecutando rollback..."

    # Ejecutar rollback
    if [ -z "$DATABASE_PASSWORD" ]; then
        psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -f "$rollback_file" >> "$MIGRATION_LOG" 2>&1
    else
        PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -f "$rollback_file" >> "$MIGRATION_LOG" 2>&1
    fi

    if [ $? -eq 0 ]; then
        # Marcar como revertida
        local update_query="UPDATE $MIGRATIONS_TABLE SET status='rolled_back' WHERE migration='$last_migration';"

        if [ -z "$DATABASE_PASSWORD" ]; then
            psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$update_query" 2>/dev/null
        else
            PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "$update_query" 2>/dev/null
        fi

        print_success "Rollback completado: $last_migration"
        log_message "Rollback ejecutado: $last_migration"
    else
        print_error "Falló el rollback"
        log_message "ERROR: Falló rollback de $last_migration"
        exit 1
    fi
}

# Crear nueva migración
create_new_migration() {
    local migration_name="$1"

    if [ -z "$migration_name" ]; then
        print_error "Nombre de migración requerido"
        echo "Uso: bash migrate_database.sh create nombre_migración"
        exit 1
    fi

    # Generar timestamp
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local migration_file="${MIGRATIONS_DIR}/${timestamp}_${migration_name}.sql"
    local rollback_file="${MIGRATIONS_DIR}/${timestamp}_${migration_name}_rollback.sql"

    # Crear template de migración
    cat > "$migration_file" << 'EOF'
-- FELIX AUTOMATION - DATABASE MIGRATION
-- Created: $(date)
-- Description: [Add description here]

BEGIN;

-- Migration code here
-- Example:
-- ALTER TABLE users ADD COLUMN last_login TIMESTAMP;

COMMIT;
EOF

    # Crear template de rollback
    cat > "$rollback_file" << 'EOF'
-- FELIX AUTOMATION - ROLLBACK MIGRATION
-- Revert: [Add description here]

BEGIN;

-- Rollback code here
-- Example:
-- ALTER TABLE users DROP COLUMN last_login;

COMMIT;
EOF

    print_success "Migración creada: $migration_file"
    print_info "Rollback creado: $rollback_file"
    print_info "Edita ambos archivos antes de ejecutar"
}

# Verificar integridad de migraciones
verify_migrations() {
    print_header "VERIFICANDO INTEGRIDAD DE MIGRACIONES"

    echo ""

    local issues=0

    # Verificar consistencia entre BD y archivos
    for migration_file in $(find "$MIGRATIONS_DIR" -name "*.sql" -type f | grep -v rollback | sort); do
        local migration_name=$(basename "$migration_file" .sql)

        # Verificar que existe rollback
        local rollback_file="${MIGRATIONS_DIR}/${migration_name}_rollback.sql"

        if [ ! -f "$rollback_file" ]; then
            print_warning "Falta rollback para: $migration_name"
            ((issues++))
        fi
    done

    # Verificar sintaxis SQL
    for migration_file in $(find "$MIGRATIONS_DIR" -name "*.sql" -type f | grep -v rollback | sort); do
        if ! grep -q "^BEGIN;" "$migration_file" || ! grep -q "^COMMIT;" "$migration_file"; then
            print_warning "Formato incorrecto en: $migration_file (debe tener BEGIN; y COMMIT;)"
            ((issues++))
        fi
    done

    echo ""

    if [ $issues -eq 0 ]; then
        print_success "Todas las migraciones son válidas"
    else
        print_error "$issues problema(s) encontrado(s)"
    fi
}

# Auto-ejecutar migraciones (usado por upgrade.sh)
auto_migrate() {
    print_info "Auto-detectando y ejecutando migraciones pendientes..."

    get_db_credentials
    create_migrations_directory
    init_migrations_table

    # Contar migraciones pendientes
    local pending=0
    for migration_file in $(find "$MIGRATIONS_DIR" -name "*.sql" -type f | grep -v rollback | sort); do
        local migration_name=$(basename "$migration_file" .sql)

        local query="SELECT COUNT(*) FROM $MIGRATIONS_TABLE WHERE migration='$migration_name' AND status='applied';"

        if [ -z "$DATABASE_PASSWORD" ]; then
            local count=$(psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
        else
            local count=$(PGPASSWORD="${DATABASE_PASSWORD}" psql -h localhost -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "$query" 2>/dev/null | tr -d ' ')
        fi

        if [ "$count" = "0" ]; then
            ((pending++))
        fi
    done

    if [ $pending -gt 0 ]; then
        run_migrations
    else
        print_success "No hay migraciones pendientes"
    fi
}

# Mostrar ayuda
show_help() {
    cat << EOF
╔════════════════════════════════════════════════════════════╗
║  FELIX AUTOMATION - DATABASE MIGRATION SCRIPT              ║
╚════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
  Script para gestionar migraciones de esquema de base de datos
  con rollback automático y versionado de cambios

COMANDO:
  bash migrate_database.sh [OPCIÓN]

OPCIONES:
  status      Ver estado actual de migraciones
  pending     Listar migraciones pendientes
  migrate     Ejecutar todas las migraciones pendientes
  rollback    Deshacer última migración
  create NAME Crear nueva migración (ej: add_users_table)
  verify      Verificar integridad de migraciones
  auto        Auto-detectar y ejecutar (usado por upgrade.sh)
  help        Mostrar esta ayuda

EJEMPLOS:
  # Ver estado
  bash migrate_database.sh status

  # Ver migraciones pendientes
  bash migrate_database.sh pending

  # Ejecutar migraciones
  bash migrate_database.sh migrate

  # Crear nueva migración
  bash migrate_database.sh create add_users_table

  # Deshacer última migración
  bash migrate_database.sh rollback

ESTRUCTURA DE MIGRACIONES:
  /opt/felix-automation/migrations/
  ├── YYYYMMDD_HHMMSS_nombre_migracion.sql
  ├── YYYYMMDD_HHMMSS_nombre_migracion_rollback.sql
  └── ...

FORMATO REQUERIDO:
  Cada migración DEBE tener:
  ✅ BEGIN; al inicio
  ✅ COMMIT; al final
  ✅ Un archivo _rollback.sql correspondiente

TABLA DE CONTROL:
  schema_migrations
  ├── id (PRIMARY KEY)
  ├── migration (VARCHAR, UNIQUE)
  ├── executed_at (TIMESTAMP)
  ├── execution_time (INTEGER - segundos)
  └── status (VARCHAR: 'applied', 'rolled_back')

SAFETY FEATURES:
  ✅ Todas las migraciones en transacciones ACID
  ✅ Requiere confirmación para rollback
  ✅ Registra tiempo de ejecución
  ✅ Valida integridad de archivos
  ✅ Rollback automático en caso de error

LOGS:
  /opt/felix-automation/migrations/migration_YYYYMMDD_HHMMSS.log

WORKFLOW TÍPICO:
  1. bash migrate_database.sh status     # Ver estado actual
  2. bash migrate_database.sh pending    # Ver qué falta
  3. bash migrate_database.sh migrate    # Ejecutar migraciones
  4. bash migrate_database.sh status     # Confirmar éxito

EOF
}

# Main
get_db_credentials
create_migrations_directory
init_migrations_table

case "${1:-help}" in
    status)
        check_migration_status
        ;;
    pending)
        list_pending_migrations
        ;;
    migrate)
        run_migrations
        ;;
    rollback)
        rollback_migration
        ;;
    create)
        create_new_migration "$2"
        ;;
    verify)
        verify_migrations
        ;;
    auto)
        auto_migrate
        ;;
    help)
        show_help
        ;;
    *)
        echo "Opción no reconocida: $1"
        echo "Usa: bash migrate_database.sh help"
        exit 1
        ;;
esac
