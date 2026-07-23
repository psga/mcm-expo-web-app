import psycopg2
import streamlit as st
from psycopg2 import pool


@st.cache_resource
def get_pool():
    try:
        return psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=st.secrets["db"]["host"],
            port=st.secrets["db"]["port"],
            dbname=st.secrets["db"]["dbname"],
            user=st.secrets["db"]["user"],
            password=st.secrets["db"]["password"],
        )
    except UnicodeDecodeError as error:
        # En Windows, si Postgres reporta errores en español (autenticación
        # fallida, DB inexistente, etc.), libpq entrega ese texto en
        # Latin-1/CP1252, no en UTF-8 — y psycopg2 revienta con
        # UnicodeDecodeError (que ya es un ValueError) al intentar
        # decodificarlo, tapando el error real con un mensaje sin
        # contenido útil. Lo recuperamos a mano (Latin-1 nunca falla, cada
        # byte 0-255 mapea a un carácter) y seguimos lanzando ValueError
        # para que el `except ValueError` de la página de registro (y
        # cualquier otro) lo siga mostrando como un error limpio, ahora con
        # el mensaje real.
        mensaje = error.object.decode("latin-1", errors="replace").strip()
        raise ValueError(
            f"No se pudo conectar a PostgreSQL: {mensaje}\n"
            "Revisa host/puerto/dbname/user/password en .streamlit/secrets.toml "
            "(y que ese usuario/base de datos existan en tu Postgres local)."
        ) from error


def get_conn():
    return get_pool().getconn()


def release_conn(conn):
    get_pool().putconn(conn)
