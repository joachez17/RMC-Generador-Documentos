import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Gestión de Desvíos", page_icon="🚧", layout="wide")

# ⚠️ PEGA AQUÍ TU URL DEL ROBOT (La que termina en /exec)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyUfzkjvU_MHAcfvlwfC1rEsaWbr3fBfMfgNKQwt1NaXLdn9x3f21NrG-hUzntYmuSq/exec" 

st.title("🚧 Gestión y Análisis de Desvíos")

# AQUÍ CREAMOS LAS DOS PESTAÑAS (TABS)
tab_registro, tab_dashboard = st.tabs(["📝 Registrar Nuevo Evento", "📊 Dashboard en Tiempo Real"])

# ==========================================
# PESTAÑA 1: FORMULARIO DE REGISTRO
# ==========================================
with tab_registro:
    st.markdown("Ingresa los datos del evento para registrarlos en la base de datos central.")
    
    with st.form("form_desvios", clear_on_submit=True):
        st.subheader("1. Descripción del Evento")
        actividad = st.text_input("Actividad (Ej: Extensión eléctrica a ras de piso, No uso EPP)")
        
        st.markdown("---")
        st.subheader("2. Clasificación (Cantidad)")
        col1, col2, col3 = st.columns(3)
        with col1: condicion = st.number_input("Condicion insegura", min_value=0, value=0)
        with col2: accion = st.number_input("Accion insegura", min_value=0, value=0)
        with col3: positivo = st.number_input("Positivo", min_value=0, value=0)
            
        st.markdown("---")
        st.subheader("3. Detalles")
        col4, col5, col6 = st.columns(3)
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        with col4: mes = st.selectbox("Mes", meses)
        with col5: tendencia = st.text_input("Tendencia", value="1")
        with col6: seguimiento = st.selectbox("Seguimiento", ["Abierto", "Cerrado", "N/A"])
            
        st.markdown("<br>", unsafe_allow_html=True)
        enviado = st.form_submit_button("🚀 GUARDAR REGISTRO", type="primary")

    # Lógica de envío
    if enviado:
        if actividad.strip() == "":
            st.warning("⚠️ Debes ingresar el nombre de la actividad.")
        else:
            with st.spinner("Guardando en la base de datos... 🛰️"):
                val_condicion = condicion if condicion > 0 else 0
                val_accion = accion if accion > 0 else 0
                val_positivo = positivo if positivo > 0 else 0

                payload = {
                    "accion": "guardar_desvio", 
                    "actividad": actividad,
                    "condicion": val_condicion, 
                    "accion_insegura": val_accion,
                    "positivo": val_positivo, 
                    "mes": mes,
                    "tendencia": tendencia, 
                    "seguimiento": seguimiento
                }
                
                try:
                    respuesta = requests.post(APPS_SCRIPT_URL, json=payload)
                    if respuesta.status_code == 200:
                        datos_respuesta = respuesta.json()
                        if datos_respuesta.get("resultado") == "OK":
                            st.success("✅ ¡Registro guardado exitosamente! Ve a la pestaña Dashboard para ver cómo se actualiza.")
                        else:
                            st.error(f"❌ El Robot reportó un error: {datos_respuesta.get('mensaje')}")
                    else: 
                        st.error(f"❌ Error de conexión HTTP: {respuesta.status_code}")
                except Exception as e:
                    st.error(f"❌ Error interno: {str(e)}")

# ==========================================
# PESTAÑA 2: DASHBOARD Y GRÁFICOS
# ==========================================
with tab_dashboard:
    st.markdown("### 📈 Análisis de Indicadores HSE")
    
    if st.button("🔄 Actualizar Datos Ahora"):
        st.rerun()

    with st.spinner("Consultando la base de datos de Google Sheets... 🛰️"):
        try:
            # Pedimos los datos al robot
            res = requests.get(APPS_SCRIPT_URL, params={"accion": "leer_desvios"}, timeout=15)
            
            if res.status_code == 200:
                datos = res.json()
                if len(datos) > 0:
                    df = pd.DataFrame(datos)
                    
                    # Limpiamos los datos numéricos por si vienen vacíos de Excel
                    columnas_num = ['Condicion insegura', 'Accion insegura', 'Positivo']
                    for col in columnas_num:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
                    # --- MÉTRICAS SUPERIORES ---
                    st.markdown("---")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("🚨 Total Cond. Inseguras", int(df['Condicion insegura'].sum()) if 'Condicion insegura' in df else 0)
                    c2.metric("⚠️ Total Acc. Inseguras", int(df['Accion insegura'].sum()) if 'Accion insegura' in df else 0)
                    c3.metric("✅ Total Positivos", int(df['Positivo'].sum()) if 'Positivo' in df else 0)
                    
                    abiertos = len(df[df['Seguimiento'] == 'Abierto']) if 'Seguimiento' in df else 0
                    c4.metric("🔓 Casos Abiertos", abiertos)
                    st.markdown("---")

                    # --- GRÁFICOS ---
                    g1, g2 = st.columns(2)
                    
                    with g1:
                        st.markdown("**Tendencia de Hallazgos por Mes**")
                        if 'Mes' in df.columns:
                            df_mes = df.groupby('Mes')[['Condicion insegura', 'Accion insegura', 'Positivo']].sum().reset_index()
                            fig1 = px.bar(df_mes, x='Mes', y=['Condicion insegura', 'Accion insegura', 'Positivo'], 
                                          barmode='group',
                                          color_discrete_map={'Condicion insegura': '#FFA500', 'Accion insegura': '#FF4B4B', 'Positivo': '#00C9FF'})
                            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
                            st.plotly_chart(fig1, use_container_width=True)

                    with g2:
                        st.markdown("**Estado de Seguimiento (Cierre de casos)**")
                        if 'Seguimiento' in df.columns:
                            df_seg = df['Seguimiento'].value_counts().reset_index()
                            df_seg.columns = ['Estado', 'Cantidad']
                            df_seg = df_seg[df_seg['Estado'] != ""]
                            fig2 = px.pie(df_seg, values='Cantidad', names='Estado', hole=0.4,
                                          color='Estado', color_discrete_map={'Abierto': '#FF4B4B', 'Cerrado': '#00C9FF', 'N/A': 'gray'})
                            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
                            st.plotly_chart(fig2, use_container_width=True)

                    # --- TABLA CRUDA ---
                    with st.expander("Ver base de datos completa"):
                        st.dataframe(df, use_container_width=True)

                else:
                    st.info("No hay datos registrados todavía en la pestaña 'Desvios'.")
            else:
                st.error("Error al conectar con Google Sheets.")
        except Exception as e:
            st.error(f"No se pudieron cargar los gráficos: {str(e)}")