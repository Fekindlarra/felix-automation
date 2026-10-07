#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Integration - PASO 1
Generador de datos para widgets de FASE 10 en dashboards
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from analytics.predictor import ConversionPredictor
from analytics.anomaly_detector import AnomalyDetector
from analytics.recommender import RecommendationEngine
from agents.analytics_agent import AnalyticsAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardIntegration:
    """Integración de FASE 10 con dashboards"""

    def __init__(self, orchestrator: Optional[FelixAutomationOrchestrator] = None):
        self.orchestrator = orchestrator
        if orchestrator:
            self.agent = AnalyticsAgent(orchestrator)
        else:
            self.agent = None
        logger.info("✅ Dashboard Integration inicializada")

    def generate_dashboard_data(self) -> Dict:
        """Genera datos para dashboard interno"""
        logger.info("📊 Generando datos para dashboard interno...")

        if not self.agent:
            logger.warning("⚠️ Agent no disponible - retornando datos vacíos")
            return {
                'predictions': {'top_10': [], 'summary': self._empty_summary()},
                'anomalies': {'active': [], 'summary': self._empty_anomaly_summary()},
                'recommendations': {'urgent': [], 'high': [], 'summary': self._empty_rec_summary()},
                'timestamp': datetime.utcnow().isoformat()
            }

        try:
            # Ejecutar análisis completo
            analysis_result = self.agent.analyze_all_clients()

            if analysis_result.get('status') != 'success':
                return {
                    'predictions': {'top_10': [], 'summary': self._empty_summary()},
                    'anomalies': {'active': [], 'summary': self._empty_anomaly_summary()},
                    'recommendations': {'urgent': [], 'high': [], 'summary': self._empty_rec_summary()},
                    'timestamp': datetime.utcnow().isoformat()
                }

            # Extraer predicciones
            predictions = analysis_result.get('predictions', [])
            top_10_predictions = [
                {
                    'client_id': p.client_id,
                    'client_name': p.client_name,
                    'probability': f"{p.probability:.1f}",
                    'confidence': f"{p.confidence:.1f}",
                    'timeline_days': p.predicted_timeline_days,
                    'recommendation': p.recommendation,
                    'status': self._get_probability_status(p.probability)
                }
                for p in predictions[:10]
            ]

            # Extraer anomalías
            all_anomalies = analysis_result.get('anomalies', {})
            active_anomalies = [
                {
                    'client_id': int(cid),
                    'anomalies': [
                        {
                            'type': a.anomaly_type,
                            'severity': a.severity,
                            'description': a.description,
                            'action': a.suggested_action,
                            'severity_color': self._get_severity_color(a.severity)
                        }
                        for a in anomalies
                    ]
                }
                for cid, anomalies in all_anomalies.items()
            ]

            # Extraer recomendaciones
            all_recommendations = analysis_result.get('recommendations', {})
            urgent_recs = []
            high_recs = []

            for client_id, recs in all_recommendations.items():
                for rec in recs:
                    rec_data = {
                        'client_id': client_id,
                        'client_name': rec.client_name,
                        'title': rec.title,
                        'priority': rec.priority.name,
                        'action': rec.action,
                        'impact': rec.expected_impact,
                        'timeline': rec.estimated_timeline
                    }

                    if rec.priority.value == 4:  # URGENT
                        urgent_recs.append(rec_data)
                    elif rec.priority.value == 3:  # HIGH
                        high_recs.append(rec_data)

            # Resumen de métricas
            summary = analysis_result.get('summary', {})

            return {
                'predictions': {
                    'top_10': top_10_predictions,
                    'summary': {
                        'total': summary.get('predictions', {}).get('total', 0),
                        'high_probability': summary.get('predictions', {}).get('high_probability', 0),
                        'medium_probability': summary.get('predictions', {}).get('medium_probability', 0),
                        'low_probability': summary.get('predictions', {}).get('low_probability', 0)
                    }
                },
                'anomalies': {
                    'active': active_anomalies,
                    'summary': {
                        'total': summary.get('anomalies', {}).get('total', 0),
                        'affected_clients': summary.get('anomalies', {}).get('affected_clients', 0),
                        'critical': summary.get('anomalies', {}).get('critical', 0),
                        'high': summary.get('anomalies', {}).get('high', 0),
                        'health': summary.get('anomalies', {}).get('system_health', '100/100')
                    }
                },
                'recommendations': {
                    'urgent': urgent_recs[:5],  # Top 5 urgent
                    'high': high_recs[:5],      # Top 5 high
                    'summary': {
                        'total': len(urgent_recs) + len(high_recs),
                        'urgent_count': len(urgent_recs),
                        'high_count': len(high_recs)
                    }
                },
                'revenue_forecast': summary.get('revenue_forecast', {}),
                'timestamp': summary.get('timestamp', datetime.utcnow().isoformat())
            }

        except Exception as e:
            logger.error(f"❌ Error generando datos dashboard: {e}")
            return {
                'predictions': {'top_10': [], 'summary': self._empty_summary()},
                'anomalies': {'active': [], 'summary': self._empty_anomaly_summary()},
                'recommendations': {'urgent': [], 'high': [], 'summary': self._empty_rec_summary()},
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    def get_client_dashboard_data(self, client_id: int) -> Dict:
        """Genera datos para dashboard cliente específico"""
        logger.info(f"📊 Generando datos para cliente {client_id}...")

        if not self.agent:
            logger.warning("⚠️ Agent no disponible")
            return {'status': 'error', 'message': 'Database not available'}

        try:
            # Análisis individual
            analysis = self.agent.analyze_client(client_id)

            if analysis.get('status') != 'success':
                return analysis

            # Formatear para dashboard cliente
            client_info = analysis.get('client', {})
            prediction = analysis.get('prediction', {})
            anomalies = analysis.get('anomalies', [])
            recommendations = analysis.get('recommendations', [])

            return {
                'status': 'success',
                'client': {
                    'id': client_info.get('id'),
                    'name': client_info.get('name'),
                    'stage': client_info.get('stage'),
                    'stage_label': self._get_stage_label(client_info.get('stage'))
                },
                'prediction': {
                    'probability': prediction.get('probability', 'N/A'),
                    'confidence': prediction.get('confidence', 'N/A'),
                    'timeline_days': prediction.get('timeline_days', 0),
                    'timeline_label': self._get_timeline_label(prediction.get('timeline_days', 0)),
                    'recommendation': prediction.get('recommendation', ''),
                    'positive_factors': prediction.get('positive_factors', []),
                    'risk_factors': prediction.get('risk_factors', []),
                    'status': self._get_probability_status(
                        float(prediction.get('probability', '0').rstrip('%'))
                    )
                },
                'anomalies': [
                    {
                        'type': a.get('type'),
                        'severity': a.get('severity'),
                        'description': a.get('description'),
                        'action': a.get('action'),
                        'severity_color': self._get_severity_color(a.get('severity'))
                    }
                    for a in anomalies
                ],
                'recommendations': [
                    {
                        'title': r.get('title'),
                        'priority': r.get('priority'),
                        'action': r.get('action'),
                        'impact': r.get('impact'),
                        'timeline': r.get('timeline'),
                        'priority_color': self._get_priority_color(r.get('priority'))
                    }
                    for r in recommendations
                ],
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error generando datos cliente {client_id}: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_probability_status(self, probability: float) -> str:
        """Determina estado basado en probabilidad"""
        if probability >= 75:
            return "🟢 ALTA"
        elif probability >= 50:
            return "🟡 MEDIA"
        elif probability >= 30:
            return "🟠 BAJA"
        else:
            return "🔴 CRÍTICA"

    def _get_severity_color(self, severity: str) -> str:
        """Retorna color para severidad"""
        colors = {
            'CRITICAL': '#dc3545',  # Rojo
            'HIGH': '#fd7e14',      # Naranja
            'MEDIUM': '#ffc107',    # Amarillo
            'LOW': '#28a745'        # Verde
        }
        return colors.get(severity, '#6c757d')  # Gris por defecto

    def _get_priority_color(self, priority: str) -> str:
        """Retorna color para prioridad"""
        colors = {
            'URGENT': '#dc3545',    # Rojo
            'HIGH': '#fd7e14',      # Naranja
            'MEDIUM': '#ffc107',    # Amarillo
            'LOW': '#28a745'        # Verde
        }
        return colors.get(priority, '#6c757d')  # Gris por defecto

    def _get_stage_label(self, stage: str) -> str:
        """Etiqueta legible para etapa"""
        labels = {
            'prospecto': '👤 Prospecto',
            'propuesta': '📋 Propuesta',
            'negociacion': '🤝 Negociación',
            'cerrado': '✅ Cerrado'
        }
        return labels.get(stage, stage)

    def _get_timeline_label(self, days: int) -> str:
        """Etiqueta legible para timeline"""
        if days == 0:
            return "Inmediato"
        elif days <= 7:
            return f"1 semana (~{days} días)"
        elif days <= 14:
            return f"2 semanas (~{days} días)"
        elif days <= 30:
            return f"1 mes (~{days} días)"
        else:
            return f"~{days} días"

    def _empty_summary(self) -> Dict:
        """Resumen vacío de predicciones"""
        return {
            'total': 0,
            'high_probability': 0,
            'medium_probability': 0,
            'low_probability': 0
        }

    def _empty_anomaly_summary(self) -> Dict:
        """Resumen vacío de anomalías"""
        return {
            'total': 0,
            'affected_clients': 0,
            'critical': 0,
            'high': 0,
            'health': '100/100'
        }

    def _empty_rec_summary(self) -> Dict:
        """Resumen vacío de recomendaciones"""
        return {
            'total': 0,
            'urgent_count': 0,
            'high_count': 0
        }


def main():
    """Test de Dashboard Integration"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     DASHBOARD INTEGRATION - PASO 1                                     ║
║     Generador de Datos para Widgets FASE 10                           ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Intentar conectar con BD
        orchestrator = FelixAutomationOrchestrator()
        if Path("database.sqlite").exists():
            orchestrator.connect_database()
            dashboard = DashboardIntegration(orchestrator)

            # Generar datos para dashboard interno
            internal_data = dashboard.generate_dashboard_data()

            print("\n✅ Datos Dashboard Interno Generados:")
            print(f"   Predicciones: {internal_data['predictions']['summary']['total']}")
            print(f"   Anomalías activas: {internal_data['anomalies']['summary']['total']}")
            print(f"   Recomendaciones urgentes: {internal_data['recommendations']['summary']['urgent_count']}")

            orchestrator.close_database()
        else:
            # Sin BD, crear con datos mock
            dashboard = DashboardIntegration()
            print("\n⚠️ Base de datos no disponible - Mode demo")
            print("   Datos de ejemplo serán generados automáticamente en dashboard")

    except Exception as e:
        logger.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
