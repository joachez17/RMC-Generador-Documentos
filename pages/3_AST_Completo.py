import streamlit as st
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import base64
import os
from datetime import date, datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AST Completo RMC", layout="wide")

# === CORRECCIÓN DE RUTAS ===
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir) # Subir un nivel
logo_path = os.path.join(root_dir, "assets", "logo.png")
templates_path = os.path.join(root_dir, "templates")

# --- FUNCIONES AUXILIARES ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img:
            return f"data:image/png;base64,{base64.b64encode(img.read()).decode()}"
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

# --- FUNCIÓN DE ENVÍO DE CORREO ---
def send_email_with_pdf(pdf_bytes, filename, location, worker_name):
    # Cargar secretos desde Streamlit Cloud
    # (Si corres en local, necesitas un archivo .streamlit/secrets.toml)
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        receiver_email = st.secrets["email"]["receiver_email"]
    except FileNotFoundError:
        st.error("⚠️ No se encontraron los secretos de correo. Configúralos en .streamlit/secrets.toml o en la nube.")
        return False

    # Crear el mensaje
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"AST NUEVO: {location} - {worker_name}"

    body = f"""
    Estimados Control Documental,
    
    Se ha generado un nuevo documento AST digital desde terreno.
    
    - Proyecto/Lugar: {location}
    - Supervisor Responsable: {worker_name}
    - Fecha: {date.today()}
    
    El documento PDF se encuentra adjunto para su archivo.
    
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

# --- TÍTULO DE LA APP ---
st.title("📋 Generador AST Completo (WBS-SIGOP-R6503)")
st.markdown("---")

# === SECCIÓN 1: ANTECEDENTES ===
with st.expander("1. Antecedentes Generales", expanded=True):
    c1, c2, c3 = st.columns(3)
    trabajo = c1.text_input("Trabajo a Realizar", "Mantenimiento Preventivo")
    lugar = c2.text_input("Lugar Específico", "Taller Central")
    fecha = c3.date_input("Fecha", date.today())
    
    c4, c5, c6 = st.columns(3)
    hora_ini = c4.time_input("Hora Inicio", datetime.strptime("08:00", "%H:%M").time())
    hora_fin = c5.time_input("Hora Término", datetime.strptime("18:00", "%H:%M").time())
    empresa = c6.text_input("Empresa Ejecutante", "Ingeniería y Servicios RMC Ltda.")
    
    c7, c8, c9 = st.columns(3)
    resp_cliente = c7.text_input("Responsable Cliente")
    resp_rmc = c8.text_input("Responsable RMC")
    supervisor = c9.text_input("Supervisor Terreno")

    st.write("Firma Supervisor Terreno:")
    canvas_sup = st_canvas(
        stroke_width=2, stroke_color="#000", background_color="#f4f4f4",
        height=80, width=300, drawing_mode="freedraw", key="sup_sig"
    )

# === SECCIÓN 2: PLANIFICACIÓN ===
with st.expander("2. Planificación del Trabajo", expanded=False):
    c_epp, c_maq = st.columns(2)
    epps = c_epp.text_area("EPPs Específicos", "Casco, Lentes, Zapatos, Guantes")
    maquinas = c_maq.text_area("Vehículos/Maquinarias", "Camioneta 4x4, Grúa Horquilla")
    
    st.markdown("**Identificación de Actividades de Alto Riesgo:**")
    riesgos_list = [
        "Potencial de arco eléctrico", "Potencial de ahogamiento", "Trabajo en altura (> 1,8 mt)",
        "Exposición a tensión viva > 50V", "Izaje y aparejos", "Poda, tala y roce",
        "Trabajo en caliente", "Áreas explosivas", "Golpeado por vehículos",
        "Sustancias peligrosas", "Energía almacenada", "Equipos rotatorios",
        "Caída de objetos", "Espacios confinados"
    ]
    riesgos_selec = st.multiselect("Seleccione Riesgos:", riesgos_list)

# === SECCIÓN 3: ANÁLISIS SEGURO ===
with st.expander("3. Análisis Seguro del Trabajo (Tabla)", expanded=False):
    st.info("Marque las casillas E (Eliminar), S (Sustituir), I (Ingeniería), A (Administrativo), EPP.")
    
    df_template_ast = pd.DataFrame([
        {"Etapa": "Ingreso", "Riesgo": "Caída", "Control": "Caminar atento", "E": False, "S": False, "I": False, "A": True, "EPP": True},
        {"Etapa": "", "Riesgo": "", "Control": "", "E": False, "S": False, "I": False, "A": False, "EPP": False}
    ])
    
    col_config = {
        "E": st.column_config.CheckboxColumn("E", width="small"),
        "S": st.column_config.CheckboxColumn("S", width="small"),
        "I": st.column_config.CheckboxColumn("I", width="small"),
        "A": st.column_config.CheckboxColumn("A", width="small"),
        "EPP": st.column_config.CheckboxColumn("EPP", width="small"),
        "Etapa": st.column_config.TextColumn("Etapa", width="medium"),
        "Riesgo": st.column_config.TextColumn("Peligro/Riesgo", width="medium"),
        "Control": st.column_config.TextColumn("Medida Control", width="large"),
    }
    
    df_ast = st.data_editor(df_template_ast, column_config=col_config, num_rows="dynamic", use_container_width=True)

# === SECCIÓN 4: EMERGENCIA ===
with st.expander("4. Plan de Emergencia", expanded=False):
    df_emer = pd.DataFrame([
        {"Emergencia": "Accidente Personal", "Pasos": "1. Detener trabajo. 2. Avisar a supervisor."},
        {"Emergencia": "Incendio", "Pasos": "1. Usar extintor si es incipiente. 2. Evacuar."}
    ])
    df_emer_edit = st.data_editor(df_emer, num_rows="dynamic", use_container_width=True)

# === SECCIÓN 5: CHARLA PREVIA ===
with st.expander("5. Charla Previa de Seguridad", expanded=True):
    cc1, cc2 = st.columns(2)
    charla_por = cc1.text_input("Realizado por (Relator)")
    charla_cargo = cc2.text_input("Cargo del Relator")
    
    cc3, cc4, cc5 = st.columns(3)
    charla_fecha = cc3.date_input("Fecha Charla", date.today(), key="date_charla")
    charla_ini = cc4.time_input("Hora Inicio Charla", datetime.strptime("08:00", "%H:%M").time(), key="time_ini_charla")
    charla_fin = cc5.time_input("Hora Término Charla", datetime.strptime("08:15", "%H:%M").time(), key="time_fin_charla")
    
    st.write("Firma del Relator:")
    canvas_charla = st_canvas(
        stroke_width=2, stroke_color="#000", background_color="#f4f4f4",
        height=80, width=300, drawing_mode="freedraw", key="charla_sig"
    )
    
    charla_temas = st.text_area("Temas Tratados", "• Análisis de riesgos del entorno.\n• Revisión de EPPs.\n• Coordinación de tareas.")

# === SECCIÓN 6: COLABORADORES ===
with st.expander("6. Registro Colaboradores", expanded=False):
    df_colab = pd.DataFrame([
        {"Nombre": "Juan Perez", "RUT": "11.111.111-1"},
        {"Nombre": "", "RUT": ""}
    ])
    df_colab_edit = st.data_editor(df_colab, num_rows="dynamic", use_container_width=True)

# === SECCIÓN 7: REVISIONES ===
with st.expander("7. Revisiones (Opcional)", expanded=False):
    rev1 = st.text_input("1° Revisión (Comentarios)", "Sin Comentarios")
    rev2 = st.text_input("2° Revisión (Comentarios)", "Sin Comentarios")

# --- GENERAR PDF Y ENVIAR ---
if st.button("📄 Generar y Enviar a RMC", type="primary"):
    
    # 1. Procesar Riesgos
    riesgos_obj = [{"label": r, "checked": r in riesgos_selec} for r in riesgos_list]
    riesgos_rows = [riesgos_obj[i:i+2] for i in range(0, len(riesgos_obj), 2)]

    # 2. Limpieza de Datos
    df_ast_clean = df_ast.fillna("").astype(str).replace(["None", "nan"], "")
    pasos_data = []
    for _, row in df_ast_clean.iterrows():
        if row["Etapa"].strip() or row["Riesgo"].strip() or row["Control"].strip():
            original_idx = _ 
            row_dict = row.to_dict()
            row_dict["E"] = bool(df_ast.at[original_idx, "E"])
            row_dict["S"] = bool(df_ast.at[original_idx, "S"])
            row_dict["I"] = bool(df_ast.at[original_idx, "I"])
            row_dict["A"] = bool(df_ast.at[original_idx, "A"])
            row_dict["EPP"] = bool(df_ast.at[original_idx, "EPP"])
            pasos_data.append(row_dict)

    df_emer_clean = df_emer_edit.fillna("").astype(str)
    emer_data = [r.to_dict() for _, r in df_emer_clean.iterrows() if r["Emergencia"].strip()]

    df_colab_clean = df_colab_edit.fillna("").astype(str)
    colab_data = [r.to_dict() for _, r in df_colab_clean.iterrows() if r["Nombre"].strip()]

    # 3. Procesar Firmas e Imágenes
    firma_sup_b64 = process_signature(canvas_sup)
    firma_charla_b64 = process_signature(canvas_charla)
    logo_b64 = get_image_base64(logo_path)

    # 4. Renderizar
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template("ast_final.html")

    html_out = template.render(
        logo_b64=logo_b64,
        trabajo=trabajo, lugar=lugar, fecha=fecha.strftime("%d/%m/%Y"),
        empresa=empresa, hora_ini=hora_ini.strftime("%H:%M"), hora_fin=hora_fin.strftime("%H:%M"),
        resp_cliente=resp_cliente, resp_rmc=resp_rmc, supervisor=supervisor,
        firma_sup_b64=firma_sup_b64,
        epps=epps, maquinas=maquinas, riesgos_rows=riesgos_rows,
        pasos=pasos_data, emergencias=emer_data,
        charla_por=charla_por, charla_cargo=charla_cargo,
        charla_fecha=charla_fecha.strftime("%d/%m/%Y"),
        charla_hora_ini=charla_ini.strftime("%H:%M"),
        charla_hora_fin=charla_fin.strftime("%H:%M"),
        firma_charla_b64=firma_charla_b64,
        charla_temas=charla_temas.replace("\n", "<br>"),
        colaboradores=colab_data,
        revision_1=rev1, revision_2=rev2
    )

    # 5. Crear PDF
    pdf_bytes = HTML(string=html_out).write_pdf()
    
    # 6. ENVIAR CORREO
    with st.spinner("Enviando documento a Control Documental..."):
        filename_pdf = f"AST_{lugar}_{fecha.strftime('%d%m%Y')}.pdf"
        
        # Llamamos a la función de correo
        if send_email_with_pdf(pdf_bytes, filename_pdf, lugar, supervisor):
            st.success("✅ ¡Documento enviado exitosamente por correo!")
            st.balloons()
        else:
            st.warning("⚠️ El PDF se generó, pero no se pudo enviar por correo. (Verifica los Secrets)")

    # 7. Botón descarga manual
    st.download_button("Descargar Copia Local", pdf_bytes, file_name="AST_RMC_Final.pdf", mime="application/pdf")