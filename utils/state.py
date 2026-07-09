"""Gestión de session_state y navegación del wizard."""

import streamlit as st

from utils.constants import RUTAS_PASOS
from utils.json_data import leer_pagos_json


def inicializar_session_state() -> None:
    """Inicializa las claves del wizard en st.session_state."""
    if "step" not in st.session_state:
        st.session_state.step = 1

    if "marca" not in st.session_state:
        st.session_state.marca = {
            "nombre": "",
            "nit": "",
            "correo": "",
            "telefono": "",
            "patrocinadora": "Seleccione",
        }

    if "pagos_data" not in st.session_state:
        st.session_state.pagos_data = leer_pagos_json()

    if "stand_seleccionado" not in st.session_state:
        st.session_state.stand_seleccionado = None

    if "cuotas_seleccionadas" not in st.session_state:
        st.session_state.cuotas_seleccionadas = []

    if "seleccion_confirmada" not in st.session_state:
        st.session_state.seleccion_confirmada = False

    if "firma_intentos" not in st.session_state:
        st.session_state.firma_intentos = 0
    if "firma_valida" not in st.session_state:
        st.session_state.firma_valida = False
    if "ultimo_archivo" not in st.session_state:
        st.session_state.ultimo_archivo = None
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "acepta_terminos" not in st.session_state:
        st.session_state.acepta_terminos = False
    if "registro_exitoso" not in st.session_state:
        st.session_state.registro_exitoso = False


def reiniciar_wizard() -> None:
    """Limpia el estado y reinicia el wizard."""
    claves = [
        "step",
        "marca",
        "pagos_data",
        "stand_seleccionado",
        "cuotas_seleccionadas",
        "seleccion_confirmada",
        "firma_intentos",
        "firma_valida",
        "ultimo_archivo",
        "uploader_key",
        "acepta_terminos",
        "registro_exitoso",
        "pago_simulado",
        "seleccion_exitosa",
    ]
    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]
    inicializar_session_state()
    st.session_state.step = 1


def ir_a_paso(paso: int) -> None:
    """Cambia al paso indicado y navega a la página correspondiente."""
    st.session_state.step = paso
    st.switch_page(RUTAS_PASOS[paso])


def obtener_pagos_filtrados() -> list:
    """Devuelve las cuotas seleccionadas o todas si no hay filtro."""
    pagos = st.session_state.pagos_data["pagos"]
    seleccion = st.session_state.cuotas_seleccionadas
    if not seleccion:
        return pagos
    return [p for p in pagos if p["concepto"] in seleccion]
