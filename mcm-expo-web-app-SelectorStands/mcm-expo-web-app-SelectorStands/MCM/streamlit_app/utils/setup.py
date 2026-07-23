"""Configuración común del flujo de la marca (dentro de app.py, un solo script)."""

import streamlit as st

from utils.sidebar import renderizar_sidebar
from utils.state import inicializar_session_state
from utils.styles import inyectar_estilos


def configurar_flujo() -> None:
    """
    Aplica estilos y sidebar del flujo de compra. No llama a
    st.set_page_config: app.py ya lo hizo una sola vez para toda la app —
    acá todo corre en el mismo script, no hay páginas separadas.
    """
    inyectar_estilos()
    inicializar_session_state()
    renderizar_sidebar()

    if st.session_state.get("mensaje_final"):
        st.success(st.session_state.mensaje_final)
        del st.session_state.mensaje_final
