"""
config
======
Configuración por usuario/instalación: qué gremio se liquida.

    gremios.py        Catálogo de gremios y su aporte adicional (ej. FAECYS).
    configuracion.py  Carga/guarda el gremio elegido en un JSON local.

Separado del motor de cálculo a propósito: las alícuotas del Decreto
407/2026 (motor_calculo.ALICUOTAS) son fijas y no dependen del gremio;
el aporte adicional sí, y varía según el convenio colectivo de cada
empresa. Así el decreto y el gremio se pueden auditar por separado.
"""
