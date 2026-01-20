import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import date
import os
import time

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ==========================================
st.set_page_config(page_title="Portal Supervisores", page_icon="🛡️", layout="wide")

# Inyección de CSS para diseño moderno (Tarjetas, Colores, Fuentes)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
        }
        
        /* Fondo general suave */
        .stApp {
            background-color: #f4f6f9;
        }
        
        /* Caja del Selector de Supervisor */
        .selector-box {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #004B8D;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        
        /* Estilo de las métricas (KPIs) */
        div.stMetric {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        /* Botones estilo RMC */
        .stButton>button {
            background-color: #004B8D;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
            font-weight: bold;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #003666;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            color: white;
        }
        
        /* Títulos */
        h1, h2, h3, h4, h5 {
            color: #004B8D;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURACIÓN MAESTRA DE SUPERVISORES
# ==========================================
# Carpeta donde guardas los Excels
BASE_DATA_FOLDER = "data"

# DICCIONARIO: Nombre del Supervisor -> Nombre del Archivo Excel
# ¡Edita esto cuando agregues nuevos supervisores!
MAPA_SUPERVISORES = {
    "Alioska Saavedra": "Plan Personalizado de actividades SSO 2026 - Alioska Saavedra.xlsx",
    "Froilán Vargas": "Plan_Froilan.xlsx",      # Ejemplo: Sube el archivo real a 'data'
    "Juan de los Rios": "Plan_Juan.xlsx"       # Ejemplo
}

# Proyecto por defecto (o podrías hacerlo seleccionable también)
PROYECTO_DEFAULT = "Minera Escondida"

# ==========================================
# 3. GESTIÓN DE MEMORIA (SESSION STATE)
# ==========================================
# Esto permite "recordar" las subidas de fotos mientras no recargues la página por completo
if "avances_sesion" not in st.session_state:
    st.session_state["avances_sesion"] = {}

# ==========================================
# 4. FUNCIÓN DE ENVÍO DE CORREO (ROBOT)
# ==========================================
def enviar_evidencia(foto, actividad, proyecto, usuario):
    try:
        # Credenciales desde secrets.toml
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        receiver_email = st.secrets["email"]["receiver_email"]

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        
        # ASUNTO CLAVE para que el Robot de Google lo detecte
        msg['Subject'] = f"UPLOAD: |{proyecto}| - {actividad} de {usuario}"

        body = f"Nueva evidencia cargada desde Portal Supervisores.\n\nActividad: {actividad}\nSupervisor: {usuario}\nFecha: {date.today()}"
        msg.attach(MIMEText(body, 'plain'))

        # Adjuntar la foto
        if foto:
            part = MIMEBase('image', 'jpeg')
            part.set_payload(foto.getvalue())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename=evidencia_{date.today()}.jpg")
            msg.attach(part)

        # Enviar
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error de conexión al enviar correo: {e}")
        return False

# ==========================================
# 5. INTERFAZ DE USUARIO (UI)
# ==========================================

st.markdown("<h2 style='color: #004B8D;'>🛡️ Portal de Gestión SSO</h2>", unsafe_allow_html=True)

# --- A. SELECTOR DE SUPERVISOR ---
st.markdown('<div class="selector-box">', unsafe_allow_html=True)
col_sel_1, col_sel_2 = st.columns([1, 3])
with col_sel_1:
    st.markdown("### 👤 Identificación")
    st.write("Seleccione su nombre para cargar su plan:")
with col_sel_2:
    usuario_seleccionado = st.selectbox("Supervisor:", list(MAPA_SUPERVISORES.keys()), label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# --- B. LÓGICA DE CARGA DE DATOS ---
nombre_archivo = MAPA_SUPERVISORES[usuario_seleccionado]
ruta_completa = os.path.join(BASE_DATA_FOLDER, nombre_archivo)

datos_cargados = False
df = pd.DataFrame()

# Verificamos si existe el archivo
if os.path.exists(ruta_completa):
    try:
        # 1. Leer Excel sin cabecera para buscar la fila correcta
        df_raw = pd.read_excel(ruta_completa, header=None)
        
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.cat(sep=' ')
            if "NOMBRE DE LA ACTIVIDAD" in row_str:
                header_row_idx = i
                break
        
        if header_row_idx is not None:
            # 2. Cargar datos reales
            df = pd.read_excel(ruta_completa, header=header_row_idx)
            
            # 3. Renombrar columnas para estandarizar
            # Ajusta estos nombres si tu Excel cambia
            df = df.rename(columns={
                "NOMBRE DE LA ACTIVIDAD": "Actividad",
                "CANTIDAD ASIGNADA": "Programado",
                "CANTIDAD REALIZADA": "Realizado",
                "MEDIO DE VERIFICACIÓN": "Verificacion"
            })
            
            # 4. Limpieza de datos numéricos
            df["Programado"] = pd.to_numeric(df["Programado"], errors='coerce').fillna(0)
            df["Realizado"] = pd.to_numeric(df["Realizado"], errors='coerce').fillna(0)
            
            # 5. Filtro: Solo mostrar actividades obligatorias (> 0)
            df = df[df["Programado"] > 0]

            # 6. Sumar avances de la sesión actual (Memoria temporal)
            def sumar_sesion(row):
                act = row["Actividad"]
                # Clave única: Usuario + Actividad
                clave = f"{usuario_seleccionado}_{act}"
                extra = st.session_state["avances_sesion"].get(clave, 0)
                return row["Realizado"] + extra

            df["Realizado_Total"] = df.apply(sumar_sesion, axis=1)
            datos_cargados = True
            
        else:
            st.error(f"❌ Error de Formato: No se encontró la columna 'NOMBRE DE LA ACTIVIDAD' en el archivo de {usuario_seleccionado}.")
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error al leer el archivo Excel: {e}")
else:
    # Mensaje si no existe el archivo todavía
    st.info(f"👋 Hola **{usuario_seleccionado}**. Estamos configurando tu perfil.")
    st.warning(f"⚠️ No se encontró el archivo: `{nombre_archivo}` en la carpeta `data/`.")


# --- C. MOSTRAR DASHBOARD (SOLO SI HAY DATOS) ---
if datos_cargados and not df.empty:
    
    # --- CÁLCULOS KPI ---
    total_prog = int(df["Programado"].sum())
    total_real = int(df["Realizado_Total"].sum())
    
    # Calcular porcentaje global (con tope de 100% visual)
    if total_prog > 0:
        pct_global = (total_real / total_prog) * 100
    else:
        pct_global = 0
        
    if pct_global > 100: pct_global = 100

    # --- TARJETAS SUPERIORES ---
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.metric(label="📍 Meta Total Mes", value=f"{total_prog}")
    with col_kpi2:
        delta_val = total_real - total_prog
        st.metric(label="✅ Actividades Realizadas", value=f"{total_real}", delta=f"{delta_val}" if delta_val < 0 else "¡Meta Cumplida!")
    with col_kpi3:
        st.metric(label="🚀 Porcentaje Global", value=f"{pct_global:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True) # Espacio separador

    # --- GRÁFICO Y TABLA DETALLADA ---
    c_viz, c_tabla = st.columns([1, 2], gap="medium")
    
    with c_viz:
        st.markdown('<div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        st.markdown(f"##### Avance: {usuario_seleccionado}")
        
        # Gráfico Velocímetro (Gauge)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = pct_global,
            number = {'suffix': "%", 'font': {'size': 40, 'color': "#004B8D"}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#004B8D"},
                'steps': [
                    {'range': [0, 100], 'color': "#f8f9fa"}
                ],
                'threshold': {'line': {'color': "#28a745", 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_tabla:
        st.markdown('<div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        st.markdown("##### 📋 Detalle de Actividades")
        
        # Calcular % Individual para la tabla (0-100)
        df["Avance_Pct"] = (df["Realizado_Total"] / df["Programado"]) * 100
        df["Avance_Pct"] = df["Avance_Pct"].clip(upper=100) # Que no pase de 100 visualmente

        st.dataframe(
            df[["Actividad", "Programado", "Realizado_Total", "Avance_Pct"]],
            column_config={
                "Actividad": st.column_config.TextColumn("Actividad", width="medium"),
                "Programado": st.column_config.NumberColumn("Meta", format="%d"),
                "Realizado_Total": st.column_config.NumberColumn("Real", format="%d"),
                "Avance_Pct": st.column_config.ProgressColumn(
                    "Estado",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                ),
            },
            use_container_width=True,
            hide_index=True,
            height=300
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ZONA DE CARGA DE EVIDENCIA ---
    st.markdown("---")
    st.markdown("<h3 style='text-align:center; color:#004B8D;'>📸 Cargar Evidencia Fotográfica</h3>", unsafe_allow_html=True)
    
    col_input_1, col_input_2 = st.columns([1, 1], gap="large")
    
    with col_input_1:
        st.info("Seleccione la actividad que acaba de realizar:")
        
        # Filtrar pendientes primero
        df_pendientes = df[df["Realizado_Total"] < df["Programado"]]
        if not df_pendientes.empty:
            lista_opciones = df_pendientes["Actividad"].unique()
        else:
            lista_opciones = df["Actividad"].unique()
            st.success("🎉 ¡Todas las metas cumplidas! (Puede seguir subiendo registros si desea)")
            
        act_seleccionada = st.selectbox("Actividad:", lista_opciones)
        
        # Mostrar requisito
        req = df[df["Actividad"] == act_seleccionada]["Verificacion"].iloc[0]
        st.markdown(f"📄 **Documento requerido:** `{req}`")

    with col_input_2:
        st.write("Tome la foto del documento:")
        foto = st.camera_input("Cámara", label_visibility="collapsed")
        
        if foto:
            if st.button("🚀 ENVIAR Y ACTUALIZAR", type="primary"):
                with st.spinner("Enviando evidencia al sistema..."):
                    if enviar_evidencia(foto, act_seleccionada, PROYECTO_DEFAULT, usuario_seleccionado):
                        # Actualizar Memoria Temporal
                        clave_unica = f"{usuario_seleccionado}_{act_seleccionada}"
                        valor_actual = st.session_state["avances_sesion"].get(clave_unica, 0)
                        st.session_state["avances_sesion"][clave_unica] = valor_actual + 1
                        
                        st.success("✅ ¡Registro Exitoso!")
                        time.sleep(1.5)
                        st.rerun() # Recargar página para ver cambios en gráfico