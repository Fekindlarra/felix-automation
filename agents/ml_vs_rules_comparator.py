#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3: ML vs Rules Comparator
Tracks and compares ML prediction accuracy vs rule-based prediction accuracy
Generates comparison reports and broadcasts results via WebSocket
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class MLvsRulesComparator:
    """
    Compares ML prediction accuracy against rule-based prediction approach.
    Tracks both methods during A/B tests for data-driven optimization.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize comparator with database connection"""
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        logger.info("✅ MLvsRulesComparator initialized")

    def record_prediction_pair(self, test_id: int, client_id: int,
                               ml_probability: float, rules_probability: float) -> int:
        """
        Record both ML and rule-based predictions for a client during A/B test.

        Args:
            test_id: A/B test identifier
            client_id: Client identifier
            ml_probability: ML model probability (0-1)
            rules_probability: Rule-based probability (0-1)

        Returns:
            Prediction record ID
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ab_test_ml_predictions
                (test_id, client_id, ml_probability, rules_probability, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (test_id, client_id, ml_probability, rules_probability))

            self.db.commit()
            record_id = cursor.lastrowid

            logger.info(f"📊 Recorded prediction pair for test {test_id}, client {client_id}")
            return record_id

        except sqlite3.Error as e:
            logger.error(f"❌ Error recording prediction pair: {e}")
            return -1

    def record_outcome(self, test_id: int, client_id: int, actual_outcome: int) -> bool:
        """
        Record the actual conversion outcome for a prediction.

        Args:
            test_id: A/B test identifier
            client_id: Client identifier
            actual_outcome: 0 = no conversion, 1 = conversion

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE ab_test_ml_predictions
                SET actual_outcome = ?, outcome_date = CURRENT_TIMESTAMP
                WHERE test_id = ? AND client_id = ?
            """, (actual_outcome, test_id, client_id))

            self.db.commit()

            logger.info(f"✅ Recorded outcome for test {test_id}, client {client_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"❌ Error recording outcome: {e}")
            return False

    def calculate_accuracy(self, test_id: int) -> Dict:
        """
        Calculate accuracy of ML vs rules based on actual conversion outcomes.
        Only considers predictions where actual_outcome has been recorded.

        Args:
            test_id: A/B test identifier

        Returns:
            Dictionary with accuracy metrics:
            {
                'ml_accuracy': float (0-1),
                'rules_accuracy': float (0-1),
                'winner': str ('ML', 'RULES', or 'TIE'),
                'sample_size': int,
                'ml_predictions': list of (prob, outcome),
                'rules_predictions': list of (prob, outcome)
            }
        """
        try:
            cursor = self.db.cursor()

            # Get all predictions with recorded outcomes
            cursor.execute("""
                SELECT ml_probability, rules_probability, actual_outcome
                FROM ab_test_ml_predictions
                WHERE test_id = ? AND actual_outcome IS NOT NULL
                ORDER BY created_at ASC
            """, (test_id,))

            results = cursor.fetchall()

            if not results:
                logger.warning(f"⚠️ No outcomes recorded for test {test_id}")
                return {
                    'ml_accuracy': None,
                    'rules_accuracy': None,
                    'winner': None,
                    'sample_size': 0,
                    'ml_predictions': [],
                    'rules_predictions': []
                }

            # Convert probabilities to binary predictions (>0.5 = 1, <=0.5 = 0)
            ml_predictions = []
            rules_predictions = []

            for row in results:
                ml_prob = float(row['ml_probability'])
                rules_prob = float(row['rules_probability'])
                actual = int(row['actual_outcome'])

                ml_pred = 1 if ml_prob > 0.5 else 0
                rules_pred = 1 if rules_prob > 0.5 else 0

                ml_predictions.append((ml_pred, actual))
                rules_predictions.append((rules_pred, actual))

            # Calculate accuracy
            ml_correct = sum(1 for pred, actual in ml_predictions if pred == actual)
            rules_correct = sum(1 for pred, actual in rules_predictions if pred == actual)

            sample_size = len(ml_predictions)
            ml_accuracy = ml_correct / sample_size if sample_size > 0 else 0
            rules_accuracy = rules_correct / sample_size if sample_size > 0 else 0

            # Determine winner
            if ml_accuracy > rules_accuracy + 0.05:  # ML needs 5% margin
                winner = 'ML'
            elif rules_accuracy > ml_accuracy + 0.05:  # Rules needs 5% margin
                winner = 'RULES'
            else:
                winner = 'TIE'

            logger.info(f"📈 Accuracy for test {test_id}: ML={ml_accuracy:.2%}, Rules={rules_accuracy:.2%}, Winner={winner}")

            return {
                'ml_accuracy': ml_accuracy,
                'rules_accuracy': rules_accuracy,
                'winner': winner,
                'sample_size': sample_size,
                'ml_correct': ml_correct,
                'rules_correct': rules_correct,
                'ml_predictions': ml_predictions,
                'rules_predictions': rules_predictions
            }

        except sqlite3.Error as e:
            logger.error(f"❌ Error calculating accuracy: {e}")
            return {
                'ml_accuracy': None,
                'rules_accuracy': None,
                'winner': None,
                'sample_size': 0
            }

    def calculate_confidence_interval(self, accuracy: float, sample_size: int,
                                     confidence_level: float = 0.95) -> Dict:
        """
        Calculate Wilson score confidence interval for accuracy metric.
        More reliable than normal approximation for small samples.

        Args:
            accuracy: Proportion correct (0-1)
            sample_size: Number of predictions
            confidence_level: Confidence level (default 0.95 for 95% CI)

        Returns:
            Dictionary with confidence interval:
            {'lower': float, 'upper': float, 'center': float}
        """
        if sample_size == 0:
            return {'lower': 0, 'upper': 0, 'center': 0}

        # Wilson score interval
        from math import sqrt

        z = 1.96  # 95% confidence level
        n = sample_size
        p_hat = accuracy

        denominator = 1 + z**2 / n
        center = (p_hat + z**2 / (2*n)) / denominator
        margin = z * sqrt(p_hat * (1 - p_hat) / n + z**2 / (4*n**2)) / denominator

        lower = max(0, center - margin)
        upper = min(1, center + margin)

        return {
            'lower': round(lower, 4),
            'upper': round(upper, 4),
            'center': round(center, 4),
            'margin': round(margin, 4)
        }

    def generate_comparison_report(self, test_id: int) -> Dict:
        """
        Generate summary comparison report and store in database.

        Args:
            test_id: A/B test identifier

        Returns:
            Comparison report dictionary
        """
        try:
            # Calculate accuracy metrics
            accuracy = self.calculate_accuracy(test_id)

            if accuracy['sample_size'] == 0:
                logger.warning(f"⚠️ Cannot generate report for test {test_id}: no data")
                return None

            # Calculate confidence intervals
            ml_ci = self.calculate_confidence_interval(
                accuracy['ml_accuracy'],
                accuracy['sample_size']
            )
            rules_ci = self.calculate_confidence_interval(
                accuracy['rules_accuracy'],
                accuracy['sample_size']
            )

            # Prepare report
            report = {
                'test_id': test_id,
                'ml_accuracy': round(accuracy['ml_accuracy'], 4),
                'rules_accuracy': round(accuracy['rules_accuracy'], 4),
                'ml_avg_confidence': ml_ci['center'],
                'rules_avg_confidence': rules_ci['center'],
                'winner': accuracy['winner'],
                'sample_size': accuracy['sample_size'],
                'confidence_interval': {
                    'ml': ml_ci,
                    'rules': rules_ci
                },
                'generated_at': datetime.utcnow().isoformat()
            }

            # Store in database
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO comparison_reports
                (test_id, ml_accuracy, rules_accuracy, ml_avg_confidence,
                 winner, confidence_interval, sample_size, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                test_id,
                report['ml_accuracy'],
                report['rules_accuracy'],
                report['ml_avg_confidence'],
                report['winner'],
                json.dumps(report['confidence_interval']),
                report['sample_size']
            ))

            self.db.commit()

            logger.info(f"✅ Generated comparison report for test {test_id}")
            return report

        except sqlite3.Error as e:
            logger.error(f"❌ Error generating report: {e}")
            return None

    def get_report(self, test_id: int) -> Optional[Dict]:
        """Retrieve stored comparison report"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT * FROM comparison_reports WHERE test_id = ?
            """, (test_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'id': row['id'],
                'test_id': row['test_id'],
                'ml_accuracy': row['ml_accuracy'],
                'rules_accuracy': row['rules_accuracy'],
                'ml_avg_confidence': row['ml_avg_confidence'],
                'winner': row['winner'],
                'sample_size': row['sample_size'],
                'confidence_interval': json.loads(row['confidence_interval']),
                'generated_at': row['generated_at']
            }

        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving report: {e}")
            return None

    def get_prediction_stats(self, test_id: int) -> Dict:
        """Get detailed statistics about predictions for a test"""
        try:
            cursor = self.db.cursor()

            # Get all predictions
            cursor.execute("""
                SELECT ml_probability, rules_probability, actual_outcome
                FROM ab_test_ml_predictions
                WHERE test_id = ?
            """, (test_id,))

            predictions = cursor.fetchall()

            if not predictions:
                return {'count': 0}

            ml_probs = [float(p['ml_probability']) for p in predictions]
            rules_probs = [float(p['rules_probability']) for p in predictions]

            stats = {
                'total_predictions': len(predictions),
                'with_outcomes': sum(1 for p in predictions if p['actual_outcome'] is not None),
                'ml_prob_avg': round(mean(ml_probs), 4),
                'ml_prob_min': round(min(ml_probs), 4),
                'ml_prob_max': round(max(ml_probs), 4),
                'rules_prob_avg': round(mean(rules_probs), 4),
                'rules_prob_min': round(min(rules_probs), 4),
                'rules_prob_max': round(max(rules_probs), 4),
            }

            # Add std dev if we have multiple samples
            if len(ml_probs) > 1:
                stats['ml_prob_stdev'] = round(stdev(ml_probs), 4)
                stats['rules_prob_stdev'] = round(stdev(rules_probs), 4)

            return stats

        except sqlite3.Error as e:
            logger.error(f"❌ Error getting prediction stats: {e}")
            return {'count': 0}
