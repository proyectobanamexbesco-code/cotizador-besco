import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import BESCO_PDF, enviar_correo

st.title("📸 Reporte Fotográfico General")

cliente = st.text_input("Cliente")
folio = st.text_input("Folio")
fa = st.file_uploader("Fotos Antes", accept_multiple_files=True)
fd = st.file_uploader("Fotos Después", accept_multiple_files=True)

if st.button("Generar y Enviar"):
    pdf = BESCO_PDF()
    pdf.add_page()
    pdf.cell(0, 10, f"Reporte: {cliente}", ln=True)
    pdf.photo_grid("Antes", fa)
    pdf.photo_grid("Después", fd)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    if enviar_correo(pdf_bytes, cliente, folio, "Reporte.pdf", "", ["gerardo.mendez@besco.mx"]):
        st.success("Reporte enviado")
