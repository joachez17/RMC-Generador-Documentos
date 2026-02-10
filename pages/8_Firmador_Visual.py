import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import streamlit.elements.image as st_image

# ==========================================
# 🚑 PARCHE DE COMPATIBILIDAD (CRÍTICO)
# ==========================================
# Esto permite que Streamlit acepte imágenes de fondo sin errores
if not hasattr(st_image, 'image_to_url'):
    def image_to_url(image, width, clamp, channels, output_format, image_id, allow_emoji=True):
        if isinstance(image, str):
            return image
        # Convertimos a JPEG ligero para evitar bloqueos de memoria
        with io.BytesIO() as buffer:
            image.save(buffer, format="JPEG", quality=80)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    st_image.image_to_url = image_to_url

st.set_page_config(page_title="Firmador V12", layout="wide")

st.title("✍️ Firmador de Documentos PDF")
st.markdown("Sube tu PDF, firma con el lápiz y luego acomoda la firma.")

# ==========================================
# 1. CARGA DEL PDF
# ==========================================
uploaded_file = st.file_uploader("📂 Selecciona tu archivo PDF:", type=["pdf"])

if uploaded_file is not None:
    # Cargar el PDF en memoria
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    c1, c2 = st.columns([1, 2])
    with c1:
        pag_num = st.number_input("Página a firmar:", min_value=1, max_value=total_paginas, value=1) - 1

    # ==========================================
    # 2. EL TRUCO: PDF -> FOTO (JPEG)
    # ==========================================
    page = doc[pag_num]
    
    # Zoom 1.5 para que se vea nítido
    mat = fitz.Matrix(1.5, 1.5)
    pix = page.get_pixmap(matrix=mat, alpha=False) # alpha=False fuerza fondo blanco
    
    # Convertimos a imagen PIL (RGB)
    bg_pil_raw = Image.open(io.BytesIO(pix.tobytes("ppm"))).convert("RGB")
    
    # --- REDIMENSIÓN OBLIGATORIA ---
    # Ajustamos la imagen al ancho de la pantalla (800px)
    # Esto evita que la imagen sea gigante y el navegador la ponga blanca.
    ancho_pantalla = 800
    alto_pantalla = int(ancho_pantalla * bg_pil_raw.height / bg_pil_raw.width)
    
    bg_pil_opt = bg_pil_raw.resize((ancho_pantalla, alto_pantalla), Image.LANCZOS)

    # ==========================================
    # 3. HERRAMIENTAS DE FIRMA
    # ==========================================
    with c2:
        modo = st.radio("Modo:", ("✏️ Firmar", "✋ Mover Firma", "🗑️ Borrar"), horizontal=True)

    if modo == "✏️ Firmar":
        d_mode = "freedraw"
        cursor = "crosshair"
    elif modo == "✋ Mover Firma":
        d_mode = "transform"
        cursor = "move"
        st.info("👆 Haz clic en tu firma para moverla.")
    else:
        d_mode = "eraser"
        cursor = "default"

    # ==========================================
    # 4. EL LIENZO (CANVAS)
    # ==========================================
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.0)",
        stroke_width=2,
        stroke_color="#000000",
        background_image=bg_pil_opt,  # <--- Aquí va la "FOTO" del PDF
        update_streamlit=True,
        height=alto_pantalla,
        width=ancho_pantalla,
        drawing_mode=d_mode,
        key=f"canvas_v12_{uploaded_file.name}_{pag_num}",
    )

    # 🕵️‍♂️ MONITOR DE DIAGNÓSTICO (Si ves esto, el PDF se leyó bien)
    with st.expander("¿Pantalla blanca? Ver imagen de referencia"):
        st.write("Si ves la imagen de abajo, el PDF se cargó correctamente.")
        st.image(bg_pil_opt, caption="Referencia del PDF", width=400)

    # ==========================================
    # 5. GUARDAR Y RECONSTRUIR PDF
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            # Recuperar la firma dibujada
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # --- MATEMÁTICAS DE ESCALA ---
            # El PDF real tiene un tamaño diferente a la pantalla (800px)
            # Calculamos la proporción para que la firma quede en el lugar exacto.
            scale_factor = page.rect.width / ancho_pantalla
            
            new_w = int(img_firma.width * scale_factor)
            new_h = int(img_firma.height * scale_factor)
            img_firma_final = img_firma.resize((new_w, new_h), Image.LANCZOS)
            
            # Pegar en el PDF Original
            buffer = io.BytesIO()
            img_firma_final.save(buffer, format="PNG")
            page.insert_image(page.rect, stream=buffer.getvalue(), overlay=True)
            
            # Generar descarga
            pdf_final = doc.convert_to_pdf()
            st.success("✅ ¡Firma aplicada con éxito!")
            st.download_button("📥 Descargar PDF Final", data=pdf_final, file_name="Firmado.pdf", mime="application/pdf")
        else:
            st.warning("⚠️ Primero debes dibujar una firma.")