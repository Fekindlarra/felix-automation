"""Bloqueante 3.4.4: QuickHTMLParser debe capturar el <title>.
Antes, handle_data tenía 'pass' y el título quedaba vacío (falso negativo)."""
from auditors.quick_audit import QuickHTMLParser


def test_captura_titulo_de_la_pagina():
    html = "<html><head><title>Zapatos de cuero en Santiago</title></head><body></body></html>"
    p = QuickHTMLParser()
    p.feed(html)
    assert p.title == "Zapatos de cuero en Santiago"


def test_titulo_vacio_sigue_vacio():
    p = QuickHTMLParser()
    p.feed("<html><head><title></title></head></html>")
    assert p.title == ""
