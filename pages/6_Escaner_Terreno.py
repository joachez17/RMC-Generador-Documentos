import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import date
import io

st.set_page_config(page_title="Escáner Terreno", page_icon="📸")

st.title("📸 Digitalización de Documentos Físicos")
st.info("Use esta opción para subir fotos de documentos realizados a mano en terreno.")

# --- 1. DATOS DEL REGISTRO ---
col1, col2 = st.columns(2)
# Aquí podrías cargar listas reales desde una base de datos o archivo de config
usuario = col1.selectbox("¿Quién sube el documento?", ["Seleccionar...", "Froilan Vargas", "Michel Nicolau", "Yorbin Valecillos", "Juan de los Rios"])
proyecto = col2.selectbox("¿A qué proyecto corresponde?", ["Seleccionar...", "Minera Escondida", "Minera WATEROUT", "Taller Central"])

tipo_doc = st.selectbox("¿Qué tipo de documento es?", ["Seleccionar...", "Charla de Seguridad Diaria", "AST Manual", "Registro de Asistencia", "Otro"])

# --- 2. CÁMARA ---
st.write("---")
st.write("📷 **Tome una foto clara del documento:**")
foto_input = st.camera_input("Cámara")

# --- FUNCIÓN DE ENVÍO (Adaptada para imágenes) ---
def enviar_foto_al_robot(foto_bytes, nombre_archivo, asunto_robot, cuerpo_mensaje):
    try:
        # Credenciales (las mismas que ya usas)
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        receiver_email = st.secrets["email"]["receiver_email"]

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = asunto_robot # EL ASUNTO ES CLAVE PARA EL ROBOT

        msg.attach(MIMEText(cuerpo_mensaje, 'plain'))

        # Adjuntar la imagen
        part = MIMEBase('image', 'jpeg') # Asumimos JPEG por la cámara
        part.set_payload(foto_bytes.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {nombre_archivo}")
        msg.attach(part)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar: {e}")
        return False

# --- 3. BOTÓN DE PROCESAMIENTO ---
if st.button("🚀 Subir Documento al Sistema", type="primary"):
    # Validaciones
    if usuario == "Seleccionar..." or proyecto == "Seleccionar..." or tipo_doc == "Seleccionar...":
        st.error("Por favor, complete todos los campos de identificación (Usuario, Proyecto y Tipo).")
    elif not foto_input:
        st.error("Debe tomar una foto del documento.")
    else:
        with st.spinner("Procesando imagen y enviando a la nube..."):
            # 1. Generar nombre de archivo estandarizado
            fecha_hoy = date.today().strftime("%Y%m%d")
            # Limpiamos espacios para el nombre del archivo
            proj_clean = proyecto.replace(" ", "")
            doc_clean = tipo_doc.replace(" ", "")
            user_clean = usuario.replace(" ", "")
            nombre_archivo = f"{fecha_hoy}_{proj_clean}_{doc_clean}_{user_clean}.jpg"

            # 2. Crear el ASUNTO CLAVE para el Robot de Google
            # Usaremos un prefijo "UPLOAD:" y separadores "|" para que el robot entienda
            asunto_clave = f"UPLOAD: |{proyecto}| - {tipo_doc} de {usuario}"

            cuerpo = f"Nuevo documento físico digitalizado.\nProyecto: {proyecto}\nTipo: {tipo_doc}\nUsuario: {usuario}\nFecha: {fecha_hoy}"

            # 3. Enviar
            if enviar_foto_al_robot(foto_input, nombre_archivo, asunto_clave, cuerpo):
                st.success(f"✅ ¡Foto enviada correctamente! Se guardará en la carpeta del proyecto: {proyecto}")
                st.balloons()