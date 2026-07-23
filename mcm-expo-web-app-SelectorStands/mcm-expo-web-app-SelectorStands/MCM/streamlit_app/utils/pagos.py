"""Plan de cuotas en memoria para el wizard (independiente de la DB)."""


def generar_plan_pagos(valor_total: int | float) -> list:
    """
    Genera el plan de cuotas del wizard a partir del valor del stand
    reservado (30% Anticipo, 35% Pago 1, 35% Pago 2). Es un plan orientativo
    en session_state para los pasos 3 y 5 del wizard; el cobro real se
    gestiona en flujo_marca._seccion_mis_pagos() contra la factura creada en la DB.
    """
    anticipo = round(valor_total * 0.30)
    pago_1 = round(valor_total * 0.35)
    pago_2 = valor_total - anticipo - pago_1

    return [
        {
            "concepto": "Anticipo",
            "valor": anticipo,
            "estado": "Pendiente",
            "fecha_limite": "2026-03-15",
        },
        {
            "concepto": "Pago 1",
            "valor": pago_1,
            "estado": "Pendiente",
            "fecha_limite": "2026-04-30",
        },
        {
            "concepto": "Pago 2",
            "valor": pago_2,
            "estado": "Pendiente",
            "fecha_limite": "2026-06-15",
        },
    ]
