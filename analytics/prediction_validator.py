#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 4: Prediction Validator
Tracks historical accuracy, validates predictions against actual outcomes,
and adjusts confidence scores for continuous model improvement.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class PredictionValidator:
    """
    Validates predictions against actual outcomes and enables continuous improvement.

    Features:
    - Track all predictions with timestamps and metadata
    - Record actual outcomes (conversion, pipeline stage, etc.)
    - Calculate accuracy metrics (precision, recall, F1, calibration)
    - Adjust confidence scores based on performance
    - Identify retraining opportunities
    - Support A/B testing of prediction models
    """

    def __init__(self, orchestrator):
        """
        Initialize Prediction Validator.

        Args:
            orchestrator: FelixAutomationOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)

    def record_prediction(self, client_id: int, prediction_data: Dict) -> str:
        """
        Record a prediction made by ConversionPredictor.

        Args:
            client_id: Client ID
            prediction_data: Dict with:
                - probability: Predicted conversion probability (0-100)
                - confidence: Confidence score (0-100)
                - pipeline_stage: Predicted pipeline stage
                - factors: List of factors influencing prediction
                - model_version: Version of prediction model used

        Returns:
            prediction_id: Unique identifier for this prediction
        """
        try:
            prediction_id = f"pred_{client_id}_{int(datetime.now().timestamp() * 1000)}"

            record = {
                'prediction_id': prediction_id,
                'client_id': client_id,
                'probability': prediction_data.get('probability', 0),
                'confidence': prediction_data.get('confidence', 0),
                'predicted_stage': prediction_data.get('pipeline_stage', 'prospecto'),
                'factors': prediction_data.get('factors', []),
                'model_version': prediction_data.get('model_version', 'v1.0'),
                'created_at': datetime.now().isoformat(),
                'actual_outcome': None,
                'actual_stage': None,
                'actual_conversion': None,
                'outcome_recorded_at': None,
                'accuracy_metrics': None,
                'status': 'pending'
            }

            # Store in database
            self.orchestrator.db.execute(
                """
                INSERT INTO predictions (
                    prediction_id, client_id, probability, confidence,
                    predicted_stage, factors, model_version, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record['prediction_id'],
                    client_id,
                    record['probability'],
                    record['confidence'],
                    record['predicted_stage'],
                    json.dumps(record['factors']),
                    record['model_version'],
                    record['created_at'],
                    'pending'
                )
            )
            self.orchestrator.db.commit()

            self.logger.info(f"✅ Prediction recorded: {prediction_id} for client {client_id}")
            return prediction_id

        except Exception as e:
            self.logger.error(f"❌ Error recording prediction: {str(e)}")
            raise

    def record_outcome(self, prediction_id: str, outcome_data: Dict) -> bool:
        """
        Record actual outcome for a prediction.

        Args:
            prediction_id: ID of the prediction to validate
            outcome_data: Dict with:
                - converted: Boolean (did they convert?)
                - actual_stage: Actual pipeline stage reached
                - closed_value: Revenue if closed
                - days_to_conversion: Days from prediction to conversion

        Returns:
            bool: Success status
        """
        try:
            # Fetch prediction
            cursor = self.orchestrator.db.execute(
                "SELECT * FROM predictions WHERE prediction_id = ?",
                (prediction_id,)
            )
            pred = cursor.fetchone()

            if not pred:
                self.logger.warning(f"⚠️ Prediction not found: {prediction_id}")
                return False

            # Calculate accuracy
            actual_converted = outcome_data.get('converted', False)
            predicted_prob = pred[2]  # probability column

            # Binarize prediction (>50% = predict conversion)
            predicted_conversion = predicted_prob >= 50

            # Calculate metrics
            accuracy = 1 if predicted_conversion == actual_converted else 0

            # Calibration: difference between predicted and actual probability
            actual_prob = 100 if actual_converted else 0
            calibration_error = abs(predicted_prob - actual_prob)

            metrics = {
                'accuracy': accuracy,
                'calibration_error': calibration_error,
                'prediction_correct': predicted_conversion == actual_converted,
                'days_to_conversion': outcome_data.get('days_to_conversion', None),
                'closed_value': outcome_data.get('closed_value', 0)
            }

            # Update prediction
            self.orchestrator.db.execute(
                """
                UPDATE predictions
                SET actual_conversion = ?, actual_stage = ?,
                    outcome_recorded_at = ?, accuracy_metrics = ?,
                    status = 'validated'
                WHERE prediction_id = ?
                """,
                (
                    actual_converted,
                    outcome_data.get('actual_stage', 'unknown'),
                    datetime.now().isoformat(),
                    json.dumps(metrics),
                    prediction_id
                )
            )
            self.orchestrator.db.commit()

            self.logger.info(
                f"✅ Outcome recorded: {prediction_id} - "
                f"Predicted: {predicted_conversion}, Actual: {actual_converted}"
            )

            return True

        except Exception as e:
            self.logger.error(f"❌ Error recording outcome: {str(e)}")
            raise

    def calculate_accuracy_metrics(self, days: int = 30, model_version: str = None) -> Dict:
        """
        Calculate accuracy metrics for predictions.

        Args:
            days: Number of days to look back
            model_version: Specific model version to analyze (None = all)

        Returns:
            Dict with metrics: precision, recall, F1, accuracy, calibration
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get validated predictions
            query = """
                SELECT probability, confidence, actual_conversion,
                       accuracy_metrics
                FROM predictions
                WHERE status = 'validated'
                AND outcome_recorded_at > ?
            """
            params = [cutoff_date]

            if model_version:
                query += " AND model_version = ?"
                params.append(model_version)

            cursor = self.orchestrator.db.execute(query, params)
            predictions = cursor.fetchall()

            if not predictions:
                return {
                    'sample_size': 0,
                    'precision': 0,
                    'recall': 0,
                    'f1_score': 0,
                    'accuracy': 0,
                    'avg_calibration_error': 0,
                    'message': 'No validated predictions in timeframe'
                }

            # Calculate metrics
            true_positives = 0
            false_positives = 0
            true_negatives = 0
            false_negatives = 0
            calibration_errors = []

            for pred in predictions:
                prob, conf, actual, metrics = pred

                # Binarize prediction
                predicted = prob >= 50

                if predicted and actual:
                    true_positives += 1
                elif predicted and not actual:
                    false_positives += 1
                elif not predicted and not actual:
                    true_negatives += 1
                else:  # not predicted and actual
                    false_negatives += 1

                # Track calibration
                if metrics:
                    try:
                        m = json.loads(metrics)
                        calibration_errors.append(m.get('calibration_error', 0))
                    except:
                        pass

            # Calculate rates
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            accuracy = (true_positives + true_negatives) / len(predictions)
            avg_calibration = mean(calibration_errors) if calibration_errors else 0

            return {
                'sample_size': len(predictions),
                'precision': round(precision, 3),
                'recall': round(recall, 3),
                'f1_score': round(f1, 3),
                'accuracy': round(accuracy, 3),
                'avg_calibration_error': round(avg_calibration, 2),
                'true_positives': true_positives,
                'false_positives': false_positives,
                'true_negatives': true_negatives,
                'false_negatives': false_negatives,
                'timeframe_days': days
            }

        except Exception as e:
            self.logger.error(f"❌ Error calculating metrics: {str(e)}")
            return {'error': str(e)}

    def adjust_confidence_scores(self, client_id: int = None) -> Dict:
        """
        Adjust confidence scores based on historical accuracy.

        For predictions with low calibration, reduce confidence.
        For predictions with high accuracy, maintain/increase confidence.

        Args:
            client_id: Specific client (None = all)

        Returns:
            Dict with adjustment summary
        """
        try:
            # Get recent predictions with outcomes
            query = """
                SELECT prediction_id, confidence, accuracy_metrics
                FROM predictions
                WHERE status = 'validated'
                AND outcome_recorded_at > datetime('now', '-30 days')
            """
            params = []

            if client_id:
                query += " AND client_id = ?"
                params.append(client_id)

            cursor = self.orchestrator.db.execute(query, params)
            predictions = cursor.fetchall()

            adjusted_count = 0
            avg_adjustment = 0

            for pred_id, conf, metrics in predictions:
                if not metrics:
                    continue

                try:
                    m = json.loads(metrics)
                    cal_error = m.get('calibration_error', 0)

                    # Calculate adjustment factor
                    # High calibration error → lower confidence
                    # Low calibration error → maintain/increase confidence
                    adjustment_factor = 1 - (cal_error / 100) * 0.1
                    adjustment_factor = max(0.7, min(1.3, adjustment_factor))  # Bound between 0.7 and 1.3

                    new_confidence = min(100, max(0, conf * adjustment_factor))
                    adjustment = new_confidence - conf

                    # Update prediction record
                    self.orchestrator.db.execute(
                        "UPDATE predictions SET confidence = ? WHERE prediction_id = ?",
                        (new_confidence, pred_id)
                    )

                    adjusted_count += 1
                    avg_adjustment += adjustment

                except:
                    pass

            self.orchestrator.db.commit()

            avg_adjustment = avg_adjustment / adjusted_count if adjusted_count > 0 else 0

            self.logger.info(
                f"✅ Adjusted {adjusted_count} confidence scores "
                f"(avg adjustment: {avg_adjustment:.1f}%)"
            )

            return {
                'adjustments_made': adjusted_count,
                'avg_adjustment': round(avg_adjustment, 2),
                'status': 'complete'
            }

        except Exception as e:
            self.logger.error(f"❌ Error adjusting confidence scores: {str(e)}")
            return {'error': str(e)}

    def get_retraining_recommendations(self) -> Dict:
        """
        Identify when model retraining is needed.

        Returns:
            Dict with retraining recommendations
        """
        try:
            # Get metrics for different timeframes
            metrics_7d = self.calculate_accuracy_metrics(days=7)
            metrics_30d = self.calculate_accuracy_metrics(days=30)

            recommendations = {
                'retrain_needed': False,
                'reasons': [],
                'metrics_7d': metrics_7d,
                'metrics_30d': metrics_30d,
                'priority': 'low'
            }

            # Check if retraining is needed
            if metrics_7d.get('sample_size', 0) >= 10:
                f1_7d = metrics_7d.get('f1_score', 0)
                f1_30d = metrics_30d.get('f1_score', 0)

                # F1 score dropping significantly
                if f1_30d > 0 and f1_7d < f1_30d * 0.85:
                    recommendations['retrain_needed'] = True
                    recommendations['reasons'].append(
                        f"F1 score dropped: {f1_30d:.3f} → {f1_7d:.3f}"
                    )
                    recommendations['priority'] = 'high'

                # Low overall F1 score
                if f1_7d < 0.6 and metrics_7d.get('sample_size', 0) >= 20:
                    recommendations['retrain_needed'] = True
                    recommendations['reasons'].append(
                        f"Low F1 score: {f1_7d:.3f} (target: 0.7+)"
                    )
                    recommendations['priority'] = 'high'

                # High calibration error
                cal_error = metrics_7d.get('avg_calibration_error', 0)
                if cal_error > 25:
                    recommendations['retrain_needed'] = True
                    recommendations['reasons'].append(
                        f"High calibration error: {cal_error:.1f}%"
                    )
                    if recommendations['priority'] == 'low':
                        recommendations['priority'] = 'medium'

                # Precision or recall too low
                precision = metrics_7d.get('precision', 0)
                recall = metrics_7d.get('recall', 0)

                if precision < 0.5 or recall < 0.5:
                    recommendations['retrain_needed'] = True
                    recommendations['reasons'].append(
                        f"Low precision ({precision:.2f}) or recall ({recall:.2f})"
                    )
                    recommendations['priority'] = 'high'

            return recommendations

        except Exception as e:
            self.logger.error(f"❌ Error generating recommendations: {str(e)}")
            return {'error': str(e)}

    def get_prediction_history(self, client_id: int = None, limit: int = 50) -> List[Dict]:
        """
        Get prediction history for analysis.

        Args:
            client_id: Specific client (None = all)
            limit: Maximum records to return

        Returns:
            List of prediction records
        """
        try:
            query = "SELECT * FROM predictions WHERE 1=1"
            params = []

            if client_id:
                query += " AND client_id = ?"
                params.append(client_id)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = self.orchestrator.db.execute(query, params)
            predictions = cursor.fetchall()

            result = []
            for pred in predictions:
                result.append({
                    'prediction_id': pred[0],
                    'client_id': pred[1],
                    'probability': pred[2],
                    'confidence': pred[3],
                    'predicted_stage': pred[4],
                    'model_version': pred[6],
                    'created_at': pred[7],
                    'status': pred[9],
                    'actual_conversion': pred[5] if len(pred) > 5 else None,
                    'accuracy_metrics': json.loads(pred[8]) if pred[8] and len(pred) > 8 else None
                })

            return result

        except Exception as e:
            self.logger.error(f"❌ Error fetching history: {str(e)}")
            return []

    def get_model_performance_by_version(self, days: int = 30) -> Dict:
        """
        Compare performance across different model versions.

        Args:
            days: Timeframe for comparison

        Returns:
            Dict with performance by model version
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
                SELECT model_version, COUNT(*) as total,
                       SUM(CASE WHEN status='validated' THEN 1 ELSE 0 END) as validated
                FROM predictions
                WHERE created_at > ?
                GROUP BY model_version
                ORDER BY created_at DESC
            """

            cursor = self.orchestrator.db.execute(query, (cutoff_date,))
            versions = cursor.fetchall()

            result = {}
            for version, total, validated in versions:
                metrics = self.calculate_accuracy_metrics(days=days, model_version=version)
                result[version] = {
                    'total_predictions': total,
                    'validated_outcomes': validated or 0,
                    **metrics
                }

            return result

        except Exception as e:
            self.logger.error(f"❌ Error comparing models: {str(e)}")
            return {}
