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
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxcKOlYS7ad95T3ssPOVxWosKbUW-8VFfbEo7PYfTJvz5iXLHQhNUrKghLZhX8dRaxC/exec"

LISTA_SUPERVISORES = [
    "Alioska Saavedra", "Carlos Araya", "Froilán Vargas", 
    "Juan de los Rios", "Yorbin Valecillos"
]

# ==========================================
# 2. ESTILOS CSS INTELIGENTES (DUAL THEME)
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700&display=swap');
        
        /* --- A. TEMA GLOBAL (DASHBOARD OSCURO) --- */
        .stApp { 
            background: linear-gradient(135deg, #05101a 0%, #0b2545 100%); 
            font-family: 'Montserrat', sans-serif; 
        }

        /* Por defecto: TODO EL TEXTO ES BLANCO (Para el Dashboard) */
        h1, h2, h3, h4, p, span, div, label { color: #FFFFFF; }
        
        /* Inputs del Dashboard (Transparentes) */
        .stTextInput > div > div > input, div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.1); 
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
        }

        /* --- B. EXCEPCIÓN: LOGIN (TEMA CLARO) --- */
        
        /* 1. Contenedor Blanco del Formulario */
        div[data-testid="stForm"] {
            background-color: #ffffff !important;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }

        /* 2. FORZAR TEXTO NEGRO DENTRO DEL FORMULARIO */
        div[data-testid="stForm"] label p, 
        div[data-testid="stForm"] h1, 
        div[data-testid="stForm"] h2, 
        div[data-testid="stForm"] p {
            color: #333333 !important; /* Gris Oscuro */
        }
        
        /* 3. INPUTS DENTRO DEL LOGIN (Gris Claro, Texto Negro) */
        div[data-testid="stForm"] input {
            background-color: #f0f2f5 !important;
            color: #333333 !important;
            border: 1px solid #ccc !important;
        }
        div[data-testid="stForm"] div[data-baseweb="select"] > div {
            background-color: #f0f2f5 !important;
            color: #333333 !important;
            border: 1px solid #ccc !important;
        }
        /* Texto de la opción seleccionada en el login */
        div[data-testid="stForm"] div[data-baseweb="select"] span {
            color: #333333 !important;
        }

        /* 4. BOTÓN (Visible en ambos modos) */
        .stButton > button {
            background: linear-gradient(90deg, #00C9FF 0%, #004B8D 100%) !important; 
            color: white !important;
            border: none; 
            border-radius: 50px; 
            padding: 12px 24px; 
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0, 75, 141, 0.3);
            width: 100%;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(0, 201, 255, 0.6);
        }
        
        /* --- C. MÉTRICAS NEÓN (DASHBOARD) --- */
        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 201, 255, 0.3);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        div[data-testid="stMetricLabel"] p { color: #e0e0e0 !important; font-size: 14px; }
        div[data-testid="stMetricValue"] div { color: #00C9FF !important; text-shadow: 0 0 10px rgba(0, 201, 255, 0.6); }

        /* Estilo Tarjeta Título Login */
        .login-header-card {
            background-color: #ffffff;
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            margin-bottom: -30px; /* Pegado al formulario */
            position: relative;
            z-index: 1;
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
    # LOGIN SCREEN
    c1, c_centro, c2 = st.columns([1, 1.5, 1])
    with c_centro:
        st.markdown("<br><br>", unsafe_allow_html=True)
        ruta_logo = "assets/logo.png" if os.path.exists("assets/logo.png") else "../assets/logo.png"
        img_b64 = get_base64_image(ruta_logo)
        logo_html = f'<img src="data:image/png;base64,{img_b64}" width="200" style="display:block; margin:auto;">' if img_b64 else "<h1 style='color:#0b1c2c; text-align:center;'>🛡️</h1>"
        
        # Tarjeta de Encabezado (Blanca)
        st.markdown(f"""
            <div class="login-header-card">
                {logo_html}
                <h2 style='margin-top:10px; font-weight:700;'>RMC CORPORATE</h2>
                <p style='font-weight:600; font-size:12px; letter-spacing:2px;'>SECURE ACCESS V4.3</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Formulario (Estilizado por CSS para ser blanco por dentro)
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
    # DASHBOARD SCREEN
    usuario = st.session_state.usuario_actual
    
    c_saludo, c_logout = st.columns([4, 1])
    with c_saludo: 
        st.markdown(f"### 👋 BIENVENIDO: <span style='color:#00C9FF; text-shadow: 0 0 10px rgba(0,201,255,0.7);'>{usuario}</span>", unsafe_allow_html=True)
    with c_logout:
        if st.button("CERRAR SESIÓN"):
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
                
                # KPIs Neón
                k1, k2, k3 = st.columns(3)
                k1.metric("META MENSUAL", int(df["Programado"].sum()))
                k2.metric("REALIZADO", int(df["Realizado"].sum()))
                k3.metric("AVANCE TOTAL", f"{pct:.1f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)

                # Gráficos (Texto Blanco)
                c_viz, c_tab = st.columns([1, 2])
                with c_viz:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=pct, 
                        gauge={'bar': {'color': "#00C9FF"}, 'axis': {'range': [None, 100], 'tickcolor':"white"}, 'bgcolor': "rgba(255,255,255,0.1)", 'bordercolor': "white"}, 
                        number={'font': {'color': "white"}}
                    ))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=280, margin=dict(t=30, b=10, l=30, r=30))
                    st.plotly_chart(fig, use_container_width=True)
                
                with c_tab:
                    df["Estado"] = (df["Realizado"] / df["Programado"]) * 100
                    st.dataframe(df[["Actividad", "Programado", "Realizado", "Estado"]], 
                                 column_config={"Estado": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}, 
                                 hide_index=True, height=280)

                st.markdown("---")
                st.markdown("""
                    <div style="background-color: rgba(0, 201, 255, 0.1); padding: 10px; border-left: 5px solid #00C9FF; border-radius: 5px; margin-bottom: 20px;">
                        <p style="margin: 0; color: white !important;">📸 <b>ZONA DE CARGA:</b> Puede seleccionar múltiples fotos.</p>
                    </div>
                """, unsafe_allow_html=True)

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