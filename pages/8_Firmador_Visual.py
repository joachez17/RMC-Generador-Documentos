import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="Firmador Visual Pro", layout="wide")

st.title("✍️ Firmador Visual con Ajuste")
st.markdown("1. Selecciona documento y página. | 2. Dibuja tu firma. | 3. Usa la herramienta 'Mover' para ajustarla.")

# ==========================================
# 1. CARGA DEL PDF
# ==========================================
uploaded_file = st.file_uploader("📂 Sube tu PDF aquí:", type=["pdf"])

if uploaded_file is not None:
    # Leer el PDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    # --- SELECTOR DE PÁGINA ---
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        pag_num = st.number_input("Ir a la Página:", min_value=1, max_value=total_paginas, value=1) - 1
    
    # ==========================================
    # CORRECCIÓN DE IMAGEN (Aquí estaba el problema)
    # ==========================================
    page = doc[pag_num]
    
    # Zoom x2 para nitidez
    mat = fitz.Matrix(2, 2)
    
    # 1. alpha=False OBLIGA a que el fondo sea blanco (no transparente)
    pix = page.get_pixmap(matrix=mat, alpha=False) 
    
    img_data = pix.tobytes("png")
    
    # 2. .convert("RGB") OBLIGA a usar colores estándar de pantalla
    bg_image = Image.open(io.BytesIO(img_data)).convert("RGB")

    # ==========================================
    # 2. CONFIGURACIÓN DE HERRAMIENTAS
    # ==========================================
    with c2:
        st.write("🔧 **Herramientas:**")
        modo = st.radio(
            "Acción:",
            ("Dibujar Firma", "✋ Mover/Ajustar Firma", "Borrador"),
            horizontal=True
        )
    
    if modo == "Dibujar Firma":
        drawing_mode = "freedraw"
    elif modo == "✋ Mover/Ajustar Firma":
        drawing_mode = "transform"
    else:
        drawing_mode = "eraser"

    stroke_width = 3
    if modo == "Dibujar Firma":
        stroke_width = st.slider("Grosor del lápiz:", 1, 10, 3)

    # ==========================================
    # 3. EL LIENZO (CANVAS)
    # ==========================================
    st.write(f"📄 **Viendo Página {pag_num + 1} de {total_paginas}** - Dibuja directamente abajo:")
    
    # Ajuste de dimensiones
    canvas_width = 700
    canvas_height = int(canvas_width * bg_image.height / bg_image.width)

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",  
        stroke_width=stroke_width,
        stroke_color="#000000",
        background_image=bg_image,  # Ahora sí debería verse la imagen
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode=drawing_mode,
        key=f"canvas_page_{pag_num}", # Clave única por página
    )

    # ==========================================
    # 4. GUARDADO
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Recálculo de escala para alta calidad
            factor_escala = page.rect.width / canvas_width
            nueva_ancho = int(img_firma.width * factor_escala)
            nueva_alto = int(img_firma.height * factor_escala)
            img_firma_resized = img_firma.resize((nueva_ancho, nueva_alto), Image.LANCZOS)

            buffer_firma = io.BytesIO()
            img_firma_resized.save(buffer_firma, format="PNG")
            
            rect = page.rect
            page.insert_image(rect, stream=buffer_firma.getvalue())
            
            pdf_bytes = doc.convert_to_pdf()
            
            st.success(f"✅ ¡Firma estampada en la página {pag_num + 1}!")
            st.download_button(
                label="📥 Descargar PDF Final",
                data=pdf_bytes,
                file_name="Documento_Firmado.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ No has dibujado nada aún.")