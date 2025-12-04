import numpy as np
from PIL import Image
import io
import streamlit as st
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from streamlit_drawable_canvas import st_canvas
import base64
from datetime import date
import os

# CONFIGURACIÓN INICIAL
st.set_page_config(page_title="RMC - Checklist", page_icon="🔧")

# FUNCIÓN PARA CONVERTIR IMAGEN A BASE64 (Vital para el PDF)
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    except FileNotFoundError:
        return "" # Retorna vacío si no hay logo

# === INTERFAZ DE USUARIO (LO QUE VE EL INSPECTOR) ===
st.title("🔧 Checklist Inspección Herramientas Manuales")
st.markdown("**Código:** 24057-SIGOP-R6529 | **Rev:** 2")

# 1. Datos Generales
col1, col2 = st.columns(2)
with col1:
    proyecto = st.text_input("Ubicación / Proyecto", placeholder="Ej: Minera X - Montaje Y")
    inspector = st.text_input("Inspección realizada por")
with col2:
    fecha_chequeo = st.date_input("Fecha del Chequeo", value=date.today())

st.divider()

# 2. Tabla de Chequeo (Cargada desde tu PDF [cite: 202])
st.subheader("Condiciones a Verificar")

# Estos son los ítems fijos de tu documento PDF
items_default = [
    {"ITEM": "Estado general de brocas", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de martillos o combos: mangos, caras", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de cinceles: mangos, cabeza", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de picotas: mangos, cabeza", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de palas: mangos, cabeza", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de alicates: mangos, filos", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de serruchos/sierras: mangos, hojas", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de carretillas, neumático, bateas", "A/R": "A", "OBSERVACIONES": ""},
    {"ITEM": "Estado general de limas: mango, desgaste", "A/R": "A", "OBSERVACIONES": ""}
]

df_inicial = pd.DataFrame(items_default)

# Data Editor: Permite cambiar A/R y escribir observaciones como en Excel
datos_editados = st.data_editor(
    df_inicial,
    column_config={
        "A/R": st.column_config.SelectboxColumn(
            "Estado",
            options=["A", "R", "NA"],
            required=True
        )
    },
    use_container_width=True,
    num_rows="dynamic", # Permite agregar filas si traen herramientas nuevas
    hide_index=True
)

obs_generales = st.text_area("Observaciones Generales (Opcional)")

# 3. Firma Digital
st.subheader("Firma del Inspector")
firma_canvas = st_canvas(
    stroke_width=2,
    stroke_color="#000000",
    background_color="#ffffff",
    height=100,
    width=300,
    drawing_mode="freedraw",
    key="firma"
)

# === GENERACIÓN DEL PDF ===
if st.button("📄 Generar e Imprimir PDF", type="primary"):
    if not proyecto or not inspector:
        st.error("⚠️ Por favor completa Proyecto e Inspector.")
    else:
        # 1. Procesamos la Firma (CORRECCIÓN CRÍTICA)
        firma_b64 = ""
        if firma_canvas.image_data is not None:
            # Convertimos la matriz de numpy a imagen PIL
            try:
                img_data = firma_canvas.image_data.astype("uint8")
                # st_canvas devuelve RGBA, creamos la imagen
                im = Image.fromarray(img_data)
                
                # Guardamos en memoria como PNG
                buffered = io.BytesIO()
                im.save(buffered, format="PNG")
                
                # Convertimos a Base64 para incrustar en HTML
                firma_b64 = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
            except Exception as e:
                st.warning(f"No se pudo procesar la firma: {e}")

        # 2. Preparamos los datos para Jinja
        lista_items = []
        for index, row in datos_editados.iterrows():
            lista_items.append({
                "nombre": row["ITEM"],
                "estado": row["A/R"],
                "obs": row["OBSERVACIONES"]
            })
        
        # 3. Cargamos Logo
        logo_str = get_image_base64("assets/logo.png") # Asegúrate que tu logo se llame así

        # 4. Renderizamos HTML (Rutas absolutas como arreglamos antes)
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_templates = os.path.join(directorio_actual, "templates")
        
        env = Environment(loader=FileSystemLoader(ruta_templates))
        template = env.get_template("checklist.html")
        
        html_final = template.render(
            logo_b64=logo_str,
            codigo="24057-SIGOP-R6529", 
            revision="2",
            fecha_rev="11/06/25",
            proyecto=proyecto,
            inspector=inspector,
            fecha_chequeo=fecha_chequeo.strftime("%d/%m/%Y"),
            items=lista_items,
            observaciones_generales=obs_generales,
            firma_b64=firma_b64  # Aquí pasamos la firma procesada
        )

        # 5. Creamos PDF
        try:
            pdf_bytes = HTML(string=html_final).write_pdf()
            st.success("✅ ¡PDF Generado correctamente!")
            st.download_button(
                label="Descargar PDF",
                data=pdf_bytes,
                file_name=f"Checklist_{proyecto}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")