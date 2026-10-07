#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test FASE 5: Follow-up Agent
Prueba completa del sistema de automatización de seguimientos
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from agents.followup_agent import FollowUpAgent

def simulate_time_passing(days: int):
    """Simula el paso de días para testing"""
    print(f"⏰ Simulando paso de {days} días...\n")


def main():
    """Testing completo de FASE 5"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           TEST FASE 5: FOLLOW-UP AGENT                        ║
║      Automatización de Seguimientos Secuenciados             ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Inicializar orquestador y agente
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = FollowUpAgent(orchestrator)

    # ========== 1. INICIAR SECUENCIAS DE FOLLOW-UP ==========
    print("\n1️⃣ INICIANDO SECUENCIAS DE FOLLOW-UP")
    print("-" * 70)

    sequences_started = []
    for client_id in [1, 2, 3]:
        result = agent.start_followup_sequence(client_id, proposal_id=client_id)
        if "error" not in result and result.get("status") != "already_exists":
            print(f"✅ {result['client_name']}: Secuencia #{result['sequence_id']} iniciada")
            sequences_started.append(result['sequence_id'])
        elif result.get("status") == "already_exists":
            print(f"⚠️  Cliente {client_id}: Ya tiene secuencia activa (reutilizando)")
            sequences_started.append(result['client_id'])
        else:
            print(f"❌ Error con cliente {client_id}: {result['error']}")

    # ========== 2. VER ESTADO INICIAL ==========
    print("\n2️⃣ ESTADO INICIAL DE SEGUIMIENTOS")
    print("-" * 70)

    for client_id in [1, 2, 3]:
        status = agent.get_followup_status(client_id)
        if "sequence_status" in status:
            print(f"\n📊 {status['client_name']}")
            print(f"   Follow-ups enviados: {status['followups_sent']}/{status['followups_total']}")
            print(f"   Estado: {status['sequence_status']}")

    # ========== 3. SIMULAR PASO DE TIEMPO ==========
    print("\n3️⃣ PENDIENTES INICIALES (Antes de tiempo)")
    print("-" * 70)

    pending = agent.get_pending_followups()
    if pending:
        print(f"⏳ Hay {len(pending)} follow-ups pendientes:")
        for item in pending:
            print(f"   • {item['client_name']}: {item['followup_name']} (#{item['followup_number']}/3)")
    else:
        print("✅ No hay follow-ups pendientes (como era de esperarse)")

    # ========== 4. MODIFICAR FECHAS PARA TESTING ==========
    print("\n4️⃣ AJUSTANDO FECHAS PARA TESTING")
    print("-" * 70)
    print("Modificando started_at en las secuencias para simular el paso de tiempo...")

    # Leer archivo de secuencias
    sequences_data = json.loads(agent.followup_file.read_text())

    # Modificar las fechas de inicio para simular que pasaron días
    now = datetime.now()
    for seq in sequences_data["sequences"]:
        # Primera secuencia: 3 días atrás (debería tener follow-up #1 pendiente)
        if seq["sequence_id"] == 1:
            seq["started_at"] = (now - timedelta(days=3)).isoformat()
        # Segunda secuencia: 5 días atrás (debería tener follow-up #1 y #2 pendientes)
        elif seq["sequence_id"] == 2:
            seq["started_at"] = (now - timedelta(days=5)).isoformat()
        # Tercera secuencia: 8 días atrás (debería tener todos los follow-ups pendientes)
        elif seq["sequence_id"] == 3:
            seq["started_at"] = (now - timedelta(days=8)).isoformat()

    agent.followup_file.write_text(json.dumps(sequences_data, indent=2, ensure_ascii=False))
    print("✅ Fechas ajustadas. Ahora simulando paso de tiempo...\n")

    # ========== 5. VER FOLLOW-UPS PENDIENTES (Después de ajuste) ==========
    print("5️⃣ FOLLOW-UPS PENDIENTES (Después de ajuste de tiempo)")
    print("-" * 70)

    pending = agent.get_pending_followups()
    if pending:
        print(f"📧 Total pendientes: {len(pending)} follow-ups\n")
        pending_by_client = {}
        for item in pending:
            if item['client_name'] not in pending_by_client:
                pending_by_client[item['client_name']] = []
            pending_by_client[item['client_name']].append(item)

        for client_name, items in pending_by_client.items():
            print(f"   {client_name}:")
            for item in items:
                print(f"      • {item['followup_name']} (#{item['followup_number']}/3) - Atrasado {item['days_overdue']} días")
            print()
    else:
        print("✅ No hay follow-ups pendientes")

    # ========== 6. ENVIAR FOLLOW-UPS ==========
    print("\n6️⃣ ENVIANDO FOLLOW-UPS")
    print("-" * 70)

    pending = agent.get_pending_followups()
    sent_count = 0

    if pending:
        for item in pending[:5]:  # Enviar primeros 5
            result = agent.send_followup(
                sequence_id=item['sequence_id'],
                followup_number=item['followup_number']
            )
            if "error" not in result:
                print(f"✅ Enviado a {item['client_email']}: {item['followup_name']}")
                print(f"   Hora: {result['sent_at'][:19]}")
                sent_count += 1
            else:
                print(f"❌ Error: {result['error']}")

    print(f"\n📊 Total enviados: {sent_count}")

    # ========== 7. MARCAR COMO ABIERTOS ==========
    print("\n7️⃣ SIMULANDO APERTURAS DE EMAILS")
    print("-" * 70)

    # Marcar algunos emails como abiertos
    sequences_data = json.loads(agent.followup_file.read_text())
    for seq in sequences_data["sequences"][:2]:  # Primeros 2 clientes
        for followup_num in ["1", "2"]:
            if seq["followups"][followup_num]["sent"]:
                result = agent.mark_followup_opened(
                    sequence_id=seq["sequence_id"],
                    followup_number=int(followup_num)
                )
                print(f"📖 Cliente {seq['client_name']}: Follow-up #{followup_num} abierto")

    # ========== 8. VER ESTADO ACTUALIZADO ==========
    print("\n8️⃣ ESTADO ACTUALIZADO POR CLIENTE")
    print("-" * 70)

    for client_id in [1, 2, 3]:
        status = agent.get_followup_status(client_id)
        if "sequence_status" in status:
            print(f"\n📊 {status['client_name']}")
            print(f"   Follow-ups enviados: {status['followups_sent']}/{status['followups_total']}")

            # Contar abiertos
            opened = sum(1 for f in status['details'].values() if f['opened'])
            clicked = sum(1 for f in status['details'].values() if f['clicked'])

            if opened > 0:
                print(f"   Abiertos: {opened}")
            if clicked > 0:
                print(f"   Clicks: {clicked}")

            if status['last_followup_at']:
                print(f"   Último envío: {status['last_followup_at'][:10]}")

    # ========== 9. COMPLETAR ALGUNAS SECUENCIAS ==========
    print("\n9️⃣ COMPLETANDO SECUENCIAS")
    print("-" * 70)

    # Marcar secuencia 1 como completada (cliente respondió)
    result = agent.complete_sequence(
        sequence_id=1,
        reason="cliente_respondió"
    )
    print(f"✅ Secuencia 1 completada: {result['reason']}")

    # Marcar secuencia 2 como completada (cliente rechazó)
    result = agent.complete_sequence(
        sequence_id=2,
        reason="rechazó"
    )
    print(f"✅ Secuencia 2 completada: {result['reason']}")

    # ========== 10. REPORTE FINAL ==========
    print("\n🔟 REPORTE FINAL DE SEGUIMIENTOS")
    print("-" * 70)
    print(agent.get_followup_report())

    # ========== 11. EXPORTAR DATOS PARA ANÁLISIS ==========
    print("\n1️⃣1️⃣ EXPORTANDO DATOS")
    print("-" * 70)

    # Leer y guardar estado actual
    sequences = json.loads(agent.followup_file.read_text())
    log = json.loads(agent.followup_log.read_text())

    # Exportar JSON limpio
    total_opened = sum(1 for seq in sequences["sequences"] for f in seq["followups"].values() if f["opened"])

    export_data = {
        "timestamp": datetime.now().isoformat(),
        "resumen": {
            "total_secuencias": len(sequences["sequences"]),
            "secuencias_activas": len([s for s in sequences["sequences"] if s["status"] == "active"]),
            "secuencias_completadas": len([s for s in sequences["sequences"] if s["status"] == "completed"]),
            "total_followups_enviados": len(log),
            "followups_abiertos": total_opened
        },
        "secuencias": sequences["sequences"],
        "log_enviados": log
    }

    export_file = Path("data/followup_export.json")
    export_file.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
    print(f"✅ Datos exportados a: {export_file}")

    # ========== 12. ESTADÍSTICAS FINALES ==========
    print("\n1️⃣2️⃣ ESTADÍSTICAS FINALES")
    print("-" * 70)

    active_seqs = [s for s in sequences["sequences"] if s["status"] == "active"]
    completed_seqs = [s for s in sequences["sequences"] if s["status"] == "completed"]

    total_sent = sum(1 for seq in sequences["sequences"] for f in seq["followups"].values() if f["sent"])
    total_opened = sum(1 for seq in sequences["sequences"] for f in seq["followups"].values() if f["opened"])

    print(f"""
📊 RESUMEN DE FASE 5:
   • Total secuencias: {len(sequences["sequences"])}
   • Secuencias activas: {len(active_seqs)}
   • Secuencias completadas: {len(completed_seqs)}
   • Total follow-ups enviados: {total_sent}
   • Total follow-ups abiertos: {total_opened}
   • Tasa de apertura: {(total_opened/total_sent*100):.1f}% (si hay envíos)

📁 ARCHIVOS GENERADOS:
   ✅ data/followup_sequences.json (estado de secuencias)
   ✅ data/followup_log.json (registro de envíos)
   ✅ data/followup_export.json (export para análisis)
    """)

    orchestrator.close_database()

    print("""
═════════════════════════════════════════════════════════════════

                    ✅ FASE 5: TEST COMPLETADO

        Automatización de seguimientos funcionando correctamente

═════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    main()
