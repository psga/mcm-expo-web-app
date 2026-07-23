import streamlit as st

from components.stand_selector import editor_admin
from db.plano_queries import guardar_diseno_plano, obtener_edicion_activa, obtener_plano_activo


def render():
    edicion = obtener_edicion_activa()
    if not edicion:
        st.warning("No hay edición activa. Crea una en la base de datos antes de diseñar el plano.")
        return

    st.title("Diseño del plano")
    st.caption(f"{edicion['nombre']} · {edicion['fecha_inicio']} – {edicion['fecha_fin']}")

    # guardar_diseno_plano() deja el plano en 'Aprobado' directamente, así
    # que lo que se ve aquí (vía obtener_plano_activo) es siempre lo último
    # guardado — no hay un borrador separado que se pierda entre sesiones.
    plano_actual = obtener_plano_activo(edicion["id_edicion"])

    resultado = editor_admin(stands_data=plano_actual or {}, key="editor_admin")

    if resultado and resultado.get("accion") == "guardar_diseno":
        id_plano = guardar_diseno_plano(edicion["id_edicion"], resultado["diseno"])
        cantidad_stands = len(resultado["diseno"].get("stands", []))
        # st.toast (no st.success) porque sobrevive al st.rerun() inmediato:
        # un st.success justo antes de rerun() se reemplaza antes de que
        # llegue a verse.
        st.toast(f"Plano guardado (id_plano: {id_plano}) con {cantidad_stands} stands. Ya es visible para las marcas.", icon="✅")
        st.rerun()
