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

# --- CONFIGURACIÓN DE PÁGINA TRUNK (DEBE SER EL PRIMER COMANDO) ---
st.set_page_config(page_title="Panel Central de Aplicaciones - Grupo Besco", layout="wide")

# --- RESOLUCIÓN Y ENRUTAMIENTO DE LOGOTIPOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOGO_PATH = r"C:\Users\GerardoMendez\OneDrive - Grupo Besco\Escritorio\MisProyectos\logo.png"
CLOUD_LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
CLOUD_LOGO_JPG = os.path.join(BASE_DIR, "logo.jpg")
CLOUD_LOGO_BESCO = os.path.join(BASE_DIR, "logo besco 2026.jpeg")

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

# --- ESTILOS VISUALES CORPORATIVOS ---
st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    div[data-testid="stExpander"] div[role="button"] p { font-weight: bold !important; color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# CLASES ESPECIALIZADAS (REPORTE FOTOGRÁFICO)
# ==========================================
class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                img_logo = Image.open(LOGO_PATH).convert("RGB")
                temp_logo = "temp_logo_principal.jpg"
                img_logo.save(temp_logo, format="JPEG")
                
                orig_w, orig_h = img_logo.size
                final_h = 25
                escala = final_h / orig_h
                final_w = orig_w * escala
                
                self.image(temp_logo, x=10, y=8, w=final_w, h=final_h)
            except Exception:
                self.set_font('Arial', 'I', 8)
                self.set_xy(10, 10)
                self.cell(0, 10, f"(Error al procesar logo)")
                
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, 'REPORTE DE SERVICIO TÉCNICO - BESCO', 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.set_x(100)
        self.cell(0, 5, f"Emisión del Reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        self.ln(12)

    def add_custom_section(self, title):
        if self.get_y() > 250:
            self.add_page()
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"{self.section_count}. {title.upper()}", 0, 1, 'L', fill=True)
        self.section_count += 1
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def photo_grid(self, title, photos, eq_index=0, prefix="img"):
        if not photos: return
        
        if self.get_y() > 240:
            self.add_page()
            
        self.add_custom_section(title)
        ancho_foto, alto_foto, espacio_v = 90, 65, 72
        
        for i, foto in enumerate(photos):
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_p = f"temp_{prefix}_{uuid.uuid4().hex}.jpg"
            img.save(temp_p, format="JPEG")
            
            col = i % 2
            
            if col == 0 and (self.get_y() + alto_foto > 265):
                self.add_page()
                self.set_font('Arial', 'I', 9)
                self.set_text_color(100, 100, 100)
                self.cell(0, 6, f"(Continuación) {title}", 0, 1, 'L')
                self.set_text_color(0, 0, 0)
                self.ln(2)
                
            y_act = self.get_y()
            self.image(temp_p, x=10 + (col * 95), y=y_act, w=ancho_foto, h=alto_foto)
            
            if col == 1 or i == len(photos) - 1:
                self.set_y(y_act + espacio_v)
        self.ln(2)

    def folio_grid(self, title, photo_files):
        if not photo_files: return
        for i, foto in enumerate(photo_files[:4]):
            self.add_page()
            self.add_custom_section(f"{title} - Evidencia {i+1}")
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_folio = f"temp_folio_{uuid.uuid4().hex}.jpg"
            img.save(temp_folio, format="JPEG")
            
            avail_w, avail_h = 190, 240
            img_w, img_h = img.size
            escala = min(avail_w/img_w, avail_h/img_h)
            final_w, final_h = img_w * escala, img_h * escala
            self.image(temp_folio, x=10 + (190 - final_w) / 2, y=self.get_y() + 5, w=final_w, h=final_h)

# ==========================================
# FUNCIONES OPERATIVAS MIGRADAS
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

def callback_guardar_cotizacion(df, folio, fecha_cot, nom_cli, inst_cli, dir_cli, tel_cli, em_cli, cotizador, puesto, em_cot, tel_cot, desc, ubi, sub, iva, tot, moneda, entrega, pago, vig, gar):
    try:
        client = obtener_gspread_client()
        sheet = client.open("Historial Cotizaciones Besco").sheet1
        for _, fila in df.iterrows():
            nueva_fila = [
                str(folio), str(fecha_cot), str(nom_cli), str(inst_cli), str(dir_cli),
                str(tel_cli), str(em_cli), str(cotizador), str(puesto), str(em_cot),
                str(tel_cot), str(desc), str(ubi), float(sub), float(iva), float(tot),
                str(moneda), str(entrega), str(pago), str(vig), str(gar),
                str(fila["Tipo"]), str(fila["Concepto"]), float(fila["Cant."]),
                str(fila["Unidad"]), float(fila["Costo U."]), float(fila["Precio Venta"]), float(fila["Importe"])
            ]
            sheet.append_row(nueva_fila)
        st.session_state.mensaje_exito = f"¡Cotización {folio} registrada en Google Sheets y PDF descargado!"
    except Exception as e:
        st.session_state.mensaje_error = f"Error al conectar con Google Sheets: {str(e)}"

def enviar_correo(pdf_bytes, cliente, folio, sucursal, office, nombre_archivo, corr_extra, f_ejec, destinatarios_base):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            st.error("❌ Error de configuración: Faltan credenciales 'EMAIL_SENDER' o 'EMAIL_PASSWORD' en Secrets.")
            return False

        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        destinatarios = list(set(destinatarios_base + ([c.strip() for c in corr_extra.split(",")] if corr_extra else [])))

        msg = EmailMessage()
        msg['Subject'] = f"Reporte Fotográfico BESCO: {cliente} | TK: {folio} | Of: {office}"
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios) 
        msg.set_content(f"Se ha generado un nuevo reporte desde el Sistema de Evidencia Técnica BESCO.\n\nFecha Ejecución: {f_ejec}\nOficina: {office}\nCliente: {cliente}\nFolio: {folio}\nSucursal: {sucursal}")
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Error de conexión SMTP: {e}")
        return False

# ==========================================
# GESTIÓN DE INTERFAZ Y FLUJOS (NAVEGACIÓN)
# ==========================================
if 'app_actual' not in st.session_state:
    st.session_state.app_actual = "Menu"

def cambiar_pantalla(nombre_app):
    st.session_state.app_actual = nombre_app
    st.rerun()

with st.sidebar:
    st.markdown("### 🛠️ Menú de Aplicaciones")
    if st.button("🏠 Inicio (Panel Central)", use_container_width=True): cambiar_pantalla("Menu")
    st.divider()
    if st.button("📄 Cotizador Industrial", use_container_width=True): cambiar_pantalla("Cotizaciones")
    if st.button("📸 Evidencia Técnica BESCO", use_container_width=True): cambiar_pantalla("Reportes")
    if st.button("🚀 Próxima Aplicación", use_container_width=True): cambiar_pantalla("OtraApp")

# ==========================================
# VISTA 1: MENÚ CENTRAL (EL APARTADO ANTES)
# ==========================================
if st.session_state.app_actual == "Menu":
    st.title("💼 Panel Integrado de Soluciones - Grupo Besco")
    st.markdown("Selecciona la herramienta operativa que deseas desplegar:")
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📄 Cotizador Industrial")
        st.caption("Cálculo dinámico de utilidades, protección anti-empalmes en PDF y guardado centralizado en Google Sheets.")
        if st.button("Desplegar Cotizador", key="btn_cot", use_container_width=True, type="primary"): cambiar_pantalla("Cotizaciones")
    with col2:
        st.markdown("### 📸 Evidencia Técnica BESCO")
        st.caption("Sistema de Evidencia Técnica Alducin. Carga múltiple de imágenes, fusión de reportes PDF y envío por correo electrónico.")
        if st.button("Desplegar Herramienta de Campo", key="btn_rep", use_container_width=True, type="primary"): cambiar_pantalla("Reportes")
    with col3:
        st.markdown("### 🚀 Próxima Aplicación")
        st.caption("Módulo en reserva listo para recibir la lógica de tus siguientes flujos automatizados.")
        if st.button("Desplegar Nueva App", key="btn_otra", use_container_width=True): cambiar_pantalla("OtraApp")

# ==========================================
# VISTA 2: COTIZADOR INDUSTRIAL
# ==========================================
elif st.session_state.app_actual == "Cotizaciones":
    if st.button("静态 ⬅️ Volver al Panel Principal", key="v_cot"): cambiar_pantalla("Menu")
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown("### Grupo Besco S.A. de C.V.")
        st.markdown("**Dirección:** Jose Ignacio Bartolache numero 1910")
    folio_placeholder = col_h2.empty()
    st.title("Generador de Cotizaciones de Mantenimiento")
    
    st.header("1. Datos del Proyecto y Cotizador")
    c1, c2 = st.columns(2)
    with c1:
        nombre_cotizador = st.text_input("Responsable de cotización", value="Gerardo Méndez")
        puesto_cotizador = st.selectbox("Puesto del Responsable", ["Gerente Regional", "Gerente de Servicio", "Jefe de oficina", "Supervisor"])
        email_cotizador = st.text_input("E-mail del cotizador", value="gerardo.mendez@besco.mx")
        descripcion_cotizacion = st.text_input("Descripción (Ej. Mantenimiento Preventivo)")
    with c2:
        fecha = st.date_input("Fecha de Cotización", date.today())
        telefono_cotizador = st.text_input("Teléfono de contacto (Cotizador)")
        ubicacion = st.text_input("Ubicación del Servicio")

    st.header("2. Datos del Cliente")
    cc1, cc2 = st.columns(2)
    with cc1:
        nombre_cliente = st.text_input("Nombre cliente:")
        institucion_cliente = st.text_input("Institución / Cliente:")
        direccion_cliente = st.text_input("Dirección:")
    with cc2:
        telefono_cliente = st.text_input("Teléfono:")
        email_cliente = st.text_input("E-mail:")

    cliente_base = institucion_cliente if institucion_cliente else nombre_cliente
    if nombre_cotizador and cliente_base and descripcion_cotizacion:
        iniciales = "".join([p[0].upper() for p in nombre_cotizador.split() if p])
        numero_presupuesto = f"{iniciales}-{fecha.strftime('%d%m%Y')}-{cliente_base.replace(' ','').upper()[:6]}-{descripcion_cotizacion.replace(' ','').upper()[:6]}"
    else:
        numero_presupuesto = "Llenando datos..."
    folio_placeholder.success(f"**Folio de Cotización:**\n{numero_presupuesto}")

    st.header("3. Detalles del Servicio")
    if 'conceptos' not in st.session_state: st.session_state.conceptos = []
    with st.form("add_concepto", clear_on_submit=True):
        cs1, cs2 = st.columns([1, 2])
        tipo_servicio = cs1.selectbox("Tipo de Servicio", ["Aire Acondicionado", "Eléctrico", "Luminarias", "Hidrosanitario", "Acabados", "Otros"])
        concepto = cs2.text_input("Concepto o Descripción detallada")
        cx1, cx2, cx3, cx4, cx5 = st.columns([1, 1, 1.2, 1.2, 1])
        cantidad = cx1.number_input("Cantidad", min_value=0.01, value=1.00)
        tipo_unidad = cx2.selectbox("Unidad", ["Pieza", "Caja", "Metro", "Metro Lineal", "Kilo", "Metro Cuadrado (m2)", "Litro", "Servicio"])
        costo_unitario = cx3.number_input("Costo Unitario ($)", min_value=0.0, value=0.0)
        margen_utilidad = cx4.number_input("Utilidad (%)", min_value=0.0, value=23.50, step=0.50)
        if cx5.form_submit_button("Agregar Línea") and concepto.strip() != "":
            p_venta = costo_unitario * (1 + (margen_utilidad / 100))
            st.session_state.conceptos.append({
                "Tipo": tipo_servicio, "Concepto": concepto, "Cant.": cantidad,
                "Unidad": tipo_unidad, "Costo U.": costo_unitario, "Precio Venta": p_venta, "Importe": p_venta * cantidad
            })

    if st.session_state.conceptos:
        st.header("4. Resumen de Cotización")
        df_editado = st.data_editor(pd.DataFrame(st.session_state.conceptos), num_rows="dynamic", use_container_width=True)
        df_editado["Importe"] = df_editado["Cant."] * df_editado["Precio Venta"]
        subtotal = df_editado["Importe"].sum()
        iva, total = subtotal * 0.16, subtotal * 1.16
        
        st.metric("TOTAL COTIZADO", f"${total:,.2f} MXN (Subtotal: ${subtotal:,.2f} + IVA)")
        
        st.header("5. Condiciones Comerciales")
        co1, co2 = st.columns(2)
        tipo_moneda = co1.selectbox("Moneda", ["Pesos Mexicanos", "Dólares de Estados Unidos"])
        tiempo_entrega = f"{int(co1.number_input('Días de Ejecución', min_value=1, value=15))} días hábiles"
        condiciones_pago = co1.selectbox("Pago", ["30% Anticipo / 70% al término", "50% Anticipo / 50% al término", "100% al término"])
        vigencia = f"{int(co2.number_input('Vigencia (Días)', min_value=1, value=15))} días hábiles"
        garantia = co2.text_input("Garantía", value="30 días sobre mano de obra")

        if st.button("Limpiar Tablas", key="clear_cot"):
            st.session_state.conceptos = []; st.rerun()

        if "mensaje_exito" in st.session_state: st.success(st.session_state.mensaje_exito)
        if "mensaje_error" in st.session_state: st.error(st.session_state.mensaje_error)
        
        pdf = FPDF()
        pdf.add_page()
        if LOGO_PATH and os.path.exists(LOGO_PATH): pdf.image(LOGO_PATH, x=10, y=5, w=66)
        pdf.set_fill_color(230, 230, 230); pdf.rect(10, 35, 190, 32, 'DF')
        pdf.set_y(37); pdf.set_font("Helvetica", "B", 10); pdf.cell(110, 5, "Grupo Besco S.A. de C.V."); pdf.cell(80, 5, f"Fecha: {fecha.strftime('%d/%m/%Y')}", ln=True, align="R")
        pdf.cell(110, 5, "Jose Ignacio Bartolache 1910, CDMX"); pdf.cell(80, 5, f"No. Presupuesto: {numero_presupuesto}", ln=True, align="R")
        pdf.cell(110, 5, f"Email: {limpiar_texto(email_cotizador)}"); pdf.cell(80, 5, f"Cotizador: {limpiar_texto(nombre_cotizador)}", ln=True, align="R")
        
        pdf.set_y(72); pdf.set_font("Helvetica", "B", 10); pdf.cell(100, 5, "DATOS DEL CLIENTE:"); pdf.cell(90, 5, "PROYECTO:", ln=True)
        pdf.set_font("Helvetica", size=9)
        y_c = pdf.get_y()
        pdf.set_xy(10, y_c); pdf.multi_cell(90, 4, f"Cliente: {limpiar_texto(nombre_cliente)}\nInst: {limpiar_texto(institucion_cliente)}\nDir: {limpiar_texto(direccion_cliente)}")
        y_l = pdf.get_y()
        pdf.set_xy(105, y_c); pdf.multi_cell(95, 4, f"Proyecto: {limpiar_texto(descripcion_cotizacion)}\nUbi: {limpiar_texto(ubicacion)}")
        pdf.set_y(max(y_l, pdf.get_y()) + 4)
        
        pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(220, 220, 220)
        pdf.cell(30, 6, "Tipo", 1, 0, "L", True); pdf.cell(75, 6, "Concepto", 1, 0, "L", True); pdf.cell(15, 6, "Cant", 1, 0, "C", True); pdf.cell(20, 6, "Unidad", 1, 0, "C", True); pdf.cell(25, 6, "Precio U.", 1, 0, "R", True); pdf.cell(25, 6, "Importe", 1, 1, "R", True)
        
        pdf.set_font("Helvetica", size=8)
        for _, fila in df_editado.iterrows():
            if pdf.get_y() > 250: pdf.add_page()
            y_s = pdf.get_y()
            pdf.set_xy(10, y_s + 1); pdf.multi_cell(30, 4, limpiar_texto(fila["Tipo"]))
            y_t = pdf.get_y()
            pdf.set_xy(40, y_s + 1); pdf.multi_cell(75, 4, limpiar_texto(fila["Concepto"]))
            y_co = pdf.get_y()
            pdf.set_xy(130, y_s + 1); pdf.multi_cell(20, 4, limpiar_texto(fila["Unidad"]), align="C")
            y_u = pdf.get_y()
            
            h_max = max(y_t, y_co, y_u) - y_s + 1.5
            if h_max < 6: h_max = 6
            pdf.set_xy(115, y_s); pdf.cell(15, h_max, f"{fila['Cant.']:.2f}", 0, 0, "C")
            pdf.set_xy(150, y_s); pdf.cell(25, h_max, f"${fila['Precio Venta']:.2f}", 0, 0, "R")
            pdf.set_xy(175, y_s); pdf.cell(25, h_max, f"${fila['Importe']:.2f}", 0, 1, "R")
            
            pdf.rect(10, y_s, 30, h_max); pdf.rect(40, y_s, 75, h_max); pdf.rect(115, y_s, 15, h_max); pdf.rect(130, y_s, 20, h_max); pdf.rect(150, y_s, 25, h_max); pdf.rect(175, y_s, 25, h_max)
            pdf.set_y(y_s + h_max)
            
        pdf.ln(3); pdf.set_font("Helvetica", "B", 9)
        pdf.cell(140, 5, ""); pdf.cell(25, 5, "Subtotal:", 1, 0); pdf.cell(25, 5, f"${subtotal:,.2f}", 1, 1, "R")
        pdf.cell(140, 5, ""); pdf.cell(25, 5, "I.V.A. 16%:", 1, 0); pdf.cell(25, 5, f"${iva:,.2f}", 1, 1, "R")
        pdf.cell(140, 5, ""); pdf.cell(25, 5, "TOTAL:", 1, 0, "L", True); pdf.cell(25, 5, f"${total:,.2f}", 1, 1, "R", True)
        
        pdf.ln(4); pdf.set_font("Helvetica", "B", 9); pdf.cell(0, 5, "CONDICIONES COMERCIALES:", ln=True)
        pdf.set_font("Helvetica", size=8)
        pdf.cell(0, 4, f"- Moneda: {limpiar_texto(tipo_moneda)} | Tiempo de Entrega: {limpiar_texto(tiempo_entrega)}", ln=True)
        pdf.cell(0, 4, f"- Pago: {limpiar_texto(condiciones_pago)} | Vigencia: {limpiar_texto(vigencia)} | Garantía: {limpiar_texto(garantia)}", ln=True)
        
        pdf.ln(3); pdf.set_font("Helvetica", "B", 6); pdf.cell(0, 3, "NOTAS IMPORTANTES:", ln=True)
        pdf.set_font("Helvetica", size=5.5)
        pdf.multi_cell(0, 3, "- Trabajos extraordinarios o refacciones se cobrarán por separado.\n- Precios basados en costos actuales; variaciones comprobables del mercado serán notificadas al cliente para ajuste.")
        
        pdf.ln(4); pdf.set_font("Helvetica", "B", 9); pdf.cell(0, 4, "ATENTAMENTE", ln=True, align="C")
        pdf.set_text_color(0, 112, 192); pdf.cell(0, 4, nombre_cotizador.upper(), ln=True, align="C")
        pdf.set_text_color(0,0,0); pdf.set_font("Helvetica", size=8); pdf.cell(0, 4, puesto_cotizador, ln=True, align="C")
        
        pdf.output("cotizacion_temp.pdf")
        with open("cotizacion_temp.pdf", "rb") as f: bytes_pdf = f.read()
        
        st.download_button(
            label="⚡ Guardar Historial y Descargar PDF", data=bytes_pdf, file_name=f"Cotizacion_{numero_presupuesto}.pdf",
            mime="application/pdf", use_container_width=True, on_click=callback_guardar_cotizacion,
            args=(df_editado, numero_presupuesto, fecha, nombre_cliente, institucion_cliente, direccion_cliente, telefono_cliente, email_cliente, nombre_cotizador, puesto_cotizador, email_cotizador, telefono_cotizador, descripcion_cotizacion, ubicacion, subtotal, iva, total, tipo_moneda, tiempo_entrega, condiciones_pago, vigencia, garantia)
        )

# ==========================================
# VISTA 3: EVIDENCIA TÉCNICA BESCO (ORIGINAL)
# ==========================================
elif st.session_state.app_actual == "Reportes":
    if st.button("⬅️ Volver al Panel Principal", key="v_rep"): cambiar_pantalla("Menu")
    if LOGO_PATH is None:
        st.warning("⚠️ Advertencia: No se encontró el archivo del logotipo en GitHub. El PDF se generará sin logotipo.")

    st.title("📑 Sistema de Evidencia Técnica BESCO")

    st.subheader("1. Identificación General del Servicio")
    c_g1, c_g2, c_g3 = st.columns([2, 1, 1.5])
    cliente = c_g1.text_input("Cliente")
    folio = c_g2.text_input("Folio / OT / TK", max_chars=20)
    fecha_ejecucion = c_g3.date_input("Fecha de Ejecución", datetime.now())

    col_loc1, col_loc2 = st.columns(2)
    sucursal = col_loc1.text_input("Sucursal / Inmueble")

    lista_oficinas = [
        "Acapulco", "Toluca", "Pachuca", "Michoacán", "Zonas/ CDMX", "CDMX", 
        "Ben & Company", "BX+", "Emerson", "Odoo", "Tampico"
    ]
    oficina = col_loc2.selectbox("Oficina Responsable", lista_oficinas)

    c_t1, c_t2, c_t3, c_t4 = st.columns(4)
    tecnico = c_t1.text_input("Técnico Asignado")
    supervisor = c_t2.text_input("Supervisor")
    tipo_serv = c_t3.selectbox("Servicio", ["Preventivo", "Correctivo", "Emergencia"])
    referencia = c_t4.selectbox("Referencia", ["Con Ticket", "Sin Ticket"])

    st.markdown("---")
    st.subheader("2. Evidencia Documental (Reporte Físico)")
    st.info("📌 Puede subir hasta 4 fotos (JPG/PNG) y/o archivos PDF del reporte firmado.")
    archivos_folio = st.file_uploader("Subir Folio BESCO", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    st.markdown("---")
    st.subheader("3. Equipos a Reportar")
    num_equipos = st.number_input("¿Cuántos equipos se atendieron?", min_value=1, max_value=20, value=1)

    leyendas_default = {
        "Conservación": "SE REALIZA REAPRIETE DE TORNILLERIA Y LUBRICACIÓN DE CHAPAS, BISAGRAS, SE HACE REVISIÓN DE ESTADO DE PINTURA, PISOS EXTINTORES Y MOBILIARIO.",
        "Hidrosanitario": "SE REALIZA REVISIÓN DE CESPOL, MEZCLADORA, MANGUERAS, LLAVES, WC, DESPACHADORES, EXTRACTORES Y CONEXIONES, SE DEJA FUNCIONANDO CORRECTAMENTE.",
        "Tableros Eléctricos": "SE REALIZA LIMPIEZA, REAPRIETE DE TORNILLERIA, TOMA DE AMPERAJES Y VOLTAJES, SE DEJA FUNCIONANDO CORRECTAMENTE.",
        "Iluminación": "SE REALIZA REVISIÓN GENERAL DE LÁMPARAS, SE CAMBIAN LAMPARAS FUNDIDAS, SE DEJA FUNCIONANDO CORRECTAMENTE.",
        "Aire Acondicionado": "SE REALIZA LIMPIEZA GENERAL DE SERPENTINES, TOMADO PRESIÓN DE REFRIGERANTE, VOLTAJES, AMPERAJES, REAPRIRTE DE CONEXIONES, LIMPIEZA DE FILTROS, SE DEJA FUNCIONANDO CORRECTAMENTE."
    }

    equipos_data = []
    for i in range(num_equipos):
        with st.expander(f"CONFIGURACIÓN EQUIPO {i+1}", expanded=True):
            cols_cat = st.columns(2)
            categorias_opciones = ["Ninguna", "Aire Acondicionado", "Tableros Eléctricos", "Hidroneumático", "Conservación", "Hidrosanitario", "Iluminación", "Otros"]
            esp = cols_cat[0].selectbox("Categoría", categorias_opciones, key=f"esp_{i}")
            estatus = cols_cat[1].selectbox("Estatus Final", ["Operando correctamente", "Operando con observaciones", "No queda operando"], key=f"est_{i}")
            
            meds, otros = {}, ""
            if esp == "Aire Acondicionado":
                cols = st.columns(4)
                meds['Succión'] = cols[0].text_input("Succión", key=f"s_{i}")
                meds['Descarga'] = cols[1].text_input("Descarga", key=f"d_{i}")
                meds['Salida'] = cols[2].text_input("Salida", key=f"t_{i}")
                meds['Amperaje'] = cols[3].text_input("Amp", key=f"a_{i}")
            elif esp == "Otros":
                otros = st.text_area("Detalles/Mediciones:", key=f"o_{i}")
                
            ca1, ca2, ca3 = st.columns(3)
            tag = ca1.text_input("TAG", key=f"tg_{i}")
            marca = ca2.text_input("Marca", key=f"mr_{i}")
            cap = ca3.text_input("Capacidad", key=f"cp_{i}")
            
            texto_defecto = leyendas_default.get(esp, "")
            actividades = st.text_area("Actividades Realizadas", value=texto_defecto, height=80, key=f"act_{i}_{esp}")
            com = st.text_area("Comentarios Extras", key=f"com_{i}")
            
            fa = st.file_uploader("Fotos ANTES", accept_multiple_files=True, key=f"fa_{i}")
            fd = st.file_uploader("Fotos DESPUÉS", accept_multiple_files=True, key=f"fd_{i}")
            
            equipos_data
