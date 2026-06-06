import streamlit as st
import pandas as pd
from utils import obtener_gspread_client, enviar_correo, BESCO_PDF, analizar_reporte_con_gemini
from datetime import date

st.title("📑 Módulo Nestlé")

# Carga de datos
client = obtener_gspread_client()
df = pd.DataFrame(client.open("NESTLE").worksheet("NESTLE").get_all_records())
df.columns = [str(c).strip().upper() for c in df.columns]

# Filtros e Interfaz
area_sel = st.selectbox("Área", ["-- Todas --"] + sorted(df["AREA"].dropna().unique().tolist()))
df_f = df[df["AREA"] == area_sel] if area_sel != "-- Todas --" else df
equipo_sel = st.selectbox("Equipo", ["-- Selecciona --"] + (df_f["ITEM"].astype(str) + " - " + df_f["DESCRIPCION DE EQUIPOS"]).tolist())

if equipo_sel != "-- Selecciona --":
    fila = df_f[df_f["ITEM"].astype(str) == equipo_sel.split(" - ")[0]].iloc[0]
    tecnico = st.text_input("Técnico", value="Oscar Salto")
    obs = st.text_area("Observaciones")
    fa = st.file_uploader("Fotos Antes", accept_multiple_files=True)
    fd = st.file_uploader("Fotos Después", accept_multiple_files=True)
    
    if st.button("Generar y Enviar"):
        # 1. Crear PDF
        pdf = BESCO_PDF()
        pdf.add_page()
        pdf.cell(0, 10, f"Equipo: {fila['DESCRIPCION DE EQUIPOS']}", ln=True)
        pdf.photo_grid("Antes", fa)
        pdf.photo_grid("Después", fd)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        # 2. Enviar Correo
        dest = ["german.constantino@besco.mx", "andres.mayagoitia@besco.mx", "brenda.cervantes@besco.mx", "gerardo.mendez@besco.mx"]
        if enviar_correo(pdf_bytes, "Nestle", fila['ITEM'], "Reporte.pdf", "", dest):
            st.success("Reporte enviado correctamente")
        
        # 3. Resumen IA
        st.info(analizar_reporte_con_gemini(f"Item: {fila['ITEM']}, Obs: {obs}"))
