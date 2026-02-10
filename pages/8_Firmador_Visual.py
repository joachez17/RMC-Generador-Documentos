import streamlit as st
from streamlit_drawable_canvas import st_canvas
from streamlit_image_coordinates import streamlit_image_coordinates
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="Firmador por Clic", layout="wide")

st.title("point_up_2: Firmador por Clic (V14)")
st.markdown("""
**Instrucciones:**
1. **Haz Clic** en el documento donde quieres que vaya la firma.
2. **Dibuja** tu firma en el recuadro de la derecha.
3. Presiona **Estampar Firma**.
""")

# Inicializar estado para guardar las coordenadas del clic
if "coords_clic" not in st.session_state:
    st.session_state.coords_clic = None

# ==========================================
# 1. CARGA DEL PDF
# ==========================================
uploaded_file = st.file_uploader("📂 Cargar PDF:", type=["pdf"])

if uploaded_file is not None:
    # Cargar PDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_paginas = len(doc)

    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("1. Documento (Haz clic para marcar)")
        
        # Selector de página
        pag_num = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1) - 1
        page = doc[pag_num]
        
        # --- RENDERIZADO DEL PDF ---
        # Usamos un ancho fijo para que las matemáticas de coordenadas sean exactas
        ancho_visual = 700 
        zoom = 1.5
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        bg_pil = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        
        # Redimensionar la imagen para mostrarla en pantalla
        # Calculamos el alto proporcional
        alto_visual = int(ancho_visual * bg_pil.height / bg_pil.width)
        bg_pil_visual = bg_pil.resize((ancho_visual, alto_visual), Image.LANCZOS)

        # Si ya hay un clic guardado, dibujamos un punto rojo en la imagen para que el usuario sepa dónde hizo clic
        if st.session_state.coords_clic:
            draw = ImageDraw.Draw(bg_pil_visual)
            x_c = st.session_state.coords_clic['x']
            y_c = st.session_state.coords_clic['y']
            # Dibujar círculo rojo
            radio = 10
            draw.ellipse((x_c - radio, y_c - radio, x_c + radio, y_c + radio), fill="red", outline="white")

        # --- COMPONENTE DE CLIC (La Magia) ---
        # Esto muestra la imagen y detecta dónde hace clic el usuario
        coords = streamlit_image_coordinates(
            bg_pil_visual,
            width=ancho_visual,
            key="click_detector"
        )

        # Si el usuario hace un clic nuevo, actualizamos el estado
        if coords:
            if st.session_state.coords_clic != coords:
                st.session_state.coords_clic = coords
                st.rerun() # Recargamos para mostrar el punto rojo

    with col_der:
        st.subheader("2. Panel de Firma")
        
        if st.session_state.coords_clic:
            st.success(f"📍 Posición fijada: (X: {st.session_state.coords_clic['x']}, Y: {st.session_state.coords_clic['y']})")
        else:
            st.info("👈 Haz clic en el documento para elegir dónde firmar.")

        st.write("**Dibuja tu firma aquí:**")
        # Lienzo pequeño solo para la firma
        canvas_firma = st_canvas(
            stroke_width=2,
            stroke_color="black",
            background_color="#ffffff", # Fondo blanco limpio
            update_streamlit=True,
            height=200,
            width=350,
            drawing_mode="freedraw",
            key="canvas_firma_simple",
        )
        
        # Slider para ajustar tamaño de la firma final
        escala_firma = st.slider("Tamaño de la firma en el documento:", 0.5, 3.0, 1.0)

        # ==========================================
        # 3. LÓGICA DE ESTAMPADO
        # ==========================================
        if st.button("🚀 ESTAMPAR FIRMA", type="primary"):
            if st.session_state.coords_clic is None:
                st.error("⚠️ Primero haz clic en el documento.")
            elif canvas_firma.image_data is None:
                st.error("⚠️ Primero dibuja tu firma.")
            else:
                # 1. Recuperar firma dibujada
                img_firma = Image.fromarray(canvas_firma.image_data.astype('uint8'), 'RGBA')
                
                # Recortar bordes vacíos de la firma
                bbox = img_firma.getbbox()
                if bbox:
                    img_firma = img_firma.crop(bbox)
                
                # 2. Matemáticas de Coordenadas (Regla de 3 simple)
                # Escala = Tamaño Real PDF / Tamaño Mostrado en Pantalla
                factor_escala = page.rect.width / ancho_visual
                
                # Coordenadas reales en el PDF
                x_real = st.session_state.coords_clic['x'] * factor_escala
                y_real = st.session_state.coords_clic['y'] * factor_escala
                
                # Tamaño real de la firma a estampar
                ancho_firma_final = int(img_firma.width * factor_escala * escala_firma)
                alto_firma_final = int(img_firma.height * factor_escala * escala_firma)
                
                # 3. Insertar imagen (Centrada en el clic)
                # El clic será el CENTRO de la firma
                rect_insert = fitz.Rect(
                    x_real - (ancho_firma_final / 2),
                    y_real - (alto_firma_final / 2),
                    x_real + (ancho_firma_final / 2),
                    y_real + (alto_firma_final / 2)
                )
                
                # Convertir firma a bytes
                buffer = io.BytesIO()
                img_firma.save(buffer, format="PNG")
                
                page.insert_image(rect_insert, stream=buffer.getvalue())
                
                # 4. Descargar
                pdf_final = doc.convert_to_pdf()
                st.balloons()
                st.success("✅ ¡Firma estampada exitosamente!")
                
                st.download_button(
                    label="📥 Descargar PDF Firmado",
                    data=pdf_final,
                    file_name="Documento_Firmado_Clic.pdf",
                    mime="application/pdf"
                )