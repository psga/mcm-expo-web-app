"""
EXPO Maratón Medellín - Wizard de registro de stands.
Punto de entrada con navegación multipágina.
"""

import streamlit as st

from utils.constants import RUTAS_PASOS
from utils.state import inicializar_session_state

st.set_page_config(
    page_title="EXPO Maratón Medellín - Registro de Stands",
    layout="wide",
    initial_sidebar_state="expanded",
)

inicializar_session_state()
st.switch_page(RUTAS_PASOS[st.session_state.step])
