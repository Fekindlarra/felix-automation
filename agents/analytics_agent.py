#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics Agent - FASE 10
Agente coordinador de análisis predictivo, detección de anomalías y recomendaciones
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator
from analytics.predictor import ConversionPredictor
from analytics.anomaly_detector import AnomalyDetector
from analytics.recommender import RecommendationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsAgent:
    """Agente de análisis avanzado - FASE 10"""

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        self.predictor = ConversionPredictor(orchestrator)
        self.anomaly_detector = AnomalyDetector(orchestrator)
        self.recommender = RecommendationEngine(orchestrator)
        logger.info("✅ Analytics Agent inicializado")

    def analyze_all_clients(self) -> Dict:
        """Análisis completo de todos los clientes"""
        logger.info("🔍 Iniciando análisis completo del pipeline...")

        try:
            # 1. Obtener todos los clientes
            clients = self.orchestrator.get_all_clients()
            if not clients:
                logger.warning("⚠️ No hay clientes para analizar")
                return {'status': 'no_clients', 'error': 'No clients found'}

            logger.info(f"📊 Analizando {len(clients)} clientes...")

            # 2. Preparar datos de clientes
            clients_data = self._prepare_client_data(clients)

            # 3. Predicciones
            predictions = self.predictor.predict_batch(clients_data)
            logger.info(f"✅ {len(predictions)} predicciones completadas")

            # 4. Detección de anomalías
            all_anomalies = self.anomaly_detector.detect_batch(clients_data)
            anomaly_impact = self.anomaly_detector.get_impact_summary(all_anomalies)
            logger.info(f"⚠️ {anomaly_impact['total_anomalies']} anomalías detectadas")

            # 5. Recomendaciones
            all_recommendations = {}
            for client_data in clients_data:
                client_id = client_data.get('id', 0)
                # Encontrar predicción correspondiente
                pred_data = next(
                    (p.__dict__ for p in predictions if p.client_id == client_id),
                    None
                )
                anomalies = all_anomalies.get(client_id, [])

                recs = self.recommender.generate_recommendations(
                    client_data,
                    pred_data,
                    anomalies
                )
                if recs:
                    all_recommendations[client_id] = recs

            logger.info(f"💡 {sum(len(r) for r in all_recommendations.values())} recomendaciones generadas")

            # 6. Forecast de revenue
            proposal_amounts = self._get_proposal_amounts(clients_data)
            revenue_forecast = self.predictor.forecast_revenue(predictions, proposal_amounts)

            # 7. Compilar resumen
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'success',
                'clients_analyzed': len(clients_data),
                'predictions': {
                    'total': len(predictions),
                    'high_probability': len([p for p in predictions if p.probability >= 75]),
                    'medium_probability': len([p for p in predictions if 50 <= p.probability < 75]),
                    'low_probability': len([p for p in predictions if p.probability < 50]),
                    'top_5': [
                        {
                            'client_id': p.client_id,
                            'name': p.client_name,
                            'probability': f"{p.probability:.1f}%",
                            'timeline_days': p.predicted_timeline_days
                        }
                        for p in predictions[:5]
                    ]
                },
                'anomalies': {
                    'total': anomaly_impact['total_anomalies'],
                    'affected_clients': anomaly_impact['affected_clients'],
                    'critical': anomaly_impact['critical_count'],
                    'high': anomaly_impact['high_count'],
                    'system_health': f"{anomaly_impact['overall_health']}/100"
                },
                'recommendations': {
                    'total': sum(len(r) for r in all_recommendations.values()),
                    'clients_with_recommendations': len(all_recommendations)
                },
                'revenue_forecast': {
                    '30_days': f"${revenue_forecast['30_days']:,.2f}",
                    '60_days': f"${revenue_forecast['60_days']:,.2f}",
                    '90_days': f"${revenue_forecast['90_days']:,.2f}",
                    'total_expected': f"${revenue_forecast['total_expected']:,.2f}"
                }
            }

            return {
                'status': 'success',
                'summary': summary,
                'predictions': predictions,
                'anomalies': all_anomalies,
                'recommendations': all_recommendations,
                'forecast': revenue_forecast
            }

        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}")
            return {'status': 'failed', 'error': str(e)}

    def analyze_client(self, client_id: int) -> Dict:
        """Análisis individual de un cliente"""
        logger.info(f"🔍 Analizando cliente {client_id}...")

        try:
            # Obtener cliente
            client = self.orchestrator.get_client_by_id(client_id)
            if not client:
                return {'status': 'not_found', 'error': f'Client {client_id} not found'}

            # Preparar datos
            client_data = self._prepare_single_client(client)

            # Análisis
            prediction = self.predictor.predict_conversion(client_id, client_data)
            anomalies = self.anomaly_detector.detect_anomalies(client_data)
            recommendations = self.recommender.generate_recommendations(
                client_data,
                prediction.__dict__ if prediction else None,
                anomalies
            )

            return {
                'status': 'success',
                'client': {
                    'id': client_id,
                    'name': client_data.get('name'),
                    'stage': client_data.get('pipeline_stage')
                },
                'prediction': {
                    'probability': f"{prediction.probability:.1f}%",
                    'confidence': f"{prediction.confidence:.1f}%",
                    'timeline_days': prediction.predicted_timeline_days,
                    'recommendation': prediction.recommendation,
                    'positive_factors': prediction.positive_factors,
                    'risk_factors': prediction.risk_factors
                },
                'anomalies': [
                    {
                        'type': a.anomaly_type,
                        'severity': a.severity,
                        'description': a.description,
                        'action': a.suggested_action
                    }
                    for a in anomalies
                ],
                'recommendations': [
                    {
                        'title': r.title,
                        'priority': r.priority.name,
                        'action': r.action,
                        'impact': r.expected_impact,
                        'timeline': r.estimated_timeline
                    }
                    for r in recommendations
                ]
            }

        except Exception as e:
            logger.error(f"❌ Error analizando cliente {client_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _prepare_client_data(self, clients: List) -> List[Dict]:
        """Preparar datos de clientes para análisis"""
        clients_data = []

        for client in clients:
            try:
                # Obtener auditoría más reciente
                audits = self.orchestrator.get_audits_by_client(client.id)
                latest_audit = audits[0] if audits else None

                # Obtener movimientos en pipeline
                pipeline_moves = self.orchestrator.get_pipeline_moves_by_client(client.id)

                # Obtener emails
                emails = self.orchestrator.get_emails_by_client(client.id)

                # Calcular métricas
                audit_score = float(latest_audit.audit_score) if latest_audit else 50

                # Pipeline stage
                current_stage = pipeline_moves[0].new_stage if pipeline_moves else 'prospecto'

                # Días en stage actual
                if pipeline_moves:
                    days_in_stage = (
                        datetime.utcnow() -
                        datetime.fromisoformat(pipeline_moves[0].moved_at)
                    ).days
                else:
                    days_in_stage = 0

                # Email engagement
                email_opens = len([e for e in emails if e.opened])
                email_clicks = len([e for e in emails if e.clicked])

                # Propuesta
                proposals = self.orchestrator.cursor.execute(
                    "SELECT * FROM proposals WHERE client_id = ? LIMIT 1",
                    (client.id,)
                ).fetchall()
                proposal_sent = len(proposals) > 0

                client_data = {
                    'id': client.id,
                    'name': client.name,
                    'audit_score': audit_score,
                    'pipeline_stage': current_stage,
                    'days_in_stage': days_in_stage,
                    'email_opens': email_opens,
                    'email_clicks': email_clicks,
                    'business_type': client.business_type or 'ecommerce',
                    'proposal_sent': proposal_sent,
                    'days_since_proposal': 0  # Calcular si existe propuesta
                }

                clients_data.append(client_data)
            except Exception as e:
                logger.warning(f"⚠️ Error preparando datos para cliente {client.id}: {e}")
                continue

        return clients_data

    def _prepare_single_client(self, client) -> Dict:
        """Preparar datos de un único cliente"""
        audits = self.orchestrator.get_audits_by_client(client.id)
        latest_audit = audits[0] if audits else None

        pipeline_moves = self.orchestrator.get_pipeline_moves_by_client(client.id)
        emails = self.orchestrator.get_emails_by_client(client.id)

        return {
            'id': client.id,
            'name': client.name,
            'audit_score': float(latest_audit.audit_score) if latest_audit else 50,
            'pipeline_stage': pipeline_moves[0].new_stage if pipeline_moves else 'prospecto',
            'days_in_stage': (
                (datetime.utcnow() - datetime.fromisoformat(pipeline_moves[0].moved_at)).days
                if pipeline_moves else 0
            ),
            'email_opens': len([e for e in emails if e.opened]),
            'email_clicks': len([e for e in emails if e.clicked]),
            'business_type': client.business_type or 'ecommerce',
            'proposal_sent': len(emails) > 0
        }

    def _get_proposal_amounts(self, clients_data: List[Dict]) -> Dict[int, float]:
        """Obtener montos de propuestas por cliente"""
        amounts = {}
        for client_data in clients_data:
            client_id = client_data.get('id', 0)
            # Montos de ejemplo (en producción, obtener de BD)
            amounts[client_id] = 3000 + (client_id * 500)  # Escala simple
        return amounts


def main():
    """Test del Analytics Agent"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║         ANALYTICS AGENT - FASE 10 ADVANCED ANALYTICS                  ║
║              Análisis Predictivo + Anomalías + Recomendaciones       ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Conectar orchestrator
        orchestrator = FelixAutomationOrchestrator()
        orchestrator.connect_database()

        # Crear agent
        agent = AnalyticsAgent(orchestrator)

        # Ejecutar análisis
        result = agent.analyze_all_clients()

        if result.get('status') == 'success':
            summary = result.get('summary', {})
            print("\n✅ ANÁLISIS COMPLETADO\n")
            print(json.dumps(summary, indent=2))
        else:
            print(f"\n❌ Error: {result.get('error')}")

        orchestrator.close_database()

    except Exception as e:
        logger.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
