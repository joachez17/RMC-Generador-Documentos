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

# --- 1. CONFIGURACIÓN ---
USUARIO_ACTUAL = "Alioska Saavedra"
PROYECTO_DEFAULT = "Minera Escondida"
FILE_PATH = "data/Plan Personalizado de actividades SSO 2026 - Alioska Saavedra.xlsx"

# --- 2. FUNCIONES DE ENVÍO ---
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
        msg['Subject'] = f"UPLOAD: |{proyecto}| - {actividad} de {usuario}"

        body = f"Evidencia enviada.\nActividad: {actividad}\nSupervisor: {usuario}\nFecha: {date.today()}"
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

try:
    if os.path.exists(FILE_PATH):
        df_raw = pd.read_excel(FILE_PATH, header=None)
        
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.cat(sep=' ')
            if "NOMBRE DE LA ACTIVIDAD" in row_str:
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            df = pd.read_excel(FILE_PATH, header=header_row_idx)
        else:
            st.error("❌ No encontré 'NOMBRE DE LA ACTIVIDAD' en el Excel.")
            st.stop()
    else:
        st.error(f"⚠️ Archivo no encontrado: {FILE_PATH}")
        st.stop()

    # --- 4. RENOMBRAMIENTO ---
    col_excel_actividad = "NOMBRE DE LA ACTIVIDAD"
    col_excel_asig = "CANTIDAD ASIGNADA"
    col_excel_real = "CANTIDAD REALIZADA"
    col_excel_verif = "MEDIO DE VERIFICACIÓN"

    if col_excel_asig not in df.columns:
        st.error(f"No encuentro la columna '{col_excel_asig}'.")
        st.stop()

    df = df.rename(columns={
        col_excel_actividad: "Actividad",
        col_excel_asig: "Programado",
        col_excel_real: "Realizado",
        col_excel_verif: "Verificacion"
    })

    # --- 5. LIMPIEZA ---
    df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
    df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
    
    # Filtro: Solo actividades obligatorias (Meta > 0)
    df = df[df["Programado"] > 0]

except Exception as e:
    st.error(f"Error procesando el archivo: {e}")
    st.stop()

# --- 6. CÁLCULO DE KPIs ---
total_prog = df["Programado"].sum()
total_real = df["Realizado"].sum()
porcentaje = (total_real / total_prog * 100) if total_prog > 0 else 0

# --- 7. DASHBOARD VISUAL ---
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
                {'range': [0, 80], 'color': "lightgray"},
                {'range': [80, 100], 'color': "#b3e6b3"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    
    st.metric("Meta Total", int(total_prog))
    st.metric("Realizadas", int(total_real), delta=f"Faltan {int(total_prog - total_real)}", delta_color="inverse")

# --- 8. TABLA DE GESTIÓN (CORREGIDA PARA % Y BARRAS LLENAS) ---
with col2:
    st.subheader("📋 Plan de Trabajo (Asignado)")
    
    # NUEVO: Calculamos el % exacto de cada fila para que la barra se pinte bien
    # Si Realizado = Programado, el resultado es 1.0 (100%)
    df["Avance_Pct"] = df["Realizado"] / df["Programado"]
    
    # Mostramos la tabla configurando la columna "Avance_Pct"
    st.dataframe(
        df[["Actividad", "Programado", "Realizado", "Avance_Pct", "Verificacion"]],
        column_config={
            "Actividad": st.column_config.TextColumn("Actividad", width="medium"),
            "Programado": st.column_config.NumberColumn("Meta"),
            "Realizado": st.column_config.NumberColumn("Real"),
            
            # CONFIGURACIÓN CLAVE PARA EL PORCENTAJE
            "Avance_Pct": st.column_config.ProgressColumn(
                "Cumplimiento",
                format="%.0f%%", # Muestra el símbolo % sin decimales
                min_value=0,
                max_value=1,     # 1 significa 100% de la barra
            ),
            
            "Verificacion": st.column_config.TextColumn("Requisito")
        },
        use_container_width=True,
        hide_index=True
    )

st.divider()

# --- 9. CARGA DE EVIDENCIA ---
st.markdown("### 📷 Cargar Evidencia")
c_up1, c_up2 = st.columns(2)

with c_up1:
    actividades_lista = df["Actividad"].unique()
    act_seleccionada = st.selectbox("Selecciona actividad:", actividades_lista)
    
    if not df.empty:
        req_series = df[df["Actividad"] == act_seleccionada]["Verificacion"]
        if not req_series.empty:
            req = req_series.values[0]
            st.info(f"Requisito: **{req}**")

with c_up2:
    foto = st.camera_input("Foto del Documento")
    
    if foto:
        if st.button("🚀 Enviar y Actualizar", type="primary", use_container_width=True):
            with st.spinner("Enviando..."):
                if enviar_evidencia(foto, act_seleccionada, PROYECTO_DEFAULT, USUARIO_ACTUAL):
                    st.success("✅ ¡Evidencia enviada!")
                    st.balloons()