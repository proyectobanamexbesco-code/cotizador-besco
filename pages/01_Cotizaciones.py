import streamlit as st
import pandas as pd
from utils import obtener_gspread_client, BESCO_PDF
from fpdf import FPDF
from datetime import date

st.title("📄 Cotizaciones")

def cargar_preciario():
    try:
        client = obtener_gspread_client()
        workbook = client.open("PRECIARIO_SODEXO")
        return pd.DataFrame(workbook.sheet1.get_all_records())
    except: return pd.DataFrame()

df_precios = cargar_preciario()
cliente = st.text_input("Nombre del Cliente")
conceptos = st.multiselect("Selecciona conceptos", df_precios["DESCRIPCION"].tolist() if not df_precios.empty else [])

if st.button("Generar PDF de Cotización"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Cotización para: {cliente}", ln=True)
    pdf.set_font("Arial", size=12)
    for c in conceptos:
        pdf.cell(0, 10, f"- {c}", ln=True)
    
    st.download_button("Descargar PDF", data=pdf.output(dest='S').encode('latin-1'), file_name="Cotizacion.pdf", mime="application/pdf")
