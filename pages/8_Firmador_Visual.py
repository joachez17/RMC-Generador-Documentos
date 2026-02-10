import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

st.set_page_config(page_title="Firmador Visual", layout="wide")

st.title("✍️ Firma Digital en Pantalla")
st.markdown("Selecciona un documento, firma directamente sobre él y guarda.")

# ==========================================
# 1. SIMULACIÓN DE CONEXIÓN CON DRIVE
# ==========================================
# En el futuro, esto vendrá de tu Apps Script
# Por ahora, simulamos una lista de documentos
docs_disponibles = ["Seleccionar...", "Permiso_Trabajo.pdf", "Charla_Seguridad.pdf"]

archivo_seleccionado = st.selectbox("📂 1. Selecciona el documento del Drive:", docs_disponibles)

# ==========================================
# 2. CARGA DEL PDF (Lógica Visual)
# ==========================================
uploaded_file = None

# Aquí simulamos que si el usuario elige algo, le pedimos subirlo para probar
# (Cuando conectemos el Drive real, este paso se hace solo)
if archivo_seleccionado != "Seleccionar...":
    st.info(f"Simulando descarga de: {archivo_seleccionado}")
    uploaded_file = st.file_uploader(" (Temporal) Sube un PDF para probar la firma:", type=["pdf"])

if uploaded_file is not None:
    # --- PROCESAMIENTO DEL PDF ---
    # Leemos el PDF con PyMuPDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    pagina_numero = st.number_input("Página a firmar:", min_value=1, max_value=len(doc), value=1) - 1
    page = doc[pagina_numero]
    
    # Convertimos la página del PDF a una IMAGEN para poder dibujar encima
    pix = page.get_pixmap(dpi=150)  # DPI 150 para buena calidad
    img_data = pix.tobytes("png")
    bg_image = Image.open(io.BytesIO(img_data)).convert("RGB")

    # ==========================================
    # 3. EL LIENZO DE FIRMA (CANVAS)
    # ==========================================
    st.write("🖌️ **Dibuja tu firma en el recuadro:**")
    
    # Creamos el canvas del tamaño exacto de la imagen del PDF
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Color de relleno (no usado para firma)
        stroke_width=2,                       # Grosor del lápiz
        stroke_color="#000000",               # Color de la tinta (Negro)
        background_image=bg_image,            # ¡AQUÍ ESTÁ LA MAGIA! El PDF es el fondo
        update_streamlit=True,
        height=bg_image.height,
        width=bg_image.width,
        drawing_mode="freedraw",
        key="canvas_firma",
    )

    # ==========================================
    # 4. GUARDADO
    # ==========================================
    if st.button("💾 GUARDAR DOCUMENTO FIRMADO", type="primary"):
        if canvas_result.image_data is not None:
            # Recuperamos lo que el usuario dibujó (la tinta)
            img_firma = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Guardamos la firma en un buffer de memoria
            buffer_firma = io.BytesIO()
            img_firma.save(buffer_firma, format="PNG")
            
            # Insertamos la imagen de la firma sobre el PDF original
            # Como dibujamos sobre la imagen del PDF con las mismas dimensiones,
            # simplemente superponemos la capa entera en (0,0)
            rect = page.rect
            page.insert_image(rect, stream=buffer_firma.getvalue())
            
            # Guardamos el PDF final
            pdf_final = doc.convert_to_pdf()
            
            st.success("✅ ¡Firma estampada correctamente!")
            
            # Botón para descargar (En el futuro, esto lo sube al Drive)
            st.download_button(
                label="📥 Descargar PDF Firmado",
                data=pdf_final,
                file_name=f"Firmado_{archivo_seleccionado}",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ Por favor realiza una firma antes de guardar.")