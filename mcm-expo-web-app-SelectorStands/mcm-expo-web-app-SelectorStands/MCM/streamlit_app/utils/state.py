"""Gestión de session_state y navegación del flujo de la marca.

Todo el proceso de compra (registro -> selección -> contrato -> firma ->
pagos) corre dentro de un único script (flujo_marca.py, llamado desde
app.py) — no hay páginas separadas ni st.switch_page. "Avanzar de paso" acá
significa cambiar st.session_state.step y volver a renderizar con
st.rerun(), igual que el dashboard de tabs del admin.

Nota: rol / id_marca los administra directamente app.py (login) o
iniciar_sesion_marca() de acá (login o registro recién creado) —
inicializar_session_state() solo cubre las claves propias del flujo.
"""

import streamlit as st


def iniciar_sesion_marca(id_marca: int, nombre_usuario: str, marca: dict) -> None:
    """
    Guarda la sesión de una marca autenticada (login existente o registro
    recién creado) para que pueda entrar al flujo. No navega: quien llama
    decide el paso de entrada (normalmente ir_a_paso(2)).

    Parámetros:
        id_marca (int)
        nombre_usuario (str): nombre a mostrar en la sidebar del flujo.
        marca (dict): {nombre, nit, correo, telefono} — mismo shape que
            st.session_state.marca, para que el paso de contrato no
            necesite cambios.
    """
    st.session_state["rol"] = "marca"
    st.session_state["id_marca"] = id_marca
    st.session_state["nombre_usuario"] = nombre_usuario
    st.session_state["marca"] = marca
    st.session_state.pop("modo_auth", None)


def inicializar_session_state() -> None:
    """Inicializa las claves del wizard en st.session_state."""
    if "step" not in st.session_state:
        st.session_state.step = 1

    if "mostrar_mis_pagos" not in st.session_state:
        st.session_state.mostrar_mis_pagos = False
    if "mostrar_activos" not in st.session_state:
        st.session_state.mostrar_activos = False
    if "mostrar_info_tecnica" not in st.session_state:
        st.session_state.mostrar_info_tecnica = False

    if "marca" not in st.session_state:
        st.session_state.marca = {
            "nombre": "",
            "nit": "",
            "correo": "",
            "telefono": "",
        }

    if "stand_seleccionado" not in st.session_state:
        st.session_state.stand_seleccionado = None

    if "plan_pagos" not in st.session_state:
        st.session_state.plan_pagos = []

    if "cuotas_seleccionadas" not in st.session_state:
        st.session_state.cuotas_seleccionadas = []

    if "seleccion_confirmada" not in st.session_state:
        st.session_state.seleccion_confirmada = False

    if "id_reserva" not in st.session_state:
        st.session_state.id_reserva = None
    if "id_contrato" not in st.session_state:
        st.session_state.id_contrato = None
    if "id_factura" not in st.session_state:
        st.session_state.id_factura = None

    if "firma_intentos" not in st.session_state:
        st.session_state.firma_intentos = 0
    if "firma_valida" not in st.session_state:
        st.session_state.firma_valida = False
    if "ultimo_archivo" not in st.session_state:
        st.session_state.ultimo_archivo = None
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "acepta_terminos" not in st.session_state:
        st.session_state.acepta_terminos = False
    if "registro_exitoso" not in st.session_state:
        st.session_state.registro_exitoso = False


def reiniciar_wizard() -> None:
    """
    Limpia el estado del wizard (NO cierra sesión) para que la marca pueda
    hacer una nueva selección desde cero. rol/id_marca/nombre_usuario se
    conservan a propósito.
    """
    claves = [
        "step",
        "mostrar_mis_pagos",
        "mostrar_activos",
        "mostrar_info_tecnica",
        "marca",
        "stand_seleccionado",
        "plan_pagos",
        "cuotas_seleccionadas",
        "seleccion_confirmada",
        "id_reserva",
        "id_contrato",
        "id_factura",
        "stand_preview_id",
        "cuotas_sel",
        "stand_etiqueta_sel",
        "filtro_zona_stand",
        "firma_intentos",
        "firma_valida",
        "ultimo_archivo",
        "uploader_key",
        "acepta_terminos",
        "registro_exitoso",
        "pago_simulado",
        "seleccion_exitosa",
    ]
    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]
    inicializar_session_state()
    st.session_state.step = 1


def ir_a_paso(paso: int) -> None:
    """Cambia al paso indicado dentro del mismo flujo de una sola página."""
    st.session_state.step = paso
    st.session_state.mostrar_mis_pagos = False
    st.session_state.mostrar_activos = False
    st.session_state.mostrar_info_tecnica = False
    st.rerun()


def obtener_pagos_filtrados() -> list:
    """Devuelve las cuotas seleccionadas del plan en sesión."""
    pagos = st.session_state.plan_pagos
    seleccion = st.session_state.cuotas_seleccionadas
    if not seleccion:
        return pagos
    return [pago for pago in pagos if pago["concepto"] in seleccion]
