#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funnel Management Agent
Gestiona el embudo de ventas y genera dashboards
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FunnelManagementAgent:
    """Agente que gestiona el embudo de ventas (4 etapas)"""

    # Las 4 etapas del embudo
    ETAPAS = {
        1: "prospecto",      # Cliente identificado
        2: "propuesta",      # Propuesta enviada
        3: "negociacion",    # Discutiendo términos
        4: "cerrado"         # Contrato firmado o rechazado
    }

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        self.pipeline_file = Path("data/pipeline.json")
        self._ensure_pipeline_file()
        logger.info("✅ Funnel Management Agent inicializado")

    def _ensure_pipeline_file(self):
        """Crear archivo de pipeline si no existe"""
        if not self.pipeline_file.exists():
            self.pipeline_file.write_text(json.dumps({"pipeline": []}, indent=2))

    def get_pipeline_data(self) -> Dict:
        """Obtener datos del pipeline"""
        return json.loads(self.pipeline_file.read_text())

    def move_client_to_stage(self, client_id: int, stage: int) -> Dict:
        """
        Mover cliente a una etapa del embudo

        Args:
            client_id: ID del cliente
            stage: Número de etapa (1-4)
        """
        if stage not in self.ETAPAS:
            logger.error(f"Etapa inválida: {stage}")
            return {"error": "Etapa inválida"}

        client = self.orchestrator.get_client(client_id)
        if not client:
            logger.error(f"Cliente {client_id} no encontrado")
            return {"error": "Cliente no encontrado"}

        pipeline = self.get_pipeline_data()

        # Buscar si el cliente ya existe en el pipeline
        client_in_pipeline = False
        for item in pipeline["pipeline"]:
            if item["client_id"] == client_id:
                item["stage"] = stage
                item["stage_name"] = self.ETAPAS[stage]
                item["updated_at"] = datetime.now().isoformat()
                client_in_pipeline = True
                break

        # Si no existe, crear registro
        if not client_in_pipeline:
            pipeline["pipeline"].append({
                "client_id": client_id,
                "client_name": client.name,
                "email": client.email,
                "stage": stage,
                "stage_name": self.ETAPAS[stage],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "notes": ""
            })

        self.pipeline_file.write_text(json.dumps(pipeline, indent=2, ensure_ascii=False))

        logger.info(f"✅ Cliente {client.name} movido a etapa: {self.ETAPAS[stage].upper()}")

        return {
            "client_id": client_id,
            "client_name": client.name,
            "stage": stage,
            "stage_name": self.ETAPAS[stage]
        }

    def get_clients_by_stage(self, stage: int) -> List[Dict]:
        """Obtener todos los clientes en una etapa específica"""
        pipeline = self.get_pipeline_data()
        return [c for c in pipeline["pipeline"] if c["stage"] == stage]

    def get_pipeline_metrics(self) -> Dict:
        """Calcular métricas del embudo"""
        pipeline = self.get_pipeline_data()
        all_clients = self.orchestrator.list_clients()

        # Contar por etapa
        metrics = {
            "total_clientes": len(all_clients),
            "por_etapa": {},
            "porcentajes": {}
        }

        for stage_num, stage_name in self.ETAPAS.items():
            count = len(self.get_clients_by_stage(stage_num))
            metrics["por_etapa"][stage_name] = count
            percentage = (count / len(all_clients) * 100) if all_clients else 0
            metrics["porcentajes"][stage_name] = round(percentage, 1)

        # Calcular ingresos esperados (basado en leads ALTO potencial)
        lead_scorer = None
        try:
            from agents.lead_scorer_agent import LeadScorerAgent
            lead_scorer = LeadScorerAgent(self.orchestrator)
            high_potential = lead_scorer.get_high_potential_leads(75)

            # Asumir $3,000 por cliente ALTO potencial
            metrics["ingresos_esperados"] = len(high_potential) * 3000
            metrics["leads_alto_potencial"] = len(high_potential)
        except:
            metrics["ingresos_esperados"] = 0
            metrics["leads_alto_potencial"] = 0

        return metrics

    def get_dashboard_data_interno(self) -> Dict:
        """Generar datos para dashboard interno"""
        pipeline = self.get_pipeline_data()
        metrics = self.get_pipeline_metrics()

        # Obtener emails enviados
        email_log_file = Path("data/email_log.json")
        emails_enviados = 0
        if email_log_file.exists():
            try:
                email_log = json.loads(email_log_file.read_text())
                emails_enviados = len(email_log)
            except:
                emails_enviados = 0

        return {
            "timestamp": datetime.now().isoformat(),
            "titulo": "Dashboard Interno - Felix Automation",
            "metricas": {
                "total_clientes": metrics["total_clientes"],
                "emails_enviados": emails_enviados,
                "ingresos_esperados": f"${metrics['ingresos_esperados']:,.0f} USD",
                "leads_alto_potencial": metrics["leads_alto_potencial"]
            },
            "por_etapa": metrics["por_etapa"],
            "porcentajes": metrics["porcentajes"],
            "clients_by_stage": {
                "prospecto": self.get_clients_by_stage(1),
                "propuesta": self.get_clients_by_stage(2),
                "negociacion": self.get_clients_by_stage(3),
                "cerrado": self.get_clients_by_stage(4)
            }
        }

    def get_dashboard_data_cliente(self, client_id: int) -> Dict:
        """Generar datos personalizados para un cliente"""
        client = self.orchestrator.get_client(client_id)
        if not client:
            return {"error": "Cliente no encontrado"}

        # Encontrar posición en pipeline
        pipeline = self.get_pipeline_data()
        client_stage = None
        for item in pipeline["pipeline"]:
            if item["client_id"] == client_id:
                client_stage = item["stage"]
                break

        if not client_stage:
            client_stage = 1  # Por defecto, prospecto

        # Obtener scores del cliente
        audits = self.orchestrator.get_client_audits(client_id)
        scores = {
            "web": 0,
            "facebook_ads": 0,
            "google_ads": 0,
            "total": 0
        }

        for audit in audits:
            if audit.platform == "web":
                scores["web"] = audit.overall_score
            elif audit.platform == "facebook_ads":
                scores["facebook_ads"] = audit.overall_score
            elif audit.platform == "google_ads":
                scores["google_ads"] = audit.overall_score

        if audits:
            scores["total"] = sum([a.overall_score for a in audits]) // len(audits)

        # Calcular oportunidad
        if scores["total"] > 0:
            mejora_estimada = (100 - scores["total"]) * 0.58
            ingresos_mes = (mejora_estimada / 100) * 420  # Asumir $420 base
        else:
            mejora_estimada = 0
            ingresos_mes = 0

        return {
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id,
            "client_name": client.name,
            "client_email": client.email,
            "stage": client_stage,
            "stage_name": self.ETAPAS[client_stage],
            "scores": scores,
            "oportunidad": {
                "mejora_estimada": f"+{int(mejora_estimada)}%",
                "ingresos_mes": f"+${int(ingresos_mes)} USD/mes"
            },
            "timeline": {
                "duracion_proyecto": "2-3 semanas",
                "roi_estimado": "~2 meses",
                "proximo_paso": self._get_next_step(client_stage)
            }
        }

    def _get_next_step(self, stage: int) -> str:
        """Obtener el próximo paso según la etapa"""
        pasos = {
            1: "Enviar propuesta personalizada",
            2: "Seguimiento y negociación",
            3: "Finalizar contrato",
            4: "Implementación o archivo"
        }
        return pasos.get(stage, "N/A")

    def get_funnel_report(self) -> str:
        """Generar reporte visual del embudo"""
        metrics = self.get_pipeline_metrics()

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         REPORTE DEL EMBUDO DE VENTAS                        ║
╚═══════════════════════════════════════════════════════════════╝

📊 MÉTRICAS GENERALES:
   • Total de clientes: {metrics['total_clientes']}
   • Ingresos esperados: ${metrics['ingresos_esperados']:,.0f} USD
   • Leads ALTO potencial: {metrics['leads_alto_potencial']}

📈 DISTRIBUCIÓN POR ETAPA:

   PROSPECTO (Clientes identificados)
   [{self._get_bar(metrics['por_etapa']['prospecto'], metrics['total_clientes'])}] {metrics['por_etapa']['prospecto']} clientes ({metrics['porcentajes']['prospecto']}%)

   PROPUESTA (Propuesta enviada)
   [{self._get_bar(metrics['por_etapa']['propuesta'], metrics['total_clientes'])}] {metrics['por_etapa']['propuesta']} clientes ({metrics['porcentajes']['propuesta']}%)

   NEGOCIACIÓN (En conversación)
   [{self._get_bar(metrics['por_etapa']['negociacion'], metrics['total_clientes'])}] {metrics['por_etapa']['negociacion']} clientes ({metrics['porcentajes']['negociacion']}%)

   CERRADO (Contratado o rechazado)
   [{self._get_bar(metrics['por_etapa']['cerrado'], metrics['total_clientes'])}] {metrics['por_etapa']['cerrado']} clientes ({metrics['porcentajes']['cerrado']}%)

═════════════════════════════════════════════════════════════════
"""
        return report

    @staticmethod
    def _get_bar(value: int, total: int) -> str:
        """Crear barra visual"""
        if total == 0:
            return "░" * 10
        percentage = value / total
        filled = int(percentage * 10)
        return "█" * filled + "░" * (10 - filled)


def main():
    """Testing del agente"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║       FUNNEL MANAGEMENT AGENT - FASE 7                       ║
║    Gestiona embudo de ventas y genera dashboards            ║
╚════════════════════════════════════════════════════════════════╝
    """)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = FunnelManagementAgent(orchestrator)

    # Mover clientes a diferentes etapas
    print("\n1️⃣ MOVIENDO CLIENTES A ETAPAS")
    print("-" * 70)

    agent.move_client_to_stage(1, 2)  # Raíces → Propuesta
    agent.move_client_to_stage(2, 1)  # TechShop → Prospecto
    agent.move_client_to_stage(3, 3)  # ConsultorLabs → Negociación

    # Mostrar reporte
    print(agent.get_funnel_report())

    # Datos del dashboard interno
    print("\n2️⃣ DATOS DASHBOARD INTERNO")
    print("-" * 70)
    internal = agent.get_dashboard_data_interno()
    print(json.dumps(internal["metricas"], indent=2, ensure_ascii=False))

    # Datos del dashboard cliente
    print("\n3️⃣ DATOS DASHBOARD CLIENTE (Raíces de Cauquenes)")
    print("-" * 70)
    client_dashboard = agent.get_dashboard_data_cliente(1)
    print(json.dumps(client_dashboard, indent=2, ensure_ascii=False))

    orchestrator.close_database()


if __name__ == "__main__":
    main()
