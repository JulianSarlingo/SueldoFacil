"""
generar_manifest.py — Genera el manifest.json para publicar una actualización
del programa 'recibos_2026' (ver recibos_407/version.py).

Calcula el SHA-256 del .exe y arma el manifest.json en la carpeta actual.

USO:
    python release/generar_manifest.py <ruta_exe> <version> <url_del_exe> "<changelog>"

EJEMPLO:
    python release/generar_manifest.py dist/SueldoFacil.exe 1.0.1 "https://github.com/JulianSarlingo/SueldoFacil/releases/download/v1.0.1/SueldoFacil.exe" "Que cambio en esta version"

DESPUES: subí el manifest.json generado al release con tag 'latest' del repo
(el mismo que apunta URL_MANIFIESTO en recibos_407/version.py), reemplazando
el manifest.json anterior. El updater (recibos_407/updater.py) compara la
versión acá publicada contra recibos_407/version.py:VERSION en cada arranque.
"""

import hashlib
import json
import os
import sys


def calcular_sha256(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while True:
            bloque = f.read(64 * 1024)
            if not bloque:
                break
            h.update(bloque)
    return h.hexdigest()


def main():
    if len(sys.argv) != 5:
        print("Uso: python generar_manifest.py <ruta_exe> <version> <url_exe> <changelog>")
        sys.exit(1)

    ruta_exe = sys.argv[1]
    version = sys.argv[2]
    url_exe = sys.argv[3]
    changelog = sys.argv[4]

    if not os.path.isfile(ruta_exe):
        print(f"Error: no se encontró el archivo '{ruta_exe}'.")
        sys.exit(1)

    sha = calcular_sha256(ruta_exe)
    print(f"SHA-256: {sha}")

    manifiesto = {
        "version": version,
        "url": url_exe,
        "sha256": sha,
        "changelog": changelog,
    }

    salida = "manifest.json"
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(manifiesto, f, indent=2, ensure_ascii=False)

    print(f"Manifiesto generado: {salida}")
    print(json.dumps(manifiesto, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
