import streamlit as st
import pandas as pd
from datetime import date
import os
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
import tempfile
from PIL import Image

# CRUCIAL: La configuración de página debe ser el primer comando de Streamlit
st.set_page_config(page_title="Panel Central de Aplicaciones", layout="wide")

# ==========================================
# FUNCIONES MAESTRAS Y AYUDANTES GLOBALES
# ==========================================

def limpiar_texto(texto):
    if not isinstance(texto, str):
        return str(texto)
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U'
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto

def callback_guardar_todo(df, folio, fecha_cot, nom_cli, inst_cli, dir_cli, tel_cli, em_cli, cotizador, puesto, em_cot, tel_cot, desc, ubi, sub, iva, tot, moneda, entrega, pago, vig, gar):
    try:
        if "mensaje_exito" in st.session_state:
            del st.session_state.mensaje_exito
        if "mensaje_error" in st.session_state:
            del st.session_state.mensaje_error

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
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
        client = gspread.authorize(creds)
        
        sheet = client.open("Historial Cotizaciones Besco").sheet1
        
        for _, fila in df.iterrows():
            nueva_fila = [
                str(folio), str(fecha_cot), str(nom_cli), str(inst_cli), str(dir_cli),
                str(tel_cli), str(em_cli), str(cotizador), str(puesto), str(em_cot),
                str(tel_cot), str(desc), str(ubi), float(sub), float(iva),
                float(tot), str(moneda), str(entrega), str(pago), str(vig),
                str(gar), str(fila["Tipo"]), str(fila["Concepto"]), float(fila["Cant."]),
                str(fila["Unidad"]), float(fila["Costo U."]), float(fila["Precio Venta"]), float(fila["Importe"])
            ]
            sheet.append_row(nueva_fila)
        
        st.session_state.mensaje_exito = f"¡Cotización {folio} registrada exitosamente en Google Sheets y PDF descargado!"
    except Exception as e:
        st.session_state.mensaje_error = f"Error crítico al conectar con Google Sheets: {str(e)}."

# ==========================================
# SISTEMA DE NAVEGACIÓN ENTRE APLICACIONES
# ==========================================

if 'app_actual' not in st.session_state:
    st.session_state.app_actual = "Menu"

def cambiar_pantalla(nombre_app):
    st.session_state.app_actual = nombre_app
    st.rerun()

# Barra lateral persistente
with st.sidebar:
    st.markdown("### 🛠️ Navegación Global")
    if st.button("🏠 Menú de Aplicaciones", use_container_width=True):
        cambiar_pantalla("Menu")
    st.divider()
    st.markdown("**Accesos Directos:**")
    if st.button("📄 Cotizador Industrial", use_container_width=True):
        cambiar_pantalla("Cotizaciones")
    if st.button("📸 Evidencia Técnica", use_container_width=True):
        cambiar_pantalla("Reportes")
    if st.button("🚀 Próxima Aplicación", use_container_width=True):
        cambiar_pantalla("OtraApp")

# ==========================================
# VISTA 1: MENÚ CENTRAL
# ==========================================
if st.session_state.app_actual == "Menu":
    st.title("💼 Panel Integrado de Soluciones Corporativas")
    st.markdown("Bienvenido al centro de mando operativo. Selecciona la plataforma que deseas desplegar:")
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📄 Cotizador Industrial")
        st.caption("Cálculo automatizado de márgenes, diseño de presupuestos en PDF y sincronización con Google Sheets.")
        if st.button("Desplegar Cotizador", key="launch_cot", use_container_width=True, type="primary"):
            cambiar_pantalla("Cotizaciones")
            
    with col2:
        st.markdown("### 📸 Evidencia Técnica")
        st.caption("Sistema de Evidencia Técnica Alducin Aire Acondicionado Industrial para registros fotográficos.")
        if st.button("Desplegar Reportes", key="launch_rep", use_container_width=True, type="primary"):
            cambiar_pantalla("Reportes")
            
    with col3:
        st.markdown("### 🚀 Próxima Aplicación")
        st.caption("Módulo en reserva configurado para recibir la integración de un nuevo flujo de trabajo.")
        if st.button("Desplegar Nueva App", key="launch_otra", use_container_width=True):
            cambiar_pantalla("OtraApp")

# ==========================================
# VISTA 2: APP DE COTIZACIONES
# ==========================================
elif st.session_state.app_actual == "Cotizaciones":
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("⬅️ Volver", key="back_to_menu_cot", use_container_width=True):
            cambiar_pantalla("Menu")
            
    col_header1, col_header2 = st.columns([2, 1])
    with col_header1:
        st.markdown("### Grupo Besco S.A. de C.V.")
        st.markdown("**Dirección:** Jose Ignacio Bartolache numero 1910")

    folio_placeholder = col_header2.empty()
    st.divider()
    st.title("Generador de Cotizaciones de Mantenimiento")

    st.header("1. Datos del Proyecto y Cotizador")
    col_cot1, col_cot2 = st.columns(2)
    with col_cot1:
        nombre_cotizador = st.text_input("Responsable de cotización", value="Gerardo Méndez")
        puesto_cotizador = st.selectbox("Puesto del Responsable", ["Gerente Regional", "Gerente de Servicio", "Jefe de oficina", "Supervisor"])
        email_cotizador = st.text_input("E-mail del cotizador", value="gerardo.mendez@besco.mx")
        descripcion_cotizacion = st.text_input("Descripción de
