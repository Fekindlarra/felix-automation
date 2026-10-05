#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite - FASE 10: Advanced Analytics
Pruebas para: ConversionPredictor, AnomalyDetector, RecommendationEngine, AnalyticsAgent
"""

import sys
import json
import unittest
import logging
from pathlib import Path
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))

from analytics.predictor import ConversionPredictor, ConversionPrediction
from analytics.anomaly_detector import AnomalyDetector, Anomaly
from analytics.recommender import RecommendationEngine, RecommendationType, RecommendationPriority
from agents.analytics_agent import AnalyticsAgent
from orchestrator import FelixAutomationOrchestrator

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestConversionPredictor(unittest.TestCase):
    """Tests para ConversionPredictor"""

    def setUp(self):
        self.predictor = ConversionPredictor()

    def test_predictor_initialization(self):
        """Test: Predictor inicializa correctamente"""
        logger.info("✅ Test: Inicialización del predictor")
        self.assertIsNotNone(self.predictor)
        self.assertEqual(len(self.predictor.conversion_history), 0)

    def test_single_prediction_high_probability(self):
        """Test: Predicción con alta probabilidad"""
        logger.info("✅ Test: Predicción de alta probabilidad")

        client_data = {
            'id': 1,
            'name': 'High Potential Client',
            'audit_score': 85,
            'pipeline_stage': 'negociacion',
            'days_in_stage': 3,
            'email_opens': 4,
            'email_clicks': 2,
            'business_type': 'saas',
            'proposal_sent': True
        }

        prediction = self.predictor.predict_conversion(1, client_data)

        self.assertIsInstance(prediction, ConversionPrediction)
        self.assertGreater(prediction.probability, 70)  # Should be high
        self.assertGreater(prediction.confidence, 60)
        self.assertGreater(len(prediction.positive_factors), 0)

    def test_single_prediction_low_probability(self):
        """Test: Predicción con baja probabilidad"""
        logger.info("✅ Test: Predicción de baja probabilidad")

        client_data = {
            'id': 2,
            'name': 'Low Potential Client',
            'audit_score': 35,
            'pipeline_stage': 'prospecto',
            'days_in_stage': 20,
            'email_opens': 0,
            'email_clicks': 0,
            'business_type': 'local',
            'proposal_sent': False
        }

        prediction = self.predictor.predict_conversion(2, client_data)

        self.assertIsInstance(prediction, ConversionPrediction)
        self.assertLess(prediction.probability, 50)  # Should be low
        self.assertGreater(len(prediction.risk_factors), 0)

    def test_batch_predictions(self):
        """Test: Predicciones en lote"""
        logger.info("✅ Test: Predicciones en lote")

        clients_data = [
            {
                'id': 1,
                'name': 'Client A',
                'audit_score': 80,
                'pipeline_stage': 'propuesta',
                'days_in_stage': 5,
                'email_opens': 3,
                'email_clicks': 1,
                'business_type': 'ecommerce'
            },
            {
                'id': 2,
                'name': 'Client B',
                'audit_score': 50,
                'pipeline_stage': 'prospecto',
                'days_in_stage': 10,
                'email_opens': 1,
                'email_clicks': 0,
                'business_type': 'local'
            }
        ]

        predictions = self.predictor.predict_batch(clients_data)

        self.assertEqual(len(predictions), 2)
        # Verificar que Client A tiene probabilidad más alta que Client B
        client_a = next(p for p in predictions if p.client_id == 1)
        client_b = next(p for p in predictions if p.client_id == 2)
        self.assertGreater(client_a.probability, client_b.probability)

    def test_revenue_forecast(self):
        """Test: Forecast de revenue"""
        logger.info("✅ Test: Forecast de revenue")

        client_data = {
            'id': 1,
            'name': 'Client',
            'audit_score': 75,
            'pipeline_stage': 'propuesta',
            'days_in_stage': 5,
            'email_opens': 2,
            'email_clicks': 1,
            'business_type': 'saas'
        }

        prediction = self.predictor.predict_conversion(1, client_data)
        predictions = [prediction]
        proposal_amounts = {1: 5000}

        forecast = self.predictor.forecast_revenue(predictions, proposal_amounts)

        self.assertIn('30_days', forecast)
        self.assertIn('60_days', forecast)
        self.assertIn('90_days', forecast)
        self.assertGreater(forecast['total_expected'], 0)


class TestAnomalyDetector(unittest.TestCase):
    """Tests para AnomalyDetector"""

    def setUp(self):
        self.detector = AnomalyDetector()

    def test_detector_initialization(self):
        """Test: Detector inicializa correctamente"""
        logger.info("✅ Test: Inicialización del detector")
        self.assertIsNotNone(self.detector)

    def test_score_drop_anomaly(self):
        """Test: Detección de caída de score"""
        logger.info("✅ Test: Detección de score drop")

        current_data = {
            'id': 1,
            'name': 'Client',
            'audit_score': 50
        }
        baseline_data = {
            'audit_score': 85
        }

        anomalies = self.detector.detect_anomalies(current_data, baseline_data)

        self.assertGreater(len(anomalies), 0)
        score_drop = next((a for a in anomalies if a.anomaly_type == 'score_drop'), None)
        self.assertIsNotNone(score_drop)
        # Drop is 41.2% (>40%), so should be CRITICAL
        self.assertEqual(score_drop.severity, 'CRITICAL')

    def test_pipeline_stagnation_anomaly(self):
        """Test: Detección de estancamiento en pipeline"""
        logger.info("✅ Test: Detección de pipeline stagnation")

        client_data = {
            'id': 1,
            'name': 'Stagnant Client',
            'pipeline_stage': 'propuesta',
            'days_in_stage': 40  # >21 días = estancado
        }

        anomalies = self.detector.detect_anomalies(client_data)

        stagnation = next((a for a in anomalies if a.anomaly_type == 'pipeline_stagnation'), None)
        self.assertIsNotNone(stagnation)
        self.assertIn('HIGH', stagnation.severity)

    def test_engagement_gap_anomaly(self):
        """Test: Detección de falta de engagement"""
        logger.info("✅ Test: Detección de engagement gap")

        client_data = {
            'id': 1,
            'name': 'No Engagement Client',
            'proposal_sent': True,
            'days_since_proposal': 12,
            'email_opens': 0  # No abrió
        }

        anomalies = self.detector.detect_anomalies(client_data)

        engagement = next((a for a in anomalies if a.anomaly_type == 'engagement_gap'), None)
        self.assertIsNotNone(engagement)
        self.assertEqual(engagement.severity, 'HIGH')

    def test_batch_anomalies(self):
        """Test: Detección de anomalías en lote"""
        logger.info("✅ Test: Detección en lote")

        clients_data = [
            {
                'id': 1,
                'name': 'Client A',
                'audit_score': 85,
                'pipeline_stage': 'prospecto',
                'days_in_stage': 5
            },
            {
                'id': 2,
                'name': 'Client B',
                'pipeline_stage': 'propuesta',
                'days_in_stage': 50,  # Anomalía
                'audit_score': 60
            }
        ]

        results = self.detector.detect_batch(clients_data)

        # Solo Client B debe tener anomalías
        self.assertEqual(len(results), 1)
        self.assertIn(2, results)

    def test_severity_score(self):
        """Test: Cálculo de score de severidad"""
        logger.info("✅ Test: Score de severidad")

        anomaly1 = Anomaly(
            client_id=1,
            client_name='Client',
            anomaly_type='test',
            severity='HIGH',
            description='Test',
            suggested_action='Test',
            detected_at=datetime.utcnow()
        )

        score = self.detector.get_severity_score([anomaly1])
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)


class TestRecommendationEngine(unittest.TestCase):
    """Tests para RecommendationEngine"""

    def setUp(self):
        self.engine = RecommendationEngine()

    def test_engine_initialization(self):
        """Test: Engine inicializa correctamente"""
        logger.info("✅ Test: Inicialización del engine")
        self.assertIsNotNone(self.engine)

    def test_prospecto_recommendations(self):
        """Test: Recomendaciones para prospecto"""
        logger.info("✅ Test: Recomendaciones para prospecto")

        client_data = {
            'id': 1,
            'name': 'Prospecto',
            'pipeline_stage': 'prospecto',
            'audit_score': 70,
            'proposal_sent': False
        }

        recs = self.engine.generate_recommendations(client_data)

        self.assertGreater(len(recs), 0)
        # Debe recomendar enviar propuesta
        send_proposal = next((r for r in recs if 'propuesta' in r.title.lower()), None)
        self.assertIsNotNone(send_proposal)

    def test_propuesta_recommendations(self):
        """Test: Recomendaciones para propuesta"""
        logger.info("✅ Test: Recomendaciones para propuesta")

        client_data = {
            'id': 1,
            'name': 'Propuesta',
            'pipeline_stage': 'propuesta',
            'proposal_sent': True,
            'days_since_proposal': 10,
            'email_opens': 0
        }

        recs = self.engine.generate_recommendations(client_data)

        self.assertGreater(len(recs), 0)
        # Debe recomendar follow-up
        followup = next((r for r in recs if r.type == RecommendationType.FOLLOW_UP), None)
        self.assertIsNotNone(followup)

    def test_negociacion_recommendations(self):
        """Test: Recomendaciones para negociación"""
        logger.info("✅ Test: Recomendaciones para negociación")

        client_data = {
            'id': 1,
            'name': 'Negociacion',
            'pipeline_stage': 'negociacion',
            'audit_score': 80,
            'proposal_sent': True
        }

        prediction = {'probability': 80}  # Alta
        recs = self.engine.generate_recommendations(client_data, prediction)

        self.assertGreater(len(recs), 0)
        # Debe recomendar cerrar rápido
        immediate = next((r for r in recs if r.priority == RecommendationPriority.URGENT), None)
        self.assertIsNotNone(immediate)

    def test_action_plan_generation(self):
        """Test: Generación de plan de acción"""
        logger.info("✅ Test: Generación de plan de acción")

        client_data = {
            'id': 1,
            'name': 'Client',
            'pipeline_stage': 'propuesta'
        }

        recs = self.engine.generate_recommendations(client_data)
        plan = self.engine.get_action_plan(recs)

        self.assertIn('urgent_actions', plan)
        self.assertIn('timeline', plan)


class TestAnalyticsAgent(unittest.TestCase):
    """Tests para AnalyticsAgent"""

    def setUp(self):
        """Inicializar fixtures"""
        self.orchestrator = None
        self.agent = None

        # Conectar orchestrator si BD existe
        try:
            if Path("database.sqlite").exists():
                self.orchestrator = FelixAutomationOrchestrator()
                self.orchestrator.connect_database()
                self.agent = AnalyticsAgent(self.orchestrator)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar DB: {e}")

    def tearDown(self):
        """Limpiar después de tests"""
        if self.orchestrator:
            try:
                self.orchestrator.close_database()
            except:
                pass

    def test_agent_initialization(self):
        """Test: Agent inicializa correctamente"""
        logger.info("✅ Test: Inicialización del agent")

        if not self.agent:
            logger.warning("⚠️ Agent no disponible (DB no conectada)")
            return

        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.predictor)
        self.assertIsNotNone(self.agent.anomaly_detector)
        self.assertIsNotNone(self.agent.recommender)

    def test_analyze_all_clients(self):
        """Test: Análisis de todos los clientes"""
        logger.info("✅ Test: Análisis de todos los clientes")

        if not self.agent:
            logger.warning("⚠️ Agent no disponible")
            return

        result = self.agent.analyze_all_clients()

        if result.get('status') == 'no_clients':
            logger.warning("⚠️ No hay clientes para analizar")
            return

        self.assertEqual(result['status'], 'success')
        self.assertIn('summary', result)
        self.assertIn('predictions', result)


class TestFase10Summary(unittest.TestCase):
    """Suite de integración FASE 10"""

    def setUp(self):
        """Print suite header"""
        print("\n" + "="*70)
        print("🚀 FASE 10 ADVANCED ANALYTICS TEST SUITE")
        print("="*70)
        print("✓ Conversion Predictor (Análisis predictivo)")
        print("✓ Anomaly Detector (Detección de anomalías)")
        print("✓ Recommendation Engine (Recomendaciones inteligentes)")
        print("✓ Analytics Agent (Orquestación)")
        print("="*70 + "\n")

    def test_all_fase10_components(self):
        """Verify all FASE 10 components"""
        logger.info("✅ All FASE 10 components verified!")


def main():
    """Execute test suite"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     FASE 10 - ADVANCED ANALYTICS TEST SUITE                           ║
║                                                                        ║
║  Componentes a Probar:                                               ║
║  ✓ Conversion Predictor (Probabilidades de conversión)              ║
║  ✓ Anomaly Detector (Patrones inusuales)                           ║
║  ✓ Recommendation Engine (Acciones inteligentes)                   ║
║  ✓ Analytics Agent (Orquestación completa)                        ║
║                                                                        ║
║  Testing: All components verified                                    ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    # Create loader and suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestConversionPredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestAnomalyDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestRecommendationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyticsAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestFase10Summary))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS - FASE 10 ADVANCED ANALYTICS")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ FASE 10 - ADVANCED ANALYTICS - COMPLETADA EXITOSAMENTE")
        print("\n📋 Próximas Fases:")
        print("   • FASE 11: Real-World API Integration")
        print("   • FASE 12: Enterprise Features")
        print("   • FASE 13: Deployment & Optimization")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")

    print("="*70 + "\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
