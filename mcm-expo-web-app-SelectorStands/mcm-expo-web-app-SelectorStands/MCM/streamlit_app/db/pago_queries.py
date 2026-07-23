from db.connection import get_conn, release_conn

# NOTA: estas consultas asumen que ya existe un contrato + factura para la
# reserva (id_contrato -> id_factura). Generar el contrato y la factura
# tras crear_reserva() no está cubierto todavía por ningún módulo — falta
# decidir si eso lo dispara el admin manualmente (p. ej. desde
# gestion_reservas.py) o un proceso aparte.


def obtener_facturas_marca(id_marca: int) -> list[dict]:
    """
    Facturas de una marca con su monto total, lo pagado (verificado) hasta
    ahora y el saldo pendiente. Alimenta flujo_marca._seccion_mis_pagos().

    Retorna: lista de dicts con {id_factura, id_contrato, id_reserva,
    codigo_stand, monto_total, monto_pagado, saldo, estado_factura,
    numero_factura_dian}.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    f.id_factura, f.id_contrato, ct.id_reserva, s.codigo_stand,
                    f.monto_total, f.estado_factura, f.numero_factura_dian,
                    COALESCE(SUM(p.monto_pagado) FILTER (WHERE p.estado_pago = 'Verificado'), 0) AS monto_pagado
                FROM factura f
                JOIN contrato ct ON ct.id_contrato = f.id_contrato
                JOIN reserva r ON r.id_reserva = ct.id_reserva
                JOIN stand s ON s.id_stand = r.id_stand
                LEFT JOIN pago p ON p.id_factura = f.id_factura
                WHERE r.id_marca = %s
                GROUP BY f.id_factura, ct.id_reserva, s.codigo_stand
                ORDER BY f.fecha_emision DESC
                """,
                (id_marca,),
            )
            filas = cur.fetchall()
    finally:
        release_conn(conn)

    resultado = []
    for fila in filas:
        monto_total = float(fila[4])
        monto_pagado = float(fila[7])
        resultado.append(
            {
                "id_factura": fila[0],
                "id_contrato": fila[1],
                "id_reserva": fila[2],
                "codigo_stand": fila[3],
                "monto_total": monto_total,
                "estado_factura": fila[5],
                "numero_factura_dian": fila[6],
                "monto_pagado": monto_pagado,
                "saldo": monto_total - monto_pagado,
            }
        )
    return resultado


def registrar_pago(id_factura: int, datos_pago: dict) -> int:
    """
    Inserta un pago para una factura, en estado 'En_Verificacion'.

    Parámetros:
        id_factura (int)
        datos_pago (dict): {monto_pagado, metodo_pago, numero_referencia,
            url_comprobante}. metodo_pago debe ser uno de 'Transferencia' |
            'Pasarela_PSE' | 'Tarjeta_Credito'. url_comprobante es la URL
            del comprobante ya subido (el upload en sí lo maneja la página,
            esta función solo guarda la URL resultante).

    Notas:
        No cambia el estado de la factura ni del stand: eso lo hace el
        admin al verificar el pago (ver `verificar_pago`).

    Retorna:
        id_pago.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pago (id_factura, monto_pagado, metodo_pago, numero_referencia, url_comprobante)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_pago
                """,
                (
                    id_factura,
                    datos_pago["monto_pagado"],
                    datos_pago["metodo_pago"],
                    datos_pago["numero_referencia"],
                    datos_pago.get("url_comprobante"),
                ),
            )
            id_pago = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)

    return id_pago


def verificar_pago(id_pago: int) -> None:
    """
    Marca un pago como 'Verificado' y recalcula el estado de su factura:
    'Pagada_Parcial' si lo verificado todavía no cubre el monto_total, o
    'Pagada_Total' si lo cubre o supera. Pasar la factura a 'Pagada_Total'
    dispara trg_confirmar_pago_stand (db/triggers/confirmar_pago.sql), que
    bloquea el stand y formaliza la reserva automáticamente en la DB.

    Parámetros:
        id_pago (int)

    Retorna:
        None.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE pago SET estado_pago = 'Verificado' WHERE id_pago = %s", (id_pago,))

            cur.execute(
                """
                SELECT f.id_factura, f.monto_total,
                       COALESCE(SUM(p.monto_pagado) FILTER (WHERE p.estado_pago = 'Verificado'), 0) AS pagado
                FROM pago pago_ref
                JOIN factura f ON f.id_factura = pago_ref.id_factura
                LEFT JOIN pago p ON p.id_factura = f.id_factura
                WHERE pago_ref.id_pago = %s
                GROUP BY f.id_factura, f.monto_total
                """,
                (id_pago,),
            )
            id_factura, monto_total, pagado = cur.fetchone()

            nuevo_estado = "Pagada_Total" if pagado >= monto_total else "Pagada_Parcial"
            cur.execute("UPDATE factura SET estado_factura = %s WHERE id_factura = %s", (nuevo_estado, id_factura))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)


def obtener_todos_pagos() -> list[dict]:
    """
    Para el admin: todas las reservas con su estado financiero, más los
    pagos en 'En_Verificacion' agrupados por factura. Alimenta
    pages/admin/gestion_pagos.py (tabla + botón "Verificar pago").

    Retorna: lista de dicts con {id_reserva, nombre_comercial, codigo_stand,
    area_m2, id_factura, monto_total, monto_pagado, saldo, estado_factura,
    pagos_pendientes: [{id_pago, monto_pagado, metodo_pago,
    numero_referencia, fecha_pago}]}.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id_reserva, m.nombre_comercial, s.codigo_stand, s.area_m2,
                    f.id_factura, f.monto_total, f.estado_factura,
                    COALESCE(SUM(p.monto_pagado) FILTER (WHERE p.estado_pago = 'Verificado'), 0) AS monto_pagado
                FROM reserva r
                JOIN empresa_marca m ON m.id_marca = r.id_marca
                JOIN stand s ON s.id_stand = r.id_stand
                LEFT JOIN contrato ct ON ct.id_reserva = r.id_reserva
                LEFT JOIN factura f ON f.id_contrato = ct.id_contrato
                LEFT JOIN pago p ON p.id_factura = f.id_factura
                GROUP BY r.id_reserva, m.nombre_comercial, s.codigo_stand, s.area_m2, f.id_factura, f.monto_total, f.estado_factura
                ORDER BY r.fecha_reserva DESC
                """
            )
            filas = cur.fetchall()

            cur.execute(
                """
                SELECT id_pago, id_factura, monto_pagado, metodo_pago, numero_referencia, fecha_pago
                FROM pago
                WHERE estado_pago = 'En_Verificacion'
                ORDER BY fecha_pago
                """
            )
            filas_pendientes = cur.fetchall()
    finally:
        release_conn(conn)

    pendientes_por_factura: dict[int, list[dict]] = {}
    for id_pago, id_factura, monto_pagado, metodo_pago, numero_referencia, fecha_pago in filas_pendientes:
        pendientes_por_factura.setdefault(id_factura, []).append(
            {
                "id_pago": id_pago,
                "monto_pagado": float(monto_pagado),
                "metodo_pago": metodo_pago,
                "numero_referencia": numero_referencia,
                "fecha_pago": fecha_pago,
            }
        )

    resultado = []
    for fila in filas:
        id_reserva, nombre_comercial, codigo_stand, area_m2, id_factura, monto_total, estado_factura, monto_pagado = fila
        monto_total = float(monto_total) if monto_total is not None else 0.0
        monto_pagado = float(monto_pagado)
        resultado.append(
            {
                "id_reserva": id_reserva,
                "nombre_comercial": nombre_comercial,
                "codigo_stand": codigo_stand,
                "area_m2": float(area_m2),
                "id_factura": id_factura,
                "monto_total": monto_total,
                "monto_pagado": monto_pagado,
                "saldo": monto_total - monto_pagado,
                "estado_factura": estado_factura,
                "pagos_pendientes": pendientes_por_factura.get(id_factura, []),
            }
        )
    return resultado
