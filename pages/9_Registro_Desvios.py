import streamlit as st
import requests

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Registro de Desvíos", page_icon="🚧", layout="wide")

# ⚠️ PEGA AQUÍ LA MISMA URL QUE USAS EN EL PORTAL DE SUPERVISORES
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwgY0zTgkMKbfY3h55nXQ_hnaqfpzgRUcoLB05uwr3Hgxfuu0kK3-YLYDr3siGwf2vREw/exec" 

st.title("🚧 Registro de Desvíos y Positivos")
st.markdown("Ingresa los datos del evento para registrarlos en la base de datos central.")

# ==========================================
# FORMULARIO
# ==========================================
with st.form("form_desvios", clear_on_submit=True):
    st.subheader("1. Descripción del Evento")
    actividad = st.text_input("Actividad (Ej: Extensión eléctrica a ras de piso, No uso EPP, etc.)")
    
    st.markdown("---")
    st.subheader("2. Clasificación (Ingresa la cantidad)")
    col1, col2, col3 = st.columns(3)
    with col1:
        condicion = st.number_input("Condición Insegura", min_value=0, value=0)
    with col2:
        accion = st.number_input("Acción Insegura", min_value=0, value=0)
    with col3:
        positivo = st.number_input("Positivo", min_value=0, value=0)
        
    st.markdown("---")
    st.subheader("3. Detalles del Reporte")
    col4, col5, col6 = st.columns(3)
    
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    with col4:
        mes = st.selectbox("Mes", meses)
    with col5:
        tendencia = st.text_input("Tendencia", value="1")
    with col6:
        seguimiento = st.selectbox("Seguimiento", ["Abierto", "Cerrado", "N/A"])
        
    st.markdown("<br>", unsafe_allow_html=True)
    enviado = st.form_submit_button("🚀 GUARDAR REGISTRO", type="primary")

# ==========================================
# LÓGICA DE ENVÍO
# ==========================================
if enviado:
    if actividad.strip() == "":
        st.warning("⚠️ Debes ingresar el nombre de la actividad.")
    else:
        with st.spinner("Guardando en la base de datos... 🛰️"):
            # Dejamos en blanco si es 0 (para que el Excel se vea limpio como en tu imagen)
            val_condicion = condicion if condicion > 0 else ""
            val_accion = accion if accion > 0 else ""
            val_positivo = positivo if positivo > 0 else ""

            payload = {
                "accion": "guardar_desvio",
                "actividad": actividad,
                "condicion": val_condicion,
                "accion_insegura": val_accion,
                "positivo": val_positivo,
                "mes": mes,
                "tendencia": tendencia,
                "seguimiento": seguimiento
            }
            
            try:
                respuesta = requests.post(APPS_SCRIPT_URL, json=payload)
                if respuesta.status_code == 200:
                    st.balloons()
                    st.success("✅ ¡Registro guardado exitosamente!")
                else:
                    st.error("❌ Error al conectar con la base de datos.")
            except Exception as e:
                st.error(f"❌ Error de conexión: {str(e)}")