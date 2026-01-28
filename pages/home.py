import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Dashboard Gerencial", page_icon="📊", layout="wide")

# ESTILOS CSS (Para replicar el look limpio de la imagen)
st.markdown("""
    <style>
        .metric-card {
            background-color: #ffffff;
            border-left: 5px solid #004B8D;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        h3 { color: #004B8D; font-size: 18px; }
        .big-number { font-size: 36px; font-weight: bold; color: #333; }
        .sub-text { color: #666; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# TÍTULO
st.markdown("<h1 style='text-align: center; color: #004B8D;'>Indicadores Estadísticos y KPI 📊</h1>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# 1. FILA SUPERIOR (TARJETAS KPI)
# ==========================================
c1, c2, c3, c4 = st.columns(4)

def card_html(titulo, valor, extra=""):
    return f"""
    <div class="metric-card">
        <h3>{titulo}</h3>
        <div class="big-number">{valor}</div>
        <div class="sub-text">{extra}</div>
    </div>
    """

with c1:
    # Simulando el gráfico de dona con Plotly
    fig = go.Figure(go.Pie(values=[2.4, 97.6], hole=.7, marker_colors=['#004B8D', '#e0e0e0'], textinfo='none'))
    fig.update_layout(showlegend=False, height=120, margin=dict(t=0,b=0,l=0,r=0))
    fig.add_annotation(text="2,4%", font=dict(size=20, color="#004B8D"), showarrow=False)
    
    st.markdown(f"""
    <div class="metric-card">
        <h3>Cumplimiento Programa SSO</h3>
        <div style="display:flex; justify-content:center; align-items:center;">
             <div style="margin-right:10px;">
                <div class="sub-text">Actividades Realizadas</div>
                <div class="big-number">11</div>
             </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)

with c2: st.markdown(card_html("Cumplimiento E-Learning Proyecto", "3,13%"), unsafe_allow_html=True)
with c3: st.markdown(card_html("Cumplimiento E-Learning Administrativo", "0,00%"), unsafe_allow_html=True)
with c4: st.markdown(card_html("Cumplimiento E-Learning Bodega", "4,17%"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 2. SECCIÓN CENTRAL (GRÁFICOS + BARRA LATERAL)
# ==========================================
col_main, col_side = st.columns([3, 1]) # 3 partes para gráficos, 1 parte para la barra derecha

with col_main:
    # FILA DE GRÁFICOS DE LINEA
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### Índice de Frecuencia")
        # Datos Dummy
        fig_line = go.Figure(go.Scatter(y=[1, 3, 2, 4, 3, 5, 2], mode='lines+markers', line=dict(color='#00C9FF', width=3)))
        fig_line.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_line, use_container_width=True)
        
    with g2:
        st.markdown("#### Índice de Gravedad")
        fig_line2 = go.Figure(go.Scatter(y=[5, 4, 6, 2, 1, 2, 3], mode='lines+markers', line=dict(color='#00C9FF', width=3)))
        fig_line2.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_line2, use_container_width=True)

    # TARJETAS DE TASAS
    t1, t2 = st.columns(2)
    with t1:
        st.info("📉 **Tasa de Accidentabilidad**: M: 0.00 | F: 0.00")
    with t2:
        st.info("🔥 **Tasa de Siniestralidad**: M: 0.00 | F: 0.00")
        
    # TARJETAS MENSUALES (GRILLA DE ABAJO)
    st.markdown("### Plan SSO Mensual")
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
    cols = st.columns(6)
    for i, mes in enumerate(meses):
        with cols[i]:
            val = "11" if i == 0 else "0"
            pct = "29%" if i == 0 else "0%"
            st.metric(label=mes, value=val, delta=pct)

with col_side:
    st.markdown("### Cumplimiento Personalizado")
    st.markdown("---")
    
    supervisores = ["Michel Nicolau", "Froilán Vargas", "Yorbin Valecillos", "Alioska Saavedra", "Juan de los Rios", "Carlos Araya"]
    
    for sup in supervisores:
        st.markdown(f"**{sup}**")
        prog = 100
        real = 25 # Simulado
        st.progress(real/prog)
        st.caption(f"Real: {real} / Prog: {prog}")