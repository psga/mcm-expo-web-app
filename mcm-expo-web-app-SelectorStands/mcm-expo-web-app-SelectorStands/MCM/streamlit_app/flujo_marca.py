"""Flujo de compra de la marca: registro -> selección de stand -> contrato ->
firma -> pagos, todo dentro de una sola página (sin st.switch_page).

app.py llama a mostrar_flujo_marca() una vez que decide que el usuario
autenticado es una marca (o que está a mitad de registrarse); acá adentro
se decide qué sección pintar según st.session_state.step /
st.session_state.mostrar_mis_pagos, y "avanzar" es solo un st.rerun()
(ver utils.state.ir_a_paso), no una navegación de página real.
"""

import re

import pandas as pd
import streamlit as st

from components.stand_selector import selector_cliente
from db.activos_queries import (
    actualizar_redes_sociales,
    obtener_activos_marca,
    obtener_redes_sociales,
    subir_activo_marca,
)
from db.auth import registrar_marca
from db.pago_queries import obtener_facturas_marca, registrar_pago
from db.plano_queries import obtener_edicion_activa, obtener_plano_activo
from db.reserva_queries import (
    crear_contrato_y_factura,
    crear_reserva,
    marca_esta_formalizada,
    marca_tiene_contrato_firmado,
    marcar_contrato_firmado,
    obtener_reservas_marca,
)
from utils.formatters import formatear_moneda
from utils.pagos import generar_plan_pagos
from utils.setup import configurar_flujo
from utils.state import ir_a_paso, iniciar_sesion_marca, obtener_pagos_filtrados

_NIT_REGEX = re.compile(r"^\d{5,15}-\d$")
_METODOS_PAGO = ["Transferencia", "Pasarela_PSE", "Tarjeta_Credito"]
_ETIQUETAS_METODO = {
    "Transferencia": "Transferencia",
    "Pasarela_PSE": "PSE",
    "Tarjeta_Credito": "Tarjeta de crédito",
}
_EXTENSIONES_LOGO_VECTORIAL = ["svg", "ai", "eps", "pdf"]
_TAMANO_MAXIMO_LOGO_MB = 10
_EXTENSIONES_MANUAL = ["pdf"]
_TAMANO_MAXIMO_MANUAL_MB = 20


def mostrar_flujo_marca() -> None:
    """Punto de entrada único llamado desde app.py."""
    configurar_flujo()

    if st.session_state.get("rol") != "marca":
        _paso_registro()
        return

    if st.session_state.get("mostrar_mis_pagos"):
        _seccion_mis_pagos()
        return
    if st.session_state.get("mostrar_activos"):
        _seccion_activos_marca()
        return
    if st.session_state.get("mostrar_info_tecnica"):
        _seccion_info_tecnica()
        return

    pasos = {
        2: _paso_seleccion_stand,
        3: _paso_contrato,
        4: _paso_firma,
        5: _paso_pagos,
    }
    paso_actual = pasos.get(st.session_state.get("step", 2), _paso_seleccion_stand)
    paso_actual()


def _validar_nit(nit: str) -> bool:
    return bool(_NIT_REGEX.match(nit.strip()))


def _paso_registro() -> None:
    st.header("Registro de marca")
    st.caption(
        "Registra tu marca para participar en la EXPO. El correo y la contraseña "
        "quedan como tus credenciales para volver a iniciar sesión."
    )

    with st.form("form_marca", clear_on_submit=False):
        st.markdown("### Datos de la marca")
        nombre_comercial = st.text_input("Nombre de la marca *", placeholder="MiMarca")
        razon_social = st.text_input("Razón social *")
        nit = st.text_input("NIT *", placeholder="900123456-7")
        correo_corporativo = st.text_input("Correo electrónico *", placeholder="contacto@marca.com")
        password = st.text_input("Contraseña *", type="password")
        telefono = st.text_input("Teléfono *")
        sector_economico = st.text_input("Sector económico")

        st.markdown("### Contacto principal")
        contacto_nombre = st.text_input("Nombre del contacto *")
        contacto_cargo = st.text_input("Cargo del contacto")
        contacto_telefono = st.text_input("Teléfono del contacto *")

        enviado = st.form_submit_button("Registrar marca", type="primary")

        if not enviado:
            return

        campos_obligatorios = {
            "Nombre de la marca": nombre_comercial,
            "Razón social": razon_social,
            "NIT": nit,
            "Correo electrónico": correo_corporativo,
            "Contraseña": password,
            "Teléfono": telefono,
            "Nombre del contacto": contacto_nombre,
            "Teléfono del contacto": contacto_telefono,
        }
        faltantes = [etiqueta for etiqueta, valor in campos_obligatorios.items() if not valor.strip()]

        if faltantes:
            st.error(f"Completa los campos obligatorios: {', '.join(faltantes)}.")
            return
        if not _validar_nit(nit):
            st.error("El NIT debe tener el formato colombiano: dígitos, guión y dígito de verificación (ej. 900123456-7).")
            return
        if "@" not in correo_corporativo:
            st.error("Ingresa un correo electrónico válido.")
            return

        try:
            id_marca = registrar_marca(
                {
                    "nombre_comercial": nombre_comercial.strip(),
                    "razon_social": razon_social.strip(),
                    "nit": nit.strip(),
                    "correo_corporativo": correo_corporativo.strip(),
                    "password": password,
                    "telefono": telefono.strip(),
                    "sector_economico": sector_economico.strip() or None,
                    "contacto_nombre": contacto_nombre.strip(),
                    "contacto_cargo": contacto_cargo.strip() or None,
                    "contacto_telefono": contacto_telefono.strip(),
                }
            )
        except ValueError as error:
            st.error(str(error))
            return

        iniciar_sesion_marca(
            id_marca=id_marca,
            nombre_usuario=nombre_comercial.strip(),
            marca={
                "nombre": nombre_comercial.strip(),
                "nit": nit.strip(),
                "correo": correo_corporativo.strip(),
                "telefono": telefono.strip(),
            },
        )
        st.session_state.registro_exitoso = True
        ir_a_paso(2)


def _paso_seleccion_stand() -> None:
    if st.session_state.get("registro_exitoso"):
        st.success("Registro exitoso")
        st.session_state.registro_exitoso = False

    st.header("Selección de stand")
    st.info("Selecciona un espacio disponible en el plano y confirma tu reserva desde el modal.")

    edicion = obtener_edicion_activa()
    if not edicion:
        st.warning("No hay una feria activa en este momento.")
        return

    plano = obtener_plano_activo(edicion["id_edicion"])
    if not plano:
        st.warning("El administrador aún no ha publicado el diseño de stands.")
        return

    resultado = selector_cliente(
        stands_data=plano,
        imagen_url="",  # ya va embebida en plano["imagenPlano"]
        id_marca=st.session_state["id_marca"],
        key="selector_marca",
    )

    if not resultado or resultado.get("accion") != "confirmar_reserva":
        return

    codigo_stand = resultado["standId"]
    stand_dict = next((s for s in plano["stands"] if s["id"] == codigo_stand), None)
    if stand_dict is None:
        st.error("No se encontró el stand seleccionado en el plano vigente. Intenta de nuevo.")
        return

    try:
        id_reserva = crear_reserva(
            id_marca=st.session_state["id_marca"],
            codigo_stand=codigo_stand,
            datos_reserva=resultado,
        )
    except ValueError as error:
        st.error(f"No fue posible reservar este stand: {error}")
        return

    try:
        datos_factura = crear_contrato_y_factura(id_reserva)
    except Exception:
        st.error("La reserva se creó, pero no se pudo generar el contrato/factura. Contacta a MCM.")
        return

    valor_total = datos_factura["monto_total"]

    # Shape compatible con lo que _paso_contrato()/_paso_pagos() esperan.
    st.session_state.stand_seleccionado = {
        "id": stand_dict["id"],
        "zona_nombre": stand_dict.get("zona_nombre") or "Sin zona",
        "area_m2": resultado["areaM2"],
        "precioM2": stand_dict["precioM2"],
        "valor_total": valor_total,
        "estado": stand_dict["estado"],
        "tipo": stand_dict["tipo"],
    }
    st.session_state.id_reserva = id_reserva
    st.session_state.id_contrato = datos_factura["id_contrato"]
    st.session_state.id_factura = datos_factura["id_factura"]

    plan_pagos = generar_plan_pagos(valor_total)
    st.session_state.plan_pagos = plan_pagos
    st.session_state.cuotas_seleccionadas = [pago["concepto"] for pago in plan_pagos]
    st.session_state.seleccion_confirmada = True
    st.session_state.seleccion_exitosa = True

    ir_a_paso(3)


def _paso_contrato() -> None:
    if not st.session_state.seleccion_confirmada:
        st.warning("Debe confirmar la selección de stand antes de continuar.")
        if st.button("Ir a selección de stand"):
            ir_a_paso(2)
        return

    if st.session_state.get("seleccion_exitosa"):
        st.success("Selección de stand confirmada")
        st.session_state.seleccion_exitosa = False

    st.header("Generación del contrato")
    st.info(
        "El contrato ha sido prediligenciado con los datos proporcionados. "
        "Por favor, verifica la información."
    )

    marca = st.session_state.marca
    stand = st.session_state.stand_seleccionado
    pagos = obtener_pagos_filtrados()
    cuotas_texto = ", ".join(pago["concepto"] for pago in pagos)
    valor_total = formatear_moneda(stand["valor_total"])
    categoria_espacio = "Patrocinador" if stand.get("tipo") == "patrocinador" else "General"

    st.markdown(
        f"""
        <div class="caja-contrato">
            <h3>Contrato de Participación - EXPO</h3>
            <p>
                Entre los suscritos, <strong>MCM</strong> y la marca
                <strong>{marca["nombre"]}</strong> con NIT <strong>{marca["nit"]}</strong>,
                correo electrónico <strong>{marca["correo"]}</strong> y teléfono
                <strong>{marca["telefono"]}</strong>, acuerdan la participación en el
                <strong>Stand {stand["id"]}</strong> (Zona {stand["zona_nombre"]},
                {stand["area_m2"]} m², {formatear_moneda(stand["precioM2"])}/m²)
                de la EXPO Maratón Medellín, por un valor total de <strong>{valor_total}</strong>
                (incluye IVA y mobiliario adicional solicitado).
            </p>
            <p>
                Categoría del espacio: <strong>{categoria_espacio}</strong>.
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

    if st.button("Descargar PDF"):
        st.toast("Descarga de PDF simulada. El contrato se generará próximamente.")

    st.divider()

    col_volver, col_siguiente = st.columns(2)
    with col_volver:
        if st.button("Volver", use_container_width=True):
            ir_a_paso(2)
        st.caption("Volver no cancela la reserva ya creada.")
    with col_siguiente:
        if st.button("Siguiente", type="primary", use_container_width=True):
            ir_a_paso(4)


def _paso_firma() -> None:
    if not st.session_state.seleccion_confirmada:
        st.warning("Debe confirmar la selección de stand antes de continuar.")
        if st.button("Ir a selección de stand"):
            ir_a_paso(2)
        return

    st.header("Verificación de firma")
    st.info("Adjunte su firma para la validación del contrato.")

    archivo = st.file_uploader(
        "Arrastre y suelte su archivo aquí o haga clic para buscar",
        type=["png", "jpg", "pdf"],
        help="Tamaño máximo sugerido: 5MB. Formatos permitidos: PNG, JPG, PDF.",
        key=f"firma_uploader_{st.session_state.uploader_key}",
    )

    if archivo is not None and not st.session_state.firma_valida:
        if st.session_state.ultimo_archivo != archivo.name:
            st.session_state.ultimo_archivo = archivo.name
            st.session_state.firma_intentos += 1

        if st.session_state.firma_intentos == 1:
            st.error("El formato de la firma es inválido")
            if st.button("Reintentar"):
                st.session_state.uploader_key += 1
                st.rerun()
        else:
            st.session_state.firma_valida = True
            if st.session_state.id_contrato:
                marcar_contrato_firmado(st.session_state.id_contrato)

    if st.session_state.firma_valida:
        st.success("Firma validada correctamente.")

    acepta = st.checkbox(
        "He leído y acepto los términos y condiciones de participación.",
        value=st.session_state.acepta_terminos,
        key="checkbox_terminos",
    )
    st.session_state.acepta_terminos = acepta

    st.divider()

    col_volver, col_siguiente = st.columns(2)
    with col_volver:
        if st.button("Volver", key="volver_paso4", use_container_width=True):
            ir_a_paso(3)
    with col_siguiente:
        if st.button("Siguiente", key="siguiente_paso4", type="primary", use_container_width=True):
            if not st.session_state.firma_valida or not st.session_state.acepta_terminos:
                st.warning(
                    "Debe adjuntar una firma válida y aceptar los términos "
                    "y condiciones para continuar."
                )
            else:
                ir_a_paso(5)


def _paso_pagos() -> None:
    if not st.session_state.seleccion_confirmada:
        st.warning("Debe completar la selección de stand antes de conciliar pagos.")
        if st.button("Ir a selección de stand"):
            ir_a_paso(2)
        return

    st.header("Conciliación automática de pagos")
    st.caption(
        "Esta es una vista previa orientativa del plan de cuotas. El seguimiento "
        "real de tu factura (saldo, pagos verificados, subir comprobantes) está "
        "en **💳 Mis pagos**, en la barra lateral."
    )

    if st.session_state.get("pago_simulado"):
        st.success("Pago bloqueado correctamente. Su espacio en la EXPO está confirmado.")
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
        if st.button("Finalizar e ir a Mis pagos", key="finalizar", type="primary", use_container_width=True):
            st.session_state.mensaje_final = (
                "Proceso finalizado con éxito. Gracias por participar en la EXPO Maratón Medellín."
            )
            st.session_state.mostrar_mis_pagos = True
            st.rerun()


def _seccion_mis_pagos() -> None:
    """
    Sección adicional (no es un paso numerado del flujo): factura y pagos
    reales de la marca en la DB. Se llega acá desde el botón de la sidebar
    o al terminar el paso 5 — sin cambiar de página.
    """
    st.header("Mis pagos")

    if st.button("← Volver al proceso"):
        st.session_state.mostrar_mis_pagos = False
        st.rerun()

    id_marca = st.session_state["id_marca"]
    reservas = obtener_reservas_marca(id_marca)

    if not reservas:
        st.info("Todavía no tienes ninguna reserva. Vuelve al proceso para elegir tu espacio.")
        return

    facturas_por_reserva = {f["id_reserva"]: f for f in obtener_facturas_marca(id_marca)}

    for reserva in reservas:
        with st.container(border=True):
            st.subheader(f"Stand {reserva['codigo_stand']}")
            st.caption(f"Reserva #{reserva['id_reserva']} · {reserva['area_m2']} m²")
            st.markdown(f"**Estado de la reserva:** {reserva['estado_reserva']}")

            factura = facturas_por_reserva.get(reserva["id_reserva"])
            if factura is None:
                st.info("Todavía no se ha generado una factura para esta reserva.")
                continue

            col1, col2, col3 = st.columns(3)
            col1.metric("Total", f"${factura['monto_total']:,.0f}")
            col2.metric("Pagado", f"${factura['monto_pagado']:,.0f}")
            col3.metric("Saldo", f"${factura['saldo']:,.0f}")
            st.caption(f"Estado de la factura: {factura['estado_factura']}")

            with st.expander("Registrar nuevo pago"):
                with st.form(f"form_pago_{factura['id_factura']}"):
                    monto_pagado = st.number_input("Monto pagado", min_value=0, step=10000)
                    metodo_pago = st.selectbox(
                        "Método de pago", _METODOS_PAGO, format_func=lambda m: _ETIQUETAS_METODO[m]
                    )
                    numero_referencia = st.text_input("Número de referencia")
                    comprobante = st.file_uploader("Comprobante de pago", type=["pdf", "png", "jpg", "jpeg"])
                    enviado = st.form_submit_button("Registrar pago", type="primary")

                if enviado:
                    if monto_pagado <= 0 or not numero_referencia.strip():
                        st.error("Completa el monto y el número de referencia.")
                    else:
                        # TODO(producción): subir `comprobante` a un storage real
                        # (S3/GCS) y usar la URL pública resultante. El
                        # prototipo solo guarda el nombre del archivo.
                        url_comprobante = f"/comprobantes/{comprobante.name}" if comprobante else None
                        registrar_pago(
                            factura["id_factura"],
                            {
                                "monto_pagado": monto_pagado,
                                "metodo_pago": metodo_pago,
                                "numero_referencia": numero_referencia.strip(),
                                "url_comprobante": url_comprobante,
                            },
                        )
                        st.toast("Pago registrado. Quedará reflejado cuando el equipo MCM lo verifique.", icon="✅")
                        st.rerun()


def _seccion_activos_marca() -> None:
    """
    HU9 — Gestión de Activos de Marca.

    Precondición (Escenario 1): la marca ya formalizó su contrato — acá
    interpretado como contrato.firmado_marca = TRUE (completó el paso 4,
    Verificación de firma). Escenario 2 (formato/tamaño inválido) se valida
    explícitamente después de cada carga, no solo con el filtro de
    extensiones de st.file_uploader.
    """
    st.header("Activos de marca")

    if st.button("← Volver al proceso", key="volver_activos"):
        st.session_state.mostrar_activos = False
        st.rerun()

    id_marca = st.session_state["id_marca"]

    if not marca_tiene_contrato_firmado(id_marca):
        st.warning(
            "Este módulo se habilita cuando tu marca ha formalizado su contrato "
            "(paso 4 — Verificación de firma). Completa ese paso del proceso "
            "para poder cargar tus activos de marca."
        )
        return

    st.subheader("Logo en alta resolución (formato vectorial)")
    st.caption(
        f"Formatos aceptados: {', '.join(e.upper() for e in _EXTENSIONES_LOGO_VECTORIAL)} · "
        f"Peso máximo: {_TAMANO_MAXIMO_LOGO_MB} MB."
    )
    logo = st.file_uploader(
        "Logo vectorial", type=_EXTENSIONES_LOGO_VECTORIAL, key="uploader_logo", label_visibility="collapsed"
    )
    if logo is not None:
        extension = logo.name.rsplit(".", 1)[-1].lower() if "." in logo.name else ""
        tamano_mb = logo.size / (1024 * 1024)
        if extension not in _EXTENSIONES_LOGO_VECTORIAL or tamano_mb > _TAMANO_MAXIMO_LOGO_MB:
            st.error(
                f"Archivo rechazado: '{logo.name}' no cumple las especificaciones técnicas. "
                f"El logo debe estar en formato vectorial "
                f"({', '.join(e.upper() for e in _EXTENSIONES_LOGO_VECTORIAL)}) y pesar como "
                f"máximo {_TAMANO_MAXIMO_LOGO_MB} MB (este archivo pesa {tamano_mb:.1f} MB)."
            )
        elif st.button("Subir logo", key="btn_subir_logo"):
            url = f"/activos/{id_marca}/{logo.name}"
            subir_activo_marca(id_marca, "Logo_Vectorial", url)
            st.toast("Logo cargado. Se notificó al Área de Soporte de Marca.", icon="✅")
            st.rerun()

    st.subheader("Manual de identidad de marca")
    st.caption(f"Formato: PDF · Peso máximo: {_TAMANO_MAXIMO_MANUAL_MB} MB.")
    manual = st.file_uploader(
        "Manual de identidad", type=_EXTENSIONES_MANUAL, key="uploader_manual", label_visibility="collapsed"
    )
    if manual is not None:
        tamano_mb = manual.size / (1024 * 1024)
        if tamano_mb > _TAMANO_MAXIMO_MANUAL_MB:
            st.error(
                f"Archivo rechazado: '{manual.name}' pesa {tamano_mb:.1f} MB, supera el "
                f"máximo permitido de {_TAMANO_MAXIMO_MANUAL_MB} MB."
            )
        elif st.button("Subir manual de identidad", key="btn_subir_manual"):
            url = f"/activos/{id_marca}/{manual.name}"
            subir_activo_marca(id_marca, "Manual_Marca", url)
            st.toast("Manual cargado. Se notificó al Área de Soporte de Marca.", icon="✅")
            st.rerun()

    st.subheader("Redes sociales")
    redes_actuales = obtener_redes_sociales(id_marca)
    with st.form("form_redes_sociales"):
        instagram = st.text_input("Instagram", value=redes_actuales.get("instagram") or "")
        facebook = st.text_input("Facebook", value=redes_actuales.get("facebook") or "")
        sitio_web = st.text_input("Sitio web", value=redes_actuales.get("sitio_web") or "")
        guardar_redes = st.form_submit_button("Guardar redes sociales", type="primary")

    if guardar_redes:
        actualizar_redes_sociales(id_marca, instagram.strip(), facebook.strip(), sitio_web.strip())
        st.toast("Datos de redes sociales actualizados.", icon="✅")
        st.rerun()

    st.divider()
    st.subheader("Activos ya cargados")
    activos = obtener_activos_marca(id_marca)
    if not activos:
        st.info("Todavía no has cargado ningún activo.")
    else:
        for activo in activos:
            with st.container(border=True):
                st.markdown(f"**{activo['tipo_activo'].replace('_', ' ')}**")
                st.caption(
                    f"{activo['url_archivo']} · Estado: {activo['estado_validacion']} · "
                    f"{activo['fecha_carga']:%Y-%m-%d %H:%M}"
                )


def _seccion_info_tecnica() -> None:
    """
    HU10 — Centro de Documentación y Cronogramas.

    Precondición: marca_esta_formalizada (contrato firmado + pago
    confirmado, según RN011). Sin eso, el módulo queda inhabilitado con un
    mensaje explícito en vez de mostrar contenido.
    """
    st.header("Información técnica")

    if st.button("← Volver al proceso", key="volver_info_tecnica"):
        st.session_state.mostrar_info_tecnica = False
        st.rerun()

    id_marca = st.session_state["id_marca"]

    if not marca_esta_formalizada(id_marca):
        st.error(
            "El acceso a este módulo es exclusivo para marcas con contrato firmado y "
            "pago al día (según RN011). Completa la formalización de tu reserva (firma "
            "del contrato en el paso 4 y confirmación del pago) para habilitar la "
            "descarga del Manual del Expositor y el cronograma de montaje/desmontaje."
        )
        return

    st.success("Formalización verificada. Ya puedes descargar la documentación técnica.")

    marca = st.session_state.get("marca") or {}
    stand = st.session_state.get("stand_seleccionado") or {}

    manual_texto = (
        "MANUAL DEL EXPOSITOR - EXPO Maraton Medellin 2026\n\n"
        "1. Normas generales de montaje y desmontaje en Plaza Mayor.\n"
        "2. Horarios de acceso para personal de montaje.\n"
        "3. Especificaciones electricas y de mobiliario permitido.\n"
        "4. Contactos de soporte tecnico durante el evento.\n"
    )
    st.download_button(
        "📘 Descargar Manual del Expositor",
        data=manual_texto,
        file_name="manual_expositor_mcm_expo.txt",
        mime="text/plain",
    )

    cronograma_texto = (
        f"CRONOGRAMA PERSONALIZADO - {marca.get('nombre', '')}\n"
        f"Stand: {stand.get('id', 'N/D')} - Zona: {stand.get('zona_nombre', 'N/D')}\n\n"
        "Montaje: 2026-09-02 08:00 a 2026-09-03 20:00\n"
        "Ingreso de expositores: 2026-09-04 07:00\n"
        "Feria: 2026-09-04 al 2026-09-06\n"
        "Desmontaje: 2026-09-06 20:00 a 2026-09-07 18:00\n"
    )
    st.download_button(
        "🗓️ Descargar cronograma de ingresos personalizado",
        data=cronograma_texto,
        file_name="cronograma_montaje_mcm_expo.txt",
        mime="text/plain",
    )
