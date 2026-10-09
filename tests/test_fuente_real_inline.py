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
