"""
gremios.py
----------
Catálogo de gremios (sindicatos) y su aporte adicional específico.

El Decreto 407/2026 fija las alícuotas GENERALES del recibo (jubilación,
obra social, seguridad social, tope de sindicato). Pero además, cada
convenio colectivo suele sumar un aporte propio del gremio que el decreto
no cubre — por ejemplo, en Comercio (CCT 130/75) el sindicato FAECYS
cobra un 0,5 % adicional al empleado, además de la cuota sindical general.
Ese es justamente el concepto "449 FAECYS" que aparece en un recibo real
de un vendedor de comercio, y es lo que este módulo modela.

Este catálogo NO toca motor_calculo.ALICUOTAS (eso sigue siendo el
decreto, fijo). Solo agrega el dato extra por gremio.

Para sumar un gremio nuevo: agregar una entrada a GREMIOS_PREDEFINIDOS
con los datos confirmados por el convenio colectivo correspondiente.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Gremio:
    """Datos de un gremio: su aporte adicional a cargo del empleado."""

    id: str
    nombre: str
    aporte_adicional_nombre: str = ""   # ej. "FAECYS"
    aporte_adicional_pct: float = 0.0   # ej. 0.5 -> 0,5 % del bruto


# Catálogo de gremios ya verificados. "personalizado" es el comodín para
# cualquier gremio no listado: sus valores los completa el usuario en la
# pestaña "Configuración" de la app.
GREMIOS_PREDEFINIDOS: dict[str, Gremio] = {
    "comercio_faecys": Gremio(
        id="comercio_faecys",
        nombre="Comercio (FAECYS)",
        aporte_adicional_nombre="FAECYS",
        aporte_adicional_pct=0.5,
    ),
    "personalizado": Gremio(
        id="personalizado",
        nombre="Personalizado",
        aporte_adicional_nombre="",
        aporte_adicional_pct=0.0,
    ),
}

GREMIO_POR_DEFECTO = "comercio_faecys"
