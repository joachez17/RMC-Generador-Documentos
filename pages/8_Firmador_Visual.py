import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import io

st.set_page_config(page_title="Estampador de Firmas V6", layout="wide")

# Inicializar estado para guardar la firma entre pasos
if 'firma_guardada' not in st.session_state:
    st.session_state.firma_guardada = None

st.title("✍️ Estampador de Documentos V6")

# ==========================================
# PASO 1: CREAR Y GUARDAR LA FIRMA
# ==========================================
st.markdown("### 1️⃣ Paso 1: Crea tu Firma")
st.markdown("Dibuja tu firma en el recuadro. Cuando te guste, presiona **'Confirmar y Guardar Firma'**.")

col_firma, col_preview = st.columns([1, 1])

with col_firma:
    # Lienzo pequeño solo para firmar (Fondo transparente pero visible)
    canvas_firma = st_canvas(
        fill_color="rgba(255, 255, 255, 0.0)", 
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF", # Fondo blanco para ver bien lo que firmas
        update_streamlit=True,
        height=200,
        width=400,
        drawing_mode="freedraw",
        key="canvas_creacion_firma",
    )
    
    if st.button("💾 Confirmar y Guardar Firma", type="primary"):
        if canvas_firma.image_data is not None:
            # Convertir a imagen usable y guardar en memoria
            img_raw = Image.fromarray(canvas_firma.image_data.astype('uint8'), 'RGBA')
            
            # Recortar los bordes vacíos para que solo quede la tinta
            bbox = img_raw.getbbox()
            if bbox:
                img_recortada = img_raw.crop(bbox)
                st.session_state.firma_guardada = img_recortada
                st.success("✅ ¡Firma guardada en memoria!")
            else:
                st.warning("⚠️ El lienzo está vacío.")

with col_preview:
    if st.session_state.firma_guardada:
        st.write("Visor de Firma Guardada:")
        st.image(st.session_state.firma_guardada, caption="Esta firma se usará en el documento.")
    else:
        st.info("Aquí aparecerá tu firma confirmada.")

st.markdown("---")

# ==========================================
# PASO 2: SELECCIONAR DOCUMENTO Y ESTAMPAR
# ==========================================
st.markdown("### 2️⃣ Paso 2: Ubicar en el Documento")

if st.session_state.firma_guardada is None:
    st.warning("🔒 Por favor, completa el Paso 1 para desbloquear el documento.")
else:
    uploaded_file = st.file_uploader("📂 Carga el PDF a firmar:", type=["pdf"])

    if uploaded_file is not None:
        # Abrir PDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        total_paginas = len(doc)
        
        c_pag, c_controles = st.columns([1, 2])
        
        with c_pag:
            pag_num = st.number_input("Página del documento:", min_value=1, max_value=total_paginas, value=1) - 1
        
        # Preparar imagen de fondo (El PDF)
        page = doc[pag_num]
        pix = page.get_pixmap(dpi=100) # Calidad media para vista previa rápida
        pdf_img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        
        # --- CONTROLES DE POSICIÓN ---
        st.write("🎛️ **Panel de Control de la Firma:**")
        
        col_x, col_y, col_tam = st.columns(3)
        with col_x:
            # Slider Horizontal (0 a Ancho del PDF)
            pos_x = st.slider("↔️ Mover Horizontal", 0, pdf_img.width, 50)
        with col_y:
            # Slider Vertical (0 a Alto del PDF)
            pos_y = st.slider("↕️ Mover Vertical", 0, pdf_img.height, pdf_img.height - 100)
        with col_tam:
            # Tamaño de la firma
            scale_factor = st.slider("🔍 Tamaño Firma", 0.1, 2.0, 0.5)

        # --- FUSIÓN VISUAL (PREVIEW) ---
        # Crear una copia del PDF para no dañarlo
        preview_img = pdf_img.copy()
        
        # Preparar la firma
        firma = st.session_state.firma_guardada
        nuevo_ancho = int(firma.width * scale_factor)
        nuevo_alto = int(firma.height * scale_factor)
        firma_resized = firma.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        
        # Pegar la firma sobre la copia del PDF (Usamos la máscara para transparencia)
        preview_img.paste(firma_resized, (pos_x, pos_y), firma_resized)
        
        # Mostrar el resultado
        st.image(preview_img, caption="Vista Previa en Tiempo Real", use_container_width=True)

        # ==========================================
        # PASO 3: GUARDADO FINAL
        # ==========================================
        if st.button("🚀 ESTAMPAR DEFINITIVAMENTE Y DESCARGAR", type="primary"):
            # Aquí hacemos la matemática para traducir de "Pixeles de Pantalla" a "Coordenadas PDF"
            
            # 1. Recuperar la página original en alta calidad
            page_real = doc[pag_num]
            rect_real = page_real.rect
            
            # 2. Calcular factor de conversión (Pantalla vs Realidad PDF)
            scale_x = rect_real.width / pdf_img.width
            scale_y = rect_real.height / pdf_img.height
            
            # 3. Calcular posición real
            real_x = pos_x * scale_x
            real_y = pos_y * scale_y
            real_width = nuevo_ancho * scale_x
            real_height = nuevo_alto * scale_y
            
            # 4. Insertar la imagen en el PDF real
            rect_insert = fitz.Rect(real_x, real_y, real_x + real_width, real_y + real_height)
            
            # Convertir la firma a bytes para PyMuPDF
            buffer_firma = io.BytesIO()
            st.session_state.firma_guardada.save(buffer_firma, format="PNG")
            
            page_real.insert_image(rect_insert, stream=buffer_firma.getvalue())
            
            # 5. Generar descarga
            pdf_bytes = doc.convert_to_pdf()
            
            st.balloons()
            st.success("✅ Documento firmado correctamente.")
            st.download_button(
                label="📥 DESCARGAR PDF FIRMADO",
                data=pdf_bytes,
                file_name="Documento_Firmado_V6.pdf",
                mime="application/pdf"
            )
            