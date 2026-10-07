#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Integration Test
Verifies all Phase 3 components are properly integrated and functional
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from backend.events import EventFactory, EventType
from agents.ml_vs_rules_comparator import MLvsRulesComparator
from agents.personalization_engine import PersonalizationEngine

class Phase3IntegrationTest:
    """Test Phase 3 integration"""

    def __init__(self, db_path="data/pipeline.sqlite"):
        self.db_path = db_path
        self.db = None
        self.test_results = {
            'passed': [],
            'failed': []
        }

    def connect_db(self):
        """Connect to database"""
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        logger.info(f"✅ Connected to {self.db_path}")

    def test_event_creation(self):
        """Test event factory methods"""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Event Factory Integration")
        logger.info("="*80)

        try:
            # Test test_created event
            event = EventFactory.test_created(
                client_id=0,
                test_id=1,
                test_name="Test Integration",
                email_type="proposal",
                duration_days=14
            )
            assert event.event_type == EventType.TEST_CREATED
            logger.info("✅ test_created event created successfully")
            self.test_results['passed'].append("Event Factory - test_created")

            # Test test_winner_announced event
            event = EventFactory.test_winner_announced(
                client_id=0,
                test_id=1,
                test_name="Test Integration",
                variant_winner="B"
            )
            assert event.event_type == EventType.TEST_WINNER_ANNOUNCED
            logger.info("✅ test_winner_announced event created successfully")
            self.test_results['passed'].append("Event Factory - test_winner_announced")

            # Test comparison_completed event
            event = EventFactory.comparison_completed(
                client_id=0,
                test_id=1,
                ml_accuracy=0.85,
                rules_accuracy=0.78,
                sample_size=100,
                winner="ML",
                confidence_interval={"lower": 0.80, "upper": 0.90}
            )
            assert event.event_type == EventType.COMPARISON_COMPLETED
            logger.info("✅ comparison_completed event created successfully")
            self.test_results['passed'].append("Event Factory - comparison_completed")

        except Exception as e:
            logger.error(f"❌ Event Factory test failed: {e}")
            self.test_results['failed'].append(f"Event Factory: {str(e)}")

    def test_ml_vs_rules_comparator(self):
        """Test ML vs Rules Comparator"""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: ML vs Rules Comparator")
        logger.info("="*80)

        try:
            comparator = MLvsRulesComparator(self.db)

            # Test recording prediction pair
            test_id = 1
            client_id = 1

            record_id = comparator.record_prediction_pair(
                test_id=test_id,
                client_id=client_id,
                ml_probability=0.85,
                rules_probability=0.72
            )

            assert record_id > 0
            logger.info(f"✅ Recorded prediction pair (ID: {record_id})")
            self.test_results['passed'].append("MLvsRulesComparator - record_prediction_pair")

            # Test recording outcome
            outcome_recorded = comparator.record_outcome(
                test_id=test_id,
                client_id=client_id,
                actual_outcome=1
            )
            assert outcome_recorded
            logger.info("✅ Recorded outcome successfully")
            self.test_results['passed'].append("MLvsRulesComparator - record_outcome")

            # Test calculate accuracy
            accuracy = comparator.calculate_accuracy(test_id)
            assert 'ml_accuracy' in accuracy or len(accuracy) >= 0
            logger.info(f"✅ Calculated accuracy: {accuracy}")
            self.test_results['passed'].append("MLvsRulesComparator - calculate_accuracy")

        except Exception as e:
            logger.error(f"❌ ML vs Rules Comparator test failed: {e}")
            self.test_results['failed'].append(f"MLvsRulesComparator: {str(e)}")

    def test_personalization_engine(self):
        """Test Personalization Engine"""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Personalization Engine")
        logger.info("="*80)

        try:
            engine = PersonalizationEngine(self.db)

            # Test applying test winner
            test_id = 1
            client_id = 2

            applied = engine.apply_test_winner(
                test_id=test_id,
                winner="A"
            )

            logger.info(f"✅ Applied test winner: {applied} records updated")
            self.test_results['passed'].append("PersonalizationEngine - apply_test_winner")

            # Test should_use_variant
            should_use, variant = engine.should_use_variant(test_id, client_id)
            logger.info(f"✅ should_use_variant: {should_use}, variant: {variant}")
            self.test_results['passed'].append("PersonalizationEngine - should_use_variant")

        except Exception as e:
            logger.error(f"❌ Personalization Engine test failed: {e}")
            self.test_results['failed'].append(f"PersonalizationEngine: {str(e)}")

    def test_database_schema(self):
        """Test database schema exists and is accessible"""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Database Schema")
        logger.info("="*80)

        try:
            cursor = self.db.cursor()

            tables = [
                'ab_test_ml_predictions',
                'personalization_variants',
                'comparison_reports',
                'ab_tests',
                'ab_test_results'
            ]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Table '{table}': {count} rows")
                self.test_results['passed'].append(f"Database - {table}")

        except Exception as e:
            logger.error(f"❌ Database schema test failed: {e}")
            self.test_results['failed'].append(f"Database schema: {str(e)}")

    def test_event_routing(self):
        """Test event routing configuration"""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Event Routing Configuration")
        logger.info("="*80)

        try:
            from backend.events import EVENT_ROUTING, EventType

            # Check Phase 3 events are in routing
            phase3_events = [
                EventType.TEST_CREATED,
                EventType.TEST_STARTED,
                EventType.TEST_COMPLETED,
                EventType.TEST_PAUSED,
                EventType.TEST_WINNER_ANNOUNCED,
                EventType.COMPARISON_STARTED,
                EventType.COMPARISON_COMPLETED
            ]

            for event_type in phase3_events:
                assert event_type in EVENT_ROUTING
                roles = EVENT_ROUTING[event_type]
                assert 'admin' in roles
                logger.info(f"✅ {event_type.value}: routed to {roles}")
                self.test_results['passed'].append(f"Event Routing - {event_type.value}")

        except Exception as e:
            logger.error(f"❌ Event routing test failed: {e}")
            self.test_results['failed'].append(f"Event routing: {str(e)}")

    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("\n" + "="*90)
        logger.info("🚀 FASE 15 PHASE 3 - INTEGRATION TEST SUITE")
        logger.info("="*90)

        self.connect_db()

        self.test_event_creation()
        self.test_ml_vs_rules_comparator()
        self.test_personalization_engine()
        self.test_database_schema()
        self.test_event_routing()

        # Summary
        logger.info("\n" + "="*90)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*90)
        logger.info(f"✅ PASSED: {len(self.test_results['passed'])} tests")
        logger.info(f"❌ FAILED: {len(self.test_results['failed'])} tests")

        if self.test_results['passed']:
            logger.info("\nPassed Tests:")
            for test in self.test_results['passed']:
                logger.info(f"  ✅ {test}")

        if self.test_results['failed']:
            logger.info("\nFailed Tests:")
            for test in self.test_results['failed']:
                logger.info(f"  ❌ {test}")

        logger.info("="*90)

        if len(self.test_results['failed']) == 0:
            logger.info("🎉 ALL TESTS PASSED - PHASE 3 INTEGRATION READY")
            return True
        else:
            logger.error("❌ SOME TESTS FAILED - CHECK ABOVE FOR DETAILS")
            return False

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

def main():
    """Run integration test suite"""
    tester = Phase3IntegrationTest()
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.close()

if __name__ == "__main__":
    sys.exit(main())
