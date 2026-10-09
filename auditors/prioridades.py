#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convierte el informe de auditoria_url en una lista priorizada de cambios.

Cada regla es explícita: impacto y esfuerzo son categorías ("alto", "medio", "bajo"),
definidas aquí y revisables por el equipo. No son mediciones de mercado.
Solo genera hallazgos desde datos medidos; las secciones "no medido" se listan aparte.
"""

from typing import Dict, List

ORDEN = {"alto": 0, "medio": 1, "bajo": 2}


def _hallazgos_seo(seo: Dict) -> List[Dict]:
    out = []
    tecnica = seo.get("metrics", {}).get("tecnica", {}).get("findings", [])
    for f in tecnica:
        issue = f.get("issue", "")
        if issue.startswith("Title muy corto"):
            out.append(_item("SEO", "Alargar el título de la página principal (≥30 caracteres)", "alto", "bajo", issue))
        elif issue.startswith("Meta description muy corta"):
            out.append(_item("SEO", "Alargar la meta descripción (≥50 caracteres)", "alto", "bajo", issue))
    return out


def _hallazgos_gtm(gtm: Dict) -> List[Dict]:
    m = gtm.get("metrics", {})
    out = []
    if m.get("cantidad_contenedores", 0) == 0:
        out.append(_item("Medición", "Instalar Google Tag Manager", "alto", "bajo", "GTM no encontrado en el HTML"))
    else:
        if m.get("duplicado"):
            out.append(_item("Medición", "Quitar el snippet de GTM duplicado", "medio", "bajo", "GTM repetido"))
        if not m.get("consent_mode_default"):
            out.append(_item("Medición", "Configurar Consent Mode v2 por defecto en GTM", "medio", "bajo",
                             "No se encontró gtag('consent','default', …)"))
    return out


def _hallazgos_tracking(tracking: Dict) -> List[Dict]:
    out = []
    titulos = [f.get("title", "") for f in tracking.get("findings", [])]
    if any("Google Analytics NO Detectado" in t for t in titulos):
        out.append(_item("Medición", "Confirmar o activar Google Analytics 4 (no está activo en el HTML)",
                         "alto", "bajo", "GA4 no detectado"))
    if any("Facebook Pixel NO Detectado" in t for t in titulos):
        out.append(_item("Medición", "Instalar el Pixel de Facebook para medir conversiones", "medio", "bajo",
                         "Pixel no detectado"))
    return out


def _hallazgos_seguridad(seo: Dict) -> List[Dict]:
    """Política de privacidad y banner de cookies: se marcan para revisión legal, no se resuelven aquí."""
    out = []
    for f in seo.get("metrics", {}).get("seguridad", {}).get("findings", []):
        issue = f.get("issue", "")
        if issue.startswith("No hay enlace a política de privacidad"):
            out.append(_item("Legal y cookies", "Agregar enlace visible a la política de privacidad", "medio", "bajo", issue))
        elif issue.startswith("No se detecta banner de cookies"):
            out.append(_item("Legal y cookies", "Revisar si corresponde un aviso de cookies con consentimiento (validar con asesoría legal)", "medio", "medio", issue))
    return out


def _hallazgos_quick(quick: Dict) -> List[Dict]:
    out = []
    for f in quick.get("findings", []):
        if "No es mobile-friendly" in f.get("title", ""):
            out.append(_item("Web", "Agregar meta viewport para verse bien en celulares", "alto", "bajo",
                             f.get("description", "")))
    return out


def _item(area: str, accion: str, impacto: str, esfuerzo: str, evidencia: str) -> Dict:
    return {"area": area, "accion": accion, "impacto": impacto, "esfuerzo": esfuerzo, "evidencia": evidencia}


def _medida(sec: Dict) -> bool:
    """Solo una sección medida genera prioridades. Sin medición no hay hallazgos."""
    return sec.get("status") == "medido"


def priorizar(informe: Dict) -> Dict:
    s = informe.get("secciones", {})
    items = []
    if _medida(s.get("seo", {})):
        items += _hallazgos_seo(s["seo"])
        items += _hallazgos_seguridad(s["seo"])
    if _medida(s.get("gtm", {})):
        items += _hallazgos_gtm(s["gtm"])
    if _medida(s.get("tracking", {})):
        items += _hallazgos_tracking(s["tracking"])
    if _medida(s.get("quick", {})):
        items += _hallazgos_quick(s["quick"])
    items.sort(key=lambda i: (ORDEN[i["impacto"]], ORDEN[i["esfuerzo"]]))

    # Secciones que no se pudieron medir (o que faltan) y subsecciones de SEO sin puntaje.
    no_medidas = [nombre for nombre in ("seo", "gtm", "tracking", "quick", "plataforma")
                  if nombre not in s or s[nombre].get("status") in ("sin_datos", "error")]
    for nombre, sub in s.get("seo", {}).get("metrics", {}).items():
        if isinstance(sub, dict) and sub.get("score") is None and "findings" in sub:
            no_medidas.append(f"seo.{nombre}")
    return {
        "url": informe.get("url"),
        "prioridades": items,
        "no_medido": no_medidas,
    }
