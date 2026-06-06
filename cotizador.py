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

# --- RESOLUCIÓN Y ENRUTAMIENTO DE LOGOTIPOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOGO_PATH = r"C:\Users\GerardoMendez\OneDrive - Grupo Besco\Escritorio\MisProyectos\logo.png"
CLOUD_LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
CLOUD_LOGO_JPG = os.path.join(BASE_DIR, "logo.jpg")
CLOUD_LOGO_BESCO = os.path.join(BASE_DIR, "logo besco 2026.jpeg")

if os.path.exists(LOCAL_LOGO_PATH): LOGO_PATH = LOCAL_LOGO_PATH
elif os.path.exists(CLOUD_LOGO_PATH): LOGO_PATH = CLOUD_LOGO_PATH
elif os.path.exists(CLOUD_LOGO_JPG): LOGO_PATH = CLOUD_LOGO_JPG
elif os.path.exists(CLOUD_LOGO_BESCO): LOGO_PATH = CLOUD_LOGO_BESCO
else: LOGO_PATH = None

# --- ESTILOS ---
st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE CONEXIÓN Y DATOS ---
def obtener_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
    }
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=120)
def cargar_listado_equipos():
    try:
        client = obtener_gspread_client()
        try: workbook = client.open("NESTLE")
        except: workbook = client.open("nestle")
        try: sheet = workbook.worksheet("NESTLE")
        except: sheet = workbook.worksheet("nestle")
        return pd.DataFrame(sheet.get_all_records())
    except: return pd.DataFrame()

def actualizar_fecha_nestle(item_val, fecha_str):
    try:
        client = obtener_gspread_client()
        workbook = client.open("NESTLE")
        sheet = workbook.worksheet("NESTLE")
        headers = [str(h).strip().upper() for h in sheet.row_values(1)]
        col_item_idx = headers.index("ITEM") + 1
        col_values = sheet.col_values(col_item_idx)
        if str(item_val) in col_values:
            row_idx = col_values.index(str(item_val)) + 1
            col_fecha_name = "FECHA DE MANTENIMIENTO"
            if col_fecha_name in headers:
                col_fecha_idx = headers.index(col_fecha_name) + 1
            else:
                col_fecha_idx = len(headers) + 1
                sheet.update_cell(1, col_fecha_idx, col_fecha_name)
            sheet.update_cell(row_idx, col_fecha_idx, fecha_str)
            cargar_listado_equipos.clear()
            return True
    except: return False
    return False

def analizar_reporte_con_gemini(cliente, tecnico, fecha, item, area, frecuencia, observaciones):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Como experto de Besco, resume este reporte: Cliente {cliente}, Técnico {tecnico}, Fecha {fecha}, Item {item}, Área {area}, Frecuencia {frecuencia}, Observaciones: {observaciones}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Error IA: {e}"

class BESCO_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12); self.cell(0, 10, 'REPORTE BESCO - NESTLE', 0, 1, 'R')
    def add_custom_section(self, title):
        self.set_fill_color(30, 58, 95); self.set_text_color(255); self.cell(0, 8, title, 0, 1, 'L', fill=True)
        self.set_text_color(0); self.ln(2)
    def photo_grid(self, title, photos, prefix="img"):
        if not photos: return
        self.add_custom_section(title)
        for i, foto in enumerate(photos):
            temp_p = f"temp_{prefix}_{uuid.uuid4().hex}.jpg"
            Image.open(foto).convert("RGB").save(temp_p, format="JPEG")
            self.image(temp_p, w=80)

def enviar_correo(pdf_bytes, cliente, folio, sucursal, office, nombre_archivo, corr_extra, f_ejec, destinatarios_base):
    try:
        remitente, password = st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"]
        destinatarios = list(set(destinatarios_base + ([c.strip() for c in corr_extra.split(",")] if corr_extra else [])))
        msg = EmailMessage()
        msg['Subject'] = f"Reporte Nestlé: {cliente} | {folio}"
        msg['From'], msg['To'] = remitente, ", ".join(destinatarios)
        msg.set_content("Reporte generado automáticamente.")
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except: return False

# --- LÓGICA PRINCIPAL ---
if 'app_actual' not in st.session_state: st.session_state.app_actual = "Menu"

with st.sidebar:
    if st.button("📑 Nestle"): st.session_state.app_actual = "OtraApp"; st.rerun()

if st.session_state.app_actual == "OtraApp":
    st.title("📑 Nestle")
    df_equipos = cargar_listado_equipos()
    if not df_equipos.empty:
        df_equipos.columns = [str(c).strip().upper() for c in df_equipos.columns]
        area_sel = st.selectbox("Área", ["-- Todas --"] + sorted(df_equipos["AREA"].dropna().unique().tolist()))
        df_f = df_equipos[df_equipos["AREA"] == area_sel] if area_sel != "-- Todas --" else df_equipos
        equipo_sel = st.selectbox("Equipo", ["-- Selecciona --"] + (df_f["ITEM"].astype(str) + " - " + df_f["DESCRIPCION DE EQUIPOS"]).tolist())
        
        if equipo_sel != "-- Selecciona --":
            fila = df_f[df_f["ITEM"].astype(str) == equipo_sel.split(" - ")[0]].iloc[0]
            tecnico_lev = st.text_input("Técnico", value="Oscar Salto")
            actividades = st.text_area("Observaciones")
            fa = st.file_uploader("Antes", accept_multiple_files=True)
            fd = st.file_uploader("Después", accept_multiple_files=True)
            
            dest = ["german.constantino@besco.mx", "andres.mayagoitia@besco.mx", "brenda.cervantes@besco.mx", "gerardo.mendez@besco.mx"]
            if st.button("Generar y Enviar"):
                pdf = BESCO_PDF()
                pdf.add_page()
                pdf.add_custom_section("Datos")
                pdf.cell(0, 10, f"Item: {fila['ITEM']} | Área: {fila['AREA']}", ln=True)
                pdf.photo_grid("Antes", fa, "ant")
                pdf.photo_grid("Después", fd, "desp")
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                if enviar_correo(pdf_bytes, "Nestle", fila['ITEM'], fila['AREA'], "Nestle", "Reporte.pdf", "", str(date.today()), dest):
                    st.success("Enviado")
                actualizar_fecha_nestle(fila['ITEM'], str(date.today()))
                st.info(analizar_reporte_con_gemini("Nestle", tecnico_lev, str(date.today()), fila['ITEM'], fila['AREA'], fila['FRECUENCIA'], actividades))
