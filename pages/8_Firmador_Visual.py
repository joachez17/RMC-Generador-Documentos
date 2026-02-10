import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import streamlit.elements.image as st_image

# ==========================================
# 🚑 PARCHE DE EMERGENCIA (CIRUGÍA)
# ==========================================
# Este bloque recrea la función 'image_to_url' que Streamlit borró.
# Esto permite pasar objetos PIL sin que la app explote.
if not hasattr(st_image, 'image_to_url'):
    def image_to_url(image, width, clamp, channels, output_format, image_id, allow_emoji=True):
        """
        Esta función falsa convierte la imagen PIL a Base64 manualmente,
        engañando a st_canvas para que funcione en versiones nuevas.
        """
        # Si la imagen ya es un string (URL), la devolvemos tal cual
        if isinstance(image, str):
            return image
        
        # Si es una imagen PIL, la convertimos a Data URL
        with io.BytesIO() as buffer:
            image.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"

    # Inyectamos la función falsa en Streamlit
    st_image.image_to_url = image_to_url

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Firmador V10 (Parcheado)", layout="wide")

st.title("✍️ Firmador V10 (Drag & Drop)")
st.markdown("""
**Instrucciones:**
1. Selecciona **'✏️ Lápiz'** y dibuja tu firma.
2. Selecciona **'✋ Mover'** para arrastrarla y acomodarla.
3. Presiona **Guardar**.
""")

# ==========================================
# 1. CARGA DEL PDF
# ==========================================
uploaded_file = st.file_uploader("📂 Cargar PDF:", type=["pdf"])

if uploaded_file is not None:
    # Leer PDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    col_nav, col_tools = st.columns([1, 2])
    with col_nav:
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1

    # ==========================================
    # 2. PREPARACIÓN DE IMAGEN (Objeto PIL)
    # ==========================================
    # En esta versión V10 volvemos a usar el Objeto PIL estándar
    # porque el parche de arriba ya soluciona el problema de compatibilidad.
    page = doc[pag_num]
    zoom = 1.5  # Zoom para calidad
    mat = fitz.Matrix(zoom, zoom)
    
    # Renderizar a imagen (Fondo blanco forzoso)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.tobytes("png")
    
    # Creamos el Objeto PIL (No texto, sino Objeto real)
    bg_pil = Image.open(io.BytesIO(img_data)).convert("RGB")

    # ==========================================
    # 3. HERRAMIENTAS
    # ==========================================
    with col_tools:
        herramienta = st.radio(
            "Herramienta:",
            ("✏️ Lápiz", "✋ Mover (Drag & Drop)", "🗑️ Borrador"),
            horizontal=True
        )

    if herramienta == "✏️ Lápiz":
        drawing_mode = "freedraw"
        stroke_width = 2
        cursor = "crosshair"
    elif herramienta == "✋ Mover (Drag & Drop)":
        drawing_mode = "transform"
        stroke_width = 2
        cursor = "move"
        st.info("👆 Haz clic en la firma para seleccionarla y moverla.")
    else:
        drawing_mode = "eraser"
        stroke_width = 10
        cursor = "default"

    # ==========================================
    # 4. EL LIENZO (CANVAS)
    # ==========================================
    # Ajuste de dimensiones
    canvas_width = 800
    canvas_height = int(canvas_width * bg_pil.height / bg_pil.width)

    # Ahora podemos pasar 'bg_pil' sin miedo gracias al parche
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",
        stroke_width=stroke_width,
        stroke_color="#000000",
        background_image=bg_pil,  # <--- Pasamos el Objeto PIL (El parche lo maneja)
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode=drawing_mode,
        key=f"canvas_v10_{uploaded_file.name}_{pag_num}",
    )

    # ==========================================
    # 5. GUARDAR
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            # Recuperar firma
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Calcular factor de escala (Realidad vs Pantalla)
            scale_factor = page.rect.width / canvas_width
            
            new_w = int(img_firma.width * scale_factor)
            new_h = int(img_firma.height * scale_factor)
            img_firma_final = img_firma.resize((new_w, new_h), Image.LANCZOS)
            
            # Insertar en PDF
            buffer = io.BytesIO()
            img_firma_final.save(buffer, format="PNG")
            
            # Overlay=True pone la firma ENCIMA del texto
            page.insert_image(page.rect, stream=buffer.getvalue(), overlay=True)
            
            pdf_final = doc.convert_to_pdf()
            
            st.success("✅ Documento firmado.")
            st.download_button("📥 Descargar PDF", data=pdf_final, file_name="Firmado.pdf", mime="application/pdf")
        else:
            st.warning("⚠️ Dibuja una firma primero.")