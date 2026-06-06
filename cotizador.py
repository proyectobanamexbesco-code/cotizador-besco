import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import smtplib
from email.message import EmailMessage
import io
import uuid
from pypdf import PdfWriter
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image
import google.generativeai as genai

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Panel de soluciones Grupo Besco", layout="wide")

# --- RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# (Configuración de logos existente)
LOGO_PATH = None 

# --- ESTILOS ---
st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE CONEXIÓN ---
def obtener_gspread_client():
    creds_dict = {k: st.secrets["gcp_service_account"][k] for k in ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]}
    return gspread.authorize(Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

def limpiar_texto(t): return str(t).replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

def enviar_correo(pdf_bytes, cliente, folio, sucursal, office, nombre_archivo, corr_extra, destinatarios):
    try:
        remitente, password = st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"]
        msg = EmailMessage()
        msg['Subject'] = f"Reporte: {cliente} | {folio}"
        msg['From'], msg['To'] = remitente, ", ".join(list(set(destinatarios + ([c.strip() for c in corr_extra.split(",")] if corr_extra else []))))
        msg.set_content("Reporte generado.")
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except: return False

def analizar_reporte_con_gemini(cliente, tecnico, fecha, item, area, frecuencia, obs):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(f"Resume este reporte técnico de Besco: {cliente}, {tecnico}, {fecha}, {item}, {area}, {frecuencia}, {obs}").text
    except Exception as e: return f"Error IA: {e}"

# --- NAVEGACIÓN ---
if 'app_actual' not in st.session_state: st.session_state.app_actual = "Menu"
with st.sidebar:
    if st.button("🏠 Inicio"): st.session_state.app_actual = "Menu"; st.rerun()
    if st.button("📄 Cotizaciones"): st.session_state.app_actual = "Cotizaciones"; st.rerun()
    if st.button("📸 Reporte General"): st.session_state.app_actual = "Reportes"; st.rerun()
    if st.button("📑 Nestle"): st.session_state.app_actual = "OtraApp"; st.rerun()
    if st.button("🚀 Reserva"): st.session_state.app_actual = "OtraApp2"; st.rerun()

# --- VISTAS ---
if st.session_state.app_actual == "Menu":
    st.title("Panel Grupo Besco")
    # (Botones de navegación principal aquí)

elif st.session_state.app_actual == "Cotizaciones":
    # (Código existente de cotizaciones)
    pass

elif st.session_state.app_actual == "Reportes":
    # (Código existente de reportes fotográficos)
    pass

elif st.session_state.app_actual == "OtraApp":
    st.title("📑 Nestle")
    df = cargar_listado_equipos()
    if not df.empty:
        df.columns = [str(c).strip().upper() for c in df.columns]
        area_sel = st.selectbox("Área", ["-- Todas --"] + sorted(df["AREA"].dropna().unique().tolist()))
        df_f = df[df["AREA"] == area_sel] if area_sel != "-- Todas --" else df
        equipo_sel = st.selectbox("Equipo", ["-- Selecciona --"] + (df_f["ITEM"].astype(str) + " - " + df_f["DESCRIPCION DE EQUIPOS"]).tolist())
        
        if equipo_sel != "-- Selecciona --":
            fila = df_f[df_f["ITEM"].astype(str) == equipo_sel.split(" - ")[0]].iloc[0]
            tecnico = st.text_input("Técnico", value="Oscar Salto")
            obs = st.text_area("Observaciones")
            if st.button("Generar y Enviar"):
                # Aquí va la lógica de PDF, Correo (con destinatarios german, andres, brenda, gerardo) y Actualización de Fecha
                pass

elif st.session_state.app_actual == "OtraApp2":
    st.title("🚀 Próxima Aplicación 2")
