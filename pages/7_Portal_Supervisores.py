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

# ⚠️ TU URL DE APPS SCRIPT
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyOPWOWEfYE2itRcwvn0QTfMQLLKCm8l8qahBcKyResMzTPyKV5OiB23ZnO9iTEtqaX/exec"

LISTA_SUPERVISORES = [
    "Alioska Saavedra", "Carlos Araya", "Froilán Vargas", 
    "Juan de los Ríos", "Yorbin Valecillos"
]

# ==========================================
# 2. ESTILOS CSS V5.2 (FULL DASHBOARD + CORRECCIÓN MÓVIL)
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700&display=swap');
        
        /* --- A. TEMA GENERAL (OSCURO NEÓN) --- */
        .stApp { 
            background: linear-gradient(135deg, #05101a 0%, #0b2545 100%); 
            font-family: 'Montserrat', sans-serif; 
            color: white;
        }
        h1, h2, h3, h4, p, label, .stMarkdown { color: #FFFFFF !important; }

        /* --- B. CORRECCIÓN CRÍTICA MÓVIL (DESPLEGABLES) --- */
        /* Esta sección fuerza a que los menús desplegables sean BLANCOS con letras NEGRAS en el celular */
        
        /* 1. Caja del selector cerrada */
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: white !important;
        }
        .stSelectbox svg { fill: white !important; }

        /* 2. MENÚ DESPLEGADO (Aquí está la magia para el móvil) */
        div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-testid="stSelectboxVirtualDropdown"] {
            background-color: #ffffff !important; /* Fondo Blanco */
            border: 1px solid #ccc !important;
        }
        
        /* 3. TEXTO DE LAS OPCIONES (NEGRO FUERTE) */
        div[data-baseweb="popover"] li, div[data-baseweb="menu"] li, ul[data-testid="stSelectboxVirtualDropdown"] li {
            color: #000000 !important;
            background-color: white !important;
        }
        div[data-baseweb="popover"] span, ul[data-testid="stSelectboxVirtualDropdown"] span {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        
        /* Hover (cuando pasas el dedo) */
        div[data-baseweb="popover"] li:hover, ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
            background-color: #f0f2f5 !important;
            color: #004B8D !important;
        }

        /* --- C. BOTÓN BROWSE FILES (Visible en Móvil) --- */
        div[data-testid="stFileUploader"] button {
            color: #333333 !important; 
            background-color: #ffffff !important; 
            border: 1px solid #ccc !important;
            font-weight: bold !important;
        }
        div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] small {
             color: #e0e0e0 !important;
        }

        /* --- D. ESTILOS DEL DASHBOARD (GRÁFICOS Y TABLAS) --- */
        /* Tabla */
        div[data-testid="stDataFrame"] {
            background-color: rgba(255,255,255,0.05);
            padding: 10px; border-radius: 10px;
        }
        
        /* Botones */
        .stButton > button {
            background: linear-gradient(90deg, #00C9FF 0%, #004B8D 100%) !important; 
            color: white !important; border: none; border-radius: 50px; font-weight: bold; width: 100%;
            box-shadow: 0 4px 15px rgba(0, 75, 141, 0.3);
        }

        /* Métricas */
        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 201, 255, 0.3);
            border-radius: 10px; padding: 15px; text-align: center;
        }
        div[data-testid="stMetricLabel"] p { color: #e0e0e0 !important; font-size: 13px; }
        div[data-testid="stMetricValue"] div { color: #00C9FF !important; text-shadow: 0 0 10px rgba(0, 201, 255, 0.6); }

        /* --- E. LOGIN --- */
        div[data-testid="stForm"] {
            background-color: #ffffff !important; padding: 40px; border-radius: 20px;
        }
        div[data-testid="stForm"] * { color: #333333 !important; }
        div[data-testid="stForm"] input, div[data-testid="stForm"] div[data-baseweb="select"] > div {
            background-color: #f0f2f5 !important; color: #333333 !important; border: 1px solid #ccc !important;
        }
        div[data-testid="stForm"] div[data-baseweb="select"] span { color: #333333 !important; }

        /* Header Login */
        .login-header-card {
            background-color: #ffffff; border-radius: 20px; padding: 20px;
            text-align: center; margin-bottom: -30px; position: relative; z-index: 1;
        }
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
        st.markdown("<br><br>", unsafe_allow_html=True)
        ruta_logo = "assets/logo.png" if os.path.exists("assets/logo.png") else "../assets/logo.png"
        img_b64 = get_base64_image(ruta_logo)
        logo_html = f'<img src="data:image/png;base64,{img_b64}" width="200" style="display:block; margin:auto;">' if img_b64 else "<h1 style='color:#0b1c2c; text-align:center;'>🛡️</h1>"
        
        st.markdown(f"""
            <div class="login-header-card">
                {logo_html}
                <h2 style='margin-top:10px; font-weight:700; color: #0b1c2c !important;'>RMC CORPORATE</h2>
                <p style='font-weight:600; font-size:12px; letter-spacing:2px; color: #00C9FF !important;'>SECURE ACCESS V5.2</p>
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
    c_saludo, c_logout = st.columns([4, 1])
    with c_saludo: 
        st.markdown(f"### 👋 BIENVENIDO: <span style='color:#00C9FF;'>{usuario}</span>", unsafe_allow_html=True)
    with c_logout:
        if st.button("SALIR"):
            st.session_state.usuario_actual = None
            st.rerun()
    st.markdown("---")

    with st.spinner("Sincronizando satélite... 🛰️"):
        df_raw = cargar_datos_google(usuario)

    if df_raw is not None and not df_raw.empty:
        header_idx = None
        for i, row in df_raw.iterrows():
            if "NOMBRE DE LA ACTIVIDAD" in str(row.values):
                header_idx = i; break
        
        if header_idx is not None:
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = df_raw.iloc[header_idx]
            df.columns = df.columns.str.strip()
            col_map = {"NOMBRE DE LA ACTIVIDAD": "Actividad", "CANTIDAD ASIGNADA": "Programado", "CANTIDAD REALIZADA": "Realizado"}
            df = df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})
            
            if "Programado" in df.columns:
                df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
                df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
                df = df[df["Programado"] > 0]
                pct = (df["Realizado"].sum() / df["Programado"].sum() * 100) if df["Programado"].sum() > 0 else 0
                
                # --- AQUÍ ESTÁN TUS GRÁFICOS Y TABLAS DE VUELTA ---
                k1, k2, k3 = st.columns(3)
                k1.metric("META MENSUAL", int(df["Programado"].sum()))
                k2.metric("REALIZADO", int(df["Realizado"].sum()))
                k3.metric("AVANCE TOTAL", f"{pct:.1f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)

                c_viz, c_tab = st.columns([1, 2])
                with c_viz:
                    # Gráfico de Velocímetro
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=pct, 
                        gauge={'bar': {'color': "#00C9FF"}, 'axis': {'range': [None, 100], 'tickcolor':"white"}, 'bgcolor': "rgba(255,255,255,0.1)", 'bordercolor': "white"}, 
                        number={'font': {'color': "white"}}
                    ))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=280, margin=dict(t=30, b=10, l=30, r=30))
                    st.plotly_chart(fig, use_container_width=True)
                
                with c_tab:
                    # Tabla de datos
                    df["Estado"] = (df["Realizado"] / df["Programado"]) * 100
                    st.dataframe(df[["Actividad", "Programado", "Realizado", "Estado"]], 
                                 column_config={"Estado": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}, 
                                 hide_index=True, height=280)

                st.markdown("---")
                # Zona de Carga (Ahora abajo, como antes)
                st.markdown("""<div style="background-color: rgba(0, 201, 255, 0.1); padding: 10px; border-left: 5px solid #00C9FF; border-radius: 5px; margin-bottom: 20px;"><p style="margin: 0; color: white !important;">📸 <b>ZONA DE CARGA:</b> Puede seleccionar múltiples fotos.</p></div>""", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    df_pend = df[df["Realizado"] < df["Programado"]]
                    ops = df_pend["Actividad"].unique() if not df_pend.empty else df["Actividad"].unique()
                    act_sel = st.selectbox("SELECCIONE ACTIVIDAD:", ops)
                with c2:
                    archivos = st.file_uploader("CARGAR DOCUMENTOS (IMG):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
                    if archivos and st.button("ENVIAR TODO A BASE CENTRAL", type="primary"):
                        with st.spinner(f"Subiendo {len(archivos)} páginas..."):
                            if enviar_datos_y_fotos(usuario, act_sel, archivos):
                                st.success("✅ GUARDADO")
                                time.sleep(2)
                                st.rerun()
                            else: st.error("❌ ERROR")
        else: st.warning("⚠️ Sin datos.")