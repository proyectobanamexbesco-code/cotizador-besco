import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import smtplib
from email.message import EmailMessage
import io
import uuid
from pypdf import PdfWriter

# --- RUTAS PARA EL LOGOTIPO BESCO (MEJORADO PARA LA NUBE) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOGO_PATH = r"C:\Users\GerardoMendez\OneDrive - Grupo Besco\Escritorio\MisProyectos\logo.png"
CLOUD_LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
CLOUD_LOGO_JPG = os.path.join(BASE_DIR, "logo.jpg")
CLOUD_LOGO_BESCO = os.path.join(BASE_DIR, "logo besco 2026.jpeg") # ¡Corregido a "logo"!

if os.path.exists(LOCAL_LOGO_PATH):
    LOGO_PATH = LOCAL_LOGO_PATH
elif os.path.exists(CLOUD_LOGO_PATH):
    LOGO_PATH = CLOUD_LOGO_PATH
elif os.path.exists(CLOUD_LOGO_JPG):
    LOGO_PATH = CLOUD_LOGO_JPG
elif os.path.exists(CLOUD_LOGO_BESCO):
    LOGO_PATH = CLOUD_LOGO_BESCO
else:
    LOGO_PATH = None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BESCO | Evidencia Técnica", layout="wide")
