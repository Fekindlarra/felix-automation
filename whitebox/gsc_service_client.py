#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente de Google Search Console (solo lectura) con cuenta de servicio.

La ruta al JSON de la cuenta de servicio NUNCA va en el código ni en el repo.
Se lee desde la variable de entorno GSC_SERVICE_ACCOUNT_FILE, o se pasa explícita.
La cuenta debe tener permiso "Restringido" en la propiedad del cliente.
"""

import os
from datetime import date, timedelta
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
API_URL = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
ENV_KEY_FILE = "GSC_SERVICE_ACCOUNT_FILE"

# Search Console publica datos con retraso de unos 2 a 3 días.
DATA_LAG_DAYS = 3


def load_credentials(key_file: Optional[str] = None):
    """Carga las credenciales de la cuenta de servicio desde una ruta explícita o la variable de entorno."""
    path = key_file or os.environ.get(ENV_KEY_FILE)
    if not path:
        raise RuntimeError(
            f"Falta {ENV_KEY_FILE}: indica la ruta al JSON de la cuenta de servicio (fuera del repo)."
        )
    return service_account.Credentials.from_service_account_file(path, scopes=[SCOPE])


def _ensure_token(creds) -> str:
    """Refresca el token si hace falta y devuelve el valor para el header Authorization."""
    if not creds.valid:
        creds.refresh(Request())
    return creds.token


def query_search_analytics(site_url: str, body: Dict, creds=None, session=None, timeout: int = 20) -> Dict:
    """
    Llama a searchAnalytics.query de Search Console.

    Args:
        site_url: propiedad tal como aparece en Search Console, por ejemplo
                  "https://www.talleresenbuenamesa.cl/" o "sc-domain:ejemplo.cl".
        body: cuerpo de la consulta (startDate, endDate, dimensions, rowLimit, ...).
        creds: credenciales ya cargadas (opcional).
        session: objeto con método post(); por defecto se usa requests (útil para pruebas).
    """
    creds = creds or load_credentials()
    token = _ensure_token(creds)
    url = API_URL.format(site=quote(site_url, safe=""))
    http = session or requests
    response = http.post(
        url,
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def date_window(days: int = 28, lag_days: int = DATA_LAG_DAYS, today: Optional[date] = None):
    """Devuelve (inicio, fin) como fechas ISO, terminando hace lag_days."""
    today = today or date.today()
    end = today - timedelta(days=lag_days)
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def top_queries(site_url: str, days: int = 28, limit: int = 10, creds=None, session=None,
                today: Optional[date] = None) -> List[Dict]:
    """Consultas con más clics en el periodo, con clics, impresiones, CTR y posición."""
    start, end = date_window(days=days, today=today)
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["query"],
        "rowLimit": limit,
    }
    data = query_search_analytics(site_url, body, creds=creds, session=session)
    return data.get("rows", [])


def top_pages(site_url: str, days: int = 28, limit: int = 10, creds=None, session=None,
              today: Optional[date] = None) -> List[Dict]:
    """Páginas con más clics en el periodo."""
    start, end = date_window(days=days, today=today)
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["page"],
        "rowLimit": limit,
    }
    data = query_search_analytics(site_url, body, creds=creds, session=session)
    return data.get("rows", [])
