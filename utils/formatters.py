"""Utilidades de formateo para la interfaz."""


def formatear_moneda(valor: int | float) -> str:
    """Formatea un valor numérico como moneda colombiana."""
    return f"${valor:,.0f}".replace(",", ".")
