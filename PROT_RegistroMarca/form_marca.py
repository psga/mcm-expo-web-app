import streamlit as st
from validar_form import val_reg
from registrar_marca import reg_marca

def formulario_marca():
    with st.form("registro marca"):
        st.title("Datos de la marca")
        st.caption("##### Registra los datos de la marca para continuar.")

        nombre = st.text_input("Nombre de la marca:*")

        nit = st.text_input("NIT de la empresa:*")

        correo = st.text_input("Correo electrónico:*")

        telefono = st.text_input("Teléfono:*")

        patrocinadora = st.selectbox(
            "¿Es marca patrocinadora?",
            ["No", "Sí"]
        )

        codigo = st.text_input("Código de patrocinio (SI ES MARCA PATROCINADORA):")

        registrar = st.form_submit_button("Registrar marca")



        # Después del botón
        if registrar:
            errores = val_reg(
                nombre,
                nit,
                correo,
                telefono,
                patrocinadora,
                codigo
            )

            if errores:
                st.error("Hubo un error al registrar la marca.")
                for error in errores:
                    st.write(f"- {error}")
            else:
                reg_marca(nombre, nit, correo, telefono, patrocinadora, codigo)
                st.success("Registro de marca exitosa.")



formulario_marca()