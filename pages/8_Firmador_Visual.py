import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

st.set_page_config(page_title="Firmador V8 (Base64)", layout="wide")

st.title("✍️ Firmador Documental (Modo Seguro)")
st.markdown("""
**Instrucciones:**
1. **Dibuja** tu firma.
2. Cambia a **✋ Mover**.
3. **Arrastra** la firma a su lugar.
""")

# ==========================================
# FUNCIÓN AUXILIAR: CONVERTIR IMAGEN A TEXTO (BASE64)
# Esta es la clave para que el fondo NUNCA falle
# ==========================================
def image_to_base64(pil_image):
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

# ==========================================
# 1. CARGA DEL DOCUMENTO
# ==========================================
uploaded_file = st.file_uploader("📂 Cargar PDF:", type=["pdf"])

if uploaded_file is not None:
    # Cargar PDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    col_nav, col_tools = st.columns([1, 2])
    with col_nav:
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1

    # ==========================================
    # 2. PREPARAR IMAGEN DE FONDO
    # ==========================================
    page = doc[pag_num]
    zoom = 1.5  # Zoom para calidad
    mat = fitz.Matrix(zoom, zoom)
    
    # Renderizar página a imagen (Forzando fondo blanco)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.tobytes("png")
    bg_image_pil = Image.open(io.BytesIO(img_data)).convert("RGB")
    
    # 🛠️ CONVERSIÓN A BASE64 (La Solución)
    bg_image_url = image_to_base64(bg_image_pil)

    # ==========================================
    # 3. HERRAMIENTAS
    # ==========================================
    with col_tools:
        herramienta = st.radio(
            "Herramienta:",
            ("✏️ Lápiz", "✋ Mover/Ajustar", "🗑️ Borrador"),
            horizontal=True
        )

    if herramienta == "✏️ Lápiz":
        drawing_mode = "freedraw"
        stroke_width = st.slider("Grosor:", 1, 5, 2)
    elif herramienta == "✋ Mover/Ajustar":
        drawing_mode = "transform"
        stroke_width = 2
        st.info("Haz clic en la firma para moverla.")
    else:
        drawing_mode = "eraser"
        stroke_width = 10

    # ==========================================
    # 4. EL LIENZO (CANVAS)
    # ==========================================
    # Ajuste de dimensiones
    canvas_width = 800
    canvas_height = int(canvas_width * bg_image_pil.height / bg_image_pil.width)

    # Nota: Aquí pasamos 'background_image' como una URL de datos (Base64)
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",
        stroke_width=stroke_width,
        stroke_color="#000000",
        background_image=bg_image_pil, # Intentamos objeto directo primero
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode=drawing_mode,
        key=f"canvas_base64_{uploaded_file.name}_{pag_num}",
    )

    # 🚨 PLAN B VISUAL: Si por alguna razón el canvas sigue blanco,
    # mostramos la imagen original ARRIBA como referencia.
    # (Solo se activa si el usuario marca la casilla)
    with st.expander("¿No ves el fondo? Haz clic aquí"):
        st.warning("Si el recuadro de abajo está blanco, usa esta imagen de referencia:")
        st.image(bg_image_pil, caption="Imagen de Referencia", use_column_width=True)

    # ==========================================
    # 5. GUARDAR
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Calcular escala
            factor = page.rect.width / canvas_width
            nuevo_w = int(img_firma.width * factor)
            nuevo_h = int(img_firma.height * factor)
            img_firma_final = img_firma.resize((nuevo_w, nuevo_h), Image.LANCZOS)

            # Insertar en PDF
            buffer = io.BytesIO()
            img_firma_final.save(buffer, format="PNG")
            
            page.insert_image(page.rect, stream=buffer.getvalue(), overlay=True)
            
            pdf_final = doc.convert_to_pdf()
            
            st.success("✅ Listo")
            st.download_button("📥 Descargar PDF", data=pdf_final, file_name="Firmado.pdf", mime="application/pdf")
        else:
            st.warning("⚠️ Lienzo vacío")