"""Paso 5: Conciliación automática de pagos."""

import pandas as pd
import streamlit as st

from utils.formatters import formatear_moneda
from utils.setup import configurar_pagina
from utils.state import ir_a_paso, obtener_pagos_filtrados, reiniciar_wizard

configurar_pagina()

if not st.session_state.seleccion_confirmada:
    st.warning("Debe completar la selección de stand antes de conciliar pagos.")
    if st.button("Ir a selección de stand"):
        ir_a_paso(2)
    st.stop()

st.header("Conciliación automática de pagos")

if st.session_state.get("pago_simulado"):
    st.success(
        "Pago bloqueado correctamente. Su espacio en la EXPO está confirmado."
    )
    st.session_state.pago_simulado = False

stand = st.session_state.stand_seleccionado
pagos_filtrados = obtener_pagos_filtrados()
conceptos_filtrados = {pago["concepto"] for pago in pagos_filtrados}

opciones_pendientes = [
    pago["concepto"]
    for pago in st.session_state.plan_pagos
    if pago["concepto"] in conceptos_filtrados and pago["estado"] == "Pendiente"
]

valor_formateado = formatear_moneda(stand["valor_total"])
st.markdown(
    f"""
    <div class="caja-stand-info">
        <strong>Detalles del Espacio Seleccionado:</strong>
        <span>
            Stand {stand['id']} | {stand['zona_nombre']} | {stand['area_m2']} m²
            | Valor total: {valor_formateado}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

cuota_a_simular = st.selectbox(
    "Seleccione la cuota a simular",
    options=opciones_pendientes if opciones_pendientes else ["Sin cuotas pendientes"],
    disabled=not opciones_pendientes,
)

df = pd.DataFrame(pagos_filtrados)
df = df.rename(
    columns={
        "concepto": "Concepto",
        "valor": "Valor",
        "estado": "Estado",
        "fecha_limite": "Fecha Límite",
    }
)
df["Valor"] = df["Valor"].apply(formatear_moneda)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown('<div class="btn-simular-pago">', unsafe_allow_html=True)
if st.button("Simular Pago Ahora", type="primary", key="simular_pago"):
    if not opciones_pendientes:
        st.info("No hay pagos pendientes por simular en las cuotas seleccionadas.")
    else:
        pago_actualizado = False
        for pago in st.session_state.plan_pagos:
            if pago["concepto"] == cuota_a_simular and pago["estado"] == "Pendiente":
                pago["estado"] = "Bloqueado"
                pago_actualizado = True
                break

        if pago_actualizado:
            st.session_state.pago_simulado = True
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.button("Descargar Factura Electrónica (DIAN)"):
    st.toast("Descarga de factura electrónica simulada.")

st.divider()

col_volver, col_finalizar = st.columns(2)
with col_volver:
    if st.button("Volver", key="volver_paso5", use_container_width=True):
        ir_a_paso(4)
with col_finalizar:
    if st.button("Finalizar", key="finalizar", type="primary", use_container_width=True):
        st.session_state.mensaje_final = (
            "Proceso finalizado con éxito. Gracias por participar en la EXPO Maratón Medellín."
        )
        reiniciar_wizard()
        ir_a_paso(1)
