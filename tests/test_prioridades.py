"""Lista priorizada desde el informe: reglas explícitas, sin cifras inventadas."""
from auditors.prioridades import priorizar


def _informe(**secciones):
    # Las secciones del informe real siempre traen status; los tests lo ponen como "medido".
    for sec in secciones.values():
        sec.setdefault("status", "medido")
    return {"url": "https://ejemplo.cl", "secciones": secciones}


SEO_CORTO = {"metrics": {"tecnica": {"findings": [
    {"issue": "Title muy corto (<30 chars)"},
    {"issue": "Meta description muy corta (<50 chars)"},
]}}}


def test_seo_corto_genera_dos_acciones_de_impacto_alto_y_esfuerzo_bajo():
    r = priorizar(_informe(seo=SEO_CORTO))
    acciones = [i["accion"] for i in r["prioridades"]]
    assert any("título" in a for a in acciones)
    assert any("meta descripción" in a for a in acciones)
    assert all(i["impacto"] == "alto" and i["esfuerzo"] == "bajo" for i in r["prioridades"])


def test_sin_gtm_es_prioridad_alta():
    gtm = {"metrics": {"cantidad_contenedores": 0, "duplicado": False, "consent_mode_default": False}}
    r = priorizar(_informe(gtm=gtm))
    assert r["prioridades"][0]["accion"] == "Instalar Google Tag Manager"
    assert r["prioridades"][0]["impacto"] == "alto"


def test_gtm_sin_consent_mode_se_marca():
    gtm = {"metrics": {"cantidad_contenedores": 1, "duplicado": False, "consent_mode_default": False}}
    acciones = [i["accion"] for i in priorizar(_informe(gtm=gtm))["prioridades"]]
    assert "Configurar Consent Mode v2 por defecto en GTM" in acciones


def test_orden_por_impacto_y_luego_esfuerzo():
    gtm = {"metrics": {"cantidad_contenedores": 1, "duplicado": False, "consent_mode_default": False}}
    seo = SEO_CORTO
    r = priorizar(_informe(seo=seo, gtm=gtm))
    impactos = [i["impacto"] for i in r["prioridades"]]
    assert impactos == sorted(impactos, key=lambda x: {"alto": 0, "medio": 1, "bajo": 2}[x])


def test_secciones_no_medidas_se_listan_aparte_sin_prioridad():
    r = priorizar(_informe(seo={"status": "sin_datos", "motivo": "x"}))
    assert r["prioridades"] == []
    assert "seo" in r["no_medido"]


def test_informe_real_talleres_genera_lista_esperada():
    import json, os
    ruta = "/tmp/claude-0/-home-claude/519f23c7-eda4-51b9-b6e7-65dba6f6a4a4/scratchpad/informe4.json"
    if not os.path.exists(ruta):
        return
    informe = json.load(open(ruta, encoding="utf-8"))
    acciones = [i["accion"] for i in priorizar(informe)["prioridades"]]
    assert "Configurar Consent Mode v2 por defecto en GTM" in acciones
    assert any("Confirmar o activar Google Analytics 4" in a for a in acciones)


def test_seccion_faltante_no_genera_falsa_alarma():
    r = priorizar(_informe(seo=SEO_CORTO))
    acciones = [i["accion"] for i in r["prioridades"]]
    assert "Instalar Google Tag Manager" not in acciones
    assert "gtm" in r["no_medido"]


def test_subseccion_seo_no_medida_se_lista():
    seo = {"status": "medido", "metrics": {
        "tecnica": {"score": 85, "findings": []},
        "rendimiento": {"score": None, "findings": []},
        "seguridad": {"score": None, "findings": []},
    }}
    r = priorizar(_informe(seo=seo))
    assert "seo.rendimiento" in r["no_medido"]
    assert "seo.seguridad" in r["no_medido"]
