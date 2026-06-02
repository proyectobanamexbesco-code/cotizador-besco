import streamlit as st
import pandas as pd
from datetime import date
import os
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials

# Configuración inicial de la página
st.set_page_config(page_title="Generador de Cotizaciones", layout="wide")

# FUNCIÓN MAESTRA: Se ejecuta automáticamente al dar clic en descargar PDF y escribe en Google Sheets
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
                str(folio),
                str(fecha_cot),
                str(nom_cli),
                str(inst_cli),
                str(dir_cli),
                str(tel_cli),
                str(em_cli),
                str(cotizador),
                str(puesto),
                str(em_cot),
                str(tel_cot),
                str(desc),
                str(ubi),
                float(sub),
                float(iva),
                float(tot),
                str(moneda),
                str(entrega),
                str(pago),
                str(vig),
                str(gar),
                str(fila["Tipo"]),
                str(fila["Concepto"]),
                float(fila["Cant."]),
                str(fila["Unidad"]),
                float(fila["Costo U."]),
                float(fila["Precio Venta"]),
                float(fila["Importe"])
            ]
            sheet.append_row(nueva_fila)
        
        st.session_state.mensaje_exito = f"¡Cotización {folio} registrada exitosamente en Google Sheets y PDF descargado!"
    except Exception as e:
        st.session_state.mensaje_error = f"Error crítico al conectar con Google Sheets: {str(e)}. Verifica la configuración de Secrets y los permisos de la hoja."

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

# Encabezado de la Empresa y Espacio para el Folio (UI Limpia)
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
    descripcion_cotizacion = st.text_input("Descripción de la cotización (Ej. Mantenimiento Preventivo)")
with col_cot2:
    fecha = st.date_input("Fecha de Cotización", date.today())
    telefono_cotizador = st.text_input("Teléfono de contacto (Cotizador)")
    ubicacion = st.text_input("Ubicación del Servicio")

st.divider()

st.header("2. Datos del Cliente (Presupuesto para)")
col_cli1, col_cli2 = st.columns(2)
with col_cli1:
    nombre_cliente = st.text_input("Nombre cliente:")
    institucion_cliente = st.text_input("Institucion/ Cliente:")
    direccion_cliente = st.text_input("Dirección:")
with col_cli2:
    telefono_cliente = st.text_input("Telefono:")
    email_cliente = st.text_input("E-mail:")

cliente_base = institucion_cliente if institucion_cliente else nombre_cliente

if nombre_cotizador and cliente_base and descripcion_cotizacion:
    iniciales = "".join([palabra[0].upper() for palabra in nombre_cotizador.split() if palabra])
    fecha_str = fecha.strftime("%d%m%Y")
    cliente_str = cliente_base.replace(" ", "").upper()[:6]
    desc_str = descripcion_cotizacion.replace(" ", "").upper()[:6]
    numero_presupuesto = f"{iniciales}-{fecha_str}-{cliente_str}-{desc_str}"
else:
    numero_presupuesto = "Llenando datos..."

folio_placeholder.success(f"**Folio de Cotización:** \n{numero_presupuesto}")
st.divider()

st.header("3. Detalles del Servicio")
if 'conceptos' not in st.session_state:
    st.session_state.conceptos = []

with st.form("agregar_concepto", clear_on_submit=True):
    col_srv, col_desc = st.columns([1, 2])
    with col_srv:
        tipo_servicio = st.selectbox("Tipo de Servicio", ["Aire Acondicionado", "Eléctrico", "Luminarias", "Hidrosanitario", "Acabados", "Otros"])
    with col_desc:
        concepto = st.text_input("Concepto o Descripción detallada")
        
    col_cant, col_uni, col_precio, col_util, col_btn = st.columns([1, 1, 1.2, 1.2, 1])
    with col_cant:
        cantidad = st.number_input("Cantidad", min_value=0.01, value=1.00, step=1.00)
    with col_uni:
        tipo_unidad = st.selectbox("Tipo de Unidad", ["Pieza", "Caja", "Metro", "Metro Lineal", "Kilo", "Metro Cuadrado (m2)", "Litro", "Servicio"])
    with col_precio:
        costo_unitario = st.number_input("Costo Unitario ($) (Tu costo)", min_value=0.0, value=0.0, step=100.0)
    with col_util:
        margen_utilidad = st.number_input("Utilidad (%)", min_value=0.0, value=23.50, step=0.50)
        
    with col_btn:
        st.write("")
        st.write("")
        submit = st.form_submit_button("Agregar a Cotización")
    
    if submit:
        if "mensaje_exito" in st.session_state:
            del st.session_state.mensaje_exito
        if "mensaje_error" in st.session_state:
            del st.session_state.mensaje_error
            
        if concepto.strip() == "":
            st.error("Por favor, escriba una descripción en el concepto antes de agregar.")
        else:
            precio_venta = costo_unitario * (1 + (margen_utilidad / 100))
            total_linea = precio_venta * cantidad
            st.session_state.conceptos.append({
                "Tipo": tipo_servicio, "Concepto": concepto, "Cant.": cantidad,
                "Unidad": tipo_unidad, "Costo U.": costo_unitario,
                "Precio Venta": precio_venta, "Importe": total_linea
            })
            st.success(f"Se agregó: {cantidad} {tipo_unidad} de {concepto}")

if st.session_state.conceptos:
    st.header("4. Resumen de Cotización")
    df_cotizacion = pd.DataFrame(st.session_state.conceptos)
    df_editado = st.data_editor(df_cotizacion, num_rows="dynamic", use_container_width=True)
    df_editado["Importe"] = df_editado["Cant."] * df_editado["Precio Venta"]
    subtotal = df_editado["Importe"].sum()
    iva = subtotal * 0.16
    total = subtotal + iva

    st.divider()
    col_vacia, col_totales = st.columns([3, 1])
    with col_totales:
        st.metric("Subtotal", f"${subtotal:,.2f}")
        st.metric("IVA (16%)", f"${iva:,.2f}")
        st.metric("TOTAL", f"${total:,.2f}")

    st.divider()

    st.header("5. Condiciones del Trabajo")
    col_cond1, col_cond2 = st.columns(2)
    with col_cond1:
        tipo_moneda = st.selectbox("Tipo de Moneda", ["Pesos Mexicanos", "Dólares de Estados Unidos"])
        tiempo_entrega_num = st.number_input("Tiempo de Ejecución / Entrega (en días)", min_value=1, value=15, step=1)
        tiempo_entrega = f"{int(tiempo_entrega_num)} días hábiles"
        condiciones_pago = st.selectbox("Condiciones de Pago", [
            "30% Anticipo / 70% al término del trabajo",
            "50% Anticipo / 50% al término de los trabajos", 
            "100% al término de los trabajos", "100% Anticipo"
        ])
    with col_cond2:
        vigencia_num = st.number_input("Vigencia de la Cotización (en días)", min_value=1, value=15, step=1)
        vigencia = f"{int(vigencia_num)} días hábiles"
        garantia = st.text_input("Garantía", value="30 días sobre mano de obra")
        
    st.info("**Nota:** Las condiciones fijas de refacciones y variación de precios se agregarán automáticamente en el PDF.")
    st.divider()

    st.header("6. Finalizar Cotización")
    if "mensaje_exito" in st.session_state:
        st.success(st.session_state.mensaje_exito)
    if "mensaje_error" in st.session_state:
        st.error(st.session_state.mensaje_error)
    
    pdf = FPDF()
    pdf.add_page()
    
    ruta_logo = "logo besco 2026.jpeg"
    if os.path.exists(ruta_logo):
        pdf.image(ruta_logo, x=10, y=5, w=66)
        
    pdf.set_fill_color(230, 230, 230)
    pdf.rect(10, 35, 190, 32, 'DF') 
    pdf.line(10, 35, 200, 35)
    pdf.line(10, 36, 200, 36)
    
    pdf.set_y(37)
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.set_text_color(0, 112, 192) 
    pdf.cell(110, 5, txt="Dirección de la compañía", ln=False)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(30, 5, txt="fecha", ln=False)
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(0, 0, 0) 
    pdf.cell(50, 5, txt=fecha.strftime('%d/%m/%Y'), ln=True, align="R")
    pdf.line(150, 42, 200, 42) 
    
    pdf.set_font("Helvetica", size=10)
    pdf.cell(110, 5, txt="Grupo Besco S.A. de C.V", ln=False)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.set_text_color(0, 112, 192) 
    pdf.cell(30, 5, txt="Nº presupuesto", ln=False)
    pdf.set_font("Helvetica", size=9) 
    pdf.set_text_color(0, 0, 0) 
    pdf.cell(50, 5, txt=numero_presupuesto, ln=True, align="R")
    pdf.line(150, 47, 200, 47) 
    
    pdf.set_font("Helvetica", size=10)
    pdf.cell(190, 5, txt="Calle Jose Ignacio Bartolache 1910, Col. Acacias , Ciudad de México", ln=True)
    pdf.cell(110, 5, txt="Telefono  55150865- ext 251", ln=False)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.set_text_color(0, 112, 192) 
    pdf.cell(80, 5, txt="Responsable de cotización", ln=True, align="C")
    
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(0, 0, 0) 
    pdf.cell(110, 5, txt=f"e-mail:   {limpiar_texto(email_cotizador)}", ln=False)
    pdf.cell(80, 5, txt=limpiar_texto(nombre_cotizador), ln=True, align="C")
    pdf.line(135, 62, 185, 62) 
    
    pdf.line(10, 67, 200, 67)
    pdf.line(10, 68, 200, 68)
    pdf.ln(8)
    
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(100, 5, txt="PRESUPUESTO PARA (CLIENTE):", ln=False)
    pdf.cell(0, 5, txt="DATOS DEL PROYECTO:", ln=True)
    
    # SISTEMA DINÁMICO DE ALTURAS PARA CABECERA
    pdf.set_font("Helvetica", size=9)
    y_current = pdf.get_y()
    
    pdf.set_xy(10, y_current)
    pdf.multi_cell(90, 4, txt=f"Nombre: {limpiar_texto(nombre_cliente)}")
    y_left = pdf.get_y()
    pdf.set_xy(105, y_current)
    pdf.multi_cell(95, 4, txt=f"Proyecto: {limpiar_texto(descripcion_cotizacion)}")
    y_right = pdf.get_y()
    y_current = max(y_left, y_right)

    pdf.set_xy(10, y_current)
    pdf.multi_cell(90, 4, txt=f"Institucion: {limpiar_texto(institucion_cliente)}")
    y_left = pdf.get_y()
    pdf.set_xy(105, y_current)
    pdf.multi_cell(95, 4, txt=f"Ubicacion: {limpiar_texto(ubicacion)}")
    y_right = pdf.get_y()
    y_current = max(y_left, y_right)

    pdf.set_xy(10, y_current)
    pdf.multi_cell(90, 4, txt=f"Direccion: {limpiar_texto(direccion_cliente)}")
    y_left = pdf.get_y()
    pdf.set_xy(105, y_current)
    pdf.multi_cell(95, 4, txt=f"Tel. Cotizador: {limpiar_texto(telefono_cotizador)}")
    y_right = pdf.get_y()
    y_current = max(y_left, y_right)

    pdf.set_xy(10, y_current)
    pdf.multi_cell(90, 4, txt=f"Telefono: {limpiar_texto(telefono_cliente)}")
    y_left = pdf.get_y()
    pdf.set_xy(105, y_current)
    pdf.multi_cell(95, 4, txt=f"E-mail: {limpiar_texto(email_cliente)}")
    y_right = pdf.get_y()
    y_current = max(y_left, y_right)
    
    pdf.set_y(y_current + 5)
    
    pdf.set_font("Helvetica", style="B", size=9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 7, txt="Tipo", border=1, ln=False, fill=True)
    pdf.cell(75, 7, txt="Concepto / Descripcion", border=1, ln=False, fill=True)
    pdf.cell(15, 7, txt="Cant.", border=1, ln=False, fill=True, align="C")
    pdf.cell(20, 7, txt="Unidad", border=1, ln=False, fill=True, align="C")
    pdf.cell(25, 7, txt="Precio U.", border=1, ln=False, fill=True, align="R")
    pdf.cell(25, 7, txt="Importe", border=1, ln=True, fill=True, align="R")
    
    # SISTEMA DINÁMICO DE ALTURAS PARA TABLA (ALINEACIÓN SUPERIOR LIMPIA)
    pdf.set_font("Helvetica", size=8)
    for _, fila in df_editado.iterrows():
        # Prevenir cortes de hoja a mitad de un renglón
        if pdf.get_y() > 255:
            pdf.add_page()
            
        x_start = 10
        y_start = pdf.get_y()
        
        texto_tipo = limpiar_texto(fila["Tipo"])
        texto_concepto = limpiar_texto(fila["Concepto"])
        texto_unidad = limpiar_texto(fila["Unidad"])
        
        # Margen superior para que el texto respire y no toque la línea
        y_text = y_start + 1.5 
        
        # 1. Imprimimos los bloques de texto alineados a la parte superior y medimos sus alturas
        pdf.set_xy(x_start, y_text)
        pdf.multi_cell(30, 4, txt=texto_tipo, border=0, align="L")
        alto_tipo = pdf.get_y()
        
        pdf.set_xy(x_start + 30, y_text)
        pdf.multi_cell(75, 4, txt=texto_concepto, border=0, align="L")
        alto_concepto = pdf.get_y()
        
        # Ahora la Unidad también es dinámica y evitará empalmes si el nombre es largo
        pdf.set_xy(x_start + 120, y_text)
        pdf.multi_cell(20, 4, txt=texto_unidad, border=0, align="C")
        alto_unidad = pdf.get_y()
        
        # 2. Encontramos la altura máxima necesaria para este renglón
        y_max = max(alto_tipo, alto_concepto, alto_unidad)
        row_height = (y_max - y_start) + 1.5 # Añadimos margen inferior
        
        if row_height < 7:
            row_height = 7
            
        # 3. Imprimimos los números alineados arriba para que se vean organizados
        pdf.set_xy(x_start + 105, y_text)
        pdf.cell(15, 4, txt=f"{fila['Cant.']:.2f}", border=0, align="C")
        
        pdf.set_xy(x_start + 140, y_text)
        pdf.cell(25, 4, txt=f"${fila['Precio Venta']:.2f}", border=0, align="R")
        
        pdf.set_xy(x_start + 165, y_text)
        pdf.cell(25, 4, txt=f"${fila['Importe']:.2f}", border=0, align="R")
        
        # 4. Dibujamos los bordes exactos
        pdf.rect(x_start, y_start, 30, row_height)
        pdf.rect(x_start + 30, y_start, 75, row_height)
        pdf.rect(x_start + 105, y_start, 15, row_height)
        pdf.rect(x_start + 120, y_start, 20, row_height)
        pdf.rect(x_start + 140, y_start, 25, row_height)
        pdf.rect(x_start + 165, y_start, 25, row_height)
        
        # 5. Preparamos el cursor para el siguiente renglón
        pdf.set_y(y_start + row_height)
        
    pdf.ln(5)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(140, 6, txt="", ln=False)
    pdf.cell(25, 6, txt="Subtotal:", border=1, ln=False, align="L")
    pdf.cell(25, 6, txt=f"${subtotal:,.2f}", border=1, ln=True, align="R")
    pdf.cell(140, 6, txt="", ln=False)
    pdf.cell(25, 6, txt="I.V.A. (16%):", border=1, ln=False, align="L")
    pdf.cell(25, 6, txt=f"${iva:,.2f}", border=1, ln=True, align="R")
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 6, txt="", ln=False)
    pdf.cell(25, 6, txt="TOTAL:", border=1, ln=False, align="L", fill=True)
    pdf.cell(25, 6, txt=f"${total:,.2f}", border=1, ln=True, align="R", fill=True)
    
    pdf.ln(10)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(0, 6, txt="CONDICIONES COMERCIALES Y DE TRABAJO:", ln=True)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, txt=f"- Tipo de Moneda: {limpiar_texto(tipo_moneda)}", ln=True)
    pdf.cell(0, 5, txt=f"- Tiempo de Ejecucion / Entrega: {limpiar_texto(tiempo_entrega)}", ln=True)
    pdf.cell(0, 5, txt=f"- Condiciones de Pago: {limpiar_texto(condiciones_pago)}", ln=True)
    pdf.cell(0, 5, txt=f"- Vigencia de la Cotizacion: {limpiar_texto(vigencia)}", ln=True)
    pdf.cell(0, 5, txt=f"- Garantia: {limpiar_texto(garantia)}", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", style="B", size=7)
    pdf.cell(0, 5, txt="NOTAS IMPORTANTES:", ln=True)
    pdf.set_font("Helvetica", size=6)
    nota1 = "- Los trabajos extraordinarios o refacciones se proceden por separado."
    nota2 = "- Los valores que aparecen en la presente cotizacion estan basados en los precios que rigen a la fecha de emision, si durante el proceso de resolucion, manufactura y hasta la entrega de la obra hubiese cambios en los precios que afecten nuestros costos previa comprobacion correspondiente, el cliente reconocera los incrementos habidos, los que seran notificados en su debida oportunidad."
    nota3 = "- En caso de existir correctivos adicionales o refacciones adicionales fuera de la presente cotizacion, se notificara al cliente para su aprobacion en caso de ser necesario."
    pdf.multi_cell(0, 4, txt=limpiar_texto(nota1))
    pdf.ln(1)
    pdf.multi_cell(0, 4, txt=limpiar_texto(nota2))
    pdf.ln(1)
    pdf.multi_cell(0, 4, txt=limpiar_texto(nota3))

    pdf.ln(8)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_draw_color(34, 139, 34) 
    pdf.set_font("Helvetica", style="B", size=9)
    texto_despedida = "Sin mas por el momento y en espera de vernos favorecidos en el presente, quedo a sus ordenes para cualquier aclaracion al respecto."
    pdf.multi_cell(0, 8, txt=limpiar_texto(texto_despedida), border=1, align="C", fill=True)
    
    pdf.set_draw_color(0, 0, 0)
    pdf.ln(8)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(0, 5, txt="ATENTAMENTE", ln=True, align="C")
    pdf.ln(12) 
    pdf.set_text_color(0, 112, 192) 
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(0, 5, txt=limpiar_texto(nombre_cotizador).upper(), ln=True, align="C")
    pdf.set_font("Helvetica", style="B", size=9)
    pdf.cell(0, 5, txt=limpiar_texto(puesto_cotizador), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)

    pdf.output("cotizacion_temp.pdf")
    with open("cotizacion_temp.pdf", "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    
    st.download_button(
        label="⚡ Guardar Historial y Descargar PDF",
        data=pdf_bytes,
        file_name=f"Cotizacion_{numero_presupuesto}.pdf",
        mime="application/pdf",
        use_container_width=True,
        on_click=callback_guardar_todo,
        args=(
            df_editado, numero_presupuesto, fecha, 
            nombre_cliente, institucion_cliente, direccion_cliente, telefono_cliente, email_cliente,
            nombre_cotizador, puesto_cotizador, email_cotizador, telefono_cotizador,
            descripcion_cotizacion, ubicacion, subtotal, iva, total,
            tipo_moneda, tiempo_entrega, condiciones_pago, vigencia, garantia
        )
    )

if st.button("Limpiar Cotización Nueva"):
    st.session_state.conceptos = []
    if "mensaje_exito" in st.session_state:
        del st.session_state.mensaje_exito
    if "mensaje_error" in st.session_state:
        del st.session_state.mensaje_error
    st.rerun()
