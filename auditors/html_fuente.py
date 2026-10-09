#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normaliza HTML que llega como "ver código fuente" del navegador.

Ese formato trae números de línea, etiquetas <span> y el markup escapado
(&lt;title&gt;). Si se audita tal cual, los auditores ven texto en vez de etiquetas.
Esta función devuelve el HTML original. Si el texto no es vista de código fuente, lo deja igual.
"""

import html as html_lib
import re

_MARCA = 'class="line-content"'
_CELDA = re.compile(r'<td class="line-content">(.*?)</td>', re.DOTALL)
_ETIQUETA = re.compile(r"<[^>]+>")


def normalizar_html(texto: str) -> str:
    if not texto or _MARCA not in texto:
        return texto
    lineas = []
    for celda in _CELDA.findall(texto):
        lineas.append(html_lib.unescape(_ETIQUETA.sub("", celda)))
    return "\n".join(lineas)
