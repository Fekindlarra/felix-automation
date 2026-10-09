"""
Detector de plataforma desde el HTML de un sitio (sin credenciales).

Señales VERIFICADAS con páginas públicas (2026-10-08, vía lectura de página):
  - Shopify: recursos en cdn.shopify.com y etiqueta shopify-digital-wallet
    (ejemplo observado: allbirds.com). HTML crudo confirmado en raicesdecauquenes.cl
    (tienda con dominio propio): id="shopify-features", dominio *.myshopify.com,
    fonts.shopifycdn.com y cdn.shopify.com
  - Wix: <meta name="generator" content="Wix.com Website Builder"> y recursos
    en static.wixstatic.com (ejemplo observado: wix.com). HTML crudo confirmado
    en un sitio Wix: id="wixDesktopViewport" e id="wix-essential-viewer-model"
  - Jumpseller: recursos en images./assets./cdnx.jumpseller.com y enlace de pie
    "Desarrollado por Jumpseller" con utm_campaign=powered_by
    (ejemplo observado: talleresenbuenamesa.cl, tienda de Felipe)

Nota: los ejemplos se confirmaron leyendo la página, no con bytes crudos.

Nota: las señales se confirmaron leyendo la página, no con bytes crudos. Revisar
con HTML crudo antes de usar el resultado con un cliente.
"""
import re
from typing import Dict, List

SENALES = {
    "shopify": [
        re.compile(r"cdn\.shopify\.com", re.I),
        re.compile(r"shopify-digital-wallet", re.I),
        re.compile(r'id=["\']shopify-features["\']', re.I),
        re.compile(r"[\w-]+\.myshopify\.com", re.I),
        re.compile(r"fonts\.shopifycdn\.com", re.I),
    ],
    "wix": [
        re.compile(r"static\.wixstatic\.com", re.I),
        re.compile(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']Wix\.com Website Builder["\']', re.I),
        re.compile(r'id=["\']wixDesktopViewport["\']', re.I),
        re.compile(r'id=["\']wix-essential-viewer-model["\']', re.I),
    ],
    "jumpseller": [
        re.compile(r"(images|assets|cdnx|files)\.jumpseller\.com", re.I),
        re.compile(r"utm_campaign=powered_by", re.I),
    ],
}


def detectar_plataforma(html: str) -> List[Dict]:
    """Devuelve las plataformas detectadas y la evidencia encontrada.

    Lista vacía = no se detectó ninguna plataforma con las señales verificadas.
    No significa que el sitio no use una plataforma.
    """
    resultado = []
    for plataforma, patrones in SENALES.items():
        evidencia = [p.pattern for p in patrones if p.search(html or "")]
        if evidencia:
            resultado.append({"platform": plataforma, "evidence": evidencia})
    return resultado
