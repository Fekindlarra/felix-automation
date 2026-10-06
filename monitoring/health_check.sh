#!/bin/bash
# Health Check Script for FASE 14 Production System

echo "🏥 FASE 14 Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HEALTH_SCORE=100
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Check 1: Database
echo -n "Database: "
if python3 -c "import sqlite3; sqlite3.connect('data/pipeline.sqlite').execute('SELECT COUNT(*) FROM clients')" > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    ((HEALTH_SCORE-=25))
fi

# Check 2: Configuration
echo -n "Configuration: "
if python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    ((HEALTH_SCORE-=20))
fi

# Check 3: Required Files
echo -n "Required Files: "
FILES_OK=true
for file in backend/auth.py init_database.py config.yaml .env; do
    if [ ! -f "$file" ]; then
        FILES_OK=false
        break
    fi
done
if [ "$FILES_OK" = true ]; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    ((HEALTH_SCORE-=15))
fi

# Check 4: Disk Space
echo -n "Disk Space: "
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✓ OK ($DISK_USAGE% used)"
else
    echo "✗ WARNING ($DISK_USAGE% used)"
    ((HEALTH_SCORE-=10))
fi

# Check 5: Python Environment
echo -n "Python Environment: "
if [ -f "venv/bin/python" ] || command -v python3 > /dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    ((HEALTH_SCORE-=20))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Health Score: $HEALTH_SCORE/100"

if [ $HEALTH_SCORE -eq 100 ]; then
    echo "Status: ✅ HEALTHY"
    exit 0
elif [ $HEALTH_SCORE -ge 80 ]; then
    echo "Status: ⚠️  DEGRADED"
    exit 1
else
    echo "Status: ❌ CRITICAL"
    exit 2
fi
