#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Reportes Automáticos Horarios
Genera reporte completo cada hora para auditoría y análisis de tendencias
Ejecutar en background: while true; do python3 generate_hourly_reports.py; sleep 3600; done
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

class HourlyReportGenerator:
    def __init__(self, db_path="data/pipeline.sqlite"):
        self.db_path = db_path
        self.reports_dir = Path("logs/hourly_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def get_current_metrics(self):
        """Obtener todas las métricas actuales"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count of tests
            cursor.execute("SELECT COUNT(*) FROM ab_tests WHERE active = 1")
            active_tests = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ab_tests")
            total_tests = cursor.fetchone()[0]

            # Predictions
            cursor.execute("SELECT COUNT(*) FROM ab_test_ml_predictions")
            predictions_tracked = cursor.fetchone()[0]

            # Personalization
            cursor.execute("SELECT COUNT(*) FROM personalization_variants")
            assignments = cursor.fetchone()[0]

            # Comparison reports
            cursor.execute("SELECT COUNT(*) FROM comparison_reports")
            comparison_reports = cursor.fetchone()[0]

            # Latest accuracy
            cursor.execute("""
                SELECT ml_accuracy FROM comparison_reports
                ORDER BY generated_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            ml_accuracy = result[0] if result else None

            # Historical counts
            cursor.execute("SELECT COUNT(*) FROM prediction_accuracy_history")
            accuracy_history_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM personalization_performance")
            perf_history_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM system_health_history")
            health_history_count = cursor.fetchone()[0]

            conn.close()

            return {
                'timestamp': datetime.now().isoformat(),
                'tests': {
                    'total': total_tests,
                    'active': active_tests
                },
                'metrics': {
                    'predictions_tracked': predictions_tracked,
                    'personalization_assignments': assignments,
                    'comparison_reports': comparison_reports,
                    'ml_accuracy_percent': ml_accuracy
                },
                'history': {
                    'accuracy_records': accuracy_history_count,
                    'performance_records': perf_history_count,
                    'health_records': health_history_count,
                    'total_historical': accuracy_history_count + perf_history_count + health_history_count
                }
            }
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return {}

    def generate_report(self):
        """Generar reporte completo"""
        metrics = self.get_current_metrics()

        if not metrics:
            print("❌ No se pudieron obtener métricas")
            return None

        timestamp = datetime.now()
        hour = timestamp.strftime("%H")
        filename = self.reports_dir / f"hourly_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            'generated_at': metrics['timestamp'],
            'hour': int(hour),
            'tests': metrics['tests'],
            'metrics': metrics['metrics'],
            'history': metrics['history'],
            'status': self._calculate_status(metrics)
        }

        # Guardar reporte
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        return report, filename

    def _calculate_status(self, metrics):
        """Calcular status general"""
        checks = []

        # Tests running
        if metrics['tests']['active'] >= 5:
            checks.append({'name': 'Active Tests', 'status': '✅', 'value': metrics['tests']['active']})
        else:
            checks.append({'name': 'Active Tests', 'status': '⚠️', 'value': metrics['tests']['active']})

        # Predictions
        if metrics['metrics']['predictions_tracked'] > 0:
            checks.append({'name': 'Predictions', 'status': '✅', 'value': metrics['metrics']['predictions_tracked']})

        # Assignments
        if metrics['metrics']['personalization_assignments'] > 0:
            checks.append({'name': 'Assignments', 'status': '✅', 'value': metrics['metrics']['personalization_assignments']})

        # Accuracy
        if metrics['metrics']['ml_accuracy_percent'] and metrics['metrics']['ml_accuracy_percent'] > 75:
            checks.append({'name': 'ML Accuracy', 'status': '✅', 'value': f"{metrics['metrics']['ml_accuracy_percent']:.1f}%"})

        # Historical
        if metrics['history']['total_historical'] > 0:
            checks.append({'name': 'Historical Data', 'status': '✅', 'value': metrics['history']['total_historical']})

        return checks

    def print_report(self, report, filename):
        """Mostrar reporte en consola"""
        print("\n" + "=" * 80)
        print(f"📊 REPORTE HORARIO - {report['generated_at']}")
        print("=" * 80)

        print(f"\n🧪 TESTS A/B")
        print(f"   Total: {report['tests']['total']} | Activos: {report['tests']['active']}")

        print(f"\n📈 MÉTRICAS")
        print(f"   Predicciones rastreadas: {report['metrics']['predictions_tracked']}")
        print(f"   Assignments personalización: {report['metrics']['personalization_assignments']}")
        print(f"   Reportes de comparación: {report['metrics']['comparison_reports']}")
        if report['metrics']['ml_accuracy_percent']:
            print(f"   ML Accuracy: {report['metrics']['ml_accuracy_percent']:.2f}%")

        print(f"\n📚 HISTÓRICO ACUMULADO")
        print(f"   Total registros: {report['history']['total_historical']}")
        print(f"   - Accuracy: {report['history']['accuracy_records']}")
        print(f"   - Performance: {report['history']['performance_records']}")
        print(f"   - Health: {report['history']['health_records']}")

        print(f"\n✅ STATUS CHECKS")
        for check in report['status']:
            print(f"   {check['status']} {check['name']}: {check['value']}")

        print(f"\n💾 Reporte guardado: {filename}")
        print("=" * 80 + "\n")

def main():
    """Generar reporte"""
    generator = HourlyReportGenerator()
    result = generator.generate_report()

    if result:
        report, filename = result
        generator.print_report(report, filename)
        return True
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
