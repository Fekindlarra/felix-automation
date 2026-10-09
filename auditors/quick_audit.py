#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Audit - Análisis rápido en 30 segundos
Para demos y pruebas rápidas sin credenciales
"""

import json
import re
import logging
import requests
from typing import Dict, List
from datetime import datetime
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class QuickHTMLParser(HTMLParser):
    """Parser rápido para extraer meta datos relevantes"""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.h1_count = 0
        self.img_count = 0
        self.has_mobile_viewport = False
        self.has_ssl = False
        self.scripts = []
        self.in_head = False
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'head':
            self.in_head = True
        elif tag == 'title' and self.in_head:
            # Solo el <title> dentro de <head> cuenta (un <title> en <body> se ignora)
            self._in_title = True
        elif tag == 'meta':
            if attrs_dict.get('name') == 'viewport':
                self.has_mobile_viewport = True
            elif attrs_dict.get('name') == 'description':
                self.description = attrs_dict.get('content', '')
        elif tag == 'h1':
            self.h1_count += 1
        elif tag == 'img':
            self.img_count += 1
        elif tag == 'script':
            src = attrs_dict.get('src', '')
            if src:
                self.scripts.append(src)

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False
        elif tag == 'title':
            self._in_title = False
            self.title = self.title.strip()


class QuickAuditor:
    """Auditor rápido para demos y pruebas"""

    def __init__(self):
        self.audit_date = datetime.now().isoformat()
        self.findings = []
        self.score = 0

    def audit(self, website_url: str) -> Dict:
        """
        Ejecutar auditoría rápida de un sitio

        Args:
            website_url: URL a auditar

        Returns:
            Dict con hallazgos rápidos
        """

        # Normalizar URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url

        try:
            # 1. Fetch HTML
            response = requests.get(website_url, timeout=10)
            response.raise_for_status()
            html = response.text
            page_size = len(response.content)

        except requests.exceptions.Timeout:
            return self._timeout_response()
        except Exception as e:
            return self._error_response(str(e))

        return self.analizar_html(website_url, html, page_size)

    def analizar_html(self, website_url: str, html: str, page_size: int) -> Dict:
        """Analiza un HTML ya descargado (sin red)."""
        # 2. Parse HTML
        parser = QuickHTMLParser()
        try:
            parser.feed(html)
        except Exception as e:
            logger.warning(f"Error parsing HTML: {e}")

        # 3. Análisis rápido
        self.findings = []
        self.score = 50  # Baseline

        # Check: Mobile Viewport
        if parser.has_mobile_viewport:
            self.findings.append({
                "severity": "success",
                "title": "✅ Responsive Design",
                "description": "El sitio está optimizado para móvil"
            })
            self.score += 15
        else:
            self.findings.append({
                "severity": "critical",
                "title": "❌ No es mobile-friendly",
                "description": "Falta viewport meta tag. El sitio no se ve bien en celulares"
            })
            self.score -= 10

        # Check: SSL/HTTPS
        has_ssl = website_url.startswith('https')
        if has_ssl:
            self.findings.append({
                "severity": "success",
                "title": "✅ Conexión Segura (HTTPS)",
                "description": "Tu sitio usa SSL - Google lo favorece"
            })
            self.score += 10
        else:
            self.findings.append({
                "severity": "critical",
                "title": "❌ No usa HTTPS",
                "description": "El sitio no está seguro. Google lo penaliza en rankings"
            })
            self.score -= 15

        # Check: Page Size
        if page_size < 2000000:  # < 2MB es bueno
            self.findings.append({
                "severity": "success",
                "title": f"✅ Tamaño Optimizado ({int(page_size/1024)}KB)",
                "description": "El sitio carga rápido"
            })
            self.score += 10
        else:
            self.findings.append({
                "severity": "warning",
                "title": f"⚠️ Sitio Pesado ({int(page_size/1024)}KB)",
                "description": "Puede tardar en cargar. Optimiza imágenes"
            })
            self.score -= 5

        # Check: Tracking Scripts
        tracking_found = self._check_tracking_scripts(html)
        if tracking_found:
            self.findings.append({
                "severity": "success",
                "title": f"✅ Tracking Detectado ({', '.join(tracking_found)})",
                "description": "Estás capturando datos de visitantes"
            })
            self.score += 15
        else:
            self.findings.append({
                "severity": "critical",
                "title": "❌ Sin Tracking Configurado",
                "description": "No estás midiendo visitantes ni conversiones. Instala GA4 o similar"
            })
            self.score -= 20

        # Check: Title & Meta
        if not parser.title or len(parser.title) < 10:
            self.findings.append({
                "severity": "warning",
                "title": "⚠️ Meta Title Faltante/Corto",
                "description": "El title es importante para SEO"
            })
            self.score -= 5

        if not parser.description or len(parser.description) < 20:
            # Distingue ausente de corta: la página sí puede tener meta descripción.
            titulo = "⚠️ Meta Description Faltante" if not parser.description else "⚠️ Meta Description Corta"
            self.findings.append({
                "severity": "warning",
                "title": titulo,
                "description": "No aparecerás bien en Google"
            })
            self.score -= 5

        # Check: Images
        if parser.img_count == 0:
            self.findings.append({
                "severity": "warning",
                "title": "⚠️ Sin imágenes",
                "description": "Las imágenes mejoran engagement"
            })
            self.score -= 5
        elif parser.img_count > 20:
            self.findings.append({
                "severity": "warning",
                "title": f"⚠️ Muchas imágenes ({parser.img_count})",
                "description": "Podría afectar velocidad. Optimiza"
            })
            self.score -= 3

        # Clamp score 0-100
        self.score = max(0, min(100, self.score))

        return {
            "status": "success",
            "website_url": website_url,
            "audit_date": self.audit_date,
            "score": self.score,
            "findings": self.findings,
            "summary": {
                "total_findings": len(self.findings),
                "critical_issues": len([f for f in self.findings if f["severity"] == "critical"]),
                "warnings": len([f for f in self.findings if f["severity"] == "warning"]),
                "next_step": "Solicita auditoría completa para plan de mejoras personalizado"
            }
        }

    def _check_tracking_scripts(self, html: str) -> List[str]:
        """Detecta scripts de tracking"""
        # Patrones específicos: una palabra suelta (p. ej. "facebook" en un enlace) no basta.
        tracking_platforms = {
            "GA4": r"googletagmanager\.com/gtag/js|gtag\(\s*['\"]config['\"]",
            "GTM": r"GTM-[A-Z0-9]{4,}|googletagmanager\.com/gtm\.js",
            "Facebook Pixel": r"connect\.facebook\.net|fbevents\.js|fbq\(",
            "Hotjar": r"static\.hotjar\.com|hjid",
            "Clarity": r"clarity\.ms",
        }

        found = []
        for platform, patron in tracking_platforms.items():
            if re.search(patron, html):
                found.append(platform)

        return found

    def _timeout_response(self) -> Dict:
        """Respuesta cuando el sitio tarda en cargar"""
        return {
            "status": "error",
            "error": "El sitio tardó demasiado en responder (>10s)",
            "findings": [
                {
                    "severity": "critical",
                    "title": "⚠️ Velocidad Crítica",
                    "description": "El sitio carga muy lentamente. Esto afecta SEO y conversiones"
                }
            ]
        }

    def _error_response(self, error: str) -> Dict:
        """Respuesta cuando hay error"""
        return {
            "status": "error",
            "error": error,
            "findings": []
        }


def perform_quick_audit(website_url: str) -> Dict:
    """Helper function"""
    auditor = QuickAuditor()
    return auditor.audit(website_url)
