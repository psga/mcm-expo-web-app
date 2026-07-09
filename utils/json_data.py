"""Lectura y utilidades sobre datasinimagen.json (solo lectura)."""

import json

import streamlit as st

from utils.constants import DATA_JSON_PATH
from utils.formatters import formatear_moneda


def leer_expo_json(ruta=DATA_JSON_PATH) -> dict:
    """Lee datasinimagen.json de forma segura."""
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (json.JSONDecodeError, OSError) as error:
        st.error(f"No se pudo leer datasinimagen.json: {error}")
        st.stop()


def mapa_zonas(datos: dict) -> dict:
    """Indexa las zonas por id."""
    return {zona["id"]: zona for zona in datos.get("zonas", [])}


def calcular_area_m2(stand: dict) -> int:
    """Calcula el área en m² a partir de la grilla del stand."""
    filas = stand["filaFin"] - stand["filaInicio"] + 1
    columnas = stand["columnaFin"] - stand["columnaInicio"] + 1
    return filas * columnas


def enriquecer_stand(stand: dict, zonas: dict) -> dict:
    """Agrega datos derivados del JSON sin modificar el archivo."""
    zona = zonas.get(stand["zonaId"], {})
    area_m2 = calcular_area_m2(stand)
    valor_total = stand["precioM2"] * area_m2
    return {
        **stand,
        "zona_nombre": zona.get("nombre", stand["zonaId"]),
        "zona_precio_m2": zona.get("precioM2", stand["precioM2"]),
        "area_m2": area_m2,
        "valor_total": valor_total,
    }


def filtrar_stands_para_marca(datos: dict, es_patrocinadora: bool) -> list:
    """Filtra stands según el tipo de marca registrada."""
    zonas = mapa_zonas(datos)
    stands = datos.get("stands", [])

    if es_patrocinadora:
        candidatos = [s for s in stands if s.get("tipo") == "patrocinador"]
    else:
        candidatos = [
            s for s in stands if s.get("tipo") == "venta" and s.get("estado") == "disponible"
        ]

    return [enriquecer_stand(stand, zonas) for stand in candidatos]


def obtener_zonas_con_stands(stands: list) -> list:
    """Lista única de zonas presentes en los stands filtrados."""
    zonas = sorted({stand["zona_nombre"] for stand in stands})
    return ["Todas"] + zonas


def filtrar_por_zona(stands: list, zona: str) -> list:
    """Filtra stands por nombre de zona."""
    if zona == "Todas":
        return stands
    return [stand for stand in stands if stand["zona_nombre"] == zona]


def formatear_stand_opcion(stand: dict) -> str:
    """Etiqueta legible para el selectbox de stands."""
    return (
        f"{stand['id']} | {stand['zona_nombre']} | {stand['area_m2']} m² | "
        f"{formatear_moneda(stand['precioM2'])}/m² | "
        f"Total {formatear_moneda(stand['valor_total'])} | {stand['estado']}"
    )


def generar_plan_pagos(valor_total: int) -> list:
    """
    Genera el plan de cuotas en memoria a partir del valor del stand.
    El JSON no incluye cuotas; se calculan sin alterar datasinimagen.json.
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
