"""Paso 3: Generación del contrato."""

import streamlit as st

from utils.formatters import formatear_moneda
from utils.setup import configurar_pagina
from utils.state import ir_a_paso, obtener_pagos_filtrados

configurar_pagina()

if not st.session_state.seleccion_confirmada:
    st.warning("Debe confirmar la selección de stand y cuotas antes de continuar.")
    if st.button("Ir a selección de stand"):
        ir_a_paso(2)
    st.stop()

if st.session_state.get("seleccion_exitosa"):
    st.success("Selección de stand y cuotas confirmada")
    st.session_state.seleccion_exitosa = False

st.header("Generación del contrato")
st.info(
    "El contrato ha sido prediligenciado con los datos proporcionados. "
    "Por favor, verifica la información."
)

marca = st.session_state.marca
stand = st.session_state.stand_seleccionado
pagos = obtener_pagos_filtrados()
cuotas_texto = ", ".join(p["concepto"] for p in pagos)
valor_total = formatear_moneda(stand["valor_total"])

st.markdown(
    f"""
    <div class="caja-contrato">
        <h3>Contrato de Participación - EXPO</h3>
        <p>
            Entre los suscritos, <strong>MCM</strong> y la marca
            <strong>{marca["nombre"]}</strong> con NIT <strong>{marca["nit"]}</strong>,
            correo electrónico <strong>{marca["correo"]}</strong> y teléfono
            <strong>{marca["telefono"]}</strong>, acuerdan la participación en el
            <strong>Stand {stand["id"]}</strong> ({stand["pabellon"]}, {stand["area"]})
            de la EXPO Maratón Medellín, por un valor total de <strong>{valor_total}</strong>.
        </p>
        <p>
            La marca se declara como patrocinadora: <strong>{marca["patrocinadora"]}</strong>.
        </p>
        <p>
            Las partes aceptan las condiciones generales de participación, incluyendo
            el cronograma de pagos ({cuotas_texto}) y las normas de montaje
            del espacio asignado.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("Editar campos del contrato"):
    ir_a_paso(1)

if st.button("Descargar PDF"):
    st.toast("Descarga de PDF simulada. El contrato se generará próximamente.")

st.divider()

col_volver, col_siguiente = st.columns(2)
with col_volver:
    if st.button("Volver", use_container_width=True):
        ir_a_paso(2)
with col_siguiente:
    if st.button("Siguiente", type="primary", use_container_width=True):
        ir_a_paso(4)
