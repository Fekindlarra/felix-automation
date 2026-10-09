#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tabla comparativa de varios sitios a partir de sus informes de auditoría.

Usa solo hechos medidos (título, meta descripción, GTM, GA4, Pixel, Consent Mode,
políticas legales, imágenes sin texto alternativo, plataforma, puntaje interno).
Cada columna es un informe. Si un dato no se midió, aparece como "no medido".

Uso:
    python -m auditors.comparar_competidores propio.json kitchen.json 2x3.json
"""

import json
import sys
from typing import Dict, List


def _titulo(informe: Dict) -> str:
    t = informe["secciones"].get("quick", {})
    return t.get("website_url", "no medido")


def _seo_metric(informe: Dict, categoria: str, issue_prefix: str) -> str:
    seo = informe["secciones"].get("seo", {})
    hallazgos = seo.get("metrics", {}).get(categoria, {}).get("findings", [])
    for f in hallazgos:
        if f.get("issue", "").startswith(issue_prefix):
            return "alerta: " + f["issue"]
    if seo.get("status") != "medido":
        return "no medido"
    return "sin alerta"


def _tracking(informe: Dict, nombre: str) -> str:
    tr = informe["secciones"].get("tracking", {})
    if tr.get("status") != "medido":
        return "no medido"
    titulos = [f.get("title", "") for f in tr.get("findings", []) if nombre in f.get("title", "")]
    if any("NO Detectado" in t for t in titulos):
        return "no"
    if any("Detectado" in t for t in titulos):
        return "sí"
    return "no medido"


def _ga4(informe: Dict) -> str:
    """GA4 puede cargarse dentro de Tag Manager; en ese caso el HTML no muestra el ID."""
    resultado = _tracking(informe, "Google Analytics")
    if resultado == "no" and informe["secciones"].get("gtm", {}).get("metrics", {}).get("contenedores"):
        return "revisar en GTM (ID no visible en el HTML)"
    return resultado


def _gtm(informe: Dict) -> str:
    g = informe["secciones"].get("gtm", {}).get("metrics", {})
    if not g:
        return "no medido"
    ids = g.get("contenedores", [])
    if ids:
        return ", ".join(ids)
    return "no"


def _consent(informe: Dict) -> str:
    g = informe["secciones"].get("gtm", {}).get("metrics", {})
    if not g:
        return "no medido"
    return "sí" if g.get("consent_mode_default") else "no"


def _imagenes_sin_alt(informe: Dict) -> str:
    seo = informe["secciones"].get("seo", {})
    for f in seo.get("metrics", {}).get("contenido", {}).get("findings", []):
        if f.get("issue", "").startswith("Imágenes sin alt text"):
            return str(f["value"])
    return "0" if seo.get("status") == "medido" else "no medido"


def _plataforma(informe: Dict) -> str:
    p = informe["secciones"].get("plataforma", {})
    if p.get("status") != "medido":
        return "no medido"
    det = [d["platform"] for d in p.get("detectadas", [])]
    return ", ".join(det) if det else "ninguna de las tres"


def _puntaje(informe: Dict) -> str:
    v = informe["secciones"].get("seo", {}).get("overall_score")
    return str(v) if v is not None else "no medido"


FILAS = [
    ("Título", lambda i: _seo_metric(i, "tecnica", "Title muy corto")),
    ("Meta descripción", lambda i: _seo_metric(i, "tecnica", "Meta description muy corta")),
    ("Google Tag Manager", _gtm),
    ("Google Analytics 4", _ga4),
    ("Facebook Pixel", lambda i: _tracking(i, "Facebook Pixel")),
    ("Universal Analytics (obsoleto)", lambda i: _tracking(i, "Universal Analytics")),
    ("Consent Mode v2 por defecto", _consent),
    ("Imágenes sin texto alternativo", _imagenes_sin_alt),
    ("Plataforma", _plataforma),
    ("Puntaje SEO (reglas internas)", _puntaje),
]


def tabla(informes: List[Dict], nombres: List[str]) -> str:
    encabezado = "| Punto | " + " | ".join(nombres) + " |"
    separador = "|---|" + "|".join("---" for _ in nombres) + "|"
    lineas = [encabezado, separador]
    for etiqueta, fn in FILAS:
        valores = [fn(i) for i in informes]
        lineas.append(f"| {etiqueta} | " + " | ".join(valores) + " |")
    return "\n".join(lineas)


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Uso: python -m auditors.comparar_competidores INFORME1.json INFORME2.json ...")
        return 1
    informes, nombres = [], []
    for ruta in argv[1:]:
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
        informe = d.get("informe", d)
        informes.append(informe)
        nombres.append(informe.get("url", ruta))
    print(tabla(informes, nombres))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
