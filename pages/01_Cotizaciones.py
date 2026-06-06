import streamlit as st
import pandas as pd
import sys
import os
# Ajuste para importar utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_gspread_client

st.title("📄 Cotizaciones")

def cargar_preciario():
    try:
        client = obtener_gspread_client()
        # Asegúrate de que el nombre de la hoja coincida con tu archivo real
        workbook = client.open("PRECIARIO_SODEXO") 
        return pd.DataFrame(workbook.sheet1.get_all_records())
    except: return pd.DataFrame()

df = cargar_preciario()
if not df.empty:
    cliente = st.text_input("Nombre del Cliente")
    st.write("Selecciona tus conceptos aquí...")
else:
    st.warning("No se pudo cargar el preciario. Verifica el nombre de la hoja.")
