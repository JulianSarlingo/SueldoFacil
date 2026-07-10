"""
generador_pdf.py — Recibo de sueldo en PDF (ReportLab).

Renderiza las 4 secciones (A, B, C, D) en una página A4 e inserta
el gráfico de torta obligatorio. PNGs temporales se limpian al terminar.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
)

from .grafico_torta import generar_grafico_torta

_AZUL = colors.HexColor("#1565C0")
_GRIS = colors.HexColor("#455A64")
_GRIS_CLARO = colors.HexColor("#ECEFF1")
_VERDE = colors.HexColor("#2E7D32")


def _money(valor) -> str:
    """Formatea importe como moneda argentina: $ 1.234.567,89."""
    if isinstance(valor, str):
        return valor
    s = f"{float(valor):,.2f}"
    s = s.replace(",", "@").replace(".", ",").replace("@", ".")
    return f"$ {s}"


def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "titulo", parent=base["Title"], fontSize=15,
            textColor=_AZUL, spaceAfter=2,
        ),
        "sub": ParagraphStyle(
            "sub", parent=base["Normal"], fontSize=8, textColor=_GRIS,
        ),
        "seccion": ParagraphStyle(
            "seccion", parent=base["Heading2"], fontSize=10.5,
            textColor=colors.white, spaceAfter=0, leading=14,
        ),
        "normal": ParagraphStyle(
            "n", parent=base["Normal"], fontSize=8.5, leading=11,
        ),
    }


def _banda_seccion(texto: str, estilos) -> Table:
    """Barra de título de sección (fondo azul, texto blanco)."""
    p = Paragraph(f"<b>{texto}</b>", estilos["seccion"])
    t = Table([[p]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _AZUL),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _tabla_datos(filas, anchos, estilos, resaltar_ultima=False) -> Table:
    t = Table(filas, colWidths=anchos)
    estilo = [
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), _GRIS),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, _GRIS_CLARO),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
    ]
    if resaltar_ultima:
        estilo += [
            ("BACKGROUND", (0, -1), (-1, -1), _GRIS_CLARO),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
        ]
    t.setStyle(TableStyle(estilo))
    return t


def generar_recibo_pdf(
    resultado: Dict,
    ruta_pdf: str,
    ruta_grafico: Optional[str] = None,
) -> str:
    """Genera el PDF del recibo. Devuelve la ruta del PDF."""
    est = _estilos()
    A, B, C, D = resultado["A"], resultado["B"], resultado["C"], resultado["D"]

    grafico_temporal = ruta_grafico is None
    if grafico_temporal:
        ruta_grafico = generar_grafico_torta(resultado)

    try:
        doc = SimpleDocTemplate(
            ruta_pdf, pagesize=A4,
            leftMargin=15 * mm, rightMargin=15 * mm,
            topMargin=14 * mm, bottomMargin=14 * mm,
            title="Recibo de sueldo - Decreto 407/2026",
        )
        story = []

        # Encabezado
        story.append(Paragraph("Recibo de Sueldo", est["titulo"]))
        story.append(Paragraph(
            f"Decreto 407/2026 &nbsp;&middot;&nbsp; "
            f"Período: <b>{A.get('periodo') or '-'}</b>",
            est["sub"],
        ))
        story.append(Spacer(1, 6))

        # Seccion A
        story.append(_banda_seccion(
            "Sección A — Datos del empleado y empleador", est))
        filas_a = [
            ["Empleado", A.get("nombre") or "-", "CUIL", A.get("cuil") or "-"],
            ["Legajo", A.get("legajo") or "-", "Categoría", A.get("categoria") or "-"],
            ["Empleador", A.get("empleador") or "-", "CUIT", A.get("cuit_empleador") or "-"],
            ["Tipo de empresa", A.get("tipo_empresa") or "-", "Período", A.get("periodo") or "-"],
        ]
        ta = Table(filas_a, colWidths=[28 * mm, 62 * mm, 24 * mm, 66 * mm])
        ta.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("TEXTCOLOR", (0, 0), (0, -1), _AZUL),
            ("TEXTCOLOR", (2, 0), (2, -1), _AZUL),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, _GRIS_CLARO),
        ]))
        story.append(ta)
        story.append(Spacer(1, 8))

        # Seccion B
        story.append(_banda_seccion(
            "Sección B — Contribuciones patronales", est))
        filas_b = [["Concepto", "Alícuota", "Monto"]]
        for clave, etiqueta in (
            ("seguridad_social", "Seguridad Social"),
            ("obra_social", "Obra Social"),
            ("art", "ART"),
            ("sindicato", "Sindicato / Cámara"),
        ):
            item = B[clave]
            filas_b.append([etiqueta, f"{item['alicuota_pct']:.2f} %", _money(item["monto"])])
        filas_b.append(["Total contribuciones", "", _money(B["total_contribuciones"])])
        story.append(_tabla_datos(
            filas_b, [90 * mm, 40 * mm, 50 * mm], est, resaltar_ultima=True))
        story.append(Spacer(1, 8))

        # Seccion C
        story.append(_banda_seccion(
            "Sección C — Costo Laboral Total", est))
        filas_c = [
            ["Sueldo Bruto", _money(C["sueldo_bruto"])],
            ["(+) Total contribuciones", _money(C["total_contribuciones"])],
            ["Costo Laboral Total", _money(C["costo_laboral_total"])],
        ]
        story.append(_tabla_datos(
            filas_c, [130 * mm, 50 * mm], est, resaltar_ultima=True))
        story.append(Spacer(1, 8))

        # Seccion D + grafico
        story.append(_banda_seccion(
            "Sección D — Descuentos y Sueldo Neto", est))
        filas_d = [["Concepto", "Alícuota", "Monto"]]
        for clave, etiqueta in (
            ("jubilacion", "Jubilación"),
            ("ley_19032", "Ley 19.032 (INSSJP)"),
            ("obra_social", "Obra Social"),
            ("sindicato", "Sindicato"),
        ):
            item = D[clave]
            filas_d.append([etiqueta, f"{item['alicuota_pct']:.2f} %", _money(item["monto"])])
        # Aporte adicional del gremio (ej. FAECYS): solo se muestra si el
        # gremio configurado tiene uno cargado (monto > 0).
        aporte_adic = D.get("aporte_adicional")
        if aporte_adic and aporte_adic["monto"] > 0:
            filas_d.append([
                aporte_adic["nombre"],
                f"{aporte_adic['alicuota_pct']:.2f} %",
                _money(aporte_adic["monto"]),
            ])
        filas_d.append(["Total descuentos", "", _money(D["total_descuentos"])])
        tabla_d = _tabla_datos(
            filas_d, [45 * mm, 22 * mm, 33 * mm], est, resaltar_ultima=True)

        img = Image(ruta_grafico, width=78 * mm, height=78 * mm)
        combinado = Table([[tabla_d, img]], colWidths=[100 * mm, 80 * mm])
        combinado.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(combinado)
        story.append(Spacer(1, 4))

        # Neto final destacado
        neto = Table(
            [[Paragraph("<b>SUELDO NETO A COBRAR</b>",
                         ParagraphStyle("neto", fontSize=11, textColor=colors.white)),
              Paragraph(f"<b>{_money(D['sueldo_neto'])}</b>",
                         ParagraphStyle("netoval", fontSize=13,
                                        textColor=colors.white, alignment=2))]],
            colWidths=[110 * mm, 70 * mm],
        )
        neto.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _VERDE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(neto)
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "Documento generado automáticamente conforme al Decreto 407/2026. "
            "Los importes surgen de las alícuotas vigentes parametrizadas en el sistema.",
            est["sub"],
        ))

        doc.build(story)
    finally:
        if grafico_temporal and ruta_grafico and os.path.exists(ruta_grafico):
            os.remove(ruta_grafico)

    return ruta_pdf
