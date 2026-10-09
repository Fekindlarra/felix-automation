"""Tabla comparativa desde informes: solo hechos medidos, 'no medido' cuando falta algo."""
from auditors.comparar_competidores import tabla


def _informe(url, titulo_corto=False, gtm=None, ga=False, pixel=True):
    tracking_findings = []
    if ga:
        tracking_findings.append({"title": "✅ Google Analytics 4 Detectado"})
    else:
        tracking_findings.append({"title": "❌ Google Analytics NO Detectado"})
    if pixel:
        tracking_findings.append({"title": "✅ Facebook Pixel Detectado"})
    else:
        tracking_findings.append({"title": "⚠️ Facebook Pixel NO Detectado"})
    tecnica = [{"issue": "Title muy corto (<30 chars)"}] if titulo_corto else []
    return {
        "url": url,
        "secciones": {
            "seo": {"status": "medido", "overall_score": 80,
                    "metrics": {"tecnica": {"findings": tecnica},
                                "contenido": {"findings": [{"issue": "Imágenes sin alt text (24)", "value": 24}]}}},
            "tracking": {"status": "medido", "findings": tracking_findings},
            "gtm": {"status": "medido", "metrics": gtm or {"cantidad_contenedores": 0, "contenedores": [], "consent_mode_default": False}},
            "plataforma": {"status": "medido", "detectadas": []},
        },
    }


def test_tabla_tiene_una_columna_por_sitio():
    t = tabla([_informe("https://a.cl"), _informe("https://b.cl")], ["A", "B"])
    encabezado = t.splitlines()[0]
    assert encabezado == "| Punto | A | B |"


def test_titulo_corto_se_muestra_como_alerta():
    t = tabla([_informe("https://a.cl", titulo_corto=True)], ["A"])
    assert "alerta: Title muy corto" in t


def test_gtm_y_ga4_se_leen_de_los_informes():
    gtm = {"cantidad_contenedores": 1, "contenedores": ["GTM-XYZ123"], "consent_mode_default": False}
    t = tabla([_informe("https://a.cl", gtm=gtm, ga=True)], ["A"])
    assert "| Google Tag Manager | GTM-XYZ123 |" in t
    assert "| Google Analytics 4 | sí |" in t


def test_dato_no_medido_no_se_inventa():
    vacio = {"url": "https://x.cl", "secciones": {}}
    t = tabla([vacio], ["X"])
    assert "| Google Tag Manager | no medido |" in t
    assert "| Puntaje SEO (reglas internas) | no medido |" in t
