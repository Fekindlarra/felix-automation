#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO COMPLETA: FASES 1-3
Orquestador Base + Auditorías Multi-Plataforma + Generación de Propuestas + Lead Scoring
"""

import sys
import json
from pathlib import Path

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from agents.proposal_generator_agent import ProposalGeneratorAgent
from agents.lead_scorer_agent import LeadScorerAgent


def print_banner(title):
    """Imprimir banner formateado"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def main():
    """Ejecutar demo completa"""

    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         FELIX AUTOMATION - OPCIÓN C                             ║
║    Sistema Automatizado de Ventas (FASES 1-3 DEMO)             ║
║                                                                  ║
║  1️⃣  Orquestador Base (Infraestructura)                        ║
║  2️⃣  Auditorías Multi-Plataforma (Web + Facebook + Google)    ║
║  3️⃣  Generación de Propuestas + Lead Scoring                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # ====== FASE 1: ORQUESTADOR BASE ======
    print_banner("FASE 1: ORQUESTADOR BASE - INICIALIZANDO")

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    print("✅ Base de datos conectada")
    print("✅ Orquestador inicializado")
    print("✅ Configuración cargada")

    # Mostrar clientes
    clients = orchestrator.list_clients()
    print(f"\n📋 Clientes en el sistema: {len(clients)}")
    for client in clients:
        print(f"   • {client.name} ({client.business_type})")

    # ====== FASE 2: AUDITORÍAS MULTI-PLATAFORMA ======
    print_banner("FASE 2: AUDITORÍAS MULTI-PLATAFORMA")

    auditor = MultiPlatformAuditorAgent(orchestrator)

    print("🔍 Auditando cada cliente en 3 plataformas...")
    print("   • Web (Performance, Security, Tracking, Technology)")
    print("   • Facebook Ads (Estructura, Contenido, Targeting, Tracking)")
    print("   • Google Ads (Estructura, Keywords, Quality Score, Tracking)\n")

    # Auditar cada cliente
    audit_results = {}
    for client in clients:
        print(f"⏳ Auditando: {client.name}...", end="")
        result = auditor.audit_client(client.id)
        audit_results[client.id] = result
        print(" ✅")

    print(f"\n✅ {len(audit_results)} clientes auditados en 3 plataformas")

    # Mostrar resumen de auditorías
    print("\n📊 RESUMEN DE AUDITORÍAS:")
    for client_id, results in audit_results.items():
        client = orchestrator.get_client(client_id)
        print(f"\n   {client.name}:")
        for platform, data in results.items():
            if 'overall_score' in data:
                score = data['overall_score']
                print(f"      • {platform.upper()}: {score}/100", end="")
                if score >= 75:
                    print(" 🟢 Bueno")
                elif score >= 50:
                    print(" 🟡 Aceptable")
                else:
                    print(" 🔴 Necesita mejora")

    # ====== FASE 3: GENERACIÓN DE PROPUESTAS ======
    print_banner("FASE 3A: GENERACIÓN DE PROPUESTAS")

    proposal_gen = ProposalGeneratorAgent(orchestrator)

    print("📝 Generando propuestas personalizadas...\n")

    proposals = {}
    for client in clients:
        print(f"⏳ Generando propuesta para: {client.name}...", end="")
        result = proposal_gen.generate_proposal(client.id, "1,2,3")
        proposals[client.id] = result
        print(" ✅")

    print(f"\n✅ {len(proposals)} propuestas generadas")

    print("\n📄 ARCHIVOS GENERADOS:")
    for client_id, proposal in proposals.items():
        client = orchestrator.get_client(client_id)
        print(f"\n   {client.name}:")
        print(f"      • HTML: {proposal['html_file']}")
        print(f"      • PDF: {proposal['pdf_file']}")

    # ====== FASE 3: LEAD SCORING ======
    print_banner("FASE 3B: LEAD SCORING (Calificación de Leads)")

    scorer = LeadScorerAgent(orchestrator)

    print("🎯 Calificando leads basado en auditorías...\n")
    scores = scorer.score_all_leads()

    print(scorer.get_scoring_report())

    # Exportar CSV
    csv_file = scorer.export_csv()
    print(f"\n💾 Scores exportados a: {csv_file}")

    # ====== ESTADÍSTICAS FINALES ======
    print_banner("RESUMEN FINAL - ESTADO DEL SISTEMA")

    status = orchestrator.get_system_status()

    print(f"""
📊 MÉTRICAS GENERALES:
   • Total de clientes: {status['total_clients']}
   • Timestamp: {status['timestamp']}

📈 PIPELINE DE VENTAS:
   • Prospectos: {status['pipeline_stats'].get('prospecto', 0)}
   • Con Propuesta: {status['pipeline_stats'].get('propuesta', 0)}
   • En Negociación: {status['pipeline_stats'].get('negociacion', 0)}
   • Cerrados: {status['pipeline_stats'].get('cerrado', 0)}

🎯 LEADS POR POTENCIAL:
   • Alto potencial (>=80): {len(scorer.get_high_potential_leads(80))}
   • Medio potencial (60-79): {len([s for s in scores if 60 <= s['overall_score'] < 80])}
   • Bajo potencial (<60): {len([s for s in scores if s['overall_score'] < 60])}

📧 EMAILS:
   • Enviados: {status['email_stats'].get('proposal', {}).get('count', 0) if 'proposal' in status['email_stats'] else 0}
""")

    # Resumen por tipo de negocio
    print("\n🏢 CLIENTES POR TIPO DE NEGOCIO:")
    business_types = {}
    for client in clients:
        bt = client.business_type
        business_types[bt] = business_types.get(bt, 0) + 1

    for bt, count in business_types.items():
        print(f"   • {bt}: {count} cliente(s)")

    # ====== PRÓXIMOS PASOS ======
    print_banner("PRÓXIMOS PASOS - FASES 4-7")

    print("""
✅ COMPLETADO:
   ✓ FASE 1: Orquestador Base (Infraestructura SQLite)
   ✓ FASE 2: Auditorías Multi-Plataforma (Web + FB + Google)
   ✓ FASE 3: Propuestas + Lead Scoring

⏭️  PRÓXIMO (FASES 4-7):
   • FASE 4: Email Sender Agent (SendGrid integration)
   • FASE 5: Follow-up Agent + Funnel Dashboards
   • FASE 6: White-Box Audit (Shopify, Jumpseller, Custom Code)
   • FASE 7: Integration & Testing

📈 PIPELINE LISTO PARA:
   1. Envío automático de propuestas (Email Sender - FASE 4)
   2. Follow-ups automáticos (Follow-up Agent - FASE 5)
   3. Gestión visual del embudo (Dashboards - FASE 5)
   4. Auditorías profundas con credenciales (White-Box - FASE 6)
    """)

    # Cerrar
    orchestrator.close_database()

    print_banner("✅ DEMO COMPLETADA EXITOSAMENTE")

    print("""
📁 ESTRUCTURA CREADA:
   /felix-automation/
   ├── orchestrator.py ...................... 🎯 Cerebro central
   ├── init_database.py ..................... 🗄️  Base de datos
   ├── config.yaml .......................... ⚙️  Configuración
   │
   ├── agents/ .............................. 🤖 Agentes automatizados
   │   ├── multi_platform_auditor_agent.py .. ✅ FASE 2
   │   ├── proposal_generator_agent.py ...... ✅ FASE 3
   │   ├── lead_scorer_agent.py ............. ✅ FASE 3
   │   ├── email_sender_agent.py ............ 🔜 FASE 4
   │   ├── followup_agent.py ................ 🔜 FASE 5
   │   ├── sales_pipeline_agent.py .......... 🔜 FASE 4
   │   └── funnel_management_agent.py ....... 🔜 FASE 5
   │
   ├── auditors/ ............................ 🔍 Módulos de auditoría
   │   ├── facebook_ads_auditor.py .......... ✅
   │   └── google_ads_auditor.py ............ ✅
   │
   ├── whitebox/ ............................ 🔐 (FASE 6)
   │   ├── shopify_auditor.py ............... 🔜
   │   ├── jumpseller_auditor.py ............ 🔜
   │   ├── code_auditor.py .................. 🔜
   │   └── credentials_manager.py ........... 🔜
   │
   ├── dashboards/ .......................... 📊 (FASE 5)
   │   ├── internal_dashboard.html .......... 🔜
   │   └── client_dashboard.html ............ 🔜
   │
   └── data/ ............................... 📁 Datos generados
       ├── audits/ .......................... ✅ Auditorías JSON
       ├── proposals/ ....................... ✅ Propuestas HTML/PDF
       ├── pipeline/ ........................ 📋 Estados del embudo
       └── logs/ ............................ 📝 Registros del sistema

🚀 PARA CONTINUAR MAÑANA:
   python3 agents/email_sender_agent.py     (FASE 4 - Envío de emails)

📊 ARCHIVOS CLAVE GENERADOS:
   • felix_automation.db ................... Base de datos SQLite
   • data/leads_scored.csv ................ Leads calificados
   • data/proposals/*.html ................ Propuestas
   • data/proposals/*.pdf ................. PDFs de propuestas
    """)


if __name__ == "__main__":
    main()
