"""Constantes de la aplicación."""

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DATA_JSON_PATH = APP_DIR / "datasinimagen.json"

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
