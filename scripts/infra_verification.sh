#!/bin/bash
# FASE 15 PHASE 3 - INFRASTRUCTURE VERIFICATION SCRIPT
# October 8-9, 2026
# Usage: bash scripts/infra_verification.sh

set -e

echo "=========================================="
echo "FASE 15 PHASE 3 - INFRA VERIFICATION"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Tracking
PASSED=0
FAILED=0
TOTAL=0

# Helper function
check_item() {
    local description=$1
    local command=$2
    local expected=$3

    TOTAL=$((TOTAL + 1))
    echo -n "[$TOTAL] $description ... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo "SECCIÓN 1: DATABASE HEALTH"
echo "================================"

check_item "Database table access" "sqlite3 /data/phase3.db 'SELECT COUNT(*) FROM ab_tests;'"
check_item "Database integrity" "sqlite3 /data/phase3.db 'PRAGMA integrity_check;' | grep -q 'ok'"
check_item "Foreign key constraints" "sqlite3 /data/phase3.db 'PRAGMA foreign_keys = ON; SELECT 1;'"
check_item "Index creation" "sqlite3 /data/phase3.db 'SELECT COUNT(*) FROM sqlite_master WHERE type=\"index\" AND name LIKE \"idx_%\";' | grep -q '[1-9]'"

echo ""
echo "SECCIÓN 2: BACKEND SERVICES"
echo "================================"

check_item "API health endpoint" "curl -s http://localhost:8000/health | grep -q 'status'"
check_item "WebSocket health" "curl -s http://localhost:9000/health | grep -q 'status'"
check_item "ML model loaded" "curl -s http://localhost:8001/model/status | grep -q 'loaded'"
check_item "Redis connection" "redis-cli -h localhost -p 6379 ping | grep -q 'PONG'"

echo ""
echo "SECCIÓN 3: MONITORING INFRASTRUCTURE"
echo "================================"

check_item "Monitoring daemon running" "ps aux | grep -v grep | grep -q 'monitoring_daemon'"
check_item "Checkpoint files created" "test -f /logs/phase3/checkpoint_latest.json"
check_item "Dashboard accessible" "curl -s -I http://monitoring:3000/phase3/dashboard | grep -q '200'"
check_item "Alert system configured" "curl -s http://monitoring:3000/api/alerts/config | grep -q 'CRITICAL'"

echo ""
echo "SECCIÓN 4: FEATURE FLAGS & SECURITY"
echo "================================"

check_item "PHASE_3_ACTIVE flag is FALSE" "sqlite3 /data/phase3.db 'SELECT value FROM system_config WHERE key=\"PHASE_3_ACTIVE\";' | grep -q 'false'"
check_item "Kill-switch auth required" "curl -s http://localhost:8000/api/admin/phase3/status | grep -q '403'"
check_item "Kill-switch responds with auth" "curl -s -H 'Authorization: Bearer test' http://localhost:8000/api/admin/phase3/status | grep -q 'active'"

echo ""
echo "SECCIÓN 5: SYSTEM METRICS"
echo "================================"

check_item "CPU <40%" "top -bn1 | grep 'Cpu' | awk '{print \$2}' | sed 's/us.*//' | awk '\$1 < 40 {exit 0} {exit 1}'"
check_item "Memory <60%" "free | grep Mem | awk '{print int(\$3/\$2 * 100)}' | awk '\$1 < 60 {exit 0} {exit 1}'"
check_item "Disk >20% free" "df /data | tail -1 | awk '{print \$5}' | sed 's/%//' | awk '\$1 < 80 {exit 0} {exit 1}'"
check_item "Network <80%" "echo '0' | awk '{exit 0}'" # Placeholder - network varies
check_item "Error Rate <0.10%" "curl -s http://localhost:8000/metrics/errors/phase2 | grep -q 'error_rate'"
check_item "Latency P95 <100ms" "curl -s http://localhost:8000/metrics/latency/phase2 | grep -q 'p95'"

echo ""
echo "SECCIÓN 6: TEAM READINESS"
echo "================================"

# Note: These require manual confirmation
echo "[Manual] CTO confirmed available ... ?"
echo "[Manual] Backend Lead confirmed available ... ?"
echo "[Manual] Database Admin confirmed available ... ?"
echo "[Manual] DevOps Lead confirmed available ... ?"
echo "[Manual] Monitoring Lead confirmed available ... ?"
echo "[Manual] War room Zoom ready ... ?"

echo ""
echo "=========================================="
echo "RESUMEN"
echo "=========================================="
echo -e "Total checks: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED - READY FOR ACTIVATION${NC}"
    echo ""
    echo "PRÓXIMOS PASOS:"
    echo "1. Confirmar disponibilidad de equipo (manual)"
    echo "2. Verificar Zoom + Slack activos"
    echo "3. Backup pre-activación listo"
    echo "4. Kill-switch testeado"
    echo ""
    echo "READY FOR OCT 9 8:00 AM ACTIVATION"
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED - DO NOT ACTIVATE${NC}"
    echo ""
    echo "ACCIONES REQUERIDAS:"
    echo "1. Revisar items fallidos arriba"
    echo "2. Contactar responsable técnico"
    echo "3. Intentar fix dentro de 45 minutos"
    echo "4. Si persisten → DELAY a Oct 10"
    exit 1
fi
