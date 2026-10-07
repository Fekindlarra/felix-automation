#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Final Report Generator
Generates comprehensive analysis and business impact report
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

class Phase3ReportGenerator:
    def __init__(self, db_path: str = "fase15.db"):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.checkpoints = []

    def load_checkpoints(self):
        """Load all checkpoints from database"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT hora, ml_accuracy, error_rate, websocket_latency,
                   predictions_hour, personalization_active, active_tests,
                   health_score, status, decision
            FROM phase3_checkpoints
            ORDER BY hora ASC
        """)
        self.checkpoints = [dict(row) for row in cursor.fetchall()]
        return len(self.checkpoints)

    def calculate_metrics_summary(self):
        """Calculate average metrics across all checkpoints"""
        if not self.checkpoints:
            return {}

        total = len(self.checkpoints)
        return {
            "ml_accuracy_avg": round(sum(cp["ml_accuracy"] for cp in self.checkpoints) / total * 100, 1),
            "error_rate_avg": round(sum(cp["error_rate"] for cp in self.checkpoints) / total * 100, 3),
            "latency_avg": round(sum(cp["websocket_latency"] for cp in self.checkpoints) / total, 0),
            "predictions_avg": round(sum(cp["predictions_hour"] for cp in self.checkpoints) / total, 1),
            "personalization_avg": round(sum(cp["personalization_active"] for cp in self.checkpoints) / total, 0),
            "active_tests_avg": round(sum(cp["active_tests"] for cp in self.checkpoints) / total, 1),
        }

    def get_final_decision(self):
        """Get final decision from database"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT value FROM system_config 
            WHERE key = 'PHASE_3_FINAL_DECISION'
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row[0] if row else "PENDING"

    def generate_report(self):
        """Generate comprehensive report"""
        self.load_checkpoints()
        metrics = self.calculate_metrics_summary()
        decision = self.get_final_decision()

        report = {
            "title": "FASE 15 Phase 3 - Final Report",
            "date": datetime.utcnow().isoformat(),
            "total_checkpoints": len(self.checkpoints),
            "execution_window": "HORA 48-72 (24 hours)",
            "final_status": decision,
            "metrics_summary": metrics,
            "success_criteria": {
                "ml_accuracy_target": "≥78%",
                "ml_accuracy_achieved": f"{metrics.get('ml_accuracy_avg', 0)}%",
                "error_rate_target": "<0.08%",
                "error_rate_achieved": f"{metrics.get('error_rate_avg', 0)}%",
                "latency_target": "<95ms",
                "latency_achieved": f"{metrics.get('latency_avg', 0)}ms",
            },
            "business_impact": self._calculate_impact(decision),
            "recommendation": self._get_recommendation(decision)
        }
        return report

    def _calculate_impact(self, decision):
        """Calculate projected business impact"""
        if decision == "GO":
            return {
                "status": "✅ SUCCESS",
                "user_base": "5.5M",
                "conversion_lift": "+40%",
                "annual_revenue": "+$1.9M",
                "roi_timeline": "6 months"
            }
        elif decision == "CAUTION":
            return {
                "status": "⚠️ MONITORING",
                "user_base": "2.75M",
                "conversion_lift": "+25%",
                "annual_revenue": "+$0.96M",
                "roi_timeline": "9 months"
            }
        else:
            return {
                "status": "❌ ROLLED BACK",
                "user_base": "0",
                "conversion_lift": "0%",
                "annual_revenue": "$0",
                "roi_timeline": "N/A"
            }

    def _get_recommendation(self, decision):
        """Get recommendation based on decision"""
        recommendations = {
            "GO": "Autorizar despliegue permanente a 100% de usuarios. Iniciar monitoreo de producción a largo plazo.",
            "CAUTION": "Mantener en producción con monitoreo intensivo 1 semana. Reevaluar antes de expansión completa.",
            "NO_GO": "Activar rollback. Investigar anomalías. Replanificar Fase 3 para próxima oportunidad."
        }
        return recommendations.get(decision, "Evaluación pendiente")

def main():
    generator = Phase3ReportGenerator()
    report = generator.generate_report()

    # Save report as JSON
    Path("reports").mkdir(exist_ok=True)
    with open("reports/phase3_final_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "="*80)
    print("📊 FASE 15 PHASE 3 - FINAL REPORT")
    print("="*80)
    print(f"\n🎯 Final Status: {report['final_status']}")
    print(f"\n📈 Metrics Summary:")
    for key, value in report['metrics_summary'].items():
        print(f"   {key}: {value}")
    print(f"\n💰 Business Impact: {report['business_impact']['status']}")
    print(f"   Annual Revenue: {report['business_impact']['annual_revenue']}")
    print(f"   User Base Deployed: {report['business_impact']['user_base']}")
    print(f"\n🎯 Recommendation:")
    print(f"   {report['recommendation']}")
    print("\n" + "="*80)
    print(f"✅ Report saved to reports/phase3_final_report.json\n")

if __name__ == "__main__":
    main()
