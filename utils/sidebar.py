"""Barra lateral con indicador de progreso."""

import streamlit as st

from utils.constants import PASOS


def renderizar_sidebar() -> None:
    """Muestra el progreso del wizard en la barra lateral."""
    st.sidebar.header("Progreso")
    paso_actual = st.session_state.step

    for indice, nombre in enumerate(PASOS, start=1):
        if indice < paso_actual:
            st.sidebar.markdown(
                f'<p class="paso-completado">{indice}. {nombre}</p>',
                unsafe_allow_html=True,
            )
        elif indice == paso_actual:
            st.sidebar.markdown(
                f'<p class="paso-activo">{indice}. {nombre}</p>',
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.markdown(
                f'<p class="paso-pendiente">{indice}. {nombre}</p>',
                unsafe_allow_html=True,
            )
