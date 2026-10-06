#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para SEO Auditor
"""

import pytest
from auditors.seo_auditor import SEOAuditor, MetaTagParser


class TestSEOAuditorBasic:
    """Tests básicos del SEO Auditor"""

    def test_seo_auditor_initialization(self):
        """SEO Auditor debe inicializar correctamente"""
        auditor = SEOAuditor()
        assert auditor.platform == "seo"
        assert auditor.overall_score == 0
        assert "tecnica" in auditor.metrics
        assert "contenido" in auditor.metrics
        assert "rendimiento" in auditor.metrics
        assert "seguridad" in auditor.metrics

    def test_seo_auditor_complete_page(self):
        """Auditar página SEO completa"""
        auditor = SEOAuditor()

        html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TechVentures Chile - Soluciones de Automatización de Ventas</title>
            <meta name="description" content="Plataforma de automatización de ventas para empresas en Chile">
            <meta name="robots" content="index, follow">
            <meta property="og:title" content="TechVentures Chile">
            <meta property="og:description" content="Soluciones de automatización">
            <meta property="og:image" content="/logo.png">
            <meta property="og:url" content="https://techventures.cl">
        </head>
        <body>
            <h1>Automatización de Ventas para Chile</h1>
            <h2>¿Por qué elegir TechVentures?</h2>
            <p>Somos la plataforma líder en automatización de ventas en Chile. Nuestras soluciones
            ayudan a empresas a aumentar su productividad y cerrar más negocios.</p>
            <h2>Características principales</h2>
            <ul>
                <li>WebSocket en tiempo real</li>
                <li>Predicciones de ML</li>
                <li>A/B Testing avanzado</li>
            </ul>
            <h3>Integración con Shopify</h3>
            <p>Conecta tu tienda Shopify y recibe insights automáticos sobre tu desempeño.</p>
            <img src="/shopify-integration.png" alt="Integración Shopify">
            <h3>Mobile optimizado</h3>
            <p>Accede desde tu teléfono con la misma funcionalidad que en desktop.</p>
            <img src="/mobile-app.png" alt="App móvil">
            <p>© 2024 TechVentures Chile. Todos los derechos reservados.</p>
            <a href="/privacy-policy">Política de Privacidad</a>
        </body>
        </html>
        """

        result = auditor.audit({
            'url': 'https://techventures.cl',
            'html': html,
            'page_size': 45000,
            'load_time': 1.2,
            'headers': {
                'content-type': 'text/html; charset=UTF-8',
                'x-frame-options': 'SAMEORIGIN',
                'x-content-type-options': 'nosniff'
            }
        })

        assert result['platform'] == 'seo'
        assert result['status'] == 'completed'
        assert result['overall_score'] > 70  # Debe tener buen score
        assert 'metrics' in result
        assert len(result['keywords_detected']) > 0


class TestSEOAuditorTecnica:
    """Tests para auditoría técnica"""

    def test_missing_title_tag(self):
        """Debe detectar falta de title tag"""
        auditor = SEOAuditor()
        html = "<html><head></head><body>Contenido sin title</body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['tecnica']['findings']
        assert any('Title' in str(f) or 'title' in str(f) for f in findings)

    def test_missing_meta_description(self):
        """Debe detectar falta de meta description"""
        auditor = SEOAuditor()
        html = "<html><head><title>Test</title></head><body>Contenido</body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['tecnica']['findings']
        assert any('description' in str(f).lower() for f in findings)

    def test_missing_h1_tag(self):
        """Debe detectar falta de H1 tag"""
        auditor = SEOAuditor()
        html = "<html><head><title>Test</title></head><body><h2>Sin H1</h2></body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['tecnica']['findings']
        assert any('H1' in str(f) for f in findings)

    def test_missing_viewport_tag(self):
        """Debe detectar falta de viewport meta tag"""
        auditor = SEOAuditor()
        html = "<html><head><title>Test</title></head><body>Content</body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['tecnica']['findings']
        assert any('viewport' in str(f).lower() for f in findings)

    def test_no_https(self):
        """Debe detectar URL sin HTTPS"""
        auditor = SEOAuditor()
        html = "<html><head><title>Test</title></head><body>Content</body></html>"

        result = auditor.audit({
            'url': 'http://example.com',  # Sin HTTPS
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['tecnica']['findings']
        assert any('HTTPS' in str(f) for f in findings)


class TestSEOAuditorContenido:
    """Tests para auditoría de contenido"""

    def test_keyword_detection(self):
        """Debe detectar palabras clave del contenido"""
        auditor = SEOAuditor()
        html = """
        <html><head><title>Automatización de Ventas</title></head><body>
        <h1>Automatización de Ventas para Empresas</h1>
        <p>La automatización de ventas es esencial. Aumenta la productividad de ventas.
        Nuestras herramientas de automatización son las mejores.</p>
        </body></html>
        """

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        keywords = result['keywords_detected']
        assert 'automatización' in [k.lower() for k in keywords] or 'ventas' in [k.lower() for k in keywords]

    def test_short_content_warning(self):
        """Debe advertir sobre contenido muy corto"""
        auditor = SEOAuditor()
        html = "<html><head><title>Test</title></head><body><h1>Título</h1><p>Muy corto</p></body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['contenido']['findings']
        assert any('corto' in str(f).lower() or 'short' in str(f).lower() for f in findings)

    def test_missing_image_alt_text(self):
        """Debe detectar imágenes sin alt text"""
        auditor = SEOAuditor()
        html = """
        <html><head><title>Test</title></head><body>
        <h1>Título</h1>
        <p>Contenido largo Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
        <img src="/image1.png">
        <img src="/image2.png" alt="Descripción">
        </body></html>
        """

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['contenido']['findings']
        assert any('alt' in str(f).lower() for f in findings)


class TestSEOAuditorRendimiento:
    """Tests para auditoría de rendimiento"""

    def test_large_page_size(self):
        """Debe advertir sobre páginas muy grandes"""
        auditor = SEOAuditor()
        html = "<html><body>Test</body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 6000000,  # 6MB
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['rendimiento']['findings']
        assert any('grande' in str(f).lower() or 'large' in str(f).lower() for f in findings)

    def test_slow_load_time(self):
        """Debe advertir sobre tiempo de carga lento"""
        auditor = SEOAuditor()
        html = "<html><body>Test</body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 50000,
            'load_time': 3.5,  # Más de 3 segundos
            'headers': {}
        })

        findings = result['metrics']['rendimiento']['findings']
        assert any('lento' in str(f).lower() or 'slow' in str(f).lower() for f in findings)

    def test_optimal_load_time(self):
        """Debe reconocer tiempo de carga óptimo"""
        auditor = SEOAuditor()
        html = "<html><body>Test</body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 50000,
            'load_time': 1.2,  # Bueno
            'headers': {}
        })

        findings = result['metrics']['rendimiento']['findings']
        assert any('óptimo' in str(f).lower() or 'optimal' in str(f).lower() for f in findings)


class TestSEOAuditorSeguridad:
    """Tests para auditoría de seguridad"""

    def test_missing_privacy_policy(self):
        """Debe detectar falta de política de privacidad"""
        auditor = SEOAuditor()
        html = "<html><body><h1>Título</h1></body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['seguridad']['findings']
        assert any('privacy' in str(f).lower() or 'privacidad' in str(f).lower() for f in findings)

    def test_privacy_policy_present(self):
        """Debe reconocer cuando hay política de privacidad"""
        auditor = SEOAuditor()
        html = "<html><body><a href='/privacy'>Política de Privacidad</a></body></html>"

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': 10000,
            'load_time': 1.0,
            'headers': {}
        })

        findings = result['metrics']['seguridad']['findings']
        # No debería haber hallazgo crítico sobre política de privacidad
        assert not any('privacy' in str(f).lower() and 'critical' in str(f).lower() for f in findings)


class TestMetaTagParser:
    """Tests para el parser de meta tags"""

    def test_parse_title(self):
        """Debe parsear title tag correctamente"""
        parser = MetaTagParser()
        parser.feed("<html><head><title>Test Title</title></head></html>")
        assert parser.title == "Test Title"

    def test_parse_meta_tags(self):
        """Debe parsear meta tags correctamente"""
        parser = MetaTagParser()
        html = """
        <html><head>
            <meta name="description" content="Test description">
            <meta name="viewport" content="width=device-width">
        </head></html>
        """
        parser.feed(html)
        assert parser.meta_tags.get('description') == 'Test description'
        assert parser.meta_tags.get('viewport') == 'width=device-width'

    def test_parse_images(self):
        """Debe parsear imágenes y alt text"""
        parser = MetaTagParser()
        html = """
        <html><body>
            <img src="/img1.png" alt="Descripción 1">
            <img src="/img2.png">
        </body></html>
        """
        parser.feed(html)
        assert len(parser.images) == 2
        assert parser.images[0]['alt'] == 'Descripción 1'
        assert parser.images[1]['alt'] == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
