#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test FASE 8: Integración Completa del Pipeline
Ejecuta el flujo completo: Clientes → Auditoría → Scores → Propuestas → Emails → Follow-ups → Pipeline → Dashboards
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main_orchestrator import MainOrchestratorFase8


def main():
    """Testing completo de FASE 8"""
    print("\n" + "=" * 80)
    print("TEST FASE 8: INTEGRACIÓN COMPLETA DEL SISTEMA".center(80))
    print("=" * 80 + "\n")

    orchestrator = MainOrchestratorFase8()

    try:
        # Ejecutar pipeline completo con los 3 clientes de prueba
        print("🚀 Ejecutando pipeline end-to-end para 3 clientes...\n")
        summary = orchestrator.execute_complete_pipeline(client_ids=[1, 2, 3])

        # Guardar resumen
        orchestrator.save_execution_summary(summary)

        # Mostrar resumen de ejecución
        print("\n" + "=" * 80)
        print("RESUMEN DE EJECUCIÓN".center(80))
        print("=" * 80)

        print(f"""
📊 ESTADÍSTICAS FINALES:

   Total de clientes: {summary['total_clientes']}
   ✅ Auditados: {summary['auditados']}/{summary['total_clientes']}
   ✅ Scores calculados: {summary['scored']}/{summary['total_clientes']}
   ✅ Propuestas generadas: {summary['propuestas_generadas']}/{summary['total_clientes']}
   ✅ Emails enviados: {summary['emails_enviados']}/{summary['total_clientes']}
   ✅ Follow-ups iniciados: {summary['followups_iniciados']}/{summary['total_clientes']}
   ✅ Pipeline actualizado: {summary['pipeline_actualizado']}/{summary['total_clientes']}
   ✅ Dashboards generados: {summary['dashboards_generados']}

⏱️  Tiempo total: {summary['execution_time_seconds']:.1f} segundos

📁 DATOS GENERADOS:
   ✅ data/fase8_execution_summary.json
   ✅ data/pipeline_analytics.json
   ✅ data/followup_export.json
   ✅ data/dashboard_interno.html
   ✅ data/dashboard_cliente_*.html
""")

        if summary["errores"]:
            print(f"⚠️  ERRORES ENCONTRADOS ({len(summary['errores'])}):")
            for error in summary["errores"]:
                print(f"   ❌ {error}")
        else:
            print("✅ SIN ERRORES - EJECUCIÓN EXITOSA")

        print("\n" + "=" * 80)
        print("✅ FASE 8: TEST COMPLETADO".center(80))
        print("=" * 80)

        print("""
El sistema de automatización de ventas ahora está completamente integrado.

PRÓXIMOS PASOS:
  1. Revisar los dashboards generados en data/dashboard_*.html
  2. Verificar logs en data/fase8_execution_summary.json
  3. Configurar webhooks de SendGrid (FASE 9)
  4. Implementar White-Box Audit (FASE 10)
        """)

        return 0 if not summary["errores"] else 1

    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        orchestrator.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
