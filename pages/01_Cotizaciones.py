import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_gspread_client

st.title("📄 Cotizaciones")

def cargar_preciario():
    try:
        client = obtener_gspread_client()
        workbook = client.open("PRECIARIO_SODEXO")
        return pd.DataFrame(workbook.sheet1.get_all_records())
    except: return pd.DataFrame()

df = cargar_preciario()
cliente = st.text_input("Nombre del Cliente")
# Aquí iría toda tu lógica de cotización y descarga de PDF
st.info("Módulo de cotizaciones activo.")
