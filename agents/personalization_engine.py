#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3: Personalization Engine
Applies A/B test winners to new clients with gradual rollout strategy.
Manages 10% → 50% → 100% phase-based variant assignment.
"""

import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """
    Applies A/B test winners to new clients with gradual rollout phases.
    Uses deterministic hashing to ensure consistent variant assignment per client.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize personalization engine with database connection"""
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        logger.info("✅ PersonalizationEngine initialized")

    def apply_test_winner(self, test_id: int, winner: str,
                         websocket_manager=None) -> bool:
        """
        Apply winning variant to future clients with gradual rollout.
        Initiates Phase 1: 10% rollout to new clients.

        Args:
            test_id: A/B test identifier
            winner: Winning variant ('A' or 'B')
            websocket_manager: Optional WebSocket manager for broadcasting

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.db.cursor()

            # Mark test as completed with winner
            cursor.execute("""
                UPDATE ab_tests
                SET active = 0, end_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (test_id,))

            # Get test details for broadcasting
            cursor.execute("""
                SELECT test_name, email_type, planned_duration_days
                FROM ab_tests
                WHERE id = ?
            """, (test_id,))

            test_row = cursor.fetchone()
            if not test_row:
                logger.error(f"❌ Test {test_id} not found")
                return False

            # Initiate Phase 1: 10% rollout
            # Get all active clients to seed personalization
            cursor.execute("""
                SELECT DISTINCT client_id FROM clients
                WHERE id NOT IN (
                    SELECT DISTINCT client_id FROM personalization_variants
                    WHERE test_id = ?
                )
                LIMIT 1000
            """, (test_id,))

            clients = cursor.fetchall()
            phase_1_count = max(1, len(clients) // 10)  # 10% of clients

            # Assign Phase 1 clients deterministically based on client_id hash
            for idx, client_row in enumerate(clients):
                client_id = client_row['client_id']

                # Deterministic assignment: if hash(client_id) < 0.1, assign variant
                if self._should_assign_variant(client_id, 0.1):
                    cursor.execute("""
                        INSERT OR REPLACE INTO personalization_variants
                        (client_id, test_id, winning_variant, rollout_phase, applied_date)
                        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    """, (client_id, test_id, winner))

            self.db.commit()

            logger.info(f"✅ Winner '{winner}' applied for test {test_id} (Phase 1: 10% rollout)")

            # Broadcast winner announcement
            if websocket_manager:
                try:
                    from backend.events import EventFactory
                    event = EventFactory.test_winner_announced(
                        test_id=test_id,
                        test_name=test_row['test_name'],
                        variant_winner=winner,
                        email_type=test_row['email_type'],
                        duration_days=test_row['planned_duration_days']
                    )
                    websocket_manager.broadcast(event, role='admin')
                    logger.info(f"📢 Broadcasted test:winner_announced for test {test_id}")
                except Exception as e:
                    logger.error(f"⚠️ Failed to broadcast winner announcement: {e}")

            return True

        except sqlite3.Error as e:
            logger.error(f"❌ Error applying test winner: {e}")
            return False

    def should_use_variant(self, test_id: int, client_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if client should receive personalized variant from completed test.
        Uses rollout phase to determine eligibility.

        Args:
            test_id: A/B test identifier
            client_id: Client identifier

        Returns:
            Tuple: (should_personalize: bool, variant: Optional[str])
            - (True, 'A'/'B') if client is in active rollout
            - (False, None) otherwise
        """
        try:
            cursor = self.db.cursor()

            # Check if personalization variant exists for this test/client
            cursor.execute("""
                SELECT winning_variant, rollout_phase, effective_until
                FROM personalization_variants
                WHERE test_id = ? AND client_id = ?
            """, (test_id, client_id))

            variant_row = cursor.fetchone()

            if not variant_row:
                return (False, None)

            # Check if rollout is still effective
            effective_until = variant_row['effective_until']
            if effective_until:
                effective_until_dt = datetime.fromisoformat(effective_until)
                if datetime.utcnow() > effective_until_dt:
                    return (False, None)

            logger.debug(f"✅ Client {client_id} should use variant {variant_row['winning_variant']} "
                        f"from test {test_id} (Phase {variant_row['rollout_phase']})")

            return (True, variant_row['winning_variant'])

        except sqlite3.Error as e:
            logger.error(f"❌ Error checking variant for client {client_id}: {e}")
            return (False, None)

    def advance_rollout_phase(self, test_id: int, target_phase: int = None) -> bool:
        """
        Advance A/B test winner rollout to next phase.
        Phase 1: 10% of new clients
        Phase 2: 50% of new clients (started after Phase 1 proves successful)
        Phase 3: 100% of new clients (full rollout)

        Args:
            test_id: A/B test identifier
            target_phase: Target rollout phase (2 or 3). If None, advance by 1 phase.

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.db.cursor()

            # Get current phase
            cursor.execute("""
                SELECT DISTINCT rollout_phase FROM personalization_variants
                WHERE test_id = ?
                ORDER BY rollout_phase DESC
                LIMIT 1
            """, (test_id,))

            phase_row = cursor.fetchone()
            current_phase = phase_row['rollout_phase'] if phase_row else 1

            # Determine next phase
            next_phase = target_phase if target_phase else min(current_phase + 1, 3)

            if next_phase <= current_phase:
                logger.warning(f"⚠️ Test {test_id} already at phase {current_phase}")
                return False

            # Get winning variant
            cursor.execute("""
                SELECT winning_variant FROM personalization_variants
                WHERE test_id = ?
                LIMIT 1
            """, (test_id,))

            variant_row = cursor.fetchone()
            if not variant_row:
                logger.error(f"❌ No variant found for test {test_id}")
                return False

            winner = variant_row['winning_variant']

            # Get all clients not yet assigned
            cursor.execute("""
                SELECT DISTINCT c.id FROM clients c
                WHERE c.id NOT IN (
                    SELECT client_id FROM personalization_variants
                    WHERE test_id = ?
                )
                LIMIT 2000
            """, (test_id,))

            unassigned_clients = cursor.fetchall()

            # Assign based on new phase rollout percentage
            phase_percentages = {1: 0.1, 2: 0.5, 3: 1.0}
            target_percentage = phase_percentages.get(next_phase, 1.0)

            assigned_count = 0
            for client_row in unassigned_clients:
                client_id = client_row['id']

                # Deterministic assignment based on hash
                if self._should_assign_variant(client_id, target_percentage):
                    cursor.execute("""
                        INSERT INTO personalization_variants
                        (client_id, test_id, winning_variant, rollout_phase, applied_date)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (client_id, test_id, winner, next_phase))
                    assigned_count += 1

            self.db.commit()

            logger.info(f"✅ Test {test_id} advanced to Phase {next_phase} "
                       f"({target_percentage:.0%} rollout, {assigned_count} new clients assigned)")

            return True

        except sqlite3.Error as e:
            logger.error(f"❌ Error advancing rollout phase: {e}")
            return False

    def get_rollout_stats(self, test_id: int) -> Dict:
        """
        Get current rollout statistics for a test.

        Args:
            test_id: A/B test identifier

        Returns:
            Dictionary with rollout statistics:
            {
                'total_assigned': int,
                'phase_1': int,  # 10% rollout count
                'phase_2': int,  # 50% rollout count
                'phase_3': int,  # 100% rollout count
                'current_phase': int,
                'winning_variant': str
            }
        """
        try:
            cursor = self.db.cursor()

            # Get phase distribution
            cursor.execute("""
                SELECT rollout_phase, COUNT(*) as count, winning_variant
                FROM personalization_variants
                WHERE test_id = ?
                GROUP BY rollout_phase
            """, (test_id,))

            phase_data = cursor.fetchall()

            stats = {
                'total_assigned': 0,
                'phase_1': 0,
                'phase_2': 0,
                'phase_3': 0,
                'current_phase': 1,
                'winning_variant': None
            }

            for row in phase_data:
                phase = row['rollout_phase']
                count = row['count']
                stats[f'phase_{phase}'] = count
                stats['total_assigned'] += count
                stats['current_phase'] = max(stats['current_phase'], phase)
                stats['winning_variant'] = row['winning_variant']

            return stats

        except sqlite3.Error as e:
            logger.error(f"❌ Error getting rollout stats: {e}")
            return {'total_assigned': 0}

    def _should_assign_variant(self, client_id: int, percentage: float) -> bool:
        """
        Deterministically determine if client should be assigned variant.
        Uses hash of client_id to ensure consistent, reproducible assignments.

        Args:
            client_id: Client identifier
            percentage: Percentage threshold (0.0-1.0)

        Returns:
            True if client's hash falls within percentage threshold
        """
        # Hash client_id to a value between 0.0 and 1.0
        hash_value = int(hashlib.md5(str(client_id).encode()).hexdigest(), 16)
        normalized = (hash_value % 10000) / 10000.0
        return normalized < percentage

    def expire_variant(self, test_id: int, expires_in_days: int = 30) -> bool:
        """
        Set expiration date for personalized variant.
        After expiration, client will revert to standard (non-personalized) assignment.

        Args:
            test_id: A/B test identifier
            expires_in_days: Days until variant expires (default 30)

        Returns:
            True if successful, False otherwise
        """
        try:
            expiration_date = datetime.utcnow() + timedelta(days=expires_in_days)

            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE personalization_variants
                SET effective_until = ?
                WHERE test_id = ?
            """, (expiration_date.isoformat(), test_id))

            self.db.commit()

            logger.info(f"✅ Set expiration date for test {test_id} variants: {expires_in_days} days")
            return True

        except sqlite3.Error as e:
            logger.error(f"❌ Error setting variant expiration: {e}")
            return False

    def rollback_personalization(self, test_id: int) -> bool:
        """
        Rollback all personalization for a test (remove all variant assignments).
        Use if test winner proves problematic during rollout.

        Args:
            test_id: A/B test identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                DELETE FROM personalization_variants
                WHERE test_id = ?
            """, (test_id,))

            self.db.commit()

            logger.warning(f"⚠️ Rolled back all personalization for test {test_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"❌ Error rolling back personalization: {e}")
            return False
