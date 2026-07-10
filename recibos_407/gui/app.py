"""
app.py — Interfaz de escritorio con Tkinter.

Formulario para liquidación individual y carga masiva de Excel/CSV.
Cero dependencias externas (Tkinter viene con Python).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from ..core.motor_calculo import ParametrosLiquidacion, liquidar
from ..pdf.generador_pdf import generar_recibo_pdf
from ..io_datos.lote import procesar_lote
from .. import version
from ..updater import check_for_updates
from ..config.gremios import GREMIOS_PREDEFINIDOS, GREMIO_POR_DEFECTO
from ..config.configuracion import gremio_actual, guardar_gremio


def _abrir_archivo(ruta: str) -> None:
    """Abre un archivo con la aplicación por defecto del sistema."""
    if sys.platform == "win32":
        os.startfile(ruta)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    else:
        subprocess.Popen(["xdg-open", ruta])


def _money(valor: float) -> str:
    """Formatea importe: $ 1.234.567,89."""
    s = f"{valor:,.2f}"
    s = s.replace(",", "@").replace(".", ",").replace("@", ".")
    return f"$ {s}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Recibos de Sueldo — Decreto 407/2026  (v{version.VERSION})")
        self.geometry("720x620")
        self.resizable(False, False)

        # Estilo
        style = ttk.Style(self)
        style.theme_use("clam")

        # Gremio configurado (aporte adicional fuera del decreto, ej. FAECYS).
        self._gremio = gremio_actual()

        self._crear_menu()
        self._crear_widgets()

    def _crear_menu(self):
        barra = tk.Menu(self)
        self.config(menu=barra)

        menu_ayuda = tk.Menu(barra, tearoff=0)
        menu_ayuda.add_command(
            label="Chequear actualizaciones",
            command=self._chequear_actualizaciones,
        )
        menu_ayuda.add_separator()
        menu_ayuda.add_command(
            label=f"Acerca de (v{version.VERSION})", state="disabled",
        )
        barra.add_cascade(label="Ayuda", menu=menu_ayuda)

    def _chequear_actualizaciones(self):
        """Lanza el chequeo de actualizaciones en un hilo."""
        def _worker():
            check_for_updates(
                version.PROGRAM_ID,
                version.VERSION,
                version.URL_MANIFIESTO,
            )
        threading.Thread(target=_worker, daemon=True).start()

    def _crear_widgets(self):
        # ── Notebook con dos pestañas ────────────────────────────
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tab_individual = ttk.Frame(notebook, padding=10)
        tab_lote = ttk.Frame(notebook, padding=10)
        tab_config = ttk.Frame(notebook, padding=10)
        notebook.add(tab_individual, text="  Liquidación Individual  ")
        notebook.add(tab_lote, text="  Procesamiento Masivo  ")
        notebook.add(tab_config, text="  Configuración  ")

        self._crear_tab_individual(tab_individual)
        self._crear_tab_lote(tab_lote)
        self._crear_tab_config(tab_config)

    # ── Pestaña Individual ───────────────────────────────────────

    def _crear_tab_individual(self, parent: ttk.Frame):
        # Datos del empleado (Sección A)
        lbl = ttk.Label(parent, text="Datos del empleado", font=("", 11, "bold"))
        lbl.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        campos_a = [
            ("Nombre:", 1, 0), ("CUIL:", 1, 2),
            ("Legajo:", 2, 0), ("Categoría:", 2, 2),
            ("Empleador:", 3, 0), ("CUIT empleador:", 3, 2),
            ("Período:", 4, 0),
        ]
        self._entries_a = {}
        for label_text, row, col in campos_a:
            ttk.Label(parent, text=label_text).grid(row=row, column=col, sticky="e", padx=(0, 4), pady=2)
            e = ttk.Entry(parent, width=28)
            e.grid(row=row, column=col + 1, sticky="w", pady=2)
            key = label_text.rstrip(":").lower().replace(" ", "_")
            self._entries_a[key] = e

        # Valor por defecto para período
        self._entries_a["período"].insert(0, "Julio 2026")

        # Separador
        ttk.Separator(parent, orient="horizontal").grid(
            row=5, column=0, columnspan=4, sticky="ew", pady=10)

        # Datos de liquidación
        lbl2 = ttk.Label(parent, text="Datos de liquidación",
                         font=("", 11, "bold"))
        lbl2.grid(row=6, column=0, columnspan=4, sticky="w", pady=(0, 8))

        ttk.Label(parent, text="Sueldo bruto:").grid(
            row=7, column=0, sticky="e", padx=(0, 4), pady=2)
        self._entry_bruto = ttk.Entry(parent, width=20)
        self._entry_bruto.insert(0, "1000000")
        self._entry_bruto.grid(row=7, column=1, sticky="w", pady=2)

        ttk.Label(parent, text="% ART:").grid(
            row=7, column=2, sticky="e", padx=(0, 4), pady=2)
        self._entry_art = ttk.Entry(parent, width=10)
        self._entry_art.insert(0, "3.0")
        self._entry_art.grid(row=7, column=3, sticky="w", pady=2)

        ttk.Label(parent, text="% Sindicato:").grid(
            row=8, column=0, sticky="e", padx=(0, 4), pady=2)
        self._entry_sind = ttk.Entry(parent, width=10)
        self._entry_sind.insert(0, "2.5")
        self._entry_sind.grid(row=8, column=1, sticky="w", pady=2)

        self._var_pyme = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Es PyME", variable=self._var_pyme).grid(
            row=8, column=2, columnspan=2, sticky="w", pady=2)

        # Botón liquidar
        btn = ttk.Button(parent, text="Liquidar y generar PDF",
                         command=self._liquidar_individual)
        btn.grid(row=9, column=0, columnspan=4, pady=15)

        # Frame de resultado
        self._frame_resultado = ttk.LabelFrame(parent, text="Resultado",
                                               padding=10)
        self._frame_resultado.grid(
            row=10, column=0, columnspan=4, sticky="ew", pady=(0, 5))
        self._lbl_neto = ttk.Label(self._frame_resultado, text="—",
                                   font=("", 14, "bold"), foreground="#2E7D32")
        self._lbl_neto.pack(anchor="w")
        self._lbl_detalle = ttk.Label(self._frame_resultado, text="",
                                      foreground="#455A64")
        self._lbl_detalle.pack(anchor="w")

    def _liquidar_individual(self):
        try:
            bruto = float(self._entry_bruto.get() or 0)
            art = float(self._entry_art.get() or 0)
            sind = float(self._entry_sind.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Los valores numéricos no son válidos.")
            return

        params = ParametrosLiquidacion(
            sueldo_bruto=bruto,
            porcentaje_art=art,
            porcentaje_sindicato=sind,
            es_pyme=self._var_pyme.get(),
            nombre=self._entries_a.get("nombre", tk.Entry()).get(),
            cuil=self._entries_a.get("cuil", tk.Entry()).get(),
            legajo=self._entries_a.get("legajo", tk.Entry()).get(),
            empleador=self._entries_a.get("empleador", tk.Entry()).get(),
            cuit_empleador=self._entries_a.get("cuit_empleador", tk.Entry()).get(),
            periodo=self._entries_a.get("período", tk.Entry()).get(),
            categoria=self._entries_a.get("categoría", tk.Entry()).get(),
            aporte_adicional_pct=self._gremio.aporte_adicional_pct,
            aporte_adicional_nombre=self._gremio.aporte_adicional_nombre,
        )

        try:
            resultado = liquidar(params)
        except ValueError as e:
            messagebox.showerror("Error de cálculo", str(e))
            return

        # Mostrar resultado
        d = resultado["D"]
        c = resultado["C"]
        self._lbl_neto.config(text=f"Sueldo Neto: {_money(d['sueldo_neto'])}")
        detalle = (
            f"Bruto: {_money(c['sueldo_bruto'])}  |  "
            f"Contribuciones: {_money(resultado['B']['total_contribuciones'])}  |  "
            f"Descuentos: {_money(d['total_descuentos'])}  |  "
            f"Costo laboral: {_money(c['costo_laboral_total'])}"
        )
        aporte_adic = d.get("aporte_adicional")
        if aporte_adic and aporte_adic["monto"] > 0:
            detalle += f"  |  {aporte_adic['nombre']}: {_money(aporte_adic['monto'])}"
        self._lbl_detalle.config(text=detalle)

        # Guardar PDF
        ruta = filedialog.asksaveasfilename(
            title="Guardar recibo PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"recibo_{params.nombre or 'empleado'}.pdf",
        )
        if not ruta:
            return

        try:
            generar_recibo_pdf(resultado, ruta)
            if messagebox.askyesno("PDF generado",
                                   f"Recibo guardado en:\n{ruta}\n\n¿Abrirlo?"):
                _abrir_archivo(ruta)
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))

    # ── Pestaña Lote ─────────────────────────────────────────────

    def _crear_tab_lote(self, parent: ttk.Frame):
        ttk.Label(
            parent,
            text="Seleccioná un archivo .xlsx o .csv con los empleados.\n"
                 "Se genera un PDF por cada fila.",
            foreground="#455A64",
        ).pack(anchor="w", pady=(0, 10))

        self._lbl_lote_gremio = ttk.Label(
            parent, text=self._texto_gremio_activo(), foreground="#1565C0")
        self._lbl_lote_gremio.pack(anchor="w", pady=(0, 10))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Seleccionar archivo y procesar",
                   command=self._procesar_lote).pack(side="left")

        self._lbl_lote_estado = ttk.Label(parent, text="", foreground="#1565C0")
        self._lbl_lote_estado.pack(anchor="w", pady=(10, 5))

        self._progress = ttk.Progressbar(parent, mode="determinate", length=500)
        self._progress.pack(fill="x", pady=(0, 10))

        self._lbl_lote_resultado = ttk.Label(parent, text="",
                                             foreground="#2E7D32",
                                             wraplength=650)
        self._lbl_lote_resultado.pack(anchor="w")

        self._lbl_lote_errores = ttk.Label(parent, text="",
                                           foreground="#C62828",
                                           wraplength=650)
        self._lbl_lote_errores.pack(anchor="w")

    def _procesar_lote(self):
        ruta_in = filedialog.askopenfilename(
            title="Seleccionar archivo de empleados",
            filetypes=[
                ("Excel / CSV", "*.xlsx *.csv"),
                ("Excel", "*.xlsx"),
                ("CSV", "*.csv"),
            ],
        )
        if not ruta_in:
            return

        carpeta_out = filedialog.askdirectory(
            title="Carpeta destino para los PDFs")
        if not carpeta_out:
            return

        # Reset UI
        self._progress["value"] = 0
        self._lbl_lote_estado.config(text="Procesando...")
        self._lbl_lote_resultado.config(text="")
        self._lbl_lote_errores.config(text="")
        self.update_idletasks()

        # Procesar en un hilo para no bloquear la GUI
        def _worker():
            def _progreso(hecho, total):
                if total > 0:
                    pct = (hecho / total) * 100
                    self._progress["value"] = pct
                    self._lbl_lote_estado.config(
                        text=f"Procesando... {hecho}/{total}")
                    self.update_idletasks()

            try:
                res = procesar_lote(ruta_in, carpeta_out, progreso=_progreso)
                self._lbl_lote_estado.config(text="Listo.")
                self._lbl_lote_resultado.config(
                    text=f"Generados {res.generados}/{res.total} recibos "
                         f"en: {carpeta_out}")
                if res.errores:
                    self._lbl_lote_errores.config(
                        text="Errores:\n" + "\n".join(res.errores[:20]))
            except Exception as e:
                self._lbl_lote_estado.config(text="Error.")
                self._lbl_lote_errores.config(text=str(e))

        threading.Thread(target=_worker, daemon=True).start()

    # ── Pestaña Configuración ────────────────────────────────────

    def _texto_gremio_activo(self) -> str:
        g = self._gremio
        if g.aporte_adicional_pct > 0:
            return (f"Gremio activo: {g.nombre}  "
                    f"({g.aporte_adicional_nombre} {g.aporte_adicional_pct:.2f} %)")
        return f"Gremio activo: {g.nombre} (sin aporte adicional)"

    def _crear_tab_config(self, parent: ttk.Frame):
        ttk.Label(parent, text="Gremio / Sindicato",
                 font=("", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(
            parent,
            text="El aporte adicional del gremio (ej. FAECYS) no está fijado "
                 "por el Decreto 407/2026: depende del convenio colectivo de "
                 "cada empresa. Configuralo acá una vez y se aplica solo, "
                 "tanto en la liquidación individual como en el lote.",
            foreground="#455A64", wraplength=560, justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(parent, text="Gremio:").grid(
            row=2, column=0, sticky="e", padx=(0, 4), pady=4)
        self._nombre_por_id = {g.id: g.nombre for g in GREMIOS_PREDEFINIDOS.values()}
        self._id_por_nombre = {v: k for k, v in self._nombre_por_id.items()}
        self._var_gremio = tk.StringVar()
        combo = ttk.Combobox(
            parent, textvariable=self._var_gremio,
            values=list(self._nombre_por_id.values()),
            state="readonly", width=28)
        combo.grid(row=2, column=1, sticky="w", pady=4)
        combo.bind("<<ComboboxSelected>>", self._on_gremio_seleccionado)

        ttk.Label(parent, text="Nombre del aporte adicional:").grid(
            row=3, column=0, sticky="e", padx=(0, 4), pady=4)
        self._entry_aporte_nombre = ttk.Entry(parent, width=28)
        self._entry_aporte_nombre.grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(parent, text="% aporte adicional (a cargo del empleado):").grid(
            row=4, column=0, sticky="e", padx=(0, 4), pady=4)
        self._entry_aporte_pct = ttk.Entry(parent, width=10)
        self._entry_aporte_pct.grid(row=4, column=1, sticky="w", pady=4)

        ttk.Label(
            parent,
            text="Estos dos campos solo se editan con el gremio "
                 "\"Personalizado\"; para los demás vienen fijos.",
            foreground="#78909C",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Button(parent, text="Guardar configuración",
                   command=self._guardar_config).grid(
            row=6, column=0, columnspan=2, pady=6)

        self._lbl_config_estado = ttk.Label(parent, text="", foreground="#2E7D32")
        self._lbl_config_estado.grid(row=7, column=0, columnspan=2, sticky="w")

        self._cargar_config_en_formulario()

    def _on_gremio_seleccionado(self, event=None):
        gremio_id = self._id_por_nombre.get(self._var_gremio.get(), GREMIO_POR_DEFECTO)
        self._entry_aporte_nombre.config(state="normal")
        self._entry_aporte_pct.config(state="normal")
        if gremio_id != "personalizado":
            preset = GREMIOS_PREDEFINIDOS[gremio_id]
            self._entry_aporte_nombre.delete(0, tk.END)
            self._entry_aporte_nombre.insert(0, preset.aporte_adicional_nombre)
            self._entry_aporte_pct.delete(0, tk.END)
            self._entry_aporte_pct.insert(0, f"{preset.aporte_adicional_pct}")
            self._entry_aporte_nombre.config(state="disabled")
            self._entry_aporte_pct.config(state="disabled")

    def _cargar_config_en_formulario(self):
        g = self._gremio
        self._var_gremio.set(self._nombre_por_id.get(g.id, self._nombre_por_id[GREMIO_POR_DEFECTO]))
        self._entry_aporte_nombre.delete(0, tk.END)
        self._entry_aporte_nombre.insert(0, g.aporte_adicional_nombre)
        self._entry_aporte_pct.delete(0, tk.END)
        self._entry_aporte_pct.insert(0, f"{g.aporte_adicional_pct}")
        self._on_gremio_seleccionado()

    def _guardar_config(self):
        gremio_id = self._id_por_nombre.get(self._var_gremio.get(), GREMIO_POR_DEFECTO)
        try:
            pct = float(self._entry_aporte_pct.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "El % de aporte adicional no es válido.")
            return

        guardar_gremio(gremio_id, self._entry_aporte_nombre.get().strip(), pct)
        self._gremio = gremio_actual()
        self._lbl_lote_gremio.config(text=self._texto_gremio_activo())
        self._lbl_config_estado.config(text="Configuración guardada.")


def iniciar():
    """Crea y ejecuta la aplicación Tkinter."""
    app = App()
    app.mainloop()
