"""
recibos_407
===========
Sistema unificado de liquidación y generación de recibos de sueldo bajo el
Decreto 407/2026 (Argentina).

Módulos:
    core.motor_calculo      Motor de cálculo (secciones A/B/C/D).
    graficos.grafico_torta  Gráfico de torta obligatorio (Matplotlib).
    graficos.generador_pdf  Render del recibo en PDF (ReportLab).
    config.gremios          Catálogo de gremios y su aporte adicional (ej. FAECYS).
    config.configuracion    Config por usuario: qué gremio está activo.
    seguridad.licencia_gate Gate de licencia (integra Seguridad de la lib).
    seguridad.auth          Login / usuarios / control de accesos (RBAC). [pendiente]
    seguridad.enmascarado   Enmascarado de datos sensibles (CUIT/CUIL/saldos). [pendiente]
    web.app                 Interfaz web (NiceGUI) + procesamiento masivo. [pendiente]
"""

__version__ = "1.1.0"
