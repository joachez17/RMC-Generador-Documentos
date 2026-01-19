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
# Nombre exacto de tu archivo en la carpeta data
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
        # Leemos sin cabecera para encontrar dónde empieza la tabla real
        df_raw = pd.read_excel(FILE_PATH, header=None)
        
        # Buscamos la fila que tiene los títulos
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.cat(sep=' ')
            if "NOMBRE DE LA ACTIVIDAD" in row_str:
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            # Cargamos de nuevo usando la fila correcta como cabecera
            df = pd.read_excel(FILE_PATH, header=header_row_idx)
        else:
            st.error("❌ No encontré 'NOMBRE DE LA ACTIVIDAD' en el Excel.")
            st.stop()
    else:
        st.error(f"⚠️ Archivo no encontrado: {FILE_PATH}")
        st.stop()

    # --- MAPEO Y RENOMBRAMIENTO (LA SOLUCIÓN AL ERROR) ---
    # Nombres exactos de tu Excel
    col_excel_actividad = "NOMBRE DE LA ACTIVIDAD"
    col_excel_asig = "CANTIDAD ASIGNADA"
    col_excel_real = "CANTIDAD REALIZADA"
    col_excel_verif = "MEDIO DE VERIFICACIÓN"

    # Verificamos que existan
    if col_excel_asig not in df.columns:
        st.error(f"No encuentro la columna '{col_excel_asig}'. Revisa el Excel.")
        st.stop()

    # TRUCO: Renombramos las columnas a nombres estándar para que el resto del código funcione
    df = df.rename(columns={
        col_excel_actividad: "Actividad",
        col_excel_asig: "Programado",
        col_excel_real: "Realizado",
        col_excel_verif: "Verificacion"
    })

    # Limpieza de datos
    df = df.dropna(subset=["Actividad"]) # Borrar filas vacías
    df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
    df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)

except Exception as e:
    st.error(f"Error procesando el archivo: {e}")
    st.stop()

# --- 4. CÁLCULO DE KPIs ---
# Ahora sí existen las columnas "Programado" y "Realizado" porque las renombramos arriba
total_prog = df["Programado"].sum()
total_real = df["Realizado"].sum()
porcentaje = (total_real / total_prog * 100) if total_prog > 0 else 0

# --- 5. DASHBOARD VISUAL ---
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

# --- 6. TABLA DE GESTIÓN ---
with col2:
    st.subheader("📋 Plan de Trabajo")
    
    val_max = int(df["Programado"].max()) if not df.empty else 1
    if val_max == 0: val_max = 1

    st.dataframe(
        df[["Actividad", "Programado", "Realizado", "Verificacion"]],
        column_config={
            "Actividad": st.column_config.TextColumn("Actividad"),
            "Programado": st.column_config.NumberColumn("Meta"),
            "Realizado": st.column_config.ProgressColumn(
                "Avance",
                format="%d",
                min_value=0,
                max_value=val_max
            ),
            "Verificacion": st.column_config.TextColumn("Requisito")
        },
        use_container_width=True,
        hide_index=True
    )

st.divider()

# --- 7. CARGA DE EVIDENCIA ---
st.markdown("### 📷 Cargar Evidencia")
c_up1, c_up2 = st.columns(2)

with c_up1:
    # Filtramos solo actividades con meta > 0
    df_activas = df[df["Programado"] > 0]
    act_seleccionada = st.selectbox("Selecciona actividad:", df_activas["Actividad"].unique())
    
    # Mostramos el requisito
    if not df_activas.empty:
        req = df_activas[df_activas["Actividad"] == act_seleccionada]["Verificacion"].values[0]
        st.info(f"Debes subir: **{req}**")

with c_up2:
    foto = st.camera_input("Foto del Documento")
    
    if foto:
        if st.button("🚀 Enviar", type="primary", use_container_width=True):
            with st.spinner("Enviando..."):
                if enviar_evidencia(foto, act_seleccionada, PROYECTO_DEFAULT, USUARIO_ACTUAL):
                    st.success("✅ ¡Enviado! (Actualiza el Excel maestro para ver cambios)")
                    st.balloons()