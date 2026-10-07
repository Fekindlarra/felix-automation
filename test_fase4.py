#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FASE 4: EMAIL SENDER AGENT
Demuestra cómo enviar emails automáticamente
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from agents.email_sender_agent import EmailSenderAgent


def test_send_proposal():
    """Test: Enviar propuesta personalizada"""
    print("\n" + "="*70)
    print("TEST FASE 4: EMAIL SENDER AGENT")
    print("="*70)

    # Conectar a la base de datos
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    # Crear el agente de emails
    email_agent = EmailSenderAgent(orchestrator)

    # ========== TEST 1: ENVIAR AUDIT REPORT ==========
    print("\n📧 TEST 1: ENVIAR AUDIT REPORT")
    print("-" * 70)

    audit_data = {
        "average_score": 81,
        "platforms": ["web", "facebook_ads", "google_ads"],
        "details": {
            "web": 79,
            "facebook_ads": 65,
            "google_ads": 72
        }
    }

    print("Enviando a Cliente ID 1 (Raíces de Cauquenes)...")
    result = email_agent.send_audit_report(1, audit_data)
    print(f"Resultado: {result['status']}")
    print(f"Destinatario: {result['recipient']}")

    # ========== TEST 2: ENVIAR PROPUESTA ==========
    print("\n📧 TEST 2: ENVIAR PROPUESTA PERSONALIZADA")
    print("-" * 70)

    proposal_data = {
        "estimated_cost": 3000,
        "estimated_duration": "2-3 semanas",
        "services": [
            "Auditoría técnica completa",
            "Optimización de campañas",
            "Implementación de tracking"
        ]
    }

    print("Enviando propuesta a Cliente ID 1...")
    result = email_agent.send_proposal(1, proposal_id=7, proposal_data=proposal_data)
    print(f"Resultado: {result['status']}")
    print(f"Propuesta ID: {result.get('proposal_id')}")

    # ========== TEST 3: ENVIAR SEGUIMIENTO ==========
    print("\n📧 TEST 3: ENVIAR EMAIL DE SEGUIMIENTO")
    print("-" * 70)

    print("Enviando followup #1...")
    result = email_agent.send_followup(1, followup_round=1)
    print(f"Resultado: {result['status']}")

    # ========== TEST 4: CONFIRMACIÓN DE CALL ==========
    print("\n📧 TEST 4: ENVIAR CONFIRMACIÓN DE CALL")
    print("-" * 70)

    booking_data = {
        "date": "2026-10-08",
        "time": "10:00 AM",
        "zoom_link": "https://zoom.us/j/123456789"
    }

    print("Enviando confirmación de call...")
    result = email_agent.send_booking_confirmation(1, booking_data)
    print(f"Resultado: {result['status']}")
    print(f"Fecha: {result.get('booking_date')} - Hora: {result.get('booking_time')}")

    # ========== RESUMEN ==========
    print("\n" + "="*70)
    print("✅ TEST COMPLETADO")
    print("="*70)
    print("""
Si viste "DEMO_MODE" en los mensajes:
  → Significa que NO tienes SendGrid API Key configurada
  → Los emails fueron SIMULADOS (no se enviaron de verdad)

Si quieres enviar emails DE VERDAD:
  1. Obtén tu API key de SendGrid (https://sendgrid.com)
  2. Crea un archivo .env en la carpeta raíz
  3. Agrega: SENDGRID_API_KEY=SG.tu_key_aqui
  4. Ejecuta este test nuevamente
  5. Los emails se enviarán de verdad ✉️
    """)

    orchestrator.close_database()


if __name__ == "__main__":
    test_send_proposal()
