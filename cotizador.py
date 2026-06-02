import streamlit as st
import pandas as pd
from datetime import date
import os
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
import tempfile

# CRUCIAL: Configuración de página inicial
st.set_page_config(page_title="Panel Central de Aplicaciones", layout="wide")

# ==========================================
# FUNCIONES AUXILIARES GLOBALES
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

# ==========================================
# CONTROL DE NAVEGACIÓN
# ==========================================
if 'app_actual' not in st.session_state:
    st.session_state.app_actual = "Menu"

def cambiar_pantalla(nombre_app):
    st.session_state.app_actual = nombre_app
    st.rerun()

with st.sidebar:
    st.markdown("### 🛠️ Menú de Navegación")
    if st.button("🏠 Inicio (Panel Central)", use_container_width=True): cambiar_pantalla("Menu")
    st.divider()
    if st.button("📄 Cotizador Industrial", use_container_width=True): cambiar_pantalla("Cotizaciones")
    if st.button("📸 Evidencia Técnica", use_container_width=True): cambiar_pantalla("Reportes")
    if st.button("🚀 Próxima Aplicación", use_container_width=True): cambiar_pantalla("OtraApp")

# ==========================================
# 1. PANTALLA PRINCIPAL: MENÚ
# ==========================================
if st.session_state.app_actual == "Menu":
    st.title("💼 Panel Integrado de Soluciones - Grupo Besco")
    st.markdown("Selecciona la herramienta automatizada que deseas desplegar:")
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📄 Cotizador Industrial")
        st.caption("Cálculo de márgenes, diseño adaptivo en PDF y guardado permanente en Google Sheets.")
        if st.button("Desplegar Cotizador", key="btn_cot", use_container_width=True, type="primary"): cambiar_pantalla("Cotizaciones")
    with col2:
        st.markdown("### 📸 Evidencia Técnica")
        st.caption("Sistema de Evidencia Técnica Alducin. Reportes fotográficos de campo y mantenimiento.")
        if st.button("Desplegar Reportes", key="btn_rep", use_container_width=True, type="primary"): cambiar_pantalla("Reportes")
    with col3:
        st.markdown("### 🚀 Próxima Aplicación")
        st.caption("Módulo en reserva para la integración de futuros flujos de trabajo operativos.")
        if st.button("Desplegar Nueva App", key="btn_otra", use_container_width=True): cambiar_pantalla("OtraApp")

# ==========================================
# 2. APP DE COTIZACIONES
# ==========================================
elif st.session_state.app_actual == "Cotizaciones":
    if st.button("⬅️ Volver al Panel Principal", key="v_cot"): cambiar_pantalla("Menu")
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

        # GENERACIÓN DEL PDF INTELIGENTE
        if "mensaje_exito" in st.session_state: st.success(st.session_state.mensaje_exito)
        if "mensaje_error" in st.session_state: st.error(st.session_state.mensaje_error)
        
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists("logo besco 2026.jpeg"): pdf.image("logo besco 2026.jpeg", x=10, y=5, w=66)
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
        pdf.cell(0, 4, f"- Pago: {limpiar_texto(condiciones_pago)} | Vigencia: {limpiar_texto(vigencia)} | Garantia: {limpiar_texto(garantia)}", ln=True)
        
        pdf.ln(3); pdf.set_font("Helvetica", "B", 6); pdf.cell(0, 3, "NOTAS IMPORTANTES:", ln=True)
        pdf.set_font("Helvetica", size=5.5)
        pdf.multi_cell(0, 3, "- Trabajos extraordinarios o refacciones se cobraran por separado.\n- Precios basados en costos actuales; variaciones comprobables del mercado seran notificadas al cliente para ajuste.")
        
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
# 3. APP DE REPORTES FOTOGRÁFICOS
# ==========================================
elif st.session_state.app_actual == "Reportes":
    if st.button("⬅️ Volver al Panel Principal", key="v_rep"): cambiar_pantalla("Menu")
    st.title("📸 Sistema de Evidencia Técnica Alducin")
    st.subheader("Módulo de Reportes Fotográficos Industriales")
    st.divider()
    
    with st.form("form_evidencia"):
        st.markdown("#### 🛠️ Datos de Inspección de Campo")
        col_r1, col_r2 = st.columns(2)
        tecnico = col_r1.text_input("Técnico Responsable", value="Gerardo Méndez")
        cliente_rep = col_r1.text_input("Cliente / Empresa")
        fecha_rep = col_r2.date_input("Fecha del Servicio", date.today())
        ot = col_r2.text_input("Orden de Trabajo (OT)")
        equipo = st.text_input("Equipo Evaluado (Modelo / Ubicación)")
        
        st.markdown("#### 🖼️ Captura de Evidencia Fotográfica")
        foto1 = st.file_uploader("Fotografía de Evidencia 1", type=["jpg", "jpeg", "png"])
        desc1 = st.text_input("Descripción / Hallazgo Fotografía 1")
        st.divider()
        foto2 = st.file_uploader("Fotografía de Evidencia 2", type=["jpg", "jpeg", "png"])
        desc2 = st.text_input("Descripción / Hallazgo Fotografía 2")
        st.divider()
        observaciones_rep = st.text_area("Diagnóstico Técnico General / Conclusiones")
        
        generar_reporte = st.form_submit_button("💥 Generar y Descargar Reporte Fotográfico")
        
        if generar_reporte:
            if not cliente_rep or not equipo:
                st.error("Por favor completa los campos mínimos (Cliente y Equipo).")
            else:
                pdf_rep = FPDF()
                pdf_rep.add_page()
                if os.path.exists("logo besco 2026.jpeg"): pdf_rep.image("logo besco 2026.jpeg", x=10, y=5, w=66)
                
                pdf_rep.set_y(35); pdf_rep.set_font("Helvetica", "B", 13); pdf_rep.set_text_color(0, 112, 192)
                pdf_rep.cell(0, 6, "SISTEMA DE EVIDENCIA TECNICA ALDUCIN", ln=True, align="C")
                pdf_rep.set_font("Helvetica", "B", 11); pdf_rep.set_text_color(0, 0, 0)
                pdf_rep.cell(0, 5, "REPORTES OPERATIVOS DE AIRE ACONDICIONADO INDUSTRIAL", ln=True, align="C")
                
                pdf_rep.ln(4); pdf_rep.set_fill_color(245, 245, 245); pdf_rep.rect(10, pdf_rep.get_y(), 190, 24, 'DF')
                pdf_rep.set_font("Helvetica", "B", 9)
                pdf_rep.cell(95, 5, f" Tecnico: {limpiar_texto(tecnico)}"); pdf_rep.cell(95, 5, f"Fecha: {fecha_rep.strftime('%d/%m/%Y')}", ln=True)
                pdf_rep.cell(95, 5, f" Cliente: {limpiar_texto(cliente_rep)}"); pdf_rep.cell(95, 5, f"OT: {limpiar_texto(ot)}", ln=True)
                pdf_rep.cell(0, 5, f" Equipo/Ubicacion: {limpiar_texto(equipo)}", ln=True)
                
                pdf_rep.set_y(70)
                # Procesar Foto 1
                if foto1:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as t1:
                        t1.write(foto1.read()); path1 = t1.name
                    pdf_rep.set_font("Helvetica", "B", 10); pdf_rep.cell(0, 5, "Evidencia Fotográfica #1:", ln=True)
                    try: pdf_rep.image(path1, x=15, y=pdf_rep.get_y()+2, w=85); pdf_rep.set_y(pdf_rep.get_y() + 68)
                    except: pdf_rep.cell(0, 5, "[Error al cargar imagen 1]", ln=True)
                    pdf_rep.set_font("Helvetica", size=9); pdf_rep.multi_cell(0, 4, f"Descripcion: {limpiar_texto(desc1)}"); pdf_rep.ln(4)
                    try: os.unlink(path1)
                    except: pass
                
                # Procesar Foto 2
                if foto2:
                    if pdf_rep.get_y() > 190: pdf_rep.add_page()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as t2:
                        t2.write(foto2.read()); path2 = t2.name
                    pdf_rep.set_font("Helvetica", "B", 10); pdf_rep.cell(0, 5, "Evidencia Fotográfica #2:", ln=True)
                    try: pdf_rep.image(path2, x=15, y=pdf_rep.get_y()+2, w=85); pdf_rep.set_y(pdf_rep.get_y() + 68)
                    except: pdf_rep.cell(0, 5, "[Error al cargar imagen 2]", ln=True)
                    pdf_rep.set_font("Helvetica", size=9); pdf_rep.multi_cell(0, 4, f"Descripcion: {limpiar_texto(desc2)}"); pdf_rep.ln(4)
                    try: os.unlink(path2)
                    except: pass
                
                # Diagnóstico Final
                if observaciones_rep:
                    if pdf_rep.get_y() > 220: pdf_rep.add_page()
                    pdf_rep.ln(3); pdf_rep.set_font("Helvetica", "B", 10); pdf_rep.cell(0, 5, "DIAGNOSTICO Y RECOMENDACIONES GENERALES:", ln=True)
                    pdf_rep.set_font("Helvetica", size=9); pdf_rep.multi_cell(0, 4, limpiar_texto(observaciones_rep))
                
                pdf_rep.output("reporte_foto_temp.pdf")
                with open("reporte_foto_temp.pdf", "rb") as f_rep: bytes_rep = f_rep.read()
                
                st.download_button(label="📥 Descargar Reporte Fotográfico PDF", data=bytes_rep, file_name=f"Reporte_Evidencia_{ot if ot else 'Inspeccion'}.pdf", mime="application/pdf", use_container_width=True)
                st.success("¡Reporte listo! Haz clic en el botón de descarga que apareció arriba.")

# ==========================================
# 4. PRÓXIMA APLICACIÓN
# ==========================================
elif st.session_state.app_actual == "OtraApp":
    if st.button("⬅️ Volver al Panel Principal", key="v_otra"): cambiar_pantalla("Menu")
    st.title("🚀 Módulo en Desarrollo")
    st.subheader("Espacio reservado para tu siguiente automatización")
    st.divider()
    st.warning("Esta sección está completamente lista y enrutada. En cuanto definas el siguiente flujo operativo, programaremos las acciones aquí dentro.")
