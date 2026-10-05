#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Follow-up Agent
Automatiza secuencias de seguimiento por email
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FollowUpAgent:
    """Agente que automatiza secuencias de seguimiento"""

    # Configuración de secuencias de follow-up
    FOLLOWUP_SCHEDULE = {
        1: {"days": 2, "name": "Primer Follow-up", "type": "check_in"},
        2: {"days": 4, "name": "Segundo Follow-up", "type": "data_share"},
        3: {"days": 7, "name": "Tercer Follow-up", "type": "last_touch"}
    }

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        self.followup_file = Path("data/followup_sequences.json")
        self.followup_log = Path("data/followup_log.json")
        self._ensure_files()
        logger.info("✅ Follow-up Agent inicializado")

    def _ensure_files(self):
        """Crear archivos si no existen"""
        if not self.followup_file.exists():
            self.followup_file.write_text(json.dumps({"sequences": []}, indent=2))
        if not self.followup_log.exists():
            self.followup_log.write_text(json.dumps([], indent=2))

    def start_followup_sequence(self, client_id: int, proposal_id: int = None) -> Dict:
        """
        Iniciar una secuencia de follow-ups para un cliente

        Args:
            client_id: ID del cliente
            proposal_id: ID de la propuesta (opcional)

        Returns:
            Estado de la secuencia iniciada
        """
        client = self.orchestrator.get_client(client_id)
        if not client:
            logger.error(f"❌ Cliente {client_id} no encontrado")
            return {"error": "Cliente no encontrado"}

        sequences = json.loads(self.followup_file.read_text())

        # Verificar si ya existe una secuencia activa
        for seq in sequences["sequences"]:
            if seq["client_id"] == client_id and seq["status"] == "active":
                logger.info(f"⚠️  Ya existe una secuencia activa para {client.name}")
                return {"status": "already_exists", "client_id": client_id}

        # Crear nueva secuencia
        new_sequence = {
            "sequence_id": len(sequences["sequences"]) + 1,
            "client_id": client_id,
            "client_name": client.name,
            "client_email": client.email,
            "proposal_id": proposal_id,
            "status": "active",  # active, paused, completed, cancelled
            "started_at": datetime.now().isoformat(),
            "last_followup_at": None,
            "followups": {
                "1": {"sent": False, "sent_at": None, "opened": False, "clicked": False},
                "2": {"sent": False, "sent_at": None, "opened": False, "clicked": False},
                "3": {"sent": False, "sent_at": None, "opened": False, "clicked": False}
            },
            "notes": ""
        }

        sequences["sequences"].append(new_sequence)
        self.followup_file.write_text(json.dumps(sequences, indent=2, ensure_ascii=False))

        logger.info(f"✅ Secuencia de follow-up iniciada para {client.name}")

        return {
            "sequence_id": new_sequence["sequence_id"],
            "client_id": client_id,
            "client_name": client.name,
            "status": "active",
            "next_followup": f"En {self.FOLLOWUP_SCHEDULE[1]['days']} días"
        }

    def get_pending_followups(self) -> List[Dict]:
        """Obtener follow-ups pendientes de enviar"""
        sequences = json.loads(self.followup_file.read_text())
        pending = []

        for seq in sequences["sequences"]:
            if seq["status"] != "active":
                continue

            started = datetime.fromisoformat(seq["started_at"])
            now = datetime.now()

            # Revisar cada follow-up
            for followup_num in [1, 2, 3]:
                followup_data = seq["followups"][str(followup_num)]

                if followup_data["sent"]:
                    continue  # Ya se envió

                schedule = self.FOLLOWUP_SCHEDULE[followup_num]
                send_at = started + timedelta(days=schedule["days"])

                # ¿Es hora de enviar este follow-up?
                if now >= send_at:
                    pending.append({
                        "sequence_id": seq["sequence_id"],
                        "client_id": seq["client_id"],
                        "client_name": seq["client_name"],
                        "client_email": seq["client_email"],
                        "followup_number": followup_num,
                        "followup_name": schedule["name"],
                        "followup_type": schedule["type"],
                        "days_overdue": (now - send_at).days
                    })

        return pending

    def send_followup(self, sequence_id: int, followup_number: int) -> Dict:
        """
        Enviar un follow-up específico

        Args:
            sequence_id: ID de la secuencia
            followup_number: Número del follow-up (1, 2 o 3)

        Returns:
            Estado del envío
        """
        sequences = json.loads(self.followup_file.read_text())
        sequence = None

        # Encontrar la secuencia
        for seq in sequences["sequences"]:
            if seq["sequence_id"] == sequence_id:
                sequence = seq
                break

        if not sequence:
            return {"error": "Secuencia no encontrada"}

        if sequence["status"] != "active":
            return {"error": f"Secuencia no está activa (estado: {sequence['status']})"}

        # Generar contenido del email
        email_content = self._generate_followup_email(
            sequence["client_name"],
            followup_number,
            self.FOLLOWUP_SCHEDULE[followup_number]["type"]
        )

        # Simular envío (en producción: usar SendGrid)
        logger.info(f"📧 Enviando follow-up #{followup_number} a {sequence['client_email']}")

        # Registrar envío
        sequence["followups"][str(followup_number)]["sent"] = True
        sequence["followups"][str(followup_number)]["sent_at"] = datetime.now().isoformat()
        sequence["last_followup_at"] = datetime.now().isoformat()

        # Guardar cambios
        self.followup_file.write_text(json.dumps(sequences, indent=2, ensure_ascii=False))

        # Registrar en log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "sequence_id": sequence_id,
            "client_id": sequence["client_id"],
            "client_name": sequence["client_name"],
            "followup_number": followup_number,
            "followup_type": self.FOLLOWUP_SCHEDULE[followup_number]["type"],
            "recipient": sequence["client_email"],
            "subject": email_content["subject"],
            "status": "sent"
        }

        followup_log = json.loads(self.followup_log.read_text())
        followup_log.append(log_entry)
        self.followup_log.write_text(json.dumps(followup_log, indent=2, ensure_ascii=False))

        logger.info(f"✅ Follow-up #{followup_number} registrado")

        return {
            "sequence_id": sequence_id,
            "client_id": sequence["client_id"],
            "followup_number": followup_number,
            "status": "sent",
            "recipient": sequence["client_email"],
            "sent_at": datetime.now().isoformat()
        }

    def mark_followup_opened(self, sequence_id: int, followup_number: int) -> Dict:
        """Marcar un follow-up como abierto"""
        sequences = json.loads(self.followup_file.read_text())

        for seq in sequences["sequences"]:
            if seq["sequence_id"] == sequence_id:
                seq["followups"][str(followup_number)]["opened"] = True
                self.followup_file.write_text(json.dumps(sequences, indent=2, ensure_ascii=False))
                logger.info(f"✅ Follow-up #{followup_number} marcado como abierto")
                return {"status": "marked"}

        return {"error": "Secuencia no encontrada"}

    def complete_sequence(self, sequence_id: int, reason: str = "cliente_respondió") -> Dict:
        """
        Completar una secuencia de follow-up

        Args:
            sequence_id: ID de la secuencia
            reason: Razón de completación (cliente_respondió, rechazó, etc.)

        Returns:
            Estado de la secuencia completada
        """
        sequences = json.loads(self.followup_file.read_text())

        for seq in sequences["sequences"]:
            if seq["sequence_id"] == sequence_id:
                seq["status"] = "completed"
                seq["completed_reason"] = reason
                seq["completed_at"] = datetime.now().isoformat()
                self.followup_file.write_text(json.dumps(sequences, indent=2, ensure_ascii=False))
                logger.info(f"✅ Secuencia {sequence_id} completada")
                return {"status": "completed", "reason": reason}

        return {"error": "Secuencia no encontrada"}

    def get_followup_status(self, client_id: int) -> Dict:
        """Obtener estado de follow-up para un cliente"""
        sequences = json.loads(self.followup_file.read_text())

        for seq in sequences["sequences"]:
            if seq["client_id"] == client_id and seq["status"] == "active":
                followups_sent = sum(1 for f in seq["followups"].values() if f["sent"])
                return {
                    "client_id": client_id,
                    "client_name": seq["client_name"],
                    "sequence_status": seq["status"],
                    "followups_sent": followups_sent,
                    "followups_total": 3,
                    "last_followup_at": seq["last_followup_at"],
                    "details": seq["followups"]
                }

        return {"status": "no_active_sequence"}

    def get_followup_report(self) -> str:
        """Generar reporte de seguimiento"""
        sequences = json.loads(self.followup_file.read_text())
        log = json.loads(self.followup_log.read_text())

        active_sequences = [s for s in sequences["sequences"] if s["status"] == "active"]
        completed_sequences = [s for s in sequences["sequences"] if s["status"] == "completed"]

        total_followups_sent = sum(1 for entry in log)

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         REPORTE DE SEGUIMIENTO (FOLLOW-UPS)                 ║
╚═══════════════════════════════════════════════════════════════╝

📊 ESTADÍSTICAS GENERALES:
   • Secuencias activas: {len(active_sequences)}
   • Secuencias completadas: {len(completed_sequences)}
   • Total follow-ups enviados: {total_followups_sent}

📋 SECUENCIAS ACTIVAS:
"""

        if active_sequences:
            for seq in active_sequences:
                followups_sent = sum(1 for f in seq["followups"].values() if f["sent"])
                report += f"""
   Cliente: {seq['client_name']}
   Email: {seq['client_email']}
   Follow-ups enviados: {followups_sent}/3
   Iniciada: {seq['started_at'][:10]}
   Estado: {seq['status'].upper()}
"""
        else:
            report += "\n   (Ninguna)\n"

        report += f"""
✅ SECUENCIAS COMPLETADAS:
"""

        if completed_sequences:
            for seq in completed_sequences[-5:]:  # Últimas 5
                report += f"""
   Cliente: {seq['client_name']}
   Completada: {seq.get('completed_at', 'N/A')[:10]}
   Razón: {seq.get('completed_reason', 'N/A')}
"""
        else:
            report += "\n   (Ninguna)\n"

        report += """
═════════════════════════════════════════════════════════════════
"""

        return report

    @staticmethod
    def _generate_followup_email(client_name: str, followup_number: int, followup_type: str) -> Dict:
        """Generar contenido de email de seguimiento"""

        templates = {
            1: {
                "check_in": {
                    "subject": f"¿Viste tu propuesta? - {client_name}",
                    "body": f"""Hola {client_name},

Solo checando si viste tu propuesta que te envié hace unos días.

¿Tienes preguntas sobre algún punto?

Respondé con un mensajito o agendemos una call corta de 15 minutos para hablar.

Link: https://calendly.com/enbuenamesa/propuesta

Saludos,
Felix"""
                }
            },
            2: {
                "data_share": {
                    "subject": f"Datos que te pueden interesar - {client_name}",
                    "body": f"""Hola {client_name},

Te quería compartir un dato que vi en tu auditoría:

Tu competencia está invirtiendo en Google Ads optimizadas. Tú tienes 3 oportunidades rápidas para mejorar tu posición.

¿Una call corta? 15 minutos y vemos dónde está la plata.

https://calendly.com/enbuenamesa/propuesta

Saludos,
Felix"""
                }
            },
            3: {
                "last_touch": {
                    "subject": f"Último dato: ROI potencial - {client_name}",
                    "body": f"""Hola {client_name},

Negocios como el tuyo típicamente ven:
  • 40% mejora en quality score
  • 25% reducción en CPC
  • 60% más conversiones

Depende de la estructura actual, pero los números son reales.

¿Una call para ver si aplica en tu caso?

https://calendly.com/enbuenamesa/propuesta

Saludos,
Felix"""
                }
            }
        }

        email_template = templates.get(followup_number, {}).get(followup_type, {
            "subject": f"Follow-up #{followup_number}",
            "body": f"Hola {client_name},\n\nSeguimiento de tu propuesta.\n\nSaludos,\nFelix"
        })

        return email_template


def main():
    """Testing del agente"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║          FOLLOW-UP AGENT - FASE 5                            ║
║    Automatización de Seguimientos Secuenciados               ║
╚════════════════════════════════════════════════════════════════╝
    """)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = FollowUpAgent(orchestrator)

    # ========== 1. INICIAR SECUENCIAS ==========
    print("\n1️⃣ INICIANDO SECUENCIAS DE FOLLOW-UP")
    print("-" * 70)

    for client_id in [1, 2, 3]:
        result = agent.start_followup_sequence(client_id, proposal_id=client_id)
        if "error" not in result:
            print(f"✅ {result['client_name']}: Secuencia iniciada")

    # ========== 2. VER FOLLOW-UPS PENDIENTES ==========
    print("\n2️⃣ FOLLOW-UPS PENDIENTES")
    print("-" * 70)

    pending = agent.get_pending_followups()
    if pending:
        for item in pending:
            print(f"⏳ {item['client_name']}: {item['followup_name']} "
                  f"({item['followup_number']}/3)")
    else:
        print("📅 No hay follow-ups pendientes en este momento")

    # ========== 3. SIMULAR ENVÍO DE FOLLOW-UPS ==========
    print("\n3️⃣ ENVIANDO FOLLOW-UPS SIMULADOS")
    print("-" * 70)

    sequences = json.loads(agent.followup_file.read_text())
    for i, seq in enumerate(sequences["sequences"][:1], 1):
        agent.send_followup(seq["sequence_id"], 1)
        print(f"✅ Enviado follow-up a {seq['client_name']}")

    # ========== 4. ESTADO DE CLIENTES ==========
    print("\n4️⃣ ESTADO DE SEGUIMIENTO POR CLIENTE")
    print("-" * 70)

    for client_id in [1, 2, 3]:
        status = agent.get_followup_status(client_id)
        if "sequence_status" in status:
            print(f"\n📊 {status['client_name']}")
            print(f"   Follow-ups enviados: {status['followups_sent']}/{status['followups_total']}")

    # ========== 5. REPORTE COMPLETO ==========
    print(agent.get_followup_report())

    orchestrator.close_database()


if __name__ == "__main__":
    main()
