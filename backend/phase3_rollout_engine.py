#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Personalization Rollout Engine
Manages gradual rollout of personalized variants:
- Phase 1 (HORA 48-56): 10% of new clients
- Phase 2 (HORA 56-64): 50% of new clients (if healthy)
- Phase 3 (HORA 64-72): 100% of new clients (if healthy)
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RolloutPhase(Enum):
    """Personalization rollout phase"""
    PHASE_1 = 1  # 10% rollout
    PHASE_2 = 2  # 50% rollout
    PHASE_3 = 3  # 100% rollout


class Phase3RolloutEngine:
    """Manage gradual rollout of Phase 3 personalization"""

    # Configuration: when to advance phases based on checkpoints
    CHECKPOINT_ADVANCE_THRESHOLDS = {
        1: {  # Phase 1 -> Phase 2
            'min_checkpoints_needed': 2,  # After ~4 hours (2 checkpoints)
            'min_health_score': 5,        # 5/6 metrics passing
            'max_red_checkpoints': 0      # No red checkpoints allowed
        },
        2: {  # Phase 2 -> Phase 3
            'min_checkpoints_needed': 2,  # After ~4 hours more
            'min_health_score': 5,
            'max_red_checkpoints': 0
        }
    }

    # Rollout percentages per phase
    ROLLOUT_PERCENTAGES = {
        RolloutPhase.PHASE_1: 10,
        RolloutPhase.PHASE_2: 50,
        RolloutPhase.PHASE_3: 100
    }

    # Current active phase defaults to Phase 1
    CURRENT_PHASE = RolloutPhase.PHASE_1

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.db = None
        self.current_phase = RolloutPhase.PHASE_1
        self.phase_start_time = None
        self.phase_start_hora = 48
        self.checkpoints_evaluated: Dict[int, bool] = {}  # HORA -> advanced?

    def connect(self):
        """Connect to database"""
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        logger.info(f"✅ Connected to database: {self.db_path}")

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

    def load_current_phase(self) -> Optional[RolloutPhase]:
        """Load current rollout phase from database"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT value FROM system_config
                WHERE key = 'PHASE_3_ROLLOUT_PHASE'
            """)
            result = cursor.fetchone()

            if result:
                phase_num = int(result[0])
                self.current_phase = RolloutPhase(phase_num)
                logger.info(f"✅ Current rollout phase: PHASE {self.current_phase.value} ({self.ROLLOUT_PERCENTAGES[self.current_phase]}%)")
            else:
                logger.info("ℹ️  No rollout phase set, defaulting to PHASE 1 (10%)")
                self.set_phase(RolloutPhase.PHASE_1)

            return self.current_phase

        except Exception as e:
            logger.error(f"Error loading current phase: {e}")
            return None

    def set_phase(self, phase: RolloutPhase) -> bool:
        """Update current rollout phase in database"""
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                DELETE FROM system_config
                WHERE key = 'PHASE_3_ROLLOUT_PHASE'
            """)

            cursor.execute("""
                INSERT INTO system_config (key, value, created_at)
                VALUES (?, ?, ?)
            """, ('PHASE_3_ROLLOUT_PHASE', str(phase.value), datetime.utcnow().isoformat()))

            self.db.commit()
            self.current_phase = phase

            logger.info(f"✅ Rollout phase updated to PHASE {phase.value} ({self.ROLLOUT_PERCENTAGES[phase]}%)")

            # Log phase advancement
            cursor.execute("""
                INSERT INTO phase3_rollout_log (phase, percentage, timestamp)
                VALUES (?, ?, ?)
            """, (phase.value, self.ROLLOUT_PERCENTAGES[phase], datetime.utcnow().isoformat()))
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error setting phase: {e}")
            return False

    def get_rollout_percentage(self) -> int:
        """Get current rollout percentage"""
        return self.ROLLOUT_PERCENTAGES.get(self.current_phase, 10)

    def evaluate_phase_advancement(self, checkpoint_hora: int) -> Optional[RolloutPhase]:
        """
        Evaluate if we should advance to next phase based on checkpoint health

        Returns:
            New phase if advanced, None otherwise
        """
        if self.current_phase == RolloutPhase.PHASE_3:
            logger.info("ℹ️  Already at PHASE 3 (100%), no further advancement")
            return None

        # Check if this is a checkpoint that can trigger advancement
        try:
            # Determine which phase advancement this is
            if self.current_phase == RolloutPhase.PHASE_1:
                next_phase = RolloutPhase.PHASE_2
                advance_key = 1
            elif self.current_phase == RolloutPhase.PHASE_2:
                next_phase = RolloutPhase.PHASE_3
                advance_key = 2
            else:
                return None

            # Load threshold config
            threshold = self.CHECKPOINT_ADVANCE_THRESHOLDS[advance_key]

            # Count checkpoints since phase start
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT COUNT(*) as check_count,
                       SUM(CASE WHEN health_score >= ? THEN 1 ELSE 0 END) as healthy_count,
                       SUM(CASE WHEN health_score < 5 THEN 1 ELSE 0 END) as red_count
                FROM phase3_checkpoints
                WHERE hora >= ?
            """, (threshold['min_health_score'], checkpoint_hora - threshold['min_checkpoints_needed'] * 2))

            result = cursor.fetchone()
            check_count = result['check_count'] or 0
            healthy_count = result['healthy_count'] or 0
            red_count = result['red_count'] or 0

            logger.info(f"\nPhase Advancement Evaluation ({self.current_phase.value} → {next_phase.value}):")
            logger.info(f"  Checkpoints evaluated: {check_count}/{threshold['min_checkpoints_needed']}")
            logger.info(f"  Healthy checkpoints: {healthy_count}/{check_count}")
            logger.info(f"  Red checkpoints: {red_count}/{threshold['max_red_checkpoints']}")

            # Check advancement criteria
            if (check_count >= threshold['min_checkpoints_needed'] and
                healthy_count >= threshold['min_checkpoints_needed'] and
                red_count <= threshold['max_red_checkpoints']):

                logger.info(f"✅ ADVANCING to PHASE {next_phase.value}!")
                self.set_phase(next_phase)
                return next_phase
            else:
                logger.info(f"⚠️  Not ready for phase advancement yet")
                return None

        except Exception as e:
            logger.error(f"Error evaluating phase advancement: {e}")
            return None

    def should_personalize_client(self, client_id: int, test_id: int) -> bool:
        """
        Determine if a client should get personalized variant based on current phase

        Args:
            client_id: Client ID
            test_id: A/B test ID

        Returns:
            True if client should get personalized variant, False otherwise
        """
        try:
            rollout_percentage = self.get_rollout_percentage()

            # Use client_id hash to deterministically select rollout sample
            # Same client always gets same decision for same rollout percentage
            rollout_slot = (client_id % 100) + 1  # 1-100

            return rollout_slot <= rollout_percentage

        except Exception as e:
            logger.error(f"Error checking personalization eligibility: {e}")
            return False

    def apply_variant_to_client(self, client_id: int, test_id: int, variant: str) -> bool:
        """
        Record that a client received a personalized variant

        Args:
            client_id: Client ID
            test_id: A/B test ID
            variant: Variant letter ('A' or 'B')

        Returns:
            True if successfully recorded, False otherwise
        """
        try:
            cursor = self.db.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO personalization_variants (
                    client_id, test_id, winning_variant, rollout_phase, applied_date
                ) VALUES (?, ?, ?, ?, ?)
            """, (client_id, test_id, variant, self.current_phase.value, datetime.utcnow().isoformat()))

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error recording variant for client {client_id}: {e}")
            return False

    def get_rollout_statistics(self) -> Dict:
        """Get statistics on rollout progress"""
        try:
            cursor = self.db.cursor()

            # Count clients per phase
            cursor.execute("""
                SELECT rollout_phase, COUNT(*) as client_count
                FROM personalization_variants
                GROUP BY rollout_phase
            """)

            phase_stats = {}
            for row in cursor.fetchall():
                phase_stats[f"phase_{row['rollout_phase']}_clients"] = row['client_count']

            # Count active tests
            cursor.execute("""
                SELECT COUNT(*) as test_count
                FROM ab_tests
                WHERE status = 'ACTIVE'
            """)
            test_count = cursor.fetchone()['test_count'] or 0

            # Get phase timeline
            cursor.execute("""
                SELECT phase, COUNT(*) as advancements, MAX(timestamp) as latest
                FROM phase3_rollout_log
                GROUP BY phase
                ORDER BY phase ASC
            """)

            phase_timeline = []
            for row in cursor.fetchall():
                phase_timeline.append({
                    "phase": row['phase'],
                    "percentage": self.ROLLOUT_PERCENTAGES[RolloutPhase(row['phase'])],
                    "latest_advancement": row['latest']
                })

            return {
                "current_phase": self.current_phase.value,
                "current_percentage": self.get_rollout_percentage(),
                "active_tests": test_count,
                "phase_statistics": phase_stats,
                "phase_timeline": phase_timeline
            }

        except Exception as e:
            logger.error(f"Error getting rollout statistics: {e}")
            return {}


def main():
    """Test rollout engine"""
    engine = Phase3RolloutEngine()
    engine.connect()

    # Load current phase
    engine.load_current_phase()

    # Get statistics
    stats = engine.get_rollout_statistics()
    print("\n" + "="*70)
    print("PHASE 3 ROLLOUT STATISTICS")
    print("="*70)
    print(f"Current Phase: {stats['current_phase']}")
    print(f"Current Percentage: {stats['current_percentage']}%")
    print(f"Active Tests: {stats['active_tests']}")
    print("="*70)

    engine.close()
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    exit(main())
