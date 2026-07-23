"""
Importa el diseño de demo (frontend/cliente/data/stands.json, 177 stands en
4 zonas) directo a la base de datos, usando el mismo guardar_diseno_plano()
que llama el botón "Guardar diseño" del admin. Sirve para tener un plano de
prueba real sin tener que dibujar todo a mano en el editor.

Uso: desde streamlit_app/, `python -m db.importar_diseno_demo`
(usa las credenciales de .streamlit/secrets.toml, igual que la app).
"""

import json
import os

from db.plano_queries import guardar_diseno_plano, obtener_edicion_activa

_RUTA_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "components",
    "stand_selector",
    "frontend",
    "cliente",
    "data",
    "stands.json",
)


def importar() -> None:
    edicion = obtener_edicion_activa()
    if not edicion:
        raise RuntimeError(
            "No hay una edición activa (estado 'Publicada' o 'En_Curso'). "
            "Corre `python -m db.seed` primero."
        )

    with open(_RUTA_JSON, encoding="utf-8") as archivo:
        diseno = json.load(archivo)

    id_plano = guardar_diseno_plano(edicion["id_edicion"], diseno)
    print(f"Plano importado: id_plano={id_plano}, stands={len(diseno.get('stands', []))}")


if __name__ == "__main__":
    importar()
