import streamlit as st
from utils import BESCO_PDF, enviar_correo

st.title("📸 Reporte Fotográfico General")

cliente = st.text_input("Cliente")
folio = st.text_input("Folio")
tecnico = st.text_input("Técnico")
fa = st.file_uploader("Fotos Antes", accept_multiple_files=True)
fd = st.file_uploader("Fotos Después", accept_multiple_files=True)

if st.button("Generar y Enviar Reporte"):
    pdf = BESCO_PDF()
    pdf.add_page()
    pdf.cell(0, 10, f"Reporte para: {cliente} | Folio: {folio}", ln=True)
    pdf.photo_grid("Antes", fa)
    pdf.photo_grid("Después", fd)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    dest = ["gerardo.mendez@besco.mx"]
    if enviar_correo(pdf_bytes, cliente, folio, "Reporte_General.pdf", "", dest):
        st.success("Reporte enviado exitosamente")
    else:
        st.error("Error al enviar el correo")
