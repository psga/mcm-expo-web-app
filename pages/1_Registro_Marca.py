"""Paso 1: Registro de datos de la marca."""

import streamlit as st

from utils.setup import configurar_pagina
from utils.state import ir_a_paso

configurar_pagina()

marca = st.session_state.marca

with st.form("form_marca", clear_on_submit=False):
    st.markdown("### Registro de marca")
    st.markdown("Registra los datos de la marca")

    nombre = st.text_input(
        "Nombre de la marca *",
        value=marca["nombre"],
        placeholder="MiMarca",
    )
    nit = st.text_input(
        "NIT de la empresa *",
        value=marca["nit"],
        placeholder="123456789",
    )
    correo = st.text_input(
        "Correo electrónico *",
        value=marca["correo"],
        placeholder="contacto@marca.com",
    )
    telefono = st.text_input(
        "Teléfono *",
        value=marca["telefono"],
        placeholder="",
    )
    patrocinadora = st.selectbox(
        "¿Es patrocinadora? *",
        options=["Seleccione", "Sí", "No"],
        index=["Seleccione", "Sí", "No"].index(marca["patrocinadora"]),
        help="Las marcas patrocinadoras tienen prioridad en la selección de stands.",
    )

    enviado = st.form_submit_button("Registrar marca", type="primary")

    if enviado:
        campos_vacios = not all(
            [nombre.strip(), nit.strip(), correo.strip(), telefono.strip()]
        )
        patrocinadora_invalida = patrocinadora == "Seleccione"

        if campos_vacios or patrocinadora_invalida:
            st.error("Por favor, completa todos los campos obligatorios.")
        else:
            st.session_state.marca = {
                "nombre": nombre.strip(),
                "nit": nit.strip(),
                "correo": correo.strip(),
                "telefono": telefono.strip(),
                "patrocinadora": patrocinadora,
            }
            st.session_state.registro_exitoso = True
            ir_a_paso(2)
