"""Backend core: motor de cálculo del Decreto 407/2026."""

from .motor_calculo import (
    ParametrosLiquidacion,
    liquidar,
    ALICUOTAS,
)

__all__ = ["ParametrosLiquidacion", "liquidar", "ALICUOTAS"]
