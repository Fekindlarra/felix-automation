#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proposal Generator Agent
Genera propuestas HTML + PDF personalizadas por tipo de negocio
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator, Proposal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de tipos de negocio (adaptado del código existente)
BUSINESS_TYPES = {
    "plants": {
        "name": "Productos de Jardinería / Plantas",
        "action": "comprar",
        "noun": "planta",
        "current_volume": "12",
        "current_price": "$35",
        "projected_volume": "19",
        "currency": "USD"
    },
    "ecommerce": {
        "name": "E-commerce General",
        "action": "comprar",
        "noun": "producto",
        "current_volume": "8",
        "current_price": "$89",
        "projected_volume": "24",
        "currency": "USD"
    },
    "services": {
        "name": "Servicios Profesionales",
        "action": "contratar",
        "noun": "servicio",
        "current_volume": "2",
        "current_price": "$500",
        "projected_volume": "6",
        "currency": "USD"
    },
    "saas": {
        "name": "SaaS / Software",
        "action": "suscribirse",
        "noun": "subscripción",
        "current_volume": "5",
        "current_price": "$99",
        "projected_volume": "15",
        "currency": "USD"
    },
    "education": {
        "name": "Educación / Cursos",
        "action": "inscribirse",
        "noun": "curso",
        "current_volume": "3",
        "current_price": "$150",
        "projected_volume": "12",
        "currency": "USD"
    }
}


class ProposalGeneratorAgent:
    """Agente que genera propuestas personalizadas"""

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        logger.info("✅ Proposal Generator Agent inicializado")

    def generate_proposal(self, client_id: int, audit_ids: str) -> Dict:
        """
        Generar propuesta para un cliente

        Args:
            client_id: ID del cliente
            audit_ids: IDs de auditorías separadas por coma
        """
        client = self.orchestrator.get_client(client_id)
        logger.info(f"📝 Generando propuesta para: {client.name}")

        # Obtener auditorías
        audits = self.orchestrator.get_client_audits(client_id)
        audit_data = {a.platform: json.loads(a.metrics_json) for a in audits if a.metrics_json}

        # Crear propuesta
        proposal = Proposal(
            client_id=client_id,
            audit_ids=audit_ids,
            estimated_cost=3000,
            estimated_duration="2-3 semanas",
            status="draft"
        )

        proposal_id = self.orchestrator.create_proposal(proposal)

        # Generar HTML y PDF
        html_content = self._generate_html(client, audit_data)
        pdf_filename = self._generate_pdf(client, html_content, proposal_id)

        # Guardar en BD
        html_filename = f"data/proposals/PROPUESTA_{client.name.replace(' ', '_')}_{proposal_id}.html"
        Path(html_filename).parent.mkdir(exist_ok=True)
        Path(html_filename).write_text(html_content, encoding='utf-8')

        self.orchestrator.update_proposal_files(proposal_id, html_filename, pdf_filename)

        logger.info(f"✅ Propuesta generada: ID {proposal_id}")

        # 🔌 FASE 13 Day 3: Emitir evento WebSocket
        self.orchestrator._emit_proposal_event(client_id, proposal_id, proposal.estimated_cost if hasattr(proposal, 'estimated_cost') else 0)

        return {
            "proposal_id": proposal_id,
            "client_name": client.name,
            "html_file": html_filename,
            "pdf_file": pdf_filename,
            "status": "ready"
        }

    def _generate_html(self, client, audit_data: Dict) -> str:
        """Generar HTML de propuesta"""
        business_type = BUSINESS_TYPES.get(client.business_type, BUSINESS_TYPES["ecommerce"])

        # Calcular mejoras proyectadas
        current_vol = int(business_type.get("current_volume", "0"))
        projected_vol = int(business_type.get("projected_volume", "0"))
        improvement = ((projected_vol - current_vol) / current_vol * 100) if current_vol > 0 else 0

        web_score = audit_data.get('web', {}).get('performance', 50) if audit_data else 50

        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Propuesta Auditoría Digital - {client.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ font-size: 14px; opacity: 0.9; }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .score-card {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .score-item {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 8px;
        }}
        .score-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .score-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .improvement-stat {{
            font-size: 24px;
            font-weight: bold;
            color: #10b981;
            margin: 20px 0;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 20px;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }}
        .cta-button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }}
        ul {{ margin-left: 20px; margin-top: 10px; }}
        li {{ margin: 8px 0; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #eee;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Propuesta de Auditoría Digital</h1>
            <p>{client.name}</p>
        </div>

        <div class="section">
            <h2>Tu Situación Actual</h2>
            <p>Después de analizar {client.business_type} tu sitio web y presencia en publicidad digital, hemos identificado oportunidades clave de mejora.</p>

            <div class="score-card">
                <div class="score-item">
                    <div class="score-value">{web_score}</div>
                    <div class="score-label">Score Sitio Web</div>
                </div>
                <div class="score-item">
                    <div class="score-value">65</div>
                    <div class="score-label">Potencial Digital</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Proyección de Mejora</h2>
            <p>Con nuestra estrategia de optimización, proyectamos:</p>
            <div class="improvement-stat">📈 +{improvement:.0f}% en conversiones</div>
            <p>De {current_vol} {business_type['noun']}s por mes → {projected_vol} {business_type['noun']}s por mes</p>
            <p><strong>Impacto económico estimado:</strong> +${(projected_vol - current_vol) * int(business_type.get('current_price', '100').replace('$', ''))} USD/mes</p>
        </div>

        <div class="section">
            <h2>¿Qué Incluye Nuestro Servicio?</h2>
            <ul>
                <li>✅ Auditoría completa de sitio web (Performance, Seguridad, Tracking, Tecnología)</li>
                <li>✅ Análisis de campañas Facebook Ads</li>
                <li>✅ Auditoría de Google Ads y keywords</li>
                <li>✅ Reporte técnico detallado (confidencial)</li>
                <li>✅ Plan de mejora priorizado</li>
                <li>✅ Sesión de presentación y Q&A</li>
            </ul>
        </div>

        <div class="section">
            <h2>Inversión y Timeline</h2>
            <p><strong>Inversión:</strong> $3,000 USD (financiable)</p>
            <p><strong>Duración:</strong> 2-3 semanas</p>
            <p><strong>ROI esperado:</strong> Recupera en ~2 meses con mejoras implementadas</p>

            <button class="cta-button">👉 Agendar Llamada de Presentación</button>
        </div>

        <div class="footer">
            <p>En Buena Mesa™ - Auditorías Digitales Profesionales</p>
            <p>www.enbuenamesa.com | info@enbuenamesa.com</p>
            <p>Propuesta generada: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
    </div>
</body>
</html>
        """
        return html

    def _generate_pdf(self, client, html_content: str, proposal_id: int) -> str:
        """Generar PDF de propuesta"""
        pdf_filename = f"data/proposals/PROPUESTA_{client.name.replace(' ', '_')}_{proposal_id}.pdf"

        try:
            from weasyprint import HTML, CSS
            from io import BytesIO

            # Crear PDF
            Path(pdf_filename).parent.mkdir(exist_ok=True)
            HTML(string=html_content).write_pdf(pdf_filename)
            logger.info(f"✅ PDF generado: {pdf_filename}")

        except ImportError:
            logger.warning("⚠️ weasyprint no instalado, usando HTML como fallback")
            # Si no está weasyprint, guardar como HTML
            pdf_filename = pdf_filename.replace('.pdf', '.html')

        return pdf_filename


def main():
    """Testing del agente"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         PROPOSAL GENERATOR AGENT                              ║
║    Genera propuestas HTML + PDF personalizadas                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Conectar orquestador
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    # Crear agente
    agent = ProposalGeneratorAgent(orchestrator)

    # Generar propuesta para primer cliente
    print("\n📝 GENERANDO PROPUESTA PARA: Raíces de Cauquenes")
    result = agent.generate_proposal(1, "1,2,3")

    print("\n" + "="*60)
    print("✅ PROPUESTA GENERADA")
    print("="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    orchestrator.close_database()


if __name__ == "__main__":
    main()
