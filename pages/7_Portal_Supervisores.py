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

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ==========================================
st.set_page_config(page_title="Portal Supervisores", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
        }
        
        /* Fondo general suave */
        .stApp {
            background-color: #f4f6f9;
        }
        
        /* Caja del Selector de Supervisor */
        .selector-box {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #004B8D;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        
        /* Estilo de las métricas (KPIs) */
        div.stMetric {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        /* Botones estilo RMC */
        .stButton>button {
            background-color: #004B8D;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
            font-weight: bold;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #003666;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            color: white;
        }
        
        h1, h2, h3, h4, h5 { color: #004B8D; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURACIÓN MAESTRA DE SUPERVISORES
# ==========================================
BASE_DATA_FOLDER = "data"

# Diccionario con los nombres EXACTOS de los archivos que subiste
MAPA_SUPERVISORES = {
    "Alioska Saavedra": "Plan Personalizado de actividades SSO 2026 - Alioska Saavedra.xlsx",
    "Carlos Araya": "Plan Personalizado de actividades SSO 2026 - Carlos Araya.xlsx",
    "Froilán Vargas": "Plan Personalizado de actividades SSO 2026 - Froilán Vargas.xlsx",
    "Juan de los Rios": "Plan Personalizado de actividades SSO 2026 - Juan de los Rios.xlsx",
    "Yorbin Valecillos": "Plan Personalizado de actividades SSO 2026 - Yorbin Valecillos.xlsx"
}

PROYECTO_DEFAULT = "Minera Escondida"

# ==========================================
# 3. GESTIÓN DE MEMORIA (SESSION STATE)
# ==========================================
if "avances_sesion" not in st.session_state:
    st.session_state["avances_sesion"] = {}

# ==========================================
# 4. FUNCIÓN DE ENVÍO (ROBOT)
# ==========================================
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

        body = f"Nueva evidencia cargada.\nActividad: {actividad}\nSupervisor: {usuario}\nFecha: {date.today()}"
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
        st.error(f"Error de conexión: {e}")
        return False

# ==========================================
# 5. INTERFAZ DE USUARIO (UI)
# ==========================================

st.markdown("<h2 style='color: #004B8D;'>🛡️ Portal de Gestión SSO</h2>", unsafe_allow_html=True)

# --- A. SELECTOR DE SUPERVISOR ---
st.markdown('<div class="selector-box">', unsafe_allow_html=True)
col_sel_1, col_sel_2 = st.columns([1, 3])
with col_sel_1:
    st.markdown("### 👤 Identificación")
    st.write("Seleccione su nombre:")
with col_sel_2:
    usuario_seleccionado = st.selectbox("Supervisor:", list(MAPA_SUPERVISORES.keys()), label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# --- B. LÓGICA DE CARGA DE DATOS ---
nombre_archivo = MAPA_SUPERVISORES[usuario_seleccionado]
ruta_completa = os.path.join(BASE_DATA_FOLDER, nombre_archivo)

datos_cargados = False
df = pd.DataFrame()

if os.path.exists(ruta_completa):
    try:
        # 1. Búsqueda inteligente de la cabecera
        df_raw = pd.read_excel(ruta_completa, header=None)
        
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.cat(sep=' ')
            if "NOMBRE DE LA ACTIVIDAD" in row_str:
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            # 2. Carga limpia
            df = pd.read_excel(ruta_completa, header=header_row_idx)
            
            # 3. Renombrar columnas
            df = df.rename(columns={
                "NOMBRE DE LA ACTIVIDAD": "Actividad",
                "CANTIDAD ASIGNADA": "Programado",
                "CANTIDAD REALIZADA": "Realizado",
                "MEDIO DE VERIFICACIÓN": "Verificacion"
            })
            
            # 4. Limpieza numérica
            df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
            df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
            
            # 5. Filtro (Solo obligatorias)
            df = df[df["Programado"] > 0]

            # 6. Sumar avances de sesión
            def sumar_sesion(row):
                act = row["Actividad"]
                clave = f"{usuario_seleccionado}_{act}"
                extra = st.session_state["avances_sesion"].get(clave, 0)
                return row["Realizado"] + extra

            df["Realizado_Total"] = df.apply(sumar_sesion, axis=1)
            datos_cargados = True
            
        else:
            st.error(f"❌ Formato incorrecto en archivo de {usuario_seleccionado} (Falta 'NOMBRE DE LA ACTIVIDAD').")
            
    except Exception as e:
        st.error(f"❌ Error leyendo archivo: {e}")
else:
    st.info(f"👋 Hola **{usuario_seleccionado}**.")
    st.warning(f"⚠️ No encuentro el archivo `{nombre_archivo}` en la carpeta `data`. Por favor cárgalo.")


# --- C. DASHBOARD ---
if datos_cargados and not df.empty:
    
    # KPI GLOBAL
    total_prog = int(df["Programado"].sum())
    total_real = int(df["Realizado_Total"].sum())
    
    pct_global = (total_real / total_prog * 100) if total_prog > 0 else 0
    if pct_global > 100: pct_global = 100

    # TARJETAS SUPERIORES
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📍 Meta Mes", f"{total_prog}")
    with c2: 
        delta = total_real - total_prog
        st.metric("✅ Realizadas", f"{total_real}", delta=f"{delta}" if delta < 0 else "¡Cumplido!")
    with c3: st.metric("🚀 Cumplimiento", f"{pct_global:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # VISUALIZACIÓN
    c_viz, c_tabla = st.columns([1, 2], gap="medium")
    
    with c_viz:
        st.markdown('<div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        st.markdown(f"##### Avance Global")
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = pct_global,
            number = {'suffix': "%", 'font': {'size': 40, 'color': "#004B8D"}},
            gauge = {
                'axis': {'range': [None, 100]}, 'bar': {'color': "#004B8D"},
                'steps': [{'range': [0, 100], 'color': "#f8f9fa"}],
                'threshold': {'line': {'color': "#28a745", 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_tabla:
        st.markdown('<div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        st.markdown("##### 📋 Detalle de Actividades")
        
        df["Avance_Pct"] = (df["Realizado_Total"] / df["Programado"]) * 100
        df["Avance_Pct"] = df["Avance_Pct"].clip(upper=100)

        st.dataframe(
            df[["Actividad", "Programado", "Realizado_Total", "Avance_Pct"]],
            column_config={
                "Actividad": st.column_config.TextColumn("Actividad", width="medium"),
                "Programado": st.column_config.NumberColumn("Meta", format="%d"),
                "Realizado_Total": st.column_config.NumberColumn("Real", format="%d"),
                "Avance_Pct": st.column_config.ProgressColumn("Estado", format="%d%%", min_value=0, max_value=100),
            },
            use_container_width=True, hide_index=True, height=300
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ZONA DE CARGA
    st.markdown("---")
    st.markdown("<h3 style='text-align:center; color:#004B8D;'>📸 Cargar Evidencia</h3>", unsafe_allow_html=True)
    
    col_in1, col_in2 = st.columns([1, 1], gap="large")
    
    with col_in1:
        # Priorizar pendientes
        df_pendientes = df[df["Realizado_Total"] < df["Programado"]]
        lista_opciones = df_pendientes["Actividad"].unique() if not df_pendientes.empty else df["Actividad"].unique()
        
        if df_pendientes.empty:
            st.success("🎉 ¡Todas las metas cumplidas!")
            
        act_seleccionada = st.selectbox("Actividad:", lista_opciones)
        req = df[df["Actividad"] == act_seleccionada]["Verificacion"].iloc[0]
        st.info(f"Requisito: **{req}**")

    with col_in2:
        foto = st.camera_input("Foto", label_visibility="collapsed")
        if foto:
            if st.button("🚀 ENVIAR Y ACTUALIZAR", type="primary"):
                with st.spinner("Procesando..."):
                    if enviar_evidencia(foto, act_seleccionada, PROYECTO_DEFAULT, usuario_seleccionado):
                        k = f"{usuario_seleccionado}_{act_seleccionada}"
                        curr = st.session_state["avances_sesion"].get(k, 0)
                        st.session_state["avances_sesion"][k] = curr + 1
                        st.success("✅ ¡Registrado!")
                        time.sleep(1)
                        st.rerun()