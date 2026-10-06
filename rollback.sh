#!/bin/bash
# ====================================================================
# FASE 14 - Emergency Rollback Script
# Restores database to previous stable state
# ====================================================================

set -e

echo "🔙 FASE 14 - EMERGENCY ROLLBACK PROCEDURE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if we're rolling back
if [ "$1" == "--confirm" ]; then
    CONFIRM=true
else
    echo "⚠️  This will restore the database from the most recent backup."
    echo "⚠️  Any changes since the backup will be lost."
    echo ""
    echo "To proceed with rollback, run:"
    echo "  bash rollback.sh --confirm"
    echo ""
    exit 0
fi

# ====================================================================
# PASO 1: Stop Current Service
# ====================================================================
echo -n "Stopping current service... "

# Try to kill FastAPI/Python process if running
pkill -f "python.*backend/main" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

sleep 1
echo -e "${GREEN}✓ Done${NC}"

# ====================================================================
# PASO 2: Find Latest Backup
# ====================================================================
echo -n "Finding latest backup... "

BACKUP_FILE=$(ls -t backups/pipeline_*.sqlite 2>/dev/null | head -1)

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}✗ No backup found!${NC}"
    echo "Cannot perform rollback without a backup file."
    exit 1
fi

echo -e "${GREEN}✓ Found: $BACKUP_FILE${NC}"

# ====================================================================
# PASO 3: Create Safety Backup
# ====================================================================
echo -n "Creating safety backup of current state... "

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BROKEN_BACKUP="backups/pipeline_broken_${TIMESTAMP}.sqlite"

if [ -f "data/pipeline.sqlite" ]; then
    cp data/pipeline.sqlite "$BROKEN_BACKUP"
    echo -e "${GREEN}✓ Saved to: $BROKEN_BACKUP${NC}"
else
    echo -e "${YELLOW}⚠ No current database to backup${NC}"
fi

# ====================================================================
# PASO 4: Restore from Backup
# ====================================================================
echo -n "Restoring database from backup... "

cp "$BACKUP_FILE" data/pipeline.sqlite
echo -e "${GREEN}✓ Database restored${NC}"

# ====================================================================
# PASO 5: Verify Restoration
# ====================================================================
echo -n "Verifying restoration... "

if python3 -c "import sqlite3; sqlite3.connect('data/pipeline.sqlite').execute('SELECT COUNT(*) FROM clients')" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database is operational${NC}"
else
    echo -e "${RED}✗ Database verification failed${NC}"
    echo ""
    echo "❌ ROLLBACK FAILED - Database is not operational"
    echo "Previous state saved to: $BROKEN_BACKUP"
    exit 1
fi

# ====================================================================
# PASO 6: Verify Health
# ====================================================================
echo ""
echo "Running health check..."
bash monitoring/health_check.sh

# ====================================================================
# Summary
# ====================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ ROLLBACK COMPLETED SUCCESSFULLY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Backup restored: $BACKUP_FILE"
echo "Previous state saved: $BROKEN_BACKUP"
echo ""
echo "To restart the service:"
echo "  python3 backend/main.py"
echo ""
echo "To analyze the broken state:"
echo "  cp $BROKEN_BACKUP data/pipeline.sqlite.broken"
echo ""
