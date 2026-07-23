"""Barra lateral del flujo de compra: progreso + sesión."""

import streamlit as st

from utils.constants import PASOS

_FLAGS_SECCIONES_EXTRA = ("mostrar_mis_pagos", "mostrar_activos", "mostrar_info_tecnica")


def _mostrar_seccion_extra(flag: str) -> None:
    """
    Activa una de las secciones fuera de la secuencia numerada (Mis pagos /
    Activos de marca / Información técnica) y apaga las otras — son
    mutuamente excluyentes, si no, el dispatcher de flujo_marca.py se queda
    pegado en la primera que encuentre True.
    """
    for otro_flag in _FLAGS_SECCIONES_EXTRA:
        st.session_state[otro_flag] = otro_flag == flag
    st.rerun()


def renderizar_sidebar() -> None:
    """Muestra usuario/sesión, el progreso del flujo y accesos rápidos."""
    st.sidebar.markdown("**MCM Expo**")
    autenticada = st.session_state.get("rol") == "marca"
    st.sidebar.caption(st.session_state.get("nombre_usuario", "") if autenticada else "Registro de marca")
    st.sidebar.divider()

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

    st.sidebar.divider()

    if not autenticada:
        if st.sidebar.button("Volver al login", use_container_width=True):
            st.session_state.pop("modo_auth", None)
            st.rerun()
        return

    if st.sidebar.button("💳 Mis pagos", use_container_width=True):
        _mostrar_seccion_extra("mostrar_mis_pagos")
    if st.sidebar.button("🎨 Activos de marca", use_container_width=True):
        _mostrar_seccion_extra("mostrar_activos")
    if st.sidebar.button("📄 Información técnica", use_container_width=True):
        _mostrar_seccion_extra("mostrar_info_tecnica")
    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()
