"""Paso 4: Verificación de firma."""

import streamlit as st

from utils.setup import configurar_pagina
from utils.state import ir_a_paso

configurar_pagina()

st.header("Verificación de firma")
st.info("Adjunte su firma para la validación del contrato.")

archivo = st.file_uploader(
    "Arrastre y suelte su archivo aquí o haga clic para buscar",
    type=["png", "jpg", "pdf"],
    help="Tamaño máximo sugerido: 5MB. Formatos permitidos: PNG, JPG, PDF.",
    key=f"firma_uploader_{st.session_state.uploader_key}",
)

if archivo is not None and not st.session_state.firma_valida:
    if st.session_state.ultimo_archivo != archivo.name:
        st.session_state.ultimo_archivo = archivo.name
        st.session_state.firma_intentos += 1

    if st.session_state.firma_intentos == 1:
        st.error("El formato de la firma es inválido")
        if st.button("Reintentar"):
            st.session_state.uploader_key += 1
            st.rerun()
    else:
        st.session_state.firma_valida = True

if st.session_state.firma_valida:
    st.success("Firma validada correctamente.")

acepta = st.checkbox(
    "He leído y acepto los términos y condiciones de participación.",
    value=st.session_state.acepta_terminos,
    key="checkbox_terminos",
)
st.session_state.acepta_terminos = acepta

st.divider()

col_volver, col_siguiente = st.columns(2)
with col_volver:
    if st.button("Volver", key="volver_paso4", use_container_width=True):
        ir_a_paso(3)
with col_siguiente:
    if st.button("Siguiente", key="siguiente_paso4", type="primary", use_container_width=True):
        if not st.session_state.firma_valida or not st.session_state.acepta_terminos:
            st.warning(
                "Debe adjuntar una firma válida y aceptar los términos "
                "y condiciones para continuar."
            )
        else:
            ir_a_paso(5)
