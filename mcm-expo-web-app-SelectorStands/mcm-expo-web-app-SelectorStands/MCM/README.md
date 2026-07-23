# MCM Expo — Sistema de Gestión de Stands

Prototipo académico de una plataforma para que **MCM** administre el plano de
stands de una feria (EXPO Maratón Medellín) y las **marcas expositoras**
puedan registrarse, seleccionar su espacio, firmar, pagar y gestionar sus
activos de marca — todo en una sola aplicación Streamlit conectada a
PostgreSQL.

## Índice

- [Qué incluye](#qué-incluye)
- [Arquitectura](#arquitectura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Puesta en marcha rápida](#puesta-en-marcha-rápida)
- [Credenciales de prueba](#credenciales-de-prueba)
- [Funcionalidades implementadas](#funcionalidades-implementadas)
- [Limitaciones conocidas](#limitaciones-conocidas--pendientes-para-producción)

## Qué incluye

Dos roles, una sola app, sin cambiar de página (todo corre con
`st.session_state` + `st.rerun()`, sin `st.switch_page`):

- **Administrador** — diseña el plano de stands con un editor visual
  (arrastrar rectángulos sobre una grilla), gestiona reservas y verifica
  pagos.
- **Marca (expositor)** — se registra, selecciona su stand en el mismo
  plano visual, genera su contrato, firma, paga, y gestiona sus activos de
  marca (logos, manual de identidad, redes sociales) y documentación
  técnica del evento.

## Arquitectura

```
┌─────────────────────────────┐
│   app.py (Streamlit)        │  login, routing por rol, sidebar admin
│   flujo_marca.py            │  todo el proceso de la marca, una sola página
└───────────────┬─────────────┘
                │
    ┌───────────┴────────────┐
    │  Custom component       │  selector de stands (HTML/JS embebido en
    │  stand_selector/        │  un iframe): admin.html dibuja, index.html
    │  frontend/{admin,       │  (cliente) selecciona y reserva
    │  cliente}/              │
    └───────────┬─────────────┘
                │
    ┌───────────┴────────────┐
    │  db/*.py (psycopg2)     │  toda la persistencia pasa por acá
    └───────────┬────────────┘
                │
        PostgreSQL (mcm_expo)
```

El selector de stands es un [Streamlit custom component](https://docs.streamlit.io/develop/concepts/custom-components)
estático (sin build de Node/React): dos directorios (`frontend/admin/` y
`frontend/cliente/`), cada uno con su propio `index.html`, porque
`declare_component` siempre sirve el `index.html` de la carpeta que se le
indique — no hay forma de elegir el archivo según un argumento.

## Estructura del proyecto

```
MCM/
├── db/
│   ├── schema.sql                # Esquema completo (13 tablas)
│   ├── triggers/confirmar_pago.sql   # Formaliza la reserva al pagar
│   └── queries/reserva_concurrencia.sql  # Referencia: bloqueo pesimista
├── docs/
│   ├── INSTALACION.md            # Cómo instalar Python y dependencias
│   └── BASE_DE_DATOS.md          # Cómo instalar y configurar PostgreSQL
└── streamlit_app/
    ├── app.py                    # Entry point: login + routing por rol
    ├── flujo_marca.py            # Todo el proceso de la marca (una página)
    ├── requirements.txt
    ├── .streamlit/
    │   ├── config.toml           # Desactiva la navegación automática de Streamlit
    │   └── secrets.toml          # Credenciales de la DB (NO se sube al repo)
    ├── components/stand_selector/
    │   ├── __init__.py           # Wrappers Python: selector_cliente(), editor_admin()
    │   └── frontend/
    │       ├── admin/            # Editor visual del plano (admin)
    │       └── cliente/          # Selector de stands (marca)
    ├── db/                       # Todas las queries a Postgres (psycopg2)
    │   ├── connection.py         # Pool de conexiones
    │   ├── auth.py               # Login admin/marca, registro (bcrypt)
    │   ├── plano_queries.py      # Guardar/leer el diseño del plano
    │   ├── reserva_queries.py    # Reservas, formalización, contratos
    │   ├── pago_queries.py       # Facturas y pagos
    │   ├── activos_queries.py    # Logos, manuales, redes sociales (HU9)
    │   ├── seed.py               # Datos mínimos de referencia
    │   └── importar_diseno_demo.py  # Importa un plano de ejemplo (177 stands)
    ├── pages/admin/              # Diseño del plano, reservas, pagos (admin)
    └── utils/                    # Sidebar, estilos, session_state, formatters
```

## Puesta en marcha rápida

1. **Python y dependencias** → ver [`docs/INSTALACION.md`](docs/INSTALACION.md).
2. **PostgreSQL** → ver [`docs/BASE_DE_DATOS.md`](docs/BASE_DE_DATOS.md).
3. Desde `streamlit_app/`:
   ```
   streamlit run app.py
   ```
4. Abre `http://localhost:8501` en el navegador.

## Credenciales de prueba

| Rol | Usuario | Contraseña |
|---|---|---|
| Admin | `admin@mcm.com` | `mcm2026admin` |
| Marca | (usa "Registrarme" en el login) | — |

El admin está hardcodeado en `db/auth.py` a propósito para este prototipo
académico — hay un `TODO(producción)` en ese archivo señalando que debe
migrarse a una tabla real antes de un despliegue de verdad.

## Funcionalidades implementadas

- Registro de marca (NIT validado, contraseña con bcrypt) e inicio de sesión.
- Diseño visual del plano por el admin (zonas, precios por m², stands
  arrastrables) con persistencia real en Postgres.
- Selección de stand por la marca sobre el mismo plano, con personalización
  de mobiliario (sillas/mesas/paneles) y cálculo de tomas eléctricas.
- Generación de contrato con IVA (19%) y verificación de firma (simulada).
- Conciliación de pagos: registro de pago por la marca → verificación por
  el admin → **trigger de base de datos** que formaliza la reserva y
  bloquea el stand automáticamente al confirmarse el pago total.
- Gestión de reservas por el admin (cancelar, ver detalle).
- **HU9 — Activos de marca**: carga de logo en formato vectorial (con
  validación de formato/peso) y manual de identidad, más datos de redes
  sociales — habilitado solo tras firmar el contrato.
- **HU10 — Centro de documentación**: descarga del manual del expositor y
  cronograma personalizado — habilitado solo cuando la reserva está
  formalizada (contrato + pago), según RN011.

## Limitaciones conocidas / pendientes para producción

- **Admin hardcodeado**: ver TODO en `db/auth.py`.
- **Sin storage real de archivos**: los uploads (logos, manuales,
  comprobantes de pago, firma) guardan solo una URL simulada
  (`/activos/...`, `/comprobantes/...`); en producción hay que subirlos a
  S3/GCS/equivalente y guardar esa URL real. Ver los `TODO(producción)` en
  `db/activos_queries.py` y `pages/admin/gestion_pagos.py`.
- **Sin contrafirma del admin**: `contrato.firmado_mcm` nunca se pone en
  `TRUE` desde la UI — no hay todavía una pantalla de contrafirma para el
  admin, así que `contrato.estado_contrato` nunca llega solo a `'Firmado'`.
- **`categoria_stand` vinculada por convención de nombre**: el admin dibuja
  "zonas" (tipo `venta`/`patrocinador`) que se resuelven contra
  `categoria_stand.nombre_categoria = 'General'/'Patrocinador'` por nombre
  exacto (ver `_resolver_id_categoria` en `db/plano_queries.py`). Si el
  catálogo de categorías cambia de nombres, hay que ajustar esa función.
