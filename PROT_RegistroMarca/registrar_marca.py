import streamlit as st

def reg_marca(nombre, nit, correo, telefono, patrocinador, codigo):
    empresa = {
        "Nombre": nombre,
        "Nit": nit,
        "Correo": correo,
        "Telefono": telefono,
        "Patrocinador": patrocinador,
        "Codigo": codigo,
    }

    st.write(empresa)
