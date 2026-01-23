import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import date
import time

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Portal Supervisores", page_icon="🛡️", layout="wide")

# ⚠️ PEGA AQUÍ LA URL QUE TE DIO GOOGLE APPS SCRIPT
# Debe verse algo como: "https://script.google.com/macros/s/AKfycbx.../exec"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwgNAYHuXEQVLtEd1ZEiYiNjpjogkbkvRH8iWBsrp581RNYDXggnIxqQcGd4Of8ZY-J/exec" 

# Lista de supervisores (deben coincidir con las pestañas del Sheet)
LISTA_SUPERVISORES = [
    "Alioska Saavedra", "Carlos Araya", "Froilán Vargas", 
    "Juan de los Rios", "Yorbin Valecillos"
]

PROYECTO_DEFAULT = "RMC PLAN ACTIVIDADES"

# Estilos CSS (Igual que antes)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
        .stApp { background-color: #f4f6f9; }
        .selector-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #004B8D; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
        div.stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }
        .stButton>button { background-color: #004B8D; color: white; border-radius: 8px; border: none; padding: 10px 24px; font-weight: bold; width: 100%; transition: all 0.3s ease; }
        .stButton>button:hover { background-color: #003666; box-shadow: 0 4px 8px rgba(0,0,0,0.2); color: white; }
        h1, h2, h3, h4, h5 { color: #004B8D; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNCIONES DE CONEXIÓN (API GOOGLE)
# ==========================================

def cargar_datos_google(supervisor):
    """Descarga los datos en tiempo real desde Google Sheet"""
    try:
        # Hacemos la petición GET al script
        response = requests.get(APPS_SCRIPT_URL, params={'supervisor': supervisor})
        
        if response.status_code == 200:
            data = response.json()
            # Convertimos la lista de listas en DataFrame
            df_raw = pd.DataFrame(data)
            return df_raw
        else:
            st.error(f"Error conectando a Google: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def actualizar_google(supervisor, actividad, foto_buffer):
    """Manda la foto y el dato a Google Script para que organice todo"""
    try:
        # 1. Convertir la foto a texto (Base64) para poder enviarla por internet
        foto_bytes = foto_buffer.getvalue()
        foto_b64 = base64.b64encode(foto_bytes).decode('utf-8')
        
        # 2. Empaquetar todo
        payload = {
            "supervisor": supervisor,
            "actividad": actividad,
            "imagen": foto_b64,
            "nombreArchivo": f"{actividad}.jpg"
        }
        
        # 3. Enviar al Script
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error Google: {response.text}")
            return False
            
    except Exception as e:
        st.error(f"Error enviando datos: {e}")
        return False

def enviar_correo_evidencia(foto, actividad, proyecto, usuario):
    # (Tu función de correo original se mantiene igual para enviar la foto)
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
        body = f"Evidencia cargada.\nActividad: {actividad}\nSupervisor: {usuario}\nFecha: {date.today()}"
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
        st.error(f"Error correo: {e}")
        return False

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================

st.markdown("<h2 style='color: #004B8D;'>🛡️ Portal de Gestión SSO (Online)</h2>", unsafe_allow_html=True)

# SELECCIÓN
st.markdown('<div class="selector-box">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 3])
with c1: st.write("### 👤 Supervisor")
with c2: usuario_seleccionado = st.selectbox("Nombre:", LISTA_SUPERVISORES, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# CARGA DE DATOS
with st.spinner(f"Conectando con Google Sheets de {usuario_seleccionado}..."):
    df_raw = cargar_datos_google(usuario_seleccionado)

if df_raw is not None and not df_raw.empty:
    # PROCESAMIENTO INTELIGENTE (Igual que hacíamos con Excel, pero ahora con datos de la nube)
    header_row_idx = None
    # Iteramos filas para encontrar "NOMBRE DE LA ACTIVIDAD"
    for i, row in df_raw.iterrows():
        row_str = row.astype(str).str.cat(sep=' ')
        if "NOMBRE DE LA ACTIVIDAD" in row_str:
            header_row_idx = i
            break
            
    if header_row_idx is not None:
        # Reconstruimos el DataFrame usando la fila detectada como header
        df = df_raw.iloc[header_row_idx + 1:].copy()
        df.columns = df_raw.iloc[header_row_idx]
        
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip() # Quitar espacios extra
        
        # Renombrar a nuestro estándar
        col_map = {
            "NOMBRE DE LA ACTIVIDAD": "Actividad",
            "CANTIDAD ASIGNADA": "Programado",
            "CANTIDAD REALIZADA": "Realizado",
            "MEDIO DE VERIFICACIÓN": "Verificacion"
        }
        # Solo renombramos si existen
        df = df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})
        
        # Validar que existan las clave
        if "Programado" in df.columns and "Realizado" in df.columns:
            # Convertir a números
            df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
            df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
            
            # Filtro Obligatorias
            df = df[df["Programado"] > 0]
            
            # --- DASHBOARD ---
            total_prog = int(df["Programado"].sum())
            total_real = int(df["Realizado"].sum())
            pct = (total_real / total_prog * 100) if total_prog > 0 else 0
            if pct > 100: pct = 100
            
            # Métricas
            c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
            with c_kpi1: st.metric("📍 Meta Mes", total_prog)
            with c_kpi2: st.metric("✅ Realizado (Nube)", total_real)
            with c_kpi3: st.metric("🚀 Avance", f"{pct:.1f}%")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Gráfico y Tabla
            c_viz, c_tab = st.columns([1, 2])
            with c_viz:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = pct,
                    number = {'suffix': "%", 'font': {'size': 40, 'color': "#004B8D"}},
                    gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#004B8D"}}
                ))
                fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
                
            with c_tab:
                df["Avance_Pct"] = (df["Realizado"] / df["Programado"]) * 100
                st.dataframe(
                    df[["Actividad", "Programado", "Realizado", "Avance_Pct"]],
                    column_config={
                        "Avance_Pct": st.column_config.ProgressColumn("Estado", format="%d%%", min_value=0, max_value=100)
                    },
                    use_container_width=True, hide_index=True, height=300
                )
            
            # --- ZONA DE CARGA ---
            st.markdown("---")
            st.markdown("### 📸 Subir Evidencia (Actualiza Google Sheet)")
            
            c_input1, c_input2 = st.columns(2)
            with c_input1:
                df_pend = df[df["Realizado"] < df["Programado"]]
                opciones = df_pend["Actividad"].unique() if not df_pend.empty else df["Actividad"].unique()
                act_sel = st.selectbox("Actividad:", opciones)
                
                # Buscar requisito
                if "Verificacion" in df.columns:
                    req = df[df["Actividad"] == act_sel]["Verificacion"].iloc[0]
                    st.info(f"Requisito: {req}")
            
            with c_input2:
                foto = st.camera_input("Evidencia")
                if foto:
                    if st.button("🚀 ENVIAR Y GRABAR EN DRIVE", type="primary"):
                        with st.spinner("Subiendo foto y actualizando planilla..."):
                            # 1. Enviar Correo (Foto)
                            envio_ok = enviar_correo_evidencia(foto, act_sel, PROYECTO_DEFAULT, usuario_seleccionado)
                            
                            # 2. Actualizar Google Sheet Dato
                            update_ok = actualizar_google(usuario_seleccionado, act_sel, foto)
                            
                            if update_ok:
                                st.success("✅ ¡Éxito! Planilla actualizada en tiempo real.")
                                time.sleep(2)
                                st.rerun() # Recargar para ver el cambio REAL
                            else:
                                st.warning("⚠️ La foto se envió, pero hubo un error actualizando la planilla.")
        else:
            st.error("No encontré las columnas 'Programado'/'Realizado'. Revisa los nombres en el Sheet.")
    else:
        st.error("No encontré la fila 'NOMBRE DE LA ACTIVIDAD' en el Sheet.")
else:
    st.error("Error al cargar datos. Verifica la URL del Apps Script.")