#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sales Pipeline Agent - FASE 6
Gestión avanzada del pipeline con predicciones y reportes
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalesPipelineAgent:
    """Agente que analiza y predice el pipeline de ventas"""

    ETAPAS = {
        1: "prospecto",
        2: "propuesta",
        3: "negociacion",
        4: "cerrado"
    }

    CIERRE_PESOS = {
        "stage_progression": 0.30,
        "engagement": 0.25,
        "lead_score": 0.20,
        "days_in_stage": 0.15,
        "communication_frequency": 0.10
    }

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        self.pipeline_file = Path("data/pipeline.json")
        self.followup_file = Path("data/followup_sequences.json")
        self.analytics_file = Path("data/pipeline_analytics.json")
        self._ensure_files()
        logger.info("✅ Sales Pipeline Agent inicializado")

    def _ensure_files(self):
        """Crear archivos si no existen"""
        if not self.analytics_file.exists():
            self.analytics_file.write_text(json.dumps({"analytics": []}, indent=2))

    def get_pipeline_health(self) -> Dict:
        """Calcula la salud general del pipeline"""
        try:
            pipeline_data = json.loads(self.pipeline_file.read_text())
        except:
            return {"error": "No se pudo leer pipeline"}

        clients = pipeline_data.get("pipeline", [])
        if not clients:
            return {"status": "empty"}

        stage_times = defaultdict(list)
        for client in clients:
            stage = client.get("stage", 1)
            created = datetime.fromisoformat(client.get("created_at", datetime.now().isoformat()))
            updated = datetime.fromisoformat(client.get("updated_at", datetime.now().isoformat()))
            days_in_stage = (updated - created).days
            stage_times[self.ETAPAS[stage]].append(days_in_stage)

        stage_health = {}
        for stage_name, times in stage_times.items():
            stage_health[stage_name] = {
                "count": len(times),
                "avg_days": sum(times) / len(times) if times else 0,
                "min_days": min(times) if times else 0,
                "max_days": max(times) if times else 0
            }

        closed = len([c for c in clients if c.get("stage") == 4])
        velocity = (closed / len(clients) * 100) if clients else 0

        return {
            "total_clients": len(clients),
            "closed_deals": closed,
            "pipeline_velocity": f"{velocity:.1f}%",
            "stage_health": stage_health,
            "calculated_at": datetime.now().isoformat()
        }

    def predict_deal_closure(self, client_id: int) -> Dict:
        """Predice probabilidad de cierre de un cliente"""
        client = self.orchestrator.get_client(client_id)
        if not client:
            return {"error": f"Cliente {client_id} no encontrado"}

        try:
            pipeline_data = json.loads(self.pipeline_file.read_text())
        except:
            return {"error": "No se pudo leer pipeline"}

        pipeline_client = None
        for c in pipeline_data.get("pipeline", []):
            if c.get("client_id") == client_id:
                pipeline_client = c
                break

        if not pipeline_client:
            return {"error": f"Cliente {client_id} no en pipeline"}

        scores = {}

        stage = pipeline_client.get("stage", 1)
        stage = stage or 1  # Asegurar que stage no es None
        stage_score = (stage / 4) * 100
        scores["stage_progression"] = stage_score

        try:
            followup_data = json.loads(self.followup_file.read_text())
            engagement_score = 0
            for seq in followup_data.get("sequences", []):
                if seq.get("client_id") == client_id:
                    opened = sum(1 for f in seq.get("followups", {}).values() if f.get("opened"))
                    sent = sum(1 for f in seq.get("followups", {}).values() if f.get("sent"))
                    if sent > 0:
                        engagement_score = (opened / sent) * 100
                    break
            scores["engagement"] = engagement_score
        except:
            scores["engagement"] = 0

        lead_score = getattr(client, 'score', 50)
        scores["lead_score"] = lead_score

        created = datetime.fromisoformat(pipeline_client.get("created_at", datetime.now().isoformat()))
        updated = datetime.fromisoformat(pipeline_client.get("updated_at", datetime.now().isoformat()))
        days_in_stage = (updated - created).days or 1  # Asegurar que no es 0
        days_score = min(100, (days_in_stage / 10) * 100)
        scores["days_in_stage"] = days_score

        try:
            followup_data = json.loads(self.followup_file.read_text())
            comm_count = 0
            for seq in followup_data.get("sequences", []):
                if seq.get("client_id") == client_id:
                    comm_count = sum(1 for f in seq.get("followups", {}).values() if f.get("sent"))
                    break
            comm_score = min(100, (comm_count / 3) * 100)
            scores["communication_frequency"] = comm_score
        except:
            scores["communication_frequency"] = 0

        total_probability = 0
        for factor, weight in self.CIERRE_PESOS.items():
            score = scores.get(factor, 0) or 0  # Asegurar que score es numérico
            if not isinstance(score, (int, float)):
                score = 0
            total_probability += (score * weight)

        if total_probability >= 75:
            category = "MUY PROBABLE"
            emoji = "🟢"
        elif total_probability >= 50:
            category = "PROBABLE"
            emoji = "🟡"
        else:
            category = "BAJO POTENCIAL"
            emoji = "🔴"

        return {
            "client_id": client_id,
            "client_name": client.name,
            "stage": self.ETAPAS.get(stage, "desconocida"),
            "closure_probability": f"{total_probability:.1f}%",
            "category": category,
            "emoji": emoji,
            "factors": scores,
            "predicted_at": datetime.now().isoformat()
        }

    def get_at_risk_clients(self, days_threshold: int = 14) -> List[Dict]:
        """Identifica clientes en riesgo (sin movimiento)"""
        try:
            pipeline_data = json.loads(self.pipeline_file.read_text())
        except:
            return []

        at_risk = []
        now = datetime.now()

        for client in pipeline_data.get("pipeline", []):
            if client.get("stage") == 4:
                continue

            updated = datetime.fromisoformat(client.get("updated_at", datetime.now().isoformat()))
            days_without_update = (now - updated).days

            if days_without_update >= days_threshold:
                at_risk.append({
                    "client_id": client.get("client_id"),
                    "client_name": client.get("client_name"),
                    "stage": self.ETAPAS.get(client.get("stage"), "desconocida"),
                    "last_update": client.get("updated_at")[:10],
                    "days_without_update": days_without_update
                })

        return sorted(at_risk, key=lambda x: x["days_without_update"], reverse=True)

    def generate_weekly_report(self) -> str:
        """Genera reporte semanal del pipeline"""
        health = self.get_pipeline_health()
        at_risk = self.get_at_risk_clients()

        try:
            pipeline_data = json.loads(self.pipeline_file.read_text())
            clients = pipeline_data.get("pipeline", [])
        except:
            clients = []

        by_stage = defaultdict(list)
        for client in clients:
            stage = self.ETAPAS.get(client.get("stage"), "desconocida")
            by_stage[stage].append(client)

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         REPORTE SEMANAL DE PIPELINE                          ║
║         {datetime.now().strftime('%Y-%m-%d %H:%M')}                          ║
╚═══════════════════════════════════════════════════════════════╝

📊 SALUD GENERAL DEL PIPELINE:
   • Total de clientes: {health.get('total_clients', 0)}
   • Deals cerrados: {health.get('closed_deals', 0)}
   • Velocidad del pipeline: {health.get('pipeline_velocity', 'N/A')}

📈 CLIENTES POR ETAPA:
"""

        for stage in [1, 2, 3, 4]:
            stage_name = self.ETAPAS[stage]
            count = len(by_stage[stage_name])
            pct = (count / len(clients) * 100) if clients else 0
            report += f"\n   {stage_name.upper()}: {count} clientes ({pct:.1f}%)"

        report += f"""

⚠️  CLIENTES EN RIESGO:
"""
        if at_risk:
            for client in at_risk[:5]:
                report += f"\n   • {client['client_name']} - Sin actualizar {client['days_without_update']} días"
        else:
            report += "\n   ✅ Ningún cliente en riesgo"

        report += "\n\n═════════════════════════════════════════════════════════════════\n"
        return report

    def export_pipeline_analytics(self) -> Dict:
        """Exporta datos analíticos del pipeline a JSON"""
        health = self.get_pipeline_health()
        at_risk = self.get_at_risk_clients()

        try:
            pipeline_data = json.loads(self.pipeline_file.read_text())
            clients = pipeline_data.get("pipeline", [])
        except:
            clients = []

        predictions = []
        for client in clients:
            pred = self.predict_deal_closure(client.get("client_id"))
            if "error" not in pred:
                predictions.append(pred)

        # Calcular probabilidad promedio de forma segura
        high_probability_count = 0
        avg_probability = 0
        if predictions:
            for p in predictions:
                try:
                    prob = float(p["closure_probability"].strip("%"))
                    if prob >= 75:
                        high_probability_count += 1
                except (ValueError, AttributeError, TypeError):
                    pass

            # Calcular promedio solo si hay predicciones válidas
            valid_probs = []
            for p in predictions:
                try:
                    prob = float(p["closure_probability"].strip("%"))
                    valid_probs.append(prob)
                except (ValueError, AttributeError, TypeError):
                    pass

            if valid_probs:
                avg_probability = sum(valid_probs) / len(valid_probs)

        analytics = {
            "timestamp": datetime.now().isoformat(),
            "pipeline_health": health,
            "at_risk_clients": at_risk,
            "closure_predictions": predictions,
            "summary": {
                "total_clients": len(clients),
                "total_at_risk": len(at_risk),
                "high_probability_deals": high_probability_count,
                "average_closure_probability": avg_probability
            }
        }

        self.analytics_file.write_text(json.dumps(analytics, indent=2, ensure_ascii=False))
        logger.info("✅ Analytics exportado a JSON")

        return analytics

    def get_followup_report(self) -> str:
        """Genera reporte de seguimientos del pipeline"""
        health = self.get_pipeline_health()
        at_risk = self.get_at_risk_clients()

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         REPORTE DE SEGUIMIENTO DEL PIPELINE                  ║
║         {datetime.now().strftime('%Y-%m-%d %H:%M')}                          ║
╚═══════════════════════════════════════════════════════════════╝

📊 SALUD DEL PIPELINE:
   • Total de clientes: {health.get('total_clients', 0)}
   • Deals cerrados: {health.get('closed_deals', 0)}
   • Velocidad del pipeline: {health.get('pipeline_velocity', 'N/A')}

⚠️  CLIENTES EN RIESGO:
"""

        if at_risk:
            for client in at_risk[:10]:
                report += f"\n   • {client['client_name']} - Sin actualizar {client['days_without_update']} días (Etapa: {client['stage']})"
        else:
            report += "\n   ✅ Ningún cliente en riesgo"

        report += "\n\n═════════════════════════════════════════════════════════════════\n"
        return report


def main():
    """Testing del agente"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║          SALES PIPELINE AGENT - FASE 6                        ║
║      Análisis Predictivo y Reportes del Pipeline             ║
╚════════════════════════════════════════════════════════════════╝
    """)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = SalesPipelineAgent(orchestrator)

    print("\n1️⃣ SALUD DEL PIPELINE")
    print("-" * 70)
    health = agent.get_pipeline_health()
    print(json.dumps(health, indent=2, ensure_ascii=False))

    print("\n2️⃣ PREDICCIONES DE CIERRE")
    print("-" * 70)
    for client_id in [1, 2, 3]:
        pred = agent.predict_deal_closure(client_id)
        if "error" not in pred:
            print(f"{pred['emoji']} {pred['client_name']}: {pred['closure_probability']}")

    print("\n3️⃣ REPORTE SEMANAL")
    print("-" * 70)
    print(agent.generate_weekly_report())

    print("\n4️⃣ EXPORTAR ANALYTICS")
    print("-" * 70)
    analytics = agent.export_pipeline_analytics()
    print(f"✅ Analytics exportado")

    orchestrator.close_database()


if __name__ == "__main__":
    main()
