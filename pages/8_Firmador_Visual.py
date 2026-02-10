import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io

# ==========================================
# 0. PARCHE DE SEGURIDAD (FIX IMAGEN INVISIBLE)
# ==========================================
# Esto arregla el bug visual de Streamlit reciente
import streamlit.elements.image as st_image
if not hasattr(st_image, 'image_to_url'):
    def image_to_url(image, width, clamp, channels, output_format, image_id, allow_emoji=True):
        return None
    st_image.image_to_url = image_to_url

st.set_page_config(page_title="Firmador Drag & Drop V7.1", layout="wide")

st.title("✍️ Firmar y Arrastrar (Versión Blindada)")
st.markdown("""
**Instrucciones:**
1. **Dibuja** tu firma (usa el lápiz).
2. Cambia a **✋ Mover y Ajustar**.
3. **Arrastra** la firma con el mouse a la posición exacta.
""")

# ==========================================
# 1. CARGA DEL DOCUMENTO
# ==========================================
uploaded_file = st.file_uploader("📂 Cargar PDF:", type=["pdf"])

if uploaded_file is not None:
    # Cargar PDF en memoria
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    col_nav, col_tools = st.columns([1, 2])
    with col_nav:
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1

    # ==========================================
    # 2. PROCESAMIENTO DE IMAGEN DE FONDO
    # ==========================================
    page = doc[pag_num]
    # Zoom x1.5 para que se vea nítido
    zoom = 1.5
    mat = fitz.Matrix(zoom, zoom)
    
    # IMPORTANTE: alpha=False fuerza fondo BLANCO (quita transparencias)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.tobytes("png")
    
    # Convertimos a imagen PIL y aseguramos modo RGB
    bg_image = Image.open(io.BytesIO(img_data)).convert("RGB")

    # ==========================================
    # 3. HERRAMIENTAS
    # ==========================================
    with col_tools:
        herramienta = st.radio(
            "Selecciona Herramienta:",
            ("✏️ Lápiz (Firmar)", "✋ Mover y Ajustar (Drag & Drop)", "🗑️ Borrador"),
            horizontal=True
        )

    if herramienta == "✏️ Lápiz (Firmar)":
        drawing_mode = "freedraw"
        stroke_width = st.slider("Grosor de tinta:", 1, 5, 2)
        cursor = "crosshair"
    elif herramienta == "✋ Mover y Ajustar (Drag & Drop)":
        drawing_mode = "transform"
        stroke_width = 2
        cursor = "move"
        st.info("💡 Haz clic sobre tu trazo para seleccionarlo y arrástralo.")
    else:
        drawing_mode = "eraser"
        stroke_width = 10
        cursor = "default"

    # ==========================================
    # 4. EL LIENZO (CANVAS)
    # ==========================================
    # Calculamos el tamaño correcto para la pantalla
    canvas_width = 800
    canvas_height = int(canvas_width * bg_image.height / bg_image.width)

    # Mostramos el canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",  # Transparente
        stroke_width=stroke_width,
        stroke_color="#000000",
        background_image=bg_image,            # AQUÍ VA EL PDF
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode=drawing_mode,
        key=f"canvas_v7_{uploaded_file.name}_{pag_num}", # Clave única para forzar recarga
    )

    # ==========================================
    # 5. GUARDAR
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            # Recuperar firma del canvas
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Calcular escala real
            factor_escala = page.rect.width / canvas_width
            
            # Redimensionar firma para el PDF real
            nuevo_ancho = int(img_firma.width * factor_escala)
            nuevo_alto = int(img_firma.height * factor_escala)
            img_firma_final = img_firma.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)

            # Insertar en el PDF
            buffer = io.BytesIO()
            img_firma_final.save(buffer, format="PNG")
            
            rect_pagina = page.rect
            # Overlay=True pone la firma ENCIMA del texto existente
            page.insert_image(rect_pagina, stream=buffer.getvalue(), overlay=True)
            
            pdf_final = doc.convert_to_pdf()
            
            st.success("✅ Firma aplicada.")
            st.download_button(
                "📥 Descargar PDF", 
                data=pdf_final, 
                file_name="Firmado.pdf", 
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ El lienzo está vacío.")