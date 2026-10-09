#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flujo completo en un comando: auditar, priorizar y, si hay informe anterior, comparar.

Uso:
    python -m auditors.flujo_correccion https://ejemplo.cl --salida informe.json
    python -m auditors.flujo_correccion https://ejemplo.cl --html pagina.html --anterior informe_antes.json --salida informe_despues.json

Guarda el informe completo y, en la pantalla, la lista priorizada y la comparación.
"""

import argparse
import json
import sys

from auditors.auditoria_url import auditar_url
from auditors.comparar_informes import comparar
from auditors.prioridades import priorizar


def ejecutar(url: str, html=None, anterior=None) -> dict:
    informe = auditar_url(url, html=html)
    resultado = {
        "informe": informe,
        "prioridades": priorizar(informe),
    }
    if anterior is not None:
        resultado["comparacion"] = comparar(anterior, informe)
    return resultado


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Auditar, priorizar y comparar una URL")
    p.add_argument("url")
    p.add_argument("--html", help="HTML local en lugar de descargar la URL")
    p.add_argument("--anterior", help="informe JSON anterior para comparar")
    p.add_argument("--salida", help="archivo JSON de salida")
    args = p.parse_args(argv)

    html = None
    if args.html:
        with open(args.html, encoding="utf-8") as f:
            html = f.read()
    anterior = None
    if args.anterior:
        with open(args.anterior, encoding="utf-8") as f:
            anterior = json.load(f)

    resultado = ejecutar(args.url, html=html, anterior=anterior)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"Resultado guardado en {args.salida}")
    if "comparacion" in resultado:
        c = resultado["comparacion"]
        print(f"Resueltas: {len(c['resueltas'])} · Pendientes: {len(c['pendientes'])} · Nuevas: {len(c['nuevas'])}")
    print("Prioridades:")
    for i in resultado["prioridades"]["prioridades"]:
        print(f"- [{i['impacto']} impacto / {i['esfuerzo']} esfuerzo] {i['accion']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
