"""Paso 2: Selección de stand y plan de cuotas desde datasinimagen.json."""

import copy

import pandas as pd
import streamlit as st

from utils.formatters import formatear_moneda
from utils.json_data import (
    filtrar_por_zona,
    filtrar_stands_para_marca,
    formatear_stand_opcion,
    generar_plan_pagos,
    obtener_zonas_con_stands,
)
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
    "Seleccione el espacio comercial y las cuotas. "
    "Stands, zonas y precios se cargan desde datasinimagen.json."
)

datos = st.session_state.expo_data
es_patrocinadora = st.session_state.marca["patrocinadora"] == "Sí"
stands_disponibles = filtrar_stands_para_marca(datos, es_patrocinadora)

if not stands_disponibles:
    st.error("No hay stands disponibles para su tipo de marca en el catálogo.")
    if st.button("Volver al registro"):
        ir_a_paso(1)
    st.stop()

zona_filtro = st.selectbox(
    "Filtrar por zona",
    options=obtener_zonas_con_stands(stands_disponibles),
    key="filtro_zona_stand",
)
stands_filtrados = filtrar_por_zona(stands_disponibles, zona_filtro)

opciones_stand = {formatear_stand_opcion(stand): stand for stand in stands_filtrados}
etiquetas = list(opciones_stand.keys())

if not etiquetas:
    st.warning("No hay stands en la zona seleccionada. Elija otra zona.")
    st.stop()

# Si cambia zona o stand, reiniciar cuotas al plan completo del stand actual
stand_etiqueta = st.selectbox(
    "Seleccione el stand *",
    options=etiquetas,
    key="stand_etiqueta_sel",
    help="Datos del stand: id, zona, área, precio/m² y valor total (datasinimagen.json)",
)
stand = opciones_stand[stand_etiqueta]
plan_pagos = generar_plan_pagos(stand["valor_total"])
conceptos = [pago["concepto"] for pago in plan_pagos]

if st.session_state.get("stand_preview_id") != stand["id"]:
    st.session_state.stand_preview_id = stand["id"]
    st.session_state.cuotas_sel = conceptos.copy()

st.markdown(
    f"""
    <div class="caja-stand-info">
        <strong>Detalle del stand:</strong>
        <span>
            {stand['id']} | Zona: {stand['zona_nombre']} | Área: {stand['area_m2']} m² |
            Precio/m²: {formatear_moneda(stand['precioM2'])} |
            Valor total: {formatear_moneda(stand['valor_total'])} |
            Estado: {stand['estado']}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Plan de cuotas")
st.caption(
    "Las cuotas se calculan a partir del valor total del stand seleccionado "
    "(30% Anticipo, 35% Pago 1, 35% Pago 2). Los cambios se reflejan al instante."
)

cuotas = st.multiselect(
    "Seleccione las cuotas a incluir *",
    options=conceptos,
    key="cuotas_sel",
)

pagos_preview = [pago for pago in plan_pagos if pago["concepto"] in cuotas]
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

    total_cuotas = sum(pago["valor"] for pago in pagos_preview)
    st.markdown(
        f"**Valor total de cuotas seleccionadas:** {formatear_moneda(total_cuotas)}"
    )
else:
    st.warning("Seleccione al menos una cuota para continuar.")

st.divider()

col_volver, col_confirmar = st.columns(2)
with col_volver:
    if st.button("Volver", use_container_width=True):
        ir_a_paso(1)
with col_confirmar:
    if st.button("Confirmar selección", type="primary", use_container_width=True):
        if not cuotas:
            st.error("Debe seleccionar al menos una cuota del plan de pagos.")
        else:
            st.session_state.stand_seleccionado = stand
            st.session_state.plan_pagos = copy.deepcopy(plan_pagos)
            st.session_state.cuotas_seleccionadas = cuotas.copy()
            st.session_state.seleccion_confirmada = True
            st.session_state.seleccion_exitosa = True
            ir_a_paso(3)
