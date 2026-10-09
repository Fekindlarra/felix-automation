#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compara dos informes de auditoría de la misma URL (antes y después de los cambios).

Clasifica cada acción priorizada como:
- resuelta: estaba en el informe anterior y ya no aparece
- pendiente: sigue apareciendo
- nueva: aparece solo en el informe nuevo (algo empeoró o es un hallazgo nuevo)

Solo compara acciones derivadas de datos medidos (ver auditors/prioridades.py).
"""

import json
import sys
from typing import Dict, List

from auditors.prioridades import priorizar


def _claves(prioridades: Dict) -> Dict[str, Dict]:
    return {i["accion"]: i for i in prioridades.get("prioridades", [])}


def comparar(anterior: Dict, nuevo: Dict) -> Dict:
    p_ant = priorizar(anterior)
    p_nue = priorizar(nuevo)
    ant, nue = _claves(p_ant), _claves(p_nue)

    return {
        "url": nuevo.get("url") or anterior.get("url"),
        "resueltas": [ant[a] for a in ant if a not in nue],
        "pendientes": [nue[a] for a in nue if a in ant],
        "nuevas": [nue[a] for a in nue if a not in ant],
        "no_medido_antes": p_ant["no_medido"],
        "no_medido_ahora": p_nue["no_medido"],
    }


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("Uso: python -m auditors.comparar_informes ANTERIOR.json NUEVO.json")
        return 1
    with open(argv[1], encoding="utf-8") as f:
        anterior = json.load(f)
    with open(argv[2], encoding="utf-8") as f:
        nuevo = json.load(f)
    print(json.dumps(comparar(anterior, nuevo), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
