#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Variant Assigner - A/B Test Assignment Logic
FASE 14: Real-Time & ML Features
Hash-based deterministic variant assignment ensuring reproducibility
"""

import logging
import hashlib
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailVariantAssigner:
    """
    Assigns clients to A/B test variants using hash-based deterministic assignment

    Key features:
    - Deterministic: same client always gets same variant for same test
    - Reproducible: easy to verify and debug
    - Balanced: 50/50 split across A and B variants
    - Trackable: stores assignment in database for statistical analysis
    """

    def __init__(self, database=None):
        """
        Initialize variant assigner

        Args:
            database: Database connection for storing assignments
        """
        self.database = database
        logger.info("✅ Email Variant Assigner initialized")

    def assign_variant(self, test_id: int, client_id: int) -> str:
        """
        Assign client to variant A or B based on deterministic hash

        The assignment is stable - same (test_id, client_id) always produces same variant

        Args:
            test_id: A/B test ID
            client_id: Client ID

        Returns:
            'A' or 'B' variant
        """
        # Create deterministic hash from test_id and client_id
        hash_input = f"{test_id}_{client_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # 50/50 split based on hash modulo 2
        variant = 'A' if hash_value % 2 == 0 else 'B'

        logger.debug(f"✅ Assigned client {client_id} to variant {variant} for test {test_id}")
        return variant

    def get_assignment(self, test_id: int, client_id: int) -> Optional[str]:
        """
        Get variant assignment for client in test (checks database first, then assigns)

        Args:
            test_id: A/B test ID
            client_id: Client ID

        Returns:
            Variant 'A' or 'B', or None if no active test
        """
        try:
            # Check if assignment already exists in database
            if self.database:
                cursor = self.database.cursor()
                cursor.execute("""
                SELECT variant FROM ab_test_results
                WHERE test_id = ? AND client_id = ?
                LIMIT 1
                """, (test_id, client_id))

                result = cursor.fetchone()
                if result:
                    variant = result[0]
                    logger.debug(f"✅ Found existing assignment: client {client_id} → {variant}")
                    return variant

            # No existing assignment, create new one
            variant = self.assign_variant(test_id, client_id)

            # Store in database
            if self.database:
                self._store_assignment(test_id, client_id, variant)

            return variant

        except Exception as e:
            logger.error(f"❌ Error getting assignment: {str(e)}")
            return None

    def is_active_test(self, test_id: int) -> bool:
        """
        Check if A/B test is active

        Args:
            test_id: A/B test ID

        Returns:
            True if test is active, False otherwise
        """
        try:
            if not self.database:
                return False

            cursor = self.database.cursor()
            cursor.execute("""
            SELECT active FROM ab_tests
            WHERE id = ? AND active = 1
            """, (test_id,))

            result = cursor.fetchone()
            return result is not None

        except Exception as e:
            logger.error(f"❌ Error checking test active status: {str(e)}")
            return False

    def get_active_test_for_email_type(self, email_type: str) -> Optional[Dict]:
        """
        Get active test for a specific email type

        Args:
            email_type: Type of email (e.g., 'audit_report', 'proposal', 'followup')

        Returns:
            Test dict with id, email_type, etc. or None
        """
        try:
            if not self.database:
                return None

            cursor = self.database.cursor()
            cursor.execute("""
            SELECT id, test_name, email_type, variant_a_subject, variant_a_body,
                   variant_b_subject, variant_b_body, start_date, end_date
            FROM ab_tests
            WHERE email_type = ? AND active = 1
            ORDER BY start_date DESC
            LIMIT 1
            """, (email_type,))

            result = cursor.fetchone()
            if result:
                test = {
                    "id": result[0],
                    "name": result[1],
                    "email_type": result[2],
                    "variant_a": {
                        "subject": result[3],
                        "body": result[4]
                    },
                    "variant_b": {
                        "subject": result[5],
                        "body": result[6]
                    },
                    "start_date": result[7],
                    "end_date": result[8]
                }
                logger.debug(f"✅ Found active test for email_type '{email_type}': {test['name']}")
                return test

            return None

        except Exception as e:
            logger.error(f"❌ Error getting active test: {str(e)}")
            return None

    def get_variants_for_test(self, test_id: int) -> Optional[Tuple[Dict, Dict]]:
        """
        Get variant A and B content for a test

        Args:
            test_id: A/B test ID

        Returns:
            Tuple of (variant_a, variant_b) dicts or None
        """
        try:
            if not self.database:
                return None

            cursor = self.database.cursor()
            cursor.execute("""
            SELECT variant_a_subject, variant_a_body, variant_b_subject, variant_b_body
            FROM ab_tests
            WHERE id = ?
            """, (test_id,))

            result = cursor.fetchone()
            if result:
                variant_a = {"subject": result[0], "body": result[1]}
                variant_b = {"subject": result[2], "body": result[3]}
                return (variant_a, variant_b)

            return None

        except Exception as e:
            logger.error(f"❌ Error getting variants: {str(e)}")
            return None

    def assign_and_get_variant(self, test_id: int, client_id: int) -> Optional[Dict]:
        """
        Assign client to variant and return the variant content

        Args:
            test_id: A/B test ID
            client_id: Client ID

        Returns:
            Dict with variant content or None
        """
        try:
            # Get variant assignment
            variant = self.get_assignment(test_id, client_id)
            if not variant:
                return None

            # Get variant content
            variants = self.get_variants_for_test(test_id)
            if not variants:
                return None

            variant_a, variant_b = variants
            selected_variant = variant_a if variant == 'A' else variant_b

            logger.info(f"✅ Assigned client {client_id} to variant {variant}")
            return {"variant": variant, "content": selected_variant}

        except Exception as e:
            logger.error(f"❌ Error in assign_and_get_variant: {str(e)}")
            return None

    def record_send(self, test_id: int, client_id: int, variant: str) -> bool:
        """
        Record that email was sent for this test variant

        Args:
            test_id: A/B test ID
            client_id: Client ID
            variant: 'A' or 'B'

        Returns:
            True if recorded successfully
        """
        try:
            if not self.database:
                logger.warning("⚠️ Database not configured - cannot record send")
                return False

            cursor = self.database.cursor()
            cursor.execute("""
            INSERT INTO ab_test_results (test_id, client_id, variant, sent_at)
            VALUES (?, ?, ?, ?)
            """, (test_id, client_id, variant, datetime.now()))

            self.database.commit()
            logger.debug(f"✅ Recorded send: test {test_id}, client {client_id}, variant {variant}")
            return True

        except Exception as e:
            logger.error(f"❌ Error recording send: {str(e)}")
            return False

    def record_open(self, test_id: int, client_id: int) -> bool:
        """
        Record that email was opened

        Args:
            test_id: A/B test ID
            client_id: Client ID

        Returns:
            True if recorded successfully
        """
        try:
            if not self.database:
                return False

            cursor = self.database.cursor()
            cursor.execute("""
            UPDATE ab_test_results
            SET opened = 1, opened_at = ?
            WHERE test_id = ? AND client_id = ? AND opened = 0
            """, (datetime.now(), test_id, client_id))

            self.database.commit()
            logger.debug(f"✅ Recorded open: test {test_id}, client {client_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error recording open: {str(e)}")
            return False

    def record_click(self, test_id: int, client_id: int) -> bool:
        """
        Record that email link was clicked

        Args:
            test_id: A/B test ID
            client_id: Client ID

        Returns:
            True if recorded successfully
        """
        try:
            if not self.database:
                return False

            cursor = self.database.cursor()
            cursor.execute("""
            UPDATE ab_test_results
            SET clicked = 1, clicked_at = ?
            WHERE test_id = ? AND client_id = ? AND clicked = 0
            """, (datetime.now(), test_id, client_id))

            self.database.commit()
            logger.debug(f"✅ Recorded click: test {test_id}, client {client_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error recording click: {str(e)}")
            return False

    def record_conversion(self, test_id: int, client_id: int) -> bool:
        """
        Record that lead converted (moved to next pipeline stage)

        Args:
            test_id: A/B test ID
            client_id: Client ID

        Returns:
            True if recorded successfully
        """
        try:
            if not self.database:
                return False

            cursor = self.database.cursor()
            cursor.execute("""
            UPDATE ab_test_results
            SET converted = 1, converted_at = ?
            WHERE test_id = ? AND client_id = ? AND converted = 0
            """, (datetime.now(), test_id, client_id))

            self.database.commit()
            logger.debug(f"✅ Recorded conversion: test {test_id}, client {client_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error recording conversion: {str(e)}")
            return False

    def _store_assignment(self, test_id: int, client_id: int, variant: str):
        """Store variant assignment in database"""
        try:
            cursor = self.database.cursor()
            cursor.execute("""
            INSERT INTO ab_test_results (test_id, client_id, variant, sent_at)
            VALUES (?, ?, ?, ?)
            """, (test_id, client_id, variant, datetime.now()))

            self.database.commit()
            logger.debug(f"✅ Assignment stored: test {test_id}, client {client_id}, variant {variant}")

        except Exception as e:
            logger.error(f"❌ Error storing assignment: {str(e)}")


def main():
    """Example usage"""
    print("🧪 Testing Email Variant Assigner...")

    assigner = EmailVariantAssigner()

    # Test deterministic assignment
    test_id = 1
    for client_id in range(1, 11):
        variant = assigner.assign_variant(test_id, client_id)
        print(f"  Client {client_id} → Variant {variant}")

    # Verify stability (same assignment twice)
    variant1 = assigner.assign_variant(1, 5)
    variant2 = assigner.assign_variant(1, 5)
    print(f"\n✅ Deterministic check: {variant1} == {variant2}: {variant1 == variant2}")

    # Calculate split
    variants = [assigner.assign_variant(1, i) for i in range(1, 101)]
    a_count = variants.count('A')
    b_count = variants.count('B')
    print(f"✅ 50/50 split: A={a_count}% ({a_count}), B={b_count}% ({b_count})")


if __name__ == "__main__":
    main()
