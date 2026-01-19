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
import time

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Portal Supervisores", page_icon="📈", layout="wide")

# --- 1. CONFIGURACIÓN ---
USUARIO_ACTUAL = "Alioska Saavedra"
PROYECTO_DEFAULT = "Minera Escondida"
FILE_PATH = "data/Plan Personalizado de actividades SSO 2026 - Alioska Saavedra.xlsx"

# --- 2. MEMORIA TEMPORAL (SESSION STATE) ---
# Esto permite que la App "recuerde" que subiste algo hoy, aunque no pueda editar el Excel
if "avances_sesion" not in st.session_state:
    st.session_state["avances_sesion"] = {}

# --- 3. FUNCIONES DE ENVÍO ---
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

# --- 4. CARGA DE DATOS ---
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
            st.error("❌ No encontré 'NOMBRE DE LA ACTIVIDAD'.")
            st.stop()
    else:
        st.error(f"⚠️ Archivo no encontrado: {FILE_PATH}")
        st.stop()

    # Renombramiento
    col_act = "NOMBRE DE LA ACTIVIDAD"
    col_asig = "CANTIDAD ASIGNADA"
    col_real = "CANTIDAD REALIZADA"
    col_verif = "MEDIO DE VERIFICACIÓN"

    df = df.rename(columns={col_act: "Actividad", col_asig: "Programado", col_real: "Realizado", col_verif: "Verificacion"})

    # Limpieza Numérica
    df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
    df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
    
    # Filtro: Solo actividades obligatorias
    df = df[df["Programado"] > 0]

    # --- MAGIA: SUMAR LO QUE ACABAS DE SUBIR EN ESTA SESIÓN ---
    # Si subiste algo ahora, se suma visualmente al Excel
    def sumar_sesion(row):
        act = row["Actividad"]
        extra = st.session_state["avances_sesion"].get(act, 0)
        return row["Realizado"] + extra

    df["Realizado_Total"] = df.apply(sumar_sesion, axis=1)

except Exception as e:
    st.error(f"Error procesando el archivo: {e}")
    st.stop()

# --- 5. CÁLCULO DE KPIs ---
total_prog = df["Programado"].sum()
total_real = df["Realizado_Total"].sum() # Usamos el total actualizado
porcentaje = (total_real / total_prog * 100) if total_prog > 0 else 0

# --- 6. DASHBOARD VISUAL ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### % Avance Mes")
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = porcentaje,
        gauge = {
            'axis': {'range': [None, 100]}, # Escala fija de 0 a 100
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

# --- 7. TABLA DE GESTIÓN (CORREGIDA 0-100) ---
with col2:
    st.subheader("📋 Plan de Trabajo")
    
    # Calculamos porcentaje en escala 0-100 para evitar decimales raros
    # Si Realizado >= Programado, ponemos 100
    df["Avance_Pct"] = (df["Realizado_Total"] / df["Programado"]) * 100
    df["Avance_Pct"] = df["Avance_Pct"].clip(upper=100) # Que no pase de 100%

    st.dataframe(
        df[["Actividad", "Programado", "Realizado_Total", "Avance_Pct", "Verificacion"]],
        column_config={
            "Actividad": st.column_config.TextColumn("Actividad", width="medium"),
            "Programado": st.column_config.NumberColumn("Meta"),
            "Realizado_Total": st.column_config.NumberColumn("Real"),
            
            # CONFIGURACIÓN PARA QUE DIGA "100%"
            "Avance_Pct": st.column_config.ProgressColumn(
                "Cumplimiento",
                format="%d%%",   # %d significa entero (100) y %% pone el símbolo %
                min_value=0,
                max_value=100,   # Escala 0 a 100
            ),
            
            "Verificacion": st.column_config.TextColumn("Requisito")
        },
        use_container_width=True,
        hide_index=True
    )

st.divider()

# --- 8. CARGA DE EVIDENCIA ---
st.markdown("### 📷 Cargar Evidencia")
c_up1, c_up2 = st.columns(2)

with c_up1:
    # Solo mostramos actividades que no estén completas al 100% (Opcional, o mostrar todas)
    df_pendientes = df[df["Realizado_Total"] < df["Programado"]]
    
    # Si todo está listo, mostramos mensaje de éxito
    if df_pendientes.empty:
        st.success("¡Felicidades! Has completado todas las actividades asignadas.")
        actividades_lista = df["Actividad"].unique() # Dejamos elegir igual por si quiere repetir
    else:
        actividades_lista = df_pendientes["Actividad"].unique()

    act_seleccionada = st.selectbox("Selecciona actividad:", actividades_lista)
    
    if not df.empty:
        req_series = df[df["Actividad"] == act_seleccionada]["Verificacion"]
        if not req_series.empty:
            req = req_series.values[0]
            st.info(f"Requisito: **{req}**")

with c_up2:
    foto = st.camera_input("Foto del Documento")
    
    if foto:
        if st.button("🚀 Enviar y Registrar", type="primary", use_container_width=True):
            with st.spinner("Procesando..."):
                if enviar_evidencia(foto, act_seleccionada, PROYECTO_DEFAULT, USUARIO_ACTUAL):
                    
                    # --- ACTUALIZACIÓN DE MEMORIA TEMPORAL ---
                    current_val = st.session_state["avances_sesion"].get(act_seleccionada, 0)
                    st.session_state["avances_sesion"][act_seleccionada] = current_val + 1
                    
                    st.success("✅ ¡Registrado! El gráfico se ha actualizado.")
                    time.sleep(2) # Espera un poco para que veas el mensaje
                    st.rerun() # Recarga la página para mostrar la barra nueva