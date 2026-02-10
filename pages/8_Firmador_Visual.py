import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

st.set_page_config(page_title="Firmador V13 (CSS)", layout="wide")

st.title("✍️ Firmador Infalible (CSS)")
st.markdown("""
**Instrucciones:**
1. **Dibuja** tu firma con el lápiz.
2. Cambia a **✋ Mover** para acomodarla.
3. Presiona **Guardar**.
""")

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def imagen_a_base64(pil_image):
    buffer = io.BytesIO()
    # Guardamos como PNG para mantener calidad
    pil_image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# ==========================================
# 1. CARGA DEL PDF
# ==========================================
uploaded_file = st.file_uploader("📂 Cargar PDF:", type=["pdf"])

if uploaded_file is not None:
    # Cargar PDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    col1, col2 = st.columns([1, 3])
    with col1:
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1

    # ==========================================
    # 2. PREPARACIÓN DE LA IMAGEN DE FONDO
    # ==========================================
    page = doc[pag_num]
    zoom = 1.5
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    # Crear imagen PIL
    bg_pil = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    
    # REDIMENSIÓN FIJA (Vital para que coincida CSS y Canvas)
    # Fijamos el ancho en 800px
    ancho_fijo = 800
    alto_fijo = int(ancho_fijo * bg_pil.height / bg_pil.width)
    bg_pil_resized = bg_pil.resize((ancho_fijo, alto_fijo), Image.LANCZOS)
    
    # Convertimos a Base64 para el CSS
    bg_base64 = imagen_a_base64(bg_pil_resized)

    # ==========================================
    # 3. LA MAGIA DEL CSS (Aquí forzamos el fondo)
    # ==========================================
    # Inyectamos estilos para poner la imagen DETRÁS del canvas
    st.markdown(
        f"""
        <style>
        /* Buscamos el contenedor del canvas y le ponemos la imagen de fondo */
        div[data-testid="stCanvas"] {{
            background-image: url("{bg_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            width: {ancho_fijo}px;
            height: {alto_fijo}px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # 4. HERRAMIENTAS Y LIENZO
    # ==========================================
    with col2:
        herramienta = st.radio("Herramienta:", ("✏️ Lápiz", "✋ Mover", "🗑️ Borrador"), horizontal=True)

    if herramienta == "✏️ Lápiz":
        d_mode = "freedraw"
    elif herramienta == "✋ Mover":
        d_mode = "transform"
        st.info("Haz clic en la firma para arrastrarla.")
    else:
        d_mode = "eraser"

    # LIENZO TRANSPARENTE
    # background_image=None (Para que no intente cargar nada y fallar)
    # background_color="rgba(0,0,0,0)" (Transparente total)
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="rgba(0, 0, 0, 0)", # Transparente
        background_image=None,               # ¡No le pasamos imagen al componente!
        update_streamlit=True,
        height=alto_fijo,
        width=ancho_fijo,
        drawing_mode=d_mode,
        key=f"canvas_css_{uploaded_file.name}_{pag_num}",
    )

    # ==========================================
    # 5. GUARDAR
    # ==========================================
    if st.button("💾 GUARDAR FIRMA", type="primary"):
        if canvas_result.image_data is not None:
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Calcular escala real
            scale = page.rect.width / ancho_fijo
            new_w = int(img_firma.width * scale)
            new_h = int(img_firma.height * scale)
            img_firma_final = img_firma.resize((new_w, new_h), Image.LANCZOS)
            
            # Insertar
            buffer = io.BytesIO()
            img_firma_final.save(buffer, format="PNG")
            page.insert_image(page.rect, stream=buffer.getvalue(), overlay=True)
            
            st.success("✅ Documento firmado.")
            st.download_button("📥 Descargar", data=doc.convert_to_pdf(), file_name="Firmado.pdf", mime="application/pdf")
        else:
            st.warning("⚠️ Dibuja primero.")