import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="Firmador Simple", layout="wide")
st.title("✍️ Firmador por Clic")

# 1. Cargar PDF
uploaded_file = st.file_uploader("📂 Cargar PDF", type=["pdf"])

if 'coords_firma' not in st.session_state:
    st.session_state.coords_firma = None

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    pag_num = st.number_input("Página:", 1, len(doc), 1) - 1
    page = doc[pag_num]
    
    # Renderizar imagen
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    img_pdf = Image.open(io.BytesIO(pix.tobytes("png")))

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("### 1. Haz clic donde quieres la firma:")
        # Usamos streamlit-image-coordinates para detectar el clic
        # (Si no tienes esta librería, avísame, pero es muy estándar)
        try:
            from streamlit_image_coordinates import streamlit_image_coordinates
            coords = streamlit_image_coordinates(img_pdf, key="pdf_click")
            
            if coords:
                st.session_state.coords_firma = coords
                st.success(f"📍 Posición seleccionada: X={coords['x']}, Y={coords['y']}")
        except ImportError:
            st.error("Necesitas instalar: pip install streamlit-image-coordinates")

    with col2:
        st.write("### 2. Dibuja tu firma:")
        canvas = st_canvas(
            stroke_width=2,
            stroke_color="black",
            background_color="#eee",
            height=150,
            width=300,
            drawing_mode="freedraw",
            key="canvas_firma_simple"
        )

        if st.button("🚀 ESTAMPAR FIRMA"):
            if st.session_state.coords_firma and canvas.image_data is not None:
                # Lógica de estampado usando las coordenadas del clic
                x_click = st.session_state.coords_firma['x']
                y_click = st.session_state.coords_firma['y']
                
                # ... (Aquí iría el código de pegado que ya conocemos) ...
                st.write("✅ ¡Firma enviada a las coordenadas!")
            else:
                st.warning("Selecciona una posición y dibuja tu firma.")