#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed datos iniciales en BD
"""

import sys
import json
from pathlib import Path

# Agregar path
sys.path.insert(0, str(Path(__file__).parent.parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator, Client, Audit, Proposal
from agents.lead_scorer_agent import LeadScorerAgent

def seed_clients():
    """Agregar clientes de ejemplo"""
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    print("🌱 Seeding datos iniciales...")

    # Clientes de ejemplo
    clients_data = [
        {
            "name": "Raíces de Cauquenes",
            "email": "info@raices.cl",
            "business_type": "plants",
            "company_size": "pyme",
            "sector": "retail"
        },
        {
            "name": "TechShop Premium",
            "email": "admin@techshop.cl",
            "business_type": "ecommerce",
            "company_size": "pyme",
            "sector": "technology"
        },
        {
            "name": "ConsultorLabs",
            "email": "hello@consultorlabs.cl",
            "business_type": "services",
            "company_size": "startup",
            "sector": "consulting"
        }
    ]

    # Insertar clientes
    client_ids = []
    for client_data in clients_data:
        client = Client(**client_data)
        try:
            client_id = orchestrator.add_client(client)
            client_ids.append(client_id)
            print(f"  ✓ Cliente: {client.name}")
        except Exception as e:
            print(f"  ⚠️ Cliente {client.name} ya existe: {str(e)}")

    # Crear auditorías de ejemplo
    print("\n🔍 Creando auditorías...")
    for client_id in client_ids:
        # Web audit
        audit = Audit(
            client_id=client_id,
            audit_type="web",
            platform="web",
            status="completed",
            overall_score=72,
            metrics_json=json.dumps({
                "performance": 85,
                "security": 90,
                "tracking": 40,
                "technology": 75
            })
        )
        audit_id = orchestrator.create_audit(audit)
        orchestrator.update_audit_score(audit_id, 72, audit.metrics_json)

        # Facebook Ads audit
        audit = Audit(
            client_id=client_id,
            audit_type="ads",
            platform="facebook_ads",
            status="completed",
            overall_score=97,
            metrics_json=json.dumps({
                "estructura": 95,
                "contenido": 98,
                "targeting": 96,
                "tracking": 99
            })
        )
        audit_id = orchestrator.create_audit(audit)
        orchestrator.update_audit_score(audit_id, 97, audit.metrics_json)

        # Google Ads audit
        audit = Audit(
            client_id=client_id,
            audit_type="ads",
            platform="google_ads",
            status="completed",
            overall_score=88,
            metrics_json=json.dumps({
                "keywords": 85,
                "quality_score": 90,
                "estructura": 85,
                "tracking": 92
            })
        )
        audit_id = orchestrator.create_audit(audit)
        orchestrator.update_audit_score(audit_id, 88, audit.metrics_json)

        print(f"  ✓ Auditorías para cliente {client_id}")

    # Hacer scoring de leads
    print("\n⭐ Scoring de leads...")
    scorer = LeadScorerAgent(orchestrator)
    scored = scorer.score_all_clients()
    print(f"  ✓ {scored} leads scored")

    # Pipeline inicial
    print("\n📈 Inicializando pipeline...")
    for client_id in client_ids:
        orchestrator.move_to_pipeline_stage(
            client_id,
            "prospecto",
            notes="Lead inicial - Demo"
        )
    print(f"  ✓ Pipeline inicializado para {len(client_ids)} clientes")

    # Estadísticas finales
    print("\n📊 ESTADO FINAL")
    status = orchestrator.get_system_status()
    print(f"  • Total clientes: {status['total_clients']}")
    print(f"  • Pipeline: {status['pipeline_stats']}")
    print(f"  • High potential leads: {status['high_potential_leads']}")

    orchestrator.close_database()
    print("\n✅ Seeding completado\n")

if __name__ == "__main__":
    seed_clients()
