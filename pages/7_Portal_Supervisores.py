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
# 2. ESTILOS CSS AVANZADOS (NEÓN & CONTRASTE)
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700&display=swap');
        
        /* FONDO GENERAL */
        .stApp { 
            background: linear-gradient(135deg, #05101a 0%, #0b2545 100%); 
            font-family: 'Montserrat', sans-serif; 
        }

        /* --- TEXTOS GENERALES (FUERZA BRUTA A BLANCO) --- */
        h1, h2, h3, h4, p, span, div, label {
            color: #FFFFFF !important;
        }

        /* --- TARJETAS DE MÉTRICAS (KPIs) --- */
        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05); /* Fondo cristal oscuro */
            border: 1px solid rgba(0, 201, 255, 0.3);   /* Borde neón sutil */
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        
        /* ETIQUETA DE LA MÉTRICA (Ej: Meta Mensual) */
        div[data-testid="stMetricLabel"] > div > div > p {
            color: #e0e0e0 !important; /* Blanco hueso para leer bien */
            font-size: 16px !important;
            font-weight: 500 !important;
            text-transform: uppercase;
        }

        /* VALOR DE LA MÉTRICA (El número grande) */
        div[data-testid="stMetricValue"] > div {
            color: #00C9FF !important; /* CIAN NEÓN */
            font-size: 36px !important;
            font-weight: 700 !important;
            text-shadow: 0 0 10px rgba(0, 201, 255, 0.6); /* Resplandor */
        }

        /* --- INPUTS Y SELECTORES (DASHBOARD) --- */
        /* Fondo de los inputs para que se lea el texto blanco */
        div[data-baseweb="select"] > div, .stTextInput > div > div > input {
            background-color: rgba(20, 30, 50, 0.8) !important; 
            color: #ffffff !important;
            border: 1px solid #405a75 !important;
        }
        /* Texto dentro del selector */
        div[data-baseweb="select"] span {
            color: #ffffff !important;
        }

        /* --- TARJETA DE LOGIN (BLANCA) - EXCEPCIONES --- */
        .login-card {
            background-color: #ffffff !important;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
            text-align: center;
            margin-bottom: -20px;
        }
        /* Revertir colores a negro SOLO dentro del login */
        .login-card h2, .login-card h3, .login-card p { color: #0b1c2c !important; }
        
        /* Contenedor del formulario Login */
        div[data-testid="stForm"] {
            background-color: #ffffff !important;
            padding: 30px;
            border-radius: 20px;
        }
        /* Inputs del Login (Fondo claro texto oscuro) */
        div[data-testid="stForm"] input, div[data-testid="stForm"] div[data-baseweb="select"] > div {
             background-color: #f0f2f5 !important;
             color: #333 !important;
             border: 1px solid #ccc !important;
        }
        div[data-testid="stForm"] label p { color: #333 !important; }
        div[data-testid="stForm"] span { color: #333 !important; }

        /* --- BOTONES --- */
        .stButton > button {
            background: linear-gradient(90deg, #00C9FF 0%, #004B8D 100%); 
            color: white !important;
            border: none; border-radius: 50px; padding: 12px 24px; font-weight: bold;
            box-shadow: 0 0 15px rgba(0, 201, 255, 0.4);
        }
        .stButton > button:hover {
            transform: scale(1.03);
            box-shadow: 0 0 25px rgba(0, 201, 255, 0.7);
        }

        /* --- TABLA --- */
        div[data-testid="stDataFrame"] {
            background-color: rgba(255,255,255,0.05);
            padding: 10px;
            border-radius: 10px;
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

# --- LÓGICA DE PANTALLAS ---

# 1. LOGIN
if st.session_state.usuario_actual is None:
    c1, c_centro, c2 = st.columns([1, 1.5, 1])
    with c_centro:
        st.markdown("<br><br>", unsafe_allow_html=True)
        ruta_logo = "assets/logo.png" if os.path.exists("assets/logo.png") else "../assets/logo.png"
        img_b64 = get_base64_image(ruta_logo)
        logo_html = f'<img src="data:image/png;base64,{img_b64}" width="220" style="margin: 0 auto 20px auto; display: block;">' if img_b64 else "<h1 style='color:#0b1c2c !important'>🛡️</h1>"
        
        # Tarjeta Visual (HTML)
        st.markdown(f"""
            <div class="login-card">
                {logo_html}
                <h2 style='margin:0; font-size: 24px;'>RMC CORPORATE</h2>
                <p style='margin:0; font-size:13px; font-weight:600;'>SECURE ACCESS V4.2</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Formulario
        with st.form("login_form"):
            u = st.selectbox("OPERADOR:", LISTA_SUPERVISORES)
            p = st.text_input("CLAVE DE ACCESO:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("INICIAR SESIÓN >"):
                if verificar_login(u, p):
                    st.session_state.usuario_actual = u
                    st.rerun()
                else: st.error("❌ ACCESO DENEGADO")

# 2. DASHBOARD
else:
    usuario = st.session_state.usuario_actual
    
    # Header
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
                
                # --- MÉTRICAS (Ahora se verán en cajas de cristal con números neón) ---
                k1, k2, k3 = st.columns(3)
                k1.metric("META MENSUAL", int(df["Programado"].sum()))
                k2.metric("REALIZADO", int(df["Realizado"].sum()))
                k3.metric("AVANCE TOTAL", f"{pct:.1f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)

                # --- GRÁFICOS ---
                c_viz, c_tab = st.columns([1, 2])
                with c_viz:
                    # Configuración del gráfico para que tenga texto BLANCO
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=pct, 
                        gauge={
                            'bar': {'color': "#00C9FF"}, 
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                            'bgcolor': "rgba(255,255,255,0.1)",
                            'bordercolor': "white"
                        }, 
                        number={'font': {'color': "white"}}
                    ))
                    # Fondo transparente y fuente blanca global
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        font={'color': "white"}, 
                        height=280, 
                        margin=dict(t=30, b=10, l=30, r=30)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with c_tab:
                    df["Estado"] = (df["Realizado"] / df["Programado"]) * 100
                    st.dataframe(
                        df[["Actividad", "Programado", "Realizado", "Estado"]], 
                        column_config={"Estado": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}, 
                        hide_index=True, 
                        height=280
                    )

                st.markdown("---")
                # Alerta con estilo visible
                st.markdown("""
                    <div style="background-color: rgba(0, 201, 255, 0.1); padding: 10px; border-left: 5px solid #00C9FF; border-radius: 5px; margin-bottom: 20px;">
                        <p style="margin: 0; color: white !important;">📸 <b>ZONA DE CARGA:</b> Puede seleccionar múltiples fotos para documentos de varias páginas.</p>
                    </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    df_pend = df[df["Realizado"] < df["Programado"]]
                    ops = df_pend["Actividad"].unique() if not df_pend.empty else df["Actividad"].unique()
                    act_sel = st.selectbox("SELECCIONE ACTIVIDAD:", ops)
                with c2:
                    archivos = st.file_uploader("CARGAR DOCUMENTOS (IMG):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
                    
                    if archivos: 
                        if st.button("ENVIAR TODO A BASE CENTRAL", type="primary"):
                            with st.spinner(f"Subiendo {len(archivos)} páginas..."):
                                if enviar_datos_y_fotos(usuario, act_sel, archivos):
                                    st.success("✅ DOCUMENTO COMPLETO GUARDADO")
                                    time.sleep(2)
                                    st.rerun()
                                else: st.error("❌ ERROR EN LA TRANSMISIÓN")
        else: st.warning("⚠️ Sin datos.")