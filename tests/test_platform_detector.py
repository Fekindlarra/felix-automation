"""Detector de plataforma (auditors/platform_detector.py).
Señales verificadas: cdn.shopify.com, shopify-digital-wallet, Wix generator, static.wixstatic.com.
Jumpseller usa señales de tienda observadas en talleresenbuenamesa.cl."""
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


def test_detecta_jumpseller_por_cdn():
    html = '<img src="https://cdnx.jumpseller.com/en-buena-mesa/image/1/thumb/306/306">'
    assert [p["platform"] for p in detectar_plataforma(html)] == ["jumpseller"]


def test_detecta_jumpseller_por_pie_de_pagina():
    html = '<a href="https://jumpseller.cl/?utm_medium=store&utm_campaign=powered_by">Desarrollado por Jumpseller</a>'
    assert [p["platform"] for p in detectar_plataforma(html)] == ["jumpseller"]


def test_sitio_corporativo_jumpseller_no_cuenta_como_tienda():
    # og:site_name de la web corporativa de Jumpseller no es señal de tienda
    html = '<meta property="og:site_name" content="Jumpseller">'
    assert detectar_plataforma(html) == []


def test_detecta_jumpseller_por_preconnect_del_html_crudo():
    # Fragmento real del <head> de talleresenbuenamesa.cl (HTML crudo)
    html = '<link rel="preconnect" href="https://files.jumpseller.com">'
    assert [p["platform"] for p in detectar_plataforma(html)] == ["jumpseller"]
