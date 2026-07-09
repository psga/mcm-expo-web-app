import streamlit as st


nombre = st.text_input("Nombre")

nit = st.text_input("NIT")

correo = st.text_input("Correo")

telefono = st.text_input("Telefono")

patrocinador = st.selectbox(
    "¿Es patrocinadora?",
    ["No", "Si"],
    key="patro"
)

if st.session_state.patro == "Si":

    codigo = st.text_input(
        "Codigo patrocinio"
    )

registrar = st.button("Registrar marca")
