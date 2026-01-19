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

# --- 3. CARGA DE DATOS INTELIGENTE ---
st.title(f"📊 Portal de Cumplimiento: {USUARIO_ACTUAL}")

# CAMBIO 1: Apuntar al archivo XLSX original (Pon el nombre exacto de tu archivo)
FILE_PATH = "data/Plan Personalizado de actividades SSO 2026 - Alioska Saavedra.xlsx"

try:
    if os.path.exists(FILE_PATH):
        # Leemos el archivo sin cabecera primero para buscar dónde empieza
        df_raw = pd.read_excel(FILE_PATH, header=None)
        
        # --- BUSCADOR DE CABECERA ---
        header_row_idx = None
        for i, row in df_raw.iterrows():
            # Buscamos la fila que contenga "NOMBRE DE LA ACTIVIDAD" (o parte del texto)
            row_str = row.astype(str).str.cat(sep=' ')
            if "NOMBRE DE LA ACTIVIDAD" in row_str:
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            # Si la encontramos, recargamos el Excel usando esa fila como cabecera
            df = pd.read_excel(FILE_PATH, header=header_row_idx)
        else:
            st.error("❌ No encontré la fila de encabezados que diga 'NOMBRE DE LA ACTIVIDAD'.")
            st.stop()
            
    else:
        st.error(f"⚠️ No se encontró el archivo en: {FILE_PATH}")
        st.stop()

    # --- MAPEO DE COLUMNAS ---
    # Ahora que tenemos la cabecera correcta, seleccionamos las columnas
    col_actividad = "NOMBRE DE LA ACTIVIDAD"
    col_prog = "CANTIDAD ASIGNADA"  # Verifica si en tu Excel dice "ASIGNADA" o "PROGRAMADA"
    col_real = "CANTIDAD REALIZADA" # Verifica si dice "REALIZADA" o "EJECUTADA"
    
    # Validación extra por si acaso
    missing_cols = [c for c in [col_actividad, col_prog, col_real] if c not in df.columns]
    if missing_cols:
        st.error(f"Faltan estas columnas en la tabla detectada: {missing_cols}")
        st.write("Columnas encontradas:", df.columns.tolist())
        st.stop()

    # Limpieza de datos (Eliminar filas vacías o de totales que suelen estar al final)
    df = df.dropna(subset=[col_actividad]) 
    
    # Normalizamos números
    df[col_prog] = pd.to_numeric(df[col_prog], errors='coerce').fillna(0)
    df[col_real] = pd.to_numeric(df[col_real], errors='coerce').fillna(0)

except Exception as e:
    st.error(f"Error al procesar el Excel: {e}")
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
    
    # Obtenemos el valor máximo como un número entero puro de Python
    # Esto evita el error de JSON serializable
    valor_maximo = int(max(df["Programado"].max(), 1))

    # Tabla con barras de progreso visuales
    st.dataframe(
        df[["Actividad", "Programado", "Realizado"]],
        column_config={
            "Programado": st.column_config.NumberColumn("Meta"),
            "Realizado": st.column_config.ProgressColumn(
                "Avance",
                format="%d",
                min_value=0,
                max_value=valor_maximo, # Usamos la variable corregida
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