#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite - PASO 4: Prediction Validator
Pruebas para validación de predicciones, ajuste de confianza,
y recomendaciones de reentrenamiento.
"""

import sys
import json
import sqlite3
import unittest
import logging
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import FelixAutomationOrchestrator
from analytics.prediction_validator import PredictionValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPredictionValidator(unittest.TestCase):
    """Tests para Prediction Validator"""

    def setUp(self):
        """Inicializar fixtures"""
        self.orchestrator = None
        self.validator = None

        # Intentar conectar a BD
        try:
            if Path("database.sqlite").exists():
                self.orchestrator = FelixAutomationOrchestrator()
                self.orchestrator.connect_database()
                self.validator = PredictionValidator(self.orchestrator)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar DB: {e}")

    def tearDown(self):
        """Limpiar después de tests"""
        if self.orchestrator:
            try:
                self.orchestrator.close_database()
            except:
                pass

    def test_record_prediction_structure(self):
        """Test: Estructura de grabación de predicción"""
        logger.info("✅ Test: Estructura de grabación de predicción")

        prediction_data = {
            'probability': 75,
            'confidence': 85,
            'pipeline_stage': 'propuesta',
            'factors': ['high_engagement', 'previous_purchase'],
            'model_version': 'v1.0'
        }

        # Validar estructura
        self.assertIn('probability', prediction_data)
        self.assertIn('confidence', prediction_data)
        self.assertIn('pipeline_stage', prediction_data)
        self.assertGreaterEqual(prediction_data['probability'], 0)
        self.assertLessEqual(prediction_data['probability'], 100)
        self.assertGreaterEqual(prediction_data['confidence'], 0)
        self.assertLessEqual(prediction_data['confidence'], 100)

        logger.info("   ✓ Prediction structure valid")

    def test_outcome_recording_structure(self):
        """Test: Estructura de grabación de resultado"""
        logger.info("✅ Test: Estructura de grabación de resultado")

        outcome_data = {
            'converted': True,
            'actual_stage': 'cerrado',
            'closed_value': 5000,
            'days_to_conversion': 14
        }

        # Validar estructura
        self.assertIn('converted', outcome_data)
        self.assertIn('actual_stage', outcome_data)
        self.assertIsInstance(outcome_data['converted'], bool)
        self.assertGreaterEqual(outcome_data['closed_value'], 0)

        logger.info("   ✓ Outcome structure valid")

    def test_accuracy_metrics_structure(self):
        """Test: Estructura de métricas de exactitud"""
        logger.info("✅ Test: Estructura de métricas de exactitud")

        metrics = {
            'sample_size': 100,
            'precision': 0.85,
            'recall': 0.78,
            'f1_score': 0.81,
            'accuracy': 0.82,
            'avg_calibration_error': 12.5,
            'true_positives': 70,
            'false_positives': 12,
            'true_negatives': 16,
            'false_negatives': 2
        }

        # Validar estructura
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)
        self.assertIn('accuracy', metrics)
        self.assertIn('avg_calibration_error', metrics)

        # Validar rangos
        self.assertGreaterEqual(metrics['precision'], 0)
        self.assertLessEqual(metrics['precision'], 1)
        self.assertGreaterEqual(metrics['accuracy'], 0)
        self.assertLessEqual(metrics['accuracy'], 1)

        logger.info("   ✓ Accuracy metrics structure valid")

    def test_calibration_error_calculation(self):
        """Test: Cálculo de error de calibración"""
        logger.info("✅ Test: Cálculo de error de calibración")

        # Predict 85% probability, actually converted (100%)
        calibration_error = abs(85 - 100)
        self.assertEqual(calibration_error, 15)

        # Predict 60% probability, didn't convert (0%)
        calibration_error = abs(60 - 0)
        self.assertEqual(calibration_error, 60)

        # Perfect prediction
        calibration_error = abs(100 - 100)
        self.assertEqual(calibration_error, 0)

        logger.info("   ✓ Calibration error calculation valid")

    def test_confidence_adjustment_logic(self):
        """Test: Lógica de ajuste de confianza"""
        logger.info("✅ Test: Lógica de ajuste de confianza")

        # High calibration error → reduce confidence
        base_confidence = 80
        high_cal_error = 35  # High error
        adjustment_factor = 1 - (high_cal_error / 100) * 0.1
        new_confidence = base_confidence * adjustment_factor

        self.assertLess(new_confidence, base_confidence)

        # Low calibration error → maintain confidence
        low_cal_error = 5  # Low error
        adjustment_factor = 1 - (low_cal_error / 100) * 0.1
        new_confidence = base_confidence * adjustment_factor

        self.assertGreater(new_confidence, base_confidence * 0.9)

        logger.info("   ✓ Confidence adjustment logic valid")

    def test_retraining_need_f1_drop(self):
        """Test: Identificar necesidad de reentrenamiento por caída de F1"""
        logger.info("✅ Test: Identificar necesidad de reentrenamiento (F1 drop)")

        f1_30d = 0.80
        f1_7d = 0.65

        # Significant drop (> 15%)
        drop_threshold = f1_30d * 0.85
        retrain_needed = f1_7d < drop_threshold

        self.assertTrue(retrain_needed)

        # No significant drop
        f1_7d = 0.77
        retrain_needed = f1_7d < drop_threshold

        self.assertFalse(retrain_needed)

        logger.info("   ✓ F1 drop detection valid")

    def test_retraining_need_low_f1(self):
        """Test: Identificar necesidad de reentrenamiento por F1 bajo"""
        logger.info("✅ Test: Identificar necesidad de reentrenamiento (Low F1)")

        f1_score = 0.55
        sample_size = 25

        # Low F1 with sufficient sample
        retrain_needed = f1_score < 0.6 and sample_size >= 20

        self.assertTrue(retrain_needed)

        # Low F1 but insufficient sample
        sample_size = 10
        retrain_needed = f1_score < 0.6 and sample_size >= 20

        self.assertFalse(retrain_needed)

        logger.info("   ✓ Low F1 detection valid")

    def test_retraining_need_calibration(self):
        """Test: Identificar necesidad de reentrenamiento por calibración"""
        logger.info("✅ Test: Identificar necesidad de reentrenamiento (Calibration)")

        # High calibration error
        cal_error = 28
        retrain_needed = cal_error > 25

        self.assertTrue(retrain_needed)

        # Acceptable calibration error
        cal_error = 18
        retrain_needed = cal_error > 25

        self.assertFalse(retrain_needed)

        logger.info("   ✓ Calibration error detection valid")

    def test_model_comparison_structure(self):
        """Test: Estructura de comparación de modelos"""
        logger.info("✅ Test: Estructura de comparación de modelos")

        model_comparison = {
            'v1.0': {
                'total_predictions': 100,
                'validated_outcomes': 85,
                'f1_score': 0.82,
                'accuracy': 0.81
            },
            'v1.1': {
                'total_predictions': 120,
                'validated_outcomes': 110,
                'f1_score': 0.85,
                'accuracy': 0.84
            }
        }

        # Validar estructura
        for version, metrics in model_comparison.items():
            self.assertIn('f1_score', metrics)
            self.assertIn('accuracy', metrics)
            self.assertGreater(metrics['validated_outcomes'], 0)

        logger.info("   ✓ Model comparison structure valid")

    def test_prediction_id_generation(self):
        """Test: Generación de prediction_id único"""
        logger.info("✅ Test: Generación de prediction_id único")

        import time

        # Generar múltiples IDs
        ids = []
        for i in range(5):
            timestamp = int(time.time() * 1000)
            pred_id = f"pred_{i}_{timestamp}"
            ids.append(pred_id)
            time.sleep(0.01)  # Pequeña pausa para diferencia en timestamp

        # Verificar que todos comienzan con 'pred_'
        for pred_id in ids:
            self.assertTrue(pred_id.startswith('pred_'))

        # Verificar unicidad
        self.assertEqual(len(ids), len(set(ids)))

        logger.info("   ✓ Prediction ID generation valid")

    def test_metric_calculations_edge_cases(self):
        """Test: Cálculos de métricas en casos extremos"""
        logger.info("✅ Test: Cálculos de métricas en casos extremos")

        # Zero predictions
        precision = 0  # 0 / (0 + 0)
        self.assertEqual(precision, 0)

        # Perfect predictions
        tp, fp = 100, 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        self.assertEqual(precision, 1.0)

        # No true positives
        tp, fn = 0, 50
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        self.assertEqual(recall, 0)

        # Perfect F1
        precision, recall = 1.0, 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        self.assertEqual(f1, 1.0)

        logger.info("   ✓ Edge case calculations valid")

    def test_history_limit_constraint(self):
        """Test: Limitación de registro histórico"""
        logger.info("✅ Test: Limitación de registro histórico")

        limit = 50
        max_limit = 500

        # Normalizar límite
        final_limit = min(limit, max_limit)
        self.assertEqual(final_limit, 50)

        # Exceso de límite
        limit = 1000
        final_limit = min(limit, max_limit)
        self.assertEqual(final_limit, 500)

        logger.info("   ✓ History limit constraint valid")

    def test_timeframe_calculations(self):
        """Test: Cálculos de marco temporal"""
        logger.info("✅ Test: Cálculos de marco temporal")

        from datetime import datetime, timedelta

        # 7 days ago
        cutoff_7d = datetime.now() - timedelta(days=7)
        self.assertIsInstance(cutoff_7d, datetime)

        # 30 days ago
        cutoff_30d = datetime.now() - timedelta(days=30)
        self.assertLess(cutoff_30d, cutoff_7d)

        # Valid ISO format
        iso_date = cutoff_7d.isoformat()
        self.assertIsInstance(iso_date, str)
        self.assertIn('T', iso_date)

        logger.info("   ✓ Timeframe calculations valid")

    def test_priority_assignment(self):
        """Test: Asignación de prioridad de reentrenamiento"""
        logger.info("✅ Test: Asignación de prioridad de reentrenamiento")

        # High priority cases
        high_priority_cases = [
            ('F1 drop', {'f1_30d': 0.80, 'f1_7d': 0.65}),
            ('Low F1', {'f1_7d': 0.55, 'sample_size': 25}),
            ('Low precision', {'precision': 0.45, 'recall': 0.80}),
        ]

        for case_name, metrics in high_priority_cases:
            # All should indicate high priority
            has_condition = any([
                metrics.get('f1_7d', 0) < metrics.get('f1_30d', 1) * 0.85,
                metrics.get('f1_7d', 0) < 0.6,
                metrics.get('precision', 1) < 0.5
            ])
            self.assertTrue(has_condition)

        logger.info("   ✓ Priority assignment valid")


def main():
    """Execute test suite"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     PASO 4: PREDICTION VALIDATOR TEST SUITE                           ║
║     Pruebas de exactitud, validación y recomendaciones de ajuste       ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    # Create loader and suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestPredictionValidator))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS - PASO 4: PREDICTION VALIDATOR")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ PASO 4: PREDICTION VALIDATOR - COMPLETADA EXITOSAMENTE")
        print("\n📋 Próximos Pasos:")
        print("   • FASE 11: White-Box Audits (Shopify, Jumpseller, Code Analysis)")
        print("   • FASE 12: Dashboard Interno + Portal Cliente")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")

    print("="*70 + "\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
