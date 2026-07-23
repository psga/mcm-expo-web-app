# Instalación de requisitos (Python + dependencias)

## 1. Requisitos previos

- **Python 3.10 o superior** (el código usa sintaxis `str | None`, que
  requiere 3.10+). Se probó con Python 3.12.
- **PostgreSQL** ya instalado y corriendo — ver [`BASE_DE_DATOS.md`](BASE_DE_DATOS.md)
  antes de continuar si todavía no lo tienes.
- pip (viene con Python).

### Windows: si tienes más de un Python instalado

Si tu equipo tiene varias versiones de Python (por ejemplo una para otro
curso/proyecto), confirma cuál vas a usar antes de instalar nada, porque
`pip install` solo instala en el intérprete que invocaste:

```
py -0p
```

Esto lista todas las instalaciones y marca con `*` la que usa `py` por
defecto. Si vas a usar una específica, invócala con `py -3.12` (o la
versión que corresponda) en vez de `python` en todos los comandos de abajo.
Este detalle causó justamente el error `ModuleNotFoundError: No module
named 'bcrypt'` durante el desarrollo: `streamlit` estaba instalado en un
Python, pero `pip install bcrypt` se corrió en otro.

## 2. Crear un entorno virtual (recomendado)

No es obligatorio, pero evita mezclar las dependencias de este proyecto con
las de otros:

```
cd MCM/streamlit_app
python -m venv .venv
```

Activarlo:

- **Windows (cmd/PowerShell):** `.venv\Scripts\activate`
- **Windows (Git Bash):** `source .venv/Scripts/activate`
- **macOS/Linux:** `source .venv/bin/activate`

## 3. Instalar las dependencias

Desde `MCM/streamlit_app/` (donde está `requirements.txt`):

```
pip install -r requirements.txt
```

Esto instala:

| Paquete | Para qué |
|---|---|
| `streamlit` | la aplicación web |
| `psycopg2-binary` | conexión a PostgreSQL |
| `bcrypt` | hash de contraseñas |
| `pandas` | tablas del wizard (plan de cuotas, pagos) |

Verifica que quedaron instalados en el intérprete correcto:

```
python -c "import streamlit, psycopg2, bcrypt, pandas; print('OK')"
```

Si esto imprime `OK`, ya puedes seguir con la configuración de la base de
datos (si no lo has hecho) y correr la app.

## 4. Correr la aplicación

Desde `MCM/streamlit_app/`:

```
streamlit run app.py
```

Streamlit abre automáticamente `http://localhost:8501` en el navegador. Si
el puerto está ocupado, usa `--server.port 8502` (o el que prefieras).

## 5. Problemas comunes

- **`ModuleNotFoundError: No module named 'bcrypt'` (o `psycopg2`,
  `pandas`, `streamlit`)** → revisa la sección de Windows más arriba: casi
  siempre es que `streamlit run` está usando un Python distinto al que
  usaste para `pip install`. Confirma con `python -c "import sys;
  print(sys.executable)"` en la misma terminal donde corres `streamlit
  run`.
- **`'utf-8' codec can't decode byte ... invalid continuation byte`** al
  intentar conectar a la base de datos → esto no es un error de
  codificación real, es un mensaje de PostgreSQL en español (por el idioma
  del sistema operativo) que `psycopg2` no logra decodificar. El mensaje
  real casi siempre es de autenticación o de que la base de datos no
  existe — ver la sección de troubleshooting en
  [`BASE_DE_DATOS.md`](BASE_DE_DATOS.md).
