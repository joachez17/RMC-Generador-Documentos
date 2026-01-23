import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import base64
import time
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Portal SSO", page_icon="C:\JoacoScope\assets\logo.png", layout="wide")

# ⚠️ TU URL DE APPS SCRIPT
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxcKOlYS7ad95T3ssPOVxWosKbUW-8VFfbEo7PYfTJvz5iXLHQhNUrKghLZhX8dRaxC/exec" 

# Lista de supervisores
LISTA_SUPERVISORES = [
    "Alioska Saavedra", 
    "Carlos Araya", 
    "Froilán Vargas", 
    "Juan de los Rios", 
    "Yorbin Valecillos"
]

# ESTILOS FUTURISTAS (RMC CORPORATE)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #0b1c2c 0%, #112D4E 100%);
            font-family: 'Montserrat', sans-serif;
        }
        
        /* Tarjeta Login Glassmorphism */
        .login-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            text-align: center;
        }

        /* Textos */
        h1, h2, h3 { color: #FFFFFF !important; text-transform: uppercase; letter-spacing: 1px; }
        p, label { color: #cfd8dc !important; }
        
        /* Inputs */
        div[data-baseweb="select"] > div, .stTextInput > div > div > input {
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: none !important;
            border-bottom: 2px solid #00C9FF !important;
        }

        /* Botones */
        .stButton > button {
            background: linear-gradient(90deg, #004B8D 0%, #00C9FF 100%);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 12px 24px;
            font-weight: bold;
            box-shadow: 0 0 15px rgba(0, 201, 255, 0.3);
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 25px rgba(0, 201, 255, 0.6);
        }
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE SESIÓN ---
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

# ==========================================
# 2. FUNCIONES ROBUSTAS (ANTI-ERRORES)
# ==========================================

def verificar_login(usuario, password):
    """Verifica credenciales limpiando espacios en blanco"""
    try:
        # .strip() elimina espacios accidentales al inicio o final
        password_limpia = str(password).strip()
        
        resp = requests.get(APPS_SCRIPT_URL, params={
            'accion': 'login', 
            'usuario': usuario, 
            'password': password_limpia
        }, timeout=10) # Timeout para evitar bloqueos
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("resultado") == "OK":
                return True
        return False
    except Exception as e:
        print(f"Error login: {e}") # Solo para consola
        return False

def cargar_datos_google(supervisor):
    try:
        response = requests.get(APPS_SCRIPT_URL, params={'supervisor': supervisor}, timeout=15)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return None
    except: return None

def enviar_datos_y_foto(supervisor, actividad, foto_buffer):
    try:
        foto_b64 = base64.b64encode(foto_buffer.getvalue()).decode('utf-8')
        # Sanitizar nombre de archivo por si la actividad tiene caracteres raros
        nombre_safe = actividad.replace("/", "-").replace("\\", "-")
        
        payload = {
            "supervisor": supervisor,
            "actividad": actividad,
            "imagen": foto_b64,
            "nombreArchivo": f"{nombre_safe}.jpg"
        }
        res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=30)
        return res.status_code == 200
    except: return False

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================

# A. PANTALLA DE LOGIN
if st.session_state.usuario_actual is None:
    c1, c_centro, c2 = st.columns([1, 2, 1])
    with c_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        # Tarjeta Visual HTML
        st.markdown("""
            <div class="login-card">
                <h1 style='font-size: 50px;'>🛡️</h1>
                <h2>RMC CORPORATE</h2>
                <p style='color: #00C9FF !important; margin-top: -10px;'>SECURE ACCESS V2.1</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Formulario
        with st.form("login_form"):
            st.markdown("<br>", unsafe_allow_html=True)
            user_input = st.selectbox("OPERADOR:", LISTA_SUPERVISORES)
            pass_input = st.text_input("CLAVE DE ACCESO:", type="password")
            
            submitted = st.form_submit_button("INICIAR SESIÓN >")
            
            if submitted:
                # Aquí aplicamos la limpieza automática
                if verificar_login(user_input, pass_input):
                    st.success(f"✅ ACCESO AUTORIZADO. BIENVENIDO {user_input.split()[0].upper()}.")
                    st.session_state.usuario_actual = user_input
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ ACCESO DENEGADO. Verifique su clave.")

# B. PANTALLA DASHBOARD (LOGUEADO)
else:
    usuario = st.session_state.usuario_actual
    
    # Header
    c_saludo, c_logout = st.columns([4, 1])
    with c_saludo:
        st.markdown(f"### 👋 OPERADOR: <span style='color:#00C9FF'>{usuario}</span>", unsafe_allow_html=True)
    with c_logout:
        if st.button("CERRAR SESIÓN"):
            st.session_state.usuario_actual = None
            st.rerun()
            
    st.markdown("---")

    # Carga de datos
    with st.spinner("Sincronizando satélite... 🛰️"):
        df_raw = cargar_datos_google(usuario)

    if df_raw is not None and not df_raw.empty:
        # Lógica de procesamiento de datos (Mantenida intacta)
        header_idx = None
        for i, row in df_raw.iterrows():
            if "NOMBRE DE LA ACTIVIDAD" in str(row.values):
                header_idx = i
                break
        
        if header_idx is not None:
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = df_raw.iloc[header_idx]
            df.columns = df.columns.str.strip()
            
            col_map = {"NOMBRE DE LA ACTIVIDAD": "Actividad", "CANTIDAD ASIGNADA": "Programado", "CANTIDAD REALIZADA": "Realizado", "MEDIO DE VERIFICACIÓN": "Verificacion"}
            df = df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})
            
            if "Programado" in df.columns:
                df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
                df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
                df = df[df["Programado"] > 0]
                
                # KPIs
                total_prog = int(df["Programado"].sum())
                total_real = int(df["Realizado"].sum())
                pct = (total_real / total_prog * 100) if total_prog > 0 else 0
                
                k1, k2, k3 = st.columns(3)
                k1.metric("META MENSUAL", total_prog)
                k2.metric("REALIZADO", total_real)
                k3.metric("AVANCE TOTAL", f"{pct:.1f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Gráficos
                c_viz, c_tab = st.columns([1, 2])
                with c_viz:
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=pct, 
                                               gauge={'bar': {'color': "#00C9FF"}, 'axis': {'range': [None, 100]}, 'bgcolor': "rgba(255,255,255,0.1)"},
                                               number={'font': {'color': "white"}}))
                    fig.update_layout(paper_bgcolor = "rgba(0,0,0,0)", plot_bgcolor = "rgba(0,0,0,0)", font={'color': "white"}, height=250, margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                with c_tab:
                    df["Estado"] = (df["Realizado"] / df["Programado"]) * 100
                    st.dataframe(df[["Actividad", "Programado", "Realizado", "Estado"]], 
                                 column_config={"Estado": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)},
                                 hide_index=True, height=250)

                # Input Evidencia
                st.markdown("---")
                st.markdown("### 📸 SUBIR EVIDENCIA")
                c1, c2 = st.columns(2)
                with c1:
                    df_pend = df[df["Realizado"] < df["Programado"]]
                    ops = df_pend["Actividad"].unique() if not df_pend.empty else df["Actividad"].unique()
                    act_sel = st.selectbox("SELECCIONE ACTIVIDAD:", ops)
                with c2:
                    foto = st.camera_input("TOMAR FOTO")
                    if foto and st.button("ENVIAR A BASE CENTRAL", type="primary"):
                        with st.spinner("Transmitiendo datos..."):
                            if enviar_datos_y_foto(usuario, act_sel, foto):
                                st.success("✅ DATOS GUARDADOS EN DRIVE Y SHEET")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ ERROR EN LA TRANSMISIÓN")
        else:
            st.warning("⚠️ No se encontraron datos. Verifique la Planilla Maestra.")