import numpy as np
from PIL import Image
import io
import streamlit as st
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from streamlit_drawable_canvas import st_canvas
import base64
from datetime import date
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# CONFIGURACIÓN INICIAL
st.set_page_config(page_title="RMC - Checklist", page_icon="🔧")

# === CORRECCIÓN DE RUTAS ===
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir) # Subir un nivel
logo_path = os.path.join(root_dir, "assets", "logo.png")
templates_path = os.path.join(root_dir, "templates")

# --- FUNCIONES AUXILIARES ---
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    except FileNotFoundError:
        return ""

def process_signature(canvas_result):
    if canvas_result.image_data is not None:
        try:
            img_data = canvas_result.image_data.astype("uint8")
            im = Image.fromarray(img_data)
            buffered = io.BytesIO()
            im.save(buffered, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
        except:
            return None
    return None

# --- FUNCIÓN DE ENVÍO DE CORREO (EL MOTOR) ---
def send_email_with_pdf(pdf_bytes, filename, location, inspector_name):
    # Cargar secretos
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        receiver_email = st.secrets["email"]["receiver_email"]
    except Exception:
        st.error("⚠️ Error de configuración de correo (Secrets).")
        return False

    # Crear el mensaje
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"CHECKLIST NUEVO: {location} - {inspector_name}"

    body = f"""
    Estimados Control Documental,
    
    Se ha realizado una nueva inspección de herramientas.
    
    - Proyecto: {location}
    - Inspector: {inspector_name}
    - Fecha: {date.today()}
    
    Adjunto encontrarás el reporte en PDF.
    
    Atte,
    Sistema Digital RMC
    """
    msg.attach(MIMEText(body, 'plain'))

    # Adjuntar PDF
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {filename}")
    msg.attach(part)

    # Enviar
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False

# === INTERFAZ DE USUARIO ===
st.title("🔧 Checklist Inspección Herramientas Manuales")
st.markdown("**Código:** 24057-SIGOP-R6529 | **Rev:** 2")

# 1. Datos Generales
col1, col2 = st.columns(2)
with col1:
    proyecto = st.text_input("Ubicación / Proyecto", placeholder="Ej: Minera X - Montaje Y")
    inspector = st.text_input("Inspección realizada por")
with col2:
    fecha_chequeo = st.date_input("Fecha del Chequeo", value=date.today())

st.divider()

# 2. Tabla de Chequeo
st.subheader("Condiciones a Verificar")

items_default = [
    {"ITEM": "Estado general de brocas", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de martillos o combos: mangos, caras", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de cinceles: mangos, cabeza", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de picotas: mangos, cabeza", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de palas: mangos, cabeza", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de alicates: mangos, filos", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de serruchos/sierras: mangos, hojas", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de carretillas, neumático, bateas", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de limas: mango, desgaste", "A/R": "A", "OBSERVACIONES": ""}
]

df_inicial = pd.DataFrame(items_default)

datos_editados = st.data_editor(
    df_inicial,
    column_config={
        "A/R": st.column_config.SelectboxColumn("Estado", options=["A", "R", "NA"], required=True)
    },
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True
)

obs_generales = st.text_area("Observaciones Generales (Opcional)")

# 3. Firma Digital
st.subheader("Firma del Inspector")
firma_canvas = st_canvas(
    stroke_width=2, stroke_color="#000000", background_color="#ffffff",
    height=100, width=300, drawing_mode="freedraw", key="firma"
)

# === GENERACIÓN DEL PDF Y ENVÍO ===
if st.button("📄 Generar y Enviar PDF", type="primary"):
    if not proyecto or not inspector:
        st.error("⚠️ Por favor completa Proyecto e Inspector.")
    else:
        # Procesar Firma
        firma_b64 = process_signature(firma_canvas)

        # Preparar datos
        lista_items = []
        for index, row in datos_editados.iterrows():
            lista_items.append({
                "nombre": row["ITEM"],
                "estado": row["A/R"],
                "obs": row["OBSERVACIONES"]
            })
        
        # Cargar Logo
        logo_str = get_image_base64(logo_path)

        # Renderizar HTML
        env = Environment(loader=FileSystemLoader(templates_path))
        template = env.get_template("checklist.html")
        
        html_final = template.render(
            logo_b64=logo_str,
            codigo="24057-SIGOP-R6529", 
            revision="2",
            fecha_rev="11/06/25",
            proyecto=proyecto,
            inspector=inspector,
            fecha_chequeo=fecha_chequeo.strftime("%d/%m/%Y"),
            items=lista_items,
            observaciones_generales=obs_generales,
            firma_b64=firma_b64
        )

        # Crear PDF
        try:
            pdf_bytes = HTML(string=html_final).write_pdf()
            
            # --- ENVÍO DE CORREO AUTOMÁTICO ---
            with st.spinner("Enviando reporte a Control Documental..."):
                filename_pdf = f"Checklist_{proyecto}_{fecha_chequeo}.pdf"
                
                if send_email_with_pdf(pdf_bytes, filename_pdf, proyecto, inspector):
                    st.success("✅ ¡Reporte enviado exitosamente!")
                    st.balloons()
                else:
                    st.warning("⚠️ El PDF se generó, pero falló el envío de correo.")

            # Botón de descarga
            st.download_button(
                label="Descargar Copia Local",
                data=pdf_bytes,
                file_name=f"Checklist_{proyecto}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")