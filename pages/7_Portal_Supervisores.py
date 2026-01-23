import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import base64
import time
from datetime import date

st.set_page_config(page_title="Portal SSO", page_icon="🔒", layout="wide")

# ⚠️ TU NUEVA URL AQUÍ
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxcKOlYS7ad95T3ssPOVxWosKbUW-8VFfbEo7PYfTJvz5iXLHQhNUrKghLZhX8dRaxC/exec" 

# Lista de supervisores (Solo para el login dropdown)
LISTA_SUPERVISORES = [
    "Alioska Saavedra", 
    "Carlos Araya", 
    "Froilán Vargas", 
    "Juan de los Rios", 
    "Yorbin Valecillos"
]

# --- ESTILOS ---
st.markdown("""
    <style>
        .stApp { background-color: #f4f6f9; }
        .login-box { max-width: 400px; margin: auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
        .stButton>button { width: 100%; background-color: #004B8D; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE SESIÓN ---
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

# --- FUNCIONES ---
def verificar_login(usuario, password):
    try:
        # Petición al Script con acción "login"
        resp = requests.get(APPS_SCRIPT_URL, params={
            'accion': 'login', 
            'usuario': usuario, 
            'password': password
        })
        data = resp.json()
        if data.get("resultado") == "OK":
            return True
        return False
    except:
        return False

def cargar_datos_google(supervisor):
    try:
        # Petición normal (sin acción 'login', el script asume datos)
        response = requests.get(APPS_SCRIPT_URL, params={'supervisor': supervisor})
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return None
    except: return None

def enviar_datos_y_foto(supervisor, actividad, foto_buffer):
    try:
        foto_b64 = base64.b64encode(foto_buffer.getvalue()).decode('utf-8')
        payload = {
            "supervisor": supervisor,
            "actividad": actividad,
            "imagen": foto_b64,
            "nombreArchivo": f"{actividad}.jpg"
        }
        res = requests.post(APPS_SCRIPT_URL, json=payload)
        return res.status_code == 200
    except: return False

# ==========================================
# LÓGICA PRINCIPAL
# ==========================================

# 1. SI NO HAY USUARIO LOGUEADO -> MOSTRAR LOGIN
if st.session_state.usuario_actual is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_Homepage.svg/1200px-Google_Homepage.svg.png", width=150) # Puedes poner logo RMC aqui
        st.markdown("<h2 style='text-align: center; color: #004B8D;'>Acceso Supervisores</h2>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            user_input = st.selectbox("Seleccione su nombre:", LISTA_SUPERVISORES)
            pass_input = st.text_input("Contraseña:", type="password")
            btn_login = st.form_submit_button("INGRESAR")
            
            if btn_login:
                if verificar_login(user_input, pass_input):
                    st.session_state.usuario_actual = user_input
                    st.success("✅ Acceso correcto")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")

# 2. SI YA ESTÁ LOGUEADO -> MOSTRAR DASHBOARD
else:
    usuario = st.session_state.usuario_actual
    
    # Barra superior con botón de Salir
    col_saludo, col_logout = st.columns([4, 1])
    with col_saludo:
        st.markdown(f"### 👋 Hola, {usuario}")
    with col_logout:
        if st.button("Cerrar Sesión"):
            st.session_state.usuario_actual = None
            st.rerun()
            
    st.markdown("---")

    # CARGA DE DATOS DEL USUARIO LOGUEADO
    with st.spinner(f"Cargando tus metas..."):
        df_raw = cargar_datos_google(usuario)

    if df_raw is not None and not df_raw.empty:
        # --- PROCESAMIENTO (Igual que antes) ---
        header_idx = None
        for i, row in df_raw.iterrows():
            if "NOMBRE DE LA ACTIVIDAD" in str(row.values):
                header_idx = i
                break
        
        if header_idx is not None:
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = df_raw.iloc[header_idx]
            df.columns = df.columns.str.strip()
            
            # Mapeo
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
                k1.metric("Tu Meta Mensual", total_prog)
                k2.metric("Llevas Realizado", total_real)
                k3.metric("Tu Avance", f"{pct:.1f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Gráficos y Tabla
                c_viz, c_tab = st.columns([1, 2])
                with c_viz:
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=pct, gauge={'bar': {'color': "#004B8D"}, 'axis': {'range': [None, 100]}}))
                    fig.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                with c_tab:
                    df["Estado"] = (df["Realizado"] / df["Programado"]) * 100
                    st.dataframe(df[["Actividad", "Programado", "Realizado", "Estado"]], 
                                 column_config={"Estado": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)},
                                 hide_index=True, height=250)

                # INPUT
                st.markdown("---")
                st.markdown("### 📸 Nueva Evidencia")
                c1, c2 = st.columns(2)
                with c1:
                    df_pend = df[df["Realizado"] < df["Programado"]]
                    ops = df_pend["Actividad"].unique() if not df_pend.empty else df["Actividad"].unique()
                    act_sel = st.selectbox("Actividad:", ops)
                with c2:
                    foto = st.camera_input("Evidencia")
                    if foto and st.button("ENVIAR", type="primary"):
                        with st.spinner("Guardando..."):
                            if enviar_datos_y_foto(usuario, act_sel, foto):
                                st.success("✅ Guardado correctamente")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Error al guardar")
        else:
            st.warning("No se encontraron datos en tu planilla.")