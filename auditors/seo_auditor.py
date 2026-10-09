#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO Auditor - Auditoría de Optimización SEO en Sitios Web
Métricas: Técnica, Contenido, Rendimiento, Seguridad
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
from html.parser import HTMLParser


class MetaTagParser(HTMLParser):
    """Parseador personalizado de meta tags y estructura HTML"""

    def __init__(self):
        super().__init__()
        self.meta_tags = {}
        self.title = ""
        self.h1_tags = []
        self.h2_tags = []
        self.h3_tags = []
        self.images = []
        self.links = {"internal": [], "external": [], "broken": []}
        self.scripts = []
        self.in_title = False
        self.current_text = ""
        self.headers_hierarchy = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            if "charset" in attrs_dict:
                # <meta charset="UTF-8"> no tiene name ni property; antes se perdía.
                self.meta_tags["charset"] = attrs_dict["charset"]
            if "name" in attrs_dict:
                self.meta_tags[attrs_dict["name"]] = attrs_dict.get("content", "")
            elif "property" in attrs_dict:
                self.meta_tags[attrs_dict["property"]] = attrs_dict.get("content", "")
        elif tag == "h1":
            self.headers_hierarchy.append(("h1", ""))
        elif tag == "h2":
            self.headers_hierarchy.append(("h2", ""))
        elif tag == "h3":
            self.headers_hierarchy.append(("h3", ""))
        elif tag == "img":
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "alt": attrs_dict.get("alt", ""),
                "title": attrs_dict.get("title", "")
            })
        elif tag == "a":
            self.links["internal" if "href" in attrs_dict and not attrs_dict["href"].startswith("http") else "external"].append(
                {"href": attrs_dict.get("href", ""), "text": attrs_dict.get("title", "")}
            )
        elif tag == "script":
            self.scripts.append(attrs_dict.get("src", ""))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.headers_hierarchy and self.headers_hierarchy[-1]:
            h_tag, content = self.headers_hierarchy[-1]
            self.headers_hierarchy[-1] = (h_tag, content + data.strip())

    def get_headers(self):
        h1s = [h[1] for h in self.headers_hierarchy if h[0] == "h1"]
        h2s = [h[1] for h in self.headers_hierarchy if h[0] == "h2"]
        h3s = [h[1] for h in self.headers_hierarchy if h[0] == "h3"]
        return h1s, h2s, h3s


class SEOAuditor:
    """Auditor especializado en SEO"""

    def __init__(self):
        self.platform = "seo"
        self.metrics = {
            "tecnica": {"score": 0, "findings": []},
            "contenido": {"score": 0, "findings": []},
            "rendimiento": {"score": 0, "findings": []},
            "seguridad": {"score": 0, "findings": []}
        }
        self.keywords = []
        self.overall_score = 0

    def audit(self, site_data: Dict) -> Dict:
        """
        Realizar auditoría SEO completa del sitio

        Esperado en site_data:
        {
            'url': str,
            'html': str,
            'page_size': int,
            'load_time': float,
            'headers': dict
        }
        """
        self.metrics = self._reset_metrics()

        # Parsear HTML
        parser = MetaTagParser()
        try:
            parser.feed(site_data.get('html', ''))
        except Exception as e:
            return self._error_response(f"Error parsing HTML: {str(e)}")

        # Auditar cada componente
        self._audit_tecnica(site_data, parser)
        self._audit_contenido(site_data, parser)
        self._audit_rendimiento(site_data)
        self._audit_seguridad(site_data)

        # Calcular score general
        self.overall_score = self._calculate_overall_score()

        return {
            "platform": self.platform,
            "overall_score": self.overall_score,
            "metrics": self.metrics,
            "keywords_detected": self.keywords[:10],  # Top 10 keywords
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

    def _audit_tecnica(self, site_data: Dict, parser: MetaTagParser):
        """Auditar aspectos técnicos SEO"""
        score = 100
        findings = []

        url = site_data.get('url', '')
        meta_tags = parser.meta_tags

        # 1. Title tag
        if parser.title:
            if len(parser.title) < 30:
                findings.append({"severity": "warning", "issue": "Title muy corto (<30 chars)", "value": len(parser.title)})
                score -= 5
            elif len(parser.title) > 60:
                findings.append({"severity": "warning", "issue": "Title muy largo (>60 chars)", "value": len(parser.title)})
                score -= 5
        else:
            findings.append({"severity": "critical", "issue": "Falta title tag", "value": None})
            score -= 20

        # 2. Meta description
        meta_desc = meta_tags.get('description', '')
        if meta_desc:
            if len(meta_desc) < 50:
                findings.append({"severity": "warning", "issue": "Meta description muy corta (<50 chars)", "value": len(meta_desc)})
                score -= 5
            elif len(meta_desc) > 160:
                findings.append({"severity": "warning", "issue": "Meta description muy larga (>160 chars)", "value": len(meta_desc)})
                score -= 5
        else:
            findings.append({"severity": "critical", "issue": "Falta meta description", "value": None})
            score -= 15

        # 3. H1 tags
        h1s, h2s, h3s = parser.get_headers()
        if len(h1s) == 0:
            findings.append({"severity": "critical", "issue": "Falta H1 tag", "value": 0})
            score -= 15
        elif len(h1s) > 1:
            findings.append({"severity": "warning", "issue": "Múltiples H1 tags (debe ser 1)", "value": len(h1s)})
            score -= 10

        # 4. Viewport meta tag
        if 'viewport' not in meta_tags:
            findings.append({"severity": "critical", "issue": "Falta viewport meta tag (no responsive)", "value": None})
            score -= 15

        # 5. Charset
        if 'charset' not in parser.meta_tags and 'charset' not in site_data.get('headers', {}).get('content-type', ''):
            findings.append({"severity": "warning", "issue": "Falta charset declaration", "value": None})
            score -= 5

        # 6. URL structure
        parsed_url = urlparse(url)
        if not url.startswith('https'):
            findings.append({"severity": "critical", "issue": "URL sin HTTPS", "value": url})
            score -= 20

        # 7. Robots meta tag
        robots_tag = meta_tags.get('robots', '')
        if 'noindex' in robots_tag:
            findings.append({"severity": "critical", "issue": "Página tiene noindex (no indexada)", "value": robots_tag})
            score -= 25

        self.metrics["tecnica"]["score"] = max(0, score)
        self.metrics["tecnica"]["findings"] = findings

    def _audit_contenido(self, site_data: Dict, parser: MetaTagParser):
        """Auditar calidad del contenido"""
        score = 100
        findings = []

        html = site_data.get('html', '')

        # 1. Detectar palabras clave principales
        self.keywords = self._detect_keywords(html)

        # 2. Densidad de palabras clave
        if len(self.keywords) > 0:
            findings.append({"severity": "info", "issue": "Palabras clave detectadas", "value": len(self.keywords)})
        else:
            findings.append({"severity": "warning", "issue": "No se detectaron palabras clave relevantes", "value": 0})
            score -= 10

        # 3. Headings hierarchy
        h1s, h2s, h3s = parser.get_headers()
        if len(h2s) == 0 and len(h3s) == 0:
            findings.append({"severity": "warning", "issue": "Falta estructura de headings (H2, H3)", "value": None})
            score -= 10

        # 4. Content length
        # Solo texto visible: se quitan scripts y estilos antes de contar.
        sin_codigo = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', html)
        text_content = re.sub(r'<[^>]+>', '', sin_codigo)
        # Largo del texto visible con espacios colapsados (sin saltos ni indentación).
        text_length = len(re.sub(r'\s+', ' ', text_content).strip())
        if text_length < 300:
            findings.append({"severity": "warning", "issue": "Contenido muy corto (<300 words)", "value": text_length})
            score -= 10
        elif text_length > 3000:
            findings.append({"severity": "info", "issue": "Contenido extenso", "value": text_length})

        # 5. Image alt text
        images_without_alt = [img for img in parser.images if not img.get('alt', '')]
        if images_without_alt:
            findings.append({"severity": "warning", "issue": f"Imágenes sin alt text ({len(images_without_alt)})", "value": len(images_without_alt)})
            # Tope: sin límite, 24 imágenes restaban 120 puntos y dejaban el puntaje en 0.
            score -= min(20, 5 * len(images_without_alt))

        # 6. Open Graph tags
        og_tags = {k: v for k, v in parser.meta_tags.items() if k.startswith('og:')}
        if len(og_tags) < 4:
            findings.append({"severity": "info", "issue": f"Open Graph tags incompletos ({len(og_tags)}/4)", "value": len(og_tags)})

        # 7. Duplicate content check
        if html.count('<h1>') > 1:
            findings.append({"severity": "warning", "issue": "Múltiples H1 tags (posible contenido duplicado)", "value": html.count('<h1>')})
            score -= 10

        self.metrics["contenido"]["score"] = max(0, score)
        self.metrics["contenido"]["findings"] = findings

    def _audit_rendimiento(self, site_data: Dict):
        """Auditar rendimiento y velocidad"""
        if 'load_time' not in site_data or 'page_size' not in site_data:
            # Sin medición real no se asigna puntaje (antes se asumía 0.00s y 100).
            self.metrics["rendimiento"]["score"] = None
            self.metrics["rendimiento"]["findings"] = [{
                "severity": "info",
                "issue": "No medido: sin tiempo de carga ni tamaño de descarga",
                "value": None,
            }]
            return

        score = 100
        findings = []

        page_size = site_data.get('page_size', 0)
        load_time = site_data.get('load_time', 0)

        # 1. Page size
        if page_size > 5000000:  # 5MB
            findings.append({"severity": "critical", "issue": "Página muy grande (>5MB)", "value": f"{page_size/1000000:.1f}MB"})
            score -= 20
        elif page_size > 2000000:  # 2MB
            findings.append({"severity": "warning", "issue": "Página grande (>2MB)", "value": f"{page_size/1000000:.1f}MB"})
            score -= 10

        # 2. Load time
        if load_time > 3:
            findings.append({"severity": "critical", "issue": "Tiempo de carga lento (>3s)", "value": f"{load_time:.2f}s"})
            score -= 15
        elif load_time > 2:
            findings.append({"severity": "warning", "issue": "Tiempo de carga moderado (>2s)", "value": f"{load_time:.2f}s"})
            score -= 10
        else:
            findings.append({"severity": "info", "issue": "Tiempo de carga óptimo", "value": f"{load_time:.2f}s"})

        # 3. Cumulative Layout Shift (CLS) - simulado
        findings.append({"severity": "info", "issue": "Core Web Vitals - Evaluación necesaria en navegador", "value": "N/A"})

        self.metrics["rendimiento"]["score"] = max(0, score)
        self.metrics["rendimiento"]["findings"] = findings

    def _audit_seguridad(self, site_data: Dict):
        """Auditar seguridad y compliance"""
        if 'headers' not in site_data:
            # Sin cabeceras HTTP reales no se evalúan (antes se marcaban como faltantes).
            self.metrics["seguridad"]["score"] = None
            self.metrics["seguridad"]["findings"] = [{
                "severity": "info",
                "issue": "No medido: sin cabeceras HTTP",
                "value": None,
            }]
            return

        score = 100
        findings = []

        headers = site_data.get('headers', {})
        html = site_data.get('html', '')

        # 1. HTTPS
        url = site_data.get('url', '')
        if not url.startswith('https'):
            findings.append({"severity": "critical", "issue": "Sin HTTPS", "value": url})
            score -= 20

        # 2. Security headers
        security_headers = {
            'x-frame-options': {'value': headers.get('x-frame-options'), 'severity': 'warning'},
            'x-content-type-options': {'value': headers.get('x-content-type-options'), 'severity': 'warning'},
            'content-security-policy': {'value': headers.get('content-security-policy'), 'severity': 'warning'},
        }

        for header, config in security_headers.items():
            if not config['value']:
                findings.append({"severity": config['severity'], "issue": f"Falta header de seguridad: {header}", "value": None})
                score -= 3

        # 3. Privacy policy
        if 'privacy' not in html.lower() and 'política' not in html.lower():
            findings.append({"severity": "warning", "issue": "No hay enlace a política de privacidad", "value": None})
            score -= 10

        # 4. Cookies consent
        if 'cookie' not in html.lower():
            findings.append({"severity": "info", "issue": "No se detecta banner de cookies", "value": None})

        self.metrics["seguridad"]["score"] = max(0, score)
        self.metrics["seguridad"]["findings"] = findings

    def _detect_keywords(self, html: str) -> List[str]:
        """Detectar palabras clave principales del contenido"""
        # Remover HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Convertir a minúsculas y limpiar
        text = text.lower()
        # Remover palabras muy comunes
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
                     'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
                     'de', 'la', 'el', 'y', 'o', 'un', 'una', 'unos', 'unas', 'los', 'las'}

        # Extraer palabras (2+ caracteres)
        words = re.findall(r'\b\w{2,}\b', text)

        # Contar frecuencia
        word_freq = {}
        for word in words:
            if word not in stop_words and not word.isdigit():
                word_freq[word] = word_freq.get(word, 0) + 1

        # Retornar top 20 palabras por frecuencia
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:20]]

    def _calculate_overall_score(self) -> int:
        """Calcular score general de SEO (0-100)"""
        # Solo promedian las secciones medidas (score None = no medido).
        scores = [self.metrics[category]["score"] for category in self.metrics
                  if self.metrics[category]["score"] is not None]
        if scores:
            return round(sum(scores) / len(scores))
        return None

    def _reset_metrics(self) -> Dict:
        """Resetear métricas a valores iniciales"""
        return {
            "tecnica": {"score": 0, "findings": []},
            "contenido": {"score": 0, "findings": []},
            "rendimiento": {"score": 0, "findings": []},
            "seguridad": {"score": 0, "findings": []}
        }

    def _error_response(self, error_message: str) -> Dict:
        """Retornar respuesta de error"""
        return {
            "platform": self.platform,
            "overall_score": 0,
            "status": "error",
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
