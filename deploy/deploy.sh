#!/bin/bash
# Production deployment script for Felix Automation FASE 14
# Usage: ./deploy/deploy.sh [staging|production] [version]

set -euo pipefail

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$SCRIPT_DIR/deploy_$(date +%Y%m%d_%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deploy_checks() {
    log "Running pre-deployment checks..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    log "✓ Docker is installed"

    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    log "✓ Docker Compose is installed"

    # Check environment file
    if [ ! -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
        error "Environment file .env.$ENVIRONMENT not found"
    fi
    log "✓ Environment file found"

    # Check required secrets
    if [ -z "${DB_PASSWORD:-}" ] && [ "$ENVIRONMENT" = "production" ]; then
        error "DB_PASSWORD environment variable not set"
    fi
    log "✓ Environment variables configured"
}

# Backup database
backup_database() {
    log "Creating database backup..."

    local backup_file="$PROJECT_DIR/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p "$PROJECT_DIR/backups"

    docker compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T db \
        pg_dump -U "${DB_USER:-felix_user}" felix_automation \
        > "$backup_file" || error "Database backup failed"

    log "✓ Database backup created: $backup_file"
}

# Build Docker image
build_image() {
    log "Building Docker image..."

    cd "$PROJECT_DIR"
    docker build \
        -f Dockerfile.prod \
        -t "felix-automation:$VERSION" \
        -t "felix-automation:latest" \
        . || error "Docker build failed"

    log "✓ Docker image built successfully"
}

# Deploy application
deploy_application() {
    log "Deploying application to $ENVIRONMENT..."

    cd "$PROJECT_DIR"

    # Load environment
    if [ -f ".env.$ENVIRONMENT" ]; then
        set -a
        source ".env.$ENVIRONMENT"
        set +a
    fi

    # Pull latest images
    log "Pulling latest images..."
    docker compose -f docker-compose.prod.yml pull || warn "Failed to pull images"

    # Start services
    log "Starting services..."
    docker compose -f docker-compose.prod.yml up -d || error "Failed to start services"

    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker compose -f docker-compose.prod.yml exec -T app curl -f http://localhost:5000/health &>/dev/null; then
            log "✓ Application is healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        error "Application failed to become healthy"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    cd "$PROJECT_DIR"
    docker compose -f docker-compose.prod.yml exec -T app flask db upgrade \
        || error "Database migration failed"

    log "✓ Database migrations completed"
}

# Health checks
run_health_checks() {
    log "Running health checks..."

    # API health
    if ! docker compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T app curl -f http://localhost:5000/health &>/dev/null; then
        error "Application health check failed"
    fi
    log "✓ Application health check passed"

    # Database health
    if ! docker compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T db pg_isready -U "${DB_USER:-felix_user}" &>/dev/null; then
        error "Database health check failed"
    fi
    log "✓ Database health check passed"

    # Redis health
    if ! docker compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T cache redis-cli ping &>/dev/null; then
        error "Cache health check failed"
    fi
    log "✓ Cache health check passed"
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."

    cd "$PROJECT_DIR"
    docker compose -f docker-compose.prod.yml exec -T app \
        pytest tests/smoke -v --tb=short || warn "Some smoke tests failed"

    log "✓ Smoke tests completed"
}

# Rollback function
rollback() {
    error_msg="${1:-Deployment failed}"
    log "Rolling back deployment due to: $error_msg"

    cd "$PROJECT_DIR"
    docker compose -f docker-compose.prod.yml down || warn "Failed to stop services"
    docker compose -f docker-compose.prod.yml up -d || error "Rollback failed"

    # Restore from backup if available
    local latest_backup=$(ls -t "$PROJECT_DIR/backups"/db_backup_*.sql 2>/dev/null | head -1)
    if [ -n "$latest_backup" ]; then
        log "Restoring database from backup..."
        docker compose -f docker-compose.prod.yml exec -T db \
            psql -U "${DB_USER:-felix_user}" felix_automation < "$latest_backup" \
            || warn "Database restore failed"
    fi

    error "Deployment rolled back"
}

# Send notification
send_notification() {
    local status=$1
    local message=$2

    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        local color=$([ "$status" = "success" ] && echo "good" || echo "danger")
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"Felix Automation Deployment - $ENVIRONMENT\",
                    \"text\": \"$message\",
                    \"footer\": \"Deployment completed at $(date)\",
                    \"ts\": $(date +%s)
                }]
            }" || warn "Failed to send Slack notification"
    fi
}

# Main deployment flow
main() {
    log "==================================================================="
    log "Felix Automation FASE 14 - Deployment Script"
    log "Environment: $ENVIRONMENT"
    log "Version: $VERSION"
    log "==================================================================="

    # Validate environment
    if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
        error "Invalid environment: $ENVIRONMENT (use 'staging' or 'production')"
    fi

    # Run deployment steps
    trap 'rollback "Script interrupted"' INT TERM

    pre_deploy_checks || exit 1
    backup_database || exit 1
    build_image || exit 1
    deploy_application || exit 1
    run_migrations || exit 1
    run_health_checks || exit 1
    run_smoke_tests || exit 1

    log "==================================================================="
    log "✓ Deployment completed successfully!"
    log "Environment: $ENVIRONMENT"
    log "Version: $VERSION"
    log "==================================================================="

    send_notification "success" "Deployment to $ENVIRONMENT completed successfully"
}

# Run main function
main "$@"
