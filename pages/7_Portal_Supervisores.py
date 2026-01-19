import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import date
import os

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Portal Supervisores", page_icon="📈", layout="wide")

# --- 1. CONFIGURACIÓN DEL USUARIO Y ARCHIVO ---
USUARIO_ACTUAL = "Alioska Saavedra"
PROYECTO_DEFAULT = "Minera Escondida"
# Asegúrate de subir tu archivo CSV a una carpeta llamada 'data' o en la raíz
# Cambia este nombre si tu archivo se llama distinto
CSV_FILE = "Plan Personalizado de actividades SSO 2026 - Alioska Saavedra.xlsx - Personalizado Enero 2026.csv"

# --- 2. FUNCIONES DE ENVÍO (ROBOT) ---
def enviar_evidencia(foto, actividad, proyecto, usuario):
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        receiver_email = st.secrets["email"]["receiver_email"]

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        # ASUNTO CLAVE (BARRA VERTICAL) PARA QUE EL ROBOT LO LEA
        msg['Subject'] = f"UPLOAD: |{proyecto}| - {actividad} de {usuario}"

        body = f"Evidencia de cumplimiento enviada desde App RMC.\nActividad: {actividad}\nSupervisor: {usuario}\nFecha: {date.today()}"
        msg.attach(MIMEText(body, 'plain'))

        if foto:
            part = MIMEBase('image', 'jpeg')
            part.set_payload(foto.getvalue())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename=evidencia_{date.today()}.jpg")
            msg.attach(part)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error enviando correo: {e}")
        return False

# --- 3. CARGA DE DATOS ---
st.title(f"📊 Portal de Cumplimiento: {USUARIO_ACTUAL}")

try:
    # Intentamos leer el archivo. Si no existe, usamos datos de prueba.
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        st.warning(f"⚠️ No se encontró el archivo '{CSV_FILE}'. Usando datos de ejemplo.")
        data = {
            "Actividad": ["Charla 5 Min", "Inspección EPP", "AST Diario", "Reunión Calidad", "Cierre NCR"],
            "Programado": [20, 4, 20, 1, 2],
            "Realizado": [12, 4, 10, 0, 1]
        }
        df = pd.DataFrame(data)

    # --- LIMPIEZA Y MAPEO DE COLUMNAS (INTELIGENCIA) ---
    # Esto busca las columnas aunque tengan nombres ligeramente distintos en tu Excel
    col_actividad = next((c for c in df.columns if "Actividad" in c or "Item" in c), None)
    col_prog = next((c for c in df.columns if "Programado" in c or "Meta" in c or "Plan" in c), None)
    col_real = next((c for c in df.columns if "Real" in c or "Ejecutado" in c), None)

    if not col_actividad or not col_prog or not col_real:
        st.error("❌ Error en las columnas del CSV. Asegúrate que tu Excel tenga columnas parecidas a: 'Actividad', 'Programado', 'Realizado'.")
        st.write("Columnas encontradas:", df.columns.tolist())
        st.stop()
    
    # Renombramos para trabajar fácil
    df = df.rename(columns={col_actividad: "Actividad", col_prog: "Programado", col_real: "Realizado"})
    
    # Aseguramos que sean números (rellena vacíos con 0)
    df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
    df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)

except Exception as e:
    st.error(f"Error al procesar el archivo: {e}")
    st.stop()

# --- 4. CÁLCULO DE KPIs ---
total_prog = df["Programado"].sum()
total_real = df["Realizado"].sum()
# Evitar división por cero
porcentaje = (total_real / total_prog * 100) if total_prog > 0 else 0

# --- 5. DASHBOARD VISUAL (VELOCÍMETRO) ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### % Avance Mes")
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = porcentaje,
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#004B8D"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    
    st.metric("Meta Total", f"{int(total_prog)} Actividades")
    st.metric("Realizadas", f"{int(total_real)}", delta=f"Faltan {int(total_prog - total_real)}")

# --- 6. TABLA DE GESTIÓN Y ESCÁNER ---
with col2:
    st.subheader("📋 Tu Plan de Trabajo")
    
    # Tabla con barras de progreso visuales
    st.dataframe(
        df[["Actividad", "Programado", "Realizado"]],
        column_config={
            "Programado": st.column_config.NumberColumn("Meta"),
            "Realizado": st.column_config.ProgressColumn(
                "Avance",
                format="%d",
                min_value=0,
                max_value=max(df["Programado"].max(), 1)
            )
        },
        use_container_width=True,
        hide_index=True
    )

st.divider()

# --- 7. ZONA DE CARGA DE EVIDENCIA ---
st.markdown("### 📷 Cargar Evidencia de Actividad")
c_upload1, c_upload2 = st.columns(2)

with c_upload1:
    # Selectbox inteligente: Solo muestra actividades que tienen meta > 0
    actividades_validas = df[df["Programado"] > 0]["Actividad"].unique()
    act_seleccionada = st.selectbox("Selecciona la actividad realizada:", actividades_validas)
    
    st.info(f"Vas a subir evidencia para: **{act_seleccionada}**")

with c_upload2:
    foto = st.camera_input("Tomar foto del documento")
    
    if foto:
        if st.button("🚀 Enviar Evidencia", type="primary", use_container_width=True):
            with st.spinner("Subiendo y notificando al Robot..."):
                if enviar_evidencia(foto, act_seleccionada, PROYECTO_DEFAULT, USUARIO_ACTUAL):
                    st.success("✅ ¡Enviado! Tu % de avance se actualizará pronto.")
                    st.balloons()