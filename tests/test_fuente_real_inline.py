"""Casos reales de talleresenbuenamesa.cl: GTM y Pixel en JavaScript inline y
HTML en formato 'ver código fuente' (sin red)."""
from auditors.auditoria_url import auditar_url
from auditors.gtm_html_auditor import auditar_gtm_html
from auditors.html_fuente import normalizar_html
from auditors.tracking_scripts_auditor import audit_tracking_scripts

SNIPPET_GTM_INLINE = """<script>
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer', "GTM-MKF23TH7");
</script>"""

PIXEL_INLINE = """<script>
!function(f,b,e,v,n,t,s){}(window, document,'script',
'https://connect.facebook.net/' + getNavigatorLocale() + '/fbevents.js');
</script>"""

PAGINA = f"<html><head><title>En buena mesa</title>{SNIPPET_GTM_INLINE}{PIXEL_INLINE}</head><body><h1>Taller</h1></body></html>"


def _fila(linea):
    return f'<tr><td class="line-number" value="1"></td><td class="line-content">{linea}</td></tr>'


def test_gtm_inline_se_detecta_y_no_es_duplicado():
    m = auditar_gtm_html(SNIPPET_GTM_INLINE)["metrics"]
    assert m["contenedores"] == ["GTM-MKF23TH7"]
    assert m["duplicado"] is False


def test_tracking_detecta_gtm_y_pixel_inline():
    r = audit_tracking_scripts("https://ejemplo.cl", PAGINA)
    titulos = [f["title"] for f in r["findings"]]
    assert any("Google Tag Manager Detectado" in t for t in titulos)
    assert any("Facebook Pixel Detectado" in t for t in titulos)
    assert not any("Google Tag Manager NO Detectado" in t for t in titulos)


def test_view_source_se_normaliza_y_recupera_el_titulo():
    fuente = (
        "<table>"
        + _fila('<span class="html-tag">&lt;title&gt;</span>En buena mesa<span class="html-tag">&lt;/title&gt;</span>')
        + _fila('<span class="html-tag">&lt;script&gt;</span>var x = 1 &lt; 2;')
        + "</table>"
    )
    n = normalizar_html(fuente)
    assert "<title>En buena mesa</title>" in n
    assert "var x = 1 < 2;" in n


def test_html_normal_no_se_toca():
    assert normalizar_html(PAGINA) == PAGINA


def test_auditoria_url_con_view_source_encuentra_titulo_y_gtm():
    from html import escape
    filas = [_fila('<span class="html-tag">&lt;title&gt;</span>En buena mesa<span class="html-tag">&lt;/title&gt;</span>')]
    for linea in SNIPPET_GTM_INLINE.splitlines():
        filas.append(_fila(escape(linea, quote=False)))
    fuente = "<table>" + "".join(filas) + "</table>"
    r = auditar_url("https://ejemplo.cl", html=fuente)
    assert r["secciones"]["quick"]["website_url"] == "https://ejemplo.cl"
    assert r["secciones"]["gtm"]["metrics"]["contenedores"] == ["GTM-MKF23TH7"]


def test_quick_no_confunde_enlace_a_facebook_con_pixel():
    from auditors.quick_audit import QuickAuditor
    html = '<html><head><title>Escuela de cocina en Santiago</title><meta name="viewport" content="x"></head><body><a href="https://facebook.com/escuela">Facebook</a></body></html>'
    r = QuickAuditor().analizar_html("https://ejemplo.cl", html, 1000)
    titulos = " ".join(f["title"] for f in r["findings"])
    assert "Facebook Pixel" not in titulos
    assert "GA4" not in titulos


def test_quick_detecta_pixel_real():
    from auditors.quick_audit import QuickAuditor
    html = '<html><head><meta name="viewport" content="x"></head><body><script src="https://connect.facebook.net/es_LA/fbevents.js"></script></body></html>'
    r = QuickAuditor().analizar_html("https://ejemplo.cl", html, 1000)
    assert any("Facebook Pixel" in f["title"] for f in r["findings"])


def test_contenido_no_cuenta_scripts_como_texto():
    from auditors.seo_auditor import SEOAuditor
    script = "var x = '" + ("abc " * 5000) + "';"
    html = f"<html><head><title>Escuela de cocina en Santiago de Chile</title></head><body><script>{script}</script><p>Texto visible corto.</p></body></html>"
    r = SEOAuditor().audit({"url": "https://ejemplo.cl", "html": html})
    issues = [f for f in r["metrics"]["contenido"]["findings"] if f["issue"] == "Contenido extenso"]
    assert issues == [] or issues[0]["value"] < 1000


def test_quick_ignora_gtag_comentado():
    from auditors.quick_audit import QuickAuditor
    html = "<html><head><meta name=\"viewport\" content=\"x\"><script>\n  // gtag('config', 'G-JBWEC7QQTS', {});\n</script></head><body>x</body></html>"
    r = QuickAuditor().analizar_html("https://ejemplo.cl", html, 1000)
    assert not any("GA4" in f["title"] for f in r["findings"])


def test_contenido_cuenta_texto_visible_sin_saltos():
    from auditors.seo_auditor import SEOAuditor
    cuerpo = "\n".join(["                <p>Taller de cocina</p>"] * 400)
    html = f"<html><head><title>Escuela de cocina en Santiago de Chile</title></head><body>{cuerpo}</body></html>"
    r = SEOAuditor().audit({"url": "https://ejemplo.cl", "html": html})
    contenido = r["metrics"]["contenido"]["findings"]
    largo = [f["value"] for f in contenido if f["issue"] == "Contenido extenso"]
    assert largo == [] or largo[0] < 10000


def test_imagenes_sin_alt_tienen_tope_en_el_puntaje():
    from auditors.seo_auditor import SEOAuditor
    def puntaje(n):
        imgs = "".join(f'<img src="foto{i}.jpg">' for i in range(n))
        html = f"<html><head><title>Escuela de cocina en Santiago de Chile</title></head><body><h1>x</h1>{imgs}</body></html>"
        return SEOAuditor().audit({"url": "https://ejemplo.cl", "html": html})["metrics"]["contenido"]["score"]
    # Con el tope, 30 y 100 imágenes sin alt dan el mismo descuento (antes 0 en ambos).
    assert puntaje(30) == puntaje(100)
    assert puntaje(30) > 0
