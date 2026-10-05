#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recommendation Engine - FASE 10
Motor de recomendaciones inteligentes basado en análisis de datos
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Tipos de recomendaciones"""
    IMMEDIATE_ACTION = "immediate_action"
    STRATEGIC_CHANGE = "strategic_change"
    CONTENT_SEND = "content_send"
    FOLLOW_UP = "follow_up"
    DISCOUNT_OFFER = "discount_offer"
    PRODUCT_PIVOT = "product_pivot"
    DEMO_REQUEST = "demo_request"
    ABANDONED_RECOVERY = "abandoned_recovery"


class RecommendationPriority(Enum):
    """Prioridad de recomendación"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Recommendation:
    """Recomendación individual"""
    client_id: int
    client_name: str
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    action: str
    expected_impact: str  # % probabilidad de conversión
    estimated_timeline: str  # Timeline para ver resultado
    dependencies: List[str]  # Requisitos previos


class RecommendationEngine:
    """Motor de recomendaciones inteligentes"""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.recommendation_history = []
        logger.info("✅ Recommendation Engine inicializado")

    def generate_recommendations(self, client_data: Dict,
                               prediction_data: Optional[Dict] = None,
                               anomalies: Optional[List] = None) -> List[Recommendation]:
        """
        Generar recomendaciones para un cliente

        Args:
            client_data: Datos del cliente
            prediction_data: Predicción de conversión
            anomalies: Anomalías detectadas

        Returns:
            Lista de recomendaciones priorizadas
        """
        recommendations = []

        stage = client_data.get('pipeline_stage', 'prospecto')
        probability = prediction_data.get('probability', 50) if prediction_data else 50

        # Generar recomendaciones según etapa
        if stage == 'prospecto':
            recommendations.extend(
                self._recommend_prospecto(client_data, probability, anomalies or [])
            )
        elif stage == 'propuesta':
            recommendations.extend(
                self._recommend_propuesta(client_data, probability, anomalies or [])
            )
        elif stage == 'negociacion':
            recommendations.extend(
                self._recommend_negociacion(client_data, probability, anomalies or [])
            )

        # Recomendaciones transversales basadas en anomalías
        recommendations.extend(
            self._anomaly_based_recommendations(client_data, anomalies or [])
        )

        # Ordenar por prioridad y retornar top 3
        recommendations.sort(
            key=lambda x: (-x.priority.value, -len(x.dependencies))
        )

        return recommendations[:5]  # Top 5 recomendaciones

    def generate_batch(self, clients_data: List[Dict]) -> Dict[int, List[Recommendation]]:
        """Generar recomendaciones para múltiples clientes"""
        results = {}
        for client_data in clients_data:
            client_id = client_data.get('id', 0)
            recommendations = self.generate_recommendations(client_data)
            if recommendations:
                results[client_id] = recommendations
        return results

    def _recommend_prospecto(self, client_data: Dict, probability: float,
                           anomalies: List) -> List[Recommendation]:
        """Recomendaciones para clientes en etapa PROSPECTO"""
        recommendations = []

        # Recomendación 1: Enviar propuesta si no existe
        if not client_data.get('proposal_sent'):
            recommendations.append(Recommendation(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                type=RecommendationType.IMMEDIATE_ACTION,
                priority=RecommendationPriority.URGENT,
                title="📋 Generar y enviar propuesta personalizada",
                description="No hay propuesta registrada. Este es el siguiente paso crítico.",
                action="Usar ProposalGeneratorAgent para crear propuesta personalizada basada en audit",
                expected_impact="+35% en probabilidad de conversión",
                estimated_timeline="2-5 días",
                dependencies=['audit_completed']
            ))

        # Recomendación 2: Mejorar audit score si es bajo
        if client_data.get('audit_score', 100) < 50:
            recommendations.append(Recommendation(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                type=RecommendationType.STRATEGIC_CHANGE,
                priority=RecommendationPriority.HIGH,
                title="🔧 Audit score bajo - Ofrecer consulta gratuita",
                description="Score <50 indica problemas críticos. Ofrecer auditoría in-situ.",
                action="Contactar cliente ofreciendo sesión de diagnóstico gratuita de 1 hora",
                expected_impact="+20% en engagement",
                estimated_timeline="3-7 días",
                dependencies=['client_willing_to_meet']
            ))

        # Recomendación 3: Enviar contenido educativo
        recommendations.append(Recommendation(
            client_id=client_data.get('id', 0),
            client_name=client_data.get('name', f"Client {client_data.get('id')}"),
            type=RecommendationType.CONTENT_SEND,
            priority=RecommendationPriority.MEDIUM,
            title="📧 Enviar guía de mejores prácticas",
            description="Aportar valor previo a propuesta. Aumentar confianza.",
            action="Enviar guía 'Top 10 errores en [industria]' + case study relevante",
            expected_impact="+15% en email opens",
            estimated_timeline="1 día",
            dependencies=['email_address_available']
        ))

        return recommendations

    def _recommend_propuesta(self, client_data: Dict, probability: float,
                           anomalies: List) -> List[Recommendation]:
        """Recomendaciones para clientes en etapa PROPUESTA"""
        recommendations = []

        days_since_proposal = client_data.get('days_since_proposal', 0)
        email_opens = client_data.get('email_opens', 0)

        # Recomendación 1: Seguimiento si no abrió el email
        if email_opens == 0 and days_since_proposal > 3:
            recommendations.append(Recommendation(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                type=RecommendationType.FOLLOW_UP,
                priority=RecommendationPriority.URGENT,
                title="📧 Re-enviar propuesta con subject mejorado",
                description="Propuesta no abierta. Cambiar subject, agregar urgencia.",
                action="Reenviar con subject: '[Oportunidad Urgente] Tu propuesta de mejora está lista'",
                expected_impact="+40% open rate en segundo intento",
                estimated_timeline="1-2 días",
                dependencies=['email_sending_available']
            ))

        # Recomendación 2: Ofrecer descuento si está estancado
        if days_since_proposal > 10 and email_opens < 2:
            recommendations.append(Recommendation(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                type=RecommendationType.DISCOUNT_OFFER,
                priority=RecommendationPriority.HIGH,
                title="🎁 Ofrecer descuento por tiempo limitado",
                description="Propuesta sin acción. Crear urgencia con oferta temporal.",
                action="Enviar email: 'Oferta especial válida hasta [fecha]: 15% descuento'",
                expected_impact="+30% en conversión",
                estimated_timeline="2-7 días",
                dependencies=['pricing_flexible']
            ))

        # Recomendación 3: Solicitar demo si hay engagement
        if email_opens >= 2:
            recommendations.append(Recommendation(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                type=RecommendationType.DEMO_REQUEST,
                priority=RecommendationPriority.HIGH,
                title="🎥 Programar demo o llamada de demostración",
                description="Buen engagement. Avanzar a siguiente nivel.",
                action="Enviar: 'Te gustaría una demostración en vivo? Tengo disponibilidad...'",
                expected_impact="+25% en probabilidad de cierre",
                estimated_timeline="3-5 días",
                dependencies=['schedule_available']
            ))

        return recommendations

    def _recommend_negociacion(self, client_data: Dict, probability: float,
                             anomalies: List) -> List[Recommendation]:
        """Recomendaciones para clientes en etapa NEGOCIACIÓN"""
        recommendations = []

        # Recomendación 1: Cerrar rápido si probabilidad es alta
        if probability >= 75:
            recommendations.append(Recommendation(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                type=RecommendationType.IMMEDIATE_ACTION,
                priority=RecommendationPriority.URGENT,
                title="🎯 Acelerar cierre - Alta probabilidad detectada",
                description="Probabilidad de cierre >75%. Actuar ahora.",
                action="Contactar directo: enviar contrato, agendar firma, celebrar pequeña victoria",
                expected_impact="Cierre en 3-7 días",
                estimated_timeline="Inmediato",
                dependencies=['contract_ready']
            ))

        # Recomendación 2: Resolver objeciones si está bajando probabilidad
        elif probability < 50:
            recommendations.append(Recommendation(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                type=RecommendationType.STRATEGIC_CHANGE,
                priority=RecommendationPriority.HIGH,
                title="⚠️ Objeciones detectadas - Re-evaluación necesaria",
                description="Probabilidad bajó. Cliente tiene dudas.",
                action="Llamada consultiva: 'Qué dudas tienes? Qué haría que esto sea YES?'",
                expected_impact="Identificar y resolver objeciones",
                estimated_timeline="1-3 días",
                dependencies=['call_available']
            ))

        # Recomendación 3: Alternativa de menor precio
        recommendations.append(Recommendation(
            client_id=client_data.get('id', 0),
            client_name=client_data.get('name', f"Client {client_data.get('id')}"),
            type=RecommendationType.PRODUCT_PIVOT,
            priority=RecommendationPriority.MEDIUM,
            title="💰 Ofrecer versión más económica",
            description="Si precio es objeción, ofrecer starter package.",
            action="Proponer: 'Starter package a $X/mes' (30% menos) con upgrade después",
            expected_impact="+40% en cierre con presupuesto ajustado",
            estimated_timeline="2-5 días",
            dependencies=['pricing_options_available']
        ))

        return recommendations

    def _anomaly_based_recommendations(self, client_data: Dict,
                                      anomalies: List) -> List[Recommendation]:
        """Recomendaciones basadas en anomalías detectadas"""
        recommendations = []

        if not anomalies:
            return recommendations

        for anomaly in anomalies:
            anomaly_type = anomaly.anomaly_type if hasattr(anomaly, 'anomaly_type') else 'unknown'

            if anomaly_type == 'abandonment':
                recommendations.append(Recommendation(
                    client_id=client_data.get('id', 0),
                    client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                    type=RecommendationType.ABANDONED_RECOVERY,
                    priority=RecommendationPriority.HIGH,
                    title="👋 Campaña de re-engagement",
                    description="Sin contacto hace muchos días. Recuperación urgente.",
                    action="Enviar: 'Echamos de menos! Aquí está la oferta especial que guardamos para ti'",
                    expected_impact="+20% re-engagement rate",
                    estimated_timeline="1-3 días",
                    dependencies=['re_engagement_email']
                ))

            elif anomaly_type == 'engagement_gap':
                recommendations.append(Recommendation(
                    client_id=client_data.get('id', 0),
                    client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                    type=RecommendationType.FOLLOW_UP,
                    priority=RecommendationPriority.URGENT,
                    title="📧 Verificar recepción de propuesta",
                    description="Propuesta enviada pero no confirmada.",
                    action="Llamada rápida: 'Recibiste la propuesta? Alguna duda?'",
                    expected_impact="+60% apertura después de llamada",
                    estimated_timeline="Mismo día",
                    dependencies=['phone_available']
                ))

        return recommendations

    def get_action_plan(self, recommendations: List[Recommendation]) -> Dict:
        """Crear plan de acción ejecutable"""
        return {
            'urgent_actions': [
                r for r in recommendations
                if r.priority == RecommendationPriority.URGENT
            ],
            'high_priority': [
                r for r in recommendations
                if r.priority == RecommendationPriority.HIGH
            ],
            'medium_priority': [
                r for r in recommendations
                if r.priority == RecommendationPriority.MEDIUM
            ],
            'timeline': self._create_timeline(recommendations),
            'responsible': 'Sales Agent / Automation'
        }

    def _create_timeline(self, recommendations: List[Recommendation]) -> List[Dict]:
        """Crear timeline de ejecución"""
        timeline = []
        for idx, rec in enumerate(recommendations, 1):
            timeline.append({
                'step': idx,
                'action': rec.title,
                'timeline': rec.estimated_timeline,
                'owner': 'Agent'
            })
        return timeline


def main():
    """Test del motor de recomendaciones"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║         RECOMMENDATION ENGINE - FASE 10 ADVANCED ANALYTICS            ║
║              Motor de Recomendaciones Inteligentes                    ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    engine = RecommendationEngine()

    # Casos de prueba
    test_client = {
        'id': 1,
        'name': 'E-commerce XYZ',
        'pipeline_stage': 'propuesta',
        'audit_score': 65,
        'proposal_sent': True,
        'days_since_proposal': 12,
        'email_opens': 0,
        'email_clicks': 0
    }

    prediction = {'probability': 45}

    # Generar recomendaciones
    recommendations = engine.generate_recommendations(test_client, prediction)

    print(f"\n📋 RECOMENDACIONES PARA: {test_client['name']}\n")
    for idx, rec in enumerate(recommendations, 1):
        print(f"{idx}. {rec.title}")
        print(f"   Prioridad: {rec.priority.name}")
        print(f"   Descripción: {rec.description}")
        print(f"   Acción: {rec.action}")
        print(f"   Impacto esperado: {rec.expected_impact}")
        print(f"   Timeline: {rec.estimated_timeline}")
        print()

    # Plan de acción
    action_plan = engine.get_action_plan(recommendations)
    print("\n📅 PLAN DE ACCIÓN:\n")
    for action in action_plan['timeline']:
        print(f"Paso {action['step']}: {action['action']}")
        print(f"  Timeline: {action['timeline']}")
    print()


if __name__ == "__main__":
    main()
