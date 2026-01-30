import streamlit as st
import pandas as pd
import io
import time
import datetime
import os
import altair as alt

import requests
import urllib3
import ssl

# Configuración de página
st.set_page_config(page_title="Visor de Terapias", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA OCULTAR MENÚS (MODO PRIVADO) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {display: none !important;}
            .stDeployButton {display: none !important;}
            
            /* Ocultar barra superior pero mantener espacio para el control del sidebar */
            /* Ocultar barra superior pero mantener espacio para el control del sidebar */
            /* Ocultar barra superior pero mantener interactividad */
            /* Ocultar barra superior pero mantener interactividad */
            /* Ocultar barra superior pero mantener interactividad */
            /* Ocultar barra superior pero mantener interactividad */
            /* SOLUCIÓN SAFE MODE: No tocar el contenedor del header, solo ocultar sus hijos molestos */
            
            /* Ocultar decoración coloreada superior */
            [data-testid="stDecoration"] {
                display: none !important;
            }
            
            /* Ocultar menús del toolbar pero SALVAR el botón de expandir */
            [data-testid="stToolbar"] {
                visibility: hidden !important; /* No display:none porque mata al hijo */
                background: transparent !important;
                height: 0px !important;
                pointer-events: none !important; 
            }
            
            /* Ocultar el 'Running Man' status widget */
            [data-testid="stStatusWidget"] {
                display: none !important;
            }
            
            /* --- SIDEBAR "EXECUTIVE MIDNIGHT" (PODER Y ELEGANCIA) --- */
            
            section[data-testid="stSidebar"] {
                /* Gradiente "Midnight City": Oscuro, serio y ejecutivo */
                background: linear-gradient(to bottom, #0f2027, #203a43, #2c5364) !important;
                color: #ffffff !important;
                border-right: 1px solid rgba(255,255,255,0.05) !important;
            }
            
            /* Textos dentro del sidebar */
            section[data-testid="stSidebar"] h1, 
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3, 
            section[data-testid="stSidebar"] label, 
            section[data-testid="stSidebar"] .stMarkdown,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] li,
            section[data-testid="stSidebar"] span,
            section[data-testid="stSidebar"] div {
                color: #e2e8f0 !important; /* Blanco "Humo" para no cansar la vista */
                font-family: 'Segoe UI', sans-serif !important;
            }
            
            /* --- BOTÓN "RECARGAR" (ESTILO SLIM TECH) --- */
            /* Diseño más fino, menos tosco, elegante */
            section[data-testid="stSidebar"] .stButton button,
            section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] button {
                width: 100% !important;
                background-color: transparent !important; /* Fondo transparente elegante */
                color: #00d4ff !important; /* Texto Neon */
                border: 1px solid rgba(0, 212, 255, 0.5) !important; /* Borde fino sutil */
                border-radius: 8px !important; /* Radio pequeño (no píldora) */
                
                font-family: 'Segoe UI', sans-serif !important;
                font-weight: 600 !important;
                letter-spacing: 1px !important;
                text-transform: uppercase !important;
                font-size: 0.8rem !important; /* Texto más pequeño */
                
                padding: 0.4rem 0.8rem !important; /* Menos relleno (más delgado) */
                box-shadow: none !important; /* Sin sombra pesada */
                transition: all 0.2s ease !important;
                
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                gap: 5px !important;
            }
            
            section[data-testid="stSidebar"] .stButton button:hover {
                background-color: rgba(0, 212, 255, 0.1) !important; /* Luz sutil al hover */
                border-color: #00d4ff !important;
                color: #ffffff !important;
                box-shadow: 0 0 10px rgba(0, 212, 255, 0.3) !important;
                transform: translateY(-1px) !important;
            }

            /* --- HEADER "FILTRO DE TIEMPO" COMPACTO --- */
            /* Reducir tamaño de encabezados en sidebar */
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3 {
                 font-size: 1rem !important;
                 font-weight: 600 !important;
                 margin-bottom: 0.5rem !important;
                 padding-bottom: 0.2rem !important;
                 border-bottom: 1px solid rgba(255,255,255,0.1) !important;
                 color: rgba(255,255,255,0.9) !important;
            }

            /* --- DROPDOWNS: TEXTO "TODOS" EN NEGRO --- */
            [data-testid="stSidebar"] [data-baseweb="select"] div[aria-selected="true"],
            [data-testid="stSidebar"] [data-baseweb="select"] span,
            [data-testid="stSidebar"] [data-baseweb="select"] div {
                color: #000000 !important; /* Texto negro forzado */
                font-weight: 600 !important;
                font-size: 0.9rem !important; /* Letra un poco más chica */
            }
            /* Asegurar fondo blanco/claro para contraste del texto negro */
            [data-testid="stSidebar"] [data-baseweb="select"] > div {
                background-color: #ffffff !important;
                border: 1px solid #ccc !important;
            }

            /* --- CONTROLES: INTEGRACIÓN TOTAL --- */
            
            /* 1. Pestaña "Abrir" (>>) - Oscura como el fondo */
            [data-testid="stSidebarCollapsedControl"],
            [data-testid="stExpandSidebarButton"] {
                display: flex !important;
                visibility: visible !important;
                
                /* Mismo gradiente que el sidebar para continuidad */
                background: linear-gradient(to bottom, #203a43, #2c5364) !important;
                color: #ffffff !important;
                
                border: 1px solid rgba(255,255,255,0.2) !important;
                border-left: none !important;
                border-radius: 0 8px 8px 0 !important; 
                
                z-index: 99999999 !important;
                position: fixed !important;
                top: 50vh !important;
                left: 0px !important;
                
                width: 24px !important;
                height: 40px !important; /* Más discreto */
                
                box-shadow: 4px 0 10px rgba(0,0,0,0.3) !important;
                pointer-events: auto !important;
            }
            
            [data-testid="stSidebarCollapsedControl"]:hover,
            [data-testid="stExpandSidebarButton"]:hover {
                width: 30px !important;
                background: #2c5364 !important; /* Un poco más claro */
            }

            [data-testid="stSidebarCollapsedControl"] svg,
            [data-testid="stExpandSidebarButton"] svg {
                fill: rgba(255,255,255,0.8) !important;
                width: 16px !important;
                height: 16px !important;
            }

            /* 2. Botón "Cerrar" (<<) - ESTRATEGIA "GHOST CLICK" (Infalible) */
            /* LÓGICA: El botón original (roto/keyboa) está ahí, INVISIBLE pero CLICKEABLE. 
               Nosotros pintamos el "<<" debajo o encima sin bloquear el click. */
            
            [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                position: relative !important; /* Necesario para pos-absolute de hijos */
                
                background: transparent !important;
                border: 1px solid transparent !important;
                
                /* Ocultar rastro de texto en el contenedor padre */
                color: transparent !important;
                
                width: 40px !important;  /* Área de click generosa */
                height: 40px !important;
                margin: 5px !important;
                
                transition: all 0.2s !important;
                cursor: pointer !important;
                z-index: 1000002 !important;
            }
            
            [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover {
                background: rgba(255,255,255,0.1) !important;
                border-radius: 6px !important;
            }
            
            /* HIJOS (Icono Original/Texto): INVISIBLES PERO CLICKEABLES */
            /* Estiramos el hijo para cubrir todo el botón y capturar el clic */
            [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] > * {
                display: flex !important;
                opacity: 0 !important; /* Invisible a la vista */
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                z-index: 10 !important; /* Por encima de nuestro ::after */
                
                cursor: pointer !important;
                pointer-events: auto !important; /* CAPTURA EL EVENTO REAL */
            }
            
            /* SÍMBOLO VISUAL (<<) - Solo decoración */
            [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]::after {
                content: "<<" !important;
                font-size: 22px !important;
                color: #ffffff !important;
                font-weight: 900 !important;
                
                position: absolute !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                z-index: 1 !important; /* Debajo de la capa clickeable transparente */
                
                pointer-events: none !important; 
            }
            
            /* OCULTAR duplicados */
            [data-testid="stSidebar"] button[kind="header"]:not([data-testid="stSidebarCollapseButton"]) {
                display: none !important;
            }

            /* --- SIDEBAR RESCUE --- */
            section[data-testid="stSidebar"] > div {
                flex-shrink: 0 !important;
                height: 100vh !important;
                overflow-y: auto !important; 
                z-index: 999999 !important;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("📊 Visor de Terapias")

# URL PROPORCIONADA POR EL USUARIO (Nueva Versión)
# Appending &download=1 to force binary download from the sharing link
DATA_URL ="https://viva1aips-my.sharepoint.com/:x:/g/personal/gsiguenas_viva1a_com_pe/IQDGPInn2jcyT6oJdUfzmJE8AdUWEyt9EHy9QBN2KqK8jYg?e=MyYJSv&download=1"
SHEET_NAME = "Seguimiento de terapias "




# Configuración SSL
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_data(timestamp_trigger):
    data_source = "Desconocido"
    df = None
    error_msg = None
    
    # 1. INTENTO WEB (Tu enlace)
    try:
        # Cache Busting "Nuclear Option"
        # 1. Headers to tell server "I want fresh data"
        # 2. Dynamic URL to force new request
        timestamp_bust = int(time.time())
        dynamic_url = f"{DATA_URL}&t={timestamp_bust}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Cache-Control': 'no-cache, no-store, must-revalidate', 
            'Pragma': 'no-cache', 
            'Expires': '0'
        }
        
        response = requests.get(dynamic_url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            df = pd.read_excel(io.BytesIO(response.content), sheet_name=SHEET_NAME, engine='openpyxl')
            
            # --- LIMPIEZA PROFUNDA ---
            # 1. Normalizar columnas: Mayúsculas y sin espacios
            df.columns = df.columns.astype(str).str.upper().str.strip()
            
            # 2. Normalizar datos: 
            # - Convertir a string todo lo que sea texto para quitar espacios
            # - Dejar NaNs como están (o convertirlos a un valor neutro si prefieres)
            # - ESTADO especificamente suele dar problemas si trae espacios " FINALIZADO "
            def clean_cell(x):
                if isinstance(x, str):
                    return x.strip().upper()
                return x
                
            df = df.map(clean_cell)
            
            data_source = "🌐 Web (Sin Caché)"
        else:
             error_msg = f"Web falló con código: {response.status_code}"
    except Exception as e:
        error_msg = f"Web falló: {str(e)}"

    # 2. INTENTO LOCAL (Si web falla)
    if df is None:
        try:
            if os.path.exists(LOCAL_PATH):
                # Check mod time
                mod_time = os.path.getmtime(LOCAL_PATH)
                age_min = (time.time() - mod_time) / 60
                
                df = pd.read_excel(LOCAL_PATH, sheet_name=SHEET_NAME, engine='openpyxl')
                if df is not None:
                     # 1. Normalizar columnas
                     df.columns = df.columns.astype(str).str.upper().str.strip()
                     # 2. Normalizar datos
                     df = df.map(clean_cell)
                     
                data_source = f"💻 Disco Local (Antigüedad: {int(age_min)} min)"
            else:
                error_msg = f"{error_msg} | Local no encontrado: {LOCAL_PATH}"
        except Exception as e:
            error_msg = f"{error_msg} | Local falló: {str(e)}"
            
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    return df, error_msg, timestamp, data_source

# --- CONFIGURACIÓN DE ENTORNO ---
# Detectamos si estamos en local chequeando el path específico del usuario
# Esto permite ver controles avanzados en tu PC, pero ocultarlos en la nube
import getpass
IS_LOCAL = "jair" in os.getcwd() or getpass.getuser() == "jair"

# --- LÓGICA DE ESTADO DE SESIÓN ---
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
if 'df_cache' not in st.session_state:
    st.session_state.df_cache, st.session_state.error, st.session_state.hora_lectura, st.session_state.data_source = load_data(st.session_state.last_refresh)

   


# Carga de datos real
# Recuperar de session_state para usar en el resto del script
df = st.session_state.df_cache
error = st.session_state.error
hora_lectura = st.session_state.hora_lectura
data_source = st.session_state.data_source

# --- LÓGICA DE CLASIFICACIÓN TEMPORAL (NUEVO) ---
# Clasificar cada fila según la fecha de su N-ésima sesión (donde N = CANT).

filt_month = "Todos"
filt_year = "Todos"

if df is not None:
    # 1. Lógica de Fechas basada en COLUMNA I (Index 8)
    def parse_spanish_date(text):
        try:
            # CASO 0: Es ya un datetime/timestamp (Excel lo parseó solo)
            if isinstance(text, (datetime.datetime, pd.Timestamp)):
                return text
                
            # CASO 1: Numero Entero (Excel Serial Date)
            if isinstance(text, (int, float)):
                # Excel start: 1899-12-30 usually
                return pd.to_datetime(text, unit='D', origin='1899-12-30')

            if not isinstance(text, str):
                return None
            
            text = text.lower().strip()
            
            # Mapeo de meses español
            meses = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }
            
            # CASO 2: Texto tipo "31-oct" (Regex estricto para evitar 'ene' en 'pendiente')
            target_month = None
            target_year = datetime.datetime.now().year # Default curr year
            
            import re
            
            # Buscar texto de mes con límites de palabra o separadores
            for mes_txt, mes_num in meses.items():
                # Regex: que 'ene' esté precedeido de inicio/espacio/-// y seguido de fin/espacio/-//
                if re.search(r'(?:^|[\s\-\/])' + mes_txt + r'(?:$|[\s\-\/])', text):
                    target_month = mes_num
                    break
            
            if target_month:
                # Intentar sacar año si existe
                years = re.findall(r'\d{4}', text)
                if years:
                    target_year = int(years[0])
                # Devolvemos fecha ficticia
                return datetime.datetime(target_year, target_month, 1)
            
            # CASO 3: Parser Standard (dd/mm/yyyy etc)
            return pd.to_datetime(text, dayfirst=True)
            
        except:
            return None

    def get_target_date(row):
        try:
            # USAR COLUMNA I (Index 8)
            val = row.iloc[8]
            
            if isinstance(val, (datetime.datetime, pd.Timestamp)):
                return val
            elif isinstance(val, str):
                return parse_spanish_date(val)
            else:
                return None
        except:
            return None

    # Aplicar logica (vectorizada row-wise)
    df['FECHA_CLAVE'] = df.apply(get_target_date, axis=1)
    
    # 2. Construir lista de Años/Meses DISPONIBLES en 'FECHA_CLAVE'
    fechas_disponibles = df['FECHA_CLAVE'].dropna().unique()
    
    if len(fechas_disponibles) > 0:
        years = sorted(list(set([d.year for d in fechas_disponibles])))
        months = sorted(list(set([d.month for d in fechas_disponibles])))
        
        month_map = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                     7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        
        opciones_mes = ["Todos"] + [month_map[m] for m in months]
        opciones_anio = ["Todos"] + [str(y) for y in years]
    else:
        opciones_mes = ["Todos"]
        opciones_anio = ["Todos"]

    # --- SIDEBAR LAYOUT ---
    with st.sidebar:
        # 1. BOTÓN RECARGAR (Minimalista, arriba)
        # Usamos columnas para centrarlo o hacerlo menos ancho si se desea
        # El usuario pidió "mas chico" y "sin titulo"
        col_reload, col_blank = st.columns([1, 0.01]) # Truco para ajustar ancho si fuera necesario, o simple button
        if st.button("↻ Recargar", help="Forzar actualización de datos"):
            st.session_state.df_cache, error, ts, source = load_data(time.time())
            st.session_state.last_refresh = time.time()
            st.rerun()
            
        st.divider()

        # 2. FILTRO DE TIEMPO
        st.markdown("### 📅 Filtro de Tiempo") 
        # Texto eliminado por petición del usuario
        
        filt_year = st.selectbox("Año:", opciones_anio, index=0)
        filt_month_name = st.selectbox("Mes:", opciones_mes, index=0)
        
        if filt_month_name != "Todos":
            rev_map = {v:k for k,v in month_map.items()}
            filt_month_num = rev_map[filt_month_name]

        # 3. FILTRO DE PACIENTE (Nuevo)
        st.markdown("### 👤 Filtro de Paciente")
        
        # Obtener lista única de pacientes del cache crudo o del df filtrado por fecha? 
        # Plan: Usar df (cache) para mostrar TODOS, o df filtrado por fecha?
        # Mejor: Mostrar Pacientes disponibles en la data cargada (df)
        if 'PACIENTES' in df.columns:
            # Normalizar y limpiar
            raw_patients = df['PACIENTES'].dropna().astype(str).str.strip().str.upper().unique()
            sorted_patients = sorted([p for p in raw_patients if p not in ["NAN", "NONE", ""]])
        else:
            sorted_patients = []
            
        opciones_pacientes = ["Todos"] + sorted_patients
        filt_patient = st.selectbox("Seleccionar Paciente:", opciones_pacientes, index=0)

        # 4. CONTROLES LOCALES (Discretos abajo)
        if IS_LOCAL:
            st.divider()
            st.caption("🛠️ Modo Local")
            enable_autorefresh = st.checkbox("✅ Auto-escaneo", value=True)
            if enable_autorefresh:
                refresh_interval = st.select_slider(
                    "Segundos:",
                    options=[90, 120, 180, 240, 300, 600],
                    value=90
                )


# Área Principal - Indicadores
# Solo mostramos la fuente de datos si estamos en local o si hay error
if  IS_LOCAL:
    col1, col2 = st.columns([3, 1])
    with col1:
        if error:
            st.error(f"❌ Error: {error}")
        elif IS_LOCAL:
             if "Web" in data_source:
                 st.success(f"☁️ {data_source}")
             elif "Local" in data_source:
                 st.warning(f" {data_source}")
             else:
                 st.error("❌ Sin Conexión")
        
    with col2:
        st.write(f"🕒 **Actualizado:** {hora_lectura}")
df = st.session_state.df_cache
error = st.session_state.error
hora_lectura = st.session_state.hora_lectura
data_source = st.session_state.data_source

if df is not None:
    # Definir 4 pestañas explícitamente para evitar errores
    tab_dashboard, tab_search, tab_main, tab_downloads = st.tabs([
        "📊 Panel Principal", 
        "🔍 Buscador de Pacientes", 
        "📋 Tabla Principal", 
        "📥 Descargas"
    ])
    
    # Check si hay algun filtro activo
    filter_active = not (filt_year == "Todos" and filt_month_name == "Todos" and filt_patient == "Todos")

    # --- FILTRADO STRICTO (GLOBAL) ---
    # Volvemos al filtrado estricto.
    if 'PACIENTES' in df.columns:
        df_base = df[df['PACIENTES'].notna() & (df['PACIENTES'].astype(str).str.strip() != '')].copy()
    else:
        df_base = df.copy()

    # --- APLICAR FILTROS (FECHA + PACIENTE) ---
    if filter_active:
        # Asegurar que FECHA_CLAVE exista en df_base
        if 'FECHA_CLAVE' not in df_base.columns:
            df_base['FECHA_CLAVE'] = df.loc[df_base.index, 'FECHA_CLAVE']
            
        # 1. Filtro de Fechas (Periodo)
        mask_period = pd.Series([True] * len(df_base), index=df_base.index)
        if (filt_year != "Todos" or filt_month_name != "Todos"):
             df_base = df_base[df_base['FECHA_CLAVE'].notna()].copy()
             mask_period = pd.Series([True] * len(df_base), index=df_base.index)
        
        if filt_year != "Todos":
            mask_period = mask_period & (df_base['FECHA_CLAVE'].dt.year == int(filt_year))
        if filt_month_name != "Todos":
             mes_map_local = {"Enero":1, "Febrero":2, "Marzo":3, "Abril":4, "Mayo":5, "Junio":6, 
                              "Julio":7, "Agosto":8, "Septiembre":9, "Octubre":10, "Noviembre":11, "Diciembre":12}
             f_num = mes_map_local.get(filt_month_name, -1)
             mask_period = mask_period & (df_base['FECHA_CLAVE'].dt.month == f_num)
             
        # df_dash SOLO tiene filtro de periodo
        df_dash = df_base[mask_period].copy()

        # 2. Filtro de Paciente
        mask_final = mask_period.copy()
        if filt_patient != "Todos":
            mask_final = mask_final & (df_base['PACIENTES'].astype(str).str.strip().str.upper() == filt_patient)
             
        df_final = df_base[mask_final].copy()
    else:
        df_dash = df_base.copy()
        df_final = df_base.copy()

    with tab_dashboard:
        st.caption(f"Visualizando datos de: {data_source} | Actualizado: {hora_lectura}")

        # Variables para KPI 3, 4, 5 GLOBAL (Toda la data)
        global_programado = 0
        global_ejecutadas = 0
        global_sesiones_saldo = 0
        global_tasa_ejec = 0
        global_tasa_pend = 0

        # Variables para KPI 3, 4, 5 FILTRADO (Capítulos)
        total_programado_final = 0
        total_ejecutadas_final = 0
        total_sesiones_saldo_final = 0
        
        col_estado_found = None
        total_validas = len(df_dash)
        
        try:
            # --- 1. CÁLCULO GLOBAL (df_base) ---
            col_p_base = None
            col_c_base = None
            col_r_base = None
            for c in df_base.columns:
                c_up = str(c).upper().strip()
                if "PENDIENTES" in c_up: col_p_base = c
                if "CANT" in c_up: col_c_base = c
                if "REALIZADAS" in c_up or "EJECUTADAS" in c_up: col_r_base = c
            
            if col_c_base:
                global_programado = pd.to_numeric(df_base[col_c_base], errors='coerce').fillna(0).sum()
            if col_p_base:
                s_p_base = pd.to_numeric(df_base[col_p_base], errors='coerce').fillna(0)
                global_sesiones_saldo = int(s_p_base[s_p_base > 0].sum())
                if col_r_base:
                    global_ejecutadas = pd.to_numeric(df_base[col_r_base], errors='coerce').fillna(0).sum()
                else:
                    global_ejecutadas = global_programado - s_p_base.sum()
            
            global_tasa_ejec = (global_ejecutadas / global_programado * 100) if global_programado > 0 else 0
            global_tasa_pend = (global_sesiones_saldo / global_programado * 100) if global_programado > 0 else 0

            # --- 2. CÁLCULO FILTRADO (df_final) ---
            col_pend_final = None
            col_cant_final = None
            col_real_final = None
            
            for c in df_final.columns:
                c_upper = str(c).upper().strip()
                if "PENDIENTES" in c_upper: col_pend_final = c
                if "CANT" in c_upper: col_cant_final = c
                if "REALIZADAS" in c_upper or "EJECUTADAS" in c_upper: col_real_final = c
                if "ESTADO" in c_upper: col_estado_found = c

            if col_cant_final:
                total_programado_final = pd.to_numeric(df_final[col_cant_final], errors='coerce').fillna(0).sum()
            if col_pend_final:
                s_pend_final = pd.to_numeric(df_final[col_pend_final], errors='coerce').fillna(0)
                total_sesiones_saldo_final = int(s_pend_final[s_pend_final > 0].sum())
                if col_real_final:
                    total_ejecutadas_final = pd.to_numeric(df_final[col_real_final], errors='coerce').fillna(0).sum()
                else:
                    total_ejecutadas_final = total_programado_final - s_pend_final.sum()
            
            # (Variables para alertas y otros usos)
            count_negativos = int(pd.to_numeric(df_final[col_pend_final], errors='coerce').fillna(0).lt(0).sum()) if col_pend_final else 0
            tasa_ejecucion = global_tasa_ejec # Para mantener compatibilidad con KPI logic
            tasa_pendiente = global_tasa_pend
            
        except:
            pass

        # --- ZONA DE ALERTAS (SIDE-BY-SIDE) ---
        if 'count_negativos' in locals() and count_negativos > 0:
            st.error(f"⚠️ **Atención:** Se han detectado **{count_negativos} casos** de pacientes con sesiones en exceso (Saldo Negativo).")
            
        c_alert1, c_alert2 = st.columns(2)
        
        # Helper para encontrar columna ID
        col_id_excel = None
        for c in df_final.columns:
            if str(c).upper().strip() in ['ID', 'Nº', 'NO', 'N.']:
                col_id_excel = c
                break
        if not col_id_excel: col_id_excel = df_final.columns[0] # Fallback primera col

        # 1. ALERTA IZQUIERDA: FINALIZACIÓN PRÓXIMA (<= 2 SESIONES)
        with c_alert1:
            col_pend_alert = None
            col_cant_alert = None
            
            for c in df_final.columns:
                c_upper = str(c).upper().strip()
                if "PENDIENTES" in c_upper: col_pend_alert = c
                if "CANT" in c_upper: col_cant_alert = c
                    
            if col_pend_alert and col_cant_alert:
                df_alert = df_final.copy()
                df_alert[col_pend_alert] = pd.to_numeric(df_alert[col_pend_alert], errors='coerce').fillna(0)
                df_alert[col_cant_alert] = pd.to_numeric(df_alert[col_cant_alert], errors='coerce').fillna(0)
                
                mask_near = (df_alert[col_pend_alert] > 0) & (df_alert[col_pend_alert] <= 2)
                df_near = df_alert[mask_near]
                count_near = len(df_near)
                
                if count_near > 0:
                    st.warning(f"🔔 **Alerta:** {count_near} pacientes por finalizar (≤ 2 sesiones).")
                    with st.expander(f"Ver lista de {count_near} pacientes"):
                        col_paciente = 'PACIENTES' if 'PACIENTES' in df_alert.columns else df_alert.columns[0]
                        # Si col_id_excel es el mismo que paciente, no repetirlo
                        cols_show = []
                        if col_id_excel != col_paciente: cols_show.append(col_id_excel)
                        cols_show.append(col_paciente)
                        
                        col_terapia = 'ESPECIALIDAD' if 'ESPECIALIDAD' in df_alert.columns else ('PROGRAMAS' if 'PROGRAMAS' in df_alert.columns else None)
                        
                        df_display = df_near.copy()
                        df_display['Progreso'] = df_display.apply(lambda x: f"{int(x[col_cant_alert] - x[col_pend_alert])}/{int(x[col_cant_alert])}", axis=1)
                        
                        if col_terapia: cols_show.append(col_terapia)
                        cols_show.append('Progreso')
                        
                        # Formatear ID sin decimales si es numerico
                        if col_id_excel in df_display.columns and pd.api.types.is_numeric_dtype(df_display[col_id_excel]):
                             df_display[col_id_excel] = df_display[col_id_excel].fillna(0).astype(int).astype(str)

                        st.dataframe(df_display[cols_show], hide_index=True, use_container_width=True)

        # 2. ALERTA DERECHA: INICIO RETRASADO (0 REALIZADAS, > 5 DÍAS)
        with c_alert2:
            col_realizadas = None
            col_fecha_om = None 
            col_estado = None
            
            for c in df_final.columns:
                c_upper = str(c).upper().strip()
                if "REALIZADAS" in c_upper: col_realizadas = c
                if "FECHA OM" in c_upper: col_fecha_om = c
                if "ESTADO" in c_upper: col_estado = c
            
            if not col_fecha_om and 'FECHA_CLAVE' in df_final.columns:
                col_fecha_om = 'FECHA_CLAVE'

            if col_realizadas and col_fecha_om:
                df_stagnant = df_final.copy()
                df_stagnant[col_realizadas] = pd.to_numeric(df_stagnant[col_realizadas], errors='coerce').fillna(0)
                
                df_stagnant['temp_date'] = pd.to_datetime(df_stagnant[col_fecha_om], errors='coerce', dayfirst=True)
                hoy = datetime.datetime.now()
                df_stagnant['dias_pasados'] = (hoy - df_stagnant['temp_date']).dt.days
                
                mask_stagnant = (df_stagnant[col_realizadas] == 0) & (df_stagnant['dias_pasados'] >= 5)
                df_stag_final = df_stagnant[mask_stagnant]
                count_stag = len(df_stag_final)
                
                if count_stag > 0:
                    st.warning(f"⏳ **Alerta:** {count_stag} pacientes sin iniciar (> 5 días esperando).")
                    with st.expander(f"Ver lista de {count_stag} pacientes"):
                        col_paciente = 'PACIENTES' if 'PACIENTES' in df_stag_final.columns else df_stag_final.columns[0]
                        
                        # --- FILTRO POR ESTADO (Request JAIR) ---
                        df_show_stag = df_stag_final.copy()
                        df_show_stag['Esperando'] = df_show_stag['dias_pasados'].astype(int).astype(str) + " días"
                        
                        cols_stag = []
                        if col_id_excel != col_paciente: cols_stag.append(col_id_excel)
                        cols_stag.append(col_paciente)
                        if col_estado: cols_stag.append(col_estado) 
                        cols_stag.append('Esperando')
                        
                        # Lógica de Filtro Multiselect
                        if col_estado and col_estado in df_show_stag.columns:
                             unique_states = df_show_stag[col_estado].unique().tolist()
                             # Crear st.multiselect
                             selected_states = st.multiselect(
                                 "Filtrar por Estado:",
                                 options=unique_states,
                                 default=unique_states
                             )
                             # Filtrar DF
                             df_show_stag = df_show_stag[df_show_stag[col_estado].isin(selected_states)]
                             
                             # Mostrar conteos resumen rapidos
                             counts_summary = df_stag_final[col_estado].value_counts().to_dict()
                             summary_text = " | ".join([f"{k}: {v}" for k,v in counts_summary.items()])
                             st.caption(f"📊 Desglose: {summary_text}")
                        
                        # Formatear ID
                        if col_id_excel in df_show_stag.columns and pd.api.types.is_numeric_dtype(df_show_stag[col_id_excel]):
                             df_show_stag[col_id_excel] = df_show_stag[col_id_excel].fillna(0).astype(int).astype(str)
                        
                        st.dataframe(df_show_stag[cols_stag], hide_index=True, use_container_width=True)

        # --- 1. KPIS (TARJETAS) ---
        # Usar container para limpiar viz previa
        kpi_holder = st.empty()
        
        with kpi_holder.container():
            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        # KPI 1: Pacientes (Patrón Ejecutivo Global)
        col_dni = 'DNI' if 'DNI' in df_base.columns else 'PACIENTES'
        if col_dni not in df_base.columns and 'DNI ' in df_base.columns: col_dni = 'DNI '
            
        # 1. VALOR PRINCIPAL: Global Total
        total_global_pacientes = df_base[col_dni].nunique() if col_dni in df_base.columns else len(df_base)
        kpi1.metric("Pacientes Totales", total_global_pacientes, "En Base")
        
        # 2. CAPTION: Detalle del Filtro (Filtro Actual)
        if filter_active:
            total_final_pacientes = df_final[col_dni].nunique() if (filt_patient != "Todos" or col_dni in df_final.columns) else 0
            if filt_patient != "Todos": total_final_pacientes = 1
            
            label_p = "paciente" if total_final_pacientes == 1 else "pacientes"
            # Re-usar lógia de periodo
            texto_periodo = ""
            if filt_month_name != "Todos" or filt_year != "Todos":
                texto_periodo = f" en {filt_month_name if filt_month_name != 'Todos' else ''} {filt_year if filt_year != 'Todos' else ''}".strip()
            
            kpi1.caption(f"📌 {total_final_pacientes} {label_p}{texto_periodo}")
        else:
            kpi1.caption(" ") # Mantiene el espacio ocupado para evitar reseteos sucios
       
        # KPI 2: Agendamiento (Patrón Ejecutivo Global)
        # 1. VALOR PRINCIPAL: Global Total
        if 'ESPECIALIDAD' in df_base.columns:
            total_global_terapias = len(df_base[df_base['ESPECIALIDAD'].notna() & (df_base['ESPECIALIDAD'].astype(str).str.strip() != '')])
        else:
            total_global_terapias = len(df_base)

        kpi2.metric("Ordenes", total_global_terapias, "Terapias")
        
        # 2. CAPTION: Detalle del Filtro (Filtro Actual)
        if filter_active:
            if 'ESPECIALIDAD' in df_final.columns:
                total_final_terapias = len(df_final[df_final['ESPECIALIDAD'].notna() & (df_final['ESPECIALIDAD'].astype(str).str.strip() != '')])
            else:
                total_final_terapias = len(df_final)
                
            label_s = "solicitud" if total_final_terapias == 1 else "solicitudes"
            texto_periodo = ""
            if filt_month_name != "Todos" or filt_year != "Todos":
                texto_periodo = f" en {filt_month_name if filt_month_name != 'Todos' else ''} {filt_year if filt_year != 'Todos' else ''}".strip()
                
            kpi2.caption(f"📌 {total_final_terapias} {label_s}{texto_periodo}")
        else:
             kpi2.caption(" ")



        # KPI 3, 4, 5: Desglose de Volúmenes (Patrón Ejecutivo Global)
        try:
            # KPI 3: Total Programado (Global)
            kpi3.metric("Total Programado", f"{int(global_programado)}", "Sesiones Totales")
            if filter_active:
                label_ses = "sesión" if int(total_programado_final) == 1 else "sesiones"
                kpi3.caption(f"📌 {int(total_programado_final)} {label_ses}")
            else:
                 kpi3.caption(" ")
            
            # KPI 4: Sesiones Ejecutadas (Global %)
            kpi4.metric(
                "Sesiones Ejecutadas", 
                f"{global_tasa_ejec:.1f}%", 
                f"{int(global_ejecutadas)} Ejecutadas"
            )
            if filter_active:
                kpi4.caption(f"📌 {int(total_ejecutadas_final)} realizadas")
            else:
                 kpi4.caption(" ")
            
            # KPI 5: Sesiones Pendientes (Global %)
            kpi5.metric(
                "Sesiones Pendientes", 
                f"{global_tasa_pend:.1f}%", 
                f"{int(global_sesiones_saldo)} Pendientes",
                delta_color="inverse"
            )
            if filter_active:
                kpi5.caption(f"📌 {int(total_sesiones_saldo_final)} por realizar")
            else:
                 kpi5.caption(" ")
                 
        except Exception as e:
            st.error(f"Error en KPIs de volumen: {e}")

        st.divider()

        # --- 2. GRÁFICOS ESTRATÉGICOS (Layout Ajustado: 3 Columnas) ---
        # Izquierda: Especialidad | Centro: Donut Balance | Derecha: Estado
        c1, c2, c3 = st.columns([1.2, 0.8, 1.2])
        
        with c1:
            st.subheader("📊 Terapias Solicitadas")
            if 'ESPECIALIDAD' in df_final.columns:
                # 1. Preparar datos limpios (sobre df_final)
                df_sp = df_final[df_final['ESPECIALIDAD'].notna() & (df_final['ESPECIALIDAD'] != '')]
                
                # 2. Calcular estadisticas
                col_id = 'DNI' if 'DNI' in df_final.columns else 'PACIENTES'
                
                agg_dict = {
                    'Total_Terapias': ('ESPECIALIDAD', 'count')
                }
                
                # Siempre sumamos CANT. si la columna existe (Sesiones Programadas)
                if 'col_cant_final' in locals() and col_cant_final:
                    df_sp[col_cant_final] = pd.to_numeric(df_sp[col_cant_final], errors='coerce').fillna(0)
                    agg_dict['Sesiones_Programadas'] = (col_cant_final, 'sum')
                else:
                    # Fallback por seguridad si no se encuentra la columna de cantidad
                    agg_dict['Pacientes_Unicos'] = (col_id, 'nunique')
                
                sp_stats = df_sp.groupby('ESPECIALIDAD').agg(**agg_dict).reset_index().sort_values(by="Total_Terapias", ascending=False)
                
                # 3. Gráfico
                tooltip_list = [
                    alt.Tooltip('ESPECIALIDAD', title='Especialidad'),
                    alt.Tooltip('Total_Terapias', title='Terapias Ordenadas'),
                ]
                
                if 'Sesiones_Programadas' in sp_stats.columns:
                    tooltip_list.append(alt.Tooltip('Sesiones_Programadas', title='Sesiones Programadas'))
                else:
                    tooltip_list.append(alt.Tooltip('Pacientes_Unicos', title='Pacientes Únicos'))

                base = alt.Chart(sp_stats).encode(
                    x=alt.X('Total_Terapias', title='Total Ordenadas'),
                    y=alt.Y('ESPECIALIDAD', sort='-x', title=''),
                    tooltip=tooltip_list
                )
                bars = base.mark_bar(color="#FF4B4B")
                text = base.mark_text(align='left', dx=3, color='black').encode(text='Total_Terapias')
                
                st.altair_chart((bars + text).properties(height=350), use_container_width=True)
                
                missing_sp = df_final[df_final['ESPECIALIDAD'].isna() | (df_final['ESPECIALIDAD'] == '')].shape[0]
                if missing_sp > 0:
                    st.warning(f"⚠️ Atención: Hay {missing_sp} filas con Especialidad vacía (No salen en la gráfica).")
                else:
                    st.success("✅ 0 filas con Especialidad vacía (Datos Limpios)")
            else:
                st.warning("Columna ESPECIALIDAD no encontrada")
                
        with c2:
            st.subheader("⏳ Estado de Gestión")
            if col_estado_found:
                # Normalizar serie para cálculos de la gráfica
                s_est = df_final[col_estado_found].astype(str).str.upper().str.strip()
                total_graf_final = len(df_final)
                
                # Definir grupos: FINALIZADO + EN PROCESO (Gestión Realizada) vs PENDIENTE AGENDAMIENTO
                count_gestion_realizada = s_est[s_est.isin(['FINALIZADO', 'EN PROCESO'])].shape[0]
                count_pend_agendamiento = s_est[s_est.str.contains("AGENDAMIENTO", case=False, na=False)].shape[0]
                count_otros = total_graf_final - count_gestion_realizada - count_pend_agendamiento
                
                source_gest = pd.DataFrame({
                    "Estado": ["Gestión Realizada", "Pendiente Agendamiento", "Otros"],
                    "Total": [count_gestion_realizada, count_pend_agendamiento, count_otros]
                })
                
                # Calcular porcentajes para la gráfica
                source_gest["Percentage"] = (source_gest["Total"] / total_graf_final * 100).fillna(0)
                source_gest["PercentageLabel"] = source_gest["Percentage"].apply(lambda x: f"{x:.1f}%")
                
                # Gráfico Donut base
                base = alt.Chart(source_gest).encode(
                    theta=alt.Theta("Total", stack=True)
                )
                
                pie = base.mark_arc(innerRadius=60, outerRadius=85).encode(
                    color=alt.Color("Estado", scale=alt.Scale(domain=["Gestión Realizada", "Pendiente Agendamiento", "Otros"],
                                                             range=["#4CAF50", "#FFC107", "#9E9E9E"]),
                                    legend=None),
                    tooltip=["Estado", "Total", alt.Tooltip("Percentage", format=".1f")]
                )
                
                # Texto central (Gestión Realizada %)
                pct_gest_val = source_gest.loc[source_gest["Estado"]=="Gestión Realizada", "Percentage"].sum()
                text_center = alt.Chart(pd.DataFrame({'text': [f"{pct_gest_val:.0f}%"]})).mark_text(
                    radius=0, size=20, fontStyle="bold", color="#4CAF50"
                ).encode(text='text:N')

                # Etiquetas laterales (Solo Pendientes y Otros)
                # "el de pendiente ... vaya al costado de su color amarrilo"
                # "el 86.1 que esta de negro quitalo" (Quitamos etiqueta de Gestión Realizada)
                text_side = base.mark_text(radius=105, size=11).encode(
                    text=alt.Text("PercentageLabel"),
                    order=alt.Order("Estado"),
                    color=alt.Color("Estado", scale=alt.Scale(domain=["Gestión Realizada", "Pendiente Agendamiento", "Otros"],
                                                             range=["#4CAF50", "#FF8F00", "#757575"]), legend=None)
                ).transform_filter(
                    alt.datum.Estado != 'Gestión Realizada'
                )
                
                st.altair_chart((pie + text_center + text_side).properties(height=250), use_container_width=True)
                
                st.markdown(f"""
                <div style="background-color: #f9f9f9; padding: 12px; border-radius: 10px; border: 1px solid #e0e0e0; margin-top: 5px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <table style="width: 100%; table-layout: fixed; border-collapse: collapse; border: none;">
                        <tr style="border: none;">
                            <td style="width: 33%; text-align: center; border-right: 1px solid #ddd; vertical-align: middle;">
                                <div style="font-size: 11px; color: #4CAF50; font-weight: 600; text-transform: uppercase;">Realizadas</div>
                                <div style="font-size: 18px; font-weight: 700; color: #2E7D32; margin-top: 2px;">{count_gestion_realizada}</div>
                            </td>
                            <td style="width: 33%; text-align: center; border-right: 1px solid #ddd; vertical-align: middle;">
                                <div style="font-size: 11px; color: #FFC107; font-weight: 600; text-transform: uppercase;">Pendientes</div>
                                <div style="font-size: 18px; font-weight: 700; color: #FF8F00; margin-top: 2px;">{count_pend_agendamiento}</div>
                            </td>
                            <td style="width: 33%; text-align: center; vertical-align: middle;">
                                <div style="font-size: 11px; color: #555; font-weight: 600; text-transform: uppercase;">Total</div>
                                <div style="font-size: 18px; font-weight: 700; color: #000; margin-top: 2px;">{total_graf_final}</div>
                            </td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Columna de Estado no disponible para gestión.")

        with c3:
            st.subheader("📋 Estado Pacientes")
            if 'ESTADO' in df_final.columns:
                df_st_valid = df_final[df_final['ESTADO'].notna() & (df_final['ESTADO'] != '')]
                
                total_counts = df_st_valid['ESTADO'].value_counts().reset_index()
                total_counts.columns = ['Estado', 'Total Terapias']
                
                col_id = 'DNI' if 'DNI' in df_final.columns else 'PACIENTES'
                unique_counts = df_st_valid.groupby('ESTADO')[col_id].nunique().reset_index()
                unique_counts.columns = ['Estado', 'Pacientes']
                final_stats = pd.merge(total_counts, unique_counts, on='Estado')
                
                base_st = alt.Chart(final_stats).encode(
                    x=alt.X('Total Terapias', title='Total'),
                    y=alt.Y('Estado', sort='-x', title=''),
                    tooltip=['Estado', 'Total Terapias', 'Pacientes']
                )
                bars_st = base_st.mark_bar(color="#FF4B4B")
                text_st = base_st.mark_text(align='left', dx=3, color='black').encode(text='Total Terapias')
                
                st.altair_chart((bars_st + text_st).properties(height=350), use_container_width=True)
                
                missing_st = df_final[df_final['PACIENTES'].notna() & (df_final['ESTADO'].isna() | (df_final['ESTADO'] == ''))].shape[0]
                if missing_st > 0:
                    st.warning(f"⚠️ Atención: Hay {missing_st} filas con Estado vacío.")
                else:
                    st.success("✅ 0 filas con Estado vacío (Datos Limpios)")
            else:
                 st.warning("Columna ESTADO no encontrada")
        
        st.divider()
        
        # --- 3. GEOGRAFÍA ---
        st.subheader("🗺️ Distribución por Distritos")
        if 'DISTRITO' in df_final.columns:
             dist_data = df_final['DISTRITO'].value_counts().reset_index()
             dist_data.columns = ['Distrito', 'Pacientes']
             
             # Chart Altair mejorado (VERTICAL)
             base_dist = alt.Chart(dist_data).encode(
                 x=alt.X('Distrito', sort='-y', title='Distrito'),
                 y=alt.Y('Pacientes', title='Total Pacientes'),
                 tooltip=['Distrito', 'Pacientes']
             )
             
             bars_dist = base_dist.mark_bar(color="#FF4B4B")
             
             text_dist = base_dist.mark_text(
                 align='center',
                 baseline='bottom',
                 dy=-5, # Encima de la barra
                 color='black'
             ).encode(
                 text='Pacientes'
             )
             
             final_dist = (bars_dist + text_dist).properties(height=400).interactive()
             st.altair_chart(final_dist, use_container_width=True)

    with tab_search:
        st.header("🔍 Buscador de Pacientes")
        
        # 1. Filtro de Estado
        st_list = ["Todos"] + sorted(df_base['ESTADO'].astype(str).unique().tolist())
        st_filt = st.selectbox("📂 Estado:", st_list, index=0, key="fs_global_v2")
        
        df_s = df_base if st_filt == "Todos" else df_base[df_base['ESTADO'].astype(str) == st_filt]
        p_list = sorted(df_s['PACIENTES'].dropna().unique().tolist())
        
        # El buscador de esta pestaña es INDEPENDIENTE de la barra lateral (por petición del usuario)
        p_sel = st.selectbox(
            "👤 Selecciona Paciente:", 
            p_list, 
            index=None, 
            placeholder="Buscar...",
            key=f"buscador_tab_p_{st_filt}" # Reseteamos lista si cambia el estado
        )

        if p_sel:
            try:
                # Usar df_s (filtrado por estado) en lugar de df_base para que las terapias coincidan con el filtro
                matches = df_s[df_s['PACIENTES'] == p_sel].copy()
                labels = []
                idx_map_s = {}
                
                for idx, r in matches.iterrows():
                    esp = str(r.get('ESPECIALIDAD', 'S/E'))
                    f_o = r.get('FECHA OM', 'S/F')
                    # VALIDACIÓN ROBUSTA DE FECHAS (Previene ValueError en NaT)
                    f_s = f_o.strftime('%d/%m/%Y') if (pd.notnull(f_o) and hasattr(f_o, 'strftime')) else str(f_o)
                    l = f"{esp} (Inicio: {f_s})"
                    o_l, c = l, 2
                    while l in idx_map_s:
                        l = f"{o_l} ({c})"; c += 1
                    labels.append(l)
                    idx_map_s[l] = idx
                
                # Llave dinámica para Terapia para que se resetee al cambiar de paciente
                t_sel = st.selectbox("📋 Terapia:", labels, key=f"ts_v2_{p_sel}")
                
                p_data_found = None
                if t_sel:
                    p_data_found = df_base.loc[idx_map_s[t_sel]]
                
                if p_data_found is not None:
                    st.markdown(f"### 👤 {p_data_found.get('PACIENTES', p_sel)}")
                    st.caption(f"Detalle: {t_sel}")
                    
                    if IS_LOCAL:
                        with st.expander("🛠️ Ver Datos Crudos"):
                            st.json(p_data_found.to_dict())

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.info(f"**DNI:** {p_data_found.get('DNI', 'N/A')}")
                        st.write(f"**Tel:** {p_data_found.get('TLF', 'N/A')}")
                    with c2:
                        st.info(f"**Programa:** {p_data_found.get('PROGRAMAS', 'N/A')}")
                        f_v = p_data_found.get('FECHA OM', 'N/A')
                        # VALIDACIÓN ROBUSTA PARA CAMPO INICIO
                        st.write(f"**Inicio:** {f_v.strftime('%d/%m/%Y') if (pd.notnull(f_v) and hasattr(f_v, 'strftime')) else f_v}")
                    with c3:
                        e_r = str(p_data_found.get('ESTADO', 'N/A'))
                        p_val = p_data_found.get('PENDIENTES', 0)
                        c_val = p_data_found.get('CANT.', 0)
                        
                        # Conversión segura a int
                        try:
                            p_v = int(float(p_val)) if pd.notnull(p_val) else 0
                            c_v = int(float(c_val)) if pd.notnull(c_val) else 0
                        except:
                            p_v, c_v = 0, 0
                            
                        if e_r == "FINALIZADO" and p_v > 0:
                            st.warning("⚠️ PENDIENTE (Saldar)")
                        else:
                            st.success(f"Estado: {e_r}")
                        
                        st.write(f"**Progreso:** {c_v - p_v}/{c_v}")
                        st.caption(f"Total: {c_v} | Pendientes: {p_v}")
                    
                    st.divider()
                    st.subheader("📅 Asistencias")
                    
                    tl = []
                    for i in range(1, 21):
                        cn = str(i)
                        if cn in p_data_found:
                            fv = p_data_found[cn]
                            if pd.notnull(fv) and str(fv).strip() != "":
                                # VALIDACIÓN ROBUSTA PARA TODAS LAS SESIONES
                                fo = fv if hasattr(fv, 'strftime') else pd.to_datetime(fv, dayfirst=True, errors='coerce')
                                if pd.notnull(fo) and hasattr(fo, 'strftime'):
                                    tl.append({"Ses": f"S{i}", "Fecha": fo, "Fmt": fo.strftime('%d/%m/%Y')})
                    
                    if tl:
                        df_tl = pd.DataFrame(tl)
                        st.scatter_chart(df_tl, x="Fecha", y="Ses", size=100)
                        st.success(f"✅ Última sesión: {df_tl['Fecha'].max().strftime('%d/%m/%Y')}")
                        
                        # NUEVA TABLA DE SESIONES (Solicitada)
                        with st.expander("📅 Ver Detalle de Fechas"):
                            # Seleccionar y renombrar columnas para la vista
                            df_view = df_tl[["Ses", "Fmt"]].rename(columns={"Ses": "Sesión", "Fmt": "Fecha"})
                            st.dataframe(df_view, hide_index=True, use_container_width=True)
                    else:
                        st.warning("⚠️ No hay fechas registradas o el formato es incompatible.")
            except Exception as e:
                st.error(f"❌ Error al cargar datos: {str(e)}")
                st.info("💡 Se detectó información mal formateada en el Excel. Se recomienda revisar el registro del paciente.")
        else:
            st.info("💡 Selecciona un paciente para ver su historial completo.")

    with tab_main:
        st.caption(f"Fuente de datos: {data_source}")
        st.info("� Modo Lectura: La edición está desactivada en la versión pública.")
        
        # Tabla de solo lectura - Respetando filtros
        st.dataframe(df_final, use_container_width=True, hide_index=True)

    
    with tab_downloads:
        st.header("📥 Descarga de Reporte Detallado")
        st.info("Este reporte desglosa cada sesión en una fila individual (Formato Vertical).")
        
        # Lógica de "Explosión" (Unpivot/Melt inteligente)
        if st.button("🚀 Generar Reporte Detallado"):
            with st.spinner("Procesando todas las sesiones..."):
                exploded_data = []
                
                # Iterar por cada orden de terapia (Respetando filtros)
                for idx, row in df_final.iterrows():
                    # Datos base del paciente
                    base_info = {
                        "PACIENTE": row.get('PACIENTES', ''),
                        "DNI": row.get('DNI', ''),
                        "TELEFONO": row.get('TLF', ''),
                        "DISTRITO": row.get('DISTRITO', ''),
                        "DIRECCION": row.get('DIRECCION', ''), # Agregado a petición
                        "ESPECIALIDAD": row.get('ESPECIALIDAD', ''),
                        "PROGRAMA": row.get('PROGRAMAS', ''),
                        "TOTAL_ORDEN": row.get('CANT.', 0),
                        "ESTADO_ORDEN": row.get('ESTADO', '')
                    }
                    
                    # Cuántas sesiones deberia tener
                    try:
                        cant_sesiones = int(row.get('CANT.', 0))
                    except:
                        cant_sesiones = 0
                        
                    # Generar una fila por cada sesión teórica (1 hasta Cantidad)
                    for i in range(1, cant_sesiones + 1):
                        info = base_info.copy()
                        info['NUM_SESION'] = i
                        
                        # Buscar fecha en columna "1", "2", etc
                        col_name = str(i)
                        fecha_val = row.get(col_name, None)
                        
                        # Procesar fecha
                        fecha_str = ""
                        estado_sesion = "PENDIENTE"
                        
                        if pd.notna(fecha_val):
                            if isinstance(fecha_val, datetime.datetime):
                                fecha_str = fecha_val.strftime('%d/%m/%Y')
                                estado_sesion = "ASISTIÓ"
                            elif isinstance(fecha_val, str):
                                # Intento de parseo rápido
                                if len(fecha_val) > 4: 
                                    fecha_str = fecha_val
                                    estado_sesion = "ASISTIÓ (Texto)"
                        
                        info['FECHA_SESION'] = fecha_str
                        info['ESTADO_SESION'] = estado_sesion
                        
                        exploded_data.append(info)
                
                # Crear DataFrame final
                if exploded_data:
                    df_export = pd.DataFrame(exploded_data)
                    
                    # Convertir a Excel en memoria
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_export.to_excel(writer, index=False, sheet_name='Detalle_Sesiones')
                        
                        # Auto-ajustar columnas (opcional, básico)
                        worksheet = writer.sheets['Detalle_Sesiones']
                        worksheet.set_column('A:A', 30) # Paciente
                        worksheet.set_column('B:I', 15) # Otros (Ajustado rango para incluír Dirección)
                    
                    st.success(f"✅ Reporte generado: {len(df_export)} filas individuales.")
                    
                    # Botón de descarga real
                    st.download_button(
                        label="💾 DESCARGAR EXCEL (VERTICAL)",
                        data=buffer.getvalue(),
                        file_name="reporte_sesiones_vertical.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                else:
                    st.warning("No se encontraron datos para exportar.")
else:
    st.error(f"⚠️ No se pudieron cargar datos.")
    if error:
        st.code(error)
        
    st.info("� Intenta guardar tu Excel Online y espera 5 minutos para que baje a tu PC.")
    
# Lógica de Auto-refresco (al final)
if 'enable_autorefresh' in locals() and enable_autorefresh:
    time.sleep(refresh_interval)
    st.rerun()