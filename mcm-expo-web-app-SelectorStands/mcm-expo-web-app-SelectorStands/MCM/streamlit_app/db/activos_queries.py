from db.connection import get_conn, release_conn


def subir_activo_marca(id_marca: int, tipo_activo: str, url_archivo: str) -> int:
    """
    Registra un activo publicitario de la marca (logo, manual de identidad,
    etc.) en estado 'Pendiente' de validación. Alimenta
    flujo_marca._seccion_activos_marca() (HU9).

    Parámetros:
        id_marca (int)
        tipo_activo (str): p. ej. "Logo_Vectorial" | "Manual_Marca".
        url_archivo (str): ubicación del archivo ya subido.

    Retorna:
        id_activo del registro creado.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO activo_publicitario (id_marca, tipo_activo, url_archivo, estado_validacion)
                VALUES (%s, %s, %s, 'Pendiente')
                RETURNING id_activo
                """,
                (id_marca, tipo_activo, url_archivo),
            )
            id_activo = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)

    return id_activo


def obtener_activos_marca(id_marca: int) -> list[dict]:
    """
    Lista los activos publicitarios ya cargados por una marca, más
    recientes primero.

    Retorna: lista de dicts con {id_activo, tipo_activo, url_archivo,
    estado_validacion, fecha_carga}.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_activo, tipo_activo, url_archivo, estado_validacion, fecha_carga
                FROM activo_publicitario
                WHERE id_marca = %s
                ORDER BY fecha_carga DESC
                """,
                (id_marca,),
            )
            filas = cur.fetchall()
    finally:
        release_conn(conn)

    return [
        {
            "id_activo": fila[0],
            "tipo_activo": fila[1],
            "url_archivo": fila[2],
            "estado_validacion": fila[3],
            "fecha_carga": fila[4],
        }
        for fila in filas
    ]


def obtener_redes_sociales(id_marca: int) -> dict:
    """
    Trae los datos de redes sociales del perfil de una marca, para
    precargar el formulario.

    Retorna: {"instagram": str | None, "facebook": str | None,
    "sitio_web": str | None}.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT instagram, facebook, sitio_web FROM empresa_marca WHERE id_marca = %s",
                (id_marca,),
            )
            fila = cur.fetchone()
    finally:
        release_conn(conn)

    if fila is None:
        return {"instagram": None, "facebook": None, "sitio_web": None}

    return {"instagram": fila[0], "facebook": fila[1], "sitio_web": fila[2]}


def actualizar_redes_sociales(id_marca: int, instagram: str | None, facebook: str | None, sitio_web: str | None) -> None:
    """Actualiza los datos de redes sociales del perfil de una marca."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE empresa_marca
                SET instagram = %s, facebook = %s, sitio_web = %s
                WHERE id_marca = %s
                """,
                (instagram or None, facebook or None, sitio_web or None, id_marca),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)
