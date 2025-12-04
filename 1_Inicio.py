import streamlit as st
import base64
import os

st.set_page_config(page_title="Portal RMC", page_icon="🏗️")

# Función simple para cargar logo
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img:
            return f"data:image/png;base64,{base64.b64encode(img.read()).decode()}"
    return ""

# Ruta al logo (estamos en la raíz, así que es directo)
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
logo_b64 = get_image_base64(logo_path)

# --- PORTADA ---
if logo_b64:
    st.markdown(f'<div style="text-align: center;"><img src="{logo_b64}" width="200"></div>', unsafe_allow_html=True)

st.title("🏗️ Portal de Documentos Digitales RMC")

st.markdown("""
### Bienvenido al sistema de gestión documental.

Selecciona el formulario que necesitas en la **barra lateral izquierda** 👈:

1.  **Checklist Herramientas:** Inspecciones diarias.
2.  **AST Completo:** Análisis seguro y charlas.

---
*Sistema v2.0 - Multi-Página*
""")