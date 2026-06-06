import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
import uuid
import os
from PIL import Image
import google.generativeai as genai

def obtener_gspread_client():
    creds_dict = {k: st.secrets["gcp_service_account"][k] for k in ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]}
    return gspread.authorize(Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

def enviar_correo(pdf_bytes, cliente, folio, nombre_archivo, corr_extra, destinatarios):
    try:
        remitente, password = st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"]
        destinatarios_totales = list(set(destinatarios + ([c.strip() for c in corr_extra.split(",")] if corr_extra else [])))
        msg = EmailMessage()
        msg['Subject'] = f"Reporte: {cliente} | {folio}"
        msg['From'], msg['To'] = remitente, ", ".join(destinatarios_totales)
        msg.set_content("Reporte generado automáticamente.")
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except: return False

def analizar_reporte_con_gemini(datos):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(f"Actúa como ingeniero senior de Besco. Resume este reporte técnico: {datos}").text
    except Exception as e: return f"Error IA: {e}"

class BESCO_PDF(FPDF):
    def header(self): self.set_font('Arial', 'B', 12); self.cell(0, 10, 'REPORTE BESCO', 0, 1, 'R')
    def add_custom_section(self, title): self.set_fill_color(30,58,95); self.set_text_color(255); self.cell(0, 8, title, 0, 1, 'L', fill=True); self.set_text_color(0); self.ln(2)
    def photo_grid(self, title, photos):
        if not photos: return
        self.add_custom_section(title)
        for foto in photos:
            temp_p = f"temp_{uuid.uuid4().hex}.jpg"; Image.open(foto).convert("RGB").save(temp_p, format="JPEG")
            self.image(temp_p, w=80); os.remove(temp_p)
