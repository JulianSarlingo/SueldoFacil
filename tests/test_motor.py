"""
test_motor.py — Tests del motor de cálculo (Decreto 407/2026).

Cubre: topes sindicato, diferencia PyME/gran empresa, validaciones.

Ejecutar:  python -m unittest discover -s tests
"""

import unittest

from recibos_407.core.motor_calculo import ParametrosLiquidacion, liquidar


class TestMotorPyme(unittest.TestCase):
    def setUp(self):
        self.r = liquidar(ParametrosLiquidacion(
            sueldo_bruto=1_000_000, porcentaje_art=3.0,
            porcentaje_sindicato=2.5, es_pyme=True,
        ))

    def test_seccion_B_pyme(self):
        b = self.r["B"]
        self.assertEqual(b["seguridad_social"]["monto"], 180_000.0)   # 18 %
        self.assertEqual(b["obra_social"]["monto"], 60_000.0)         # 6 %
        self.assertEqual(b["art"]["monto"], 30_000.0)                 # 3 %
        self.assertEqual(b["sindicato"]["monto"], 5_000.0)           # tope 0.5 %
        self.assertEqual(b["total_contribuciones"], 275_000.0)

    def test_seccion_C(self):
        self.assertEqual(self.r["C"]["costo_laboral_total"], 1_275_000.0)

    def test_seccion_D(self):
        d = self.r["D"]
        self.assertEqual(d["jubilacion"]["monto"], 110_000.0)   # 11 %
        self.assertEqual(d["ley_19032"]["monto"], 30_000.0)     # 3 %
        self.assertEqual(d["obra_social"]["monto"], 30_000.0)   # 3 %
        self.assertEqual(d["sindicato"]["monto"], 20_000.0)     # tope 2 %
        self.assertEqual(d["total_descuentos"], 190_000.0)
        self.assertEqual(d["sueldo_neto"], 810_000.0)


class TestMotorGranEmpresa(unittest.TestCase):
    def test_seguridad_social_20_4(self):
        r = liquidar(ParametrosLiquidacion(
            sueldo_bruto=1_000_000, porcentaje_art=4.0,
            porcentaje_sindicato=0.4, es_pyme=False,
        ))
        self.assertEqual(r["B"]["seguridad_social"]["monto"], 204_000.0)
        # Sindicato 0.4 % < tope 0.5 % -> se respeta 0.4 %
        self.assertEqual(r["B"]["sindicato"]["alicuota_pct"], 0.4)
        self.assertEqual(r["B"]["sindicato"]["monto"], 4_000.0)
        # Empleado 0.4 % < tope 2 % -> 0.4 %
        self.assertEqual(r["D"]["sindicato"]["monto"], 4_000.0)


class TestTopesSindicato(unittest.TestCase):
    def test_topes_se_aplican(self):
        r = liquidar(ParametrosLiquidacion(
            sueldo_bruto=2_000_000, porcentaje_art=2.0,
            porcentaje_sindicato=5.0, es_pyme=True,
        ))
        # Patronal topeado a 0.5 % = 10.000
        self.assertEqual(r["B"]["sindicato"]["monto"], 10_000.0)
        # Empleado topeado a 2 % = 40.000
        self.assertEqual(r["D"]["sindicato"]["monto"], 40_000.0)


class TestValidaciones(unittest.TestCase):
    def test_bruto_negativo(self):
        with self.assertRaises(ValueError):
            liquidar(ParametrosLiquidacion(-1, 3, 2, True))

    def test_aporte_adicional_negativo(self):
        with self.assertRaises(ValueError):
            liquidar(ParametrosLiquidacion(
                1_000_000, 3, 2, True, aporte_adicional_pct=-1))


class TestAporteAdicionalGremio(unittest.TestCase):
    """Aporte adicional del gremio (ej. FAECYS), fuera de las alícuotas
    fijas del decreto. Ver recibo real: código 449 FAECYS 0,5 %."""

    def test_sin_gremio_configurado_no_suma_nada(self):
        # Comportamiento por defecto (aporte_adicional_pct=0): idéntico al
        # motor antes de este campo, no rompe liquidaciones existentes.
        r = liquidar(ParametrosLiquidacion(
            sueldo_bruto=1_000_000, porcentaje_art=3.0,
            porcentaje_sindicato=2.5, es_pyme=True,
        ))
        self.assertEqual(r["D"]["aporte_adicional"]["monto"], 0.0)
        self.assertEqual(r["D"]["total_descuentos"], 190_000.0)
        self.assertEqual(r["D"]["sueldo_neto"], 810_000.0)

    def test_faecys_se_suma_a_los_descuentos(self):
        r = liquidar(ParametrosLiquidacion(
            sueldo_bruto=1_000_000, porcentaje_art=3.0,
            porcentaje_sindicato=2.5, es_pyme=True,
            aporte_adicional_pct=0.5, aporte_adicional_nombre="FAECYS",
        ))
        aporte = r["D"]["aporte_adicional"]
        self.assertEqual(aporte["nombre"], "FAECYS")
        self.assertEqual(aporte["monto"], 5_000.0)          # 0,5 % de 1.000.000
        self.assertEqual(r["D"]["total_descuentos"], 195_000.0)  # 190.000 + 5.000
        self.assertEqual(r["D"]["sueldo_neto"], 805_000.0)

    def test_nombre_por_defecto_si_no_se_indica(self):
        r = liquidar(ParametrosLiquidacion(
            sueldo_bruto=1_000_000, porcentaje_art=3.0,
            porcentaje_sindicato=2.5, es_pyme=True,
            aporte_adicional_pct=1.0,
        ))
        self.assertEqual(r["D"]["aporte_adicional"]["nombre"], "Aporte adicional gremio")


class TestLicenciaStub(unittest.TestCase):
    def test_verificar_licencia_stub(self):
        from recibos_407.seguridad import verificar_licencia
        self.assertTrue(verificar_licencia())


if __name__ == "__main__":
    unittest.main()
