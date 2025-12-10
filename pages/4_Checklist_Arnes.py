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

st.set_page_config(page_title="Insp. Arnés", page_icon="🦺")

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
st.title("🦺 Inspección Arnés de Seguridad")
st.markdown("**Código:** 99300-SIGOP-R6517 | **Rev:** 2")

col1, col2 = st.columns(2)
id_equipo = col1.text_input("ID Equipo / Código Arnés")
fecha = col2.date_input("Fecha", date.today())
col3, col4 = st.columns(2)
colaborador = col3.text_input("Nombre Colaborador (Usuario)")
cargo = col4.text_input("Cargo")

st.markdown("---")

# --- ITEMS DEL PDF  ---
items_data = [
    {"CAT": "1. CONDICIÓN DEL TEJIDO", "ITEM": "1.1 Estiramiento excesivo", "A/R": "A", "OBS": ""},
    {"CAT": "1. CONDICIÓN DEL TEJIDO", "ITEM": "1.2 Costuras, cortes o rotura del tejido", "A/R": "A", "OBS": ""},
    {"CAT": "1. CONDICIÓN DEL TEJIDO", "ITEM": "1.3 Fibras externas cortadas/desgastadas", "A/R": "A", "OBS": ""},
    {"CAT": "1. CONDICIÓN DEL TEJIDO", "ITEM": "1.4 Quemaduras", "A/R": "A", "OBS": ""},
    {"CAT": "1. CONDICIÓN DEL TEJIDO", "ITEM": "1.5 Deterioro general", "A/R": "A", "OBS": ""},
    {"CAT": "2. ARGOLLAS", "ITEM": "2.1 Defectos de funcionamiento", "A/R": "A", "OBS": ""},
    {"CAT": "2. ARGOLLAS", "ITEM": "2.2 Deformaciones, desgaste excesivo", "A/R": "A", "OBS": ""},
    {"CAT": "2. ARGOLLAS", "ITEM": "2.3 Corrosión", "A/R": "A", "OBS": ""},
    {"CAT": "2. ARGOLLAS", "ITEM": "2.4 Grietas, trizaduras", "A/R": "A", "OBS": ""},
    {"CAT": "2. ARGOLLAS", "ITEM": "2.5 Defectos de funcionamiento", "A/R": "A", "OBS": ""},
    {"CAT": "3. COLAS DE VIDA", "ITEM": "3.1 Estiramiento o elongación excesivos", "A/R": "A", "OBS": ""},
    {"CAT": "3. COLAS DE VIDA", "ITEM": "3.2 Desgaste, deformación o desgarro", "A/R": "A", "OBS": ""},
    {"CAT": "3. COLAS DE VIDA", "ITEM": "3.3 Cortes, rotura tejido", "A/R": "A", "OBS": ""},
    {"CAT": "3. COLAS DE VIDA", "ITEM": "3.3 Quemaduras", "A/R": "A", "OBS": ""},
    {"CAT": "4. CUERDAS DE VIDA", "ITEM": "4.1 Fibras cortadas o deshilachadas", "A/R": "A", "OBS": ""},
    {"CAT": "4. CUERDAS DE VIDA", "ITEM": "4.2 Estiramiento o elongación excesivos", "A/R": "A", "OBS": ""},
    {"CAT": "4. CUERDAS DE VIDA", "ITEM": "4.3 Extremo libre deshilachado", "A/R": "A", "OBS": ""},
    {"CAT": "4. CUERDAS DE VIDA", "ITEM": "4.4 Corroído, desgarrado", "A/R": "A", "OBS": ""},
    {"CAT": "4. CUERDAS DE VIDA", "ITEM": "4.5 Deterioro general", "A/R": "A", "OBS": ""},
]

df = pd.DataFrame(items_data)
edited_df = st.data_editor(
    df,
    column_config={
        "CAT": st.column_config.TextColumn("Categoría", disabled=True),
        "ITEM": st.column_config.TextColumn("Punto a Inspeccionar", disabled=True),
        "A/R": st.column_config.SelectboxColumn("Estado", options=["A", "R", "NA"], required=True)
    },
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.subheader("Firmas")
c_firma1, c_firma2 = st.columns(2)

with c_firma1:
    st.write("Firma Inspección Realizada (Usuario)")
    canvas_user = st_canvas(stroke_width=2, height=100, width=300, key="firma_user")

with c_firma2:
    st.write("Firma Inspección Validada (Supervisor)")
    canvas_sup = st_canvas(stroke_width=2, height=100, width=300, key="firma_sup")

# --- GENERACIÓN ---
if st.button("📄 Generar y Enviar", type="primary"):
    if not colaborador:
        st.warning("Falta nombre del colaborador")
    else:
        # Procesar datos
        items_procesados = edited_df.to_dict('records')
        firma_user_b64 = process_signature(canvas_user)
        firma_sup_b64 = process_signature(canvas_sup)
        logo_b64 = get_image_base64(logo_path)

        # Render
        env = Environment(loader=FileSystemLoader(templates_path))
        template = env.get_template("arnes.html")
        html = template.render(
            logo_b64=logo_b64,
            id_equipo=id_equipo, fecha=fecha.strftime("%d/%m/%Y"),
            colaborador=colaborador, cargo=cargo,
            items=items_procesados,
            firma_user=firma_user_b64, firma_sup=firma_sup_b64
        )

        pdf = HTML(string=html).write_pdf()
        
        # Enviar
        filename = f"Arnes_{colaborador}_{fecha}.pdf"
        if send_email_with_pdf(pdf, filename, "Inspección Arnés", colaborador):
            st.success("¡Enviado a Drive/Correo!")
            st.balloons()