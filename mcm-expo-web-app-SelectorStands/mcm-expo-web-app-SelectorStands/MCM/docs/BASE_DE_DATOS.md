# Configuración de PostgreSQL

## 1. Instalar PostgreSQL

- **Windows**: instalador de [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
  (EDB). Durante la instalación te pide una contraseña para el superusuario
  `postgres` — anótala, la necesitas en el paso 2.
- **macOS**: `brew install postgresql@16 && brew services start postgresql@16`
- **Linux (Debian/Ubuntu)**: `sudo apt install postgresql && sudo systemctl start postgresql`

Confirma que el servicio está corriendo y escuchando en el puerto 5432
(el default).

## 2. Crear el rol y la base de datos del proyecto

Conéctate como superusuario y crea un rol y una base de datos dedicados
para la app (no uses el rol `postgres` directamente):

```sql
-- Desde psql, conectado como postgres:
CREATE ROLE mcm_user WITH LOGIN PASSWORD 'mcm2026db';
CREATE DATABASE mcm_expo OWNER mcm_user;
```

Puedes usar otro usuario/contraseña — solo asegúrate de que coincidan con
lo que pongas en `secrets.toml` en el paso 4.

## 3. Cargar el esquema

Con el rol y la base ya creados, corre el script de esquema **conectado a
la base `mcm_expo`** (no a `postgres`):

```
psql -U mcm_user -d mcm_expo -h localhost -f MCM/db/schema.sql
```

Esto crea las 13 tablas del modelo (`edicion_expo`, `categoria_stand`,
`empresa_marca`, `expositor_contacto`, `plano`, `stand`, `reserva`,
`contrato`, `factura`, `pago`, `servicio_adicional`,
`reserva_servicio_adicional`, `activo_publicitario`) con sus columnas,
`CHECK` constraints y claves foráneas.

Luego carga el trigger que formaliza automáticamente una reserva cuando su
factura queda pagada en su totalidad:

```
psql -U mcm_user -d mcm_expo -h localhost -f MCM/db/triggers/confirmar_pago.sql
```

## 4. Configurar las credenciales de la app

Copia el archivo de ejemplo y complétalo con tus credenciales reales:

```
cd MCM/streamlit_app/.streamlit
cp secrets.toml.example secrets.toml
```

`secrets.toml` (con los valores del paso 2):

```toml
[db]
host = "localhost"
port = 5432
dbname = "mcm_expo"
user = "mcm_user"
password = "mcm2026db"
```

**Este archivo no se debe subir al repositorio** (contiene la contraseña
real de la base de datos) — ya está listado en `.gitignore`.

## 5. Sembrar los datos mínimos de referencia

Antes de poder registrar marcas o guardar un plano, la app necesita
categorías de stand, servicios adicionales (sillas/mesas/paneles) y una
edición de feria publicada. Desde `MCM/streamlit_app/`:

```
python -m db.seed
```

Esto inserta (con `ON CONFLICT DO NOTHING`, así que es seguro correrlo más
de una vez):

- `categoria_stand`: Patrocinador, Apoyo, General.
- `servicio_adicional`: Silla adicional, Mesa adicional, Panel adicional.
- `edicion_expo`: "Expo Maratón Medellín 2026", estado `Publicada`.

## 6. (Opcional) Cargar un plano de ejemplo con 177 stands

Para no tener que dibujar el plano a mano antes de probar la app, hay un
plano de demostración ya armado (el mismo que se usó para el diseño
visual) que se puede importar directo a la base de datos:

```
python -m db.importar_diseno_demo
```

Esto usa la misma función (`guardar_diseno_plano`) que llama el botón
"Guardar diseño" del admin, así que el resultado es idéntico a si un admin
hubiera dibujado ese plano a mano. Si prefieres empezar desde cero, sáltate
este paso y diseña el plano desde la pestaña "Diseño del plano" del admin.

## Troubleshooting

### `psycopg2.OperationalError` / `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf3...`

Este es el error más confuso que te vas a encontrar y **no es un problema
de codificación real**. En Windows, si el sistema operativo está en
español, PostgreSQL devuelve sus mensajes de error (contraseña incorrecta,
base de datos inexistente, etc.) en español codificados en Latin-1/CP1252,
no en UTF-8 — y la librería `psycopg2` revienta con `UnicodeDecodeError` al
intentar leer ese mensaje, tapando el error real.

La app ya maneja esto (`db/connection.py` decodifica el mensaje con
Latin-1 y lo vuelve a lanzar como un error legible), así que si te
encuentras con esto de verdad, el mensaje que va a mostrar la app te dice
la causa real — normalmente:

- **Usuario/contraseña incorrectos**: revisa que `secrets.toml` tenga
  exactamente el usuario y contraseña que creaste en el paso 2.
- **La base de datos no existe**: revisa que `dbname` en `secrets.toml` sea
  `mcm_expo` y que la creaste con `CREATE DATABASE`.
- **PostgreSQL no está corriendo** o no escucha en el host/puerto
  configurado: confirma el servicio y que el puerto 5432 esté libre.

### `relation "stand" does not exist` (o cualquier tabla)

El esquema no se cargó. Repite el paso 3 y confirma que no haya errores en
la salida de `psql`.

### `categoria_stand 'General' no existe en la DB`

Te faltó el paso 5 (`python -m db.seed`) — la app resuelve la categoría de
cada stand por nombre exacto contra esa tabla.

### Quiero empezar de cero (borrar todo)

```sql
DROP DATABASE mcm_expo;
CREATE DATABASE mcm_expo OWNER mcm_user;
```

Y repite desde el paso 3.
