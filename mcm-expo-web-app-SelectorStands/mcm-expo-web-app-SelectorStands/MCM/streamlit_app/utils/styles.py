"""Estilos CSS del wizard."""

import streamlit as st


def inyectar_estilos() -> None:
    """Inyecta CSS personalizado para botones, resaltados y cajas informativas."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            div.stButton > button[kind="primary"],
            div.stButton > button[data-testid="baseButton-primary"] {
                background-color: #FF6600 !important;
                border-color: #FF6600 !important;
                color: #ffffff !important;
            }
            div.stButton > button[kind="primary"]:hover,
            div.stButton > button[data-testid="baseButton-primary"]:hover {
                background-color: #E55A00 !important;
                border-color: #E55A00 !important;
            }
            .paso-activo {
                color: #FF6600 !important;
                font-weight: bold !important;
            }
            .paso-completado {
                color: #28a745 !important;
            }
            .paso-pendiente {
                color: #888888 !important;
            }
            .caja-contrato,
            .caja-stand-info {
                border: 2px solid #FF6600;
                border-radius: 8px;
                padding: 24px;
                background-color: #fafafa !important;
                color: #1a1a1a !important;
                margin: 16px 0;
            }
            .caja-contrato h3 {
                color: #FF6600 !important;
                margin-top: 0;
            }
            .caja-contrato p,
            .caja-contrato strong,
            .caja-stand-info,
            .caja-stand-info strong,
            .caja-stand-info span {
                color: #1a1a1a !important;
            }
            div[data-testid="stForm"] h3 {
                color: #FF6600 !important;
                margin-bottom: 0.25rem;
            }
            .btn-simular-pago button {
                background-color: #FF6600 !important;
                color: white !important;
                font-weight: bold !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
