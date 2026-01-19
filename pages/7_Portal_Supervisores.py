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

# --- 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO ---
st.set_page_config(page_title="Portal Supervisores", page_icon="🛡️", layout="wide")

# --- INYECCIÓN DE CSS PERSONALIZADO (AQUÍ ESTÁ LA MAGIA VISUAL) ---
st.markdown("""
    <style>
        /* Importamos fuente moderna */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
        }

        /* Fondo general un poco más gris para que resalten las tarjetas */
        .stApp {
            background-color: #f4f6f9;
        }

        /* Títulos principales */
        h1, h2, h3 {
            color: #004B8D; /* Azul RMC */
            font-weight: 700;
        }

        /* Estilo para las "Tarjetas" (Contenedores blancos) */
        .css-1r6slb0, .css-12w0qpk { 
            /* Esto afecta a los contenedores nativos, pero usaremos divs personalizados */
        }
        
        div.stMetric {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        /* Botones primarios (Enviar) */
        .stButton>button {
            background-color: #004B8D;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
            font-weight: bold;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #003666;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            color: white;
        }

        /* Separador bonito */
        hr {
            margin: 2rem 0;
            border: 0;
            border-top: 2px solid #004B8D;
            opacity: 0.1;
        }
        
        /* Ajuste de alertas */
        .stAlert {
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE VARIABLES ---
USUARIO_ACTUAL = "Alioska Saavedra"
PROYECTO_DEFAULT = "Minera Escondida"
FILE_PATH = "data/Plan Personalizado de actividades SSO 2026 - Alioska Saavedra.xlsx"

# --- MEMORIA TEMPORAL ---
if "avances_sesion" not in st.session_state:
    st.session_state["avances_sesion"] = {}

# --- FUNCIONES DE ENVÍO ---
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

# --- LÓGICA DE CARGA DE DATOS ---
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
            st.error("❌ No se encontró la tabla de actividades.")
            st.stop()
    else:
        st.error(f"⚠️ Archivo no encontrado: {FILE_PATH}")
        st.stop()

    df = df.rename(columns={
        "NOMBRE DE LA ACTIVIDAD": "Actividad",
        "CANTIDAD ASIGNADA": "Programado",
        "CANTIDAD REALIZADA": "Realizado",
        "MEDIO DE VERIFICACIÓN": "Verificacion"
    })

    df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
    df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
    df = df[df["Programado"] > 0]

    # Sumar sesión actual
    def sumar_sesion(row):
        act = row["Actividad"]
        extra = st.session_state["avances_sesion"].get(act, 0)
        return row["Realizado"] + extra

    df["Realizado_Total"] = df.apply(sumar_sesion, axis=1)

except Exception as e:
    st.error(f"Error procesando datos: {e}")
    st.stop()

# --- CÁLCULOS KPI ---
total_prog = int(df["Programado"].sum())
total_real = int(df["Realizado_Total"].sum())
# Limitar visualmente el total real al total programado para que no de más de 100% en el KPI global si se pasan
porcentaje_global = (total_real / total_prog * 100) if total_prog > 0 else 0
if porcentaje_global > 100: porcentaje_global = 100

# ==========================================
#              INTERFAZ GRÁFICA
# ==========================================

# HEADER CON ESTILO
st.markdown(f"""
    <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;">
        <h2 style="margin:0; color: #004B8D;">🛡️ Portal de Cumplimiento SSO</h2>
        <p style="margin:0; color: #666; font-size: 14px;">Bienvenido/a <strong>{USUARIO_ACTUAL}</strong> | Proyecto: <strong>{PROYECTO_DEFAULT}</strong></p>
    </div>
""", unsafe_allow_html=True)

# SECCIÓN 1: TARJETAS DE MÉTRICAS (KPIs)
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    st.metric(label="📍 Meta del Mes", value=f"{total_prog} Actividades")
with col_kpi2:
    delta_val = total_real - total_prog
    st.metric(label="✅ Ejecutadas", value=f"{total_real}", delta=f"{delta_val} Gap" if delta_val < 0 else "¡Cumplido!", delta_color="normal")
with col_kpi3:
    st.metric(label="🚀 % Cumplimiento", value=f"{porcentaje_global:.1f}%")

st.markdown("<br>", unsafe_allow_html=True) # Espacio

# SECCIÓN 2: GRÁFICO Y TABLA (LADO A LADO)
c_main1, c_main2 = st.columns([1, 2], gap="medium")

# COLUMNA IZQUIERDA: GRÁFICO
with c_main1:
    st.markdown('<div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 100%;">', unsafe_allow_html=True)
    st.markdown("##### 📊 Velocidad de Avance")
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = porcentaje_global,
        number = {'suffix': "%", 'font': {'size': 40, 'color': "#004B8D"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#333"},
            'bar': {'color': "#004B8D"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#f0f2f6",
            'steps': [
                {'range': [0, 60], 'color': "#f8f9fa"},
                {'range': [60, 90], 'color': "#e9ecef"}],
            'threshold': {'line': {'color': "#28a745", 'width': 4}, 'thickness': 0.75, 'value': 100}
        }
    ))
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# COLUMNA DERECHA: TABLA DETALLADA
with c_main2:
    st.markdown('<div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 100%;">', unsafe_allow_html=True)
    st.markdown("##### 📋 Detalle de Actividades")
    
    # Calculamos % para la barra
    df["Avance_Pct"] = (df["Realizado_Total"] / df["Programado"]) * 100
    df["Avance_Pct"] = df["Avance_Pct"].clip(upper=100)

    st.dataframe(
        df[["Actividad", "Programado", "Realizado_Total", "Avance_Pct"]],
        column_config={
            "Actividad": st.column_config.TextColumn("Actividad", width="medium"),
            "Programado": st.column_config.NumberColumn("Meta", format="%d"),
            "Realizado_Total": st.column_config.NumberColumn("Real", format="%d"),
            "Avance_Pct": st.column_config.ProgressColumn(
                "Estado",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=350
    )
    st.markdown('</div>', unsafe_allow_html=True)

# SECCIÓN 3: ZONA DE ACCIÓN (DIFERENCIADA VISUALMENTE)
st.markdown("---")
st.markdown("<h3 style='text-align: center; color: #333;'>📸 Centro de Carga Rápida</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Selecciona la actividad pendiente y sube tu evidencia fotográfica.</p>", unsafe_allow_html=True)

col_act, col_cam = st.columns([1, 1], gap="large")

with col_act:
    st.markdown('<div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #004B8D;">', unsafe_allow_html=True)
    st.markdown("**1. Seleccionar Actividad**")
    
    # Filtro inteligente: Mostrar primero las pendientes
    df_pendientes = df[df["Realizado_Total"] < df["Programado"]]
    
    if df_pendientes.empty:
        opciones = df["Actividad"].unique()
        st.success("🎉 ¡Todo completado! (Puedes seguir subiendo si deseas)")
    else:
        opciones = df_pendientes["Actividad"].unique()
        
    act_seleccionada = st.selectbox("Actividad a reportar:", opciones, label_visibility="collapsed")
    
    # Buscar requisito
    req = df[df["Actividad"] == act_seleccionada]["Verificacion"].iloc[0]
    st.info(f"📄 **Documento Requerido:** {req}")
    st.markdown('</div>', unsafe_allow_html=True)

with col_cam:
    st.markdown('<div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px dashed #999;">', unsafe_allow_html=True)
    st.markdown("**2. Capturar Evidencia**")
    foto = st.camera_input("Cámara", label_visibility="collapsed")
    
    if foto:
        st.write("") # Espacio
        if st.button("🚀 ENVIAR REPORTE AHORA", type="primary"):
            with st.spinner("Procesando y notificando..."):
                if enviar_evidencia(foto, act_seleccionada, PROYECTO_DEFAULT, USUARIO_ACTUAL):
                    # Actualizar sesión
                    curr = st.session_state["avances_sesion"].get(act_seleccionada, 0)
                    st.session_state["avances_sesion"][act_seleccionada] = curr + 1
                    
                    st.success("✅ ¡Registro Exitoso!")
                    time.sleep(1.5)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)