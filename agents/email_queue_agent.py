#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Queue Agent
Cola local de emails para enviar cuando sea posible
(Útil cuando hay restricciones de firewall/proxy)
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailQueueAgent:
    """Agente que maneja una cola de emails para enviar después"""

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        self.queue_file = Path("data/email_queue.json")
        self.sent_file = Path("data/emails_sent.json")
        self._ensure_queue_files()
        logger.info("✅ Email Queue Agent inicializado")

    def _ensure_queue_files(self):
        """Crear archivos de queue si no existen"""
        if not self.queue_file.exists():
            self.queue_file.write_text(json.dumps([], indent=2))
        if not self.sent_file.exists():
            self.sent_file.write_text(json.dumps([], indent=2))

    def add_to_queue(self, client_id: int, email_type: str, recipient: str, subject: str, body: str) -> Dict:
        """Agregar email a la cola"""
        queue = json.loads(self.queue_file.read_text())

        email_item = {
            "id": len(queue) + 1,
            "client_id": client_id,
            "email_type": email_type,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

        queue.append(email_item)
        self.queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False))

        logger.info(f"✅ Email agregado a cola (ID: {email_item['id']}) - Para: {recipient}")

        return email_item

    def get_queue(self) -> List[Dict]:
        """Obtener todos los emails pendientes"""
        return json.loads(self.queue_file.read_text())

    def get_queue_size(self) -> int:
        """Contar emails pendientes"""
        return len(self.get_queue())

    def export_queue_csv(self) -> str:
        """Exportar cola a CSV para procesar externamente"""
        import csv

        queue = self.get_queue()
        csv_path = Path("data/email_queue.csv")

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'client_id', 'email_type', 'recipient', 'subject', 'created_at', 'status'
            ])
            writer.writeheader()
            for email in queue:
                writer.writerow({
                    'id': email['id'],
                    'client_id': email['client_id'],
                    'email_type': email['email_type'],
                    'recipient': email['recipient'],
                    'subject': email['subject'],
                    'created_at': email['created_at'],
                    'status': email['status']
                })

        logger.info(f"✅ Cola exportada a: {csv_path}")
        return str(csv_path)

    def export_queue_html(self) -> str:
        """Exportar cola como HTML para visualizar en navegador"""
        queue = self.get_queue()
        html_path = Path("data/email_queue_preview.html")

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cola de Emails - Felix Automation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .stats {{ background: #e8f5e9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
        tr:hover {{ background: #f9f9f9; }}
        .email-content {{ max-height: 100px; overflow-y: auto; background: #f9f9f9; padding: 10px; border-radius: 3px; font-size: 12px; }}
        .pending {{ color: #ff9800; font-weight: bold; }}
        .sent {{ color: #4caf50; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 Cola de Emails - Felix Automation</h1>

        <div class="stats">
            <p><strong>Total de emails pendientes:</strong> {len(queue)}</p>
            <p><strong>Generado:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Cliente</th>
                    <th>Tipo</th>
                    <th>Destinatario</th>
                    <th>Asunto</th>
                    <th>Creado</th>
                    <th>Estado</th>
                    <th>Vista Previa</th>
                </tr>
            </thead>
            <tbody>
"""

        for email in queue:
            client = self.orchestrator.get_client(email['client_id'])
            client_name = client.name if client else "N/A"
            status_class = "pending" if email['status'] == "pending" else "sent"

            html_content += f"""
                <tr>
                    <td>{email['id']}</td>
                    <td>{client_name}</td>
                    <td>{email['email_type']}</td>
                    <td>{email['recipient']}</td>
                    <td>{email['subject'][:40]}...</td>
                    <td>{email['created_at'][:10]}</td>
                    <td><span class="{status_class}">{email['status']}</span></td>
                    <td><details><summary>Ver</summary><div class="email-content">{email['body'][:200]}...</div></details></td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        html_path.write_text(html_content)
        logger.info(f"✅ Cola exportada como HTML: {html_path}")
        return str(html_path)

    def mark_as_sent(self, email_id: int):
        """Marcar email como enviado"""
        queue = self.get_queue()
        sent_emails = json.loads(self.sent_file.read_text())

        for email in queue:
            if email['id'] == email_id:
                email['status'] = "sent"
                email['sent_at'] = datetime.now().isoformat()
                sent_emails.append(email)
                break

        self.queue_file.write_text(json.dumps([e for e in queue if e['status'] == "pending"], indent=2, ensure_ascii=False))
        self.sent_file.write_text(json.dumps(sent_emails, indent=2, ensure_ascii=False))

        logger.info(f"✅ Email {email_id} marcado como enviado")

    def get_queue_report(self) -> str:
        """Generar reporte de la cola"""
        queue = self.get_queue()
        sent = json.loads(self.sent_file.read_text())

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         REPORTE DE COLA DE EMAILS                           ║
╚═══════════════════════════════════════════════════════════════╝

📊 ESTADÍSTICAS:
   • Emails pendientes: {len(queue)}
   • Emails enviados: {len(sent)}
   • Total procesados: {len(queue) + len(sent)}

📋 PENDIENTES:
"""

        if queue:
            for email in queue:
                client = self.orchestrator.get_client(email['client_id'])
                client_name = client.name if client else "N/A"
                report += f"\n   ID {email['id']}: {email['email_type']} → {client_name} ({email['recipient']})"
                report += f"\n            Asunto: {email['subject']}"
        else:
            report += "\n   (Ninguno)"

        report += f"""

✅ ENVIADOS RECIENTEMENTE:
"""

        if sent:
            for email in sent[-5:]:  # Últimos 5
                report += f"\n   ID {email['id']}: {email['email_type']} → {email['recipient']}"
        else:
            report += "\n   (Ninguno)"

        report += """

💡 PRÓXIMOS PASOS:
   1. Exporta la cola: queue_agent.export_queue_csv()
   2. Procesa con SendGrid desde tu computadora (sin proxy)
   3. Marca como enviados: queue_agent.mark_as_sent(id)

═════════════════════════════════════════════════════════════════
"""

        return report
