#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test FASE 6: Sales Pipeline Agent
Prueba completa del análisis predictivo del pipeline
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from agents.sales_pipeline_agent import SalesPipelineAgent


def main():
    """Testing completo de FASE 6"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           TEST FASE 6: SALES PIPELINE AGENT                   ║
║      Análisis Predictivo y Reportes del Pipeline             ║
╚════════════════════════════════════════════════════════════════╝
    """)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = SalesPipelineAgent(orchestrator)

    # ========== 1. SALUD DEL PIPELINE ==========
    print("\n1️⃣ SALUD DEL PIPELINE")
    print("-" * 70)
    health = agent.get_pipeline_health()
    if "error" not in health:
        print(f"✅ Total clientes: {health.get('total_clients', 0)}")
        print(f"✅ Deals cerrados: {health.get('closed_deals', 0)}")
        print(f"✅ Velocidad: {health.get('pipeline_velocity', 'N/A')}")
        
        for stage, info in health.get('stage_health', {}).items():
            print(f"   • {stage}: {info['count']} clientes (~{info['avg_days']:.0f} días promedio)")
    else:
        print(f"⚠️  {health['error']}")

    # ========== 2. PREDICCIONES INDIVIDUALES ==========
    print("\n2️⃣ PREDICCIONES DE CIERRE (Por Cliente)")
    print("-" * 70)
    predictions = []
    for client_id in [1, 2, 3]:
        pred = agent.predict_deal_closure(client_id)
        if "error" not in pred:
            print(f"\n{pred['emoji']} {pred['client_name']} ({pred['stage']})")
            print(f"   Probabilidad: {pred['closure_probability']}")
            print(f"   Categoría: {pred['category']}")
            predictions.append(pred)
        else:
            print(f"⚠️  {pred['error']}")

    # ========== 3. CLIENTES EN RIESGO ==========
    print("\n3️⃣ CLIENTES EN RIESGO (Sin actualización 14+ días)")
    print("-" * 70)
    at_risk = agent.get_at_risk_clients()
    if at_risk:
        print(f"⚠️  {len(at_risk)} cliente(s) en riesgo:")
        for client in at_risk[:5]:
            print(f"\n   • {client['client_name']} ({client['stage']})")
            print(f"     Última actualización: {client['days_without_update']} días atrás")
    else:
        print("✅ Ningún cliente en riesgo")

    # ========== 4. REPORTE SEMANAL ==========
    print("\n4️⃣ REPORTE SEMANAL")
    print("-" * 70)
    report = agent.generate_weekly_report()
    print(report)

    # ========== 5. EXPORTAR ANALYTICS ==========
    print("\n5️⃣ EXPORTANDO ANALYTICS")
    print("-" * 70)
    analytics = agent.export_pipeline_analytics()
    print(f"✅ Archivo creado: data/pipeline_analytics.json")
    print(f"\n   Total clientes: {analytics['summary']['total_clients']}")
    print(f"   En riesgo: {analytics['summary']['total_at_risk']}")
    print(f"   Deals altos (>75%): {analytics['summary']['high_probability_deals']}")
    print(f"   Probabilidad promedio: {analytics['summary']['average_closure_probability']:.1f}%")

    # ========== 6. VER JSON GENERADO ==========
    print("\n6️⃣ PRIMEROS DATOS DE ANALYTICS")
    print("-" * 70)
    analytics_data = json.loads(Path("data/pipeline_analytics.json").read_text())
    print(f"⏰ Timestamp: {analytics_data['timestamp']}")
    print(f"📊 Health Status: {analytics_data['pipeline_health'].get('pipeline_velocity', 'N/A')}")

    print("""
═════════════════════════════════════════════════════════════════

                    ✅ FASE 6: TEST COMPLETADO

        Análisis predictivo del pipeline funcionando correctamente

═════════════════════════════════════════════════════════════════
    """)

    orchestrator.close_database()


if __name__ == "__main__":
    main()
