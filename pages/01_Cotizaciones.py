import streamlit as st
import pandas as pd
from utils import obtener_gspread_client

st.title("📄 Cotizaciones - Sistema Besco")

def cargar_preciario():
    try:
        client = obtener_gspread_client()
        sheet = client.open("PRECIARIO_SODEXO").sheet1
        return pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = cargar_preciario()
if not df.empty:
    with st.form("cotizador_form"):
        cliente = st.text_input("Nombre del Cliente")
        conceptos = st.multiselect("Conceptos", df["DESCRIPCION"].tolist())
        # Aquí puedes añadir campos de precio unitario y cantidad
        if st.form_submit_button("Generar Cotización"):
            if cliente and conceptos:
                st.success(f"Procesando cotización para {cliente}...")
                # Lógica de FPDF aquí para generar el PDF
            else:
                st.warning("Completa los campos obligatorios.")
