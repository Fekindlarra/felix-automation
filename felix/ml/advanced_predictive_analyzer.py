#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Predictive Analysis Engine
Análisis de tendencias con proyecciones ML
Scoring automático de Phase 2 readiness
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

class AdvancedPredictiveAnalyzer:
    def __init__(self, db_path="data/pipeline.sqlite"):
        self.db_path = db_path
        self.analysis_dir = Path("logs/predictive_analysis")
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    def get_historical_trend(self, metric_name: str, hours: int = 24):
        """Obtener tendencia histórica de una métrica"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            if metric_name == "ml_accuracy":
                cursor.execute("""
                    SELECT ml_accuracy_percent, timestamp
                    FROM prediction_accuracy_history
                    ORDER BY timestamp DESC LIMIT ?
                """, (hours,))
            elif metric_name == "error_rate":
                cursor.execute("""
                    SELECT error_rate_percent, timestamp
                    FROM system_health_history
                    ORDER BY timestamp DESC LIMIT ?
                """, (hours,))
            elif metric_name == "predictions":
                cursor.execute("""
                    SELECT predictions_per_hour, timestamp
                    FROM system_health_history
                    ORDER BY timestamp DESC LIMIT ?
                """, (hours,))
            else:
                return None

            data = cursor.fetchall()
            db.close()

            return data
        except:
            return None

    def calculate_trend_projection(self, data_points: list, hours_ahead: int = 20):
        """Calcular proyección usando regresión lineal simple"""
        if not data_points or len(data_points) < 2:
            return None

        values = [d[0] for d in data_points]
        n = len(values)

        # Simple linear regression
        x = list(range(n))
        x_mean = mean(x)
        y_mean = mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Project ahead
        projected = intercept + slope * (n + hours_ahead)
        return projected

    def score_phase2_readiness(self):
        """Calcular score de readiness para Phase 2 (0-100)"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            score_components = {
                'ml_accuracy': 0,
                'error_rate': 0,
                'predictions': 0,
                'assignments': 0,
                'stability': 0,
                'tests_health': 0
            }

            # 1. ML Accuracy (25 puntos)
            cursor.execute("SELECT AVG(ml_accuracy_percent) FROM prediction_accuracy_history")
            ml_acc = cursor.fetchone()[0] or 0
            score_components['ml_accuracy'] = min(25, (ml_acc / 75) * 25)

            # 2. Error Rate (20 puntos) - lower is better
            cursor.execute("SELECT AVG(error_rate_percent) FROM system_health_history")
            error_rate = cursor.fetchone()[0] or 0
            score_components['error_rate'] = max(0, 20 - (error_rate * 200))

            # 3. Predictions (15 puntos)
            cursor.execute("SELECT AVG(predictions_per_hour) FROM system_health_history")
            predictions = cursor.fetchone()[0] or 0
            score_components['predictions'] = min(15, (predictions / 36) * 15)

            # 4. Assignments (15 puntos)
            cursor.execute("SELECT COUNT(*) FROM personalization_variants")
            assignments = cursor.fetchone()[0] or 0
            score_components['assignments'] = min(15, (assignments / 70) * 15)

            # 5. Stability (15 puntos) - no critical incidents
            cursor.execute("SELECT COUNT(*) FROM ab_tests WHERE active = 1")
            active_tests = cursor.fetchone()[0] or 0
            score_components['stability'] = min(15, (active_tests / 10) * 15)

            # 6. Tests Health (10 puntos)
            cursor.execute("SELECT COUNT(*) FROM ab_tests")
            total_tests = cursor.fetchone()[0] or 0
            score_components['tests_health'] = min(10, (total_tests / 10) * 10)

            db.close()

            total_score = sum(score_components.values())
            return {
                'total_score': total_score,
                'components': score_components,
                'phase2_ready': total_score >= 83,
                'confidence': min(100, (total_score / 100) * 100)
            }

        except Exception as e:
            print(f"Error calculating score: {e}")
            return None

    def generate_phase2_recommendation(self):
        """Generar recomendación automática para Phase 2"""
        readiness = self.score_phase2_readiness()
        if not readiness:
            return None

        score = readiness['total_score']

        if score >= 90:
            recommendation = {
                'status': 'STRONG GO',
                'confidence': 'HIGH',
                'action': 'Proceed to Phase 2 escalation immediately',
                'risk_level': 'LOW',
                'monitoring': 'Continue standard 2-hour checkpoints'
            }
        elif score >= 83:
            recommendation = {
                'status': 'GO',
                'confidence': 'MEDIUM-HIGH',
                'action': 'Proceed to Phase 2 escalation',
                'risk_level': 'MEDIUM',
                'monitoring': 'Increase monitoring to 1-hour intervals'
            }
        elif score >= 70:
            recommendation = {
                'status': 'CONDITIONAL GO',
                'confidence': 'MEDIUM',
                'action': 'Proceed with caution, monitor closely',
                'risk_level': 'MEDIUM-HIGH',
                'monitoring': 'Increase monitoring to 30-minute intervals'
            }
        elif score >= 50:
            recommendation = {
                'status': 'HOLD',
                'confidence': 'LOW-MEDIUM',
                'action': 'Delay Phase 2, investigate weak areas',
                'risk_level': 'HIGH',
                'monitoring': 'Investigate root causes'
            }
        else:
            recommendation = {
                'status': 'NO-GO',
                'confidence': 'LOW',
                'action': 'Execute rollback protocol',
                'risk_level': 'CRITICAL',
                'monitoring': 'Emergency response required'
            }

        return {
            'readiness': readiness,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }

    def save_prediction_report(self, prediction_data: dict):
        """Guardar reporte de predicción"""
        filename = self.analysis_dir / f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(prediction_data, f, indent=2)
        return filename

    def generate_full_analysis(self):
        """Generar análisis completo"""
        print("\n" + "="*80)
        print("🔮 ADVANCED PREDICTIVE ANALYSIS - GENERATING")
        print("="*80)

        # Phase 2 Recommendation
        print("\n[1/2] Calculating Phase 2 Readiness Score...")
        phase2_data = self.generate_phase2_recommendation()

        if phase2_data:
            readiness = phase2_data['readiness']
            print(f"\n📊 READINESS SCORE: {readiness['total_score']:.1f}/100")
            print("\nComponent Breakdown:")
            for component, score in readiness['components'].items():
                print(f"   {component.replace('_', ' ').title()}: {score:.1f}")

            print(f"\n💡 RECOMMENDATION: {phase2_data['recommendation']['status']}")
            print(f"   Action: {phase2_data['recommendation']['action']}")
            print(f"   Risk Level: {phase2_data['recommendation']['risk_level']}")
            print(f"   Monitoring: {phase2_data['recommendation']['monitoring']}")

        # Save Report
        print("\n[2/2] Saving prediction report...")
        if phase2_data:
            filename = self.save_prediction_report(phase2_data)
            print(f"   ✅ Report saved: {filename}")

        print("\n" + "="*80)
        return phase2_data

def main():
    """Ejecutar análisis"""
    analyzer = AdvancedPredictiveAnalyzer()
    analyzer.generate_full_analysis()

if __name__ == "__main__":
    main()
