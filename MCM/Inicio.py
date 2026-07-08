import streamlit as st
import json
import os

st.set_page_config(page_title="EXPO MCM - Inicio", layout="centered")

st.title("🏃‍♂️ Sistema EXPO Maratón Medellín")
st.write("Bienvenido al Portal de Comercialización de Stands.")
st.divider()

# Función para cargar la base de datos del archivo externo
def cargar_db():
    if not os.path.exists("stands_db.json"):
        # Crear archivo por defecto si se borra
        stands_iniciales = {
            "Stand A-12 (3x3m)": {"precio": 1500000, "estado": "Disponible", "marca_reservada": ""},
            "Stand A-15 (3x3m)": {"precio": 2500000, "estado": "Disponible", "marca_reservada": ""},
            "Stand B-01 (4x4m)": {"precio": 3800000, "estado": "Disponible", "marca_reservada": ""}
        }
        with open("stands_db.json", "w", encoding="utf-8") as f:
            json.dump(stands_iniciales, f, indent=4, ensure_ascii=False)
    
    with open("stands_db.json", "r", encoding="utf-8") as f:
        return json.load(f)

db_stands = cargar_db()

# Inicializar variables globales de control de usuario
if 'datos_marca' not in st.session_state:
    st.session_state.datos_marca = {
        "nombre": "Gatorade Colombia S.A.S.",
        "nit": "900.123.456-7",
        "representante": "Juan José Piedrahíta",
        "email_rep": "contacto@marca.com",
        "stand_seleccionado": None,
        "precio_stand": 0
    }

st.subheader("Simulación: Seleccione un Stand de la Base de Datos")
st.write("Estos datos y precios se extraen en tiempo real de `stands_db.json`:")

# Listar los stands que no estén ocupados ("Bloqueados")
opciones_disponibles = [k for k, v in db_stands.items() if v["estado"] != "Bloqueado"]

if opciones_disponibles:
    stand_elegido = st.selectbox("Seleccione un Stand disponible para pre-reservar:", opciones_disponibles)
    
    # Extraer el precio dinámicamente del archivo JSON
    precio_extraido = db_stands[stand_elegido]["precio"]
    estado_extraido = db_stands[stand_elegido]["estado"]
    
    st.info(f"**Precio del espacio:** ${precio_extraido:,.0f} COP | **Estado:** {estado_extraido}")
    
    if st.button("Confirmar Pre-reserva y Proceder", type="primary"):
        # Actualizar datos de sesión
        st.session_state.datos_marca["stand_seleccionado"] = stand_elegido
        st.session_state.datos_marca["precio_stand"] = precio_extraido
        
        st.success(f"¡Pre-reserva exitosa! Ha seleccionado el {stand_elegido}. Por favor, proceda a la sección **1_HU4_Contratos** en la barra lateral.")
else:
    st.warning("Todos los stands se encuentran bloqueados o reservados.")
