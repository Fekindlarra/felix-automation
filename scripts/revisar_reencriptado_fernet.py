#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revisa y, si se pide, re-encripta valores Fernet guardados en una base SQLite
al rotar WHITEBOX_MASTER_KEY.

Por defecto NO escribe nada: solo cuenta cuántos valores cifrados hay y si
la clave antigua los abre. Para escribir hay que pasar --aplicar, y antes se
guarda una copia de la base.

Claves (por variables de entorno, para no dejarlas en el historial de la terminal):
    WHITEBOX_KEY_ANTIGUA   clave que hoy abre los datos
    WHITEBOX_KEY_NUEVA     clave nueva (solo con --aplicar)

Uso:
    python scripts/revisar_reencriptado_fernet.py BASE.db
    python scripts/revisar_reencriptado_fernet.py BASE.db --aplicar
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

PREFIJO_FERNET = "gAAAAA"


def columnas_texto(conn, tabla):
    cols = []
    for _, nombre, tipo, *_ in conn.execute(f'PRAGMA table_info("{tabla}")'):
        if tipo is None or "CHAR" in tipo.upper() or "TEXT" in tipo.upper() or tipo == "":
            cols.append(nombre)
    return cols


def recorrer(conn, aplicar=False, clave_antigua=None, clave_nueva=None):
    """Devuelve un resumen por tabla y columna. Con aplicar=True re-encripta las filas."""
    resumen = []
    for (tabla,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        for col in columnas_texto(conn, tabla):
            filas = conn.execute(
                f'SELECT rowid, "{col}" FROM "{tabla}" WHERE CAST("{col}" AS TEXT) LIKE ?',
                (PREFIJO_FERNET + "%",),
            ).fetchall()
            if not filas:
                continue
            abiertas = sin_abrir = reencriptadas = 0
            for rowid, valor in filas:
                try:
                    texto = clave_antigua.decrypt(valor.encode() if isinstance(valor, str) else valor)
                    abiertas += 1
                except (InvalidToken, AttributeError, TypeError):
                    sin_abrir += 1
                    continue
                if aplicar:
                    nuevo = clave_nueva.encrypt(texto).decode()
                    conn.execute(f'UPDATE "{tabla}" SET "{col}" = ? WHERE rowid = ?', (nuevo, rowid))
                    reencriptadas += 1
            resumen.append({
                "tabla": tabla, "columna": col, "total": len(filas),
                "abiertas_con_clave_antigua": abiertas,
                "no_abiertas": sin_abrir, "reencriptadas": reencriptadas,
            })
    return resumen


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("base", help="Ruta a la base SQLite")
    p.add_argument("--aplicar", action="store_true", help="Escribir cambios (hace copia antes)")
    args = p.parse_args(argv)

    ruta = Path(args.base)
    if not ruta.exists():
        print(f"No existe la base: {ruta}")
        return 1

    antigua = os.getenv("WHITEBOX_KEY_ANTIGUA")
    if not antigua:
        print("Falta WHITEBOX_KEY_ANTIGUA en el entorno.")
        return 1
    try:
        clave_antigua = Fernet(antigua.encode())
    except ValueError:
        print("WHITEBOX_KEY_ANTIGUA no es una clave Fernet válida.")
        return 1

    clave_nueva = None
    if args.aplicar:
        nueva = os.getenv("WHITEBOX_KEY_NUEVA")
        if not nueva:
            print("Con --aplicar falta WHITEBOX_KEY_NUEVA en el entorno.")
            return 1
        try:
            clave_nueva = Fernet(nueva.encode())
        except ValueError:
            print("WHITEBOX_KEY_NUEVA no es una clave Fernet válida.")
            return 1
        copia = ruta.with_name(f"{ruta.stem}_respaldo_{datetime.now():%Y%m%d_%H%M%S}{ruta.suffix}")
        shutil.copy2(ruta, copia)
        print(f"Copia de respaldo: {copia}")

    conn = sqlite3.connect(ruta)
    try:
        resumen = recorrer(conn, aplicar=args.aplicar, clave_antigua=clave_antigua, clave_nueva=clave_nueva)
        if args.aplicar:
            conn.commit()
    finally:
        conn.close()

    if not resumen:
        print("No se encontraron valores Fernet en esta base. No hace falta re-encriptar.")
        return 0

    print(f"{'Tabla':<28}{'Columna':<20}{'Total':>7}{'Abiertas':>10}{'No abiertas':>13}{'Reencriptadas':>15}")
    for r in resumen:
        print(f"{r['tabla']:<28}{r['columna']:<20}{r['total']:>7}"
              f"{r['abiertas_con_clave_antigua']:>10}{r['no_abiertas']:>13}{r['reencriptadas']:>15}")
    no_abiertas = sum(r["no_abiertas"] for r in resumen)
    if no_abiertas:
        print(f"\nAtención: {no_abiertas} valores no se abren con la clave antigua. No se tocan. Revisar antes de rotar.")
        return 2
    print("\nTodos los valores se abren con la clave antigua." + (" Re-encriptados." if args.aplicar else " Ejecutar con --aplicar solo después de confirmar."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
