"""
Seguridad — Gate de licencia para el programa 'recibos_2026'.

Integra el paquete compartido Seguridad (seguridad-licencias) sin
modificarlo: registra el programa en runtime sobre PROGRAMAS_VALIDOS.
"""

from __future__ import annotations

import os

PROGRAMA = "recibos_2026"

# Variable de entorno para desarrollo (sin licencia emitida todavía).
#   PowerShell:  $env:RECIBOS_MODO_PRUEBA = "1"; python main.py
#   Bash:        RECIBOS_MODO_PRUEBA=1 python main.py
MODO_PRUEBA = os.environ.get("RECIBOS_MODO_PRUEBA") == "1"


def _registrar_programa() -> bool:
    """Registra 'recibos_2026' en el módulo Seguridad en runtime."""
    try:
        from Seguridad import firestore as _fs
        from Seguridad import interfaz as _ui
    except ImportError:
        return False

    if PROGRAMA not in _fs.PROGRAMAS_VALIDOS:
        _fs.PROGRAMAS_VALIDOS[PROGRAMA] = PROGRAMA
    if PROGRAMA not in _ui.PROGRAMAS_VALIDOS:
        _ui.PROGRAMAS_VALIDOS = tuple(_ui.PROGRAMAS_VALIDOS) + (PROGRAMA,)
    return True


def verificar_licencia() -> bool:
    """
    Gate de licencia. Verifica/solicita autorización por consola.

    Returns:
        True si el equipo está autorizado (o si MODO_PRUEBA está activo).
    """
    if not _registrar_programa():
        if MODO_PRUEBA:
            print("[Licencia] Módulo Seguridad no disponible — modo prueba.")
            return True
        print(
            "[Licencia] No se encontró el paquete 'Seguridad'. Instalalo con:\n"
            '  pip install -e "C:\\Users\\Julian\\Desktop\\Programacion\\libs\\seguridad-licencias"'
        )
        return False

    from Seguridad import licencia

    hwid = licencia.obtener_hwid()

    if licencia.licencia_autorizada(hwid, PROGRAMA):
        return True

    if MODO_PRUEBA:
        print("[Licencia] Sin licencia real — modo prueba activo.")
        return True

    # No autorizado: verificar solicitud pendiente o crear una nueva.
    if licencia.solicitud_existente(hwid, PROGRAMA):
        print("\nYa existe una solicitud pendiente para este equipo.")
        print("Esperá la aprobación del administrador.")
        input("\nPresioná Enter para salir...")
        return False

    print(f"\nEste equipo no está autorizado para {PROGRAMA}.")
    nombre = input("Ingresá un nombre para identificar este equipo: ")
    if licencia.crear_solicitud(hwid, nombre, PROGRAMA):
        print("\nSolicitud enviada. Esperá la aprobación.")
    else:
        print("\nError al enviar la solicitud.")
    input("\nPresioná Enter para salir...")
    return False
