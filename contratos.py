import streamlit as st

# Configuración básica de la página
st.set_page_config(page_title="Sistema EXPO MCM - Contratos", layout="centered")

# --- INICIALIZACIÓN DE ESTADOS (Session State) ---
# Esto permite simular la persistencia de datos del proceso en memoria
if 'paso_actual' not in st.session_state:
    st.session_state.paso_actual = "pre_reserva"  # Pasos: pre_reserva, verificacion_contrato, contrato_enviado

if 'datos_marca' not in st.session_state:
    # Datos simulados que provienen de la HU1 y HU2 (Registro y Selección de Stand)
    st.session_state.datos_marca = {
        "nombre": "Gatorade Colombia S.A.S.",
        "nit": "900.123.456-7",
        "representante": "Juan José Piedrahíta",
        "email_rep": "contacto@marca.com",
        "stand": "Stand Pabellón Amarillo - A-15 (3x3m)",
        "valor": "$2,500,000 COP"
    }

st.title("🏛️ Portal EXPO Maratón Medellín")
st.write("Módulo Automatizado de Formalización de Contratos")
st.divider()

# =====================================================================
# ESCENARIO 1: Creación de pre-reserva y envío automático (Simulado)
# =====================================================================
if st.session_state.paso_actual == "pre_reserva":
    st.subheader("📍 Paso 1: Confirmación de Pre-reserva")
    st.write("Usted ha seleccionado satisfactoriamente el siguiente espacio comercial en el mapa interactivo:")
    
    # Caja con la información del Stand seleccionado por la marca
    st.info(f"""
    **Stand Seleccionado:** {st.session_state.datos_marca['stand']}  
    **Valor de la Ubicación:** {st.session_state.datos_marca['valor']}  
    **Estado actual:** Pre-reservado temporalmente
    """)
    
    st.write("Al hacer clic en el siguiente botón, el sistema procesará la pre-reserva y generará automáticamente el borrador del contrato.")
    
    # Al hacer clic, se simula el comportamiento del "Cuando: El sistema procesa la pre-reserva"
    if st.button("Procesar Pre-reserva y Generar Contrato", type="primary"):
        st.session_state.paso_actual = "verificacion_contrato"
        st.rerun()


# =====================================================================
# ESCENARIO 2: Verificación y edición de información prediligenciada
# =====================================================================
elif st.session_state.paso_actual == "verificacion_contrato":
    st.subheader("📝 Paso 2: Verificación y Validación de Datos")
    st.write("El sistema ha generado un borrador prediligenciado. Si algún dato legal es incorrecto, puede editarlo en el formulario a continuación para asegurar su validez.")

    # Formulario interactivo (Cumple el criterio: "Entonces: El sistema permite editar información")
    col1, col2 = st.columns(2)
    with col1:
        nombre_editado = st.text_input("Razón Social de la Marca", value=st.session_state.datos_marca["nombre"])
        nit_editado = st.text_input("NIT / Identificación Tributaria", value=st.session_state.datos_marca["nit"])
    with col2:
        representante_editado = st.text_input("Nombre del Representante Legal", value=st.session_state.datos_marca["representante"])
        email_editado = st.text_input("Correo electrónico para Notificación Legal", value=st.session_state.datos_marca["email_rep"])

    # Actualizamos el estado con los datos editados por el usuario
    st.session_state.datos_marca["nombre"] = nombre_editado
    st.session_state.datos_marca["nit"] = nit_editado
    st.session_state.datos_marca["representante"] = representante_editado
    st.session_state.datos_marca["email_rep"] = email_editado

    # Plantilla dinámica de contrato que se actualiza en tiempo real según el formulario
    texto_contrato = f"""
    CONTRATO DE ARRENDAMIENTO DE ESPACIO COMERCIAL - EXPO MCM 2026

    Entre los suscritos a saber, de una parte, la Corporación Maratón Medellín (MCM), representada por su Dirección Operativa, y por la otra parte, la marca "{st.session_state.datos_marca['nombre']}", representada legalmente por {st.session_state.datos_marca['representante']}, identificado con NIT/CC {st.session_state.datos_marca['nit']}, se conviene celebrar el presente acuerdo comercial regido por las siguientes cláusulas:

    PRIMERA. OBJETO: MCM otorga el uso temporal y exclusivo del espacio denominado "{st.session_state.datos_marca['stand']}" en el recinto de Plaza Mayor Medellín.
    SEGUNDA. VALOR Y PAGO: El valor pactado para el arrendamiento es de {st.session_state.datos_marca['valor']}.
    TERCERA. COMPROMISO LOGÍSTICO: El expositor se compromete a cumplir estrictamente el reglamento y normas de montaje estipuladas por Plaza Mayor y el Manual de Expositores de MCM.
    CUARTA. PENALIDADES POR DESISTIMIENTO: En caso de cancelación unilateral de la participación tras la firma del presente acuerdo, la marca se somete a una penalidad del 30% del valor total.

    Para constancia, se procede a despachar de forma digital al correo: {st.session_state.datos_marca['email_rep']}.
    """

    st.write("---")
    st.write("### Vista Previa del Documento Legal:")
    # st.text_area actualiza el texto en pantalla de forma interactiva
    st.text_area("Cuerpo del Contrato Autogenerado", value=texto_contrato, height=300, disabled=True)

    # Navegación del prototipo
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("Volver"):
            st.session_state.paso_actual = "pre_reserva"
            st.rerun()
    with col_btn2:
        if st.button("Confirmar Borrador y Enviar Solicitud de Firma Digital", type="primary"):
            st.session_state.paso_actual = "contrato_enviado"
            st.rerun()


# =====================================================================
# FIN DEL FLUJO: Contrato Enviado a Firma Electrónica
# =====================================================================
elif st.session_state.paso_actual == "contrato_enviado":
    st.success("🎉 ¡Solicitud de Firma Digital Enviada Exitosamente!")
    st.write(f"El sistema de EXPO MCM ha generado la versión final del contrato de arrendamiento para el **{st.session_state.datos_marca['stand']}**.")
    
    st.info(f"""
    **Destinatario:** {st.session_state.datos_marca['representante']}  
    **Correo de Envío:** {st.session_state.datos_marca['email_rep']}  
    **Plataforma de Firma:** Certicamara / Adobe Sign (Integración simulada)
    """)
    
    st.write("Se ha enviado una notificación por correo electrónico con el enlace de firma electrónica segura. Una vez completado, el estado de la reserva cambiará automáticamente.")
    
    if st.button("Simular nuevo proceso (Reiniciar demo)"):
        st.session_state.paso_actual = "pre_reserva"
        st.rerun()
