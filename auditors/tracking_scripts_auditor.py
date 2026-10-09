#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tracking Scripts Auditor - Detecta y valida scripts de tracking
Detecta: Google Tag Manager, Google Analytics 4, Facebook Pixel, Hotjar, etc.
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime
from html.parser import HTMLParser


class TrackingScriptParser(HTMLParser):
    """Parseador para detectar scripts de tracking en HTML"""

    def __init__(self):
        super().__init__()
        self.scripts = []
        self.gtm_script = None
        self.ga_script = None
        self.ga_measurement_id = None
        self.facebook_pixel = None
        self.hotjar_script = None
        self.clarity_script = None
        self.other_tracking = []
        self._en_script = False
        self._texto_script = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "script":
            self._en_script = True
            self._texto_script = ""
            src = attrs_dict.get("src", "")
            if src:
                self.scripts.append(src)
                self._classify_script(src, attrs_dict)

    def handle_data(self, data):
        if getattr(self, "_en_script", False):
            self._texto_script += data

    def handle_endtag(self, tag):
        if tag == "script" and getattr(self, "_en_script", False):
            self._en_script = False
            self._clasificar_inline(self._texto_script)

    def _clasificar_inline(self, texto: str):
        """Scripts inline: GTM estándar y Pixel cargado con JavaScript."""
        # Snippet estándar de GTM: el ID va como argumento, la URL se arma en JS.
        if "gtm.start" in texto and self.gtm_script is None:
            m = re.search(r"['\"](GTM-[A-Z0-9]{4,})['\"]", texto)
            if m:
                self.gtm_script = {"src": "inline", "id": m.group(1)}
        # Pixel de Facebook armado con JavaScript.
        if "fbevents.js" in texto and self.facebook_pixel is None:
            self.facebook_pixel = "inline"

    def _classify_script(self, src: str, attrs: Dict):
        """Clasifica el script según su origen"""

        # Google Tag Manager
        if "googletagmanager.com/gtm.js" in src:
            self.gtm_script = src
            # Extrae el GTM ID (GTM-XXXXX)
            match = re.search(r'id=([A-Z0-9-]+)', src)
            if match:
                self.gtm_script = {"src": src, "id": match.group(1)}

        # Google Analytics 4
        elif "googletagmanager.com/gtag/js" in src:
            self.ga_script = src
            match = re.search(r'id=([A-Z0-9-]+)', src)
            if match:
                self.ga_measurement_id = match.group(1)
                self.ga_script = {"src": src, "id": match.group(1)}

        # Facebook Pixel
        elif "connect.facebook.net" in src or "facebook.com/en_US/fbevents.js" in src:
            self.facebook_pixel = src

        # Hotjar
        elif "hotjar.com" in src:
            self.hotjar_script = src

        # Microsoft Clarity
        elif "clarity.ms" in src:
            self.clarity_script = src

        # Otros scripts de tracking conocidos
        elif any(provider in src for provider in ["segment", "mixpanel", "amplitude", "heap", "intercom"]):
            self.other_tracking.append(src)


class TrackingScriptsAuditor:
    """Auditor especializado en scripts de tracking"""

    def __init__(self):
        self.platform = "tracking"
        self.audit_date = datetime.now().isoformat()
        self.findings = []
        self.score = 0

    def audit(self, site_data: Dict) -> Dict:
        """
        Auditar scripts de tracking en el sitio

        Args:
            site_data: {
                'url': str,
                'html_content': str
            }
        """
        url = site_data.get('url', '')
        html = site_data.get('html_content', '')

        # Parse HTML para detectar scripts
        parser = TrackingScriptParser()
        try:
            parser.feed(html)
        except Exception as e:
            self.findings.append({
                "severity": "ERROR",
                "title": "Error al parsear HTML",
                "description": str(e)
            })
            return self._generate_report()

        # Evaluar tracking setup
        self._evaluate_gtm(parser)
        self._evaluate_ga(parser)
        self._evaluate_facebook_pixel(parser)
        self._evaluate_tracking_completeness(parser)

        # Calcular score
        self.score = self._calculate_score(parser)

        return self._generate_report()

    def _evaluate_gtm(self, parser: TrackingScriptParser):
        """Evalúa Google Tag Manager"""

        if parser.gtm_script:
            if isinstance(parser.gtm_script, dict):
                gtm_id = parser.gtm_script.get("id", "")
                self.findings.append({
                    "severity": "SUCCESS",
                    "title": "✅ Google Tag Manager Detectado",
                    "description": f"GTM instalado correctamente con ID: {gtm_id}",
                    "gtm_id": gtm_id,
                    "category": "tracking"
                })
            else:
                self.findings.append({
                    "severity": "WARNING",
                    "title": "⚠️ Google Tag Manager Sin ID",
                    "description": "GTM detectado pero no se pudo extraer el ID",
                    "category": "tracking"
                })
        else:
            self.findings.append({
                "severity": "CRITICAL",
                "title": "❌ Google Tag Manager NO Detectado",
                "description": "No hay script de GTM en el sitio. Se recomienda instalarlo para mejor tracking.",
                "impact": "Sin GTM, no hay tracking centralizado de eventos.",
                "category": "tracking"
            })

    def _evaluate_ga(self, parser: TrackingScriptParser):
        """Evalúa Google Analytics 4"""

        if parser.ga_script:
            if isinstance(parser.ga_script, dict):
                ga_id = parser.ga_script.get("id", "")
                self.findings.append({
                    "severity": "SUCCESS",
                    "title": "✅ Google Analytics 4 Detectado",
                    "description": f"GA4 instalado correctamente con ID: {ga_id}",
                    "ga_id": ga_id,
                    "category": "analytics"
                })
            else:
                self.findings.append({
                    "severity": "WARNING",
                    "title": "⚠️ Google Analytics Sin ID",
                    "description": "GA detectado pero no se pudo extraer el ID",
                    "category": "analytics"
                })
        else:
            self.findings.append({
                "severity": "HIGH",
                "title": "❌ Google Analytics NO Detectado",
                "description": "No hay script de GA4. Se recomienda agregarlo para analytics.",
                "impact": "Sin GA, no hay datos de tráfico y comportamiento del usuario.",
                "category": "analytics"
            })

    def _evaluate_facebook_pixel(self, parser: TrackingScriptParser):
        """Evalúa Facebook Pixel"""

        if parser.facebook_pixel:
            self.findings.append({
                "severity": "SUCCESS",
                "title": "✅ Facebook Pixel Detectado",
                "description": "Facebook Pixel instalado correctamente",
                "category": "conversion_tracking"
            })
        else:
            self.findings.append({
                "severity": "MEDIUM",
                "title": "⚠️ Facebook Pixel NO Detectado",
                "description": "No hay Facebook Pixel. Recomendado para e-commerce y conversiones.",
                "impact": "Sin Facebook Pixel, no se pueden trackear conversiones en Facebook Ads.",
                "category": "conversion_tracking"
            })

    def _evaluate_tracking_completeness(self, parser: TrackingScriptParser):
        """Evalúa si hay otros scripts de tracking"""

        tracking_count = sum([
            1 if parser.gtm_script else 0,
            1 if parser.ga_script else 0,
            1 if parser.facebook_pixel else 0,
            1 if parser.hotjar_script else 0,
            1 if parser.clarity_script else 0,
            len(parser.other_tracking)
        ])

        if tracking_count >= 3:
            self.findings.append({
                "severity": "SUCCESS",
                "title": "✅ Tracking Setup Completo",
                "description": f"Hay {tracking_count} sistemas de tracking activos. Buen coverage.",
                "tracking_count": tracking_count,
                "category": "completeness"
            })
        elif tracking_count == 2:
            self.findings.append({
                "severity": "INFO",
                "title": "ℹ️ Tracking Setup Básico",
                "description": f"Hay {tracking_count} sistemas de tracking. Se puede mejorar agregando más.",
                "tracking_count": tracking_count,
                "category": "completeness"
            })
        else:
            self.findings.append({
                "severity": "HIGH",
                "title": "❌ Tracking Setup Insuficiente",
                "description": f"Solo hay {tracking_count} sistema(s) de tracking. Se recomienda agregar más.",
                "tracking_count": tracking_count,
                "category": "completeness"
            })

        # Otros tracking encontrados
        if parser.hotjar_script:
            self.findings.append({
                "severity": "INFO",
                "title": "ℹ️ Hotjar Detectado",
                "description": "Hotjar instalado para session recording y heatmaps",
                "category": "additional"
            })

        if parser.clarity_script:
            self.findings.append({
                "severity": "INFO",
                "title": "ℹ️ Microsoft Clarity Detectado",
                "description": "Microsoft Clarity instalado para analytics",
                "category": "additional"
            })

        if parser.other_tracking:
            dominio_pattern = re.compile(r'([^/]+\.com|[^/]+\.net)')
            nombres = []
            for s in parser.other_tracking:
                m = dominio_pattern.search(s)
                nombres.append(m.group(1) if m else s)
            self.findings.append({
                "severity": "INFO",
                "title": f"ℹ️ {len(parser.other_tracking)} Script(s) de Tracking Adicional(es)",
                "description": f"Scripts detectados: {', '.join(nombres)}",
                "category": "additional"
            })

    def _calculate_score(self, parser: TrackingScriptParser) -> int:
        """Calcula score de tracking (0-100)"""

        score = 0

        # GTM es crítico: 40 puntos
        if parser.gtm_script:
            score += 40

        # GA4 es importante: 30 puntos
        if parser.ga_script:
            score += 30

        # Facebook Pixel: 15 puntos
        if parser.facebook_pixel:
            score += 15

        # Otros scripts: 15 puntos
        other_count = sum([
            1 if parser.hotjar_script else 0,
            1 if parser.clarity_script else 0,
            min(len(parser.other_tracking), 2)  # máx 2
        ])
        score += min(other_count * 5, 15)

        return min(score, 100)

    def _generate_report(self) -> Dict:
        """Genera el reporte de auditoría"""

        return {
            "platform": self.platform,
            "score": self.score,
            "audit_date": self.audit_date,
            "findings": self.findings,
            "summary": {
                "total_findings": len(self.findings),
                "critical_count": len([f for f in self.findings if f.get("severity") == "CRITICAL"]),
                "high_count": len([f for f in self.findings if f.get("severity") == "HIGH"]),
                "medium_count": len([f for f in self.findings if f.get("severity") == "MEDIUM"]),
                "success_count": len([f for f in self.findings if f.get("severity") == "SUCCESS"])
            }
        }


def audit_tracking_scripts(url: str, html_content: str) -> Dict:
    """Función helper para auditar scripts de tracking"""
    auditor = TrackingScriptsAuditor()
    return auditor.audit({"url": url, "html_content": html_content})
