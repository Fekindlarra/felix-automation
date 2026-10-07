#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Activation Script
Activates Phase 3 for 24-hour production test (HORA 48-72)
Must pass all pre-flight checks before activation
"""

import logging
import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from phase3_preflights import Phase3Preflights


def main():
    """Main activation flow"""
    print("\n" + "="*70)
    print("🚀 FASE 15 Phase 3 - Activation Script")
    print("   HORA 48-72 (24-hour production test)")
    print("="*70 + "\n")
    
    # Find database
    db_path = "fase15.db"
    if not os.path.exists(db_path):
        logger.error(f"❌ Database not found at {db_path}")
        sys.exit(1)
    
    # Connect to database
    try:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
        logger.info(f"✅ Connected to database: {db_path}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    # Run pre-flight checks
    print("\n📋 Running Pre-Flight Checks...\n")
    preflights = Phase3Preflights(db_connection)
    result = preflights.run_all_checks()
    
    # Print check results
    print("\n" + "-"*70)
    for check_name, passed in result["checks"].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check_name}")
        if check_name in result.get("details", {}):
            print(f"         {result['details'][check_name]}")
    print("-"*70 + "\n")
    
    if not result["all_pass"]:
        logger.error(f"❌ Pre-flight checks FAILED")
        logger.error(f"   Blocked by: {result['blocked_reason']}")
        print("\n❌ Phase 3 activation BLOCKED due to pre-flight check failure\n")
        db_connection.close()
        sys.exit(1)
    
    # All checks passed - proceed with activation
    print("\n✅ All pre-flight checks PASSED!\n")
    
    # Create backup
    print("💾 Creating database backup...")
    try:
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"phase3_start_{timestamp}.sqlite"
        
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
    except Exception as e:
        logger.error(f"❌ Backup creation failed: {e}")
        db_connection.close()
        sys.exit(1)
    
    # Set Phase 3 active
    print("\n⚡ Activating Phase 3...")
    try:
        cursor = db_connection.cursor()
        
        # Create system_config table if needed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Set PHASE_3_ACTIVE flag
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVE', 'true', CURRENT_TIMESTAMP)
        """)
        
        # Store activation timestamp
        activation_time = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('PHASE_3_ACTIVATED_AT', ?, CURRENT_TIMESTAMP)
        """, (activation_time,))
        
        # Initialize checkpoint counter
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES ('CURRENT_CHECKPOINT', '0', CURRENT_TIMESTAMP)
        """)
        
        db_connection.commit()
        logger.info("✅ Phase 3 activated in database")
    except Exception as e:
        logger.error(f"❌ Failed to activate Phase 3: {e}")
        db_connection.close()
        sys.exit(1)
    
    # Print activation summary
    print("\n" + "="*70)
    print("✅ PHASE 3 ACTIVATION SUCCESSFUL")
    print("="*70)
    print(f"\n📍 Activation Timestamp: {activation_time}")
    print(f"💾 Backup Location: {backup_path}")
    print(f"📊 Status: ACTIVE - Beginning 24-hour test")
    print(f"⏱️  First Checkpoint: HORA 50 (in ~2 hours)")
    print(f"🎯 Test Duration: HORA 48-72 (24 hours)")
    print("\n🎯 Key Metrics to Monitor:")
    print("   • ML Accuracy: ≥78%")
    print("   • Error Rate: <0.08%")
    print("   • WebSocket Latency: <95ms")
    print("   • Predictions/Hour: ≥42")
    print("   • Personalization Active: ≥140")
    print("   • Active Tests: ≥8")
    print("\n🔴 EMERGENCY KILL-SWITCH: POST /api/admin/phase3/deactivate")
    print("="*70 + "\n")
    
    # Close database
    db_connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
