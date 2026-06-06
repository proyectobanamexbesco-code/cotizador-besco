import streamlit as st

# --- CONFIGURACIÓN GLOBAL ---
st.set_page_config(
    page_title="Sistema Grupo Besco",
    page_icon="🏗️",
    layout="wide"
)

# --- MENÚ PRINCIPAL ---
st.title("🏗️ Panel de Soluciones Grupo Besco")
st.markdown("""
Bienvenido al sistema de gestión operativa. 
Selecciona una de las herramientas en la barra lateral para comenzar.
""")

st.divider()

# --- ACCESOS RÁPIDOS ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Cotizaciones")
    st.write("Cálculo de presupuestos y gestión de preciarios.")
    if st.button("Ir a Cotizaciones"):
        st.switch_page("pages/01_Cotizaciones.py")

with col2:
    st.markdown("### 📸 Reporte General")
    st.write("Generación de reportes fotográficos en campo.")
    if st.button("Ir a Reportes"):
        st.switch_page("pages/02_Reporte_General.py")

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.markdown("### 📑 Nestlé")
    st.write("Levantamiento y mantenimiento de activos.")
    if st.button("Ir a Nestlé"):
        st.switch_page("pages/03_Nestle.py")

with col4:
    st.markdown("### 🚀 Reserva")
    st.write("Módulo en desarrollo para futuras herramientas.")
    if st.button("Ir a Reserva"):
        st.switch_page("pages/04_Proximas_Apps.py")

# --- FOOTER ---
st.sidebar.success("Selecciona una opción arriba")
