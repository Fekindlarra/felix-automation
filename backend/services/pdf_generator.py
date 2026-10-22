#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Generator Service
Convierte análisis de Hermes a reportes PDF profesionales
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
from typing import Dict, Any, Optional, List
from io import BytesIO
import os

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

FONT_COLOR = colors.HexColor("#1f2937")
ACCENT_COLOR = colors.HexColor("#f59e0b")  # Naranja
PRIMARY_COLOR = colors.HexColor("#3b82f6")  # Azul
SUCCESS_COLOR = colors.HexColor("#10b981")  # Verde
WARNING_COLOR = colors.HexColor("#ef4444")  # Rojo

# ═══════════════════════════════════════════════════════════════════════════
# ESTILOS PERSONALIZADOS
# ═══════════════════════════════════════════════════════════════════════════

def get_custom_styles():
    """Retorna estilos personalizados para el reporte"""
    styles = getSampleStyleSheet()

    # Título principal
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    ))

    # Subtítulo
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=FONT_COLOR,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    ))

    # Heading de sección
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold',
        borderColor=ACCENT_COLOR,
        borderWidth=1,
        borderPadding=6,
        backColor=colors.HexColor("#f0f9ff")
    ))

    # Texto normal
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=FONT_COLOR,
        spaceAfter=8,
        leading=14,
        alignment=TA_JUSTIFY
    ))

    # Hallazgo
    styles.add(ParagraphStyle(
        name='Finding',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#dc2626"),
        spaceAfter=6,
        leftIndent=20,
        fontName='Helvetica-Bold'
    ))

    # Recomendación
    styles.add(ParagraphStyle(
        name='Recommendation',
        parent=styles['Normal'],
        fontSize=10,
        textColor=SUCCESS_COLOR,
        spaceAfter=6,
        leftIndent=20,
        fontName='Helvetica-Bold'
    ))

    return styles

# ═══════════════════════════════════════════════════════════════════════════
# COMPONENTES PERSONALIZADOS
# ═══════════════════════════════════════════════════════════════════════════

class ScoreCard(Flowable):
    """Card que muestra el score general"""

    def __init__(self, score: float, width=200, height=150):
        super().__init__()
        self.score = score
        self.width = width
        self.height = height

    def draw(self):
        """Dibuja el card de score"""
        canvas = self.canv

        # Fondo
        canvas.setFillColor(colors.HexColor("#f3f4f6"))
        canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Borde
        canvas.setStrokeColor(PRIMARY_COLOR)
        canvas.setLineWidth(2)
        canvas.rect(0, 0, self.width, self.height)

        # Círculo del score
        center_x = self.width / 2
        center_y = self.height / 2
        radius = 35

        # Fondo del círculo
        if self.score >= 70:
            canvas.setFillColor(SUCCESS_COLOR)
        elif self.score >= 50:
            canvas.setFillColor(ACCENT_COLOR)
        else:
            canvas.setFillColor(WARNING_COLOR)

        canvas.circle(center_x, center_y, radius, fill=1, stroke=0)

        # Texto del score
        canvas.setFont("Helvetica-Bold", 28)
        canvas.setFillColor(colors.white)
        canvas.drawCentredString(center_x, center_y + 5, f"{self.score:.1f}")

        # Etiqueta
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(FONT_COLOR)
        canvas.drawCentredString(center_x, 15, "SCORE GENERAL")

    def wrap(self, *args):
        return self.width, self.height

# ═══════════════════════════════════════════════════════════════════════════
# GENERADOR DE PDFs
# ═══════════════════════════════════════════════════════════════════════════

class PDFGenerator:
    """Genera PDFs profesionales de auditorías"""

    def __init__(self):
        self.styles = get_custom_styles()

    def generate_audit_report(
        self,
        cliente_id: str,
        cliente_nombre: str,
        auditoria_id: str,
        analysis: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Genera un reporte PDF completo de auditoría

        Args:
            cliente_id: ID del cliente
            cliente_nombre: Nombre del cliente (para mostrar)
            auditoria_id: ID de la auditoría
            analysis: Datos de análisis de Hermes
            output_path: Ruta para guardar el PDF (opcional)

        Returns:
            Bytes del PDF generado
        """

        # Crear documento en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )

        # Contenido
        elements = []

        # ═══════════════════════════════════════════════════════════════
        # ENCABEZADO
        # ═══════════════════════════════════════════════════════════════

        elements.extend(self._build_header(cliente_nombre, auditoria_id))
        elements.append(Spacer(1, 0.3*inch))

        # ═══════════════════════════════════════════════════════════════
        # RESUMEN EJECUTIVO
        # ═══════════════════════════════════════════════════════════════

        elements.append(Paragraph("RESUMEN EJECUTIVO", self.styles['SectionHeading']))

        resumen = analysis.get('resumen_ejecutivo', 'Sin información')
        elements.append(Paragraph(resumen, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.2*inch))

        # Score card
        score = analysis.get('score_general', 0)
        elements.append(ScoreCard(score, width=200, height=120))
        elements.append(Spacer(1, 0.3*inch))

        # ═══════════════════════════════════════════════════════════════
        # HALLAZGOS PRINCIPALES
        # ═══════════════════════════════════════════════════════════════

        elementos_hallazgos = []
        elementos_hallazgos.append(Paragraph("HALLAZGOS PRINCIPALES", self.styles['SectionHeading']))

        hallazgos = analysis.get('hallazgos_principales', [])
        if hallazgos:
            for i, hallazgo in enumerate(hallazgos, 1):
                texto = f"{i}. {hallazgo}"
                elementos_hallazgos.append(Paragraph(texto, self.styles['Finding']))
        else:
            elementos_hallazgos.append(Paragraph("Sin hallazgos destacados.", self.styles['CustomBody']))

        elementos_hallazgos.append(Spacer(1, 0.2*inch))
        elements.extend(elementos_hallazgos)

        # ═══════════════════════════════════════════════════════════════
        # RECOMENDACIONES
        # ═══════════════════════════════════════════════════════════════

        elementos_recom = []
        elementos_recom.append(Paragraph("RECOMENDACIONES", self.styles['SectionHeading']))

        recomendaciones = analysis.get('recomendaciones', [])
        if recomendaciones:
            for i, recom in enumerate(recomendaciones, 1):
                texto = f"{i}. {recom}"
                elementos_recom.append(Paragraph(texto, self.styles['Recommendation']))
        else:
            elementos_recom.append(Paragraph("Sin recomendaciones.", self.styles['CustomBody']))

        elementos_recom.append(Spacer(1, 0.2*inch))
        elements.extend(elementos_recom)

        # ═══════════════════════════════════════════════════════════════
        # PRÓXIMOS PASOS
        # ═══════════════════════════════════════════════════════════════

        elementos_pasos = []
        elementos_pasos.append(Paragraph("PRÓXIMOS PASOS", self.styles['SectionHeading']))

        pasos = analysis.get('proximos_pasos', [])
        if pasos:
            for i, paso in enumerate(pasos, 1):
                texto = f"{i}. {paso}"
                elementos_pasos.append(Paragraph(texto, self.styles['CustomBody']))
        else:
            elementos_pasos.append(Paragraph("Sin pasos adicionales.", self.styles['CustomBody']))

        elementos_pasos.append(Spacer(1, 0.3*inch))
        elements.extend(elementos_pasos)

        # ═══════════════════════════════════════════════════════════════
        # DETALLES TÉCNICOS
        # ═══════════════════════════════════════════════════════════════

        elementos_detalles = []
        elementos_detalles.append(Paragraph("DETALLES TÉCNICOS", self.styles['SectionHeading']))

        detalles = analysis.get('detalles_por_metrica', {})
        if detalles:
            for metrica, datos in detalles.items():
                titulo = f"📊 {metrica.upper()}"
                elementos_detalles.append(Paragraph(titulo, self.styles['Heading2']))

                if isinstance(datos, dict):
                    for clave, valor in datos.items():
                        texto = f"• <b>{clave.replace('_', ' ').title()}:</b> {str(valor)}"
                        elementos_detalles.append(Paragraph(texto, self.styles['CustomBody']))

        elementos_detalles.append(Spacer(1, 0.3*inch))
        elements.extend(elementos_detalles)

        # ═══════════════════════════════════════════════════════════════
        # FOOTER
        # ═══════════════════════════════════════════════════════════════

        elements.append(PageBreak())
        footer_elements = self._build_footer(auditoria_id, analysis.get('timestamp', ''))
        if footer_elements:
            elements.extend(footer_elements)

        # Generar PDF
        doc.build(elements)

        # Obtener bytes
        pdf_bytes = buffer.getvalue()

        # Guardar a archivo si se especifica ruta
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def _build_header(self, cliente_nombre: str, auditoria_id: str) -> List:
        """Construye el encabezado del reporte"""

        elementos = []

        # Logo/Título de Felix
        elementos.append(Paragraph("📊 FELIX AUDITORÍAS AUTOMÁTICAS", self.styles['CustomTitle']))

        # Información del cliente
        info_table_data = [
            [
                f"<b>Cliente:</b> {cliente_nombre}",
                f"<b>Auditoría:</b> {auditoria_id}"
            ],
            [
                f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                f"<b>Status:</b> <font color=green>✓ Completada</font>"
            ]
        ]

        info_table = Table(info_table_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), FONT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb"))
        ]))

        elementos.append(info_table)

        return elementos

    def _build_footer(self, auditoria_id: str, timestamp: str) -> List:
        """Construye el footer del reporte"""

        elementos = []

        # Línea separadora
        elementos.append(Paragraph("_" * 80, self.styles['Normal']))
        elementos.append(Spacer(1, 0.1*inch))

        # Información del footer
        footer_text = f"""
        <font size=8>
        <b>Felix Auditorías Automáticas</b><br/>
        Reporte generado automáticamente el {datetime.now().strftime('%d de %B de %Y')} a las {datetime.now().strftime('%H:%M')}<br/>
        Auditoría ID: {auditoria_id}<br/>
        <br/>
        <i>Este reporte fue generado por un sistema automático de análisis. Para más información,
        contacta a tu gestor de auditorías.</i><br/>
        <br/>
        © 2026 Felix - Auditorías Automáticas. Todos los derechos reservados.
        </font>
        """

        elementos.append(Paragraph(footer_text, self.styles['Normal']))

        return elementos

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE PRUEBA
# ═══════════════════════════════════════════════════════════════════════════

async def test_pdf_generation():
    """Test del generador de PDFs"""

    # Datos de ejemplo
    sample_analysis = {
        "resumen_ejecutivo": "Instagram de Luz Agencia muestra un crecimiento consistente con buenas tasas de engagement. Se recomienda mantener la frecuencia de posts y aumentar la variedad de contenido.",
        "hallazgos_principales": [
            "Engagement rate de 3.2% es competitivo para el sector",
            "Alcance diario de 450 es bajo considerando 1500 seguidores",
            "Stories tienen mayor engagement que feed",
            "Comentarios son bajos respecto a likes (imbalance)"
        ],
        "recomendaciones": [
            "Aumentar frecuencia de stories a 3-5 por día",
            "Usar más calls-to-action en captions para aumentar comentarios",
            "Crear contenido interactivo (polls, quizzes) en stories",
            "Colaborar con influencers locales en Santiago"
        ],
        "score_general": 72.5,
        "detalles_por_metrica": {
            "instagram": {
                "followers": "1500",
                "engagement_rate": "3.2%",
                "reach_daily": "450",
                "impressions": "2000",
                "posts": "12",
                "stories_views": "800"
            }
        },
        "proximos_pasos": [
            "Implementar plan de contenido optimizado para próximas 2 semanas",
            "Aumentar presupuesto de ads en Instagram a $200/semana",
            "Hacer seguimiento a métricas cada semana",
            "Reportar resultados mensualmente"
        ],
        "timestamp": datetime.now().isoformat()
    }

    generator = PDFGenerator()

    print("🔄 Generando PDF de prueba...")

    pdf_bytes = generator.generate_audit_report(
        cliente_id="luz-agencia-001",
        cliente_nombre="Luz Agencia",
        auditoria_id="audit-20261021-001",
        analysis=sample_analysis,
        output_path="/tmp/test_auditoria.pdf"
    )

    print(f"✅ PDF generado: {len(pdf_bytes)} bytes")
    print(f"📄 Guardado en: /tmp/test_auditoria.pdf")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pdf_generation())
