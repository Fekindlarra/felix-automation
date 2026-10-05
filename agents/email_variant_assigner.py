#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 14: Email Variant Assigner
Deterministic A/B variant assignment for email tests
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)


class EmailVariantAssigner:
    """Assign clients to A/B test variants deterministically"""

    def assign_variant(self, test_id: int, client_id: int) -> Literal['A', 'B']:
        """
        Assign client to variant based on hash
        Same client always gets same variant for same test
        """
        hash_value = hash(f"{test_id}_{client_id}")
        return 'A' if hash_value % 2 == 0 else 'B'

    def get_test_group_counts(self, test_id: int, 
                             client_ids: list) -> dict:
        """Get count of clients in each variant"""
        variant_a = 0
        variant_b = 0

        for client_id in client_ids:
            if self.assign_variant(test_id, client_id) == 'A':
                variant_a += 1
            else:
                variant_b += 1

        return {
            "variant_a": variant_a,
            "variant_b": variant_b,
            "total": len(client_ids),
            "ratio_a": variant_a / len(client_ids) if client_ids else 0
        }

    def is_client_in_test(self, test_id: int, client_id: int) -> bool:
        """Check if client is eligible for test (always true if hash assigned)"""
        return True

    def log_assignment(self, test_id: int, client_id: int):
        """Log variant assignment"""
        variant = self.assign_variant(test_id, client_id)
        logger.debug(f"Assigned client {client_id} to variant {variant} (test {test_id})")
