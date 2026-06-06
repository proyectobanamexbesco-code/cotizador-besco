import streamlit as st

st.set_page_config(page_title="Panel Grupo Besco", layout="wide")

st.title("Panel de soluciones Grupo Besco")
st.markdown("Bienvenido al sistema operativo. Selecciona una herramienta desde la barra lateral:")

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 📄 Cotizaciones")
    st.caption("Accede al módulo de cálculo y preciarios.")
with col2:
    st.markdown("### 📸 Reporte Fotográfico")
    st.caption("Generador de evidencias técnicas.")

st.divider()

col3, col4 = st.columns(2)
with col3:
    st.markdown("### 📑 Nestlé")
    st.caption("Levantamiento y mantenimiento de equipos Nestlé.")
