import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

st.set_page_config(page_title="Firmador Drag & Drop V9", layout="wide")

st.title("✍️ Firmador V9 (Base64 Forzado)")
st.markdown("""
**Pasos:**
1. Selecciona **'✏️ Lápiz'** y haz tu firma (en cualquier parte).
2. Selecciona **'✋ Mover'**, haz clic en tu firma y arrástrala.
3. Presiona **Guardar**.
""")

# ==========================================
# FUNCIÓN: Convertir Imagen a Texto (Base64)
# ==========================================
def imagen_a_base64(pil_image):
    buff = io.BytesIO()
    pil_image.save(buff, format="PNG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

# ==========================================
# 1. CARGA DEL PDF
# ==========================================
uploaded_file = st.file_uploader("📂 Cargar PDF:", type=["pdf"])

if uploaded_file is not None:
    # Leer PDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    c1, c2 = st.columns([1, 2])
    with c1:
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1

    # ==========================================
    # 2. PREPARACIÓN INFALIBLE DE IMAGEN
    # ==========================================
    page = doc[pag_num]
    zoom = 1.5  # Zoom para buena calidad
    mat = fitz.Matrix(zoom, zoom)
    
    # Renderizar a imagen (Forzamos fondo blanco con alpha=False)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.tobytes("png")
    
    # 1. Crear objeto imagen PIL
    bg_pil = Image.open(io.BytesIO(img_data)).convert("RGB")
    
    # 2. CONVERTIR A TEXTO BASE64 (Aquí estaba el error antes)
    bg_base64 = imagen_a_base64(bg_pil)

    # ==========================================
    # 3. CONFIGURACIÓN DE HERRAMIENTAS
    # ==========================================
    with c2:
        herramienta = st.radio(
            "Herramienta:",
            ("✏️ Lápiz", "✋ Mover (Drag & Drop)", "🗑️ Borrador"),
            horizontal=True
        )

    if herramienta == "✏️ Lápiz":
        drawing_mode = "freedraw"
        stroke_width = 2
    elif herramienta == "✋ Mover (Drag & Drop)":
        drawing_mode = "transform"
        stroke_width = 2
        st.info("👆 Haz clic sobre tu firma para seleccionarla y moverla.")
    else:
        drawing_mode = "eraser"
        stroke_width = 10

    # ==========================================
    # 4. EL LIENZO (CANVAS)
    # ==========================================
    # Ajustar ancho del canvas
    canvas_width = 800
    canvas_height = int(canvas_width * bg_pil.height / bg_pil.width)

    # ¡AQUÍ ESTÁ LA CORRECCIÓN!
    # Pasamos 'bg_base64' (el texto), NO 'bg_pil' (el objeto)
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",
        stroke_width=stroke_width,
        stroke_color="#000000",
        background_image=bg_base64,  # <--- ESTO ES LO QUE ARREGLA TODO
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode=drawing_mode,
        key=f"canvas_v9_{uploaded_file.name}_{pag_num}",
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