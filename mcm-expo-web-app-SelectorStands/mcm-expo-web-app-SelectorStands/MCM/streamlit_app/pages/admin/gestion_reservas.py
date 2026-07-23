import streamlit as st

from db.reserva_queries import cancelar_reserva, obtener_detalle_reserva, obtener_todas_reservas


def render():
    st.title("Reservas")

    reservas = obtener_todas_reservas()
    if not reservas:
        st.info("Todavía no hay reservas registradas.")
        return

    for reserva in reservas:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.markdown(f"**{reserva['nombre_comercial']}** · Stand {reserva['codigo_stand']}")
            col2.metric("Área", f"{reserva['area_m2']} m²")
            col3.metric("Precio base", f"${reserva['precio_base']:,.0f}")
            col4.markdown(f"Reserva: **{reserva['estado_reserva']}**")
            st.caption(f"Stand: {reserva['estado_stand']} · Reservado el {reserva['fecha_reserva']}")

            with st.expander("Ver detalle"):
                detalle = obtener_detalle_reserva(reserva["id_reserva"])

                if detalle["servicios"]:
                    for servicio in detalle["servicios"]:
                        extra = servicio["cantidad"] - servicio["cantidad_base"]
                        st.write(
                            f"- {servicio['nombre_servicio']}: {servicio['cantidad']} "
                            f"(dotación base {servicio['cantidad_base']}, extra {extra})"
                        )
                else:
                    st.write("Sin servicios adicionales registrados.")

                st.write(f"Tomas eléctricas: {detalle['tomas']}")
                st.write(f"Estado del contrato: {detalle['estado_contrato'] or 'Sin contrato generado'}")

            if reserva["estado_reserva"] == "Pendiente":
                if st.button("Cancelar reserva", key=f"cancelar_{reserva['id_reserva']}"):
                    try:
                        cancelar_reserva(reserva["id_reserva"])
                    except ValueError as error:
                        st.error(str(error))
                    else:
                        st.toast(f"Reserva #{reserva['id_reserva']} cancelada.", icon="🗑️")
                        st.rerun()
