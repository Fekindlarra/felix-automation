#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Decision Engine
Evaluates all 13 checkpoints and makes final GO/CAUTION/NO-GO decision at HORA 72
"""

import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class Phase3Decision(Enum):
    """Final Phase 3 decision outcomes"""
    GO = "GO"                      # 6/6 metrics all checkpoints
    CAUTION = "CAUTION"            # 5/6 metrics consistent
    NO_GO = "NO_GO"                # <5/6 metrics detected


class Phase3DecisionEngine:
    """Evaluate Phase 3 checkpoint data and make final decision"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.checkpoints: List[Dict] = []
        self.decision = None
        self.confidence = 0
        self.reasoning = []

    def load_checkpoints(self) -> bool:
        """Load all Phase 3 checkpoints from database"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT hora, ml_accuracy, error_rate, websocket_latency,
                   predictions_hour, personalization_active, active_tests,
                   health_score, status, decision, created_at
            FROM phase3_checkpoints
            ORDER BY hora ASC
        """)

        self.checkpoints = []
        for row in cursor.fetchall():
            checkpoint = {
                "hora": row[0],
                "metrics": {
                    "ml_accuracy": row[1],
                    "error_rate": row[2],
                    "websocket_latency": row[3],
                    "predictions_hour": row[4],
                    "personalization_active": row[5],
                    "active_tests": row[6]
                },
                "health_score": row[7],
                "status": row[8],
                "decision": row[9],
                "timestamp": row[10]
            }
            self.checkpoints.append(checkpoint)

        logger.info(f"✅ Cargados {len(self.checkpoints)} checkpoints")
        return len(self.checkpoints) > 0

    def calculate_health_scores(self) -> Dict[int, int]:
        """Calculate health score (0-6) for each checkpoint"""
        health_scores = {}

        for checkpoint in self.checkpoints:
            metrics = checkpoint["metrics"]
            checks = [
                metrics["ml_accuracy"] >= 0.78,           # ML Accuracy ≥78%
                metrics["error_rate"] < 0.0008,           # Error Rate <0.08%
                metrics["websocket_latency"] < 95,        # Latency <95ms
                metrics["predictions_hour"] >= 42,        # Predictions ≥42/hour
                metrics["personalization_active"] >= 140, # Personalization ≥140
                metrics["active_tests"] >= 8              # Active Tests ≥8
            ]
            health_scores[checkpoint["hora"]] = sum(checks)

        return health_scores

    def evaluate_checkpoint_progression(self) -> Tuple[int, int, int]:
        """Evaluate progression through checkpoints"""
        health_scores = self.calculate_health_scores()

        green_count = sum(1 for score in health_scores.values() if score >= 5)
        caution_count = sum(1 for score in health_scores.values() if score == 5)
        critical_count = sum(1 for score in health_scores.values() if score < 5)

        return green_count, caution_count, critical_count

    def make_final_decision(self) -> Phase3Decision:
        """Make final GO/CAUTION/NO-GO decision"""
        if not self.checkpoints:
            logger.error("❌ No checkpoints loaded")
            return Phase3Decision.NO_GO

        green_count, caution_count, critical_count = self.evaluate_checkpoint_progression()
        total_checkpoints = len(self.checkpoints)

        self.reasoning = []

        # Decision Logic
        if critical_count > 0:
            # ANY checkpoint with <5/6 metrics = NO-GO
            self.decision = Phase3Decision.NO_GO
            self.confidence = 0
            self.reasoning.append(f"❌ {critical_count} checkpoint(s) con <5/6 métricas detectados")
            self.reasoning.append(f"   Rollback automático activado")

        elif green_count == total_checkpoints:
            # ALL checkpoints with 6/6 = GO
            self.decision = Phase3Decision.GO
            self.confidence = 100
            self.reasoning.append(f"✅ ÉXITO: Todos los {total_checkpoints} checkpoints con 6/6 VERDE")
            self.reasoning.append(f"   Despliegue permanente autorizado")
            self.reasoning.append(f"   Confianza: 100% (perfecta)")

        elif green_count + caution_count == total_checkpoints:
            # ALL checkpoints with 5-6 metrics = CAUTION
            self.decision = Phase3Decision.CAUTION
            self.confidence = 75
            self.reasoning.append(f"⚠️  PRECAUCIÓN: Métricas consistentes 5-6/6")
            self.reasoning.append(f"   {green_count} checkpoints 6/6, {caution_count} checkpoints 5/6")
            self.reasoning.append(f"   Continuar monitoreando 1 semana antes de decisión final")
            self.reasoning.append(f"   Confianza: 75% (alto)")

        else:
            # Mixed results = CAUTION
            self.decision = Phase3Decision.CAUTION
            self.confidence = 50
            self.reasoning.append(f"⚠️  PRECAUCIÓN: Resultados mixtos en checkpoints")
            self.reasoning.append(f"   {green_count} GREEN, {caution_count} CAUTION, {critical_count} CRITICAL")
            self.reasoning.append(f"   Investigar anomalías antes de desplegar")
            self.reasoning.append(f"   Confianza: 50% (moderada)")

        return self.decision

    def calculate_metrics_summary(self) -> Dict:
        """Calculate aggregated metrics across all checkpoints"""
        if not self.checkpoints:
            return {}

        metrics_sum = {
            "ml_accuracy": 0,
            "error_rate": 0,
            "websocket_latency": 0,
            "predictions_hour": 0,
            "personalization_active": 0,
            "active_tests": 0
        }

        for checkpoint in self.checkpoints:
            for key, value in checkpoint["metrics"].items():
                metrics_sum[key] += value

        count = len(self.checkpoints)
        return {
            "ml_accuracy": round(metrics_sum["ml_accuracy"] / count, 3),
            "error_rate": round(metrics_sum["error_rate"] / count, 4),
            "websocket_latency": round(metrics_sum["websocket_latency"] / count, 1),
            "predictions_hour": round(metrics_sum["predictions_hour"] / count, 1),
            "personalization_active": int(metrics_sum["personalization_active"] / count),
            "active_tests": int(metrics_sum["active_tests"] / count)
        }

    def calculate_business_impact(self) -> Dict:
        """Calculate projected business impact"""
        avg_metrics = self.calculate_metrics_summary()

        # Conservative projections
        if self.decision == Phase3Decision.GO:
            conversion_improvement = 0.40  # +40%
            base_conversion = 0.025
            new_conversion = base_conversion * (1 + conversion_improvement)
            user_count = 5_500_000
            revenue_per_conversion = 100
            annual_revenue_impact = user_count * new_conversion * revenue_per_conversion
            roi_months = 6
        elif self.decision == Phase3Decision.CAUTION:
            conversion_improvement = 0.25  # +25%
            base_conversion = 0.025
            new_conversion = base_conversion * (1 + conversion_improvement)
            user_count = 2_750_000  # Phase 2 deployment
            revenue_per_conversion = 100
            annual_revenue_impact = user_count * new_conversion * revenue_per_conversion
            roi_months = 9
        else:
            conversion_improvement = 0
            annual_revenue_impact = 0
            roi_months = 0

        return {
            "conversion_improvement_percent": int(conversion_improvement * 100),
            "annual_revenue_impact": round(annual_revenue_impact / 1_000_000, 1),  # Millions
            "roi_timeline_months": roi_months,
            "user_base_deployed": user_count if self.decision != Phase3Decision.NO_GO else 0
        }

    def generate_decision_report(self) -> Dict:
        """Generate comprehensive final decision report"""
        if self.decision is None:
            self.make_final_decision()

        health_scores = self.calculate_health_scores()
        metrics_summary = self.calculate_metrics_summary()
        business_impact = self.calculate_business_impact()
        green_count, caution_count, critical_count = self.evaluate_checkpoint_progression()

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "final_decision": self.decision.value,
            "confidence_percent": self.confidence,
            "reasoning": self.reasoning,
            "checkpoint_summary": {
                "total_checkpoints": len(self.checkpoints),
                "green_6_6": green_count,
                "caution_5_6": caution_count,
                "critical_below_5_6": critical_count
            },
            "metrics_average": metrics_summary,
            "business_impact": business_impact,
            "recommendation": self._get_recommendation()
        }

        return report

    def _get_recommendation(self) -> str:
        """Get recommended action based on decision"""
        if self.decision == Phase3Decision.GO:
            return "Autorizar despliegue permanente a 100% de usuarios. Iniciar monitoreo de producción a largo plazo."
        elif self.decision == Phase3Decision.CAUTION:
            return "Mantener en producción con monitoreo intensivo durante 1 semana. Reevaluar antes de expansión completa."
        else:
            return "Activar rollback automático. Investigar anomalías. Replanificar Fase 3 para próxima oportunidad."

    def save_decision(self, report: Dict) -> bool:
        """Save final decision to database"""
        cursor = self.db.cursor()

        # Save decision to system_config
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value)
            VALUES (?, ?)
        """, ("PHASE_3_FINAL_DECISION", report["final_decision"]))

        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value)
            VALUES (?, ?)
        """, ("PHASE_3_DECISION_CONFIDENCE", str(report["confidence_percent"])))

        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value)
            VALUES (?, ?)
        """, ("PHASE_3_DECISION_TIMESTAMP", report["timestamp"]))

        # Save full report as JSON
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value)
            VALUES (?, ?)
        """, ("PHASE_3_DECISION_REPORT_JSON", json.dumps(report)))

        self.db.commit()
        logger.info(f"✅ Decision saved to database: {report['final_decision']}")

        return True

    def print_decision_report(self, report: Dict):
        """Print formatted decision report"""
        print("\n" + "=" * 80)
        print("🎯 FASE 15 PHASE 3 - FINAL DECISION REPORT (HORA 72)")
        print("=" * 80)

        print(f"\n📊 FINAL DECISION: {report['final_decision']}")
        print(f"   Confidence: {report['confidence_percent']}%")

        print(f"\n📈 Checkpoint Summary:")
        print(f"   Total: {report['checkpoint_summary']['total_checkpoints']}")
        print(f"   6/6 GREEN: {report['checkpoint_summary']['green_6_6']}")
        print(f"   5/6 CAUTION: {report['checkpoint_summary']['caution_5_6']}")
        print(f"   <5/6 CRITICAL: {report['checkpoint_summary']['critical_below_5_6']}")

        print(f"\n💡 Reasoning:")
        for reason in report["reasoning"]:
            print(f"   {reason}")

        print(f"\n📊 Metrics Average:")
        for metric, value in report["metrics_average"].items():
            if "accuracy" in metric:
                print(f"   {metric}: {value*100:.1f}%")
            elif "rate" in metric:
                print(f"   {metric}: {value*100:.3f}%")
            elif "latency" in metric:
                print(f"   {metric}: {value:.1f}ms")
            else:
                print(f"   {metric}: {value}")

        print(f"\n💰 Business Impact:")
        impact = report["business_impact"]
        print(f"   Conversion Improvement: +{impact['conversion_improvement_percent']}%")
        print(f"   Annual Revenue Impact: +${impact['annual_revenue_impact']:.1f}M")
        print(f"   ROI Timeline: {impact['roi_timeline_months']} months")
        print(f"   User Base Deployed: {impact['user_base_deployed']:,}")

        print(f"\n🎯 Recommendation:")
        print(f"   {report['recommendation']}")

        print("\n" + "=" * 80 + "\n")


def make_phase3_final_decision(db_path: str = "fase15.db") -> Tuple[Phase3Decision, Dict]:
    """Main function to make final Phase 3 decision"""
    engine = Phase3DecisionEngine(db_path)

    if not engine.load_checkpoints():
        logger.error("❌ No checkpoint data available")
        return Phase3Decision.NO_GO, {}

    decision = engine.make_final_decision()
    report = engine.generate_decision_report()

    engine.print_decision_report(report)
    engine.save_decision(report)

    return decision, report


if __name__ == "__main__":
    decision, report = make_phase3_final_decision()
    print(f"\n✅ Decision: {decision.value}")
