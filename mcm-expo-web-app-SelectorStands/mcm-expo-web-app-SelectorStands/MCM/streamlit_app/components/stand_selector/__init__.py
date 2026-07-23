import os

import streamlit.components.v1 as components

# streamlit.components.v1.declare_component(path=...) sirve ese directorio
# como estático y SIEMPRE carga su index.html como punto de entrada del
# iframe — no hay forma de elegir "admin.html" vs "index.html" con un solo
# path según un argumento. Por eso son dos declaraciones, cada una con su
# propio directorio (frontend/admin/, frontend/cliente/), cada uno con su
# propio index.html. Antes compartían un solo _component_func y
# frontend/admin.html nunca se llegaba a servir: el admin siempre veía el
# selector de cliente.
_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
_RELEASE = True  # cambiar a False para desarrollo con servidor de dev (npm start en frontend/)

if _RELEASE:
    _component_admin = components.declare_component(
        "stand_selector_admin",
        path=os.path.join(_FRONTEND_DIR, "admin"),
    )
    _component_cliente = components.declare_component(
        "stand_selector_cliente",
        path=os.path.join(_FRONTEND_DIR, "cliente"),
    )
else:
    _component_admin = components.declare_component("stand_selector_admin", url="http://localhost:3001")
    _component_cliente = components.declare_component("stand_selector_cliente", url="http://localhost:3002")


def selector_cliente(stands_data: dict, imagen_url: str = "", id_marca: int = None, key: str = None):
    """
    Renderiza el selector de stands para la marca (frontend/cliente/index.html).

    Parámetros:
        stands_data (dict): diseño de la feria con la forma que produce
            `obtener_plano_activo` / `editor_admin` (filas, columnas,
            tamanoCeldaPx, imagenPlano, zonas, stands).
        imagen_url (str, opcional): URL de la imagen de referencia a mostrar
            en la columna lateral. Si se omite, se usa
            `stands_data["imagenPlano"]` (embebida en base64).
        id_marca (int, opcional): id de la marca autenticada, se envía al
            frontend por si necesita distinguir su propia reserva.
        key (str, opcional): key único de Streamlit para este componente.

    Retorna:
        dict con accion="confirmar_reserva" y los datos de la selección
        (standId, areaM2, precioBase, personalizacion, costoExtra,
        precioTotal, tomas) la primera vez que la marca confirma una
        reserva en el modal del componente, o None si no hay una
        confirmación nueva.
    """
    return _component_cliente(
        modo="cliente",
        standsData=stands_data,
        imagenUrl=imagen_url,
        idMarca=id_marca,
        key=key,
        default=None,
    )


def editor_admin(stands_data: dict = None, key: str = None):
    """
    Renderiza el editor de plano para el administrador (frontend/admin/index.html).

    Parámetros:
        stands_data (dict, opcional): diseño existente a precargar, con la
            misma forma que retorna esta función en `diseno`. Si es None o
            no trae stands, el editor arranca vacío.
        key (str, opcional): key único de Streamlit para este componente.

    Retorna:
        dict con accion="guardar_diseno" y el diseño completo (filas,
        columnas, tamanoCeldaPx, imagenPlano, zonas, stands) cuando el
        admin hace clic en "Guardar diseño", o None si no hay cambios
        confirmados aún.
    """
    return _component_admin(
        modo="admin",
        standsData=stands_data or {},
        key=key,
        default=None,
    )
