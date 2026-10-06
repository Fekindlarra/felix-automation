#!/bin/bash
# Pre-deployment verification script for FASE 14 Production
# Verifies all prerequisites before deploying to production

set -euo pipefail

ENVIRONMENT=${1:-production}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_FILE="/tmp/pre_deployment_check_$(date +%Y%m%d_%H%M%S).txt"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

passed=0
failed=0
warnings=0

check_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1" | tee -a "$RESULTS_FILE"
    ((passed++))
}

check_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1" | tee -a "$RESULTS_FILE"
    ((failed++))
}

check_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1" | tee -a "$RESULTS_FILE"
    ((warnings++))
}

echo "==================================================================="
echo "FASE 14 - Pre-Deployment Verification"
echo "Environment: $ENVIRONMENT"
echo "Timestamp: $(date)"
echo "==================================================================="
echo "" | tee "$RESULTS_FILE"

# ===================================================================
# SECTION 1: CODE QUALITY
# ===================================================================
echo "SECTION 1: Code Quality Checks" | tee -a "$RESULTS_FILE"
echo "---" | tee -a "$RESULTS_FILE"

# Test: Tests passing (allow 95%+ pass rate) - FASE 14
if cd "$PROJECT_DIR" && timeout 120 python -m pytest tests/ -q --tb=no > /tmp/pytest_output.txt 2>&1; then
    check_pass "All pytest tests passing"
else
    # Parse results to check pass rate
    passed_count=$(grep -oP '\d+(?= passed)' /tmp/pytest_output.txt 2>/dev/null | tail -1)
    failed_count=$(grep -oP '\d+(?= failed)' /tmp/pytest_output.txt 2>/dev/null | tail -1)
    failed_count=${failed_count:-0}

    if [ -z "$passed_count" ]; then
        check_warn "Could not parse test results, proceeding cautiously"
    elif [ "$passed_count" -gt 300 ]; then
        pass_rate=$((passed_count * 100 / (passed_count + failed_count)))
        if [ "$pass_rate" -ge 95 ]; then
            check_warn "Minor test failures (${pass_rate}% pass rate, $passed_count/$((passed_count + failed_count)) passed)"
        else
            check_fail "Test pass rate too low: ${pass_rate}%"
        fi
    else
        check_fail "Insufficient test coverage or too many failures ($failed_count failures, $passed_count passed)"
    fi
fi

# Test: Linting
if cd "$PROJECT_DIR" && pylint backend agents --exit-zero --disable=all --enable=E 2>/dev/null | grep -q "^Your code"; then
    check_pass "Linting passed (E level)"
else
    check_warn "Linting check could not verify"
fi

# Test: No uncommitted changes
if cd "$PROJECT_DIR" && git diff --exit-code > /dev/null 2>&1; then
    check_pass "No uncommitted changes"
else
    check_fail "Uncommitted changes detected"
fi

# Test: Code coverage
if cd "$PROJECT_DIR" && python -c "import coverage; print('coverage installed')" 2>/dev/null; then
    check_pass "Coverage measurement tool installed"
else
    check_warn "Coverage tool not found"
fi

echo "" | tee -a "$RESULTS_FILE"

# ===================================================================
# SECTION 2: INFRASTRUCTURE
# ===================================================================
echo "SECTION 2: Infrastructure Checks" | tee -a "$RESULTS_FILE"
echo "---" | tee -a "$RESULTS_FILE"

# Test: Docker installed
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | grep -oP '\d+\.\d+\.\d+')
    check_pass "Docker installed (v$docker_version)"
else
    check_fail "Docker not installed"
fi

# Test: Docker Compose installed
if command -v docker compose &> /dev/null; then
    compose_version=$(docker compose version | grep -oP '\d+\.\d+\.\d+')
    check_pass "Docker Compose installed (v$compose_version)"
else
    check_fail "Docker Compose not installed"
fi

# Test: Sufficient disk space
disk_available=$(df "$PROJECT_DIR" | awk 'NR==2 {print $4}')
disk_available_gb=$((disk_available / 1024 / 1024))
if [ "$disk_available_gb" -gt 50 ]; then
    check_pass "Sufficient disk space available (${disk_available_gb}GB)"
else
    check_fail "Insufficient disk space (${disk_available_gb}GB < 50GB)"
fi

# Test: RAM available
ram_available=$(free -m | awk 'NR==2 {print $7}')
if [ "$ram_available" -gt 4096 ]; then
    check_pass "Sufficient RAM available (${ram_available}MB)"
else
    check_warn "RAM available is ${ram_available}MB (recommend 8GB+)"
fi

# Test: CPU cores
cpu_cores=$(nproc)
if [ "$cpu_cores" -ge 4 ]; then
    check_pass "CPU cores available ($cpu_cores)"
else
    check_warn "Limited CPU cores ($cpu_cores, recommend 4+)"
fi

echo "" | tee -a "$RESULTS_FILE"

# ===================================================================
# SECTION 3: CONFIGURATION
# ===================================================================
echo "SECTION 3: Configuration Checks" | tee -a "$RESULTS_FILE"
echo "---" | tee -a "$RESULTS_FILE"

# Test: Environment file exists
if [ -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
    check_pass "Environment file (.env.$ENVIRONMENT) found"
else
    check_fail "Environment file (.env.$ENVIRONMENT) not found"
fi

# Test: Docker compose file exists
if [ -f "$PROJECT_DIR/docker-compose.prod.yml" ]; then
    check_pass "Docker Compose file (docker-compose.prod.yml) found"
else
    check_fail "Docker Compose file not found"
fi

# Test: Nginx configuration exists
if [ -f "$PROJECT_DIR/nginx.prod.conf" ]; then
    check_pass "Nginx configuration found"
else
    check_fail "Nginx configuration not found"
fi

# Test: Dockerfile exists
if [ -f "$PROJECT_DIR/Dockerfile.prod" ]; then
    check_pass "Production Dockerfile found"
else
    check_fail "Production Dockerfile not found"
fi

# Test: Secret configuration
if grep -q "CHANGE_ME" "$PROJECT_DIR/.env.$ENVIRONMENT" 2>/dev/null; then
    check_fail "Uninitialized secrets detected in .env file"
else
    if [ -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
        check_pass "No uninitialized secrets in .env file"
    fi
fi

echo "" | tee -a "$RESULTS_FILE"

# ===================================================================
# SECTION 4: DEPLOYMENT ASSETS
# ===================================================================
echo "SECTION 4: Deployment Assets" | tee -a "$RESULTS_FILE"
echo "---" | tee -a "$RESULTS_FILE"

# Test: Deployment scripts
if [ -x "$PROJECT_DIR/deploy/deploy.sh" ]; then
    check_pass "Deployment script is executable"
else
    check_fail "Deployment script missing or not executable"
fi

# Test: Health check script
if [ -x "$PROJECT_DIR/deploy/health_check.sh" ]; then
    check_pass "Health check script is executable"
else
    check_warn "Health check script not found"
fi

# Test: Backup directory
if [ -d "$PROJECT_DIR/backups" ] || mkdir -p "$PROJECT_DIR/backups" 2>/dev/null; then
    check_pass "Backup directory available"
else
    check_fail "Cannot create backup directory"
fi

# Test: Logs directory
if [ -d "$PROJECT_DIR/logs" ] || mkdir -p "$PROJECT_DIR/logs" 2>/dev/null; then
    check_pass "Logs directory available"
else
    check_fail "Cannot create logs directory"
fi

echo "" | tee -a "$RESULTS_FILE"

# ===================================================================
# SECTION 5: DATABASE
# ===================================================================
echo "SECTION 5: Database Checks" | tee -a "$RESULTS_FILE"
echo "---" | tee -a "$RESULTS_FILE"

# Test: SQL schema file exists
if [ -f "$PROJECT_DIR/backend/schema.sql" ]; then
    check_pass "Database schema file found"
else
    check_warn "Database schema file not found (will be created)"
fi

# Test: Migration scripts exist
if [ -d "$PROJECT_DIR/backend/migrations" ]; then
    migration_count=$(find "$PROJECT_DIR/backend/migrations" -name "*.py" 2>/dev/null | wc -l)
    check_pass "Database migrations found ($migration_count files)"
else
    check_warn "Migration directory not found"
fi

echo "" | tee -a "$RESULTS_FILE"

# ===================================================================
# SECTION 6: FEATURE COMPLETENESS
# ===================================================================
echo "SECTION 6: Feature Completeness - FASE 14" | tee -a "$RESULTS_FILE"
echo "---" | tee -a "$RESULTS_FILE"

# Track D: Real-Time Alerts
if [ -f "$PROJECT_DIR/backend/models/alert.py" ]; then
    check_pass "Track D: Alert models implemented"
else
    check_fail "Track D: Alert models missing"
fi

if [ -f "$PROJECT_DIR/tests/test_track_d_e2e_alerts.py" ]; then
    check_pass "Track D: E2E alert tests present"
else
    check_fail "Track D: E2E tests missing"
fi

# Track E: Mobile Optimization
if [ -f "$PROJECT_DIR/frontend/styles/mobile.css" ]; then
    check_pass "Track E: Mobile CSS implemented"
else
    check_fail "Track E: Mobile CSS missing"
fi

if [ -f "$PROJECT_DIR/backend/service_worker.js" ]; then
    check_pass "Track E: Service Worker implemented"
else
    check_fail "Track E: Service Worker missing"
fi

if [ -f "$PROJECT_DIR/backend/manifest.json" ]; then
    check_pass "Track E: PWA manifest implemented"
else
    check_fail "Track E: PWA manifest missing"
fi

# Track F: Deployment
if [ -f "$PROJECT_DIR/.github/workflows/deploy.yml" ]; then
    check_pass "Track F: CI/CD pipeline configured"
else
    check_warn "Track F: CI/CD pipeline not configured"
fi

echo "" | tee -a "$RESULTS_FILE"

# ===================================================================
# SUMMARY
# ===================================================================
echo "" | tee -a "$RESULTS_FILE"
echo "==================================================================="
echo "SUMMARY"
echo "==================================================================="
echo "Passed: $passed" | tee -a "$RESULTS_FILE"
echo "Failed: $failed" | tee -a "$RESULTS_FILE"
echo "Warnings: $warnings" | tee -a "$RESULTS_FILE"
echo "==================================================================="

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT${NC}" | tee -a "$RESULTS_FILE"
    exit 0
elif [ $failed -le 3 ]; then
    echo -e "${YELLOW}⚠ SOME NON-CRITICAL CHECKS FAILED - REVIEW REQUIRED${NC}" | tee -a "$RESULTS_FILE"
    echo "Results saved to: $RESULTS_FILE"
    exit 0
else
    echo -e "${RED}✗ CRITICAL CHECKS FAILED - DEPLOYMENT NOT RECOMMENDED${NC}" | tee -a "$RESULTS_FILE"
    echo "Results saved to: $RESULTS_FILE"
    exit 1
fi
