#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lead Scorer Agent
Califica leads por potencial de venta usando auditorías multi-plataforma
"""

import sys
import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import FelixAutomationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ponderaciones para scoring
SCORING_WEIGHTS = {
    "web_score": 0.40,
    "facebook_score": 0.20,
    "google_score": 0.20,
    "business_type": 0.10,
    "company_size": 0.10
}

# Mapeo de factores
BUSINESS_TYPE_SCORES = {
    "ecommerce": 95,
    "saas": 90,
    "services": 80,
    "plants": 75,
    "education": 70
}

COMPANY_SIZE_SCORES = {
    "startup": 60,
    "pyme": 85,
    "mediana": 90,
    "grande": 70
}


class LeadScorerAgent:
    """Agente que califica leads automáticamente"""

    def __init__(self, orchestrator: FelixAutomationOrchestrator):
        self.orchestrator = orchestrator
        self.scores = []
        logger.info("✅ Lead Scorer Agent inicializado")

    def score_all_leads(self) -> List[Dict]:
        """Calificar todos los leads en el sistema"""
        logger.info("🎯 Iniciando scoring de todos los leads...")

        clients = self.orchestrator.list_clients()
        self.scores = []

        for client in clients:
            score_result = self.score_lead(client.id)
            self.scores.append(score_result)

            # Guardar en BD
            self.orchestrator.save_lead_score(
                client.id,
                score_result['web_score'],
                score_result['facebook_score'],
                score_result['google_score'],
                score_result['overall_score'],
                score_result['ranking']
            )

        # Ordenar por score descendente
        self.scores.sort(key=lambda x: x['overall_score'], reverse=True)

        logger.info(f"✅ Scored {len(self.scores)} leads")

        return self.scores

    def score_lead(self, client_id: int) -> Dict:
        """Calcular score de un lead individual"""
        client = self.orchestrator.get_client(client_id)
        audits = self.orchestrator.get_client_audits(client_id)

        # Extraer scores por plataforma
        web_score = 0
        facebook_score = 0
        google_score = 0

        for audit in audits:
            if audit.platform == 'web':
                web_score = audit.overall_score or 0
            elif audit.platform == 'facebook_ads':
                facebook_score = audit.overall_score or 0
            elif audit.platform == 'google_ads':
                google_score = audit.overall_score or 0

        # Calcular factores
        business_type_score = BUSINESS_TYPE_SCORES.get(client.business_type, 60)
        company_size_score = COMPANY_SIZE_SCORES.get(client.company_size, 75)

        # Aplicar pesos
        overall_score = int(
            (web_score * SCORING_WEIGHTS['web_score']) +
            (facebook_score * SCORING_WEIGHTS['facebook_score']) +
            (google_score * SCORING_WEIGHTS['google_score']) +
            (business_type_score * SCORING_WEIGHTS['business_type']) +
            (company_size_score * SCORING_WEIGHTS['company_size'])
        )

        # Determinar ranking
        if overall_score >= 80:
            ranking = "🟢 ALTO"
        elif overall_score >= 60:
            ranking = "🟡 MEDIO"
        else:
            ranking = "🔴 BAJO"

        return {
            "client_id": client_id,
            "client_name": client.name,
            "email": client.email,
            "business_type": client.business_type,
            "company_size": client.company_size,
            "web_score": web_score,
            "facebook_score": facebook_score,
            "google_score": google_score,
            "overall_score": overall_score,
            "ranking": ranking,
            "recommendation": self._get_recommendation(overall_score, web_score, facebook_score, google_score)
        }

    def _get_recommendation(self, overall: int, web: int, fb: int, google: int) -> str:
        """Generar recomendación personalizada"""
        weaknesses = []

        if web < 60:
            weaknesses.append("Sitio web necesita mejoras urgentes")
        if fb < 40:
            weaknesses.append("Facebook Ads sin configurar")
        if google < 40:
            weaknesses.append("Google Ads optimización necesaria")

        if overall >= 80:
            return "Contacto inmediato - Alto potencial - Prioridad 1"
        elif overall >= 60:
            if weaknesses:
                return f"Follow-up en 2 semanas - Área débil: {weaknesses[0]}"
            return "Contacto estándar - Potencial medio"
        else:
            return "Nutrir lead - Revisar en 1 mes"

    def export_csv(self, filename: str = "data/leads_scored.csv"):
        """Exportar scores a CSV"""
        Path(filename).parent.mkdir(exist_ok=True)

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'client_id', 'client_name', 'email', 'business_type', 'company_size',
                'web_score', 'facebook_score', 'google_score', 'overall_score',
                'ranking', 'recommendation'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.scores)

        logger.info(f"✅ Leads exportados a: {filename}")
        return filename

    def get_high_potential_leads(self, min_score: int = 75) -> List[Dict]:
        """Obtener leads con alto potencial"""
        high_potential = [s for s in self.scores if s['overall_score'] >= min_score]
        logger.info(f"🎯 {len(high_potential)} leads con score >= {min_score}")
        return high_potential

    def get_scoring_report(self) -> str:
        """Generar reporte de scoring"""
        if not self.scores:
            return "❌ No hay scores. Ejecuta score_all_leads() primero."

        # Estadísticas
        total = len(self.scores)
        alto = sum(1 for s in self.scores if '🟢' in s['ranking'])
        medio = sum(1 for s in self.scores if '🟡' in s['ranking'])
        bajo = sum(1 for s in self.scores if '🔴' in s['ranking'])

        avg_score = sum(s['overall_score'] for s in self.scores) / total if total > 0 else 0

        report = f"""
╔════════════════════════════════════════════════════════════════╗
║             REPORTE DE LEAD SCORING                           ║
║               {datetime.now().strftime('%d/%m/%Y %H:%M')}
╚════════════════════════════════════════════════════════════════╝

📊 ESTADÍSTICAS:
   • Total de leads: {total}
   • Score promedio: {avg_score:.1f}/100

🎯 DISTRIBUCIÓN:
   • 🟢 Alto potencial (>=80): {alto} leads ({alto/total*100:.1f}%)
   • 🟡 Medio potencial (60-79): {medio} leads ({medio/total*100:.1f}%)
   • 🔴 Bajo potencial (<60): {bajo} leads ({bajo/total*100:.1f}%)

🏆 TOP 5 LEADS:
"""

        for i, score in enumerate(self.scores[:5], 1):
            report += f"\n   {i}. {score['client_name']} ({score['email']})"
            report += f"\n      Score: {score['overall_score']}/100 {score['ranking']}"
            report += f"\n      Recomendación: {score['recommendation']}\n"

        return report


def main():
    """Testing del agente"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║            LEAD SCORER AGENT                                  ║
║    Califica leads por potencial de venta                      ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Conectar orquestador
    orchestrator = FelixAutomationOrchestrator()
    orchestrator.connect_database()

    # Crear agente
    agent = LeadScorerAgent(orchestrator)

    # Score todos los leads
    print("\n🎯 CALIFICANDO TODOS LOS LEADS...")
    all_scores = agent.score_all_leads()

    # Mostrar reporte
    print(agent.get_scoring_report())

    # Exportar CSV
    print("\n💾 Exportando resultados...")
    csv_file = agent.export_csv()
    print(f"✅ Archivo generado: {csv_file}")

    # Mostrar alto potencial
    print("\n🏆 LEADS CON ALTO POTENCIAL:")
    high_potential = agent.get_high_potential_leads(75)
    for lead in high_potential:
        print(f"\n  • {lead['client_name']}")
        print(f"    Email: {lead['email']}")
        print(f"    Score: {lead['overall_score']}/100")
        print(f"    Ranking: {lead['ranking']}")

    # Guardar scores en BD
    print("\n💾 Guardando scores en base de datos...")
    orchestrator.log_agent_action(
        "LeadScorerAgent",
        "score_all_leads",
        "success",
        details=f"Scored {len(all_scores)} leads"
    )

    orchestrator.close_database()
    print("\n✅ Lead Scoring completado")


if __name__ == "__main__":
    main()
