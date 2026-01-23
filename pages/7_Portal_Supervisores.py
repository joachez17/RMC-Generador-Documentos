import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import base64
import time
import os
from datetime import date

st.set_page_config(page_title="Portal SSO", page_icon="🛡️", layout="wide")

# ⚠️ TU NUEVA URL AQUÍ
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxcKOlYS7ad95T3ssPOVxWosKbUW-8VFfbEo7PYfTJvz5iXLHQhNUrKghLZhX8dRaxC/exec"

LISTA_SUPERVISORES = [
    "Alioska Saavedra", "Carlos Araya", "Froilán Vargas", 
    "Juan de los Rios", "Yorbin Valecillos"
]

# --- ESTILOS (Mantenemos tu diseño blanco y limpio) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700&display=swap');
        .stApp { background: linear-gradient(135deg, #0b1c2c 0%, #112D4E 100%); font-family: 'Montserrat', sans-serif; }
        
        .login-card {
            background-color: #ffffff; border-radius: 20px; padding: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); text-align: center; animation: fadeIn 1s ease-in;
        }
        .login-card h2, .login-card h3 { color: #0b1c2c !important; text-transform: uppercase; font-weight: 700; }
        .login-card p { color: #00C9FF !important; }
        
        div[data-baseweb="select"] > div, .stTextInput > div > div > input {
            background-color: #f0f2f5 !important; color: #333 !important;
            border: 1px solid #dce0e4 !important; border-bottom: 2px solid #00C9FF !important; border-radius: 8px !important;
        }
        .stButton > button {
            background: linear-gradient(90deg, #0b1c2c 0%, #004B8D 100%); color: white;
            border: none; border-radius: 50px; padding: 12px 24px; font-weight: bold; width: 100%;
            box-shadow: 0 4px 15px rgba(11, 28, 44, 0.3); transition: all 0.3s ease;
        }
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(11, 28, 44, 0.4); background: linear-gradient(90deg, #004B8D 0%, #00C9FF 100%); }
        
        /* Estilos Dashboard */
        h1, h2, h3, .stMarkdown p { color: #FFFFFF !important; }
        .stMetricLabel { color: #cfd8dc !important; }
        
        @keyframes fadeIn { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
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

# MODIFICADO: Ahora recibe una LISTA de archivos
def enviar_datos_y_fotos(supervisor, actividad, lista_archivos):
    try:
        lista_b64 = []
        # Convertir cada archivo a Base64
        for archivo in lista_archivos:
            b64_str = base64.b64encode(archivo.getvalue()).decode('utf-8')
            lista_b64.append(b64_str)
        
        # Enviar lista de imagenes
        payload = {
            "supervisor": supervisor,
            "actividad": actividad,
            "imagenes": lista_b64 # <-- Array
        }
        res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=60) # Timeout mayor por si son muchas fotos
        return res.status_code == 200
    except: return False

# --- INTERFAZ ---
if st.session_state.usuario_actual is None:
    c1, c_centro, c2 = st.columns([1, 1.5, 1])
    with c_centro:
        st.markdown("<br><br>", unsafe_allow_html=True)
        ruta_logo = "assets/logo.png" if os.path.exists("assets/logo.png") else "../assets/logo.png"
        img_b64 = get_base64_image(ruta_logo)
        logo_html = f'<img src="data:image/png;base64,{img_b64}" width="220" style="margin: 0 auto 20px auto; display: block;">' if img_b64 else "<h1>🛡️</h1>"
        
        st.markdown(f"""<div class="login-card">{logo_html}<h2 style='margin:0;'>RMC CORPORATE</h2><p style='margin:0; font-size:13px; font-weight:600;'>SECURE ACCESS V4.0</p></div>""", unsafe_allow_html=True)
        
        with st.container():
             st.markdown("""<style>div[data-testid="stForm"] {background-color: #ffffff; padding: 30px; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-top: -20px; position: relative; z-index: 1;}</style>""", unsafe_allow_html=True)
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
    with c_saludo: st.markdown(f"### 👋 OPERADOR: <span style='color:#00C9FF'>{usuario}</span>", unsafe_allow_html=True)
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
                k1, k2, k3 = st.columns(3)
                k1.metric("META MENSUAL", int(df["Programado"].sum()))
                k2.metric("REALIZADO", int(df["Realizado"].sum()))
                k3.metric("AVANCE TOTAL", f"{pct:.1f}%")
                st.markdown("<br>", unsafe_allow_html=True)

                c_viz, c_tab = st.columns([1, 2])
                with c_viz:
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=pct, gauge={'bar': {'color': "#00C9FF"}, 'axis': {'range': [None, 100]}, 'bgcolor': "rgba(255,255,255,0.1)"}, number={'font': {'color': "white"}}))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=250, margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                with c_tab:
                    df["Estado"] = (df["Realizado"] / df["Programado"]) * 100
                    st.dataframe(df[["Actividad", "Programado", "Realizado", "Estado"]], column_config={"Estado": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}, hide_index=True, height=250)

                st.markdown("---")
                st.markdown("### 📸 SUBIR EVIDENCIA (MULTIPAGE)")
                st.info("💡 Puede seleccionar varias fotos a la vez (Ej: Las 4 hojas del AST).")

                c1, c2 = st.columns(2)
                with c1:
                    df_pend = df[df["Realizado"] < df["Programado"]]
                    ops = df_pend["Actividad"].unique() if not df_pend.empty else df["Actividad"].unique()
                    act_sel = st.selectbox("SELECCIONE ACTIVIDAD:", ops)
                with c2:
                    # CAMBIO CLAVE: file_uploader en lugar de camera_input
                    archivos = st.file_uploader("CARGAR DOCUMENTOS:", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
                    
                    if archivos and st.button("ENVIAR TODO A BASE CENTRAL", type="primary"):
                        with st.spinner(f"Subiendo {len(archivos)} páginas..."):
                            if enviar_datos_y_fotos(usuario, act_sel, archivos):
                                st.success("✅ DOCUMENTO COMPLETO GUARDADO")
                                time.sleep(2)
                                st.rerun()
                            else: st.error("❌ ERROR EN LA TRANSMISIÓN")
        else: st.warning("⚠️ Sin datos.")