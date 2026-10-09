"""Comparación antes/después: resueltas, pendientes y nuevas, sin inventar cambios."""
from auditors.comparar_informes import comparar


def _informe(titulo_corto=True, consent=False):
    tecnica = []
    if titulo_corto:
        tecnica.append({"issue": "Title muy corto (<30 chars)"})
    return {
        "url": "https://ejemplo.cl",
        "secciones": {
            "seo": {"status": "medido", "metrics": {"tecnica": {"score": 85, "findings": tecnica}}},
            "gtm": {"status": "medido", "metrics": {
                "cantidad_contenedores": 1, "duplicado": False, "consent_mode_default": consent}},
        },
    }


def test_arreglo_aparece_como_resuelto():
    r = comparar(_informe(titulo_corto=True), _informe(titulo_corto=False))
    assert [i["accion"] for i in r["resueltas"]] == ["Alargar el título de la página principal (≥30 caracteres)"]
    assert r["nuevas"] == []


def test_sin_cambios_todo_pendiente():
    r = comparar(_informe(), _informe())
    assert r["resueltas"] == []
    assert r["nuevas"] == []
    assert len(r["pendientes"]) == 2  # título y consent


def test_consent_configurado_se_resuelve():
    r = comparar(_informe(titulo_corto=False, consent=False), _informe(titulo_corto=False, consent=True))
    acciones = [i["accion"] for i in r["resueltas"]]
    assert "Configurar Consent Mode v2 por defecto en GTM" in acciones


def test_empeoramiento_aparece_como_nuevo():
    r = comparar(_informe(titulo_corto=False), _informe(titulo_corto=True))
    assert any("título" in i["accion"] for i in r["nuevas"])


def test_flujo_completo_con_html_y_anterior():
    from auditors.flujo_correccion import ejecutar
    html = '<html><head><title>En buena mesa</title><meta name="description" content="Taller"></head><body><h1>x</h1></body></html>'
    antes = {"url": "https://ejemplo.cl", "secciones": {}}
    r = ejecutar("https://ejemplo.cl", html=html, anterior=antes)
    assert r["informe"]["origen_html"]["tipo"] == "archivo"
    assert "comparacion" in r
    assert "prioridades" in r["prioridades"]
