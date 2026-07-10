"""
configuracion.py
-----------------
Configuración simple por usuario/instalación: qué gremio se usa para
liquidar. Se guarda en un JSON en la carpeta de datos del usuario
(%APPDATA%/SueldoFacil/config.json), fuera de la carpeta del .exe, para
que la elección del gremio sobreviva a cada actualización del programa
(el updater reemplaza el ejecutable, no esta carpeta).

Uso:
    from recibos_407.config.configuracion import gremio_actual, guardar_gremio

    g = gremio_actual()                       # Gremio activo (o el default)
    guardar_gremio("comercio_faecys")         # elegir un preset
    guardar_gremio("personalizado", "Mi aporte", 1.2)   # gremio a medida
"""

from __future__ import annotations

import json
import os

from .gremios import Gremio, GREMIOS_PREDEFINIDOS, GREMIO_POR_DEFECTO

_NOMBRE_ARCHIVO = "config.json"


def _carpeta_datos() -> str:
    """Carpeta de datos del usuario. Se lee en cada llamada (no cachear)
    para que los tests puedan redirigirla cambiando la variable de entorno."""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    carpeta = os.path.join(base, "SueldoFacil")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def _ruta_config() -> str:
    return os.path.join(_carpeta_datos(), _NOMBRE_ARCHIVO)


def gremio_actual() -> Gremio:
    """Gremio configurado por el usuario. Si no configuró nada todavía
    (o el archivo está corrupto), devuelve el gremio por defecto."""
    ruta = _ruta_config()
    if not os.path.exists(ruta):
        return GREMIOS_PREDEFINIDOS[GREMIO_POR_DEFECTO]

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (json.JSONDecodeError, OSError):
        return GREMIOS_PREDEFINIDOS[GREMIO_POR_DEFECTO]

    gremio_id = datos.get("gremio_id", GREMIO_POR_DEFECTO)

    if gremio_id == "personalizado":
        return Gremio(
            id="personalizado",
            nombre="Personalizado",
            aporte_adicional_nombre=datos.get("aporte_adicional_nombre", ""),
            aporte_adicional_pct=float(datos.get("aporte_adicional_pct", 0.0)),
        )

    return GREMIOS_PREDEFINIDOS.get(gremio_id, GREMIOS_PREDEFINIDOS[GREMIO_POR_DEFECTO])


def guardar_gremio(
    gremio_id: str,
    aporte_adicional_nombre: str = "",
    aporte_adicional_pct: float = 0.0,
) -> None:
    """
    Guarda el gremio elegido.

    Args:
        gremio_id: clave en GREMIOS_PREDEFINIDOS (ej. "comercio_faecys")
            o "personalizado".
        aporte_adicional_nombre, aporte_adicional_pct: solo se usan
            cuando gremio_id == "personalizado"; para un preset se
            ignoran (el preset ya trae sus propios valores fijos).
    """
    if gremio_id not in GREMIOS_PREDEFINIDOS:
        raise ValueError(f"Gremio desconocido: {gremio_id!r}")

    datos = {
        "gremio_id": gremio_id,
        "aporte_adicional_nombre": aporte_adicional_nombre,
        "aporte_adicional_pct": aporte_adicional_pct,
    }
    with open(_ruta_config(), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
