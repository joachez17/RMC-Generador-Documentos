import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import base64
import time
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Portal Supervisores", page_icon="🛡️", layout="wide")

# ⚠️ PEGA AQUÍ LA URL DE TU APPS SCRIPT (La que termina en /exec)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxcKOlYS7ad95T3ssPOVxWosKbUW-8VFfbEo7PYfTJvz5iXLHQhNUrKghLZhX8dRaxC/exec" 

# Lista de supervisores (Deben coincidir EXACTO con las pestañas del Google Sheet)
LISTA_SUPERVISORES = [
    "Alioska Saavedra", 
    "Carlos Araya", 
    "Froilán Vargas", 
    "Juan de los Rios", 
    "Yorbin Valecillos",
    "Joaquin Sánchez"
]

PROYECTO_DEFAULT = "Minera Escondida"

# Estilos CSS
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
    """Descarga los datos del Sheet"""
    try:
        response = requests.get(APPS_SCRIPT_URL, params={'supervisor': supervisor})
        if response.status_code == 200:
            data = response.json()
            # Si el script devuelve un error controlado
            if isinstance(data, dict) and "mensaje" in data:
                st.error(f"⚠️ Error del Servidor: {data['mensaje']}")
                return None
            return pd.DataFrame(data)
        else:
            st.error(f"❌ Error HTTP: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def enviar_datos_y_foto(supervisor, actividad, foto_buffer):
    """Envía la foto y la orden de actualizar al Script"""
    try:
        # 1. Convertir imagen a Base64
        foto_bytes = foto_buffer.getvalue()
        foto_b64 = base64.b64encode(foto_bytes).decode('utf-8')
        
        # 2. Preparar paquete
        payload = {
            "supervisor": supervisor,
            "actividad": actividad,
            "imagen": foto_b64,
            "nombreArchivo": f"{actividad}.jpg"
        }
        
        # 3. Enviar (POST)
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        
        if response.status_code == 200:
            # Verificar respuesta del script
            res_json = response.json()
            if "Exito" in res_json.get("mensaje", ""):
                return True, res_json["mensaje"]
            else:
                return False, res_json.get("mensaje", "Error desconocido")
        else:
            return False, f"Error HTTP {response.status_code}"
            
    except Exception as e:
        return False, str(e)

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================

st.markdown("<h2 style='color: #004B8D;'>🛡️ Portal de Gestión SSO (En Vivo)</h2>", unsafe_allow_html=True)

# SELECCIÓN
st.markdown('<div class="selector-box">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 3])
with c1: st.write("### 👤 Supervisor")
with c2: usuario_seleccionado = st.selectbox("Nombre:", LISTA_SUPERVISORES, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# CARGA DE DATOS
with st.spinner(f"Sincronizando con nube de {usuario_seleccionado}..."):
    df_raw = cargar_datos_google(usuario_seleccionado)

if df_raw is not None and not df_raw.empty:
    # --- PROCESAMIENTO DE DATOS ---
    header_row_idx = None
    for i, row in df_raw.iterrows():
        row_str = row.astype(str).str.cat(sep=' ')
        if "NOMBRE DE LA ACTIVIDAD" in row_str:
            header_row_idx = i
            break
            
    if header_row_idx is not None:
        df = df_raw.iloc[header_row_idx + 1:].copy()
        df.columns = df_raw.iloc[header_row_idx]
        df.columns = df.columns.str.strip() # Limpiar espacios
        
        # Mapeo de columnas
        col_map = {
            "NOMBRE DE LA ACTIVIDAD": "Actividad",
            "CANTIDAD ASIGNADA": "Programado",
            "CANTIDAD REALIZADA": "Realizado",
            "MEDIO DE VERIFICACIÓN": "Verificacion"
        }
        df = df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})
        
        if "Programado" in df.columns and "Realizado" in df.columns:
            # Conversión numérica
            df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
            df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
            df = df[df["Programado"] > 0]
            
            # --- DASHBOARD ---
            total_prog = int(df["Programado"].sum())
            total_real = int(df["Realizado"].sum())
            pct = (total_real / total_prog * 100) if total_prog > 0 else 0
            if pct > 100: pct = 100
            
            # Métricas
            c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
            with c_kpi1: st.metric("📍 Meta Mes", total_prog)
            with c_kpi2: st.metric("✅ Realizado", total_real)
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
            
            # --- ZONA DE CARGA (INPUT) ---
            st.markdown("---")
            st.markdown("### 📸 Subir Evidencia")
            
            c_input1, c_input2 = st.columns(2)
            with c_input1:
                # Mostrar pendientes primero
                df_pend = df[df["Realizado"] < df["Programado"]]
                opciones = df_pend["Actividad"].unique() if not df_pend.empty else df["Actividad"].unique()
                
                act_sel = st.selectbox("Seleccione Actividad:", opciones)
                
                if "Verificacion" in df.columns:
                    req = df[df["Actividad"] == act_sel]["Verificacion"].iloc[0]
                    st.info(f"Requisito: {req}")
            
            with c_input2:
                foto = st.camera_input("Tomar Foto")
                
                if foto:
                    if st.button("🚀 ENVIAR Y GRABAR", type="primary"):
                        with st.spinner("Subiendo a Drive y Actualizando Planilla..."):
                            
                            exito, mensaje = enviar_datos_y_foto(usuario_seleccionado, act_sel, foto)
                            
                            if exito:
                                st.success(f"✅ ¡LISTO! {mensaje}")
                                st.balloons() # ¡Celebración!
                                time.sleep(3)
                                st.rerun() # Recarga la página para ver el cambio
                            else:
                                st.error(f"❌ Error: {mensaje}")

        else:
            st.error("No se encontraron columnas numéricas (Programado/Realizado).")
    else:
        st.error("No se encontró la fila 'NOMBRE DE LA ACTIVIDAD' en el Sheet.")
else:
    # Mensaje si falla la carga inicial
    pass