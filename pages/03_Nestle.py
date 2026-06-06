import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_gspread_client, enviar_correo, BESCO_PDF, analizar_reporte_con_gemini

st.title("📑 Módulo Nestlé")

client = obtener_gspread_client()
df = pd.DataFrame(client.open("NESTLE").worksheet("NESTLE").get_all_records())
df.columns = [str(c).strip().upper() for c in df.columns]

area = st.selectbox("Área", sorted(df["AREA"].dropna().unique()))
equipo = st.selectbox("Equipo", df[df["AREA"]==area]["ITEM"].tolist())

obs = st.text_area("Observaciones")
if st.button("Generar y Enviar"):
    pdf = BESCO_PDF()
    pdf.add_page()
    pdf.cell(0, 10, f"Equipo: {equipo}", ln=True)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    dest = ["german.constantino@besco.mx", "andres.mayagoitia@besco.mx", "brenda.cervantes@besco.mx", "gerardo.mendez@besco.mx"]
    enviar_correo(pdf_bytes, "Nestle", equipo, "Reporte.pdf", "", dest)
    st.info(analizar_reporte_con_gemini(f"Equipo {equipo}, Obs: {obs}"))
