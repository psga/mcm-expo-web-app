import streamlit as st


with st.form("registro marca"):
    st.title("Registro de marca")
    st.markdown("##### Registra los datos de la marca")

    nombre = st.text_input("Nombre de la marca*")

    nit = st.text_input("NIT de la empresa*")

    correo = st.text_input("Correo electrónico*")

    telefono = st.text_input("Teléfono*")

    patrocinadora = st.selectbox(
        "¿Es patrocinadora?",
        ["No", "Sí"]
    )

    codigo = st.text_input("Codigo de patrocinio (SI ES PATROCINADORA)")

    enviar = st.form_submit_button("Registrar marca")
