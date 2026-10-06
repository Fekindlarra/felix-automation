#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO Auditor - Full Workflow Test
Demonstrates complete SEO auditing workflow
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from auditors.seo_auditor import SEOAuditor, MetaTagParser


def test_seo_auditor_workflow():
    """Complete SEO auditor workflow with real HTML"""

    # Sample HTML from TechVentures Chile (from existing tests)
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
        ayudan a empresas a aumentar su productividad y cerrar más negocios.
        La automatización de ventas es esencial para optimizar procesos.
        Implementar estas herramientas puede aumentar la productividad de ventas significativamente.
        Nuestras herramientas de automatización son líderes en la industria.</p>
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

    # Create auditor
    auditor = SEOAuditor()

    # Run audit
    print("\n" + "="*70)
    print("🔍 SEO AUDITOR - WORKFLOW DEMO")
    print("="*70)

    result = auditor.audit({
        'url': 'https://techventures.cl',
        'html': html,
        'page_size': len(html.encode()),
        'load_time': 1.2,
        'headers': {
            'content-type': 'text/html; charset=UTF-8',
            'x-frame-options': 'SAMEORIGIN',
            'x-content-type-options': 'nosniff'
        }
    })

    # Display results
    print(f"\n✅ Platform: {result['platform']}")
    print(f"📊 Overall Score: {result['overall_score']}/100")
    print(f"⏰ Timestamp: {result['timestamp']}")
    print(f"📝 Status: {result['status']}")

    # Metrics breakdown
    print("\n" + "-"*70)
    print("📋 DETAILED METRICS")
    print("-"*70)

    for category, metrics in result['metrics'].items():
        print(f"\n{category.upper()} - Score: {metrics['score']}/100")
        if metrics['findings']:
            print(f"  Findings ({len(metrics['findings'])}):")
            for finding in metrics['findings'][:3]:  # Show first 3
                severity_icon = "🔴" if finding['severity'] == 'critical' else "🟡" if finding['severity'] == 'warning' else "ℹ️"
                print(f"    {severity_icon} [{finding['severity'].upper()}] {finding['issue']}")
        else:
            print(f"  ✅ No findings")

    # Keywords
    print("\n" + "-"*70)
    print("🔑 DETECTED KEYWORDS")
    print("-"*70)
    keywords = result.get('keywords_detected', [])
    if keywords:
        print(f"\nTop keywords detected ({len(keywords)}):")
        for i, keyword in enumerate(keywords[:10], 1):
            print(f"  {i:2d}. {keyword}")

    # Summary
    print("\n" + "="*70)
    print("📈 SUMMARY")
    print("="*70)

    if result['overall_score'] >= 80:
        rating = "🌟 Excellent"
    elif result['overall_score'] >= 70:
        rating = "✅ Good"
    elif result['overall_score'] >= 60:
        rating = "⚠️  Fair"
    else:
        rating = "❌ Poor"

    print(f"\n{rating} - Overall SEO Score: {result['overall_score']}/100")
    print("\nNext steps:")
    print("1. ✅ Fix critical issues first (red indicators)")
    print("2. ⚠️  Address warnings (yellow indicators)")
    print("3. 📈 Implement keyword optimization recommendations")
    print("4. 🔄 Re-audit after changes to verify improvements")

    print("\n" + "="*70 + "\n")

    # Verify results
    assert result['platform'] == 'seo'
    assert result['overall_score'] > 0
    assert 'metrics' in result
    assert 'keywords_detected' in result
    assert result['status'] == 'completed'

    return result


if __name__ == "__main__":
    result = test_seo_auditor_workflow()
    print("✅ SEO Auditor workflow completed successfully!")
