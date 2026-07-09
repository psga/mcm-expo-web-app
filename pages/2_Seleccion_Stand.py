"""Paso 2: Selección de stand y plan de cuotas desde pagos_stand.json."""

import pandas as pd
import streamlit as st

from utils.formatters import formatear_moneda
from utils.json_data import formatear_stand_opcion, obtener_stand_desde_json
from utils.setup import configurar_pagina
from utils.state import ir_a_paso

configurar_pagina()

if not st.session_state.marca.get("nombre"):
    st.warning("Debe registrar los datos de la marca antes de continuar.")
    if st.button("Ir a registro de marca"):
        ir_a_paso(1)
    st.stop()

if st.session_state.get("registro_exitoso"):
    st.success("Registro exitoso")
    st.session_state.registro_exitoso = False

st.header("Selección de stand y plan de pagos")
st.info(
    "Seleccione el espacio comercial y las cuotas del plan de pagos "
    "disponibles en el catálogo."
)

datos = st.session_state.pagos_data
stand = obtener_stand_desde_json(datos)
pagos = datos["pagos"]
opcion_stand = formatear_stand_opcion(stand)

with st.form("form_seleccion_stand"):
    st.markdown("### Espacio comercial")
    stand_elegido = st.selectbox(
        "Seleccione el stand *",
        options=[opcion_stand],
        index=0,
        help="Opciones cargadas desde pagos_stand.json",
    )

    st.markdown("### Plan de cuotas")
    conceptos = [p["concepto"] for p in pagos]
    default_cuotas = (
        st.session_state.cuotas_seleccionadas
        if st.session_state.cuotas_seleccionadas
        else conceptos
    )
    cuotas = st.multiselect(
        "Seleccione las cuotas a incluir *",
        options=conceptos,
        default=default_cuotas,
        help="Cuotas y valores definidos en pagos_stand.json",
    )

    st.markdown("#### Resumen del plan seleccionado")
    pagos_preview = [p for p in pagos if p["concepto"] in cuotas] if cuotas else []
    if pagos_preview:
        df = pd.DataFrame(pagos_preview)
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

        total = sum(p["valor"] for p in pagos_preview)
        st.markdown(
            f"""
            <div class="caja-stand-info">
                <strong>Stand seleccionado:</strong>
                <span>{stand_elegido}</span><br><br>
                <strong>Valor total de cuotas seleccionadas:</strong>
                <span>{formatear_moneda(total)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Seleccione al menos una cuota para continuar.")

    confirmar = st.form_submit_button("Confirmar selección", type="primary")

    if confirmar:
        if not cuotas:
            st.error("Debe seleccionar al menos una cuota del plan de pagos.")
        else:
            st.session_state.stand_seleccionado = stand
            st.session_state.cuotas_seleccionadas = cuotas
            st.session_state.seleccion_confirmada = True
            st.session_state.seleccion_exitosa = True
            ir_a_paso(3)

st.divider()
if st.button("Volver", use_container_width=True):
    ir_a_paso(1)
