"""
Detector de plataforma desde el HTML de un sitio (sin credenciales).

Señales VERIFICADAS con páginas públicas (2026-10-08, vía lectura de página):
  - Shopify: recursos en cdn.shopify.com y etiqueta shopify-digital-wallet
    (ejemplo observado: allbirds.com)
  - Wix: <meta name="generator" content="Wix.com Website Builder"> y recursos
    en static.wixstatic.com (ejemplo observado: wix.com)

NO incluido: Jumpseller. Las señales observadas corresponden al sitio corporativo
de Jumpseller, no a una tienda de cliente; no se puede afirmar una señal de tienda.
Antes de incluirla, verificar con una tienda Jumpseller real.

Nota: las señales se confirmaron leyendo la página, no con bytes crudos. Revisar
con HTML crudo antes de usar el resultado con un cliente.
"""
import re
from typing import Dict, List

SENALES = {
    "shopify": [
        re.compile(r"cdn\.shopify\.com", re.I),
        re.compile(r"shopify-digital-wallet", re.I),
    ],
    "wix": [
        re.compile(r"static\.wixstatic\.com", re.I),
        re.compile(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']Wix\.com Website Builder["\']', re.I),
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
