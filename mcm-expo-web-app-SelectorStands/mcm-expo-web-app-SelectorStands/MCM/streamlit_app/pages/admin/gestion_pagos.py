import streamlit as st

from db.pago_queries import obtener_todos_pagos, verificar_pago


def render():
    st.title("Gestión de pagos")

    filas = obtener_todos_pagos()
    if not filas:
        st.info("Todavía no hay reservas con factura asociada.")
        return

    for fila in filas:
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            col1.markdown(f"**{fila['nombre_comercial']}** · Stand {fila['codigo_stand']}")
            col2.metric("Área", f"{fila['area_m2']} m²")
            col3.metric("Total", f"${fila['monto_total']:,.0f}")
            col4.metric("Pagado", f"${fila['monto_pagado']:,.0f}")
            col5.metric("Saldo", f"${fila['saldo']:,.0f}")
            st.caption(f"Estado factura: {fila['estado_factura'] or 'Sin factura'}")

            for pago in fila["pagos_pendientes"]:
                pcol1, pcol2 = st.columns([3, 1])
                pcol1.write(
                    f"Pago pendiente: ${pago['monto_pagado']:,.0f} · "
                    f"{pago['metodo_pago']} · ref {pago['numero_referencia']}"
                )
                if pcol2.button("Verificar pago", key=f"verificar_{pago['id_pago']}"):
                    verificar_pago(pago["id_pago"])
                    st.success("Pago verificado.")
                    st.rerun()
