import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="EXPO MCM - Pagos", layout="centered")

st.title("💳 Pasarela de Pago y Conciliación (HU6)")

# Validar pre-reserva
if 'datos_marca' not in st.session_state or st.session_state.datos_marca["stand_seleccionado"] is None:
    st.warning("⚠️ No hay pre-reserva activa registrada para procesar pagos.")
else:
    stand_actual = st.session_state.datos_marca["stand_seleccionado"]
    precio_actual = st.session_state.datos_marca["precio_stand"]
    
    st.write("Simulación del portal financiero para la formalización del stand.")
    
    # Lectura del archivo para verificar el estado actual del stand
    with open("stands_db.json", "r", encoding="utf-8") as f:
        db = json.load(f)
    
    estado_actual_db = db[stand_actual]["estado"]
    
    st.info(f"""
    **Espacio:** {stand_actual}  
    **Precio total a liquidar:** ${precio_actual:,.0f} COP  
    **Estado actual en Base de Datos:** {estado_actual_db}
    """)
    
    if estado_actual_db == "Bloqueado":
        st.success("✅ Este stand ya cuenta con un pago verificado. Su participación está confirmada.")
    else:
        st.subheader("Simulación de Escenarios Financieros")
        st.write("Marque la siguiente casilla si desea simular un pago retrasado para probar las reglas de penalización de la HU6 (Escenario 2):")
        
        # Simulación de condiciones temporales para cumplir los criterios de aceptación de HU6
        pago_retrasado = st.checkbox("Simular: Pago realizado fuera del plazo establecido (Vencido)")

        # Botón para detonar el pago
        if st.button("Efectuar Transacción de Pago (PSE / Tarjeta)", type="primary"):
            
            if not pago_retrasado:
                # ----------------- ESCENARIO 1: Pago a Tiempo -----------------
                # Actualizar el stand a "Bloqueado" de forma permanente en stands_db.json
                with open("stands_db.json", "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data[stand_actual]["estado"] = "Bloqueado"
                    f.seek(0)
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    f.truncate()
                
                st.success("🎉 ¡Transacción Exitosa!")
                st.balloons()
                st.write(f"El stand **{stand_actual}** ha sido bloqueado de forma automática en la base de datos externa.")
                st.info("Se ha generado la Factura Electrónica y se remitió al correo electrónico de la marca.")
                
            else:
                # ----------------- ESCENARIO 2: Pago fuera de Plazo -----------------
                st.error("🚨 Alerta Financiera: Transacción fuera de plazo detectada")
                st.warning(f"""
                El pago para el **{stand_actual}** fue procesado, pero se detectó que el límite temporal de reserva había expirado.
                
                **Acción tomada por el sistema:**
                - Se notificó automáticamente al Coordinador de la EXPO.
                - El estado no se actualizó automáticamente a 'Bloqueado' para salvaguardar la disponibilidad del espacio ante competidores.
                - Se aplicará el cobro de la penalidad correspondiente sobre el valor total antes de confirmar la participación física.
                """)
                
        if st.button("Resetear Base de Datos de Stands"):
            # Permite restablecer el archivo JSON para reiniciar las pruebas
            stands_iniciales = {
                "Stand A-12 (3x3m)": {"precio": 1500000, "estado": "Disponible", "marca_reservada": ""},
                "Stand A-15 (3x3m)": {"precio": 2500000, "estado": "Disponible", "marca_reservada": ""},
                "Stand B-01 (4x4m)": {"precio": 3800000, "estado": "Disponible", "marca_reservada": ""}
            }
            with open("stands_db.json", "w", encoding="utf-8") as f:
                json.dump(stands_iniciales, f, indent=4, ensure_ascii=False)
            st.success("Base de datos de stands reestablecida con éxito.")
            st.rerun()
