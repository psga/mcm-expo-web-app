from db.connection import get_conn, release_conn

# Nombre exacto en servicio_adicional (ver db/seed.py) para cada clave de
# personalizacion que manda selector_cliente. El precio (COSTOS_EXTRA en
# frontend/selector.js) vive solo en el frontend para el cálculo en vivo del
# modal; acá solo hace falta el nombre para encontrar el id_servicio.
_NOMBRES_SERVICIOS = {
    "sillas": "Silla adicional",
    "mesas": "Mesa adicional",
    "paneles": "Panel adicional",
}
_CLAVES_DOTACION_BASE = {
    "sillas": "sillaBase",
    "mesas": "mesaBase",
    "paneles": "panelBase",
}
_IVA_COLOMBIA = 0.19


def crear_reserva(id_marca: int, codigo_stand: str, datos_reserva: dict) -> int:
    """
    Ejecuta la transacción ACID de reserva:
        1. SELECT ... FOR UPDATE en stand (bloqueo pesimista).
        2. Verifica que siga 'Disponible' y lo pasa a 'Pre_Reservado'.
        3. INSERT INTO reserva.
        4. INSERT INTO reserva_servicio_adicional por cada ítem de
           mobiliario con cantidad > 0 (sillas, mesas, paneles).

    Parámetros:
        id_marca (int)
        codigo_stand (str): stand.codigo_stand del stand elegido (viene
            como resultado["standId"] del componente selector_cliente).
        datos_reserva (dict): payload de selector_cliente cuando
            accion == "confirmar_reserva":
                {areaM2, precioBase, personalizacion: {sillas, sillaBase,
                 mesas, mesaBase, paneles, panelBase}, costoExtra,
                 precioTotal, tomas}

    Retorna:
        id_reserva.

    Lanza:
        ValueError si el stand no existe en un plano aprobado, o si ya no
        está 'Disponible' (lo tomó otra marca en una carrera de reservas).
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id_stand, s.estado_stand
                FROM stand s
                JOIN plano p ON p.id_plano = s.id_plano
                WHERE s.codigo_stand = %s AND p.estado_validacion = 'Aprobado'
                ORDER BY p.fecha_creacion DESC
                LIMIT 1
                FOR UPDATE OF s
                """,
                (codigo_stand,),
            )
            fila = cur.fetchone()
            if fila is None:
                raise ValueError(f"El stand {codigo_stand} no existe en ningún plano aprobado.")

            id_stand, estado_stand = fila
            if estado_stand != "Disponible":
                raise ValueError(f"El stand {codigo_stand} ya no está disponible (estado actual: {estado_stand}).")

            cur.execute(
                "UPDATE stand SET estado_stand = 'Pre_Reservado' WHERE id_stand = %s AND estado_stand = 'Disponible'",
                (id_stand,),
            )
            if cur.rowcount == 0:
                raise ValueError(f"El stand {codigo_stand} ya no está disponible (otra marca lo reservó primero).")

            observaciones = (
                f"Área: {datos_reserva.get('areaM2')} m² · "
                f"Precio total: {datos_reserva.get('precioTotal')} · "
                f"Tomas eléctricas: {datos_reserva.get('tomas')}"
            )
            cur.execute(
                """
                INSERT INTO reserva (id_stand, id_marca, estado_reserva, observaciones)
                VALUES (%s, %s, 'Pendiente', %s)
                RETURNING id_reserva
                """,
                (id_stand, id_marca, observaciones),
            )
            id_reserva = cur.fetchone()[0]

            personalizacion = datos_reserva.get("personalizacion", {})
            for tipo, nombre_servicio in _NOMBRES_SERVICIOS.items():
                cantidad = int(personalizacion.get(tipo, 0) or 0)
                if cantidad <= 0:
                    continue
                cantidad_base = int(personalizacion.get(_CLAVES_DOTACION_BASE[tipo], 0) or 0)

                cur.execute(
                    "SELECT id_servicio FROM servicio_adicional WHERE nombre_servicio = %s",
                    (nombre_servicio,),
                )
                fila_servicio = cur.fetchone()
                if fila_servicio is None:
                    continue  # servicio no seedeado; ejecutar `python -m db.seed`

                cur.execute(
                    """
                    INSERT INTO reserva_servicio_adicional (id_reserva, id_servicio, cantidad, cantidad_base)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_reserva, fila_servicio[0], cantidad, cantidad_base),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)

    return id_reserva


def crear_contrato_y_factura(id_reserva: int) -> dict:
    """
    Crea el contrato ('Borrador') y la factura ('Emitida') para una reserva
    recién creada. Se llama en una transacción propia, justo después de
    crear_reserva() — si esto falla, la reserva ya quedó registrada
    igual (no se revierte); se puede reintentar la facturación aparte.

    monto_subtotal = stand.precio_base (el precio ya calculado al guardar
    el diseño como precio_m2 * área del stand — no se vuelve a multiplicar
    por área acá, sería contarla dos veces) + la suma de
    (cantidad - cantidad_base) * precio_unitario de cada fila en
    reserva_servicio_adicional para esta reserva (costo del mobiliario
    pedido por encima de la dotación base).
    IVA: 19% sobre monto_subtotal (tasa colombiana estándar).
    monto_total = monto_subtotal + monto_iva.

    numero_factura_dian queda NULL: en producción lo asigna la integración
    con la DIAN, no se inventa un formato acá.

    Parámetros:
        id_reserva (int)

    Retorna:
        {"id_contrato": int, "id_factura": int, "monto_total": float}

    Lanza:
        ValueError si la reserva no existe.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.precio_base
                FROM reserva r
                JOIN stand s ON s.id_stand = r.id_stand
                WHERE r.id_reserva = %s
                """,
                (id_reserva,),
            )
            fila = cur.fetchone()
            if fila is None:
                raise ValueError(f"La reserva {id_reserva} no existe.")
            precio_base_stand = float(fila[0])

            cur.execute(
                """
                SELECT COALESCE(SUM((rsa.cantidad - rsa.cantidad_base) * sa.precio_unitario), 0)
                FROM reserva_servicio_adicional rsa
                JOIN servicio_adicional sa ON sa.id_servicio = rsa.id_servicio
                WHERE rsa.id_reserva = %s
                """,
                (id_reserva,),
            )
            costo_extra = float(cur.fetchone()[0])

            monto_subtotal = precio_base_stand + costo_extra
            monto_iva = round(monto_subtotal * _IVA_COLOMBIA, 2)
            monto_total = monto_subtotal + monto_iva

            cur.execute(
                """
                INSERT INTO contrato (id_reserva, estado_contrato)
                VALUES (%s, 'Borrador')
                RETURNING id_contrato
                """,
                (id_reserva,),
            )
            id_contrato = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO factura (
                    id_contrato, numero_factura_dian,
                    monto_subtotal, monto_iva, monto_total, estado_factura
                )
                VALUES (%s, NULL, %s, %s, %s, 'Emitida')
                RETURNING id_factura
                """,
                (id_contrato, monto_subtotal, monto_iva, monto_total),
            )
            id_factura = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)

    return {"id_contrato": id_contrato, "id_factura": id_factura, "monto_total": monto_total}


def marcar_contrato_firmado(id_contrato: int) -> None:
    """
    Marca contrato.firmado_marca = TRUE y, si ya estaba firmado_mcm, pasa
    estado_contrato a 'Firmado'. Se llama desde flujo_marca._paso_firma()
    cuando la firma simulada queda válida y la marca acepta los términos.

    Parámetros:
        id_contrato (int)

    Retorna:
        None.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE contrato SET firmado_marca = TRUE WHERE id_contrato = %s RETURNING firmado_mcm",
                (id_contrato,),
            )
            fila = cur.fetchone()
            if fila is not None and fila[0]:
                cur.execute(
                    "UPDATE contrato SET estado_contrato = 'Firmado' WHERE id_contrato = %s",
                    (id_contrato,),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)


def marca_tiene_contrato_firmado(id_marca: int) -> bool:
    """
    Gate de HU9 (Gestión de Activos de Marca): True si la marca ya firmó
    (contrato.firmado_marca) al menos un contrato — sin exigir todavía que
    el pago esté confirmado (ese es el gate más estricto de
    marca_esta_formalizada, para HU10).
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM contrato c
                JOIN reserva r ON r.id_reserva = c.id_reserva
                WHERE r.id_marca = %s AND c.firmado_marca = TRUE
                LIMIT 1
                """,
                (id_marca,),
            )
            return cur.fetchone() is not None
    finally:
        release_conn(conn)


def marca_esta_formalizada(id_marca: int) -> bool:
    """
    Gate de HU10 (Centro de Documentación y Cronogramas, según RN011):
    True si la marca tiene al menos una reserva en estado 'Formalizada'
    (contrato + pago confirmado — ver trg_confirmar_pago_stand en
    db/triggers/confirmar_pago.sql, que es lo único que pone a una reserva
    en ese estado).
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM reserva WHERE id_marca = %s AND estado_reserva = 'Formalizada' LIMIT 1",
                (id_marca,),
            )
            return cur.fetchone() is not None
    finally:
        release_conn(conn)


def obtener_reservas_marca(id_marca: int) -> list[dict]:
    """
    Trae todas las reservas de una marca con datos del stand y del contrato
    (si ya se generó). Alimenta flujo_marca._seccion_mis_pagos().

    Retorna: lista de dicts con {id_reserva, codigo_stand, area_m2,
    precio_base, estado_reserva, fecha_reserva, estado_stand, id_contrato,
    estado_contrato}.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id_reserva, s.codigo_stand, s.area_m2, s.precio_base,
                    r.estado_reserva, r.fecha_reserva, s.estado_stand,
                    c.id_contrato, c.estado_contrato
                FROM reserva r
                JOIN stand s ON s.id_stand = r.id_stand
                LEFT JOIN contrato c ON c.id_reserva = r.id_reserva
                WHERE r.id_marca = %s
                ORDER BY r.fecha_reserva DESC
                """,
                (id_marca,),
            )
            filas = cur.fetchall()
    finally:
        release_conn(conn)

    return [
        {
            "id_reserva": fila[0],
            "codigo_stand": fila[1],
            "area_m2": float(fila[2]),
            "precio_base": float(fila[3]),
            "estado_reserva": fila[4],
            "fecha_reserva": fila[5],
            "estado_stand": fila[6],
            "id_contrato": fila[7],
            "estado_contrato": fila[8],
        }
        for fila in filas
    ]


def obtener_todas_reservas() -> list[dict]:
    """
    Para el admin: todas las reservas con datos de marca y stand. Alimenta
    pages/admin/gestion_reservas.py.

    Retorna: lista de dicts con {id_reserva, nombre_comercial, codigo_stand,
    area_m2, precio_base, estado_reserva, estado_stand, fecha_reserva}.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id_reserva, m.nombre_comercial, s.codigo_stand,
                    s.area_m2, s.precio_base, r.estado_reserva,
                    s.estado_stand, r.fecha_reserva
                FROM reserva r
                JOIN empresa_marca m ON m.id_marca = r.id_marca
                JOIN stand s ON s.id_stand = r.id_stand
                ORDER BY r.fecha_reserva DESC
                """
            )
            filas = cur.fetchall()
    finally:
        release_conn(conn)

    return [
        {
            "id_reserva": fila[0],
            "nombre_comercial": fila[1],
            "codigo_stand": fila[2],
            "area_m2": float(fila[3]),
            "precio_base": float(fila[4]),
            "estado_reserva": fila[5],
            "estado_stand": fila[6],
            "fecha_reserva": fila[7],
        }
        for fila in filas
    ]


def cancelar_reserva(id_reserva: int) -> None:
    """
    Cancela una reserva: reserva.estado_reserva -> 'Cancelada' y
    stand.estado_stand -> 'Disponible'. Solo permitido si la reserva sigue
    en 'Pendiente' (no se cancela una ya formalizada). Alimenta el botón
    "Cancelar reserva" en pages/admin/gestion_reservas.py.

    Parámetros:
        id_reserva (int)

    Retorna:
        None.

    Lanza:
        ValueError si la reserva no existe o ya no está en 'Pendiente'.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE reserva
                SET estado_reserva = 'Cancelada'
                WHERE id_reserva = %s AND estado_reserva = 'Pendiente'
                RETURNING id_stand
                """,
                (id_reserva,),
            )
            fila = cur.fetchone()
            if fila is None:
                raise ValueError(
                    f"La reserva {id_reserva} no existe o ya no está en 'Pendiente' (no se puede cancelar)."
                )

            cur.execute("UPDATE stand SET estado_stand = 'Disponible' WHERE id_stand = %s", (fila[0],))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)


def _calcular_tomas(area_m2: float) -> int:
    """Misma fórmula que calcularTomas() en frontend/selector.js."""
    if area_m2 <= 17:
        return 1
    if area_m2 <= 26:
        return 2
    return int(area_m2 // 9)


def obtener_detalle_reserva(id_reserva: int) -> dict:
    """
    Detalle de mobiliario (sillas/mesas/paneles), tomas eléctricas y estado
    del contrato para una reserva. Alimenta el expander "Ver detalle" en
    pages/admin/gestion_reservas.py.

    Las tomas no se guardan aparte: se recalculan con _calcular_tomas() a
    partir de stand.area_m2, igual que crear_contrato_y_factura usa
    stand.precio_base — no hay una columna de área propia de la reserva en
    el schema, se asume igual a la del stand completo.

    Parámetros:
        id_reserva (int)

    Retorna:
        {"servicios": [{"nombre_servicio": str, "cantidad": int,
        "cantidad_base": int}], "tomas": int, "estado_contrato": str | None}
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sa.nombre_servicio, rsa.cantidad, rsa.cantidad_base
                FROM reserva_servicio_adicional rsa
                JOIN servicio_adicional sa ON sa.id_servicio = rsa.id_servicio
                WHERE rsa.id_reserva = %s
                ORDER BY sa.nombre_servicio
                """,
                (id_reserva,),
            )
            servicios = [
                {"nombre_servicio": fila[0], "cantidad": fila[1], "cantidad_base": fila[2]}
                for fila in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT s.area_m2, c.estado_contrato
                FROM reserva r
                JOIN stand s ON s.id_stand = r.id_stand
                LEFT JOIN contrato c ON c.id_reserva = r.id_reserva
                WHERE r.id_reserva = %s
                """,
                (id_reserva,),
            )
            fila_reserva = cur.fetchone()
    finally:
        release_conn(conn)

    area_m2 = float(fila_reserva[0]) if fila_reserva else 0.0
    estado_contrato = fila_reserva[1] if fila_reserva else None

    return {
        "servicios": servicios,
        "tomas": _calcular_tomas(area_m2),
        "estado_contrato": estado_contrato,
    }
