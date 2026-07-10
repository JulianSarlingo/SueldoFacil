"""
motor_calculo.py
----------------
Motor de cálculo (Backend Core) para el recibo de sueldo del
Decreto 407/2026.

Toda alícuota se define UNA sola vez en ``ALICUOTAS`` para que el
sistema sea 100% fiel al decreto y fácil de auditar/actualizar. El
resto del programa nunca "hardcodea" un porcentaje: siempre lo lee
de acá.

Estructura del cálculo (según decreto):

    Sección A  Encabezado / datos del empleado y empleador (no calcula).
    Sección B  Contribuciones patronales (las paga el empleador):
                 - Seguridad Social  18% PyME / 20.4% gran empresa
                 - Obra Social        6%
                 - ART                según parámetro
                 - Sindicato/Cámara   según parámetro, TOPE 0.5%
    Sección C  Costo Laboral Total = Sueldo Bruto + Total Contribuciones B.
    Sección D  Descuentos al empleado y Sueldo Neto:
                 - Jubilación        11%
                 - Ley 19.032         3%
                 - Obra Social        3%
                 - Sindicato          según parámetro, TOPE 2%
                 - Aporte adicional del gremio (opcional, ej. FAECYS 0,5%;
                   ver recibos_407.config.gremios — NO es parte del
                   decreto, es propio de cada convenio colectivo)
                 Neto = Bruto - Total Descuentos D.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict


# ---------------------------------------------------------------------------
# Fuente única de verdad: alícuotas del Decreto 407/2026.
# Todos los valores son fracciones (0.06 == 6 %).
# ---------------------------------------------------------------------------
ALICUOTAS = {
    # Sección B — Contribuciones patronales
    "seg_social_pyme": Decimal("0.18"),      # 18 %  (empresa PyME)
    "seg_social_grande": Decimal("0.204"),   # 20.4 % (gran empresa)
    "obra_social_patronal": Decimal("0.06"),  # 6 %
    "sindicato_patronal_tope": Decimal("0.005"),  # tope 0.5 %
    # Sección D — Descuentos al empleado
    "jubilacion": Decimal("0.11"),           # 11 %
    "ley_19032": Decimal("0.03"),            # 3 %  (INSSJP / PAMI)
    "obra_social_empleado": Decimal("0.03"),  # 3 %
    "sindicato_empleado_tope": Decimal("0.02"),  # tope 2 %
}

_DOS_DEC = Decimal("0.01")


def _q(valor: Decimal) -> float:
    """Redondea a 2 decimales (half-up) y devuelve float para presentación."""
    return float(valor.quantize(_DOS_DEC, rounding=ROUND_HALF_UP))


def _dec(valor) -> Decimal:
    """Convierte cualquier entrada numérica a Decimal de forma segura."""
    return Decimal(str(valor))


@dataclass
class ParametrosLiquidacion:
    """
    Parámetros de entrada de una liquidación individual.

    Attributes:
        sueldo_bruto: Remuneración bruta del período (float o str numérico).
        porcentaje_art: Alícuota ART pactada, en % (ej. 2.5 == 2.5 %).
        porcentaje_sindicato: Aporte/contribución sindical, en %.
            Se topea automáticamente: 0.5 % patronal (B) y 2 % empleado (D).
        es_pyme: True si el empleador es PyME (18 %); False gran empresa (20.4 %).
        aporte_adicional_pct: Aporte adicional del gremio, en % (ej. FAECYS
            2.5 == 0.5 %). NO tiene tope: es un dato fijo del convenio,
            propio del gremio configurado (ver recibos_407.config).
            Default 0 -> no suma nada (compatible con liquidaciones sin
            gremio configurado).
        aporte_adicional_nombre: Etiqueta para ese aporte (ej. "FAECYS").
        nombre: Datos opcionales para la Sección A (encabezado del recibo).
        cuil, legajo, empleador, cuit_empleador, periodo, categoria: idem.
    """

    sueldo_bruto: float
    porcentaje_art: float
    porcentaje_sindicato: float
    es_pyme: bool
    # --- Datos de Sección A (opcionales, solo presentación) ---
    nombre: str = ""
    cuil: str = ""
    legajo: str = ""
    empleador: str = ""
    cuit_empleador: str = ""
    periodo: str = ""
    categoria: str = ""
    # --- Aporte adicional del gremio (opcional, fuera del decreto) ---
    aporte_adicional_pct: float = 0.0
    aporte_adicional_nombre: str = ""


def liquidar(p: ParametrosLiquidacion) -> Dict:
    """
    Ejecuta la liquidación completa y devuelve un diccionario estructurado.

    Args:
        p: Parámetros de la liquidación (ver ParametrosLiquidacion).

    Returns:
        dict con cuatro secciones ("A", "B", "C", "D") más "meta". Todos
        los importes ya vienen redondeados a 2 decimales.

    Raises:
        ValueError: si el sueldo bruto es negativo o los porcentajes lo son.
    """
    bruto = _dec(p.sueldo_bruto)
    art_pct = _dec(p.porcentaje_art) / 100
    sind_pct = _dec(p.porcentaje_sindicato) / 100
    aporte_adic_pct = _dec(p.aporte_adicional_pct) / 100

    if bruto < 0:
        raise ValueError("El sueldo bruto no puede ser negativo.")
    if art_pct < 0 or sind_pct < 0 or aporte_adic_pct < 0:
        raise ValueError("Los porcentajes no pueden ser negativos.")

    # ---------------- Sección B — Contribuciones patronales ----------------
    seg_social_alic = (
        ALICUOTAS["seg_social_pyme"] if p.es_pyme else ALICUOTAS["seg_social_grande"]
    )
    sind_patronal_alic = min(sind_pct, ALICUOTAS["sindicato_patronal_tope"])

    b_seg_social = bruto * seg_social_alic
    b_obra_social = bruto * ALICUOTAS["obra_social_patronal"]
    b_art = bruto * art_pct
    b_sindicato = bruto * sind_patronal_alic
    total_contribuciones = b_seg_social + b_obra_social + b_art + b_sindicato

    # ---------------- Sección C — Costo Laboral Total ----------------------
    costo_laboral_total = bruto + total_contribuciones

    # ---------------- Sección D — Descuentos al empleado -------------------
    sind_empleado_alic = min(sind_pct, ALICUOTAS["sindicato_empleado_tope"])

    d_jubilacion = bruto * ALICUOTAS["jubilacion"]
    d_ley_19032 = bruto * ALICUOTAS["ley_19032"]
    d_obra_social = bruto * ALICUOTAS["obra_social_empleado"]
    d_sindicato = bruto * sind_empleado_alic
    d_aporte_adicional = bruto * aporte_adic_pct
    total_descuentos = (
        d_jubilacion + d_ley_19032 + d_obra_social + d_sindicato + d_aporte_adicional
    )

    sueldo_neto = bruto - total_descuentos

    return {
        "A": {
            "nombre": p.nombre,
            "cuil": p.cuil,
            "legajo": p.legajo,
            "empleador": p.empleador,
            "cuit_empleador": p.cuit_empleador,
            "periodo": p.periodo,
            "categoria": p.categoria,
            "tipo_empresa": "PyME" if p.es_pyme else "Gran empresa",
        },
        "B": {
            "titulo": "Contribuciones patronales",
            "seguridad_social": {"alicuota_pct": _q(seg_social_alic * 100), "monto": _q(b_seg_social)},
            "obra_social": {"alicuota_pct": _q(ALICUOTAS["obra_social_patronal"] * 100), "monto": _q(b_obra_social)},
            "art": {"alicuota_pct": _q(art_pct * 100), "monto": _q(b_art)},
            "sindicato": {"alicuota_pct": _q(sind_patronal_alic * 100), "monto": _q(b_sindicato)},
            "total_contribuciones": _q(total_contribuciones),
        },
        "C": {
            "titulo": "Costo Laboral Total",
            "sueldo_bruto": _q(bruto),
            "total_contribuciones": _q(total_contribuciones),
            "costo_laboral_total": _q(costo_laboral_total),
        },
        "D": {
            "titulo": "Descuentos al empleado y Sueldo Neto",
            "sueldo_bruto": _q(bruto),
            "jubilacion": {"alicuota_pct": _q(ALICUOTAS["jubilacion"] * 100), "monto": _q(d_jubilacion)},
            "ley_19032": {"alicuota_pct": _q(ALICUOTAS["ley_19032"] * 100), "monto": _q(d_ley_19032)},
            "obra_social": {"alicuota_pct": _q(ALICUOTAS["obra_social_empleado"] * 100), "monto": _q(d_obra_social)},
            "sindicato": {"alicuota_pct": _q(sind_empleado_alic * 100), "monto": _q(d_sindicato)},
            "aporte_adicional": {
                "nombre": p.aporte_adicional_nombre or "Aporte adicional gremio",
                "alicuota_pct": _q(aporte_adic_pct * 100),
                "monto": _q(d_aporte_adicional),
            },
            "total_descuentos": _q(total_descuentos),
            "sueldo_neto": _q(sueldo_neto),
        },
        "meta": {
            "decreto": "407/2026",
            "es_pyme": p.es_pyme,
        },
    }


if __name__ == "__main__":
    # Demo rápida por consola.
    demo = ParametrosLiquidacion(
        sueldo_bruto=1_000_000,
        porcentaje_art=3.0,
        porcentaje_sindicato=2.5,   # se topeará: 0.5 % patronal / 2 % empleado
        es_pyme=True,
        nombre="Juan Pérez",
        cuil="20-12345678-9",
        periodo="Julio 2026",
    )
    from pprint import pprint
    pprint(liquidar(demo))
