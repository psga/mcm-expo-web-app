import streamlit as st
import json

st.set_page_config(page_title="EXPO MCM - Contratos", layout="centered")

st.title("🏛️ Módulo de Generación de Contratos (HU4)")

# Validar que exista una pre-reserva activa antes de proceder
if 'datos_marca' not in st.session_state or st.session_state.datos_marca["stand_seleccionado"] is None:
    st.warning("⚠️ No se ha detectado ninguna pre-reserva activa. Por favor, regrese a la página de **Inicio** y seleccione un stand.")
else:
    # Datos cargados de la sesión
    stand_actual = st.session_state.datos_marca["stand_seleccionado"]
    precio_actual = st.session_state.datos_marca["precio_stand"]

    st.write("Verifique y actualice la información tributaria y jurídica de su empresa para generar el documento:")

    # Formulario interactivo (Escenario 2 de HU4)
    col1, col2 = st.columns(2)
    with col1:
        nombre_editado = st.text_input("Razón Social de la Marca", value=st.session_state.datos_marca["nombre"])
        nit_editado = st.text_input("NIT de la Empresa", value=st.session_state.datos_marca["nit"])
    with col2:
        representante_editado = st.text_input("Nombre del Representante Legal", value=st.session_state.datos_marca["representante"])
        email_editado = st.text_input("Email Notificaciones", value=st.session_state.datos_marca["email_rep"])

    # Actualizar estado de sesión con los cambios
    st.session_state.datos_marca["nombre"] = nombre_editado
    st.session_state.datos_marca["nit"] = nit_editado
    st.session_state.datos_marca["representante"] = representante_editado
    st.session_state.datos_marca["email_rep"] = email_editado

    # Estructura del Contrato Dinámico con el precio extraído del JSON
    texto_contrato = f"""
    CONTRATO DE ARRENDAMIENTO DE ESPACIO COMERCIAL - EXPO MCM 2026

    Arrendador: Corporación Maratón Medellín (MCM)
    Arrendatario: {st.session_state.datos_marca['nombre']} (NIT: {st.session_state.datos_marca['nit']})
    Representante Legal: {st.session_state.datos_marca['representante']}
    
    CLÁUSULAS PRINCIPALES:
    PRIMERA. OBJETO: MCM entrega el uso temporal de la ubicación '{stand_actual}' en Plaza Mayor.
    SEGUNDA. VALOR: Las partes fijan el canon de arrendamiento en la suma de ${precio_actual:,.0f} COP.
    TERCERA. VIGENCIA: Este contrato tiene efecto para los días de desarrollo de la feria.

    Enviado para notificación de firma electrónica a: {st.session_state.datos_marca['email_rep']}.
    """

    st.subheader("Borrador del Contrato Generado")
    st.text_area("Contrato Legal", value=texto_contrato, height=220, disabled=True)

    # Botones de Acción
    col_descarga, col_enviar = st.columns(2)
    with col_descarga:
        st.download_button(
            label="📥 Descargar Contrato (.txt)",
            data=texto_contrato,
            file_name=f"Contrato_{st.session_state.datos_marca['nombre'].replace(' ', '_')}.txt",
            mime="text/plain"
        )
        
    with col_enviar:
        if st.button("Enviar Solicitud de Firma Digital", type="primary"):
            # Actualizar el estado del Stand en el archivo externo JSON a "Pre-reserva"
            with open("stands_db.json", "r+", encoding="utf-8") as f:
                data = json.load(f)
                data[stand_actual]["estado"] = "Pre-reserva"
                data[stand_actual]["marca_reservada"] = st.session_state.datos_marca["nombre"]
                f.seek(0)
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.truncate()
                
            st.success("¡Solicitud enviada! El stand ha cambiado de estado a 'Pre-reserva' en la base de datos. Diríjase a la sección de **2_HU6_Pagos**.")
