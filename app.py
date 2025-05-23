import streamlit as st
import pandas as pd
from datetime import datetime

# ============================
# 📂 Función para cargar datos
# ============================
@st.cache_data
def cargar_datos(archivo):
    try:
        xls = pd.ExcelFile(archivo)
        if "PERSONAL" not in xls.sheet_names:
            st.error("⚠️ Este archivo Excel no es compatible ya que no tiene la hoja de PERSONAL.")
            return None
        df = pd.read_excel(
            archivo,
            sheet_name="PERSONAL",
            header=2
        )
        df.columns = df.columns.str.strip()

        columnas_interes = [
            "NOMBRE", 
            "ID", 
            "FECHA INDUCCION", 
            "VENCE.INDUCCION", 
            "CERT-MAN.ALIMENTOS",
            "VENCE.MANI.ALIM",
            "EXAMENES MEDICOS",
            "VENCIMIENTO.EX.MED",
            "TRABAJADOR AUTORIZADO", 
            "COORDINADOR DE ALTURAS",
            "MANEJO DEFENSIVO",
            "OPERARIOS DE MONTACARGAS",
            "OPERACION"
        ]
        df = df[[col for col in columnas_interes if col in df.columns]]

        df = df.rename(columns={
            "NOMBRE": "Nombre",
            "ID": "Documento",
            "FECHA INDUCCION": "Fecha de Inducción",
            "VENCE.INDUCCION": "Fecha de Vencimiento Inducción",
            "CERT-MAN.ALIMENTOS": "Certificación de Alimentos",
            "VENCE.MANI.ALIM": "Fecha de Vencimiento C.A",
            "EXAMENES MEDICOS": "Exámenes Médicos",
            "VENCIMIENTO.EX.MED": "Fecha de Vencimiento EX.MED",
            "TRABAJADOR AUTORIZADO": "Trabajador Autorizado",
            "COORDINADOR DE ALTURAS": "Coordinador de Alturas",
            "MANEJO DEFENSIVO": "Manejo Defensivo",
            "OPERARIOS DE MONTACARGAS": "Operarios de Montacarga",
            "OPERACION": "Operación"
        })

        # Convertir columnas de fechas al tipo datetime
        columnas_fecha = [
            "Fecha de Inducción",
            "Fecha de Vencimiento Inducción",
            "Fecha de Vencimiento C.A",
            "Fecha de Vencimiento EX.MED"
        ]
        for columna in columnas_fecha:
            df[columna] = pd.to_datetime(df[columna], errors='coerce')

        return df
    except Exception as e:
        st.error(f"⚠️ Error al cargar el archivo: {e}")
        return None

# ================================
# 🚀 Configuración inicial de página
# ================================
st.set_page_config(page_title="Control del Personal", layout="wide")
st.title("Control de Certificaciones, Exámenes Médicos e Inducción del Personal")

# ======================================
# 📄 Subida de archivo y guardado en sesión
# ======================================
if "archivo" not in st.session_state:
    archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])
    if archivo is not None:
        st.session_state.archivo = archivo
        st.session_state.df = cargar_datos(archivo)

if "archivo" in st.session_state:
    archivo = st.session_state.archivo
    if archivo is not None:
        df = cargar_datos(archivo)
        st.session_state.df = df

if "df" in st.session_state and st.session_state.df is not None:
    df = st.session_state.df
    hoy = datetime.now()

    # =======================
    # 🔎 Filtros de búsqueda
    # =======================
    st.sidebar.header("Filtros avanzados")

    busqueda = st.sidebar.text_input("Buscar por nombre o documento:")
    operaciones = df["Operación"].dropna().unique()
    operacion_seleccionada = st.sidebar.selectbox("Filtrar por operación:", ["Todas"] + list(operaciones))
    tipo_alerta = st.sidebar.multiselect(
        "Tipos de alertas a mostrar:",
        ["Inducción", "Certificación", "Exámenes Médicos"],
        default=["Inducción", "Certificación", "Exámenes Médicos"]
    )
    rango_dias = st.sidebar.slider("Días hasta vencimiento máximo:", 0, 365, 30)

    df_filtrado = df.copy()
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado['Nombre'].str.contains(busqueda, case=False, na=False) |
            df_filtrado['Documento'].astype(str).str.contains(busqueda, case=False, na=False)
        ]

    if operacion_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Operación"] == operacion_seleccionada]

    st.dataframe(df_filtrado)

    # =======================
    # 🚨 Procesar Alertas
    # =======================
    def procesar_alerta(fecha, categoria, nombre, lista_vencidos, lista_por_vencer):
        if pd.notna(fecha):
            if not isinstance(fecha, (pd.Timestamp, datetime)):
                fecha = pd.to_datetime(str(fecha), dayfirst=True, errors='coerce')
            if pd.notna(fecha):
                dias_restantes = (fecha.date() - hoy.date()).days
                if dias_restantes < 0:
                    lista_vencidos.append(f"⚠️ {nombre} - {categoria} vencida hace {-dias_restantes} días")
                elif dias_restantes <= rango_dias:
                    lista_por_vencer.append(f"⏳ {nombre} - {categoria} vence en {dias_restantes} días")

    induccion_vencidas, induccion_por_vencer = [], []
    cert_vencidas, cert_por_vencer = [], []
    examenes_vencidos, examenes_por_vencer = [], []

    for index, row in df_filtrado.iterrows():
        nombre = row["Nombre"]
        if "Inducción" in tipo_alerta:
            procesar_alerta(row["Fecha de Vencimiento Inducción"], "Inducción", nombre, induccion_vencidas, induccion_por_vencer)
        if "Certificación" in tipo_alerta:
            procesar_alerta(row["Fecha de Vencimiento C.A"], "Certificación", nombre, cert_vencidas, cert_por_vencer)
        if "Exámenes Médicos" in tipo_alerta:
            procesar_alerta(row["Fecha de Vencimiento EX.MED"], "Examen", nombre, examenes_vencidos, examenes_por_vencer)

    # ======================
    # 📊 Resumen General
    # ======================
    st.subheader("📊 Resumen General")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    def tarjeta(color, titulo, valor):
        st.markdown(f"""
            <div style="background-color: {color}; padding: 15px; border-radius: 10px; text-align: center; color: white;">
                <h4>{titulo}</h4>
                <h2>{valor}</h2>
            </div>
            """, unsafe_allow_html=True)

    with col1:
        tarjeta("#FF4B4B", "Inducciones Vencidas", len(induccion_vencidas))
    with col2:
        tarjeta("#FFC300", "Inducciones por Vencer", len(induccion_por_vencer))
    with col3:
        tarjeta("#C70039", "Certificaciones Vencidas", len(cert_vencidas))
    with col4:
        tarjeta("#FFC300", "Certificaciones por Vencer", len(cert_por_vencer))
    with col5:
        tarjeta("#900C3F", "Exámenes Vencidos", len(examenes_vencidos))
    with col6:
        tarjeta("#FF5733", "Exámenes por Vencer", len(examenes_por_vencer))

    # ======================
    # 📋 Detalle de Alertas
    # ======================
    st.subheader("📋 Detalle de Alertas")

    for titulo, lista_alertas in [
        ("⚠️ Inducciones vencidas", induccion_vencidas),
        ("⏳ Inducciones por vencer", induccion_por_vencer),
        ("⚠️ Certificaciones vencidas", cert_vencidas),
        ("⏳ Certificaciones por vencer", cert_por_vencer),
        ("⚠️ Exámenes vencidos", examenes_vencidos),
        ("⏳ Exámenes por vencer", examenes_por_vencer),
    ]:
        if lista_alertas:
            with st.expander(f"{titulo} ({len(lista_alertas)})"):
                for alerta in lista_alertas:
                    st.warning(alerta)

else:
    st.info("Por favor, sube un archivo Excel para comenzar.")
