#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HORA 24 Readiness Validator
Valida progreso hacia GO status para Phase 2 escalation
Proporciona checklist clara de qué falta para alcanzar GO
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class HORA24ReadinessValidator:
    def __init__(self, db_path="data/pipeline.sqlite"):
        self.db_path = db_path
        self.validator_dir = Path("logs/hora24_validation")
        self.validator_dir.mkdir(parents=True, exist_ok=True)

        # Thresholds for Phase 2 GO
        self.go_criteria = {
            'ml_accuracy': {'value': 75, 'operator': '>=', 'unit': '%'},
            'error_rate': {'value': 0.1, 'operator': '<', 'unit': '%'},
            'websocket_latency': {'value': 100, 'operator': '<', 'unit': 'ms'},
            'predictions_per_hour': {'value': 36, 'operator': '>=', 'unit': '/hora'},
            'personalization_assignments': {'value': 70, 'operator': '>=', 'unit': 'total'},
            'active_tests': {'value': 5, 'operator': '>=', 'unit': 'tests'}
        }

    def validate_criterion(self, criterion: str, actual_value: float):
        """Validar un criterio individual"""
        if criterion not in self.go_criteria:
            return None

        threshold = self.go_criteria[criterion]
        operator = threshold['operator']
        threshold_val = threshold['value']

        if operator == '>=':
            passes = actual_value >= threshold_val
        elif operator == '>':
            passes = actual_value > threshold_val
        elif operator == '<':
            passes = actual_value < threshold_val
        elif operator == '<=':
            passes = actual_value <= threshold_val
        else:
            passes = False

        return {
            'criterion': criterion,
            'actual': actual_value,
            'threshold': threshold_val,
            'operator': operator,
            'unit': threshold['unit'],
            'passes': passes,
            'gap': actual_value - threshold_val if operator in ['>=', '>'] else threshold_val - actual_value
        }

    def get_current_metrics(self):
        """Obtener métricas actuales para validación"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            # ML Accuracy
            cursor.execute("SELECT AVG(ml_accuracy_percent) FROM prediction_accuracy_history")
            ml_acc = cursor.fetchone()[0] or 0

            # Error Rate
            cursor.execute("SELECT AVG(error_rate_percent) FROM system_health_history")
            error_rate = cursor.fetchone()[0] or 0

            # WebSocket Latency
            cursor.execute("SELECT websocket_latency_ms FROM system_health_history ORDER BY timestamp DESC LIMIT 1")
            result = cursor.fetchone()
            ws_lat = result[0] if result else 8

            # Predictions per Hour
            cursor.execute("SELECT AVG(predictions_per_hour) FROM system_health_history")
            pred_hour = cursor.fetchone()[0] or 0

            # Personalization Assignments
            cursor.execute("SELECT COUNT(*) FROM personalization_variants")
            assignments = cursor.fetchone()[0]

            # Active Tests
            cursor.execute("SELECT COUNT(*) FROM ab_tests WHERE active = 1")
            active_tests = cursor.fetchone()[0]

            db.close()

            return {
                'ml_accuracy': ml_acc,
                'error_rate': error_rate,
                'websocket_latency': ws_lat,
                'predictions_per_hour': pred_hour,
                'personalization_assignments': assignments,
                'active_tests': active_tests
            }

        except Exception as e:
            print(f"❌ Error getting metrics: {e}")
            return {}

    def validate_all_criteria(self):
        """Validar todos los criterios de GO"""
        metrics = self.get_current_metrics()

        results = {}
        for criterion, _ in self.go_criteria.items():
            actual = metrics.get(criterion, 0)
            results[criterion] = self.validate_criterion(criterion, actual)

        return results

    def print_validation_report(self):
        """Mostrar reporte de validación"""
        print("\n" + "="*80)
        print("🎯 HORA 24 READINESS VALIDATION REPORT")
        print("="*80)

        results = self.validate_all_criteria()

        passes = sum(1 for r in results.values() if r and r['passes'])
        total = len(results)

        print(f"\n📊 VALIDATION SCORE: {passes}/{total} CRITERIA PASS")
        print(f"🎯 GO THRESHOLD: 5/6 or 83% (currently: {100*passes/total:.0f}%)")

        print(f"\n{'Criterion':<30} {'Actual':<15} {'Threshold':<15} {'Status':<12}")
        print("-" * 72)

        passed_list = []
        failed_list = []

        for criterion, result in results.items():
            if result:
                status = "✅ PASS" if result['passes'] else "❌ FAIL"
                actual_str = f"{result['actual']:.1f} {result['unit']}"
                threshold_str = f"{result['operator']} {result['threshold']}"

                print(f"{criterion:<30} {actual_str:<15} {threshold_str:<15} {status:<12}")

                if result['passes']:
                    passed_list.append(criterion)
                else:
                    failed_list.append({
                        'criterion': criterion,
                        'gap': result['gap'],
                        'actual': result['actual'],
                        'threshold': result['threshold']
                    })

        # GO/NO-GO Decision
        print("\n" + "="*80)
        if passes >= 5:
            print("✅ RECOMMENDATION: GO FOR PHASE 2 ESCALATION")
            print(f"   Met {passes} of 6 criteria. Ready for 50% rollout.")
            confidence = min(100, 83 + (passes - 5) * 17)
            print(f"   Confidence: {confidence:.0f}%")
        else:
            print("❌ RECOMMENDATION: NO-GO (Hold for optimization)")
            print(f"   Only met {passes} of 6 criteria. Need more work.")

            print(f"\n🔧 AREAS NEEDING IMPROVEMENT:")
            for item in failed_list:
                deficit = item['threshold'] - item['actual'] if item['threshold'] > item['actual'] else 0
                print(f"   • {item['criterion']}: {item['actual']:.1f} (need +{deficit:.1f} to reach {item['threshold']})")

        print("\n" + "="*80)

        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_results': results,
            'summary': {
                'criteria_passed': passes,
                'total_criteria': total,
                'score_percent': 100 * passes / total,
                'go_threshold': 83,
                'recommendation': 'GO' if passes >= 5 else 'NO-GO'
            }
        }

        filename = self.validator_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved: {filename}")
        return passes >= 5

def main():
    validator = HORA24ReadinessValidator()
    validator.print_validation_report()

if __name__ == "__main__":
    main()
