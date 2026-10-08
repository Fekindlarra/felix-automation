#!/usr/bin/env python3
"""
FELIX Audit Report Generator
Generates branded PDF reports with Nothing Aesthetic + FELIX tone of voice

Usage:
    python generate_audit_reports.py --client "Cliente Name" --score 81 --processes 47 --apis 12 --hours 4.2
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from weasyprint import HTML, CSS
from io import BytesIO

# HTML Template with FELIX branding + Nothing Aesthetic
REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Auditoría — {client_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --black: #0a0a0a;
            --white: #ffffff;
            --gray-dark: #4d4d4d;
            --gray-light: #f0f0f0;
            --accent-green: #00ff00;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'IBM Plex Sans', sans-serif;
            background: var(--white);
            color: var(--black);
            line-height: 1.6;
        }}

        .page {{
            max-width: 595px;
            height: 841px;
            background: var(--white);
            margin: 0 auto;
            padding: 50px 40px;
            page-break-after: always;
            border: 1px solid var(--gray-light);
        }}

        .page:last-child {{
            page-break-after: avoid;
        }}

        h1 {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 48px;
            font-weight: 700;
            letter-spacing: -2px;
            margin-bottom: 8px;
            text-align: center;
        }}

        h2 {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -1px;
            margin-top: 30px;
            margin-bottom: 16px;
            text-transform: uppercase;
        }}

        h3 {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-bottom: 12px;
            text-transform: uppercase;
            color: var(--gray-dark);
        }}

        p {{
            font-size: 13px;
            line-height: 1.7;
            margin-bottom: 12px;
        }}

        .divider {{
            height: 1px;
            background: var(--black);
            margin: 20px 0;
        }}

        .divider-accent {{
            height: 2px;
            background: var(--accent-green);
            width: 100px;
            margin: 16px auto;
        }}

        .header-section {{
            text-align: center;
            margin-bottom: 40px;
        }}

        .subtitle {{
            font-size: 12px;
            color: var(--gray-dark);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 24px;
        }}

        .client-info {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            text-align: left;
            margin-bottom: 40px;
            line-height: 1.8;
        }}

        .client-info-line {{
            margin-bottom: 12px;
        }}

        .client-info-label {{
            color: var(--gray-dark);
            text-transform: uppercase;
            letter-spacing: 1px;
            display: inline-block;
            width: 80px;
        }}

        .client-info-value {{
            font-weight: 700;
            color: var(--black);
            display: inline;
        }}

        .score-box {{
            text-align: center;
            margin: 40px 0;
            padding: 40px;
            border: 1px solid var(--black);
        }}

        .score-number {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 72px;
            font-weight: 700;
            letter-spacing: -3px;
            color: var(--accent-green);
            margin-bottom: 8px;
        }}

        .score-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--gray-dark);
        }}

        .findings-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 12px;
        }}

        .findings-table th {{
            font-family: 'IBM Plex Mono', monospace;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--black);
            background: var(--white);
        }}

        .findings-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid var(--gray-light);
        }}

        .findings-table tr:last-child td {{
            border-bottom: none;
        }}

        .recommendation {{
            border-left: 2px solid var(--black);
            padding-left: 16px;
            margin-bottom: 16px;
        }}

        .recommendation-title {{
            font-family: 'IBM Plex Mono', monospace;
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        .recommendation-desc {{
            font-size: 12px;
            color: var(--gray-dark);
        }}

        .next-steps {{
            margin-top: 30px;
        }}

        .next-steps-list {{
            font-size: 12px;
            line-height: 1.8;
        }}

        .step {{
            margin-bottom: 12px;
            font-family: 'IBM Plex Mono', monospace;
        }}

        .step-number {{
            font-weight: 700;
            color: var(--accent-green);
            margin-right: 8px;
        }}

        .footer {{
            text-align: center;
            font-size: 11px;
            color: var(--gray-dark);
            margin-top: 40px;
            border-top: 1px solid var(--gray-light);
            padding-top: 16px;
        }}

        .page-number {{
            text-align: right;
            font-size: 10px;
            color: var(--gray-dark);
            margin-top: 20px;
        }}

        .manifesto {{
            font-size: 12px;
            line-height: 1.8;
            font-style: italic;
            color: var(--gray-dark);
            margin: 20px 0;
            padding: 16px;
            border-left: 2px solid var(--accent-green);
        }}

        @media print {{
            body {{
                margin: 0;
                padding: 0;
            }}
            .page {{
                margin: 0;
                border: none;
                page-break-after: always;
            }}
        }}
    </style>
</head>
<body>

    <!-- PAGE 1: PORTADA -->
    <div class="page">
        <div class="header-section">
            <h1>FELIX</h1>
            <div class="divider-accent"></div>
            <p class="subtitle">Auditoría de Infraestructura Digital</p>
        </div>

        <div class="client-info">
            <div class="client-info-line">
                <span class="client-info-label">Cliente</span>
                <span class="client-info-value">{client_name}</span>
            </div>
            <div class="client-info-line">
                <span class="client-info-label">Email</span>
                <span class="client-info-value">{client_email}</span>
            </div>
            <div class="client-info-line">
                <span class="client-info-label">Fecha</span>
                <span class="client-info-value">{audit_date}</span>
            </div>
            <div class="client-info-line">
                <span class="client-info-label">Plataformas</span>
                <span class="client-info-value">{platforms}</span>
            </div>
        </div>

        <div class="divider"></div>

        <div class="score-box">
            <div class="score-number">{score}</div>
            <div class="score-label">Puntuación General (0–100)</div>
        </div>

        <div class="manifesto">
            "{manifesto}"
        </div>

        <p style="text-align: center; font-size: 12px; color: var(--gray-dark); margin-top: 30px;">
            Tu infraestructura digital medida, analizada y presentada.<br>
            Sin ornamentos. Sin promesas. Solo datos.
        </p>

        <div class="page-number">1</div>
    </div>

    <!-- PAGE 2: HALLAZGOS -->
    <div class="page">
        <h2>Lo que encontramos</h2>

        <div class="score-box" style="margin: 20px 0; padding: 20px; border: 1px solid var(--black);">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; text-align: center;">
                <div>
                    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 32px; font-weight: 700; color: var(--accent-green); margin-bottom: 4px;">{processes}</div>
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--gray-dark);">Procesos Manuales</div>
                </div>
                <div>
                    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 32px; font-weight: 700; color: var(--accent-green); margin-bottom: 4px;">{apis}</div>
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--gray-dark);">APIs Inactivas</div>
                </div>
                <div>
                    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 32px; font-weight: 700; color: var(--accent-green); margin-bottom: 4px;">{hours}</div>
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--gray-dark);">h/semana Perdidas</div>
                </div>
                <div>
                    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 32px; font-weight: 700; color: var(--accent-green); margin-bottom: 4px;">${{cost_annual}}</div>
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--gray-dark);">Costo Anual</div>
                </div>
            </div>
        </div>

        <h2 style="margin-top: 30px;">¿Qué significa?</h2>

        <p style="font-size: 13px; line-height: 1.8; color: var(--gray-dark);">
            {interpretation}
        </p>

        <h2 style="margin-top: 30px;">Hallazgos Principales</h2>

        <div class="recommendation">
            <div class="recommendation-title">1. {finding_1_title}</div>
            <div class="recommendation-desc">{finding_1_desc}</div>
        </div>

        <div class="recommendation">
            <div class="recommendation-title">2. {finding_2_title}</div>
            <div class="recommendation-desc">{finding_2_desc}</div>
        </div>

        <div class="recommendation">
            <div class="recommendation-title">3. {finding_3_title}</div>
            <div class="recommendation-desc">{finding_3_desc}</div>
        </div>

        <div class="page-number">2</div>
    </div>

    <!-- PAGE 3: PROPUESTA -->
    <div class="page">
        <h2>La Propuesta</h2>

        <div style="border: 1px solid var(--black); padding: 20px; margin: 20px 0;">
            <h3>Automatizar • Integrar • Controlar</h3>

            <div style="margin-top: 16px;">
                <p style="font-size: 12px; margin-bottom: 8px;">
                    <strong style="font-family: 'IBM Plex Mono', monospace;">Fase 1:</strong> Auditoría completa ({audit_weeks}w)
                </p>
                <p style="font-size: 12px; color: var(--gray-dark); margin-bottom: 16px;">
                    Mapeo detallado de flujos. Identificación de automatizaciones rápidas. Plan de implementación.
                </p>

                <p style="font-size: 12px; margin-bottom: 8px;">
                    <strong style="font-family: 'IBM Plex Mono', monospace;">Fase 2:</strong> Implementación ({impl_weeks}w)
                </p>
                <p style="font-size: 12px; color: var(--gray-dark); margin-bottom: 16px;">
                    Setup de integraciones. Automatización de procesos. Testing y validación.
                </p>

                <p style="font-size: 12px; margin-bottom: 8px;">
                    <strong style="font-family: 'IBM Plex Mono', monospace;">Fase 3:</strong> Capacitación (1w)
                </p>
                <p style="font-size: 12px; color: var(--gray-dark);">
                    Documentación. Entrenamientos. Monitoring.
                </p>
            </div>
        </div>

        <h2 style="margin-top: 30px;">Impacto Esperado</h2>

        <p style="font-size: 12px; line-height: 1.8; margin: 16px 0;">
            <strong>Antes:</strong> {impact_before}
        </p>

        <p style="font-size: 12px; line-height: 1.8; margin: 16px 0;">
            <strong>Después:</strong> {impact_after}
        </p>

        <h2 style="margin-top: 30px;">Próximos Pasos</h2>

        <div class="next-steps-list">
            <div class="step">
                <span class="step-number">1</span>
                Revisar este reporte y los hallazgos
            </div>
            <div class="step">
                <span class="step-number">2</span>
                Agendar una llamada de 30 minutos
            </div>
            <div class="step">
                <span class="step-number">3</span>
                Discutir timeline y presupuesto
            </div>
            <div class="step">
                <span class="step-number">4</span>
                Comenzar la Fase 1
            </div>
        </div>

        <div class="footer">
            <p style="margin-bottom: 8px;">FELIX — Auditoría y Automatización Digital</p>
            <p>© 2026 FELIX. Todos los derechos reservados.</p>
            <p style="margin-top: 8px;">Para más información: felix@enbuenamesa.com</p>
        </div>

        <div class="page-number">3</div>
    </div>

</body>
</html>
"""

def generate_report(config: dict) -> bytes:
    """Generate PDF report from configuration"""

    html_content = REPORT_TEMPLATE.format(**config)

    # Generate PDF using WeasyPrint
    html_doc = HTML(string=html_content, base_url='.')
    pdf_bytes = html_doc.write_pdf()

    return pdf_bytes

def main():
    parser = argparse.ArgumentParser(description='FELIX Audit Report Generator')
    parser.add_argument('--client', required=True, help='Client name')
    parser.add_argument('--email', default='contact@example.com', help='Client email')
    parser.add_argument('--score', type=int, default=81, help='Audit score (0-100)')
    parser.add_argument('--processes', type=int, default=47, help='Manual processes found')
    parser.add_argument('--apis', type=int, default=12, help='Inactive APIs found')
    parser.add_argument('--hours', type=float, default=4.2, help='Hours/week lost')
    parser.add_argument('--output', default=None, help='Output PDF path')

    args = parser.parse_args()

    # Calculate cost annually (hours * 52 weeks * estimated hourly rate)
    hourly_rate = 50  # Default estimate
    cost_annual = int(args.hours * 52 * hourly_rate)

    # Configure report
    config = {
        'client_name': args.client,
        'client_email': args.email,
        'audit_date': datetime.now().strftime('%d de %B, %Y'),
        'platforms': 'Web • Google Ads • Facebook Ads • Shopify • GA4',
        'score': args.score,
        'processes': args.processes,
        'apis': args.apis,
        'hours': f'{args.hours}h',
        'cost_annual': f'{cost_annual:,}',
        'manifesto': 'Las empresas construyen imperios en flujos que nunca ven. Lo invisible está roto. Nosotros lo hacemos visible.',
        'interpretation': f'{args.processes} procesos repetitivos. {args.apis} integraciones sin conectar. {args.hours} horas por semana por empleado en tareas que un script puede hacer. Eso es dinero que sale sin que lo veas.',
        'finding_1_title': 'Procesos Desconectados',
        'finding_1_desc': 'Tu ecommerce genera datos en 5 plataformas pero no hablan entre sí. Información duplicada. Errores manuales.',
        'finding_2_title': 'Sin Visibilidad',
        'finding_2_desc': 'Nadie tiene la imagen completa de tu operación. Cada área ve su parte. Nadie ve el flujo.',
        'finding_3_title': 'Automatización Incompleta',
        'finding_3_desc': 'Tienes herramientas pero no están conectadas. APIs sin activar. Potencial sin explotar.',
        'audit_weeks': 3,
        'impl_weeks': 8,
        'impact_before': f'{args.processes} procesos manuales. {args.hours}h/semana perdidas. ${cost_annual:,}/año en costo de oportunidad.',
        'impact_after': f'Cero procesos manuales en tu workflow crítico. Recuperación de {args.hours}h/semana por empleado. Visibilidad total en tiempo real.',
    }

    # Generate PDF
    pdf = generate_report(config)

    # Save to file
    output_path = args.output or f"reporte_{args.client.replace(' ', '_')}.pdf"
    Path(output_path).write_bytes(pdf)

    print(f"✅ Reporte generado: {output_path}")
    print(f"   Cliente: {args.client}")
    print(f"   Score: {args.score}/100")
    print(f"   Procesos: {args.processes} | APIs: {args.apis} | Horas: {args.hours}h/semana")

if __name__ == '__main__':
    main()
