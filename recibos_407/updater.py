"""
updater.py — Módulo autocontenido de auto-actualización para ejecutables Windows.

Diseñado para ser copiado tal cual a cualquier proyecto.
NO importa nada del proyecto ni de librerías externas (solo stdlib).

Uso:
    from updater import check_for_updates
    check_for_updates("mi_programa", "1.0.0", "https://...manifest.json")

El manifiesto remoto debe ser un JSON con esta estructura:
    {
        "version": "1.2.0",
        "url": "https://...nuevo.exe",
        "sha256": "abcdef1234...",
        "changelog": "Descripción de cambios"
    }
"""

import hashlib
import json
import os
import sys
import tempfile
import textwrap
import urllib.error
import urllib.request


def _comparar_versiones(v1: str, v2: str) -> int:
    partes1 = [int(x) for x in v1.strip().split(".")]
    partes2 = [int(x) for x in v2.strip().split(".")]
    largo = max(len(partes1), len(partes2))
    partes1.extend([0] * (largo - len(partes1)))
    partes2.extend([0] * (largo - len(partes2)))
    for a, b in zip(partes1, partes2):
        if a < b:
            return -1
        if a > b:
            return 1
    return 0


def _descargar_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "AutoUpdater/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _descargar_archivo(url: str, destino: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "AutoUpdater/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        descargado = 0
        bloque = 64 * 1024
        with open(destino, "wb") as f:
            while True:
                datos = resp.read(bloque)
                if not datos:
                    break
                f.write(datos)
                descargado += len(datos)
                if total:
                    pct = descargado * 100 // total
                    mb = descargado / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    print(f"\r  Descargando: {mb:.1f} / {total_mb:.1f} MB ({pct}%)", end="", flush=True)
                else:
                    mb = descargado / (1024 * 1024)
                    print(f"\r  Descargando: {mb:.1f} MB", end="", flush=True)
    print()


def _verificar_sha256(ruta: str, hash_esperado: str) -> bool:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while True:
            bloque = f.read(64 * 1024)
            if not bloque:
                break
            h.update(bloque)
    return h.hexdigest().lower() == hash_esperado.lower()


def _crear_bat_reemplazo(exe_actual: str, exe_nuevo: str, nombre_imagen: str) -> str:
    bat_contenido = textwrap.dedent(f"""\
        @echo off
        echo Aplicando actualizacion, no cierres esta ventana...
        :esperar
        tasklist /FI "IMAGENAME eq {nombre_imagen}" 2>NUL | find /I "{nombre_imagen}" >NUL
        if not errorlevel 1 (
            timeout /t 1 /nobreak >NUL
            goto esperar
        )
        echo Reemplazando ejecutable...
        move /y "{exe_nuevo}" "{exe_actual}"
        if errorlevel 1 (
            echo ERROR: No se pudo reemplazar el ejecutable.
            pause
            exit /b 1
        )
        echo Relanzando programa...
        start "" "{exe_actual}"
        echo Listo. Esta ventana se cerrara sola.
        (goto) 2>nul & del "%~f0"
    """)
    directorio = os.path.dirname(exe_actual) or "."
    bat_path = os.path.join(directorio, "_updater_temp.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_contenido)
    return bat_path


def check_for_updates(program_id: str, version_actual: str, url_manifiesto: str) -> None:
    if not url_manifiesto:
        print("[Updater] URL del manifiesto no configurada.")
        return

    frozen = getattr(sys, "frozen", False)
    if not frozen:
        print("[Updater] Modo desarrollo detectado (.py, no .exe).")
        print("          El chequeo se ejecutará, pero no se aplicará el reemplazo.")

    print(f"\n[Updater] Consultando actualizaciones para '{program_id}'...")
    try:
        manifiesto = _descargar_json(url_manifiesto)
    except urllib.error.URLError as e:
        print(f"[Updater] Error de red al descargar el manifiesto: {e}")
        return
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[Updater] El manifiesto no es un JSON válido: {e}")
        return
    except Exception as e:
        print(f"[Updater] Error inesperado: {e}")
        return

    for campo in ("version", "url", "sha256"):
        if campo not in manifiesto:
            print(f"[Updater] Manifiesto incompleto: falta el campo '{campo}'.")
            return

    version_remota = manifiesto["version"]
    url_exe = manifiesto["url"]
    hash_esperado = manifiesto["sha256"]
    changelog = manifiesto.get("changelog", "(sin descripción de cambios)")

    cmp = _comparar_versiones(version_actual, version_remota)
    if cmp >= 0:
        print(f"[Updater] Ya tenés la versión más reciente ({version_actual}).")
        return

    print(f"\n  Nueva versión disponible: {version_remota} (actual: {version_actual})")
    print(f"  Cambios: {changelog}\n")

    resp = input("  ¿Descargar e instalar? (s/n): ").strip().lower()
    if resp != "s":
        print("[Updater] Actualización cancelada.")
        return

    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".exe", prefix="update_")
        os.close(tmp_fd)
        _descargar_archivo(url_exe, tmp_path)
    except Exception as e:
        print(f"[Updater] Error al descargar el nuevo ejecutable: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return

    print("  Verificando integridad (SHA-256)...")
    if not _verificar_sha256(tmp_path, hash_esperado):
        print("[Updater] ERROR: El hash no coincide. Descarga corrupta o manipulada.")
        os.remove(tmp_path)
        return
    print("  Hash OK.")

    if not frozen:
        print("\n[Updater] Modo desarrollo: la descarga y verificación funcionaron,")
        print("          pero no se reemplaza nada (no estás corriendo un .exe).")
        os.remove(tmp_path)
        return

    exe_actual = sys.executable
    nombre_imagen = os.path.basename(exe_actual)

    print("  Preparando reemplazo...")
    bat_path = _crear_bat_reemplazo(exe_actual, tmp_path, nombre_imagen)

    os.startfile(bat_path)
    print("  Cerrando para aplicar la actualización...")
    os._exit(0)
