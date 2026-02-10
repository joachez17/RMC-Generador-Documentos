import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="Firmador Drag & Drop", layout="wide")

st.title("✍️ Firmar y Arrastrar (Drag & Drop)")
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

    # Selector de página
    col_nav, col_tools = st.columns([1, 2])
    with col_nav:
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1

    # --- BLINDAJE DE IMAGEN (La corrección clave) ---
    page = doc[pag_num]
    # Zoom x1.5 para buena resolución en pantalla
    zoom = 1.5
    mat = fitz.Matrix(zoom, zoom)
    # alpha=False elimina transparencias (Fondo blanco forzoso)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.tobytes("png")
    # Convertir a RGB para compatibilidad total
    bg_image = Image.open(io.BytesIO(img_data)).convert("RGB")

    # ==========================================
    # 2. HERRAMIENTAS DE EDICIÓN
    # ==========================================
    with col_tools:
        herramienta = st.radio(
            "Selecciona Herramienta:",
            ("✏️ Lápiz (Firmar)", "✋ Mover y Ajustar (Drag & Drop)", "🗑️ Borrador"),
            horizontal=True
        )

    # Configuración lógica del Canvas
    if herramienta == "✏️ Lápiz (Firmar)":
        drawing_mode = "freedraw"
        stroke_width = st.slider("Grosor de tinta:", 1, 5, 2)
    elif herramienta == "✋ Mover y Ajustar (Drag & Drop)":
        drawing_mode = "transform" # <--- ESTO ACTIVA EL ARRASTRAR
        stroke_width = 2
        st.info("💡 Haz clic sobre tu firma para seleccionarla, luego arrástrala o cámbiale el tamaño desde las esquinas.")
    else:
        drawing_mode = "eraser"
        stroke_width = 10

    # ==========================================
    # 3. EL LIENZO INTERACTIVO
    # ==========================================
    # Calculamos dimensiones para que no se salga de la pantalla
    ancho_canvas = 750
    alto_canvas = int(ancho_canvas * bg_image.height / bg_image.width)

    # Mostramos el lienzo
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",  # Relleno transparente
        stroke_width=stroke_width,
        stroke_color="#000000",               # Tinta Negra
        background_image=bg_image,            # EL PDF DE FONDO
        update_streamlit=True,
        height=alto_canvas,
        width=ancho_canvas,
        drawing_mode=drawing_mode,
        key=f"canvas_pdf_{pag_num}",         # Clave única para refrescar al cambiar pág
    )

    # ==========================================
    # 4. GUARDAR CAMBIOS
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            # 1. Obtener lo que el usuario dibujó/movió
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # 2. Calcular la escala real (Pantalla vs PDF Original)
            # El PDF original (page.rect) suele ser más grande o diferente que los 750px de pantalla
            factor_escala_ancho = page.rect.width / ancho_canvas
            factor_escala_alto = page.rect.height / alto_canvas
            
            nuevo_ancho = int(img_firma.width * factor_escala_ancho)
            nuevo_alto = int(img_firma.height * factor_escala_alto)
            
            img_firma_final = img_firma.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)

            # 3. Insertar en el PDF
            # Como el canvas cubre TODA la hoja, insertamos la imagen superpuesta en (0,0)
            # cubriendo toda la página con la capa transparente de la firma
            rect_pagina = page.rect
            
            buffer = io.BytesIO()
            img_firma_final.save(buffer, format="PNG")
            
            page.insert_image(rect_pagina, stream=buffer.getvalue(), overlay=True)
            
            # 4. Generar Descarga
            pdf_final = doc.convert_to_pdf()
            
            st.success("✅ Firma aplicada correctamente.")
            st.download_button(
                label="📥 Descargar PDF Listo",
                data=pdf_final,
                file_name="Documento_Firmado_DragDrop.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ El lienzo está vacío.")