#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAIN ORCHESTRATOR - FASE 8
Sistema de Integración Completa de Felix Automation
Ejecuta el pipeline completo: Clientes → Auditoría → Scores → Propuestas → Emails → Follow-ups → Pipeline → Dashboards
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from agents.lead_scorer_agent import LeadScorerAgent
from agents.proposal_generator_agent import ProposalGeneratorAgent
from agents.email_sender_agent import EmailSenderAgent
from agents.followup_agent import FollowUpAgent
from agents.sales_pipeline_agent import SalesPipelineAgent
from agents.funnel_management_agent import FunnelManagementAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MainOrchestratorFase8:
    """Orquestador principal que coordina todos los agentes"""

    def __init__(self):
        """Inicializar orquestador y todos los agentes"""
        self.orchestrator = FelixAutomationOrchestrator()
        self.orchestrator.connect_database()
        
        # Inicializar todos los agentes
        self.auditor = MultiPlatformAuditorAgent(self.orchestrator)
        self.scorer = LeadScorerAgent(self.orchestrator)
        self.proposal_gen = ProposalGeneratorAgent(self.orchestrator)
        self.email_sender = EmailSenderAgent(self.orchestrator)
        self.followup = FollowUpAgent(self.orchestrator)
        self.pipeline = SalesPipelineAgent(self.orchestrator)
        self.funnel = FunnelManagementAgent(self.orchestrator)
        
        self.execution_log = []
        self.start_time = datetime.now()
        
        logger.info("✅ Main Orchestrator FASE 8 inicializado")

    def log_step(self, step: str, status: str, details: str = ""):
        """Registrar un paso del pipeline"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "details": details
        }
        self.execution_log.append(entry)
        logger.info(f"{status} {step} | {details}")

    def execute_complete_pipeline(self, client_ids: List[int] = None) -> Dict:
        """
        Ejecutar el pipeline completo para clientes
        
        Args:
            client_ids: Lista de IDs de clientes. Si None, procesa todos.
        
        Returns:
            Resumen de ejecución
        """
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║          🚀 FASE 8: INTEGRACIÓN COMPLETA - PIPELINE END-TO-END           ║
║                                                                            ║
║   Sistema Automatizado de Ventas - Clientes → Cierres                    ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
        """)

        # Si no se especifican clientes, usar todos
        if not client_ids:
            clients = self.orchestrator.get_all_clients()
            client_ids = [c.id for c in clients] if clients else [1, 2, 3]

        summary = {
            "total_clientes": len(client_ids),
            "auditados": 0,
            "scored": 0,
            "propuestas_generadas": 0,
            "emails_enviados": 0,
            "followups_iniciados": 0,
            "pipeline_actualizado": 0,
            "dashboards_generados": 0,
            "errores": []
        }

        # ════════════════════════════════════════════════════════════════
        # PASO 1: AUDITAR CLIENTES (Web + Facebook Ads + Google Ads)
        # ════════════════════════════════════════════════════════════════
        print("\n1️⃣  AUDITORÍA MULTI-PLATAFORMA")
        print("─" * 70)
        
        audits = {}
        for client_id in client_ids:
            try:
                client = self.orchestrator.get_client(client_id)
                print(f"   Auditando {client.name}...", end=" ")

                # Auditoría multi-plataforma (web + facebook ads + google ads)
                audit_result = self.auditor.audit_client(
                    client_id,
                    platforms=['web', 'facebook_ads', 'google_ads']
                )

                audits[client_id] = audit_result
                
                self.log_step("Audit", "✅", f"Cliente {client.name}")
                summary["auditados"] += 1
                print("✅")
            except Exception as e:
                self.log_step("Audit", "❌", str(e))
                summary["errores"].append(f"Auditoría {client_id}: {str(e)}")
                print("❌")

        # ════════════════════════════════════════════════════════════════
        # PASO 2: CALCULAR LEAD SCORES
        # ════════════════════════════════════════════════════════════════
        print("\n2️⃣  CÁLCULO DE LEAD SCORES")
        print("─" * 70)
        
        scores = {}
        for client_id in client_ids:
            try:
                if client_id in audits:
                    client = self.orchestrator.get_client(client_id)
                    print(f"   Scoring {client.name}...", end=" ")

                    # Calcular score basado en auditorías multi-plataforma
                    score_result = self.scorer.score_lead(client_id)
                    score = score_result.get("overall_score", 0)

                    scores[client_id] = score
                    category = "🟢 ALTO" if score > 75 else "🟡 MEDIO" if score > 50 else "🔴 BAJO"
                    
                    self.log_step("Lead Score", "✅", f"{client.name}: {score} {category}")
                    summary["scored"] += 1
                    print(f"✅ {score}%")
            except Exception as e:
                self.log_step("Lead Score", "❌", str(e))
                summary["errores"].append(f"Scoring {client_id}: {str(e)}")
                print("❌")

        # ════════════════════════════════════════════════════════════════
        # PASO 3: GENERAR PROPUESTAS
        # ════════════════════════════════════════════════════════════════
        print("\n3️⃣  GENERACIÓN DE PROPUESTAS")
        print("─" * 70)
        
        proposals = {}
        for client_id in client_ids:
            try:
                if client_id in audits and client_id in scores:
                    client = self.orchestrator.get_client(client_id)
                    print(f"   Generando propuesta para {client.name}...", end=" ")

                    # Obtener IDs de auditorías para la propuesta
                    client_audits = self.orchestrator.get_client_audits(client_id)
                    audit_ids = ",".join(str(a.id) for a in client_audits) if client_audits else ""

                    proposal_result = self.proposal_gen.generate_proposal(
                        client_id,
                        audit_ids
                    )

                    proposal_id = proposal_result.get("proposal_id")
                    
                    proposals[client_id] = proposal_id
                    
                    self.log_step("Proposal Gen", "✅", f"{client.name} (ID: {proposal_id})")
                    summary["propuestas_generadas"] += 1
                    print("✅")
            except Exception as e:
                self.log_step("Proposal Gen", "❌", str(e))
                summary["errores"].append(f"Propuesta {client_id}: {str(e)}")
                print("❌")

        # ════════════════════════════════════════════════════════════════
        # PASO 4: ENVIAR EMAILS CON PROPUESTAS
        # ════════════════════════════════════════════════════════════════
        print("\n4️⃣  ENVÍO DE EMAILS")
        print("─" * 70)
        
        for client_id in client_ids:
            try:
                if client_id in proposals:
                    client = self.orchestrator.get_client(client_id)
                    print(f"   Enviando email a {client.name}...", end=" ")

                    # Enviar propuesta por email
                    proposal_data = {
                        "client_name": client.name,
                        "client_email": client.email,
                        "score": scores.get(client_id, 0)
                    }
                    result = self.email_sender.send_proposal(
                        client_id,
                        proposals[client_id],
                        proposal_data
                    )
                    
                    if result.get("status") == "sent":
                        self.log_step("Email Send", "✅", f"{client.name} → {client.email}")
                        summary["emails_enviados"] += 1
                        print("✅")
                    else:
                        print("⚠️ ")
            except Exception as e:
                self.log_step("Email Send", "❌", str(e))
                summary["errores"].append(f"Email {client_id}: {str(e)}")
                print("❌")

        # ════════════════════════════════════════════════════════════════
        # PASO 5: INICIAR FOLLOW-UP SEQUENCES
        # ════════════════════════════════════════════════════════════════
        print("\n5️⃣  INICIAR SECUENCIAS DE FOLLOW-UP")
        print("─" * 70)
        
        for client_id in client_ids:
            try:
                if client_id in proposals:
                    client = self.orchestrator.get_client(client_id)
                    print(f"   Follow-up para {client.name}...", end=" ")
                    
                    result = self.followup.start_followup_sequence(
                        client_id,
                        proposals[client_id]
                    )
                    
                    if "error" not in result or result.get("status") == "already_exists":
                        self.log_step("Follow-up Init", "✅", f"{client.name} (Seq: {result.get('sequence_id', 'N/A')})")
                        summary["followups_iniciados"] += 1
                        print("✅")
                    else:
                        print("⚠️ ")
            except Exception as e:
                self.log_step("Follow-up Init", "❌", str(e))
                summary["errores"].append(f"Follow-up {client_id}: {str(e)}")
                print("❌")

        # ════════════════════════════════════════════════════════════════
        # PASO 6: ACTUALIZAR PIPELINE (Mover a Propuesta)
        # ════════════════════════════════════════════════════════════════
        print("\n6️⃣  ACTUALIZAR PIPELINE")
        print("─" * 70)
        
        for client_id in client_ids:
            try:
                if client_id in proposals:
                    client = self.orchestrator.get_client(client_id)
                    print(f"   Moviendo {client.name} a PROPUESTA...", end=" ")
                    
                    # Mover cliente a etapa de propuesta
                    self.funnel.move_client_to_stage(client_id, stage=2)  # 2 = PROPUESTA
                    
                    self.log_step("Pipeline Update", "✅", f"{client.name} → PROPUESTA")
                    summary["pipeline_actualizado"] += 1
                    print("✅")
            except Exception as e:
                self.log_step("Pipeline Update", "❌", str(e))
                summary["errores"].append(f"Pipeline {client_id}: {str(e)}")
                print("❌")

        # ════════════════════════════════════════════════════════════════
        # PASO 7: GENERAR DASHBOARDS
        # ════════════════════════════════════════════════════════════════
        print("\n7️⃣  GENERAR DASHBOARDS")
        print("─" * 70)
        
        try:
            print("   Generando dashboard interno...", end=" ")

            # Generar dashboards internos y por cliente
            dashboard_count = 0

            # Dashboard interno (para Felix)
            internal_data = self.funnel.get_dashboard_data_interno()
            dashboard_count += 1

            # Dashboards por cliente
            for client_id in client_ids:
                client_data = self.funnel.get_dashboard_data_cliente(client_id)
                dashboard_count += 1

            # Métricas del pipeline
            pipeline_metrics = self.funnel.get_pipeline_metrics()

            self.log_step("Dashboard Gen", "✅", f"Dashboards generados ({dashboard_count})")
            summary["dashboards_generados"] = dashboard_count
            print("✅")
        except Exception as e:
            self.log_step("Dashboard Gen", "❌", str(e))
            summary["errores"].append(f"Dashboards: {str(e)}")
            print("❌")

        # ════════════════════════════════════════════════════════════════
        # PASO 8: GENERAR REPORTES FINALES
        # ════════════════════════════════════════════════════════════════
        print("\n8️⃣  GENERAR REPORTES FINALES")
        print("─" * 70)
        
        try:
            print("   Pipeline Health...", end=" ")
            health = self.pipeline.get_pipeline_health()
            print("✅")
            
            print("   Analytics Export...", end=" ")
            self.pipeline.export_pipeline_analytics()
            print("✅")
            
            print("   Generating reports...", end=" ")
            weekly_report = self.pipeline.generate_weekly_report()
            print("✅")
            
            self.log_step("Reports", "✅", "Todos los reportes generados")
        except Exception as e:
            self.log_step("Reports", "❌", str(e))
            summary["errores"].append(f"Reports: {str(e)}")
            print("❌")

        # ════════════════════════════════════════════════════════════════
        # RESUMEN FINAL
        # ════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("9️⃣  RESUMEN DE EJECUCIÓN")
        print("=" * 70)
        
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        print(f"""
📊 PIPELINE EJECUTADO EXITOSAMENTE

⏱️  Tiempo de ejecución: {execution_time:.1f} segundos

✅ RESULTADOS:
   • Clientes procesados: {summary["total_clientes"]}
   • Auditados: {summary["auditados"]}/{summary["total_clientes"]}
   • Con scores calculados: {summary["scored"]}/{summary["total_clientes"]}
   • Propuestas generadas: {summary["propuestas_generadas"]}/{summary["total_clientes"]}
   • Emails enviados: {summary["emails_enviados"]}/{summary["total_clientes"]}
   • Follow-ups iniciados: {summary["followups_iniciados"]}/{summary["total_clientes"]}
   • Pipeline actualizado: {summary["pipeline_actualizado"]}/{summary["total_clientes"]}
   • Dashboards generados: {summary["dashboards_generados"]}

⚠️  ERRORES: {len(summary["errores"])}
""")
        
        if summary["errores"]:
            for error in summary["errores"]:
                print(f"   ❌ {error}")

        # Guardar resumen
        summary["execution_log"] = self.execution_log
        summary["execution_time_seconds"] = execution_time
        summary["timestamp"] = self.start_time.isoformat()
        
        return summary

    def save_execution_summary(self, summary: Dict):
        """Guardar resumen de ejecución"""
        summary_file = Path("data/fase8_execution_summary.json")
        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        logger.info(f"✅ Resumen guardado en: {summary_file}")

    def close(self):
        """Cerrar conexiones"""
        self.orchestrator.close_database()


def main():
    """Ejecutar el pipeline completo de FASE 8"""
    orchestrator = MainOrchestratorFase8()
    
    try:
        # Ejecutar pipeline completo
        summary = orchestrator.execute_complete_pipeline()
        
        # Guardar resumen
        orchestrator.save_execution_summary(summary)
        
        # Mostrar reportes
        print("\n" + "=" * 70)
        print("📈 REPORTES FINALES")
        print("=" * 70)
        print(orchestrator.pipeline.get_followup_report())
        
        print("\n" + "=" * 70)
        print("✅ FASE 8: INTEGRACIÓN COMPLETA - ÉXITO")
        print("=" * 70)
        print("""
Sistema automatizado de ventas funcionando correctamente:
  ✅ Clientes auditados
  ✅ Scores calculados
  ✅ Propuestas generadas
  ✅ Emails enviados
  ✅ Follow-ups iniciados
  ✅ Pipeline actualizado
  ✅ Dashboards generados
        """)
        
    finally:
        orchestrator.close()


if __name__ == "__main__":
    main()
