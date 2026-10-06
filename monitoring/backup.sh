#!/bin/bash
# ====================================================================
# Backup Automation Script
# Creates daily backups with rotation
# ====================================================================

BACKUP_DIR="backups"
DB_FILE="data/pipeline.sqlite"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📦 Starting backup at $(date)"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
BACKUP_FILE="$BACKUP_DIR/pipeline_${TIMESTAMP}.sqlite"
cp "$DB_FILE" "$BACKUP_FILE"

if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup created: $BACKUP_FILE ($SIZE)"
else
    echo "✗ Backup failed"
    exit 1
fi

# Rotate old backups (keep last 7 days)
find "$BACKUP_DIR" -name "pipeline_*.sqlite" -mtime +$RETENTION_DAYS -delete
echo "✓ Old backups cleaned (retention: $RETENTION_DAYS days)"

# Calculate backup stats
TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/pipeline_*.sqlite 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo "✓ Backup statistics:"
echo "  - Total backups: $TOTAL_BACKUPS"
echo "  - Total size: $TOTAL_SIZE"
echo "✅ Backup completed successfully"
