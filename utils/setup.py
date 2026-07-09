"""Configuración común ejecutada al inicio de cada página del wizard."""

import streamlit as st

from utils.sidebar import renderizar_sidebar
from utils.state import inicializar_session_state
from utils.styles import inyectar_estilos


def configurar_pagina() -> None:
    """Aplica configuración, estilos y sidebar compartidos."""
    if "page_config_set" not in st.session_state:
        st.set_page_config(
            page_title="EXPO Maratón Medellín - Registro de Stands",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        st.session_state.page_config_set = True

    inyectar_estilos()
    inicializar_session_state()
    renderizar_sidebar()

    if st.session_state.get("mensaje_final"):
        st.success(st.session_state.mensaje_final)
        del st.session_state.mensaje_final
