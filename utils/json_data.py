"""Lectura y escritura segura del archivo pagos_stand.json."""

import copy
import json

import streamlit as st

from utils.constants import DEFAULT_PAGOS_DATA, PAGOS_JSON_PATH


def crear_pagos_json_si_no_existe(ruta=PAGOS_JSON_PATH) -> None:
    """Crea el archivo mock de pagos si aún no existe."""
    if not ruta.exists():
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(DEFAULT_PAGOS_DATA, archivo, ensure_ascii=False, indent=2)


def leer_pagos_json(ruta=PAGOS_JSON_PATH) -> dict:
    """Lee el JSON de pagos; devuelve copia de datos por defecto si falla."""
    try:
        crear_pagos_json_si_no_existe(ruta)
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (json.JSONDecodeError, OSError) as error:
        st.warning(f"No se pudo leer el archivo de pagos: {error}. Usando datos por defecto.")
        return copy.deepcopy(DEFAULT_PAGOS_DATA)


def guardar_pagos_json(datos: dict, ruta=PAGOS_JSON_PATH) -> bool:
    """Persiste los datos de pagos en el archivo JSON."""
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        return True
    except OSError as error:
        st.error(f"Error al guardar los pagos: {error}")
        return False


def formatear_stand_opcion(stand: dict) -> str:
    """Genera la etiqueta visible para el selectbox de stands."""
    valor = f"${stand['valor_total']:,}".replace(",", ".")
    return f"Stand {stand['id']} | {stand['pabellon']} | {stand['area']} | {valor}"


def obtener_stand_desde_json(datos: dict) -> dict:
    """Obtiene el stand definido en el JSON (estructura actual: un solo stand)."""
    return datos["stand"]
