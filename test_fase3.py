#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FASE 3: AGENTES DE GENERACION Y SCORING
Demuestra la integracion completa de:
- Proposal Generator Agent (genera propuestas HTML/PDF)
- Lead Scorer Agent (califica leads por potencial)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator, Audit
from agents.proposal_generator_agent import ProposalGeneratorAgent
from agents.lead_scorer_agent import LeadScorerAgent


def setup_test_data(orchestrator):
    """Crear datos de prueba basados en clientes existentes"""
    print("\n" + "="*70)
    print("CONFIGURANDO DATOS DE PRUEBA")
    print("="*70)

    # Usar clientes existentes
    existing_clients = orchestrator.list_clients()
    client_ids = [c.id for c in existing_clients]

    print("\nOK - {} clientes existentes encontrados".format(len(client_ids)))
    for client in existing_clients:
        print("   . {} (ID: {})".format(client.name, client.id))

    # Crear auditorias para cada cliente si no existen
    audit_data = [
        (1, "web", 79),
        (1, "facebook_ads", 65),
        (1, "google_ads", 72),
        (2, "web", 85),
        (2, "facebook_ads", 78),
        (2, "google_ads", 88),
        (3, "web", 72),
        (3, "facebook_ads", 68),
        (3, "google_ads", 75),
    ]

    print("\nCreando auditorias para clientes...")
    created_count = 0
    for client_id, platform, score in audit_data:
        try:
            audit = Audit(
                client_id=client_id,
                platform=platform,
                audit_type=platform,
                overall_score=score,
                status="completed",
                metrics_json=json.dumps({
                    "score": score,
                    "platform": platform,
                    "timestamp": datetime.now().isoformat()
                })
            )
            audit_id = orchestrator.create_audit(audit)
            print("   OK - Cliente {}, {}: {}/100 (Audit ID: {})".format(
                client_id, platform.upper(), score, audit_id))
            created_count += 1
        except Exception as e:
            print("   ! Cliente {}, {}: {}".format(client_id, platform, str(e)[:50]))

    return client_ids, created_count


def test_proposal_generator(orchestrator):
    """Probar Proposal Generator Agent"""
    print("\n" + "="*70)
    print("TEST 1: PROPOSAL GENERATOR AGENT")
    print("="*70)

    agent = ProposalGeneratorAgent(orchestrator)

    # Generar propuesta para primer cliente
    print("\nGenerando propuesta para: Cliente ID 1")
    try:
        result = agent.generate_proposal(1, "1,2,3")

        print("\nOK - Propuesta Generada:")
        print("   ID: {}".format(result['proposal_id']))
        print("   Cliente: {}".format(result['client_name']))
        print("   Archivo HTML: {}".format(result['html_file']))
        print("   Estado: {}".format(result['status']))

        # Mostrar contenido del HTML
        html_path = Path(result['html_file'])
        if html_path.exists():
            content = html_path.read_text(encoding='utf-8')
            print("   Tamano: {} bytes".format(len(content)))

            # Extraer informacion clave del HTML
            if "Propuesta de Auditoria Digital" in content:
                print("   OK - Titulo de propuesta presente")
            if "Score Sitio Web" in content:
                print("   OK - Scores de auditoria incluidos")

        return result
    except Exception as e:
        print("ERROR: {}".format(str(e)))
        return None


def test_lead_scorer(orchestrator):
    """Probar Lead Scorer Agent"""
    print("\n" + "="*70)
    print("TEST 2: LEAD SCORER AGENT")
    print("="*70)

    agent = LeadScorerAgent(orchestrator)

    print("\nCalificando todos los leads...")
    all_scores = agent.score_all_leads()

    print("\nOK - Scoring Completado:")
    print("   Total de leads: {}".format(len(all_scores)))

    # Mostrar ranking
    print("\nLEADS ORDENADOS POR POTENCIAL:")
    print("-" * 70)
    for i, score in enumerate(all_scores, 1):
        print("\n{}. {}".format(i, score['client_name']))
        print("   Email: {}".format(score['email']))
        print("   Scores: Web={}/100, FB={}/100, Google={}/100".format(
            score['web_score'], score['facebook_score'], score['google_score']))
        print("   Overall: {}/100 {}".format(score['overall_score'], score['ranking']))
        print("   Recomendacion: {}".format(score['recommendation']))

    # Exportar CSV
    csv_file = agent.export_csv()
    print("\nOK - Scores exportados a: {}".format(csv_file))

    # Mostrar reporte
    print(agent.get_scoring_report())

    # Obtener alto potencial
    high_potential = agent.get_high_potential_leads(75)
    print("\nLEADS CON ALTO POTENCIAL (>75):")
    for lead in high_potential:
        print("   OK - {} - Score: {}/100".format(lead['client_name'], lead['overall_score']))

    return all_scores


def test_integration(orchestrator):
    """Probar integracion: Auditoria -> Scoring -> Propuesta"""
    print("\n" + "="*70)
    print("TEST 3: INTEGRACION AUDITORIA -> SCORING -> PROPUESTA")
    print("="*70)

    print("\nFlujo de Datos:")
    print("   1. Cliente obtiene auditorias (Web + Facebook + Google)")
    print("   2. Lead Scorer califica automaticamente")
    print("   3. Si score > 70: Proposal Generator crea propuesta")
    print("   4. Propuesta lista para enviar")

    lead_scorer = LeadScorerAgent(orchestrator)
    proposal_generator = ProposalGeneratorAgent(orchestrator)

    # Obtener leads alto potencial
    all_scores = lead_scorer.score_all_leads()
    high_potential = [s for s in all_scores if s['overall_score'] >= 70]

    print("\nOK - {} leads califican para propuesta:".format(len(high_potential)))

    for lead in high_potential:
        client_id = lead['client_id']
        print("\n   Procesando: {} (Score: {}/100)".format(
            lead['client_name'], lead['overall_score']))

        # Obtener auditorias del cliente
        try:
            audits = orchestrator.get_client_audits(client_id)
            audit_ids = ",".join(str(a.id) for a in audits)

            # Generar propuesta
            result = proposal_generator.generate_proposal(client_id, audit_ids)
            print("      OK - Propuesta generada (ID: {})".format(result['proposal_id']))
            print("      OK - Archivo: {}".format(Path(result['html_file']).name))
        except Exception as e:
            print("      ERROR: {}".format(str(e)[:60]))


def main():
    """Ejecutar tests de FASE 3"""
    print("""
PROPUESTA - FASE 3: AGENTES DE GENERACION Y SCORING

1. Proposal Generator Agent
   -> Convierte auditorias JSON en propuestas HTML/PDF

2. Lead Scorer Agent
   -> Califica leads por potencial (Web 40% + FB 20% + G 20%)

3. Integracion Completa
   -> Auditoria -> Scoring -> Propuesta automatica
    """)

    # Conectar orquestador
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    try:
        # Setup de datos
        client_ids, audit_count = setup_test_data(orchestrator)

        # Test 1: Proposal Generator
        proposal_result = test_proposal_generator(orchestrator)

        # Test 2: Lead Scorer
        scores = test_lead_scorer(orchestrator)

        # Test 3: Integracion
        test_integration(orchestrator)

        # Resumen final
        print("\n" + "="*70)
        print("OK - FASE 3 COMPLETADA EXITOSAMENTE")
        print("="*70)

        high_potential_count = len([s for s in scores if s['overall_score'] >= 70])
        medium_count = len([s for s in scores if 50 <= s['overall_score'] < 70])
        low_count = len([s for s in scores if s['overall_score'] < 50])

        print("""
RESULTADOS:
   Propuestas generadas: 1+
   Leads calificados: {}
   Alto potencial (>=70): {}
   Medio potencial (50-69): {}
   Bajo potencial (<50): {}

ARCHIVOS GENERADOS:
   Propuestas: data/proposals/*.html
   Scores: data/leads_scored.csv
   Logs: data/logs/orchestrator.log

PROXIMAS FASES:
   FASE 4: Email Sender Agent (enviar propuestas)
   FASE 5: Follow-up Agent (seguimiento automatico)
   FASE 6: Sales Pipeline Agent (gestionar embudo)
   FASE 7: Funnel Management Agent (dashboards)
        """.format(len(scores), high_potential_count, medium_count, low_count))

    finally:
        orchestrator.close_database()


if __name__ == "__main__":
    main()
