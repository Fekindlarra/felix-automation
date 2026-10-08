"""Detector de plataforma (auditors/platform_detector.py).
Señales verificadas: cdn.shopify.com, shopify-digital-wallet, Wix generator, static.wixstatic.com.
Jumpseller NO está en el detector a propósito (sin señal verificada de tienda)."""
from auditors.platform_detector import detectar_plataforma


def test_detecta_shopify_por_cdn():
    html = '<img src="https://cdn.shopify.com/s/files/1/abc.png">'
    plataformas = [p["platform"] for p in detectar_plataforma(html)]
    assert plataformas == ["shopify"]


def test_detecta_shopify_por_meta():
    html = '<meta name="shopify-digital-wallet" content="x">'
    assert [p["platform"] for p in detectar_plataforma(html)] == ["shopify"]


def test_detecta_wix_por_generator():
    html = '<meta name="generator" content="Wix.com Website Builder">'
    assert [p["platform"] for p in detectar_plataforma(html)] == ["wix"]


def test_detecta_wix_por_cdn():
    html = '<img src="https://static.wixstatic.com/media/a.jpg">'
    assert [p["platform"] for p in detectar_plataforma(html)] == ["wix"]


def test_sitio_generico_no_detecta_nada():
    html = "<html><head><title>Mi sitio</title></head><body>hola</body></html>"
    assert detectar_plataforma(html) == []


def test_jumpseller_no_se_detecta_sin_senal_verificada():
    html = '<meta property="og:site_name" content="Jumpseller">'
    assert detectar_plataforma(html) == []
