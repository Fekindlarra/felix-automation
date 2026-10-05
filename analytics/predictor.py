#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversion Predictor - FASE 10
Análisis predictivo de conversiones usando datos históricos y ML simple
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversionPrediction:
    """Predicción de conversión para un cliente"""
    client_id: int
    client_name: str
    probability: float  # 0-100
    confidence: float   # 0-100
    risk_factors: List[str]
    positive_factors: List[str]
    recommendation: str
    predicted_timeline_days: int


class ConversionPredictor:
    """Motor de predicción de conversiones basado en patrones históricos"""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.conversion_history = []  # Histórico de conversiones
        self.pipeline_patterns = {}   # Patrones por etapa
        logger.info("✅ Conversion Predictor inicializado")

    def predict_conversion(self, client_id: int, client_data: Dict) -> ConversionPrediction:
        """
        Predecir probabilidad de conversión para un cliente

        Args:
            client_id: ID del cliente
            client_data: Datos del cliente (audits, stage, timeline, etc)

        Returns:
            ConversionPrediction con probabilidad y factores
        """
        probability, confidence = self._calculate_probability(client_data)
        risk_factors = self._identify_risk_factors(client_data, probability)
        positive_factors = self._identify_positive_factors(client_data, probability)
        timeline = self._predict_timeline(client_data, probability)

        recommendation = self._generate_recommendation(
            probability, risk_factors, positive_factors
        )

        return ConversionPrediction(
            client_id=client_id,
            client_name=client_data.get('name', f'Client {client_id}'),
            probability=probability,
            confidence=confidence,
            risk_factors=risk_factors,
            positive_factors=positive_factors,
            recommendation=recommendation,
            predicted_timeline_days=timeline
        )

    def predict_batch(self, clients_data: List[Dict]) -> List[ConversionPrediction]:
        """Predecir para múltiples clientes"""
        predictions = []
        for client_data in clients_data:
            pred = self.predict_conversion(
                client_data.get('id', 0),
                client_data
            )
            predictions.append(pred)

        # Ordenar por probabilidad (descendente)
        predictions.sort(key=lambda x: x.probability, reverse=True)
        return predictions

    def _calculate_probability(self, client_data: Dict) -> Tuple[float, float]:
        """Calcular probabilidad de conversión (0-100)"""
        score = 0.0
        factors = 0

        # Factor 1: Audit Score (0-30 puntos)
        audit_score = client_data.get('audit_score', 50)
        if audit_score >= 80:
            score += 30
        elif audit_score >= 60:
            score += 20
        elif audit_score >= 40:
            score += 10
        factors += 30

        # Factor 2: Pipeline Stage (0-25 puntos)
        stage = client_data.get('pipeline_stage', 'prospecto')
        stage_weight = {
            'prospecto': 5,
            'propuesta': 15,
            'negociacion': 22,
            'cerrado': 25
        }
        score += stage_weight.get(stage, 5)
        factors += 25

        # Factor 3: Time in Current Stage (0-20 puntos)
        days_in_stage = client_data.get('days_in_stage', 0)
        if stage == 'prospecto' and days_in_stage < 7:
            score += 15  # Rápido progreso
        elif stage == 'propuesta' and days_in_stage < 10:
            score += 18  # Tomando acción rápido
        elif stage == 'negociacion' and days_in_stage < 14:
            score += 20  # Buena velocidad de cierre
        factors += 20

        # Factor 4: Email Engagement (0-15 puntos)
        email_opens = client_data.get('email_opens', 0)
        email_clicks = client_data.get('email_clicks', 0)
        if email_clicks >= 2:
            score += 15
        elif email_opens >= 3:
            score += 10
        elif email_opens >= 1:
            score += 5
        factors += 15

        # Factor 5: Business Profile (0-10 puntos)
        business_type = client_data.get('business_type', 'ecommerce')
        high_value_types = ['ecommerce', 'saas', 'marketplace']
        if business_type in high_value_types:
            score += 10
        factors += 10

        # Normalizar a 0-100
        probability = min(100, (score / factors) * 100) if factors > 0 else 50

        # Confidence basado en disponibilidad de datos
        data_points = sum([
            1 for k in ['audit_score', 'pipeline_stage', 'days_in_stage',
                       'email_opens', 'business_type']
            if k in client_data and client_data[k] is not None
        ])
        confidence = min(100, (data_points / 5) * 100)

        return probability, confidence

    def _identify_risk_factors(self, client_data: Dict, probability: float) -> List[str]:
        """Identificar factores de riesgo"""
        risks = []

        # Riesgo 1: Audit Score bajo
        if client_data.get('audit_score', 0) < 50:
            risks.append("⚠️ Audit score bajo (<50) - Necesita mejoras críticas")

        # Riesgo 2: Mucho tiempo en stage actual
        days = client_data.get('days_in_stage', 0)
        stage = client_data.get('pipeline_stage', 'prospecto')
        stage_limits = {'prospecto': 14, 'propuesta': 21, 'negociacion': 30}
        if days > stage_limits.get(stage, 30):
            risks.append(f"⏳ Estancado en {stage} por {days} días")

        # Riesgo 3: Sin engagement de email
        if (client_data.get('email_opens', 0) == 0 and
            client_data.get('email_clicks', 0) == 0):
            risks.append("📧 Sin engagement de email - No abre correos")

        # Riesgo 4: Probabilidad baja
        if probability < 30:
            risks.append("📉 Baja probabilidad de conversión - Revisar approach")

        # Riesgo 5: Sin propuesta enviada
        if not client_data.get('proposal_sent'):
            risks.append("📋 Propuesta no enviada aún")

        return risks[:3]  # Top 3 risks

    def _identify_positive_factors(self, client_data: Dict, probability: float) -> List[str]:
        """Identificar factores positivos"""
        positives = []

        # Factor 1: Audit score alto
        if client_data.get('audit_score', 0) >= 80:
            positives.append("✅ Excelente audit score (80+)")

        # Factor 2: Movimiento rápido en pipeline
        if client_data.get('days_in_stage', 100) < 5:
            positives.append("🚀 Progresión rápida en pipeline")

        # Factor 3: Alto engagement
        if client_data.get('email_opens', 0) >= 3:
            positives.append("💬 Alto email engagement")

        # Factor 4: Tipo de negocio favorable
        if client_data.get('business_type') in ['ecommerce', 'saas']:
            positives.append("🎯 Negocio de alto potencial")

        # Factor 5: En etapa avanzada
        stage = client_data.get('pipeline_stage', 'prospecto')
        if stage in ['negociacion', 'cerrado']:
            positives.append(f"📈 En etapa avanzada: {stage}")

        return positives[:3]  # Top 3 positives

    def _predict_timeline(self, client_data: Dict, probability: float) -> int:
        """Predecir cuántos días hasta conversión"""
        stage = client_data.get('pipeline_stage', 'prospecto')

        # Base timeline por stage
        stage_timeline = {
            'prospecto': 21,    # 3 semanas
            'propuesta': 14,    # 2 semanas
            'negociacion': 7,   # 1 semana
            'cerrado': 0        # Ya cerrado
        }

        base_timeline = stage_timeline.get(stage, 21)

        # Ajustar por probabilidad (clientes con alta prob cierren más rápido)
        if probability >= 80:
            return max(0, base_timeline - 7)
        elif probability >= 60:
            return max(0, base_timeline - 3)
        else:
            return base_timeline

    def _generate_recommendation(self, probability: float, risks: List[str],
                               positives: List[str]) -> str:
        """Generar recomendación de acción"""
        if probability >= 80:
            return "🟢 ALTA: Preparar cierre. Enviar propuesta refinada, follow-up intensivo."
        elif probability >= 60:
            return "🟡 MEDIA: Seguimiento activo. Resolver dudas, enviar case studies."
        elif probability >= 40:
            return "🟠 BAJA: Necesita reengage. Revisar propuesta, ofrecer demo/consulta."
        else:
            return "🔴 CRÍTICA: Repensar estrategia. Considerar otro ángulo de valor."

    def forecast_revenue(self, clients_predictions: List[ConversionPrediction],
                        proposal_amounts: Dict[int, float]) -> Dict:
        """
        Forecast de revenue basado en predicciones

        Args:
            clients_predictions: Lista de predicciones
            proposal_amounts: Dict {client_id: amount}

        Returns:
            Dict con forecast a 30, 60, 90 días
        """
        forecast = {
            '30_days': 0.0,
            '60_days': 0.0,
            '90_days': 0.0,
            'total_expected': 0.0,
            'by_client': []
        }

        for pred in clients_predictions:
            amount = proposal_amounts.get(pred.client_id, 0)
            if amount == 0:
                continue

            # Probabilidad ajustada por timeline
            if pred.predicted_timeline_days <= 30:
                forecast['30_days'] += amount * (pred.probability / 100)
                forecast['total_expected'] += amount * (pred.probability / 100)
            elif pred.predicted_timeline_days <= 60:
                forecast['60_days'] += amount * (pred.probability / 100)
                forecast['total_expected'] += amount * (pred.probability / 100)
            else:
                forecast['90_days'] += amount * (pred.probability / 100)
                forecast['total_expected'] += amount * (pred.probability / 100)

            forecast['by_client'].append({
                'client_id': pred.client_id,
                'name': pred.client_name,
                'probability': pred.probability,
                'expected_revenue': amount * (pred.probability / 100),
                'timeline_days': pred.predicted_timeline_days
            })

        # Ordenar por expected revenue
        forecast['by_client'].sort(
            key=lambda x: x['expected_revenue'],
            reverse=True
        )

        return forecast


def main():
    """Test del predictor"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║         CONVERSION PREDICTOR - FASE 10 ADVANCED ANALYTICS             ║
║           Análisis Predictivo de Conversiones                        ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    predictor = ConversionPredictor()

    # Datos de prueba
    test_clients = [
        {
            'id': 1,
            'name': 'Tech Startup A',
            'audit_score': 85,
            'pipeline_stage': 'negociacion',
            'days_in_stage': 5,
            'email_opens': 4,
            'email_clicks': 2,
            'business_type': 'saas',
            'proposal_sent': True
        },
        {
            'id': 2,
            'name': 'E-commerce B',
            'audit_score': 65,
            'pipeline_stage': 'propuesta',
            'days_in_stage': 8,
            'email_opens': 2,
            'email_clicks': 0,
            'business_type': 'ecommerce',
            'proposal_sent': True
        },
        {
            'id': 3,
            'name': 'Local Business C',
            'audit_score': 45,
            'pipeline_stage': 'prospecto',
            'days_in_stage': 12,
            'email_opens': 0,
            'email_clicks': 0,
            'business_type': 'local',
            'proposal_sent': False
        }
    ]

    # Predecir conversiones
    predictions = predictor.predict_batch(test_clients)

    print("\n📊 PREDICCIONES DE CONVERSIÓN:\n")
    for pred in predictions:
        print(f"📌 {pred.client_name} (ID: {pred.client_id})")
        print(f"   Probabilidad: {pred.probability:.1f}% (Confianza: {pred.confidence:.1f}%)")
        print(f"   Timeline estimado: {pred.predicted_timeline_days} días")
        print(f"   Factores positivos: {', '.join(pred.positive_factors)}")
        print(f"   Factores de riesgo: {', '.join(pred.risk_factors)}")
        print(f"   Recomendación: {pred.recommendation}")
        print()

    # Forecast de revenue
    proposal_amounts = {1: 5000, 2: 3000, 3: 2000}
    forecast = predictor.forecast_revenue(predictions, proposal_amounts)

    print("\n💰 FORECAST DE REVENUE:\n")
    print(f"Esperado 30 días: ${forecast['30_days']:,.2f}")
    print(f"Esperado 60 días: ${forecast['60_days']:,.2f}")
    print(f"Esperado 90 días: ${forecast['90_days']:,.2f}")
    print(f"Total esperado: ${forecast['total_expected']:,.2f}")


if __name__ == "__main__":
    main()
