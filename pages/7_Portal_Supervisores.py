import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import base64
import time
import os
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Portal SSO", page_icon="🛡️", layout="wide")

# ⚠️ TU URL DE APPS SCRIPT
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxcKOlYS7ad95T3ssPOVxWosKbUW-8VFfbEo7PYfTJvz5iXLHQhNUrKghLZhX8dRaxC/exec" 

LISTA_SUPERVISORES = [
    "Alioska Saavedra", "Carlos Araya", "Froilán Vargas", 
    "Juan de los Rios", "Yorbin Valecillos"
]

# ESTILOS FUTURISTAS Y LIMPIOS (RMC CORPORATE)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;500;700&display=swap');
        
        /* Fondo general oscuro */
        .stApp {
            background: linear-gradient(135deg, #0b1c2c 0%, #112D4E 100%);
            font-family: 'Montserrat', sans-serif;
        }
        
        /* Tarjeta Login BLANCA */
        .login-card {
            background-color: #ffffff; /* Fondo blanco sólido */
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); /* Sombra para resaltar */
            text-align: center;
            animation: fadeIn 1s ease-in;
        }

        /* Textos dentro de la tarjeta (ahora oscuros) */
        .login-card h2, .login-card h3 { 
            color: #0b1c2c !important; /* Azul oscuro corporativo */
            text-transform: uppercase; 
            letter-spacing: 1px; 
            font-weight: 700;
        }
        .login-card p { 
            color: #00C9FF !important; /* Cian para el subtítulo */
        }
        /* Etiquetas del formulario */
        .stMarkdown label p {
            color: #4a5a6a !important; /* Gris oscuro */
            font-weight: 500;
        }
        
        /* Inputs (diseño limpio para fondo blanco) */
        div[data-baseweb="select"] > div, .stTextInput > div > div > input {
            background-color: #f0f2f5 !important; /* Fondo gris muy claro */
            color: #333 !important; /* Texto oscuro */
            border: 1px solid #dce0e4 !important; /* Borde sutil */
            border-bottom: 2px solid #00C9FF !important; /* Acento cian abajo */
            border-radius: 8px !important;
        }

        /* Botones */
        .stButton > button {
            background: linear-gradient(90deg, #0b1c2c 0%, #004B8D 100%); /* Gradiente azul corporativo */
            color: white;
            border: none;
            border-radius: 50px;
            padding: 12px 24px;
            font-weight: bold;
            letter-spacing: 1px;
            box-shadow: 0 4px 15px rgba(11, 28, 44, 0.3);
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(11, 28, 44, 0.4);
            background: linear-gradient(90deg, #004B8D 0%, #00C9FF 100%); /* Se ilumina al pasar el mouse */
        }
        
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE SESIÓN ---
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

# ==========================================
# 2. FUNCIONES ROBUSTAS
# ==========================================

def get_base64_image(image_path):
    """Convierte la imagen a código para mostrarla en HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def verificar_login(usuario, password):
    try:
        password_limpia = str(password).strip()
        resp = requests.get(APPS_SCRIPT_URL, params={
            'accion': 'login', 'usuario': usuario, 'password': password_limpia
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("resultado") == "OK": return True
        return False
    except: return False

def cargar_datos_google(supervisor):
    try:
        response = requests.get(APPS_SCRIPT_URL, params={'supervisor': supervisor}, timeout=15)
        if response.status_code == 200: return pd.DataFrame(response.json())
        return None
    except: return None

def enviar_datos_y_foto(supervisor, actividad, foto_buffer):
    try:
        foto_b64 = base64.b64encode(foto_buffer.getvalue()).decode('utf-8')
        nombre_safe = actividad.replace("/", "-").replace("\\", "-")
        payload = {
            "supervisor": supervisor, "actividad": actividad,
            "imagen": foto_b64, "nombreArchivo": f"{nombre_safe}.jpg"
        }
        res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=30)
        return res.status_code == 200
    except: return False

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================

# A. PANTALLA DE LOGIN
if st.session_state.usuario_actual is None:
    # Columnas para centrar y dar ancho a la tarjeta
    c1, c_centro, c2 = st.columns([1, 1.5, 1])
    with c_centro:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- CARGAR LOGO ---
        ruta_logo = "assets/logo.png"
        # Ajuste de ruta por si se ejecuta desde diferente nivel
        if not os.path.exists(ruta_logo):
            if os.path.exists("../assets/logo.png"):
                ruta_logo = "../assets/logo.png"
            
        img_b64 = get_base64_image(ruta_logo)
        
        if img_b64:
            logo_html = f'<img src="data:image/png;base64,{img_b64}" width="220" style="margin-bottom: 20px; display: block; margin-left: auto; margin-right: auto;">'
        else:
            logo_html = "<h1 style='font-size: 60px; text-align: center;'>🛡️</h1>"

        # Tarjeta Visual BLANCA con Logo Real
        st.markdown(f"""
            <div class="login-card">
                {logo_html}
                <h2 style='margin-top: 0; margin-bottom: 5px;'>RMC CORPORATE</h2>
                <p style='margin-top: 0px; font-size: 13px; letter-spacing: 2px; font-weight: 600;'>SECURE ACCESS V3.1</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Formulario (fuera del div HTML para que Streamlit lo maneje)
        # Usamos un container con el mismo estilo de fondo blanco para integrarlo
        with st.container():
             st.markdown("""<style>div[data-testid="stForm"] {background-color: #ffffff; padding: 30px; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); margin-top: -20px; position: relative; z-index: 1;}</style>""", unsafe_allow_html=True)
             with st.form("login_form"):
                user_input = st.selectbox("OPERADOR:", LISTA_SUPERVISORES)
                pass_input = st.text_input("CLAVE DE ACCESO:", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("INICIAR SESIÓN >")
                
                if submitted:
                    if verificar_login(user_input, pass_input):
                        st.success(f"✅ BIENVENIDO, {user_input.split()[0].upper()}.")
                        st.session_state.usuario_actual = user_input
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ ACCESO DENEGADO")

# B. PANTALLA DASHBOARD (Esta parte no cambia, usa estilos propios)
else:
    usuario = st.session_state.usuario_actual
    
    # Estilos específicos para el Dashboard (para volver a textos claros sobre fondo oscuro)
    st.markdown("""
        <style>
            h1, h2, h3, .stMarkdown p { color: #FFFFFF !important; }
            .stMetricLabel { color: #cfd8dc !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    c_saludo, c_logout = st.columns([4, 1])
    with c_saludo:
        st.markdown(f"### 👋 OPERADOR: <span style='color:#00C9FF'>{usuario}</span>", unsafe_allow_html=True)
    with c_logout:
        if st.button("CERRAR SESIÓN"):
            st.session_state.usuario_actual = None
            st.rerun()
            
    st.markdown("---")

    # (El resto del código del dashboard sigue exactamente igual...)
    # ... (Carga de datos, KPIs, Gráficos, Formulario de subida)
    with st.spinner("Sincronizando satélite... 🛰️"):
        df_raw = cargar_datos_google(usuario)

    if df_raw is not None and not df_raw.empty:
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
                
                total_prog = int(df["Programado"].sum())
                total_real = int(df["Realizado"].sum())
                pct = (total_real / total_prog * 100) if total_prog > 0 else 0
                
                k1, k2, k3 = st.columns(3)
                k1.metric("META MENSUAL", total_prog)
                k2.metric("REALIZADO", total_real)
                k3.metric("AVANCE TOTAL", f"{pct:.1f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
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
            st.warning("⚠️ No se encontraron datos.")