#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditor de Google Search Console (white-box, solo lectura)

Usa whitebox/gsc_service_client.py (cuenta de servicio con permiso restringido).
Regla: nunca inventa cifras. Si no hay conexión o la API no devuelve filas,
el reporte queda en estado "sin_datos" con overall_score None.
"""

import logging
from typing import Dict, List, Optional

from whitebox import gsc_service_client as client

logger = logging.getLogger(__name__)

DIAS_POR_DEFECTO = 28
LIMITE_FILAS = 10


class GSCAuditor:
    """Auditor de Search Console basado en métricas medidas"""

    def __init__(self, credentials: Optional[Dict] = None):
        """
        Args:
            credentials: {
                'site_url': str,            # propiedad tal como está en GSC
                'service_account_file': str # opcional; si falta, se usa GSC_SERVICE_ACCOUNT_FILE
                'creds': credenciales ya cargadas (opcional, pruebas)
                'session': objeto opcional con post() (pruebas)
            }
        """
        self.platform = "gsc"
        self.credentials = credentials or {}
        self.site_url = self.credentials.get("site_url")
        self.is_connected = bool(self.site_url)
        self.audit_date = None
        self.findings: List[Dict] = []
        self.metrics: Dict = {}
        self.overall_score: Optional[int] = None

    def audit(self, site_data: Optional[Dict] = None) -> Dict:
        if not self.is_connected:
            return self._sin_datos("No hay propiedad de Search Console indicada (site_url).")

        try:
            creds = self.credentials.get("creds")
            if creds is None:
                creds = client.load_credentials(self.credentials.get("service_account_file"))
            session = self.credentials.get("session")

            consultas = client.top_queries(
                self.site_url, days=DIAS_POR_DEFECTO, limit=LIMITE_FILAS, creds=creds, session=session
            )
            paginas = client.top_pages(
                self.site_url, days=DIAS_POR_DEFECTO, limit=LIMITE_FILAS, creds=creds, session=session
            )
        except Exception as e:
            logger.error(f"Error consultando Search Console: {e}")
            return self._sin_datos(f"No se pudo consultar Search Console: {e}")

        if not consultas and not paginas:
            return self._sin_datos("Search Console no devolvió filas para el periodo.")

        self._medir(consultas, paginas)
        return self._generate_report()

    def _medir(self, consultas: List[Dict], paginas: List[Dict]):
        """Resume las filas medidas. Sin puntaje: el puntaje lo define el equipo, no el código."""
        clics = sum(r.get("clicks", 0) for r in consultas)
        impresiones = sum(r.get("impressions", 0) for r in consultas)
        posicion_ponderada = (
            sum(r.get("position", 0) * r.get("impressions", 0) for r in consultas) / impresiones
            if impresiones else None
        )
        self.metrics = {
            "dias": DIAS_POR_DEFECTO,
            "clics_top_consultas": clics,
            "impresiones_top_consultas": impresiones,
            "ctr_top_consultas": round(clics / impresiones, 4) if impresiones else None,
            "posicion_media_ponderada": round(posicion_ponderada, 2) if posicion_ponderada is not None else None,
            "top_consultas": [
                {"consulta": r["keys"][0], "clics": r.get("clicks", 0),
                 "impresiones": r.get("impressions", 0), "posicion": round(r.get("position", 0), 2)}
                for r in consultas if r.get("keys")
            ],
            "top_paginas": [
                {"url": r["keys"][0], "clics": r.get("clicks", 0), "impresiones": r.get("impressions", 0)}
                for r in paginas if r.get("keys")
            ],
        }
        self.findings.append({
            "severity": "INFO",
            "title": "📈 Búsqueda orgánica medida",
            "description": f"{clics} clics e {impresiones} impresiones en las top consultas de los últimos {DIAS_POR_DEFECTO} días.",
            "category": "performance",
        })

    def _sin_datos(self, motivo: str) -> Dict:
        return {
            "platform": self.platform,
            "overall_score": None,
            "status": "sin_datos",
            "motivo": motivo,
            "metrics": {},
            "findings": [],
        }

    def _generate_report(self) -> Dict:
        return {
            "platform": self.platform,
            "overall_score": None,
            "status": "medido",
            "motivo": None,
            "metrics": self.metrics,
            "findings": self.findings,
        }


def audit_gsc(credentials: Optional[Dict] = None, site_data: Optional[Dict] = None) -> Dict:
    """Función helper para auditar Google Search Console"""
    return GSCAuditor(credentials).audit(site_data)
