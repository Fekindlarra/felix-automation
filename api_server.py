#!/usr/bin/env python3
"""
FELIX Audit Report API Server
REST API for generating, managing, and delivering audit reports
Integrates with generate_audit_reports.py and provides email automation
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from io import BytesIO
from generate_audit_reports import generate_report
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Email config (load from environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "felix@enbuenamesa.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Reports database (in-memory + persistent JSON)
REPORTS_DB = REPORTS_DIR / "reports_registry.json"

def load_reports_db():
    """Load reports registry from JSON"""
    if REPORTS_DB.exists():
        with open(REPORTS_DB) as f:
            return json.load(f)
    return {"reports": []}

def save_reports_db(data):
    """Save reports registry to JSON"""
    with open(REPORTS_DB, "w") as f:
        json.dump(data, f, indent=2)

def send_report_email(recipient_email, client_name, pdf_bytes, report_config):
    """Send audit report via email"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Reporte de Auditoría FELIX — {client_name}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email

        # Email body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #0a0a0a; background: #f0f0f0;">
                <div style="max-width: 600px; margin: 0 auto; padding: 40px; background: white; border-left: 2px solid #00ff00;">
                    <h1 style="font-family: 'IBM Plex Mono', monospace; font-size: 28px; margin-bottom: 8px;">FELIX</h1>
                    <p style="color: #4d4d4d; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 32px;">Auditoría de Infraestructura Digital</p>

                    <p>Hola,</p>

                    <p>Tu auditoría de infraestructura digital está lista. Encontramos:</p>

                    <ul style="line-height: 1.8;">
                        <li><strong>{report_config['processes']} procesos manuales</strong> que pueden automatizarse</li>
                        <li><strong>{report_config['apis']} integraciones inactivas</strong> esperando conexión</li>
                        <li><strong>{report_config['hours']} horas/semana</strong> que se pierden en tareas repetitivas</li>
                        <li><strong>${{report_config['cost_annual']}}/año</strong> de costo de oportunidad</li>
                    </ul>

                    <p style="margin-top: 24px; padding: 16px; background: #f0f0f0; border-left: 2px solid #00ff00;">
                        <strong>Tu puntuación: {report_config['score']}/100</strong><br>
                        Próximo paso: agendar una llamada de 30 minutos para discutir el plan de implementación.
                    </p>

                    <p style="margin-top: 32px; font-size: 12px; color: #4d4d4d;">
                        El reporte está adjunto (PDF de 3 páginas).<br>
                        Cualquier pregunta: <strong>felix@enbuenamesa.com</strong>
                    </p>

                    <p style="margin-top: 16px; border-top: 1px solid #f0f0f0; padding-top: 16px; font-size: 11px; color: #4d4d4d;">
                        FELIX — Auditoría y Automatización Digital<br>
                        © 2026 FELIX. Todos los derechos reservados.
                    </p>
                </div>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_body, "html"))

        # Attach PDF
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= reporte_{client_name.replace(' ', '_')}.pdf")
        msg.attach(part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logger.info(f"✅ Email enviado a {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Error enviando email: {str(e)}")
        return False

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "FELIX Audit Report API"})

@app.route("/api/reports/generate", methods=["POST"])
def generate_audit_report():
    """
    Generate a new audit report

    POST /api/reports/generate
    {
        "client_name": "Tienda Online ABC",
        "client_email": "abc@example.com",
        "score": 81,
        "processes": 47,
        "apis": 12,
        "hours": 4.2,
        "send_email": true,
        "platforms": "Web • Google Ads • Facebook Ads"
    }
    """
    try:
        data = request.json

        # Validate required fields
        required_fields = ["client_name", "client_email", "score", "processes", "apis", "hours"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Calculate cost
        hourly_rate = data.get("hourly_rate", 50)
        cost_annual = int(data["hours"] * 52 * hourly_rate)

        # Prepare config
        config = {
            "client_name": data["client_name"],
            "client_email": data["client_email"],
            "audit_date": datetime.now().strftime('%d de %B, %Y'),
            "platforms": data.get("platforms", "Web • Google Ads • Facebook Ads • Shopify • GA4"),
            "score": data["score"],
            "processes": data["processes"],
            "apis": data["apis"],
            "hours": f'{data["hours"]}h',
            "cost_annual": f'{cost_annual:,}',
            "manifesto": data.get("manifesto", "Las empresas construyen imperios en flujos que nunca ven. Lo invisible está roto. Nosotros lo hacemos visible."),
            "interpretation": f'{data["processes"]} procesos repetitivos. {data["apis"]} integraciones sin conectar. {data["hours"]} horas por semana por empleado en tareas que un script puede hacer. Eso es dinero que sale sin que lo veas.',
            "finding_1_title": data.get("finding_1_title", "Procesos Desconectados"),
            "finding_1_desc": data.get("finding_1_desc", "Tu operación genera datos en múltiples plataformas pero no hablan entre sí. Información duplicada. Errores manuales."),
            "finding_2_title": data.get("finding_2_title", "Sin Visibilidad"),
            "finding_2_desc": data.get("finding_2_desc", "Nadie tiene la imagen completa de tu operación. Cada área ve su parte. Nadie ve el flujo."),
            "finding_3_title": data.get("finding_3_title", "Automatización Incompleta"),
            "finding_3_desc": data.get("finding_3_desc", "Tienes herramientas pero no están conectadas. APIs sin activar. Potencial sin explotar."),
            "audit_weeks": data.get("audit_weeks", 3),
            "impl_weeks": data.get("impl_weeks", 8),
            "impact_before": f'{data["processes"]} procesos manuales. {data["hours"]}h/semana perdidas. ${cost_annual:,}/año en costo de oportunidad.',
            "impact_after": f'Cero procesos manuales en tu workflow crítico. Recuperación de {data["hours"]}h/semana por empleado. Visibilidad total en tiempo real.',
        }

        # Generate PDF
        pdf_bytes = generate_report(config)

        # Save report to disk
        output_filename = f"reporte_{data['client_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = REPORTS_DIR / output_filename
        output_path.write_bytes(pdf_bytes)

        # Register in database
        db = load_reports_db()
        report_record = {
            "id": len(db["reports"]) + 1,
            "client_name": data["client_name"],
            "client_email": data["client_email"],
            "score": data["score"],
            "processes": data["processes"],
            "apis": data["apis"],
            "created_at": datetime.now().isoformat(),
            "filename": output_filename,
            "status": "generated"
        }
        db["reports"].append(report_record)
        save_reports_db(db)

        # Send email if requested
        email_sent = False
        if data.get("send_email", False):
            email_sent = send_report_email(
                data["client_email"],
                data["client_name"],
                pdf_bytes,
                config
            )
            report_record["email_sent"] = email_sent
            save_reports_db(db)

        return jsonify({
            "status": "success",
            "message": f"Reporte generado para {data['client_name']}",
            "report_id": report_record["id"],
            "filename": output_filename,
            "email_sent": email_sent,
            "download_url": f"/api/reports/download/{report_record['id']}"
        }), 201

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports/batch", methods=["POST"])
def batch_generate_reports():
    """
    Generate multiple reports at once

    POST /api/reports/batch
    {
        "reports": [
            {"client_name": "...", "client_email": "...", "score": 81, ...},
            {"client_name": "...", "client_email": "...", "score": 72, ...}
        ],
        "send_emails": true
    }
    """
    try:
        data = request.json
        reports_list = data.get("reports", [])
        send_emails = data.get("send_emails", False)

        results = []
        for report_data in reports_list:
            report_data["send_email"] = send_emails

            # Use the generate function directly
            hourly_rate = report_data.get("hourly_rate", 50)
            cost_annual = int(report_data["hours"] * 52 * hourly_rate)

            config = {
                "client_name": report_data["client_name"],
                "client_email": report_data["client_email"],
                "audit_date": datetime.now().strftime('%d de %B, %Y'),
                "platforms": report_data.get("platforms", "Web • Google Ads • Facebook Ads • Shopify • GA4"),
                "score": report_data["score"],
                "processes": report_data["processes"],
                "apis": report_data["apis"],
                "hours": f'{report_data["hours"]}h',
                "cost_annual": f'{cost_annual:,}',
                "manifesto": report_data.get("manifesto", "Las empresas construyen imperios en flujos que nunca ven. Lo invisible está roto. Nosotros lo hacemos visible."),
                "interpretation": f'{report_data["processes"]} procesos repetitivos. {report_data["apis"]} integraciones sin conectar. {report_data["hours"]} horas por semana en tareas repetitivas.',
                "finding_1_title": report_data.get("finding_1_title", "Procesos Desconectados"),
                "finding_1_desc": report_data.get("finding_1_desc", "Tu operación genera datos en múltiples plataformas pero no hablan entre sí."),
                "finding_2_title": report_data.get("finding_2_title", "Sin Visibilidad"),
                "finding_2_desc": report_data.get("finding_2_desc", "Nadie tiene la imagen completa de tu operación."),
                "finding_3_title": report_data.get("finding_3_title", "Automatización Incompleta"),
                "finding_3_desc": report_data.get("finding_3_desc", "Tienes herramientas pero no están conectadas."),
                "audit_weeks": report_data.get("audit_weeks", 3),
                "impl_weeks": report_data.get("impl_weeks", 8),
                "impact_before": f'{report_data["processes"]} procesos manuales. {report_data["hours"]}h/semana perdidas.',
                "impact_after": f'Cero procesos manuales. Recuperación de {report_data["hours"]}h/semana.',
            }

            pdf_bytes = generate_report(config)
            output_filename = f"reporte_{report_data['client_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = REPORTS_DIR / output_filename
            output_path.write_bytes(pdf_bytes)

            email_sent = False
            if send_emails:
                email_sent = send_report_email(
                    report_data["client_email"],
                    report_data["client_name"],
                    pdf_bytes,
                    config
                )

            results.append({
                "client_name": report_data["client_name"],
                "status": "success",
                "filename": output_filename,
                "email_sent": email_sent
            })

        return jsonify({
            "status": "success",
            "message": f"Procesados {len(results)} reportes",
            "results": results
        }), 201

    except Exception as e:
        logger.error(f"Error in batch generation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports", methods=["GET"])
def list_reports():
    """List all generated reports"""
    try:
        db = load_reports_db()
        return jsonify({
            "status": "success",
            "total": len(db["reports"]),
            "reports": db["reports"]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    """Get report details"""
    try:
        db = load_reports_db()
        report = next((r for r in db["reports"] if r["id"] == report_id), None)

        if not report:
            return jsonify({"error": "Report not found"}), 404

        return jsonify({
            "status": "success",
            "report": report
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports/download/<int:report_id>", methods=["GET"])
def download_report(report_id):
    """Download report PDF"""
    try:
        db = load_reports_db()
        report = next((r for r in db["reports"] if r["id"] == report_id), None)

        if not report:
            return jsonify({"error": "Report not found"}), 404

        filepath = REPORTS_DIR / report["filename"]
        if not filepath.exists():
            return jsonify({"error": "File not found"}), 404

        return send_file(
            filepath,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=report["filename"]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("🚀 FELIX Audit Report API Server starting...")
    logger.info(f"📁 Reports directory: {REPORTS_DIR}")
    logger.info(f"📧 Email configured: {SENDER_EMAIL if SENDER_PASSWORD else 'DISABLED'}")
    app.run(debug=True, host="0.0.0.0", port=5000)
