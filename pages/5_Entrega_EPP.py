import streamlit as st
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import base64
import os
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

st.set_page_config(page_title="Entrega EPP", page_icon="🦺")

# --- RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
logo_path = os.path.join(root_dir, "assets", "logo.png")
templates_path = os.path.join(root_dir, "templates")

# --- FUNCIONES (Copia exacta de tu lógica exitosa) ---
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

def send_email_with_pdf(pdf_bytes, filename, location, worker_name):
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        receiver_email = st.secrets["email"]["receiver_email"]
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"CHECKLIST NUEVO: {location} - {worker_name}" # ROBOT DRIVE LO DETECTARÁ
        
        body = f"Adjunto inspección de Arnés.\nInspector: {worker_name}\nFecha: {date.today()}"
        msg.attach(MIMEText(body, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {filename}")
        msg.attach(part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error correo: {e}")
        return False

# --- UI ---
st.title("🛡️ Entrega de EPP y Ropa Corporativa")
st.markdown("**Código:** 99200-SIGOP-R6506")

st.info("De acuerdo a Ley 16.744, Art. 68: Las empresas deberán proporcionar gratuitamente los equipos necesarios.")

c1, c2, c3 = st.columns(3)
nombre = c1.text_input("Nombre Trabajador")
rut = c2.text_input("RUT")
cargo = c3.text_input("Cargo")
fecha_entrega = st.date_input("Fecha de Entrega", date.today())

st.subheader("Detalle de Entrega")
# Tabla inicial vacía para llenar
df_epp = pd.DataFrame([
    {"EPP/ROPA": "Casco de Seguridad", "TALLA": "Est.", "CANT": 1, "REPOSICIÓN": False},
    {"EPP/ROPA": "Lentes de Seguridad", "TALLA": "Est.", "CANT": 1, "REPOSICIÓN": False},
    {"EPP/ROPA": "Zapatos de Seguridad", "TALLA": "40", "CANT": 1, "REPOSICIÓN": False},
    {"EPP/ROPA": "", "TALLA": "", "CANT": 0, "REPOSICIÓN": False},
])

edited_epp = st.data_editor(
    df_epp,
    num_rows="dynamic",
    column_config={
        "REPOSICIÓN": st.column_config.CheckboxColumn("Es Reposición?", default=False)
    },
    use_container_width=True
)

st.write("Firma de Recepción (Trabajador):")
canvas_epp = st_canvas(stroke_width=2, height=100, width=300, key="firma_epp")

if st.button("📄 Generar Constancia EPP", type="primary"):
    # Filtrar filas vacías
    items = [row.to_dict() for _, row in edited_epp.iterrows() if row["EPP/ROPA"]]
    
    firma_b64 = process_signature(canvas_epp)
    logo_b64 = get_image_base64(logo_path)
    
    # Render
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template("epp.html")
    html = template.render(
        logo_b64=logo_b64,
        nombre=nombre, rut=rut, cargo=cargo, fecha=fecha_entrega.strftime("%d/%m/%Y"),
        items=items, firma_b64=firma_b64
    )
    
    pdf = HTML(string=html).write_pdf()
    
    filename = f"EPP_{nombre}_{fecha_entrega}.pdf"
    # ENVÍO CON ASUNTO CLAVE PARA EL ROBOT
    if send_email_with_pdf(pdf, filename, "Entrega EPP", nombre):
        st.success("✅ Constancia enviada y guardada.")
        st.balloons()