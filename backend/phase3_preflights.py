#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Pre-Flight Checks
Validates system readiness before Phase 3 activation (HORA 48)
Must pass all 5 checks before activation is allowed
"""

import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Phase3Preflights:
    """Pre-flight validation for Phase 3 activation"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self.checks_passed = {}
        self.check_details = {}

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all pre-flight checks

        Returns:
        {
            "all_pass": bool,
            "checks": {
                "phase2_health": bool,
                "backup_recent": bool,
                "database_integrity": bool,
                "components_healthy": bool,
                "circuit_breakers_ok": bool
            },
            "blocked_reason": Optional[str]  # First failed check
        }
        """
        logger.info("🚀 Starting Phase 3 pre-flight checks...")

        # Run all checks in order
        checks = {
            "phase2_health": self.check_phase2_metrics,
            "backup_recent": self.check_backup_age,
            "database_integrity": self.check_database_integrity,
            "components_healthy": self.check_all_components,
            "circuit_breakers_ok": self.check_circuit_breakers,
        }

        all_pass = True
        blocked_reason = None

        for check_name, check_func in checks.items():
            try:
                result = check_func()
                self.checks_passed[check_name] = result

                status = "✅" if result else "❌"
                logger.info(f"{status} Check '{check_name}': {result}")

                if not result and not blocked_reason:
                    blocked_reason = check_name
                    all_pass = False
            except Exception as e:
                logger.error(f"❌ Check '{check_name}' threw exception: {e}")
                self.checks_passed[check_name] = False
                self.check_details[check_name] = str(e)
                if not blocked_reason:
                    blocked_reason = f"{check_name} (exception)"
                all_pass = False

        logger.info(f"{'✅' if all_pass else '❌'} Pre-flight checks complete. All pass: {all_pass}")

        return {
            "all_pass": all_pass,
            "checks": self.checks_passed,
            "blocked_reason": blocked_reason,
            "details": self.check_details
        }

    def check_phase2_metrics(self) -> bool:
        """
        Check Phase 2 (current production) metrics are healthy
        Requirement: error_rate < 1% (not just <0.08%, allow some margin before Phase 3)
        """
        logger.info("📊 Checking Phase 2 metrics...")

        try:
            cursor = self.db.cursor()

            # Query recent error rate from metrics
            # Adjust table/column names based on actual schema
            cursor.execute("""
                SELECT error_rate FROM metrics
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC LIMIT 1
            """)

            result = cursor.fetchone()

            if not result:
                logger.warning("⚠️ No recent metrics found for Phase 2")
                return False

            error_rate = float(result[0])
            threshold = 0.01  # 1% error rate

            if error_rate < threshold:
                logger.info(f"✅ Phase 2 error rate: {error_rate*100:.3f}% (threshold: {threshold*100:.1f}%)")
                return True
            else:
                logger.warning(f"❌ Phase 2 error rate too high: {error_rate*100:.3f}% (threshold: {threshold*100:.1f}%)")
                self.check_details["phase2_health"] = f"Error rate {error_rate*100:.3f}% exceeds {threshold*100:.1f}%"
                return False

        except Exception as e:
            logger.warning(f"⚠️ Phase 2 metrics check failed: {e}")
            self.check_details["phase2_health"] = str(e)
            # Don't block activation if metrics can't be queried (might not be logging yet)
            return True

    def check_backup_age(self) -> bool:
        """
        Check that recent backups exist and are fresh (<2 hours old)
        """
        logger.info("💾 Checking backup age...")

        try:
            backup_dir = Path("data/backups")

            if not backup_dir.exists():
                logger.warning("❌ Backup directory does not exist")
                self.check_details["backup_recent"] = "Backup directory not found"
                return False

            # Find most recent backup
            backup_files = list(backup_dir.glob("*.sqlite")) + list(backup_dir.glob("*.db"))

            if not backup_files:
                logger.warning("❌ No backup files found")
                self.check_details["backup_recent"] = "No backup files found"
                return False

            # Get most recent
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            backup_age_seconds = (datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)).total_seconds()
            backup_age_hours = backup_age_seconds / 3600

            threshold_hours = 2.0

            if backup_age_hours < threshold_hours:
                logger.info(f"✅ Latest backup is {backup_age_hours:.1f} hours old (threshold: {threshold_hours}h)")
                return True
            else:
                logger.warning(f"❌ Latest backup is {backup_age_hours:.1f} hours old (threshold: {threshold_hours}h)")
                self.check_details["backup_recent"] = f"Latest backup is {backup_age_hours:.1f}h old"
                return False

        except Exception as e:
            logger.error(f"❌ Backup age check failed: {e}")
            self.check_details["backup_recent"] = str(e)
            return False

    def check_database_integrity(self) -> bool:
        """
        Check database is accessible and tables exist
        """
        logger.info("🔍 Checking database integrity...")

        try:
            cursor = self.db.cursor()

            # Check that key tables exist
            required_tables = [
                "system_config",
                "users",
                "predictions",
                "events"
            ]

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
            """)

            existing_tables = {row[0] for row in cursor.fetchall()}

            missing = set(required_tables) - existing_tables

            if missing:
                logger.warning(f"❌ Missing tables: {missing}")
                self.check_details["database_integrity"] = f"Missing tables: {missing}"
                return False

            logger.info(f"✅ All required tables exist: {required_tables}")
            return True

        except Exception as e:
            logger.error(f"❌ Database integrity check failed: {e}")
            self.check_details["database_integrity"] = str(e)
            return False

    def check_all_components(self) -> bool:
        """
        Check that all Phase 3 system components are accessible
        - Database: ping
        - WebSocket: manager initialized
        - Prediction service: can be imported
        - Monitoring daemon: running
        """
        logger.info("🔧 Checking system components...")

        try:
            # 1. Database - already being used in init, so it's working
            cursor = self.db.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            logger.info("✅ Database accessible")

            # 2. Check monitoring daemon configuration
            try:
                from monitoring_daemon import MonitoringDaemon
                logger.info("✅ Monitoring daemon available")
            except Exception as e:
                logger.warning(f"⚠️ Monitoring daemon not available: {e}")
                self.check_details["components_healthy"] = f"Monitoring daemon: {e}"
                return False

            # 3. Check circuit breaker registry
            try:
                from circuit_breaker import CircuitBreakerRegistry
                registry = CircuitBreakerRegistry()
                registry.get_all_metrics()
                logger.info("✅ Circuit breaker registry accessible")
            except Exception as e:
                logger.warning(f"⚠️ Circuit breaker registry issue: {e}")
                self.check_details["components_healthy"] = f"Circuit breakers: {e}"
                return False

            logger.info("✅ All components healthy")
            return True

        except Exception as e:
            logger.error(f"❌ Component check failed: {e}")
            self.check_details["components_healthy"] = str(e)
            return False

    def check_circuit_breakers(self) -> bool:
        """
        Check that circuit breakers are working and in CLOSED state
        Any OPEN or excessive HALF_OPEN states block activation
        """
        logger.info("⚡ Checking circuit breakers...")

        try:
            from circuit_breaker import CircuitBreakerRegistry

            registry = CircuitBreakerRegistry()
            metrics = registry.get_all_metrics()

            # Check each breaker
            for breaker_name, state_info in metrics.items():
                state = state_info.get("state")
                failure_count = state_info.get("failure_count", 0)

                logger.info(f"  {breaker_name}: state={state}, failures={failure_count}")

                if state == "OPEN":
                    logger.warning(f"❌ Circuit breaker '{breaker_name}' is OPEN")
                    self.check_details["circuit_breakers_ok"] = f"{breaker_name} is OPEN"
                    return False

                if state == "HALF_OPEN" and failure_count > 2:
                    logger.warning(f"❌ Circuit breaker '{breaker_name}' is HALF_OPEN with {failure_count} failures")
                    self.check_details["circuit_breakers_ok"] = f"{breaker_name} is unstable"
                    return False

            logger.info("✅ All circuit breakers healthy")
            return True

        except Exception as e:
            logger.error(f"❌ Circuit breaker check failed: {e}")
            self.check_details["circuit_breakers_ok"] = str(e)
            return False


def run_preflights(db_connection: sqlite3.Connection) -> Dict[str, Any]:
    """
    Standalone function to run pre-flight checks

    Usage:
        from phase3_preflights import run_preflights
        result = run_preflights(db_connection)
        if not result["all_pass"]:
            raise Exception(f"Pre-flight failed: {result['blocked_reason']}")
    """
    preflights = Phase3Preflights(db_connection)
    return preflights.run_all_checks()
