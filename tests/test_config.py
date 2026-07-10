"""
test_config.py — Tests de la configuración de gremio por usuario.

Ejecutar:  python -m unittest discover -s tests
"""

import os
import shutil
import tempfile
import unittest

from recibos_407.config import configuracion
from recibos_407.config.gremios import GREMIOS_PREDEFINIDOS, GREMIO_POR_DEFECTO


class TestConfiguracionGremio(unittest.TestCase):
    def setUp(self):
        # Aislar cada test en una carpeta de datos propia (no tocar el
        # %APPDATA% real del usuario que corre los tests).
        self._tmp = tempfile.mkdtemp(prefix="sueldofacil_test_")
        self._appdata_original = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self._tmp

    def tearDown(self):
        if self._appdata_original is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self._appdata_original
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_sin_configurar_devuelve_default(self):
        g = configuracion.gremio_actual()
        self.assertEqual(g.id, GREMIO_POR_DEFECTO)
        self.assertEqual(g.aporte_adicional_nombre, "FAECYS")
        self.assertEqual(g.aporte_adicional_pct, 0.5)

    def test_guardar_preset_y_releer(self):
        configuracion.guardar_gremio("comercio_faecys")
        g = configuracion.gremio_actual()
        self.assertEqual(g.id, "comercio_faecys")
        self.assertEqual(g.aporte_adicional_pct, 0.5)

    def test_guardar_personalizado_y_releer(self):
        configuracion.guardar_gremio("personalizado", "Aporte Sindical XYZ", 1.25)
        g = configuracion.gremio_actual()
        self.assertEqual(g.id, "personalizado")
        self.assertEqual(g.aporte_adicional_nombre, "Aporte Sindical XYZ")
        self.assertEqual(g.aporte_adicional_pct, 1.25)

    def test_gremio_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            configuracion.guardar_gremio("no_existe")

    def test_archivo_corrupto_devuelve_default(self):
        ruta = configuracion._ruta_config()
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("{esto no es json valido")
        g = configuracion.gremio_actual()
        self.assertEqual(g.id, GREMIO_POR_DEFECTO)

    def test_catalogo_tiene_al_menos_comercio_y_personalizado(self):
        self.assertIn("comercio_faecys", GREMIOS_PREDEFINIDOS)
        self.assertIn("personalizado", GREMIOS_PREDEFINIDOS)


if __name__ == "__main__":
    unittest.main()
