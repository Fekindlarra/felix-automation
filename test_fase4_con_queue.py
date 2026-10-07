#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FASE 4: EMAIL QUEUE (Sin restricciones de firewall)
Sistema de cola para enviar emails después
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from agents.email_queue_agent import EmailQueueAgent


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  EMAIL QUEUE SYSTEM - FASE 4 ALTERNATIVO                     ║
║  (Para cuando hay restricciones de firewall/proxy)           ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Conectar a la base de datos
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    # Crear agente de cola
    queue_agent = EmailQueueAgent(orchestrator)

    # ========== AGREGAR EMAILS A LA COLA ==========
    print("\n📥 AGREGANDO EMAILS A LA COLA LOCAL")
    print("-" * 70)

    # Email 1: Audit Report
    print("\n1. Agregando AUDIT REPORT...")
    queue_agent.add_to_queue(
        client_id=1,
        email_type="audit_report",
        recipient="info@raices.cl",
        subject="Tu auditoria digital completada - Raices de Cauquenes",
        body="""Hola Raices de Cauquenes,

Tu auditoria digital esta lista.

RESULTADO GENERAL: 81/100

Plataformas auditadas:
  * Web (Performance, Seguridad, Tracking)
  * Facebook Ads (Estructura, Contenido, Targeting)
  * Google Ads (Keywords, Quality Score, Tracking)

Proximos pasos: Una call corta de 15 minutos para explicar hallazgos.

Agendamos? -> https://calendly.com/enbuenamesa/propuesta

Saludos,
Felix Automation
"""
    )

    # Email 2: Proposal
    print("2. Agregando PROPUESTA PERSONALIZADA...")
    queue_agent.add_to_queue(
        client_id=1,
        email_type="proposal",
        recipient="info@raices.cl",
        subject="Tu propuesta de mejora - Raices de Cauquenes",
        body="""Hola Raices de Cauquenes,

Te envio la propuesta personalizada basada en tu auditoria.

PRESUPUESTO ESTIMADO
  * Costo: $3,000 USD
  * Duracion: 2-3 semanas
  * ROI estimado: 2 meses

INCLUYE
  * Auditoria tecnica completa
  * Optimizacion de campanas de ads
  * Implementacion de tracking
  * Reportes mensuales

Agendar call: https://calendly.com/enbuenamesa/propuesta

Saludos,
Felix Automation
"""
    )

    # Email 3: Followup
    print("3. Agregando EMAIL DE SEGUIMIENTO...")
    queue_agent.add_to_queue(
        client_id=1,
        email_type="followup_1",
        recipient="info@raices.cl",
        subject="Seguimiento: Tu auditoria digital",
        body="""Hola Raices de Cauquenes,

Solo checando si viste tu reporte de auditoria.

Preguntas? Duda en algun punto?

Respondé con un mensajito o agendemos 15 minutos de call directa.

Link de call: https://calendly.com/enbuenamesa/propuesta

Saludos,
Felix
"""
    )

    # ========== MOSTRAR COLA ==========
    print("\n" + "="*70)
    print("COLA ACTUAL")
    print("="*70)

    queue = queue_agent.get_queue()
    print(f"\nTotal de emails en la cola: {queue_agent.get_queue_size()}\n")

    for i, email in enumerate(queue, 1):
        print(f"{i}. [{email['status'].upper()}] {email['email_type']}")
        print(f"   Para: {email['recipient']}")
        print(f"   Asunto: {email['subject']}")
        print(f"   Creado: {email['created_at']}")
        print()

    # ========== EXPORTAR COLA ==========
    print("="*70)
    print("EXPORTANDO COLA")
    print("="*70)

    csv_file = queue_agent.export_queue_csv()
    print(f"\nCSV exportado a: {csv_file}")

    html_file = queue_agent.export_queue_html()
    print(f"HTML exportado a: {html_file}")

    # ========== MOSTRAR REPORTE ==========
    print("\n" + queue_agent.get_queue_report())

    orchestrator.close_database()

    # ========== INSTRUCCIONES FINALES ==========
    print("""
╔════════════════════════════════════════════════════════════════╗
║  SIGUIENTE PASO                                               ║
╚════════════════════════════════════════════════════════════════╝

OPCION 1: Enviar desde tu computadora
  1. Descarga los archivos de la cola (data/email_queue.csv)
  2. Usa Python en tu PC (sin proxy): pip install sendgrid
  3. Ejecuta un script para procesar la cola
  4. Marca como enviados

OPCION 2: Usar desde aqui cuando no haya proxy
  1. Configura un proxy alternativo o usa VPN
  2. Ejecuta python test_fase4.py normalmente
  3. Los emails se envian directamente

OPCION 3: Usar servicio externo
  1. Descarga data/email_queue.csv
  2. Importa a campaña de email (MailChimp, Brevo, etc)
  3. Envía masivamente

LA COLA ESTA LISTA. Los emails estan listos para enviarse.
""")


if __name__ == "__main__":
    main()
