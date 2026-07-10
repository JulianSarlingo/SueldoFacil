"""
grafico_torta.py — Gráfico de torta obligatorio (Decreto 407/2026).

Porciones: Neto, Seguridad Social, Obra Social, ART, Sindicato.
Backend "Agg" para generar sin ventana gráfica.
"""

from __future__ import annotations

import os
import tempfile
from typing import Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_COLORES = {
    "Neto": "#2E7D32",
    "Seguridad Social": "#1565C0",
    "Obra Social": "#00838F",
    "ART": "#EF6C00",
    "Sindicato": "#6A1B9A",
}


def generar_grafico_torta(resultado: Dict, ruta_salida: Optional[str] = None) -> str:
    """Crea el gráfico de torta y lo guarda como PNG. Devuelve la ruta."""
    porciones = {
        "Neto": resultado["D"]["sueldo_neto"],
        "Seguridad Social": resultado["B"]["seguridad_social"]["monto"],
        "Obra Social": resultado["B"]["obra_social"]["monto"],
        "ART": resultado["B"]["art"]["monto"],
        "Sindicato": resultado["B"]["sindicato"]["monto"],
    }

    etiquetas = [k for k, v in porciones.items() if v > 0]
    valores = [porciones[k] for k in etiquetas]
    colores = [_COLORES[k] for k in etiquetas]

    if ruta_salida is None:
        fd, ruta_salida = tempfile.mkstemp(suffix=".png", prefix="torta_")
        os.close(fd)

    fig, ax = plt.subplots(figsize=(4.6, 4.6), dpi=150)
    wedges, _texts, autotexts = ax.pie(
        valores, colors=colores,
        autopct=lambda pct: f"{pct:.1f}%",
        startangle=90, counterclock=False, pctdistance=0.75,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(9)
        t.set_fontweight("bold")

    ax.axis("equal")
    ax.set_title("Composición del Costo Laboral", fontsize=11, fontweight="bold")
    ax.legend(
        wedges,
        [f"{k}: ${porciones[k]:,.2f}" for k in etiquetas],
        loc="upper center", bbox_to_anchor=(0.5, -0.02),
        ncol=1, fontsize=8, frameon=False,
    )

    fig.tight_layout()
    fig.savefig(ruta_salida, bbox_inches="tight", transparent=False)
    plt.close(fig)
    return ruta_salida
