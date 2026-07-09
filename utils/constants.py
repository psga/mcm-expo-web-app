"""Constantes y datos por defecto de la aplicación."""

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PAGOS_JSON_PATH = APP_DIR / "pagos_stand.json"

DEFAULT_PAGOS_DATA = {
    "stand": {
        "id": "A-12",
        "pabellon": "Pabellón Norte",
        "area": "24 m²",
        "valor_total": 8500000,
    },
    "pagos": [
        {
            "concepto": "Anticipo",
            "valor": 2550000,
            "estado": "Pagado",
            "fecha_limite": "2026-03-15",
        },
        {
            "concepto": "Pago 1",
            "valor": 2975000,
            "estado": "Pagado",
            "fecha_limite": "2026-04-30",
        },
        {
            "concepto": "Pago 2",
            "valor": 2975000,
            "estado": "Pendiente",
            "fecha_limite": "2026-06-15",
        },
    ],
}

PASOS = [
    "Registro de marca",
    "Selección de stand",
    "Generación del contrato",
    "Verificación de firma",
    "Conciliación de pagos",
]

RUTAS_PASOS = {
    1: "pages/1_Registro_Marca.py",
    2: "pages/2_Seleccion_Stand.py",
    3: "pages/3_Generacion_Contrato.py",
    4: "pages/4_Verificacion_Firma.py",
    5: "pages/5_Conciliacion_Pagos.py",
}
