"""
EXPO Maratón Medellín - Wizard de registro de stands.
Punto de entrada con navegación multipágina (st.navigation).
"""

import streamlit as st

from utils.constants import RUTAS_PASOS
from utils.json_data import crear_pagos_json_si_no_existe
from utils.state import inicializar_session_state

st.set_page_config(
    page_title="EXPO Maratón Medellín - Registro de Stands",
    layout="wide",
    initial_sidebar_state="expanded",
)

crear_pagos_json_si_no_existe()
inicializar_session_state()
st.switch_page(RUTAS_PASOS[st.session_state.step])
