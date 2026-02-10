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
    
    # Renderizar la página seleccionada como imagen de fondo
    page = doc[pag_num]
    # Zoom x2 para que se vea nítido en pantalla
    mat = fitz.Matrix(2, 2) 
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    bg_image = Image.open(io.BytesIO(img_data))

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
    
    # Traducir la selección del usuario al idioma de la librería
    if modo == "Dibujar Firma":
        drawing_mode = "freedraw"
    elif modo == "✋ Mover/Ajustar Firma":
        drawing_mode = "transform"  # <--- ESTA ES LA MAGIA PARA MOVER
    else:
        drawing_mode = "eraser"

    stroke_width = 3
    if modo == "Dibujar Firma":
        stroke_width = st.slider("Grosor del lápiz:", 1, 10, 3)

    # ==========================================
    # 3. EL LIENZO (CANVAS)
    # ==========================================
    st.write(f"📄 **Viendo Página {pag_num + 1} de {total_paginas}** - Dibuja directamente abajo:")
    
    # Calculamos el ancho para que quepa en la pantalla (ajustable)
    canvas_width = 700
    canvas_height = int(canvas_width * bg_image.height / bg_image.width)

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",  # Relleno transparente
        stroke_width=stroke_width,
        stroke_color="#000000",               # Tinta Negra
        background_image=bg_image,            # La página del PDF de fondo
        update_streamlit=True,
        height=canvas_height,                 # Alto ajustado a la página
        width=canvas_width,                   # Ancho fijo
        drawing_mode=drawing_mode,            # Aquí cambia entre dibujar y mover
        key=f"canvas_page_{pag_num}",        # Clave única por página para no mezclar firmas
    )

    # ==========================================
    # 4. GUARDADO
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            # 1. Obtener la firma dibujada (sin el fondo del PDF)
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # 2. Ajustar tamaño de la firma para que coincida con el PDF real
            # (El canvas en pantalla es más pequeño que el PDF original de alta calidad)
            factor_escala = page.rect.width / canvas_width
            nueva_ancho = int(img_firma.width * factor_escala)
            nueva_alto = int(img_firma.height * factor_escala)
            img_firma_resized = img_firma.resize((nueva_ancho, nueva_alto), Image.LANCZOS)

            # 3. Guardar en buffer
            buffer_firma = io.BytesIO()
            img_firma_resized.save(buffer_firma, format="PNG")
            
            # 4. Pegar sobre la página seleccionada (Overlay)
            rect = page.rect # Rectángulo completo de la página
            page.insert_image(rect, stream=buffer_firma.getvalue())
            
            # 5. Generar PDF final
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