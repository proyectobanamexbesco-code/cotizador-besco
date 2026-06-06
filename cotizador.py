import streamlit as st

st.set_page_config(
    page_title="Sistema Grupo Besco",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Panel de Soluciones Grupo Besco")
st.markdown("""
Bienvenido al sistema. 
Utiliza la **barra lateral izquierda** para navegar entre las diferentes herramientas:
- **Cotizaciones**
- **Reporte Fotográfico General**
- **Nestlé**
""")

st.info("Nota: La navegación se realiza a través del menú lateral izquierdo gestionado automáticamente por el sistema.")
