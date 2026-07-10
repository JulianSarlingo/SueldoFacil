"""
main.py — Entrypoint del sistema de recibos (Decreto 407/2026).

Flujo:
    1) Gate de LICENCIA: valida que este equipo esté autorizado para
       'recibos_2026'. Si no lo está, permite generar la solicitud.
    2) Abre la GUI de escritorio (Tkinter).

Modo prueba (sin licencia emitida):
    PowerShell:  $env:RECIBOS_MODO_PRUEBA = "1"; python main.py
    Bash:        RECIBOS_MODO_PRUEBA=1 python main.py

    Para compilar, el comando es:
    # 'pyinstaller --onefile --icon=Icono_v2.ico -n SueldoFacil .\main.py'
"""

from __future__ import annotations

import sys


def main() -> int:
    from recibos_407.seguridad import verificar_licencia
    from recibos_407.version import VERSION
    print(f"Bienvenido a SueldoFácil v{VERSION}\n")
    print("Verificando licencia del equipo...")
    if not verificar_licencia():
        return 1

    print("Licencia OK. Iniciando aplicación...\n")
    from recibos_407.gui.app import iniciar
    iniciar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
