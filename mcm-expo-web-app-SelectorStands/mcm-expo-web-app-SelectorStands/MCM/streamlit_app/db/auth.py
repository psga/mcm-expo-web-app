import bcrypt

from db.connection import get_conn, release_conn

# Credenciales del admin MCM, hardcodeadas para el prototipo académico.
# TODO(producción): mover el admin a una tabla real (p. ej. usuario_interno
# con password_hash + bcrypt, igual que empresa_marca) en vez de constantes
# hardcodeadas en el código fuente.
ADMIN_EMAIL = "admin@mcm.com"
ADMIN_PASSWORD = "mcm2026admin"


def login_admin(email: str, password: str) -> bool:
    """Verifica credenciales hardcodeadas del admin MCM."""
    return email.strip().lower() == ADMIN_EMAIL and password == ADMIN_PASSWORD


def login_marca(email: str, password: str) -> dict | None:
    """
    Busca en empresa_marca por correo_corporativo y verifica password_hash
    con bcrypt.

    Parámetros:
        email (str): correo_corporativo ingresado en el login.
        password (str): contraseña en texto plano ingresada en el login.

    Retorna:
        {"id_marca": int, "nombre_comercial": str, "nit": str,
        "correo_corporativo": str, "telefono": str} si las credenciales son
        válidas, o None si el correo no existe o la contraseña no coincide.
        Incluye nit/correo/telefono (no solo el id) porque
        utils.state.iniciar_sesion_marca() los necesita para poblar
        st.session_state.marca, que usa flujo_marca._paso_contrato().
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_marca, nombre_comercial, nit, correo_corporativo, telefono, password_hash
                FROM empresa_marca
                WHERE correo_corporativo = %s
                """,
                (email.strip().lower(),),
            )
            fila = cur.fetchone()
    finally:
        release_conn(conn)

    if fila is None:
        return None

    id_marca, nombre_comercial, nit, correo_corporativo, telefono, password_hash = fila
    if not password_hash or not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
        return None

    return {
        "id_marca": id_marca,
        "nombre_comercial": nombre_comercial,
        "nit": nit,
        "correo_corporativo": correo_corporativo,
        "telefono": telefono,
    }


def registrar_marca(datos: dict) -> int:
    """
    Inserta en empresa_marca + expositor_contacto en una transacción.

    Parámetros:
        datos (dict): claves nit, razon_social, nombre_comercial,
            sector_economico, correo_corporativo, telefono, password,
            contacto_nombre, contacto_cargo, contacto_telefono.

    Retorna:
        id_marca del registro creado.

    Lanza:
        ValueError si el NIT o el correo corporativo ya existen.
    """
    password_hash = bcrypt.hashpw(datos["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    correo = datos["correo_corporativo"].strip().lower()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM empresa_marca WHERE nit = %s OR correo_corporativo = %s",
                (datos["nit"], correo),
            )
            if cur.fetchone() is not None:
                raise ValueError("Ya existe una marca registrada con ese NIT o correo corporativo.")

            cur.execute(
                """
                INSERT INTO empresa_marca (
                    nit, razon_social, nombre_comercial, sector_economico,
                    correo_corporativo, telefono, password_hash
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_marca
                """,
                (
                    datos["nit"],
                    datos["razon_social"],
                    datos["nombre_comercial"],
                    datos.get("sector_economico"),
                    correo,
                    datos["telefono"],
                    password_hash,
                ),
            )
            id_marca = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO expositor_contacto (
                    id_marca, nombre_completo, cargo, correo, telefono, es_principal
                )
                VALUES (%s, %s, %s, %s, %s, TRUE)
                """,
                (
                    id_marca,
                    datos["contacto_nombre"],
                    datos.get("contacto_cargo"),
                    correo,
                    datos["contacto_telefono"],
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)

    return id_marca
