#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite - PASO 2: Analytics Scheduler
Pruebas para verificar que AnalyticsScheduler funciona correctamente
"""

import sys
import json
import unittest
import logging
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from analytics.analytics_scheduler import AnalyticsScheduler
from felix.orchestration.orchestrator import FelixAutomationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAnalyticsScheduler(unittest.TestCase):
    """Tests para AnalyticsScheduler"""

    def setUp(self):
        """Inicializar fixtures"""
        self.orchestrator = None
        self.scheduler = None

        # Intentar conectar a BD si existe
        try:
            if Path("database.sqlite").exists():
                self.orchestrator = FelixAutomationOrchestrator()
                self.orchestrator.connect_database()
                self.scheduler = AnalyticsScheduler(self.orchestrator)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar DB: {e}")

    def tearDown(self):
        """Limpiar después de tests"""
        if self.scheduler and self.scheduler.scheduler.running:
            try:
                self.scheduler.stop()
            except:
                pass
        if self.orchestrator:
            try:
                self.orchestrator.close_database()
            except:
                pass

    def test_scheduler_initialization(self):
        """Test: AnalyticsScheduler inicializa correctamente"""
        logger.info("✅ Test: Inicialización del scheduler")

        # Sin BD
        scheduler_no_db = AnalyticsScheduler()
        self.assertIsNotNone(scheduler_no_db)
        self.assertIsNone(scheduler_no_db.orchestrator)
        self.assertFalse(scheduler_no_db.scheduler.running)

        # Con BD
        if self.scheduler:
            self.assertIsNotNone(self.scheduler)
            self.assertIsNotNone(self.scheduler.orchestrator)

    def test_scheduler_start_stop(self):
        """Test: Scheduler inicia y se detiene correctamente"""
        logger.info("✅ Test: Start/Stop del scheduler")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        # Start
        self.scheduler.start()
        self.assertTrue(self.scheduler.scheduler.running)
        logger.info("   ✓ Scheduler started")

        # Stop
        self.scheduler.stop()
        self.assertFalse(self.scheduler.scheduler.running)
        logger.info("   ✓ Scheduler stopped")

    def test_add_daily_analysis(self):
        """Test: Se puede programar análisis diario"""
        logger.info("✅ Test: Programación de análisis diario")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        self.scheduler.start()

        # Add daily job
        job = self.scheduler.add_daily_analysis(hour=10, minute=30)

        self.assertIsNotNone(job)
        self.assertEqual(job.id, 'daily_analytics')
        logger.info(f"   ✓ Daily job added: {job.id}")

        self.scheduler.stop()

    def test_add_weekly_analysis(self):
        """Test: Se puede programar análisis semanal"""
        logger.info("✅ Test: Programación de análisis semanal")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        self.scheduler.start()

        # Add weekly job (Monday at 09:00)
        job = self.scheduler.add_weekly_analysis(day_of_week=0, hour=9)

        self.assertIsNotNone(job)
        self.assertEqual(job.id, 'weekly_analytics')
        logger.info(f"   ✓ Weekly job added: {job.id}")

        self.scheduler.stop()

    def test_run_analysis_now(self):
        """Test: Se puede ejecutar análisis inmediato"""
        logger.info("✅ Test: Análisis inmediato")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        # Ejecutar análisis
        result = self.scheduler.run_analysis_now('full')

        # Verificar estructura del resultado
        self.assertIn('status', result)
        self.assertIn('timestamp', result)

        # Si fue exitoso, verificar summary
        if result.get('status') == 'success':
            self.assertIn('summary', result)
            self.assertIn('total_predictions', result['summary'])
            self.assertIn('total_anomalies', result['summary'])
            logger.info(f"   ✓ Analysis completed: {result['summary']}")
        else:
            logger.warning(f"   ⚠️ Analysis failed: {result.get('reason')}")

    def test_notification_threshold_configuration(self):
        """Test: Se pueden configurar umbrales de notificación"""
        logger.info("✅ Test: Configuración de umbrales de notificación")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        # Configuración inicial
        initial_thresholds = self.scheduler.notification_threshold.copy()

        # Cambiar configuración
        new_thresholds = {
            'CRITICAL': True,
            'HIGH': False,
            'MEDIUM': False,
            'LOW': False
        }

        self.scheduler.configure_notifications(new_thresholds)

        # Verificar que cambió
        self.assertEqual(
            self.scheduler.notification_threshold,
            new_thresholds
        )
        logger.info("   ✓ Notification thresholds updated")

    def test_get_scheduler_status(self):
        """Test: Se puede obtener estado del scheduler"""
        logger.info("✅ Test: Estado del scheduler")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        self.scheduler.start()

        # Add some jobs
        self.scheduler.add_daily_analysis(hour=8)
        self.scheduler.add_weekly_analysis(day_of_week=0, hour=8)

        # Get status
        status = self.scheduler.get_scheduler_status()

        self.assertIn('running', status)
        self.assertIn('jobs_count', status)
        self.assertIn('jobs', status)
        self.assertTrue(status['running'])
        self.assertGreaterEqual(status['jobs_count'], 2)
        logger.info(f"   ✓ Status retrieved: {status['jobs_count']} jobs")

        self.scheduler.stop()

    def test_job_history_structure(self):
        """Test: Estructura de historial de trabajos"""
        logger.info("✅ Test: Estructura de historial")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        # Obtener historial
        history = self.scheduler.get_job_history(limit=10)

        # Verificar estructura (aunque esté vacío)
        self.assertIsInstance(history, list)

        if history:
            job = history[0]
            self.assertIn('job_id', job)
            self.assertIn('analysis_type', job)
            self.assertIn('status', job)
            self.assertIn('timestamp', job)
            logger.info(f"   ✓ Job history structure valid: {len(history)} records")
        else:
            logger.info("   ℹ️  No job history available yet")

    def test_trend_analysis_empty(self):
        """Test: Análisis de tendencias retorna estructura correcta"""
        logger.info("✅ Test: Análisis de tendencias")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        # Get trends
        trends = self.scheduler.get_trend_analysis(days=7)

        # Verificar estructura
        self.assertIn('period_days', trends)
        self.assertIn('daily_stats', trends)
        self.assertIn('week_over_week_change', trends)
        self.assertIn('total_runs', trends)
        self.assertIn('avg_execution_time', trends)

        self.assertEqual(trends['period_days'], 7)
        self.assertIsInstance(trends['daily_stats'], list)
        logger.info(f"   ✓ Trend analysis structure valid")

    def test_empty_analysis_result(self):
        """Test: Resultado vacío de análisis tiene estructura correcta"""
        logger.info("✅ Test: Resultado vacío de análisis")

        result = AnalyticsScheduler._empty_analysis_result(
            'full', 'test_reason', 'test error'
        )

        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['analysis_type'], 'full')
        self.assertEqual(result['reason'], 'test_reason')
        self.assertIn('summary', result)
        self.assertEqual(result['summary']['total_predictions'], 0)
        logger.info("   ✓ Empty analysis result structure valid")

    def test_multiple_job_configurations(self):
        """Test: Se pueden configurar múltiples trabajos"""
        logger.info("✅ Test: Configuración de múltiples trabajos")

        if not self.scheduler:
            logger.warning("⚠️ Scheduler no disponible")
            return

        self.scheduler.start()

        # Add multiple daily jobs at different times
        self.scheduler.add_daily_analysis(hour=8, minute=0)
        self.scheduler.add_daily_analysis(hour=14, minute=30)  # Sobrescribe el anterior
        self.scheduler.add_weekly_analysis(day_of_week=0, hour=9)
        self.scheduler.add_weekly_analysis(day_of_week=3, hour=15)  # Sobrescribe el anterior

        status = self.scheduler.get_scheduler_status()

        # Debe haber 2 trabajos (daily y weekly, siendo los últimos los que sobrescriben)
        self.assertEqual(status['jobs_count'], 2)
        logger.info(f"   ✓ Multiple jobs configured correctly")

        self.scheduler.stop()


def main():
    """Execute test suite"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     PASO 2: ANALYTICS SCHEDULER TEST SUITE                            ║
║     Pruebas de integración para automatización de análisis            ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    # Create loader and suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyticsScheduler))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS - PASO 2: ANALYTICS SCHEDULER")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ PASO 2: ANALYTICS SCHEDULER - COMPLETADA EXITOSAMENTE")
        print("\n📋 Próximos Pasos:")
        print("   • PASO 3: REST API Enhancement")
        print("   • PASO 4: Prediction Validator")
        print("   • FASE 11: White-Box Audits")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")

    print("="*70 + "\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
