#!/usr/bin/env python3
"""
FASE 14 PASO 8: Email Variant Assigner
Hash-based deterministic A/B test variant assignment
"""

import logging
import hashlib
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from sqlite3 import Connection

logger = logging.getLogger(__name__)


class EmailVariantAssigner:
    """
    Manages A/B test variant assignment for email campaigns.
    Uses deterministic hash-based assignment so same client always gets same variant.
    """

    def __init__(self, db_connection: Optional[Connection] = None):
        """
        Initialize variant assigner with database connection.

        Args:
            db_connection: SQLite database connection (optional)
        """
        self.db = db_connection
        self.cursor = self.db.cursor() if db_connection else None

    def assign_variant(self, test_id: int, client_id: int) -> str:
        """
        Determine variant (A or B) for client in test.
        First checks for personalized winner from completed test.
        Falls back to deterministic hash-based assignment.
        Same client always gets same variant for a given test.

        Args:
            test_id: ID of A/B test
            client_id: ID of client

        Returns:
            'A' or 'B' variant
        """
        try:
            # Phase 3.5 Integration: Check for personalized variant first
            if self.db and self.cursor:
                try:
                    self.cursor.execute(
                        """
                        SELECT winning_variant FROM personalization_variants
                        WHERE test_id = ? AND client_id = ?
                        """,
                        (test_id, client_id)
                    )
                    personalized = self.cursor.fetchone()

                    if personalized:
                        variant = personalized[0]
                        # Validate that variant is a string (not a mock or invalid type)
                        if isinstance(variant, str) and variant in ['A', 'B']:
                            logger.info(f"✅ Using personalized variant: client {client_id} → {variant} (test {test_id})")
                            return variant
                except Exception as e:
                    logger.debug(f"⚠️ Personalization check skipped: {e}")

            # Fall back to deterministic hash assignment
            hash_input = f"{test_id}_{client_id}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()
            hash_int = int(hash_value, 16)

            # Assign based on hash parity (deterministic)
            variant = 'A' if hash_int % 2 == 0 else 'B'

            logger.debug(f"✅ Variant assigned (hash-based): client {client_id} → {variant} (test {test_id})")
            return variant

        except Exception as e:
            logger.error(f"❌ Error assigning variant: {e}")
            return 'A'  # Default to A on error

    def get_or_assign_variant(self, test_id: int, client_id: int) -> Optional[Dict]:
        """
        Get existing variant assignment or create new one.
        Includes audit trail (created_at timestamp).

        Args:
            test_id: ID of A/B test
            client_id: ID of client

        Returns:
            Dict with variant, test_id, client_id, created_at, or None on error
        """
        if not self.cursor:
            logger.warning("⚠️ No database connection available, using deterministic assignment only")
            variant = self.assign_variant(test_id, client_id)
            return {
                'variant': variant,
                'test_id': test_id,
                'client_id': client_id,
                'created_at': datetime.utcnow().isoformat(),
                'existing': False
            }

        try:
            # Check if assignment already exists
            self.cursor.execute(
                """
                SELECT id, variant, created_at FROM ab_test_results
                WHERE test_id = ? AND client_id = ?
                LIMIT 1
                """,
                (test_id, client_id)
            )
            existing = self.cursor.fetchone()

            if existing:
                logger.debug(
                    f"♻️ Using existing assignment: client {client_id} → {existing[1]} (test {test_id})"
                )
                return {
                    'id': existing[0],
                    'variant': existing[1],
                    'test_id': test_id,
                    'client_id': client_id,
                    'created_at': existing[2],
                    'existing': True
                }

            # Create new assignment
            variant = self.assign_variant(test_id, client_id)
            now = datetime.utcnow().isoformat()

            self.cursor.execute(
                """
                INSERT INTO ab_test_results
                (test_id, client_id, variant, sent_count, opens, clicks, conversions, created_at)
                VALUES (?, ?, ?, 0, 0, 0, 0, ?)
                """,
                (test_id, client_id, variant, now)
            )
            self.db.commit()

            logger.info(f"✅ New variant assignment created: client {client_id} → {variant} (test {test_id})")

            return {
                'id': self.cursor.lastrowid,
                'variant': variant,
                'test_id': test_id,
                'client_id': client_id,
                'created_at': now,
                'existing': False
            }

        except Exception as e:
            logger.error(f"❌ Error getting/assigning variant: {e}")
            return None

    def get_test_distribution(self, test_id: int) -> Dict[str, int]:
        """
        Get count of clients assigned to each variant in a test.

        Args:
            test_id: ID of A/B test

        Returns:
            Dict with counts: {'A': count_a, 'B': count_b}
        """
        try:
            self.cursor.execute(
                """
                SELECT variant, COUNT(*) as count
                FROM ab_test_results
                WHERE test_id = ?
                GROUP BY variant
                """,
                (test_id,)
            )
            results = self.cursor.fetchall()

            distribution = {'A': 0, 'B': 0}
            for variant, count in results:
                distribution[variant] = count

            logger.debug(f"📊 Test {test_id} distribution: {distribution}")
            return distribution

        except Exception as e:
            logger.error(f"❌ Error getting test distribution: {e}")
            return {'A': 0, 'B': 0}

    def get_client_assignments(self, client_id: int) -> List[Dict]:
        """
        Get all active A/B test assignments for a client.

        Args:
            client_id: ID of client

        Returns:
            List of active test assignments
        """
        try:
            self.cursor.execute(
                """
                SELECT ab_tests.id, ab_tests.email_type, ab_test_results.variant, ab_tests.active
                FROM ab_test_results
                JOIN ab_tests ON ab_test_results.test_id = ab_tests.id
                WHERE ab_test_results.client_id = ? AND ab_tests.active = 1
                """,
                (client_id,)
            )
            results = self.cursor.fetchall()

            assignments = [
                {
                    'test_id': row[0],
                    'email_type': row[1],
                    'variant': row[2],
                    'active': row[3]
                }
                for row in results
            ]

            logger.debug(f"📋 Client {client_id} has {len(assignments)} active assignments")
            return assignments

        except Exception as e:
            logger.error(f"❌ Error getting client assignments: {e}")
            return []

    def get_variant_content(self, test_id: int, variant: str) -> Optional[Dict]:
        """
        Get email content (subject, body) for a specific variant.

        Args:
            test_id: ID of A/B test
            variant: 'A' or 'B'

        Returns:
            Dict with subject and body for variant, or None
        """
        try:
            variant_col = f"variant_{variant.lower()}"

            self.cursor.execute(
                f"""
                SELECT id, email_type, {variant_col}
                FROM ab_tests
                WHERE id = ?
                """,
                (test_id,)
            )
            result = self.cursor.fetchone()

            if result:
                # Parse variant content (stored as JSON: {"subject": "...", "body": "..."})
                import json
                content = json.loads(result[2]) if result[2] else {}
                return {
                    'test_id': result[0],
                    'email_type': result[1],
                    'subject': content.get('subject', ''),
                    'body': content.get('body', '')
                }

            return None

        except Exception as e:
            logger.error(f"❌ Error getting variant content: {e}")
            return None

    def record_event(self, result_id: int, event_type: str) -> bool:
        """
        Record email engagement event (open, click, conversion).

        Args:
            result_id: ID of ab_test_results row
            event_type: 'open', 'click', or 'conversion'

        Returns:
            True if successful, False otherwise
        """
        try:
            event_col_map = {
                'open': 'opens',
                'click': 'clicks',
                'conversion': 'conversions'
            }

            if event_type not in event_col_map:
                logger.warning(f"⚠️ Unknown event type: {event_type}")
                return False

            col_name = event_col_map[event_type]

            self.cursor.execute(
                f"""
                UPDATE ab_test_results
                SET {col_name} = {col_name} + 1
                WHERE id = ?
                """,
                (result_id,)
            )
            self.db.commit()

            logger.debug(f"✅ Event recorded: result {result_id} → {event_type}")
            return True

        except Exception as e:
            logger.error(f"❌ Error recording event: {e}")
            return False

    def record_open(self, result_id: int) -> bool:
        """Record email open event."""
        return self.record_event(result_id, 'open')

    def record_click(self, result_id: int) -> bool:
        """Record email click event."""
        return self.record_event(result_id, 'click')

    def record_conversion(self, result_id: int) -> bool:
        """Record conversion event."""
        return self.record_event(result_id, 'conversion')

    def increment_sent(self, result_id: int) -> bool:
        """
        Increment sent count for test result.

        Args:
            result_id: ID of ab_test_results row

        Returns:
            True if successful
        """
        try:
            self.cursor.execute(
                """
                UPDATE ab_test_results
                SET sent_count = sent_count + 1
                WHERE id = ?
                """,
                (result_id,)
            )
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Error incrementing sent count: {e}")
            return False
    def get_active_test_for_email_type(self, email_type: str) -> Optional[Dict]:
        """
        Get the currently active A/B test for an email type.

        Args:
            email_type: Type of email (e.g., 'audit_report', 'proposal', 'followup_1')

        Returns:
            Dict with test data including variant_a and variant_b content, or None
        """
        if not self.cursor:
            logger.warning("⚠️ No database connection available")
            return None

        try:
            self.cursor.execute(
                """
                SELECT id, email_type, active, variant_a, variant_b
                FROM ab_tests
                WHERE email_type = ? AND active = 1
                LIMIT 1
                """,
                (email_type,)
            )
            result = self.cursor.fetchone()

            if result:
                import json
                test_id, et, active, var_a, var_b = result
                return {
                    'id': test_id,
                    'email_type': et,
                    'active': active,
                    'variant_a': json.loads(var_a) if var_a else {},
                    'variant_b': json.loads(var_b) if var_b else {}
                }

            return None

        except Exception as e:
            logger.error(f"❌ Error getting active test: {e}")
            return None

    def get_assignment(self, test_id: int, client_id: int) -> Optional[str]:
        """
        Get or assign variant for client in test.

        Args:
            test_id: ID of A/B test
            client_id: ID of client

        Returns:
            Variant letter ('A' or 'B'), or None
        """
        try:
            result = self.get_or_assign_variant(test_id, client_id)
            if result:
                return result['variant']
            return None

        except Exception as e:
            logger.error(f"❌ Error getting assignment: {e}")
            return None

    def record_send(self, test_id: int, client_id: int, variant: str) -> bool:
        """
        Record that an email was sent to a client in a test.

        Args:
            test_id: ID of A/B test
            client_id: ID of client
            variant: Variant sent ('A' or 'B')

        Returns:
            True if successful
        """
        if not self.cursor:
            logger.warning("⚠️ No database connection available")
            return False

        try:
            self.cursor.execute(
                """
                SELECT id FROM ab_test_results
                WHERE test_id = ? AND client_id = ?
                """,
                (test_id, client_id)
            )
            result = self.cursor.fetchone()

            if result:
                result_id = result[0]
                return self.increment_sent(result_id)

            return False

        except Exception as e:
            logger.error(f"❌ Error recording send: {e}")
            return False


if __name__ == "__main__":
    print("✅ EmailVariantAssigner module loaded (import it in email_sender_agent.py)")
