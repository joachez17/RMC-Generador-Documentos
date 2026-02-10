import streamlit as st
from streamlit_drawable_canvas import st_canvas
from streamlit_image_coordinates import streamlit_image_coordinates
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageOps
import io
import numpy as np

st.set_page_config(page_title="Firmador Transparente", layout="wide")

st.title("✍️ Firmador Transparente (V14.1)")
st.markdown("""
**Instrucciones:**
1. **Haz Clic** en el documento (izquierda) donde quieres la firma.
2. **Dibuja** tu firma (derecha).
3. Presiona **Estampar Firma**.
""")

if "coords_clic" not in st.session_state:
    st.session_state.coords_clic = None

# ==========================================
# 1. CARGA DEL PDF
# ==========================================
uploaded_file = st.file_uploader("📂 Cargar PDF:", type=["pdf"])

if uploaded_file is not None:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("1. Selecciona Posición")
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1
        page = doc[pag_num]
        
        # Renderizado visual
        ancho_visual = 700 
        zoom = 1.5
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        bg_pil = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        
        alto_visual = int(ancho_visual * bg_pil.height / bg_pil.width)
        bg_pil_visual = bg_pil.resize((ancho_visual, alto_visual), Image.LANCZOS)

        # Dibujar punto rojo si hay clic
        if st.session_state.coords_clic:
            draw = ImageDraw.Draw(bg_pil_visual)
            x_c = st.session_state.coords_clic['x']
            y_c = st.session_state.coords_clic['y']
            radio = 8
            # Círculo rojo con borde blanco para que se vea bien
            draw.ellipse((x_c - radio, y_c - radio, x_c + radio, y_c + radio), fill=None, outline="red", width=3)
            draw.line((x_c - radio, y_c, x_c + radio, y_c), fill="red", width=2)
            draw.line((x_c, y_c - radio, x_c, y_c + radio), fill="red", width=2)

        # Detector de Clics
        coords = streamlit_image_coordinates(
            bg_pil_visual,
            width=ancho_visual,
            key="click_detector"
        )

        if coords:
            if st.session_state.coords_clic != coords:
                st.session_state.coords_clic = coords
                st.rerun()

    with col_der:
        st.subheader("2. Dibuja tu Firma")
        
        if st.session_state.coords_clic:
            st.success(f"📍 Destino: (X={st.session_state.coords_clic['x']}, Y={st.session_state.coords_clic['y']})")
        else:
            st.info("👈 Haz clic en el documento primero.")

        # --- LIENZO TRANSPARENTE ---
        # background_color="#eeeeee": Un gris muy suave para que veas el recuadro,
        # pero luego lo borraremos digitalmente.
        canvas_firma = st_canvas(
            stroke_width=3,
            stroke_color="black",
            background_color="#eeeeee", 
            update_streamlit=True,
            height=200,
            width=350,
            drawing_mode="freedraw",
            key="canvas_firma_transparente",
        )
        
        # Ajuste fino de tamaño
        escala_firma = st.slider("Tamaño de firma:", 0.5, 2.0, 1.0)

        if st.button("🚀 ESTAMPAR FIRMA (PNG TRANSPARENTE)", type="primary"):
            if st.session_state.coords_clic is None:
                st.error("⚠️ Falta el clic de posición.")
            elif canvas_firma.image_data is None:
                st.error("⚠️ Falta el dibujo.")
            else:
                # 1. Recuperar la imagen del canvas (RGBA)
                img_data = canvas_firma.image_data
                img_firma = Image.fromarray(img_data.astype('uint8'), 'RGBA')
                
                # --- MAGIA DE TRANSPARENCIA ---
                # El canvas trae un fondo gris (#eeeeee) o blanco. Vamos a quitarlo.
                datos = img_firma.getdata()
                nuevos_datos = []
                for item in datos:
                    # Si el pixel es muy claro (blanco/gris), lo hacemos transparente
                    # (R > 200 y G > 200 y B > 200)
                    if item[0] > 200 and item[1] > 200 and item[2] > 200:
                        nuevos_datos.append((255, 255, 255, 0)) # Transparente total
                    else:
                        nuevos_datos.append(item) # Mantener tinta negra
                
                img_firma.putdata(nuevos_datos)

                # Recortar bordes vacíos
                bbox = img_firma.getbbox()
                if bbox:
                    img_firma = img_firma.crop(bbox)
                
                # 2. Cálculos de posición (Igual que antes)
                factor_escala = page.rect.width / ancho_visual
                x_real = st.session_state.coords_clic['x'] * factor_escala
                y_real = st.session_state.coords_clic['y'] * factor_escala
                
                ancho_final = int(img_firma.width * factor_escala * escala_firma)
                alto_final = int(img_firma.height * factor_escala * escala_firma)
                
                rect_insert = fitz.Rect(
                    x_real - (ancho_final / 2),
                    y_real - (alto_final / 2),
                    x_real + (ancho_final / 2),
                    y_real + (alto_final / 2)
                )
                
                # 3. Insertar con MÁSCARA (Esto asegura transparencia en PDF)
                buffer = io.BytesIO()
                img_firma.save(buffer, format="PNG")
                
                # overlay=True es vital
                page.insert_image(rect_insert, stream=buffer.getvalue(), overlay=True)
                
                # 4. Descargar
                pdf_final = doc.convert_to_pdf()
                st.balloons()
                st.success("✅ Firma transparente aplicada.")
                
                st.download_button(
                    label="📥 Descargar PDF Listo",
                    data=pdf_final,
                    file_name="Firmado_Transparente.pdf",
                    mime="application/pdf"
                )