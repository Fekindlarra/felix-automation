#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoría de una URL con un solo comando (núcleo por URL, sin credenciales).

Descarga el HTML una sola vez (o usa un archivo local) y ejecuta:
- SEO (auditors/seo_auditor.py)
- Scripts de tracking (auditors/tracking_scripts_auditor.py)
- Revisión GTM desde HTML (auditors/gtm_html_auditor.py)
- QuickAudit: responsive, HTTPS, scripts, título, peso (auditors/quick_audit.py)
- Plataforma detectada (auditors/platform_detector.py)

Cada sección es independiente: si una falla, las demás igual se entregan y
la sección fallida queda con status "error" y su motivo. Sin HTML, todo queda "sin_datos".

Uso:
    python -m auditors.auditoria_url https://ejemplo.cl
    python -m auditors.auditoria_url https://ejemplo.cl --html pagina.html --salida informe.json
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from typing import Callable, Dict, Optional

import requests

from auditors.gtm_html_auditor import auditar_gtm_html
from auditors.html_fuente import normalizar_html
from auditors.platform_detector import detectar_plataforma
from auditors.quick_audit import QuickAuditor
from auditors.seo_auditor import SEOAuditor
from auditors.tracking_scripts_auditor import audit_tracking_scripts

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 15


def _normalizar_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def descargar_html(url: str, fetch: Callable = requests.get) -> Dict:
    """Devuelve html, cabeceras y medidas reales de la descarga (o el motivo del error)."""
    try:
        inicio = time.monotonic()
        r = fetch(url, timeout=TIMEOUT_SEGUNDOS, headers={"User-Agent": "FelixAuditor/1.0"})
        r.raise_for_status()
        tiempo = time.monotonic() - inicio
        return {
            "html": r.text,
            "status": "ok",
            "motivo": None,
            "cabeceras": {k.lower(): v for k, v in dict(r.headers).items()},
            "tamano": len(r.content),
            "tiempo": tiempo,
        }
    except Exception as e:
        return {"html": None, "status": "error", "motivo": f"No se pudo descargar la página: {e}"}


def _seccion(fn: Callable[[], Dict]) -> Dict:
    try:
        return fn()
    except Exception as e:
        logger.error(f"Sección falló: {e}", exc_info=True)
        return {"status": "error", "motivo": str(e)}


def auditar_url(url: str, html: Optional[str] = None, fetch: Callable = requests.get) -> Dict:
    """
    Args:
        url: sitio a auditar (se normaliza a https si falta el esquema).
        html: HTML ya disponible (archivo local). Si viene, no se descarga nada.
        fetch: función HTTP (inyectable para pruebas).
    """
    url = _normalizar_url(url)
    origen = {"tipo": "archivo", "status": "ok", "motivo": None}
    datos_http = {}  # solo existen si se descargó: cabeceras, tamaño y tiempo reales

    if html is None:
        d = descargar_html(url, fetch=fetch)
        origen = {"tipo": "descarga", "status": d["status"], "motivo": d["motivo"]}
        html = d["html"]
        if html is not None:
            datos_http = {"headers": d["cabeceras"], "page_size": d["tamano"], "load_time": d["tiempo"]}

    html = normalizar_html(html)

    informe = {
        "url": url,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "origen_html": origen,
        "secciones": {},
    }

    if not html:
        sin = {"status": "sin_datos", "motivo": origen["motivo"] or "No hay HTML para analizar."}
        for nombre in ("seo", "tracking", "gtm", "quick", "plataforma"):
            informe["secciones"][nombre] = dict(sin)
        return informe

    informe["secciones"]["seo"] = _seccion(
        lambda: {**SEOAuditor().audit({"url": url, "html": html, **datos_http}), "status": "medido"}
    )
    informe["secciones"]["tracking"] = _seccion(
        lambda: {**audit_tracking_scripts(url, html), "status": "medido"}
    )
    informe["secciones"]["gtm"] = _seccion(lambda: auditar_gtm_html(html))
    informe["secciones"]["quick"] = _seccion(
        lambda: {**QuickAuditor().analizar_html(url, html, len(html.encode("utf-8"))), "status": "medido"}
    )
    informe["secciones"]["plataforma"] = _seccion(
        lambda: {"status": "medido", "detectadas": detectar_plataforma(html)}
    )
    return informe


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Auditoría de una URL (sin credenciales)")
    p.add_argument("url")
    p.add_argument("--html", help="archivo HTML local en lugar de descargar la URL")
    p.add_argument("--salida", help="archivo JSON de salida (por defecto, imprime en pantalla)")
    args = p.parse_args(argv)

    html = None
    if args.html:
        with open(args.html, encoding="utf-8") as f:
            html = f.read()

    informe = auditar_url(args.url, html=html)
    texto = json.dumps(informe, ensure_ascii=False, indent=2, default=str)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"Informe guardado en {args.salida}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
