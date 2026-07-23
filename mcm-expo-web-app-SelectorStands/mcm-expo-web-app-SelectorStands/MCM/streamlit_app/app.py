import streamlit as st

from db.auth import login_admin, login_marca
from flujo_marca import mostrar_flujo_marca
from pages.admin import diseno_plano, gestion_pagos, gestion_reservas
from utils.state import ir_a_paso, iniciar_sesion_marca

st.set_page_config(page_title="MCM Expo — Feria de Stands", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# Identidad visual MCM aplicada al chrome nativo de Streamlit (login, sidebar
# del dashboard admin). El flujo de la marca (flujo_marca.py) usa su propio
# CSS en utils/styles.py — mismo acento naranja, distinta implementación
# porque viene de un proyecto separado que se unificó acá.
# ---------------------------------------------------------------------------
_MCM_DARK = "#282828"
_MCM_ACCENT = "#e05b26"
_MCM_ACCENT_HOVER = "#c94e1f"
_MCM_GRAY_LIGHT = "#f5f5f5"


def _inyectar_estilos_mcm():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Figtree', 'Segoe UI', sans-serif;
        }}

        [data-testid="stAppViewContainer"], .stApp {{
            background-color: {_MCM_GRAY_LIGHT};
        }}

        [data-testid="stForm"] {{
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-top: 4px solid {_MCM_ACCENT};
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(40, 40, 40, 0.07);
            padding: 28px 24px;
        }}

        [data-testid="stSidebar"] {{
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }}

        .mcm-wordmark {{
            font-weight: 800;
            font-size: 1.4rem;
            letter-spacing: -0.02em;
            color: {_MCM_DARK};
        }}

        .mcm-wordmark span {{
            color: {_MCM_ACCENT};
        }}

        button[kind="primary"] {{
            background-color: {_MCM_ACCENT} !important;
            border-color: {_MCM_ACCENT} !important;
        }}

        button[kind="primary"]:hover {{
            background-color: {_MCM_ACCENT_HOVER} !important;
            border-color: {_MCM_ACCENT_HOVER} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _mostrar_wordmark():
    st.markdown('<div class="mcm-wordmark">MCM <span>Expo</span></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Estado 1: no autenticado — login, o "Registrarme" hacia el wizard
# ---------------------------------------------------------------------------
def _iniciar_sesion_admin(nombre: str):
    st.session_state["rol"] = "admin"
    st.session_state["nombre_usuario"] = nombre
    st.session_state["id_marca"] = None
    st.session_state["tab_activa"] = "diseno_plano"
    st.rerun()


def _formulario_login():
    with st.form("form_login"):
        correo = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        enviado = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

    if not enviado:
        return

    if not correo or not password:
        st.error("Completa correo y contraseña.")
        return

    if login_admin(correo, password):
        _iniciar_sesion_admin(nombre="Administrador MCM")
        return

    marca = login_marca(correo, password)
    if marca is not None:
        iniciar_sesion_marca(
            id_marca=marca["id_marca"],
            nombre_usuario=marca["nombre_comercial"],
            marca={
                "nombre": marca["nombre_comercial"],
                "nit": marca["nit"],
                "correo": marca["correo_corporativo"],
                "telefono": marca["telefono"],
            },
        )
        ir_a_paso(2)
        return

    st.error("Credenciales incorrectas")


def mostrar_login():
    _, columna_centro, _ = st.columns([1, 2, 1])
    with columna_centro:
        st.write("")
        st.write("")
        _mostrar_wordmark()
        st.title("Bienvenido")
        st.caption("Inicia sesión o registra tu marca para participar en la feria.")

        _formulario_login()

        st.divider()
        st.write("¿Tu marca todavía no está registrada?")
        if st.button("Registrarme", use_container_width=True):
            st.session_state["modo_auth"] = "registro"
            st.rerun()


# ---------------------------------------------------------------------------
# Estado 2: autenticado como admin — sidebar + dispatcher de tabs.
# Estado 3: marca (autenticada o a mitad de registro) — mostrar_flujo_marca()
# renderiza todo el proceso de compra dentro de esta misma página, sin
# st.switch_page.
# ---------------------------------------------------------------------------
TABS_ADMIN = {
    "🗺️ Diseño del plano": "diseno_plano",
    "📋 Reservas": "gestion_reservas",
    "💳 Pagos": "gestion_pagos",
}


def mostrar_sidebar_admin() -> None:
    with st.sidebar:
        _mostrar_wordmark()
        st.markdown(f"**{st.session_state['nombre_usuario']}**")
        st.caption("admin")
        st.divider()

        for etiqueta, tab_id in TABS_ADMIN.items():
            es_activa = st.session_state.get("tab_activa") == tab_id
            if st.button(
                etiqueta,
                use_container_width=True,
                type="primary" if es_activa else "secondary",
                key=f"nav_{tab_id}",
            ):
                st.session_state["tab_activa"] = tab_id
                st.rerun()

        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()


RENDERIZADORES_ADMIN = {
    "diseno_plano": diseno_plano.render,
    "gestion_reservas": gestion_reservas.render,
    "gestion_pagos": gestion_pagos.render,
}


def main():
    _inyectar_estilos_mcm()

    rol = st.session_state.get("rol")

    if rol == "admin":
        mostrar_sidebar_admin()
        tab_activa = st.session_state.get("tab_activa") or "diseno_plano"
        RENDERIZADORES_ADMIN[tab_activa]()
        return

    if rol == "marca" or st.session_state.get("modo_auth") == "registro":
        mostrar_flujo_marca()
        return

    mostrar_login()


main()
