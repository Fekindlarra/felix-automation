#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Orchestrator Service
Orquesta el flujo completo: Recibir → Analizar → PDF → Email
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from backend.services.hermes_analyzer import (
    AuditoryAnalyzer,
    AuditoriaData,
    InstagramMetrics
)
from backend.services.pdf_generator import PDFGenerator
from backend.services.brevo_email import (
    BrevoClient,
    AuditEmailGenerator
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# ORQUESTADOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

class AuditOrchestrator:
    """
    Orquesta el flujo completo de auditoría:
    1. Recibe datos de Make.com
    2. Analiza con Hermes LLM
    3. Genera PDF
    4. Envía por email con Brevo
    """

    def __init__(self):
        self.analyzer = AuditoryAnalyzer()
        self.pdf_generator = PDFGenerator()
        self.email_client = BrevoClient()

    async def process_audit(
        self,
        cliente_id: str,
        cliente_nombre: str,
        cliente_email: str,
        auditoria_id: str,
        auditoria_nombre: str,
        datos: Dict[str, Any],
        enviar_email: bool = True
    ) -> Dict[str, Any]:
        """
        Procesa una auditoría completa

        Args:
            cliente_id: ID del cliente
            cliente_nombre: Nombre del cliente
            cliente_email: Email para enviar reporte
            auditoria_id: ID de la auditoría
            auditoria_nombre: Nombre descriptivo de la auditoría
            datos: Dict con datos de Instagram/website
            enviar_email: Si enviar el reporte por email

        Returns:
            Dict con resultado del procesamiento
        """

        try:
            logger.info(f"🔄 Iniciando auditoría {auditoria_id} para {cliente_nombre}")

            # ═══════════════════════════════════════════════════════════
            # PASO 1: ANALIZAR CON HERMES
            # ═══════════════════════════════════════════════════════════

            logger.info(f"🧠 Analizando con Hermes...")

            # Convertir datos a AuditoriaData
            instagram_data = None
            if datos.get('instagram'):
                instagram_data = InstagramMetrics(**datos['instagram'])

            auditoria_data = AuditoriaData(
                cliente_id=cliente_id,
                auditoria_id=auditoria_id,
                instagram=instagram_data,
                website_metrics=datos.get('website_metrics'),
                otros_datos=datos.get('otros_datos')
            )

            # Analizar
            analysis = await self.analyzer.analyze_auditoria(auditoria_data)
            logger.info(f"✅ Análisis completado: score {analysis.score_general}")

            # ═══════════════════════════════════════════════════════════
            # PASO 2: GENERAR PDF
            # ═══════════════════════════════════════════════════════════

            logger.info(f"📄 Generando PDF...")

            pdf_bytes = self.pdf_generator.generate_audit_report(
                cliente_id=cliente_id,
                cliente_nombre=cliente_nombre,
                auditoria_id=auditoria_id,
                analysis=analysis.model_dump()
            )

            logger.info(f"✅ PDF generado: {len(pdf_bytes)} bytes")

            # ═══════════════════════════════════════════════════════════
            # PASO 3: ENVIAR EMAIL (OPCIONAL)
            # ═══════════════════════════════════════════════════════════

            email_result = None
            if enviar_email:
                logger.info(f"📧 Enviando email a {cliente_email}...")

                email = AuditEmailGenerator.build_audit_email(
                    cliente_email=cliente_email,
                    cliente_nombre=cliente_nombre,
                    auditoria_nombre=auditoria_nombre,
                    pdf_bytes=pdf_bytes,
                    score=analysis.score_general
                )

                email_result = await self.email_client.send_email(email)
                logger.info(f"✅ Email enviado: {email_result.get('message_id')}")

            # ═══════════════════════════════════════════════════════════
            # RESULTADO FINAL
            # ═══════════════════════════════════════════════════════════

            resultado = {
                "status": "success",
                "auditoria_id": auditoria_id,
                "cliente_id": cliente_id,
                "timestamp": datetime.utcnow().isoformat(),
                "steps_completed": {
                    "hermes_analysis": True,
                    "pdf_generation": True,
                    "email_sent": email_result is not None
                },
                "analysis": {
                    "score_general": analysis.score_general,
                    "resumen_ejecutivo": analysis.resumen_ejecutivo,
                    "hallazgos": len(analysis.hallazgos_principales),
                    "recomendaciones": len(analysis.recomendaciones)
                },
                "pdf_size_bytes": len(pdf_bytes),
                "email_message_id": email_result.get('message_id') if email_result else None
            }

            logger.info(f"✅ Auditoría completada exitosamente: {auditoria_id}")
            return resultado

        except Exception as e:
            logger.error(f"❌ Error en auditoría {auditoria_id}: {str(e)}")
            return {
                "status": "error",
                "auditoria_id": auditoria_id,
                "cliente_id": cliente_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    async def close(self):
        """Cierra todas las conexiones"""
        await self.analyzer.close()
        await self.email_client.close()

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE PRUEBA
# ═══════════════════════════════════════════════════════════════════════════

async def test_full_audit_flow():
    """Test del flujo completo de auditoría"""

    orchestrator = AuditOrchestrator()

    # Datos de prueba
    datos = {
        "instagram": {
            "followers": 2500,
            "engagement_rate": 4.5,
            "reach_daily": 650,
            "impressions": 3200,
            "posts_created": 15,
            "stories_views": 1200,
            "comments": 65,
            "likes": 450
        }
    }

    try:
        print("🚀 Iniciando flujo completo de auditoría...")
        print("=" * 60)

        resultado = await orchestrator.process_audit(
            cliente_id="luz-agencia-001",
            cliente_nombre="Luz Agencia",
            cliente_email="felipe@enbuenamesa.com",
            auditoria_id="audit-test-20261021",
            auditoria_nombre="Luz Agencia Instagram Audit",
            datos=datos,
            enviar_email=False  # Desactivar para test
        )

        print("\n📊 RESULTADO:")
        print("=" * 60)
        import json
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await orchestrator.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_full_audit_flow())
