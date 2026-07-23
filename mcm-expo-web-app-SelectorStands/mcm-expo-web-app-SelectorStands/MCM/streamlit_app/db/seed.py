"""
Ejecutar UNA vez en una DB limpia antes de probar la aplicación.
Inserta los datos mínimos de referencia que el sistema asume existentes:
categorías de stand (usadas por plano_queries._resolver_id_categoria),
servicios adicionales (usados por reserva_queries.crear_reserva) y una
edición de feria publicada (usada por plano_queries.obtener_edicion_activa).

Uso: desde streamlit_app/, `python -m db.seed` (toma las credenciales de
.streamlit/secrets.toml, igual que la app).
"""

import psycopg2
import streamlit as st

SEED_SQL = """
INSERT INTO categoria_stand (nombre_categoria, prioridad_seleccion, descripcion)
VALUES
    ('Patrocinador', 1, 'Marcas patrocinadoras principales del evento'),
    ('Apoyo',        2, 'Marcas de apoyo y copatrocinio'),
    ('General',      3, 'Expositores generales')
ON CONFLICT (nombre_categoria) DO NOTHING;

INSERT INTO servicio_adicional (nombre_servicio, precio_unitario)
VALUES
    ('Silla adicional',    25000),
    ('Mesa adicional',     45000),
    ('Panel adicional',    60000)
ON CONFLICT DO NOTHING;

INSERT INTO edicion_expo (nombre, fecha_inicio, fecha_fin, estado)
VALUES ('Expo Maratón Medellín 2026', '2026-09-04', '2026-09-06', 'Publicada')
ON CONFLICT DO NOTHING;
"""


def ejecutar_seed() -> None:
    conn = psycopg2.connect(
        host=st.secrets["db"]["host"],
        port=st.secrets["db"]["port"],
        dbname=st.secrets["db"]["dbname"],
        user=st.secrets["db"]["user"],
        password=st.secrets["db"]["password"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute(SEED_SQL)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    ejecutar_seed()
    print("Seed aplicado.")
