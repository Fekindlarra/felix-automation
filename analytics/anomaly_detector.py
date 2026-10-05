#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anomaly Detector - FASE 10
Detección de anomalías y patrones inusuales en datos de clientes
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Anomalía detectada"""
    client_id: int
    client_name: str
    anomaly_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    suggested_action: str
    detected_at: datetime


class AnomalyDetector:
    """Detector de anomalías en comportamiento de clientes"""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.historical_averages = {}
        logger.info("✅ Anomaly Detector inicializado")

    def detect_anomalies(self, client_data: Dict, baseline: Optional[Dict] = None) -> List[Anomaly]:
        """
        Detectar anomalías en datos de un cliente

        Args:
            client_data: Datos actuales del cliente
            baseline: Datos históricos para comparación

        Returns:
            Lista de anomalías detectadas
        """
        anomalies = []

        # Anomalía 1: Cambio abrupto en audit score
        if baseline and 'audit_score' in baseline and 'audit_score' in client_data:
            anomaly = self._check_score_drop(
                client_data['id'],
                client_data.get('name', f"Client {client_data['id']}"),
                client_data['audit_score'],
                baseline['audit_score']
            )
            if anomaly:
                anomalies.append(anomaly)

        # Anomalía 2: Estancamiento en pipeline
        anomaly = self._check_pipeline_stagnation(client_data)
        if anomaly:
            anomalies.append(anomaly)

        # Anomalía 3: Falta de engagement sin acción
        anomaly = self._check_engagement_gap(client_data)
        if anomaly:
            anomalies.append(anomaly)

        # Anomalía 4: Rechazo repentino
        anomaly = self._check_rejection_pattern(client_data)
        if anomaly:
            anomalies.append(anomaly)

        # Anomalía 5: Patrón de abandono
        anomaly = self._check_abandonment_pattern(client_data)
        if anomaly:
            anomalies.append(anomaly)

        return anomalies

    def detect_batch(self, clients_data: List[Dict],
                    baselines: Optional[Dict[int, Dict]] = None) -> Dict[int, List[Anomaly]]:
        """Detectar anomalías para múltiples clientes"""
        results = {}
        baselines = baselines or {}

        for client_data in clients_data:
            client_id = client_data.get('id', 0)
            baseline = baselines.get(client_id)
            anomalies = self.detect_anomalies(client_data, baseline)
            if anomalies:
                results[client_id] = anomalies

        return results

    def _check_score_drop(self, client_id: int, client_name: str,
                         current_score: float, baseline_score: float) -> Optional[Anomaly]:
        """Detectar caída abrupta en audit score"""
        drop_percentage = ((baseline_score - current_score) / baseline_score) * 100 if baseline_score > 0 else 0

        if drop_percentage > 20:  # >20% drop
            severity = "CRITICAL" if drop_percentage > 40 else "HIGH"
            return Anomaly(
                client_id=client_id,
                client_name=client_name,
                anomaly_type="score_drop",
                severity=severity,
                description=f"⚠️ Audit score dropped {drop_percentage:.1f}% ({baseline_score:.0f} → {current_score:.0f})",
                suggested_action="Investigar qué cambió en el sitio. Contactar cliente para diagnóstico.",
                detected_at=datetime.utcnow()
            )
        return None

    def _check_pipeline_stagnation(self, client_data: Dict) -> Optional[Anomaly]:
        """Detectar estancamiento en pipeline"""
        stage = client_data.get('pipeline_stage', 'prospecto')
        days_in_stage = client_data.get('days_in_stage', 0)

        # Límites de tiempo normal por etapa
        stage_limits = {
            'prospecto': 14,    # 2 semanas
            'propuesta': 21,    # 3 semanas
            'negociacion': 30   # 4 semanas
        }

        limit = stage_limits.get(stage, 30)

        if days_in_stage > limit:
            excess_days = days_in_stage - limit
            severity = "CRITICAL" if excess_days > 30 else "HIGH" if excess_days > 14 else "MEDIUM"

            return Anomaly(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                anomaly_type="pipeline_stagnation",
                severity=severity,
                description=f"⏳ Cliente estancado en '{stage}' por {days_in_stage} días (límite: {limit})",
                suggested_action="Hacer follow-up urgente. Identificar objeciones o retrasos.",
                detected_at=datetime.utcnow()
            )

        return None

    def _check_engagement_gap(self, client_data: Dict) -> Optional[Anomaly]:
        """Detectar propuesta enviada pero sin engagement"""
        proposal_sent = client_data.get('proposal_sent', False)
        days_since_proposal = client_data.get('days_since_proposal', 0)
        email_opens = client_data.get('email_opens', 0)

        if proposal_sent and days_since_proposal > 7 and email_opens == 0:
            return Anomaly(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                anomaly_type="engagement_gap",
                severity="HIGH",
                description=f"📧 Propuesta no abierta hace {days_since_proposal} días",
                suggested_action="Reenviar propuesta con resumen ejecutivo. Hacer llamada confirmando recepción.",
                detected_at=datetime.utcnow()
            )

        return None

    def _check_rejection_pattern(self, client_data: Dict) -> Optional[Anomaly]:
        """Detectar patrón de rechazo"""
        status = client_data.get('status', '').lower()
        rejection_reason = client_data.get('rejection_reason', '')

        if status == 'rejected' or 'rechazado' in status:
            return Anomaly(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                anomaly_type="rejection",
                severity="CRITICAL",
                description=f"❌ Cliente rechazó propuesta: {rejection_reason}",
                suggested_action="Analizar razón de rechazo. Ofrecer alternativa más económica o diferentes servicios.",
                detected_at=datetime.utcnow()
            )

        return None

    def _check_abandonment_pattern(self, client_data: Dict) -> Optional[Anomaly]:
        """Detectar patrón de abandono sin contacto"""
        days_since_contact = client_data.get('days_since_contact', 0)
        status = client_data.get('status', '').lower()

        if (days_since_contact > 21 and
            status not in ['cerrado', 'closed', 'rechazado', 'rejected']):
            return Anomaly(
                client_id=client_data.get('id', 0),
                client_name=client_data.get('name', f"Client {client_data.get('id')}"),
                anomaly_type="abandonment",
                severity="HIGH",
                description=f"👻 Sin contacto hace {days_since_contact} días",
                suggested_action="Re-engagement campaign. Enviar contenido de valor, oferta especial o follow-up directo.",
                detected_at=datetime.utcnow()
            )

        return None

    def get_severity_score(self, anomalies: List[Anomaly]) -> int:
        """
        Calcular score de severidad total (0-100)
        """
        if not anomalies:
            return 0

        severity_weights = {
            'LOW': 10,
            'MEDIUM': 30,
            'HIGH': 60,
            'CRITICAL': 100
        }

        total_score = sum(severity_weights.get(a.severity, 0) for a in anomalies)
        # Normalizar a 0-100
        max_score = len(anomalies) * 100
        return min(100, int((total_score / max_score) * 100))

    def get_impact_summary(self, all_anomalies: Dict[int, List[Anomaly]]) -> Dict:
        """Resumen de impacto de anomalías en el sistema"""
        if not all_anomalies:
            return {
                'total_anomalies': 0,
                'affected_clients': 0,
                'critical_count': 0,
                'high_count': 0,
                'overall_health': 100
            }

        critical_anomalies = []
        high_anomalies = []
        total_anomalies = 0

        for client_id, anomalies in all_anomalies.items():
            total_anomalies += len(anomalies)
            for anomaly in anomalies:
                if anomaly.severity == 'CRITICAL':
                    critical_anomalies.append(anomaly)
                elif anomaly.severity == 'HIGH':
                    high_anomalies.append(anomaly)

        # Health score
        health = 100 - (len(critical_anomalies) * 20 + len(high_anomalies) * 10)
        health = max(0, health)

        return {
            'total_anomalies': total_anomalies,
            'affected_clients': len(all_anomalies),
            'critical_count': len(critical_anomalies),
            'high_count': len(high_anomalies),
            'overall_health': health,
            'critical_anomalies': critical_anomalies,
            'high_anomalies': high_anomalies
        }


def main():
    """Test del detector de anomalías"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║         ANOMALY DETECTOR - FASE 10 ADVANCED ANALYTICS                 ║
║              Detección de Patrones Inusuales                         ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    detector = AnomalyDetector()

    # Clientes con anomalías
    test_clients = [
        {
            'id': 1,
            'name': 'Tech Startup A',
            'audit_score': 45,  # Bajó de 85
            'pipeline_stage': 'negociacion',
            'days_in_stage': 40,  # Estancado
            'email_opens': 0,
            'proposal_sent': True,
            'days_since_proposal': 20,
            'status': 'active',
            'days_since_contact': 0
        },
        {
            'id': 2,
            'name': 'E-commerce B',
            'audit_score': 65,
            'pipeline_stage': 'propuesta',
            'days_in_stage': 8,
            'email_opens': 0,
            'proposal_sent': True,
            'days_since_proposal': 15,  # Sin abrir
            'status': 'active',
            'days_since_contact': 25
        },
        {
            'id': 3,
            'name': 'Rejected Client C',
            'audit_score': 50,
            'pipeline_stage': 'prospecto',
            'days_in_stage': 28,
            'status': 'rejected',
            'rejection_reason': 'Precio demasiado alto',
            'days_since_contact': 10
        }
    ]

    # Detectar anomalías
    print("\n🔍 ANOMALÍAS DETECTADAS:\n")
    all_anomalies = detector.detect_batch(test_clients)

    for client_id, anomalies in all_anomalies.items():
        print(f"Client ID: {client_id}")
        for anomaly in anomalies:
            print(f"  [{anomaly.severity}] {anomaly.anomaly_type.upper()}")
            print(f"    {anomaly.description}")
            print(f"    Acción: {anomaly.suggested_action}")
        print()

    # Resumen de impacto
    impact = detector.get_impact_summary(all_anomalies)
    print("\n📊 RESUMEN DE IMPACTO:\n")
    print(f"Clientes afectados: {impact['affected_clients']}")
    print(f"Total de anomalías: {impact['total_anomalies']}")
    print(f"Anomalías críticas: {impact['critical_count']}")
    print(f"Anomalías altas: {impact['high_count']}")
    print(f"Salud general: {impact['overall_health']}/100")


if __name__ == "__main__":
    main()
