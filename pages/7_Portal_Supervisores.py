import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import base64
import time
import os
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="Portal SSO", page_icon="🛡️", layout="wide")

# ⚠️ TU URL DE APPS SCRIPT (Asegúrate de usar la V11 o la que te funcionó para subir fotos)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxcKOlYS7ad95T3ssPOVxWosKbUW-8VFfbEo7PYfTJvz5iXLHQhNUrKghLZhX8dRaxC/exec"

LISTA_SUPERVISORES = [
    "Alioska Saavedra", "Carlos Araya", "Froilán Vargas", 
    "Juan de los Rios", "Yorbin Valecillos"
]

# ==========================================
# 2. ESTILOS CSS V5.1 (BLINDAJE MÓVIL)
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700&display=swap');
        
        /* --- A. FONDO Y TEXTO GLOBAL --- */
        .stApp { 
            background: linear-gradient(135deg, #05101a 0%, #0b2545 100%); 
            font-family: 'Montserrat', sans-serif; 
            color: white;
        }
        h1, h2, h3, h4, p, label, .stMarkdown { color: #FFFFFF !important; }

        /* --- B. CORRECCIÓN CRÍTICA DE DESPLEGABLES (MÓVIL Y PC) --- */
        
        /* 1. La caja cerrada (Lo que ves antes de hacer clic) */
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: white !important; /* Texto blanco cuando está cerrado */
        }
        
        /* 2. El icono de la flechita */
        .stSelectbox svg { fill: white !important; }

        /* 3. LA LISTA DESPLEGABLE (MENÚ ABIERTO) */
        /* Apuntamos a todos los posibles contenedores que usa Streamlit/Mobile */
        div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-testid="stSelectboxVirtualDropdown"] {
            background-color: #ffffff !important; /* Fondo BLANCO Puro */
            border: 1px solid #ccc !important;
        }

        /* 4. LAS OPCIONES DE TEXTO (Dentro del menú abierto) */
        /* Forzamos negro a todos los niveles */
        div[data-baseweb="popover"] li, 
        div[data-baseweb="menu"] li,
        ul[data-testid="stSelectboxVirtualDropdown"] li {
            background-color: #ffffff !important;
            color: #000000 !important; /* TEXTO NEGRO */
        }
        
        div[data-baseweb="popover"] span, 
        div[data-baseweb="menu"] span,
        ul[data-testid="stSelectboxVirtualDropdown"] span {
            color: #000000 !important; /* TEXTO NEGRO (Doble seguridad) */
            font-weight: 500 !important;
        }

        /* Efecto Hover (cuando pasas el dedo/mouse) */
        div[data-baseweb="popover"] li:hover,
        ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
            background-color: #f0f2f5 !important;
            color: #004B8D !important;
        }

        /* --- C. BOTÓN BROWSE FILES --- */
        div[data-testid="stFileUploader"] button {
            color: #333333 !important; 
            background-color: #ffffff !important; 
            border: 1px solid #ccc !important;
            font-weight: bold !important;
        }
        div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] small {
             color: #e0e0e0 !important;
        }

        /* --- D. LOGIN (ESTILO CLARO) --- */
        div[data-testid="stForm"] {
            background-color: #ffffff !important;
            padding: 30px; border-radius: 20px;
        }
        div[data-testid="stForm"] * { color: #333333 !important; }
        div[data-testid="stForm"] input, div[data-testid="stForm"] div[data-baseweb="select"] > div {
            background-color: #f0f2f5 !important;
            color: #333333 !important;
            border: 1px solid #ccc !important;
        }
        /* Corrección específica para el selector DENTRO del login */
        div[data-testid="stForm"] div[data-baseweb="select"] span {
            color: #333333 !important;
        }

        /* --- E. BOTONES Y KPIs --- */
        .stButton > button {
            background: linear-gradient(90deg, #00C9FF 0%, #004B8D 100%) !important; 
            color: white !important; border: none; border-radius: 50px; font-weight: bold;
        }
        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 201, 255, 0.3);
            border-radius: 10px; padding: 10px; text-align: center;
        }
        div[data-testid="stMetricLabel"] p { color: #e0e0e0 !important; font-size: 13px; }
        div[data-testid="stMetricValue"] div { color: #00C9FF !important; }
        
        .login-header-card {
            background-color: #ffffff; border-radius: 20px; padding: 20px;
            text-align: center; margin-bottom: -20px; position: relative; z-index: 1;
        }
        .login-header-card h2 { color: #0b1c2c !important; }
        .login-header-card p { color: #00C9FF !important; }

    </style>
""", unsafe_allow_html=True)

if 'usuario_actual' not in st.session_state: st.session_state.usuario_actual = None

# --- FUNCIONES ---
def get_base64_image(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def verificar_login(usr, pwd):
    try:
        resp = requests.get(APPS_SCRIPT_URL, params={'accion': 'login', 'usuario': usr, 'password': str(pwd).strip()}, timeout=10)
        return resp.status_code == 200 and resp.json().get("resultado") == "OK"
    except: return False

def cargar_datos_google(sup):
    try:
        resp = requests.get(APPS_SCRIPT_URL, params={'supervisor': sup}, timeout=15)
        return pd.DataFrame(resp.json()) if resp.status_code == 200 else None
    except: return None

def enviar_datos_y_fotos(supervisor, actividad, lista_archivos):
    try:
        lista_b64 = []
        for archivo in lista_archivos:
            b64_str = base64.b64encode(archivo.getvalue()).decode('utf-8')
            lista_b64.append(b64_str)
        payload = {"supervisor": supervisor, "actividad": actividad, "imagenes": lista_b64}
        res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=60)
        return res.status_code == 200
    except: return False

# --- INTERFAZ ---
if st.session_state.usuario_actual is None:
    c1, c_centro, c2 = st.columns([1, 1.5, 1])
    with c_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        ruta_logo = "assets/logo.png" if os.path.exists("assets/logo.png") else "../assets/logo.png"
        img_b64 = get_base64_image(ruta_logo)
        logo_html = f'<img src="data:image/png;base64,{img_b64}" width="180" style="display:block; margin:auto;">' if img_b64 else "<h1 style='color:#0b1c2c; text-align:center;'>🛡️</h1>"
        
        st.markdown(f"""
            <div class="login-header-card">
                {logo_html}
                <h2 style='margin-top:10px; font-weight:700; font-size:22px;'>RMC CORPORATE</h2>
                <p style='font-weight:600; font-size:12px; letter-spacing:2px;'>PORTAL MÓVIL V5.1</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.selectbox("OPERADOR:", LISTA_SUPERVISORES)
            p = st.text_input("CLAVE DE ACCESO:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("INICIAR SESIÓN >"):
                if verificar_login(u, p):
                    st.session_state.usuario_actual = u
                    st.rerun()
                else: st.error("❌ ACCESO DENEGADO")

else:
    usuario = st.session_state.usuario_actual
    c_saludo, c_logout = st.columns([3, 1])
    with c_saludo: 
        st.markdown(f"### 👋 <span style='color:#00C9FF;'>{usuario}</span>", unsafe_allow_html=True)
    with c_logout:
        if st.button("SALIR"):
            st.session_state.usuario_actual = None
            st.rerun()
    st.markdown("---")

    # MÓDULO DE CARGA DE EVIDENCIA (PRIORIDAD MÓVIL: ARRIBA)
    st.markdown("### 📸 CARGA DE EVIDENCIA")
    st.markdown("""<div style="background-color: rgba(0, 201, 255, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 15px;"><p style="margin: 0; color: white !important; font-size: 13px;">☝️ <b>TIP:</b> Puedes subir varias fotos a la vez.</p></div>""", unsafe_allow_html=True)

    with st.spinner("Cargando actividades..."):
        df_raw = cargar_datos_google(usuario)

    if df_raw is not None and not df_raw.empty:
        header_idx = None
        for i, row in df_raw.iterrows():
            if "NOMBRE DE LA ACTIVIDAD" in str(row.values): header_idx = i; break
        
        if header_idx is not None:
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = df_raw.iloc[header_idx]
            col_map = {"NOMBRE DE LA ACTIVIDAD": "Actividad", "CANTIDAD ASIGNADA": "Programado", "CANTIDAD REALIZADA": "Realizado"}
            df = df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})
            
            # Selector de Actividad
            df_pend = df # Mostrar todas por ahora para facilitar
            ops = df_pend["Actividad"].unique()
            
            # --- FORMULARIO DE CARGA ---
            act_sel = st.selectbox("SELECCIONE ACTIVIDAD:", ops)
            archivos = st.file_uploader("TOMAR FOTO O SELECCIONAR:", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
            
            if archivos:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📤 ENVIAR REPORTE AHORA", type="primary"):
                    with st.spinner(f"Subiendo {len(archivos)} fotos..."):
                        if enviar_datos_y_fotos(usuario, act_sel, archivos):
                            st.balloons()
                            st.success("✅ ¡RECIBIDO CORRECTAMENTE!")
                            time.sleep(2)
                            st.rerun()
                        else: st.error("❌ ERROR DE CONEXIÓN")
            
            st.markdown("---")
            
            # --- RESUMEN DE AVANCE (KPIs) ---
            if "Programado" in df.columns:
                df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
                df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
                df = df[df["Programado"] > 0]
                pct = (df["Realizado"].sum() / df["Programado"].sum() * 100) if df["Programado"].sum() > 0 else 0
                
                st.markdown("#### 📊 MI AVANCE MENSUAL")
                k1, k2, k3 = st.columns(3)
                k1.metric("META", int(df["Programado"].sum()))
                k2.metric("LISTO", int(df["Realizado"].sum()))
                k3.metric("%", f"{pct:.0f}%")

    else: st.warning("⚠️ No se pudo cargar tu lista de actividades.")