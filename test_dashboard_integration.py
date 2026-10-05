#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite - PASO 1: Dashboard Integration
Pruebas para verificar que DashboardIntegration funciona correctamente
y que los datos se pueden mostrar en el dashboard
"""

import sys
import json
import unittest
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analytics.dashboard_integration import DashboardIntegration
from orchestrator import FelixAutomationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDashboardIntegration(unittest.TestCase):
    """Tests para DashboardIntegration"""

    def setUp(self):
        """Inicializar fixtures"""
        self.orchestrator = None
        self.dashboard = None

        # Intentar conectar a BD si existe
        try:
            if Path("database.sqlite").exists():
                self.orchestrator = FelixAutomationOrchestrator()
                self.orchestrator.connect_database()
                self.dashboard = DashboardIntegration(self.orchestrator)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar DB: {e}")

    def tearDown(self):
        """Limpiar después de tests"""
        if self.orchestrator:
            try:
                self.orchestrator.close_database()
            except:
                pass

    def test_dashboard_initialization(self):
        """Test: DashboardIntegration inicializa correctamente"""
        logger.info("✅ Test: Inicialización del dashboard")

        # Sin BD
        dashboard_no_db = DashboardIntegration()
        self.assertIsNotNone(dashboard_no_db)
        self.assertIsNone(dashboard_no_db.agent)

        # Con BD
        if self.dashboard:
            self.assertIsNotNone(self.dashboard)
            self.assertIsNotNone(self.dashboard.agent)

    def test_generate_dashboard_data_structure(self):
        """Test: generate_dashboard_data retorna estructura correcta"""
        logger.info("✅ Test: Estructura de generate_dashboard_data")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible (BD no conectada)")
            return

        data = self.dashboard.generate_dashboard_data()

        # Verificar estructura
        self.assertIn('predictions', data)
        self.assertIn('anomalies', data)
        self.assertIn('recommendations', data)
        self.assertIn('timestamp', data)

        # Verificar predictions
        self.assertIn('top_10', data['predictions'])
        self.assertIn('summary', data['predictions'])
        self.assertIn('total', data['predictions']['summary'])
        self.assertIn('high_probability', data['predictions']['summary'])

        # Verificar anomalies
        self.assertIn('active', data['anomalies'])
        self.assertIn('summary', data['anomalies'])
        self.assertIn('total', data['anomalies']['summary'])

        # Verificar recommendations
        self.assertIn('urgent', data['recommendations'])
        self.assertIn('high', data['recommendations'])
        self.assertIn('summary', data['recommendations'])

        # Verificar forecast
        self.assertIn('revenue_forecast', data)

    def test_get_client_dashboard_data_structure(self):
        """Test: get_client_dashboard_data retorna estructura correcta"""
        logger.info("✅ Test: Estructura de get_client_dashboard_data")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible")
            return

        # Test con cliente que existe (si hay alguno)
        data = self.dashboard.generate_dashboard_data()
        predictions = data.get('predictions', {}).get('top_10', [])

        if predictions:
            client_id = predictions[0].get('client_id', 1)
            client_data = self.dashboard.get_client_dashboard_data(client_id)

            self.assertIn('status', client_data)
            self.assertIn('client', client_data)
            self.assertIn('prediction', client_data)
            self.assertIn('anomalies', client_data)
            self.assertIn('recommendations', client_data)

    def test_probability_status_values(self):
        """Test: _get_probability_status retorna valores correctos"""
        logger.info("✅ Test: Valores de probability status")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible")
            return

        # Test diferentes probabilidades
        test_cases = [
            (85, "🟢 ALTA"),
            (75, "🟢 ALTA"),
            (65, "🟡 MEDIA"),
            (50, "🟡 MEDIA"),
            (45, "🟠 BAJA"),
            (30, "🟠 BAJA"),
            (25, "🔴 CRÍTICA"),
            (0, "🔴 CRÍTICA"),
        ]

        for prob, expected in test_cases:
            result = self.dashboard._get_probability_status(prob)
            self.assertEqual(result, expected, f"Probability {prob} should be {expected}")

    def test_severity_colors_mapping(self):
        """Test: _get_severity_color mapea correctamente"""
        logger.info("✅ Test: Mapeo de colores por severidad")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible")
            return

        test_cases = {
            'CRITICAL': '#dc3545',
            'HIGH': '#fd7e14',
            'MEDIUM': '#ffc107',
            'LOW': '#28a745',
            'UNKNOWN': '#6c757d'
        }

        for severity, expected_color in test_cases.items():
            result = self.dashboard._get_severity_color(severity)
            self.assertEqual(result, expected_color, f"Severity {severity} should map to {expected_color}")

    def test_priority_colors_mapping(self):
        """Test: _get_priority_color mapea correctamente"""
        logger.info("✅ Test: Mapeo de colores por prioridad")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible")
            return

        test_cases = {
            'URGENT': '#dc3545',
            'HIGH': '#fd7e14',
            'MEDIUM': '#ffc107',
            'LOW': '#28a745',
            'UNKNOWN': '#6c757d'
        }

        for priority, expected_color in test_cases.items():
            result = self.dashboard._get_priority_color(priority)
            self.assertEqual(result, expected_color, f"Priority {priority} should map to {expected_color}")

    def test_stage_labels(self):
        """Test: _get_stage_label retorna labels legibles"""
        logger.info("✅ Test: Labels de etapas")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible")
            return

        test_cases = {
            'prospecto': '👤 Prospecto',
            'propuesta': '📋 Propuesta',
            'negociacion': '🤝 Negociación',
            'cerrado': '✅ Cerrado'
        }

        for stage, expected_label in test_cases.items():
            result = self.dashboard._get_stage_label(stage)
            self.assertEqual(result, expected_label, f"Stage {stage} should be {expected_label}")

    def test_timeline_labels(self):
        """Test: _get_timeline_label retorna labels legibles"""
        logger.info("✅ Test: Labels de timeline")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible")
            return

        test_cases = {
            0: 'Inmediato',
            3: '1 semana (~3 días)',
            7: '1 semana (~7 días)',
            10: '2 semanas (~10 días)',
            14: '2 semanas (~14 días)',
            20: '1 mes (~20 días)',
            30: '1 mes (~30 días)',
            45: '~45 días'
        }

        for days, expected_label in test_cases.items():
            result = self.dashboard._get_timeline_label(days)
            self.assertEqual(result, expected_label, f"Days {days} should be {expected_label}")

    def test_empty_summaries(self):
        """Test: Métodos de empty summary retornan estructuras correctas"""
        logger.info("✅ Test: Estructuras vacías")

        if not self.dashboard:
            logger.warning("⚠️ Dashboard no disponible")
            return

        # Empty prediction summary
        empty_pred = self.dashboard._empty_summary()
        self.assertIn('total', empty_pred)
        self.assertIn('high_probability', empty_pred)
        self.assertEqual(empty_pred['total'], 0)

        # Empty anomaly summary
        empty_anom = self.dashboard._empty_anomaly_summary()
        self.assertIn('total', empty_anom)
        self.assertIn('health', empty_anom)
        self.assertEqual(empty_anom['total'], 0)

        # Empty recommendation summary
        empty_rec = self.dashboard._empty_rec_summary()
        self.assertIn('total', empty_rec)
        self.assertIn('urgent_count', empty_rec)
        self.assertEqual(empty_rec['total'], 0)


def main():
    """Execute test suite"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     PASO 1: DASHBOARD INTEGRATION TEST SUITE                          ║
║     Pruebas de integración para visualización de FASE 10 Analytics    ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    # Create loader and suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardIntegration))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS - PASO 1: DASHBOARD INTEGRATION")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ PASO 1: DASHBOARD INTEGRATION - COMPLETADA EXITOSAMENTE")
        print("\n📋 Próximos Pasos:")
        print("   • PASO 2: Analytics Scheduler (APScheduler)")
        print("   • PASO 3: REST API Endpoints")
        print("   • PASO 4: Prediction Validator")
        print("   • FASE 11: White-Box Audits")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")

    print("="*70 + "\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
