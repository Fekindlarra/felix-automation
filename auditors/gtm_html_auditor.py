#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revisión de Google Tag Manager desde el HTML público (sin API, solo lectura).

Mide solo lo que aparece en el HTML entregado:
- contenedores GTM distintos
- si el snippet está repetido (duplicado)
- si está el bloque noscript
- si existe dataLayer
- si hay Consent Mode v2 configurado por defecto

No inventa puntajes: devuelve hechos. El puntaje lo define el equipo.
"""

import re
from typing import Dict, List

GTM_ID = re.compile(r"GTM-[A-Z0-9]{4,}")
SCRIPT_GTM = re.compile(r"googletagmanager\.com/gtm\.js\?id=(GTM-[A-Z0-9]{4,})")
NOSCRIPT_GTM = re.compile(r"googletagmanager\.com/ns\.html\?id=(GTM-[A-Z0-9]{4,})")
CONSENT_DEFAULT = re.compile(r"gtag\(\s*['\"]consent['\"]\s*,\s*['\"]default['\"]")
DATALAYER = re.compile(r"window\.dataLayer\s*=|var\s+dataLayer\s*=|dataLayer\s*=\s*\[")


def auditar_gtm_html(html: str) -> Dict:
    if not html or not html.strip():
        return {"status": "sin_datos", "motivo": "No hay HTML para analizar.", "metrics": {}}

    scripts: List[str] = SCRIPT_GTM.findall(html)
    noscript: List[str] = NOSCRIPT_GTM.findall(html)
    contenedores = sorted(set(scripts) | set(noscript))

    return {
        "status": "medido",
        "motivo": None,
        "overall_score": None,
        "metrics": {
            "contenedores": contenedores,
            "cantidad_contenedores": len(contenedores),
            "snippet_script_repeticiones": len(scripts),
            "snippet_noscript_presente": bool(noscript),
            "duplicado": len(scripts) > 1 or len(contenedores) > 1,
            "datalayer_presente": bool(DATALAYER.search(html)),
            "consent_mode_default": bool(CONSENT_DEFAULT.search(html)),
        },
    }
