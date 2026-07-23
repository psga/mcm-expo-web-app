from psycopg2 import errors

from db.connection import get_conn, release_conn

# El selector HTML (selector.js) espera estado en minúscula y un vocabulario
# distinto al de la máquina de estados de negocio de `stand.estado_stand`
# (Disponible/Pre_Reservado/Bloqueado/Mantenimiento). 'Pre_Reservado' se
# muestra como "reservado" (tomado, no seleccionable) y 'Bloqueado'/
# 'Mantenimiento' como "ocupado" (no disponible por ningún motivo).
_MAPA_ESTADO_STAND_A_FRONTEND = {
    "Disponible": "disponible",
    "Pre_Reservado": "reservado",
    "Bloqueado": "ocupado",
    "Mantenimiento": "ocupado",
}


def obtener_edicion_activa() -> dict | None:
    """
    Retorna la edición con estado 'Publicada' o 'En_Curso' (la más reciente
    por fecha_inicio si hubiera varias, lo que no debería ocurrir en
    operación normal).

    Retorna:
        {"id_edicion": int, "nombre": str, "fecha_inicio": date,
         "fecha_fin": date, "ubicacion": str} o None si no hay edición activa.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_edicion, nombre, fecha_inicio, fecha_fin, ubicacion
                FROM edicion_expo
                WHERE estado IN ('Publicada', 'En_Curso')
                ORDER BY fecha_inicio DESC
                LIMIT 1
                """
            )
            fila = cur.fetchone()
    finally:
        release_conn(conn)

    if fila is None:
        return None

    id_edicion, nombre, fecha_inicio, fecha_fin, ubicacion = fila
    return {
        "id_edicion": id_edicion,
        "nombre": nombre,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "ubicacion": ubicacion,
    }


def obtener_plano_activo(id_edicion: int) -> dict | None:
    """
    Trae el plano en estado 'Aprobado' más reciente para la edición dada,
    listo para pasarle a `selector_cliente` / `editor_admin`.

    Las "zonas" no existen como tabla propia (son un agrupador de UI del
    editor admin.html): se reconstruyen agrupando los stands del plano por
    (zona_nombre, color, tipo_stand, id_categoria).

    Retorna:
        dict {filas, columnas, tamanoCeldaPx, imagenPlano, zonas, stands}
        (exactamente lo que espera selector_cliente/editor_admin) o None si
        no hay plano aprobado para esa edición.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_plano, filas, columnas, tamano_celda_px, imagen_plano
                FROM plano
                WHERE id_edicion = %s AND estado_validacion = 'Aprobado'
                ORDER BY fecha_creacion DESC
                LIMIT 1
                """,
                (id_edicion,),
            )
            fila_plano = cur.fetchone()
            if fila_plano is None:
                return None

            id_plano, filas, columnas, tamano_celda_px, imagen_plano = fila_plano

            cur.execute(
                """
                SELECT
                    s.codigo_stand, s.fila_inicio, s.columna_inicio,
                    s.fila_fin, s.columna_fin, s.precio_base, s.area_m2,
                    COALESCE(s.color, c.color) AS color,
                    s.tipo_stand, s.estado_stand, s.zona_nombre, s.id_categoria,
                    c.precio_m2 AS categoria_precio_m2
                FROM stand s
                JOIN categoria_stand c ON c.id_categoria = s.id_categoria
                WHERE s.id_plano = %s
                ORDER BY s.codigo_stand
                """,
                (id_plano,),
            )
            filas_stand = cur.fetchall()
    finally:
        release_conn(conn)

    zonas_por_clave: dict[tuple, dict] = {}
    stands = []

    for (
        codigo_stand, fila_inicio, columna_inicio, fila_fin, columna_fin,
        precio_base, area_m2, color, tipo_stand, estado_stand, zona_nombre,
        id_categoria, categoria_precio_m2,
    ) in filas_stand:
        precio_m2 = float(precio_base) / float(area_m2) if area_m2 else float(categoria_precio_m2 or 0)
        clave_zona = (zona_nombre, color, tipo_stand, id_categoria)

        if clave_zona not in zonas_por_clave:
            zonas_por_clave[clave_zona] = {
                "id": f"zona-{len(zonas_por_clave) + 1:03d}",
                "nombre": zona_nombre or "Sin zona",
                "color": color,
                "precioM2": precio_m2,
                "tipo": tipo_stand,
            }

        stands.append(
            {
                "id": codigo_stand,
                "zonaId": zonas_por_clave[clave_zona]["id"],
                "filaInicio": fila_inicio,
                "columnaInicio": columna_inicio,
                "filaFin": fila_fin,
                "columnaFin": columna_fin,
                "precioM2": precio_m2,
                "color": color,
                "tipo": tipo_stand,
                "estado": _MAPA_ESTADO_STAND_A_FRONTEND.get(estado_stand, "ocupado"),
                "zona_nombre": zona_nombre,
            }
        )

    return {
        "filas": filas,
        "columnas": columnas,
        "tamanoCeldaPx": tamano_celda_px,
        "imagenPlano": imagen_plano,
        "zonas": list(zonas_por_clave.values()),
        "stands": stands,
    }


def _resolver_id_categoria(tipo_stand: str, conn) -> int:
    """
    tipo_stand: "patrocinador" | "venta"
    Mapea directamente a categoria_stand por nombre_categoria exacto.
    Asume que la DB tiene al menos estas dos filas en categoria_stand
    (ver db/seed.py):
      ('Patrocinador', prioridad 1)
      ('General', prioridad 2)
    """
    nombre = "Patrocinador" if tipo_stand == "patrocinador" else "General"
    cur = conn.cursor()
    cur.execute("SELECT id_categoria FROM categoria_stand WHERE nombre_categoria = %s", (nombre,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"categoria_stand '{nombre}' no existe en la DB. Ejecuta db/seed.py primero.")
    return row[0]


def guardar_diseno_plano(id_edicion: int, diseno: dict) -> int:
    """
    Upsert del plano + sus stands para una edición, en una transacción.

    El plano queda directamente en 'Aprobado': este prototipo no tiene un
    flujo de revisión separado, así que en cuanto el admin hace clic en
    "Guardar diseño" ya debe quedar visible para las marcas vía
    `obtener_plano_activo`. Reutiliza el único plano existente de la
    edición si lo hay (no crea versiones nuevas en cada guardado).

    Los stands se upsertean por codigo_stand (no se borra todo y se
    reinserta):
        - Si el codigo_stand ya existe en ese plano, se actualiza su
          geometría/color/zona/tipo/categoría, SIN tocar estado_stand, para
          no revertir a 'Disponible' un stand que ya tiene una reserva.
        - Si es nuevo, se inserta (estado_stand arranca en 'Disponible').
        - Si un codigo_stand que existía en el plano ya no viene en
          `diseno` (el admin lo borró en el editor), se elimina. Si ese
          stand ya tiene una reserva asociada, la FK lo bloquea y se
          relanza como ValueError en vez de tumbar la transacción con un
          error de psycopg2 crudo.

    Parámetros:
        id_edicion (int)
        diseno (dict): {filas, columnas, tamanoCeldaPx, imagenPlano, zonas, stands}
            tal como lo entrega el componente `editor_admin` en
            resultado["diseno"].

    Retorna:
        id_plano (el existente si se actualizó, uno nuevo si se creó).

    Lanza:
        ValueError si se intenta eliminar (por no venir ya en el diseño) un
        stand que ya tiene una reserva.
    """
    zonas_por_id = {zona["id"]: zona for zona in diseno.get("zonas", [])}

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_plano FROM plano
                WHERE id_edicion = %s
                ORDER BY fecha_creacion DESC
                LIMIT 1
                """,
                (id_edicion,),
            )
            fila_existente = cur.fetchone()

            if fila_existente:
                id_plano = fila_existente[0]
                cur.execute(
                    """
                    UPDATE plano
                    SET filas = %s, columnas = %s, tamano_celda_px = %s,
                        imagen_plano = %s, estado_validacion = 'Aprobado'
                    WHERE id_plano = %s
                    """,
                    (diseno["filas"], diseno["columnas"], diseno["tamanoCeldaPx"], diseno.get("imagenPlano"), id_plano),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO plano (
                        id_edicion, version_plano, estado_validacion,
                        filas, columnas, tamano_celda_px, imagen_plano
                    )
                    VALUES (%s, %s, 'Aprobado', %s, %s, %s, %s)
                    RETURNING id_plano
                    """,
                    (id_edicion, "1.0", diseno["filas"], diseno["columnas"], diseno["tamanoCeldaPx"], diseno.get("imagenPlano")),
                )
                id_plano = cur.fetchone()[0]

            categorias_cache: dict[str, int] = {}
            codigos_incoming = []

            for stand in diseno.get("stands", []):
                zona = zonas_por_id.get(stand.get("zonaId"))
                tipo = stand.get("tipo") or (zona["tipo"] if zona else "venta")

                if tipo not in categorias_cache:
                    categorias_cache[tipo] = _resolver_id_categoria(tipo, conn)
                id_categoria = categorias_cache[tipo]

                codigo_stand = stand["id"]
                codigos_incoming.append(codigo_stand)

                fila_inicio = int(stand["filaInicio"])
                columna_inicio = int(stand["columnaInicio"])
                fila_fin = int(stand["filaFin"])
                columna_fin = int(stand["columnaFin"])
                area_m2 = (fila_fin - fila_inicio + 1) * (columna_fin - columna_inicio + 1)
                precio_m2 = float(stand.get("precioM2") or (zona["precioM2"] if zona else 0) or 0)
                precio_base = precio_m2 * area_m2
                color = stand.get("color") or (zona["color"] if zona else None)
                zona_nombre = zona["nombre"] if zona else None

                cur.execute(
                    """
                    UPDATE stand
                    SET id_categoria = %s, area_m2 = %s, precio_base = %s,
                        fila_inicio = %s, columna_inicio = %s,
                        fila_fin = %s, columna_fin = %s,
                        color = %s, zona_nombre = %s, tipo_stand = %s
                    WHERE id_plano = %s AND codigo_stand = %s
                    """,
                    (
                        id_categoria, area_m2, precio_base,
                        fila_inicio, columna_inicio, fila_fin, columna_fin,
                        color, zona_nombre, tipo,
                        id_plano, codigo_stand,
                    ),
                )

                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO stand (
                            id_plano, id_categoria, codigo_stand, area_m2, precio_base,
                            fila_inicio, columna_inicio, fila_fin, columna_fin,
                            color, zona_nombre, tipo_stand
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            id_plano, id_categoria, codigo_stand, area_m2, precio_base,
                            fila_inicio, columna_inicio, fila_fin, columna_fin,
                            color, zona_nombre, tipo,
                        ),
                    )

            if codigos_incoming:
                cur.execute(
                    "DELETE FROM stand WHERE id_plano = %s AND codigo_stand != ALL(%s)",
                    (id_plano, codigos_incoming),
                )
            else:
                cur.execute("DELETE FROM stand WHERE id_plano = %s", (id_plano,))

        conn.commit()
    except errors.ForeignKeyViolation:
        conn.rollback()
        raise ValueError(
            "No se pudo guardar: al menos un stand que quitaste del editor ya tiene una reserva asociada."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)

    return id_plano
