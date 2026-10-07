#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FASE 7: FUNNEL MANAGEMENT AGENT
Gestión del embudo de ventas y generación de dashboards
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from agents.funnel_management_agent import FunnelManagementAgent


def generate_html_internal_dashboard(agent: FunnelManagementAgent) -> str:
    """Generar dashboard interno dinámico con datos reales"""

    metrics = agent.get_pipeline_metrics()
    dashboard_data = agent.get_dashboard_data_interno()

    # Generar barras de progreso
    def get_percentage(value, total):
        if total == 0:
            return 0
        return (value / total) * 100

    prospecto_pct = get_percentage(metrics['por_etapa']['prospecto'], metrics['total_clientes'])
    propuesta_pct = get_percentage(metrics['por_etapa']['propuesta'], metrics['total_clientes'])
    negociacion_pct = get_percentage(metrics['por_etapa']['negociacion'], metrics['total_clientes'])
    cerrado_pct = get_percentage(metrics['por_etapa']['cerrado'], metrics['total_clientes'])

    # Generar filas de tabla de clientes
    clients_html = ""
    for stage_num in range(1, 5):
        clients = agent.get_clients_by_stage(stage_num)
        for client in clients:
            stage_name = agent.ETAPAS[stage_num]
            badge_class = f"badge-{stage_name}"
            stage_label = stage_name.upper()

            clients_html += f"""
                    <tr>
                        <td class="client-name">{client['client_name']}</td>
                        <td>{client['email']}</td>
                        <td><span class="stage-badge {badge_class}">{stage_label}</span></td>
                        <td>{client['created_at'][:10]}</td>
                        <td>{client['updated_at'][:10]}</td>
                    </tr>
            """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Interno - Felix Automation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
        }}

        header p {{
            font-size: 14px;
            opacity: 0.9;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}

        .metric-label {{
            font-size: 12px;
            color: #667eea;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}

        .metric-value {{
            font-size: 36px;
            font-weight: 700;
            color: #333;
            margin-bottom: 5px;
        }}

        .metric-subtitle {{
            font-size: 13px;
            color: #999;
        }}

        .funnel-section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}

        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #333;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }}

        .funnel-stage {{
            margin-bottom: 20px;
        }}

        .stage-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }}

        .stage-name {{
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }}

        .stage-count {{
            color: #667eea;
            font-weight: 700;
        }}

        .stage-bar {{
            width: 100%;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}

        .stage-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            color: white;
            transition: width 0.5s ease;
        }}

        .stage-percentage {{
            font-size: 12px;
            color: #999;
            margin-top: 5px;
            text-align: right;
        }}

        .clients-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 13px;
        }}

        .clients-table thead {{
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
        }}

        .clients-table th {{
            padding: 12px;
            text-align: left;
            font-weight: 700;
            color: #667eea;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }}

        .clients-table td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}

        .clients-table tbody tr:hover {{
            background: #f8f9fa;
        }}

        .client-name {{
            font-weight: 600;
            color: #333;
        }}

        .stage-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }}

        .badge-prospecto {{
            background: #e3f2fd;
            color: #1976d2;
        }}

        .badge-propuesta {{
            background: #fff3e0;
            color: #f57c00;
        }}

        .badge-negociacion {{
            background: #fce4ec;
            color: #c2185b;
        }}

        .badge-cerrado {{
            background: #e8f5e9;
            color: #388e3c;
        }}

        .footer {{
            text-align: center;
            color: white;
            font-size: 12px;
            margin-top: 30px;
            opacity: 0.8;
        }}

        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}

            header h1 {{
                font-size: 24px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Dashboard Interno</h1>
            <p>Felix Automation - Control del Embudo de Ventas (Datos en Vivo)</p>
        </header>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">👥 Total Clientes</div>
                <div class="metric-value">{metrics['total_clientes']}</div>
                <div class="metric-subtitle">En el pipeline activo</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">📧 Emails Enviados</div>
                <div class="metric-value">0</div>
                <div class="metric-subtitle">Esta semana</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">💰 Ingresos Esperados</div>
                <div class="metric-value">{dashboard_data['metricas']['ingresos_esperados']}</div>
                <div class="metric-subtitle">De leads ALTO potencial</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">🎯 Leads Alto Potencial</div>
                <div class="metric-value">{metrics['leads_alto_potencial']}</div>
                <div class="metric-subtitle">Score >= 75</div>
            </div>
        </div>

        <div class="funnel-section">
            <div class="section-title">Distribución del Embudo</div>

            <div class="funnel-stage">
                <div class="stage-header">
                    <span class="stage-name">1️⃣ PROSPECTO - Clientes identificados</span>
                    <span class="stage-count">{metrics['por_etapa']['prospecto']} clientes</span>
                </div>
                <div class="stage-bar">
                    <div class="stage-fill" style="width: {prospecto_pct}%">{metrics['porcentajes']['prospecto']}%</div>
                </div>
                <div class="stage-percentage">{metrics['por_etapa']['prospecto']} / {metrics['total_clientes']} clientes</div>
            </div>

            <div class="funnel-stage">
                <div class="stage-header">
                    <span class="stage-name">2️⃣ PROPUESTA - Propuesta enviada</span>
                    <span class="stage-count">{metrics['por_etapa']['propuesta']} clientes</span>
                </div>
                <div class="stage-bar">
                    <div class="stage-fill" style="width: {propuesta_pct}%">{metrics['porcentajes']['propuesta']}%</div>
                </div>
                <div class="stage-percentage">{metrics['por_etapa']['propuesta']} / {metrics['total_clientes']} clientes</div>
            </div>

            <div class="funnel-stage">
                <div class="stage-header">
                    <span class="stage-name">3️⃣ NEGOCIACIÓN - En conversación</span>
                    <span class="stage-count">{metrics['por_etapa']['negociacion']} clientes</span>
                </div>
                <div class="stage-bar">
                    <div class="stage-fill" style="width: {negociacion_pct}%">{metrics['porcentajes']['negociacion']}%</div>
                </div>
                <div class="stage-percentage">{metrics['por_etapa']['negociacion']} / {metrics['total_clientes']} clientes</div>
            </div>

            <div class="funnel-stage">
                <div class="stage-header">
                    <span class="stage-name">4️⃣ CERRADO - Contratado o rechazado</span>
                    <span class="stage-count">{metrics['por_etapa']['cerrado']} clientes</span>
                </div>
                <div class="stage-bar">
                    <div class="stage-fill" style="width: {cerrado_pct}%">{metrics['porcentajes']['cerrado']}%</div>
                </div>
                <div class="stage-percentage">{metrics['por_etapa']['cerrado']} / {metrics['total_clientes']} clientes</div>
            </div>
        </div>

        <div class="funnel-section">
            <div class="section-title">Clientes Activos</div>

            <table class="clients-table">
                <thead>
                    <tr>
                        <th>Cliente</th>
                        <th>Email</th>
                        <th>Etapa</th>
                        <th>Creado</th>
                        <th>Última Actualización</th>
                    </tr>
                </thead>
                <tbody>
                    {clients_html}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Felix Automation Dashboard | Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def generate_html_client_dashboard(agent: FunnelManagementAgent, client_id: int) -> str:
    """Generar dashboard personalizado del cliente con datos reales"""

    client_data = agent.get_dashboard_data_cliente(client_id)

    if "error" in client_data:
        return f"<p>Error: {client_data['error']}</p>"

    client = agent.orchestrator.get_client(client_id)
    scores = client_data['scores']

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tu Dashboard - Felix Automation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: #f8f9fa;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
        }}

        .header-content h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .header-content p {{
            font-size: 14px;
            opacity: 0.95;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }}

        .card-title {{
            font-size: 18px;
            font-weight: 700;
            color: #333;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .card-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }}

        .stage-timeline {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }}

        .stage-timeline::before {{
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: #e0e0e0;
            z-index: 0;
        }}

        .stage-item {{
            flex: 1;
            text-align: center;
            position: relative;
            z-index: 1;
        }}

        .stage-dot {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e0e0e0;
            margin: 0 auto 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
            color: #999;
        }}

        .stage-item.active .stage-dot {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}

        .stage-item.completed .stage-dot {{
            background: #4caf50;
            color: white;
        }}

        .stage-label {{
            font-size: 12px;
            font-weight: 700;
            color: #667eea;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}

        .stage-name {{
            font-size: 13px;
            color: #666;
            font-weight: 500;
        }}

        .scores-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .score-box {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #e0e0e0;
        }}

        .score-platform {{
            font-size: 12px;
            font-weight: 700;
            color: #667eea;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .score-value {{
            font-size: 32px;
            font-weight: 700;
            color: #333;
        }}

        .score-max {{
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }}

        .opportunity-section {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .opportunity-item {{
            margin-bottom: 15px;
        }}

        .opportunity-label {{
            font-size: 12px;
            font-weight: 700;
            color: #667eea;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}

        .opportunity-value {{
            font-size: 24px;
            font-weight: 700;
            color: #333;
        }}

        .timeline-section {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 25px;
            border-radius: 10px;
        }}

        .timeline-item {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }}

        .timeline-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
            flex-shrink: 0;
        }}

        .timeline-content {{
            flex: 1;
        }}

        .timeline-label {{
            font-size: 12px;
            font-weight: 700;
            color: #667eea;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}

        .timeline-value {{
            font-size: 14px;
            color: #333;
            font-weight: 600;
        }}

        .cta-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
        }}

        .cta-title {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 12px;
        }}

        .cta-subtitle {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 20px;
        }}

        .cta-button {{
            display: inline-block;
            background: white;
            color: #667eea;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 700;
            text-decoration: none;
            font-size: 14px;
            transition: all 0.3s ease;
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        .footer {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 40px;
        }}

        @media (max-width: 768px) {{
            .two-column {{
                grid-template-columns: 1fr;
            }}

            .stage-timeline {{
                flex-direction: column;
                gap: 20px;
            }}

            .stage-timeline::before {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <h1>¡Hola, {client.name}! 👋</h1>
                <p>Tu progreso en la propuesta de mejora digital</p>
            </div>
        </header>

        <div class="card">
            <div class="card-title">Tu Posición en el Proceso</div>

            <div class="stage-timeline">
                <div class="stage-item{'active' if client_data['stage'] == 1 else 'completed' if client_data['stage'] > 1 else ''}">
                    <div class="stage-dot">{'✓' if client_data['stage'] > 1 else '1'}</div>
                    <div class="stage-label">{'Completado' if client_data['stage'] > 1 else 'Actual'}</div>
                    <div class="stage-name">Prospecto</div>
                </div>
                <div class="stage-item{'active' if client_data['stage'] == 2 else 'completed' if client_data['stage'] > 2 else ''}">
                    <div class="stage-dot">{'✓' if client_data['stage'] > 2 else '2'}</div>
                    <div class="stage-label">{'Completado' if client_data['stage'] > 2 else 'Actual' if client_data['stage'] == 2 else 'Próximo'}</div>
                    <div class="stage-name">Propuesta</div>
                </div>
                <div class="stage-item{'active' if client_data['stage'] == 3 else 'completed' if client_data['stage'] > 3 else ''}">
                    <div class="stage-dot">{'✓' if client_data['stage'] > 3 else '3'}</div>
                    <div class="stage-label">{'Completado' if client_data['stage'] > 3 else 'Próximo'}</div>
                    <div class="stage-name">Negociación</div>
                </div>
                <div class="stage-item">
                    <div class="stage-dot">4</div>
                    <div class="stage-label">Final</div>
                    <div class="stage-name">Cerrado</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Resultados de tu Auditoría Digital</div>

            <div class="scores-grid">
                <div class="score-box">
                    <div class="score-platform">🌐 Web</div>
                    <div class="score-value">{scores['web']}</div>
                    <div class="score-max">de 100</div>
                </div>

                <div class="score-box">
                    <div class="score-platform">📘 Facebook Ads</div>
                    <div class="score-value">{scores['facebook_ads']}</div>
                    <div class="score-max">de 100</div>
                </div>

                <div class="score-box">
                    <div class="score-platform">🔍 Google Ads</div>
                    <div class="score-value">{scores['google_ads']}</div>
                    <div class="score-max">de 100</div>
                </div>

                <div class="score-box">
                    <div class="score-platform">⭐ Puntuación Total</div>
                    <div class="score-value">{scores['total']}</div>
                    <div class="score-max">de 100</div>
                </div>
            </div>
        </div>

        <div class="two-column">
            <div class="card">
                <div class="card-title">Oportunidades de Mejora</div>

                <div class="opportunity-section">
                    <div class="opportunity-item">
                        <div class="opportunity-label">📈 Mejora Estimada</div>
                        <div class="opportunity-value">{client_data['oportunidad']['mejora_estimada']}</div>
                    </div>
                    <div class="opportunity-item">
                        <div class="opportunity-label">💰 Impacto Mensual</div>
                        <div class="opportunity-value">{client_data['oportunidad']['ingresos_mes']}</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Timeline del Proyecto</div>

                <div class="timeline-section">
                    <div class="timeline-item">
                        <div class="timeline-icon">📅</div>
                        <div class="timeline-content">
                            <div class="timeline-label">Duración</div>
                            <div class="timeline-value">{client_data['timeline']['duracion_proyecto']}</div>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon">📊</div>
                        <div class="timeline-content">
                            <div class="timeline-label">ROI Estimado</div>
                            <div class="timeline-value">{client_data['timeline']['roi_estimado']}</div>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon">👉</div>
                        <div class="timeline-content">
                            <div class="timeline-label">Próximo Paso</div>
                            <div class="timeline-value">{client_data['timeline']['proximo_paso']}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="cta-section">
                <div class="cta-title">¿Listo para comenzar?</div>
                <div class="cta-subtitle">Agendemos una call de 15 minutos para discutir los próximos pasos</div>
                <a href="https://calendly.com/enbuenamesa/propuesta" class="cta-button">Agendar Llamada</a>
            </div>
        </div>

        <div class="footer">
            <p>Felix Automation | Dashboard Personalizado | Última actualización: {client_data['timestamp']}</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║           TEST FASE 7: FUNNEL MANAGEMENT AGENT               ║
║    Gestión del embudo de ventas y generación de dashboards   ║
╚════════════════════════════════════════════════════════════════╝
    """)

    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    agent = FunnelManagementAgent(orchestrator)

    # ========== 1. GESTIONAR PIPELINE ==========
    print("\n1️⃣ GESTIONANDO PIPELINE")
    print("-" * 70)

    # Mover clientes a diferentes etapas
    agent.move_client_to_stage(1, 2)  # Raíces → Propuesta
    agent.move_client_to_stage(2, 1)  # TechShop → Prospecto
    agent.move_client_to_stage(3, 3)  # ConsultorLabs → Negociación

    # ========== 2. MOSTRAR REPORTE TEXTUAL ==========
    print("\n" + agent.get_funnel_report())

    # ========== 3. GENERAR DASHBOARDS HTML ==========
    print("\n2️⃣ GENERANDO DASHBOARDS HTML")
    print("-" * 70)

    # Dashboard Interno
    internal_html = generate_html_internal_dashboard(agent)
    internal_path = Path("data/dashboard_interno.html")
    internal_path.write_text(internal_html)
    print(f"✅ Dashboard Interno: {internal_path}")

    # Dashboards de Clientes
    for client_id in [1, 2, 3]:
        client = orchestrator.get_client(client_id)
        if client:
            client_html = generate_html_client_dashboard(agent, client_id)
            client_path = Path(f"data/dashboard_cliente_{client_id}.html")
            client_path.write_text(client_html)
            print(f"✅ Dashboard Cliente {client_id} ({client.name}): {client_path}")

    # ========== 4. EXPORTAR DATOS JSON ==========
    print("\n3️⃣ EXPORTANDO DATOS EN JSON")
    print("-" * 70)

    # Datos internos
    internal_data = agent.get_dashboard_data_interno()
    internal_json = Path("data/dashboard_interno.json")
    internal_json.write_text(json.dumps(internal_data, indent=2, ensure_ascii=False))
    print(f"✅ JSON Interno: {internal_json}")

    # Datos de cada cliente
    for client_id in [1, 2, 3]:
        client_data = agent.get_dashboard_data_cliente(client_id)
        if "error" not in client_data:
            client_json = Path(f"data/dashboard_cliente_{client_id}.json")
            client_json.write_text(json.dumps(client_data, indent=2, ensure_ascii=False))
            print(f"✅ JSON Cliente {client_id}: {client_json}")

    # ========== 5. MOSTRAR RESUMEN ==========
    print("\n" + "="*70)
    print("RESUMEN DE FASE 7")
    print("="*70)

    metrics = agent.get_pipeline_metrics()
    print(f"""
✅ Pipeline Management COMPLETADO

📊 MÉTRICAS ACTUALES:
   • Total de clientes: {metrics['total_clientes']}
   • Clientes en Prospecto: {metrics['por_etapa']['prospecto']} ({metrics['porcentajes']['prospecto']}%)
   • Clientes en Propuesta: {metrics['por_etapa']['propuesta']} ({metrics['porcentajes']['propuesta']}%)
   • Clientes en Negociación: {metrics['por_etapa']['negociacion']} ({metrics['porcentajes']['negociacion']}%)
   • Clientes Cerrados: {metrics['por_etapa']['cerrado']} ({metrics['porcentajes']['cerrado']}%)

   • Leads ALTO potencial: {metrics['leads_alto_potencial']}
   • Ingresos esperados: ${metrics['ingresos_esperados']:,.0f} USD

📁 ARCHIVOS GENERADOS:
   ✓ Dashboard Interno (HTML + JSON)
   ✓ 3 Dashboards de Clientes (HTML + JSON)
   ✓ Pipeline Data Storage (JSON)

🎯 PRÓXIMOS PASOS:
   → FASE 5: Follow-up Agent (seguimiento automático)
   → FASE 6: Sales Pipeline Agent (gestión del pipeline)
   → Integración con Email Sender Agent (FASE 4)
    """)

    orchestrator.close_database()


if __name__ == "__main__":
    main()
