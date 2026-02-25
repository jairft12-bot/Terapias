# Visor de Terapias v2.1 - Deploy Fix
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
import re
import getpass
import mapas # Importamos modulo local

# --- CONFIGURACIÓN DE ENTORNO ---
# Detectamos si estamos en local (PC de Jair) de forma robusta
IS_LOCAL = os.path.exists("/Users/jair/Desktop/terapias") or os.environ.get("USER") == "jair"

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
            
            /* --- BOTONES "SLIM EXECUTIVE" (ZERO-WRAP) --- */
            /* Priorizamos que el texto no se rompa y se vea premium */
            section[data-testid="stSidebar"] .stButton button {
                width: 100% !important;
                white-space: nowrap !important; /* NO ROMPER PALABRAS */
                overflow: hidden !important;
                
                background: rgba(255, 255, 255, 0.02) !important;
                color: #e2e8f0 !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                border-radius: 4px !important;
                
                font-family: 'Inter', 'Segoe UI', sans-serif !important;
                font-weight: 500 !important;
                font-size: 0.72rem !important; /* Tamaño optimizado para evitar wrap */
                padding: 0.4rem 0.3rem !important; /* Padding horizontal mínimo */
                
                transition: all 0.25s ease !important;
                text-transform: none !important;
                letter-spacing: 0.2px !important;
            }
            
            section[data-testid="stSidebar"] .stButton button:hover {
                background: rgba(0, 212, 255, 0.05) !important;
                border-color: #00d4ff !important;
                color: #ffffff !important;
                box-shadow: 0 0 15px rgba(0, 212, 255, 0.1) !important;
            }

            /* Botón "⚡ Forzar Web" (Acento Tecnológico) */
            [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div:nth-child(2) button {
                border-color: rgba(0, 212, 255, 0.3) !important;
                color: #00d4ff !important;
                background: rgba(0, 212, 255, 0.02) !important;
            }
            [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div:nth-child(2) button:hover {
                background: rgba(0, 212, 255, 0.1) !important;
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.2) !important;
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
# URL VERIFICADA (gsiguenas) - 200 OK
DATA_URL ="https://viva1aips-my.sharepoint.com/:x:/g/personal/gsiguenas_viva1a_com_pe/IQDGPInn2jcyT6oJdUfzmJE8AdUWEyt9EHy9QBN2KqK8jYg?e=YsMUjL&download=1"
SHEET_NAME = "Seguimiento de terapias "




# Configuración de Rutas y Archivos
LOCAL_PATH = os.path.join(os.getcwd(), "Seguimiento de terapias .xlsx")

# Configuración SSL
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_data(force_web=False):
    data_source = "Desconocido"
    df = None
    error_msg = None
    age_min = 0 
    
    # --- DETERMINAR ORDEN DE INTENTOS ---
    if force_web:
        intentos = ["web"]
    elif IS_LOCAL:
        intentos = ["local", "web"]
    else:
        intentos = ["web", "local"]
        
    for metodo in intentos:
        if df is not None: break
        
        if metodo == "web":
            try:
                # Cache Busting Nuclear v3: Random string + multiple timestamps
                import random
                rand_id = random.randint(1000, 9999)
                t_ms = int(time.time() * 1000)
                # JAIR: SharePoint a veces demora. Forzamos descarga limpia.
                dynamic_url = f"{DATA_URL}&t={t_ms}&r={rand_id}&download_fresh=1"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0',
                    'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0, post-check=0, pre-check=0', 
                    'Pragma': 'no-cache', 
                    'Expires': '0',
                    'DNT': '1'
                }
                
                # Usar timeout más largo para SharePoint pero con reintentos? No, simple.
                response = requests.get(dynamic_url, headers=headers, verify=False, timeout=15)
                
                if response.status_code == 200:
                    df = pd.read_excel(io.BytesIO(response.content), sheet_name=SHEET_NAME, engine='openpyxl')
                    df.columns = df.columns.astype(str).str.upper().str.strip()
                    df = df.map(lambda x: x.strip().upper() if isinstance(x, str) else x)
                    data_source = "🌐 SharePoint (Nube)"
                else:
                    error_msg = f"Web falló ({response.status_code})"
            except Exception as e:
                error_msg = f"Web falló: {str(e)}"
                
        elif metodo == "local":
            try:
                if os.path.exists(LOCAL_PATH):
                    mod_time = os.path.getmtime(LOCAL_PATH)
                    age_min = (time.time() - mod_time) / 60
                    # Si el archivo tiene menos de 10 segundos, es "fresco"
                    
                    cols_str = {'DNI': str, 'ID': str, 'CODIGO': str, 'DOCUMENTO': str, 'TLF': str}
                    df = pd.read_excel(LOCAL_PATH, sheet_name=SHEET_NAME, engine='openpyxl', converters=cols_str)
                    if df is not None:
                        df.columns = df.columns.astype(str).str.upper().str.strip()
                        def clean_id(val):
                            if pd.isna(val): return ""
                            s = str(val).strip()
                            return s.split('.')[0] if re.match(r'^\d+\.0+$', s) else s
                        for col in ['DNI', 'ID', 'DOCUMENTO', 'TLF', 'TELEFONO', 'CODIGO']:
                            if col in df.columns: df[col] = df[col].map(clean_id)
                        df = df.map(lambda x: x.strip().upper() if isinstance(x, str) else x)
                        data_source = f"💻 PC Local ({int(age_min)} min)"
            except Exception as e:
                error_msg = f"{error_msg} | Local falló: {str(e)}"

    now_local = datetime.datetime.now() - datetime.timedelta(hours=5)
    timestamp = now_local.strftime('%H:%M:%S')
    return df, error_msg, timestamp, data_source

# --- HELPER PARA ACTUALIZAR TODO EL ESTADO ---
def refresh_all_data(force_web=False):
    # Si forzamos web, limpiamos rastro de local para evitar confusiones
    if force_web:
        st.session_state.data_source = "Cargando desde Web..."
    
    df, err, ts, src = load_data(force_web=force_web)
    
    # Actualizar estado global
    st.session_state.df_cache = df
    st.session_state.error = err
    st.session_state.hora_lectura = ts
    st.session_state.data_source = src
    st.session_state.last_refresh = time.time()
    st.session_state.last_refresh_date = datetime.date.today()
    st.session_state.last_auto_refresh = time.time()
    
    # Si hubo error en web y no estamos forzando, intentar local? 
    # No, load_data ya maneja la jerarquía.

# --- CONFIGURACIÓN DE ENTORNO ---
# (Movido al inicio)

# --- LÓGICA DE ESTADO DE SESIÓN ---
# Forzar recarga si:
# 1. No hay caché
# 2. Ha pasado más de 1 hora (TTL para frescura)
# 3. Ha cambiado el día (Fix: No actualiza cuando pasa un día)
TTL_CACHE_SECONDS = 3600
current_time = time.time()
current_date = datetime.date.today()

cache_exists = 'df_cache' in st.session_state
needs_refresh = False

if not cache_exists:
    needs_refresh = True
else:
    last_refresh = st.session_state.get('last_refresh', 0)
    last_date = st.session_state.get('last_refresh_date')
    
    # Validar tiempo
    if (current_time - last_refresh) > TTL_CACHE_SECONDS:
        needs_refresh = True
    # Validar cambio de día
    if last_date != current_date:
        needs_refresh = True

if needs_refresh:
    refresh_all_data()

   


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
            # USAR COLUMNA EXPLICITA 'FECHA OM'
            # Buscamos la columna, asumiendo que ya fue normalizada a mayúsculas
            # o buscamos una que contenga "FECHA" y "OM"
            
            val = None
            if 'FECHA OM' in row.index:
                val = row['FECHA OM']
            elif 'FECHA_OM' in row.index:
                val = row['FECHA_OM']
            else:
                 # Fallback: Buscar index 9 (donde suele estar) si no lo encuentra por nombre
                 if len(row) > 9: val = row.iloc[9]
            
            if pd.isna(val): return None

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
    # Filtramos NaT explícitamente y aseguramos que sean datetimes válidos
    fechas_disponibles = df['FECHA_CLAVE'].dropna()
    fechas_disponibles = fechas_disponibles[pd.to_datetime(fechas_disponibles, errors='coerce').notna()]
    
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
        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            if st.button("↻ Recargar", help="Recarga estándar (Usa local si es Jair)"):
                refresh_all_data(force_web=False)
                st.rerun()
        with col_rel2:
            if st.button("⚡ Forzar Web", help="Ignora el archivo local y baja de SharePoint"):
                # Limpieza profunda para forzar descarga
                if 'df_cache' in st.session_state: del st.session_state.df_cache
                refresh_all_data(force_web=True)
                st.rerun()
            
        st.divider()

        # 2. FILTRO DE TIEMPO
        st.markdown("### 📅 Filtro de Tiempo") 
        # Texto eliminado por petición del usuario
        
        # Intentar pre-seleccionar 2026 si está disponible
        default_year_idx = 0
        if "2026" in opciones_anio:
            default_year_idx = opciones_anio.index("2026")
            
        filt_year = st.selectbox("Año:", opciones_anio, index=default_year_idx)
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

        # 4. CONTROLES DE ACTUALIZACIÓN (Solo JAIR - Local)
        if IS_LOCAL:
            st.divider()
            
            # DIAGNOSTICO OCULTO POR SOLICITUD USER (Pero logica preservada si se necesita reactivar)
            view_diagnosis = False 
            if view_diagnosis:
                with st.expander("🔍 Diagnóstico de Datos"):
                    st.caption(f"Fuente: {data_source}")
                    if df is not None:
                         total_raw = len(df)
                         
                         if 'PACIENTES' in df.columns:
                             n_empty = df['PACIENTES'].isna().sum() + (df['PACIENTES'].astype(str).str.strip() == '').sum()
                             n_valid = total_raw - n_empty
                             
                             st.markdown(f"""
                             | Métrica | Valor |
                             | :--- | :--- |
                             | **Total Filas Excel** | `{total_raw}` |
                             | **Filas con Paciente** | `{n_valid}` (Gráficos) |
                             | **Filas Huérfanas** | `{n_empty}` (Solo suman KPI) |
                             """)
                             
                             # Mostrar huérfanas con data
                             orphans = df[(df['PACIENTES'].isna()) | (df['PACIENTES'].astype(str).str.strip() == '')]
                             if not orphans.empty:
                                 orphans_with_cant = orphans[orphans['CANT.'].notna()]
                                 if not orphans_with_cant.empty:
                                     st.caption(f"⚠️ Hay {len(orphans_with_cant)} filas sin nombre pero con CANTIDAD (Suman {orphans_with_cant['CANT.'].sum()} al Total Programado).")
                         else:
                             st.error("Columna PACIENTES no encontrada")
            
            st.caption("⚙️ Configuración")
            enable_autorefresh = st.checkbox("✅ Auto-Recarga", value=True)
            if enable_autorefresh:
                if (time.time() - st.session_state.get('last_auto_refresh', 0)) > 300: # 5 min default
                     refresh_all_data()
                     st.rerun()


# Área Principal - Indicadores de Estado
col_status_info, col_time_info = st.columns([3, 1])
with col_status_info:
    if error:
        st.error(f"❌ Error de Carga: {error}")
    elif IS_LOCAL:
        # Mostrar fuente de datos elegante (Solo JAIR - Local)
        if "web" in str(data_source).lower():
            st.success(f"✔️ Conectado a Excel Online ({data_source})")
        else:
            st.warning(f"⚠️ Usando copia local ({data_source})")
    
with col_time_info:
    st.info(f"🕒 **Actualizado:** {hora_lectura}")

df = st.session_state.df_cache
error = st.session_state.error
hora_lectura = st.session_state.hora_lectura
data_source = st.session_state.data_source

if df is not None:
    # --- AUTH HELPER ---
    def check_access(key_suffix):
        auth_key = f"auth_{key_suffix}"
        if st.session_state.get(auth_key, False):
            return True
        
        st.warning("🔒 Esta sección está protegida.")
        pwd = st.text_input("Contraseña:", type="password", key=f"pwd_{key_suffix}")
        if st.button("Acceder", key=f"btn_{key_suffix}"):
            if pwd == "1234":
                st.session_state[auth_key] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        return False

    # Definir pestañas dinámicamente según entorno
    tabs_list = [
        "📊 Panel Principal", 
        "🔍 Buscador de Pacientes", 
        "📋 Tabla Principal", 
        "📥 Descargas",
        "🔥 Mapa de Calor"
    ]
    
    # Unpacking de pestañas
    all_tabs = st.tabs(tabs_list)
    
    tab_dashboard = all_tabs[0]
    tab_search = all_tabs[1]
    tab_main = all_tabs[2]
    tab_downloads = all_tabs[3]
    tab_map = all_tabs[4]
    
    # Check si hay algun filtro activo
    filter_active = not (filt_year == "Todos" and filt_month_name == "Todos" and filt_patient == "Todos")

    # --- FILTRADO STRICTO (GLOBAL) ---
    # MODIFICADO JAIR: Mantenemos df_base intacto (con filas vacías y todo)
    # para que los KPIs globales (Total Programado: 1174) cuadren.
    # El filtrado visual se hará en df_final.
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

        # 2. Filtro de Paciente (Para Tablas y Gráficos)
        # AQUÍ SÍ eliminamos filas sin paciente para que los conteos de ordenes sean ~153
        mask_final = mask_period.copy()
        
        # Filtro base: Paciente no vacío
        if 'PACIENTES' in df_base.columns:
             mask_final = mask_final & (df_base['PACIENTES'].notna()) & (df_base['PACIENTES'].astype(str).str.strip() != "")

        if filt_patient != "Todos":
            mask_final = mask_final & (df_base['PACIENTES'].astype(str).str.strip().str.upper() == filt_patient)
             
        df_final = df_base[mask_final].copy()
    else:
        df_dash = df_base.copy()
        # En caso no haya filtro de fecha, igual limpiamos vacíos para df_final
        if 'PACIENTES' in df_base.columns:
             df_final = df_base[(df_base['PACIENTES'].notna()) & (df_base['PACIENTES'].astype(str).str.strip() != "")].copy()
        else:
             df_final = df_base.copy()

    with tab_dashboard:
        # --- CÁLCULO DE RANGO DE FECHAS VISIBLE ---
        rango_texto = "Periodo no definido"
        if 'FECHA_CLAVE' in df_dash.columns:
            dates_viz = df_dash['FECHA_CLAVE'].dropna()
            if not dates_viz.empty:
                min_d = dates_viz.min()
                max_d = dates_viz.max()
                m_map = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 
                         7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
                rango_texto = f"{m_map.get(min_d.month, '')} {min_d.year} - {m_map.get(max_d.month, '')} {max_d.year}"
        
        # Header informativo
        st.markdown(f"**📅 Periodo Analizado:** `{rango_texto}`")
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
                global_sesiones_saldo = int(s_p_base.sum())
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
                total_sesiones_saldo_final = int(s_pend_final.sum())
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
        # Wrapper para evitar "Ghost Elements" opacos al cambiar filtros
        alert_holder = st.empty()
        
        with alert_holder.container():
            # Helper para encontrar columna ID (MOVIDO ARRIBA para que esté disponible para Negative Balance)
            col_id_excel = None
            for c in df_final.columns:
                if str(c).upper().strip() in ['ID', 'Nº', 'NO', 'N.']:
                    col_id_excel = c
                    break
            if not col_id_excel: col_id_excel = df_final.columns[0] # Fallback primera col

            if IS_LOCAL and 'count_negativos' in locals() and count_negativos > 0:
                st.error(f"⚠️ **Atención:** Se han detectado **{count_negativos} casos** de pacientes con sesiones en exceso (Saldo Negativo).")
                with st.expander(f"Ver lista de {count_negativos} pacientes"):
                    if col_pend_final:
                        # Filtrar negativos
                        df_neg = df_final[pd.to_numeric(df_final[col_pend_final], errors='coerce').fillna(0) < 0].copy()
                        
                        # Columnas a mostrar
                        col_paciente = 'PACIENTES' if 'PACIENTES' in df_neg.columns else df_neg.columns[0]
                        
                        # Buscar columna de Terapia
                        col_terapia = 'ESPECIALIDAD' if 'ESPECIALIDAD' in df_neg.columns else ('PROGRAMAS' if 'PROGRAMAS' in df_neg.columns else None)
                        
                        cols_show_neg = []
                        if col_id_excel and col_id_excel != col_paciente: cols_show_neg.append(col_id_excel)
                        cols_show_neg.append(col_paciente)
                        if col_terapia: cols_show_neg.append(col_terapia) 
                        
                        # Agregado: CANT y REALIZADAS
                        if col_cant_final: cols_show_neg.append(col_cant_final)
                        if col_real_final: cols_show_neg.append(col_real_final)
                        
                        if col_pend_final: cols_show_neg.append(col_pend_final)
                        
                        # Formatear ID y numéricos para evitar decimales feos en la tabla
                        if col_id_excel in df_neg.columns and pd.api.types.is_numeric_dtype(df_neg[col_id_excel]):
                             df_neg[col_id_excel] = df_neg[col_id_excel].fillna(0).astype(int).astype(str)
                        
                        for c_num in [col_cant_final, col_real_final, col_pend_final]:
                            if c_num and c_num in df_neg.columns:
                                df_neg[c_num] = pd.to_numeric(df_neg[c_num], errors='coerce').fillna(0).astype(int)
                             
                        st.dataframe(df_neg[cols_show_neg], hide_index=True, use_container_width=True)
                
            c_alert1, c_alert2 = st.columns(2)
            
            # (Helper ID movido arriba)
    
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
                        col_paciente = 'PACIENTES' if 'PACIENTES' in df_alert.columns else df_alert.columns[0]
                        count_unique_patients = df_near[col_paciente].nunique()
                        st.warning(f"🔔 **Alerta:** {count_near} Ordenes por finalizar que son de {count_unique_patients} pacientes (≤ 2 sesiones).")
                        with st.expander(f"Ver lista de {count_near} ordenes"):
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
                    
                    # --- FILTRO POR ESTADO (Solicitud JAIR): SOLO PENDIENTE AGENDAMIENTO ---
                    if col_estado:
                         # Filtro flexible para capturar "PENDIENTE AGENDAMIENTO" SOLAMENTE
                         mask_status = (
                             (df_stagnant[col_estado].astype(str).str.upper().str.contains("PENDIENTE", na=False) & 
                              df_stagnant[col_estado].astype(str).str.upper().str.contains("AGENDAMIENTO", na=False))
                         )
                         mask_stagnant = mask_stagnant & mask_status
                    
                    df_stag_final = df_stagnant[mask_stagnant]
                    count_stag = len(df_stag_final)
                    
                    if count_stag > 0:
                        col_paciente = 'PACIENTES' if 'PACIENTES' in df_stag_final.columns else df_stag_final.columns[0]
                        count_unique_patients = df_stag_final[col_paciente].nunique()
                        
                        st.warning(f"⏳ **Alerta:** {count_stag} ordenamientos pendientes por agendar que son de {count_unique_patients} pacientes (> 5 días esperando).")
                        with st.expander(f"Ver lista de {count_stag} ordenamientos"):
                            
                            # --- FILTRO POR ESTADO (Request JAIR) ---
                            df_show_stag = df_stag_final.copy()
                            df_show_stag['Esperando'] = df_show_stag['dias_pasados'].astype(int).astype(str) + " días"
                            
                            # Identificar columnas solicitadas (Especialidad y DNI)
                            col_especialidad = next((c for c in df_stag_final.columns if "ESPECIALIDAD" in str(c).upper()), None)
                            col_dni = next((c for c in df_stag_final.columns if "DNI" in str(c).upper()), None)

                            cols_stag = []
                            if col_id_excel != col_paciente: cols_stag.append(col_id_excel)
                            cols_stag.append(col_paciente)
                            
                            # Agregar columnas solicitadas
                            if col_especialidad: cols_stag.append(col_especialidad)
                            if col_dni: cols_stag.append(col_dni)
                            
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
                            
                            # (Código eliminado que forzaba int y rompía leading zeros en el ID) 
                            if col_dni and col_dni in df_show_stag.columns:
                                df_show_stag[col_dni] = df_show_stag[col_dni].astype(str).str.replace(r'\.0+$', '', regex=True).str.strip()
                                df_show_stag[col_dni] = df_show_stag[col_dni].apply(lambda x: x.zfill(8) if x.isdigit() and len(x) == 7 else x)
                            # if col_id_excel in df_show_stag.columns ...
                            
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
        kpi1.metric("Pacientes Totales", total_global_pacientes, "Pacientes")
        
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

        kpi2.metric("Ordenes", total_global_terapias, "Terapias Ordenadas")
        
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

        # --- TOGGLE VISTA GENERAL vs MENSUAL ---
        # "Solo trabajaremos en el local ojo" -> "Por Mes" vs "General"
        # Usamos st.radio horizontal para simular segmented control
        # CSS PERSONALIZADO PARA BOTONES CON SOMBRA (SIN BOLITA)
        st.markdown("""
        <style>
            /* Ocultar la etiqueta del radio button "Modo de Visualización" si se muestra arriba */
            div[class*="stRadio"] > label {
                display: none;
            }
            
            /* Contenedor del grupo de botones */
            div[role="radiogroup"] {
                display: flex;
                flex-direction: row;
                gap: 12px;
            }

            /* Estilo base del botón (Label del radio) */
            div[role="radiogroup"] > label {
                background-color: #ffffff;
                padding: 10px 24px;
                border-radius: 12px;
                cursor: pointer;
                border: 1px solid #e0e0e0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05); /* Sombra suave */
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                width: auto;
            }
            
            /* Ocultar la "bolita" (circle) del radio button por defecto */
            div[role="radiogroup"] > label > div:first-child {
                display: none !important;
            }

            /* Hover del botón */
            div[role="radiogroup"] > label:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1);
                border-color: #bdbdbd;
            }

            /* Botón Seleccionado */
            div[role="radiogroup"] > label[data-checked="true"] {
                background-color: #262730; /* Color oscuro elegante */
                color: white;
                border: 1px solid #262730;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }
            
            /* Texto del botón seleccionado */
            div[role="radiogroup"] > label[data-checked="true"] div {
                color: white !important;
                font-weight: 600;
            }
        </style>
        """, unsafe_allow_html=True)

        view_mode = st.radio(
            "Modo de Visualización:",
            ["General", "Terapias por Paciente", "Por Mes"],
            horizontal=True,
            label_visibility="collapsed",
            key="view_mode_selector"
        )
        
        st.divider()

        # Configurar variable que determina la métrica
        ver_por_pacientes = (view_mode == "Terapias por Paciente")

        # --- 2. GRÁFICOS ESTRATÉGICOS ---
        if view_mode == "General":
            # Layout de 3 columnas: Terapias | Gestión (Donut) | Estados
            c1, c2, c3 = st.columns([1.2, 0.8, 1.2])
            container_terapias = c1
            container_gestion = c2
            container_pacientes = c3
        else: # Por Mes y Por Pacientes
            # Layout de 1 columna (Vertical) para MAXIMIZAR TAMAÑO
            # Al usar st.container(), se apilan uno debajo del otro ocupando todo el ancho
            c1 = st.container()
            c2 = st.container()
            
            container_terapias = c1
            container_gestion = None # Ocultar
            container_pacientes = c2
        
        with container_terapias:
            if view_mode in ["General", "Terapias por Paciente"]:
                st.subheader("📊 Terapias Solicitadas")
                
            if 'ESPECIALIDAD' in df_final.columns:

                
                # --- MODO GENERAL ---
                if view_mode == "General":
                    # 1. Preparar datos limpios (sobre df_final)
                    df_sp = df_final[df_final['ESPECIALIDAD'].notna() & (df_final['ESPECIALIDAD'] != '')]
                    
                    # 2. Calcular estadisticas
                    col_id = 'DNI' if 'DNI' in df_final.columns else 'PACIENTES'
                    
                    agg_dict = {
                        'Total_Terapias': ('ESPECIALIDAD', 'count')
                    }
                    
                    # JAIR: Sumamos Sesiones Programadas y Realizadas
                    col_c = next((c for c in df_sp.columns if "CANT" in str(c).upper()), None)
                    col_r = next((c for c in df_sp.columns if "REALIZADAS" in str(c).upper() or "EJECUTADAS" in str(c).upper()), None)

                    if col_c:
                        df_sp[col_c] = pd.to_numeric(df_sp[col_c], errors='coerce').fillna(0)
                        agg_dict['Sesiones_Programadas'] = (col_c, 'sum')
                    
                    if col_r:
                        df_sp[col_r] = pd.to_numeric(df_sp[col_r], errors='coerce').fillna(0)
                        agg_dict['Sesiones_Realizadas'] = (col_r, 'sum')

                    agg_dict['Pacientes_Unicos'] = (col_id, 'nunique')
                    
                    sp_stats = df_sp.groupby('ESPECIALIDAD').agg(**agg_dict).reset_index()
                    sp_stats = sp_stats.sort_values(by='Total_Terapias', ascending=False)
                    
                    # 3. Gráfico
                    tooltip_list = [
                        alt.Tooltip('ESPECIALIDAD', title='Especialidad'),
                        alt.Tooltip('Total_Terapias', title='Terapias Ordenadas'),
                        alt.Tooltip('Pacientes_Unicos', title='Pacientes Únicos')
                    ]
                    
                    if 'Sesiones_Programadas' in sp_stats.columns:
                        tooltip_list.append(alt.Tooltip('Sesiones_Programadas', title='Sesiones Programadas'))
                    if 'Sesiones_Realizadas' in sp_stats.columns:
                        tooltip_list.append(alt.Tooltip('Sesiones_Realizadas', title='Sesiones Realizadas'))

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
                        st.warning(f"⚠️ {missing_sp} filas sin Especialidad.")

                # --- MODO POR PACIENTES (NUEVO DISEÑO) ---
                elif view_mode == "Terapias por Paciente":
                    df_sp = df_final[df_final['ESPECIALIDAD'].notna() & (df_final['ESPECIALIDAD'] != '')].copy()
                    
                    if df_sp.empty:
                        st.warning("No hay datos de especialidad disponibles para graficar.")
                    else:
                        col_id = 'DNI' if 'DNI' in df_sp.columns else 'PACIENTES'
                        col_paciente = 'PACIENTES' if 'PACIENTES' in df_sp.columns else df_sp.columns[0]
                        
                        # Agrupar solo para contar únicos en la gráfica rápida superior
                        sp_stats = df_sp.groupby('ESPECIALIDAD')[col_id].nunique().reset_index(name='Pacientes_Unicos')
                        sp_stats = sp_stats.sort_values(by='Pacientes_Unicos', ascending=False)
                        
                        st.markdown("#### 👥 Pacientes por Especialidad")
                        
                        # Grafico de Barras de Pacientes unicos
                        base = alt.Chart(sp_stats).encode(
                            x=alt.X('Pacientes_Unicos', title='Pacientes Únicos'),
                            y=alt.Y('ESPECIALIDAD', sort='-x', title=''),
                            tooltip=[
                                alt.Tooltip('ESPECIALIDAD', title='Especialidad'),
                                alt.Tooltip('Pacientes_Unicos', title='Pacientes Únicos')
                            ]
                        )
                        bars = base.mark_bar(color="#FF4B4B")
                        text = base.mark_text(align='left', dx=3, color='black', fontWeight='bold').encode(text='Pacientes_Unicos')
                        
                        st.altair_chart((bars + text).properties(height=300), use_container_width=True)

                        st.divider()
                        
                        # --- LISTA DESPLEGABLE CON FILTRO ---
                        st.markdown("#### 📋 Detalle de Pacientes por Terapia y Estado")
                        
                        col_filt_1, col_filt_2 = st.columns(2)
                        
                        with col_filt_1:
                            # Obtener especialidades únicas de este dataframe filtrado
                            especialidades_disp = ["Todas"] + sorted(df_sp['ESPECIALIDAD'].unique().tolist())
                            sel_esp = st.selectbox("Seleccione tipo de terapia:", especialidades_disp, index=0)
                            
                        with col_filt_2:
                            # Filtro de Estado
                            if 'ESTADO' in df_sp.columns:
                                estados_disp = ["Todos"] + sorted([str(e) for e in df_sp['ESTADO'].unique().tolist() if pd.notna(e) and str(e).strip() != ''])
                            else:
                                estados_disp = ["Todos"]
                                
                            sel_estado = st.selectbox("Seleccione estado:", estados_disp, index=0)
                        
                        # Filtrar df según selección
                        df_list = df_sp.copy()
                        
                        if sel_esp != "Todas":
                            df_list = df_list[df_list['ESPECIALIDAD'] == sel_esp]
                            
                        if sel_estado != "Todos" and 'ESTADO' in df_list.columns:
                            df_list = df_list[df_list['ESTADO'].astype(str).str.strip() == sel_estado]
                            
                        # Limpiar para obtener 1 fila por paciente (El usuario quiere saber CUÁNTAS personas y QUIÉNES)
                        # Agruparemos por Paciente y traemos datos relevantes de su última gestión o suma de sesiones
                        
                        cols_grouped = [col_id, col_paciente]
                        # Tomamos la primera coincidencia de especialidad si es que buscan "Todas" (para mostrar qué hace)
                        # Y sumamos sesiones si están disponibles
                        
                        aggs_lista = {
                            'ESPECIALIDAD': lambda x: ', '.join(set(x.dropna().astype(str))), # Terapias del paciente
                        }
                        
                        col_c = next((c for c in df_list.columns if "CANT" in str(c).upper()), None)
                        col_p = next((c for c in df_list.columns if "PENDIENTES" in str(c).upper()), None)
                        
                        # OBTENER COLUMNAS D, E, H e I (Índices 3, 4, 7, 8) 
                        col_d = df_list.columns[3] if len(df_list.columns) > 3 else None
                        col_e = df_list.columns[4] if len(df_list.columns) > 4 else None
                        col_h = df_list.columns[7] if len(df_list.columns) > 7 else None
                        col_i = df_list.columns[8] if len(df_list.columns) > 8 else None
                        col_j = df_list.columns[9] if len(df_list.columns) > 9 else None
                        col_aj = df_list.columns[35] if len(df_list.columns) > 35 else None
                        
                        for extra_col in [col_d, col_e, col_h, col_i, col_j, col_aj]:
                            if extra_col and extra_col not in cols_grouped and extra_col not in aggs_lista:
                                if extra_col != col_c and extra_col != col_p:
                                    if pd.api.types.is_numeric_dtype(df_list[extra_col]):
                                        aggs_lista[extra_col] = 'sum'
                                    else:
                                        aggs_lista[extra_col] = lambda x: ', '.join(set(x.dropna().astype(str)))
                        
                        if col_c: aggs_lista[col_c] = 'sum'
                        if col_p: aggs_lista[col_p] = 'sum'
                        
                        # Agrupar
                        df_pacientes_unicos = df_list.groupby(cols_grouped).agg(aggs_lista).reset_index()
                        
                        # Limpiar ID si numerico para vista
                        if pd.api.types.is_numeric_dtype(df_pacientes_unicos[col_id]):
                            df_pacientes_unicos[col_id] = df_pacientes_unicos[col_id].fillna(0).astype(int).astype(str)
                            
                        st.success(f"📌 Se encontraron **{len(df_pacientes_unicos)} pacientes únicos** para la selección.")
                        
                        # Renombrar columnas para la tabla (Mejor presentación)
                        rename_cols = {
                            col_paciente: "Nombre del Paciente",
                            "ESPECIALIDAD": "Tipo de Terapias"
                        }
                        if col_d and col_d in df_pacientes_unicos.columns and col_d not in rename_cols:
                            rename_cols[col_d] = str(col_d).title()
                        if col_e and col_e in df_pacientes_unicos.columns and col_e not in rename_cols:
                            rename_cols[col_e] = "TLF"
                        if col_h and col_h in df_pacientes_unicos.columns and col_h not in rename_cols:
                            rename_cols[col_h] = "DISTRITO"
                        if col_i and col_i in df_pacientes_unicos.columns and col_i not in rename_cols:
                            rename_cols[col_i] = "PROGRAMAS"
                        if col_j and col_j in df_pacientes_unicos.columns and col_j not in rename_cols:
                            rename_cols[col_j] = "FECHA ORDEN"
                        if col_aj and col_aj in df_pacientes_unicos.columns and col_aj not in rename_cols:
                            rename_cols[col_aj] = "OBSERVACIÓN"
                            
                        if col_c: rename_cols[col_c] = "Total Ordenadas"
                        if col_p: rename_cols[col_p] = "Saldo Pendiente"
                        
                        df_mostrar = df_pacientes_unicos.rename(columns=rename_cols)
                        
                        st.dataframe(df_mostrar, hide_index=True, use_container_width=True)
                
                # --- MODO POR MES (Gráfico Solicitado) ---
                else: 
                    # 1. Preparar datos (SIN FILTRO DE FECHA - "All History")
                    # El usuario quiere ver la evolución completa (incluyendo futuros como Ene 2026),
                    # independientemente del filtro de año seleccionado en el sidebar.
                    
                    df_history = df.copy()
                    
                    # Aplicar SOLO filtro de Paciente si está activo
                    if filt_patient != "Todos":
                         if 'PACIENTES' in df_history.columns:
                             df_history = df_history[df_history['PACIENTES'].astype(str).str.strip().str.upper() == filt_patient]

                    if 'FECHA_CLAVE' in df_history.columns and 'ESPECIALIDAD' in df_history.columns:
                        df_m = df_history[df_history['ESPECIALIDAD'].notna() & (df_history['ESPECIALIDAD'] != '') & df_history['FECHA_CLAVE'].notna()].copy()
                        df_m['FECHA_CLAVE'] = pd.to_datetime(df_m['FECHA_CLAVE'], errors='coerce')
                        df_m = df_m.dropna(subset=['FECHA_CLAVE'])

                        
                        # Usamos el primer día del mes para ordenamiento correcto (Ene, Feb, Mar...)
                        df_m['Mes_Orden'] = df_m['FECHA_CLAVE'].apply(lambda x: x.replace(day=1))
                        
                        # Mapeo de Meses a Español corto con Año (Ejes: Ene25, Feb25...)
                        # Format similar to user request: "ener25" -> "Ene25"
                        
                        def format_mes_anio(d):
                            meses_corto = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                            m = meses_corto[d.month]
                            y = str(d.year)[-2:] # Últimos 2 dígitos
                            return f"{m}{y}"

                        df_m['Mes_Nombre'] = df_m['Mes_Orden'].apply(format_mes_anio)

                        # Agregamos conteo (Incluimos Mes_Orden y Mes_Nombre para poder ordenar)
                        agg_m = df_m.groupby(['Mes_Orden', 'Mes_Nombre', 'ESPECIALIDAD']).size().reset_index(name='Cantidad')

                        
                        st.markdown(f"""

                        <style>
                        /* Estilo de sombra personalizado para el gráfico */
                        .chart-container {{
                            background-color: white;
                            padding: 20px;
                            border-radius: 12px;
                            box-shadow: 0 4px 15px rgba(0,0,0,0.1); /* Sombra suave */
                            border: 1px solid #eee;
                            margin-bottom: 20px;
                        }}
                        </style>
                        """, unsafe_allow_html=True)

                        # --- LAYOUT APILADO (UNA GRÁFICA POR FILA) ---
                        
                        # --- 1ERA GRÁFICA: ESPECIALIDAD ---
                        st.markdown("#### 📅 Por Especialidad")
                        st.caption("Evolución mensual de terapias por tipo.")

                        # Agregamos conteo existente
                        # (agg_m ya creado arriba)
                        
                        base = alt.Chart(agg_m).encode(
                            x=alt.X('ESPECIALIDAD', title=None, axis=alt.Axis(labelAngle=-90, labelLimit=80)), 
                            y=alt.Y('Cantidad', title='Cantidad'),
                            color=alt.Color('ESPECIALIDAD', legend=alt.Legend(orient='right', title='Tipo de Terapia'), scale=alt.Scale(range=['#2C3E50', '#7F8C8D', '#34495E', '#95A5A6', '#1A5276', '#5D6D7E'])), 
                            tooltip=[
                                alt.Tooltip('Mes_Nombre', title='Mes'),
                                alt.Tooltip('ESPECIALIDAD', title='Especialidad'),
                                alt.Tooltip('Cantidad', title='Cantidad')
                            ]
                        )
                        
                        bars = base.mark_bar().encode(opacity=alt.value(0.9))
                        text = base.mark_text(dy=-10, color='black', fontSize=10, fontWeight='bold').encode(
                            text=alt.Text('Cantidad')
                        )
                        
                        final_chart = (bars + text).properties(
                            width=alt.Step(40), 
                            height=300
                        ).facet(
                            column=alt.Column('Mes_Nombre:O', title=None, sort=alt.SortField('Mes_Orden'), header=alt.Header(titleOrient="bottom", labelOrient="bottom", labelFontSize=12, labelFontWeight="bold")), 
                            spacing=5 
                        ).resolve_scale(y='shared') 
                        
                        with st.container(height=450, border=True):
                             st.altair_chart(final_chart, use_container_width=True)

                        # --- 2DA GRÁFICA: ESTADO ---
                        st.markdown("#### ⏳ Por Estado")
                        st.caption("Evolución mensual del estado de las gestiones.")
                        
                        if 'ESTADO' in df_m.columns:
                            # Agrupar por Mes y ESTADO
                            agg_st = df_m.groupby(['Mes_Orden', 'Mes_Nombre', 'ESTADO']).size().reset_index(name='Cantidad')
                            
                            base_st = alt.Chart(agg_st).encode(

                                x=alt.X('ESTADO', title=None, axis=alt.Axis(labelAngle=-90, labelLimit=80)), 
                                y=alt.Y('Cantidad', title='Cantidad'),
                                color=alt.Color('ESTADO', legend=alt.Legend(orient='right', title='Estado Gestión'), scale=alt.Scale(range=['#4A235A', '#6E2C00', '#145A32', '#1B4F72', '#78281F', '#4D5656'])), # Sober executive color scheme
                                tooltip=[
                                    alt.Tooltip('Mes_Nombre', title='Mes'),
                                    alt.Tooltip('ESTADO', title='Estado'),
                                    alt.Tooltip('Cantidad', title='Cantidad')
                                ]
                            )
                            
                            bars_st = base_st.mark_bar().encode(opacity=alt.value(0.9))
                            text_st = base_st.mark_text(dy=-10, color='black', fontSize=10, fontWeight='bold').encode(
                                text=alt.Text('Cantidad')
                            )
                            
                            final_chart_st = (bars_st + text_st).properties(
                                width=alt.Step(40), 
                                height=300
                            ).facet(
                                column=alt.Column('Mes_Nombre:O', title=None, sort=alt.SortField('Mes_Orden'), header=alt.Header(titleOrient="bottom", labelOrient="bottom", labelFontSize=12, labelFontWeight="bold")), 
                                spacing=5 
                            ).resolve_scale(y='shared') 
                            
                            with st.container(height=450, border=True):
                                 st.altair_chart(final_chart_st, use_container_width=True)
                        else:
                            st.warning("Columna ESTADO no encontrada en los datos filtrados.")




                        
                    else:
                        st.warning("Faltan columnas necesarias (FECHA o ESPECIALIDAD) para el gráfico mensual.")


            else:
                st.warning("Columna ESPECIALIDAD no encontrada")
                
        if container_gestion:
            # Solo mostrar en MODO GENERAL o POR PACIENTES
            if view_mode in ["General", "Terapias por Paciente"]:
                with container_gestion:
                    st.subheader("⏳ Estado de Gestión")
                    if col_estado_found:
                        # Si ver_por_pacientes es True, agrupar por paciente y tomar el estado más 'avanzado' 
                        # o simplemente mapear contornos únicos.
                        # Para mantenerlo simple y preciso:
                        
                        if ver_por_pacientes:
                            # Contar pacientes únicos por estado
                            col_id = 'DNI' if 'DNI' in df_final.columns else 'PACIENTES'
                            estado_counts = df_final[df_final[col_estado_found].notna()].groupby(col_estado_found)[col_id].nunique()
                            
                            total_graf_final = estado_counts.sum()
                            
                            # Identificar indices por keyword
                            idx_realizada = [i for i in estado_counts.index if i.strip().upper() in ['FINALIZADO', 'EN PROCESO']]
                            idx_pend = [i for i in estado_counts.index if 'AGENDAMIENTO' in i.strip().upper()]
                            
                            count_gestion_realizada = estado_counts[idx_realizada].sum() if idx_realizada else 0
                            count_pend_agendamiento = estado_counts[idx_pend].sum() if idx_pend else 0
                            count_otros = total_graf_final - count_gestion_realizada - count_pend_agendamiento
                            
                        else:
                            # Normalizar serie para cálculos de la gráfica original (Por Terapias)
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
                        
                        source_gest["Percentage"] = (source_gest["Total"] / total_graf_final * 100).fillna(0) if total_graf_final > 0 else 0
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

                        # Etiquetas laterales
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


        with container_pacientes:
            if view_mode == "General":
                st.subheader("📋 Estado Pacientes")

            if 'ESTADO' in df_final.columns:
                
                # --- MODO GENERAL ---
                if view_mode == "General":
                    df_st_valid = df_final[df_final['ESTADO'].notna() & (df_final['ESTADO'] != '')]
                    
                    total_counts = df_st_valid['ESTADO'].value_counts().reset_index()
                    total_counts.columns = ['Estado', 'Total Terapias']
                    
                    col_id = 'DNI' if 'DNI' in df_final.columns else 'PACIENTES'
                    unique_counts = df_st_valid.groupby('ESTADO')[col_id].nunique().reset_index()
                    unique_counts.columns = ['Estado', 'Pacientes']
                    
                    # --- AGREGAR SESIONES REALIZADAS ---
                    df_st_viz = df_st_valid.copy()
                    
                    col_real_viz = None
                    for c in df_st_viz.columns:
                        if "REALIZADAS" in str(c).upper():
                            col_real_viz = c
                            df_st_viz[c] = pd.to_numeric(df_st_viz[c], errors='coerce').fillna(0)
                            break
                    
                    real_counts = pd.DataFrame()
                    if col_real_viz:
                        real_counts = df_st_viz.groupby('ESTADO')[col_real_viz].sum().reset_index()
                        real_counts.columns = ['Estado', 'Sesiones Realizadas']

                    # --- AGREGAR SESIONES PROGRAMADAS ---
                    prog_counts = pd.DataFrame()
                    col_prog_viz = None
                    for c in df_st_viz.columns:
                        if "CANT" in str(c).upper():
                            col_prog_viz = c
                            df_st_viz[c] = pd.to_numeric(df_st_viz[c], errors='coerce').fillna(0)
                            break
                    
                    if col_prog_viz:
                        prog_counts = df_st_viz.groupby('ESTADO')[col_prog_viz].sum().reset_index()
                        prog_counts.columns = ['Estado', 'Sesiones Programadas']
                    
                    # Merge de todas las métricas
                    final_stats = pd.merge(total_counts, unique_counts, on='Estado')
                    if not real_counts.empty:
                        final_stats = pd.merge(final_stats, real_counts, on='Estado')
                    if not prog_counts.empty:
                        final_stats = pd.merge(final_stats, prog_counts, on='Estado')
                    
                    var_graf_st = 'Total Terapias'
                    titulo_graf_st = 'Total Terapias'
                    
                    final_stats = final_stats.sort_values(by=var_graf_st, ascending=False)
                    
                    tooltip_list = ['Estado', 'Total Terapias', 'Pacientes']
                    if not prog_counts.empty:
                        tooltip_list.append('Sesiones Programadas')
                    if not real_counts.empty:
                        tooltip_list.append('Sesiones Realizadas')

                    base_st = alt.Chart(final_stats).encode(
                        x=alt.X(var_graf_st, title=titulo_graf_st),
                        y=alt.Y('Estado', sort='-x', title=''),
                        tooltip=tooltip_list
                    )
                    bars_st = base_st.mark_bar(color="#FF4B4B")
                    text_st = base_st.mark_text(align='left', dx=3, color='black').encode(text=var_graf_st)
                    
                    st.altair_chart((bars_st + text_st).properties(height=350), use_container_width=True)
                
                # --- MODO MENSUAL O POR PACIENTES (Vacío para esta subsección) ---
                else: 
                     pass



                if view_mode == "General":
                     missing_st = df_final[df_final['PACIENTES'].notna() & (df_final['ESTADO'].isna() | (df_final['ESTADO'] == ''))].shape[0]
                     if missing_st > 0:
                         st.warning(f"⚠️ {missing_st} filas con Estado vacío.")

            else:
                 if view_mode == "General":
                      st.warning("Columna ESTADO no encontrada")
        
        st.divider()
        
        # --- 3. GEOGRAFÍA ---
        if view_mode == "General" and 'DISTRITO' in df_final.columns:
             
             # --- TOGGLE DISTRIBUCIÓN POR DISTRITO (Pedido Usuario) ---
             st.subheader("🗺️ Distribución por Distritos")
             
             # Opciones de visualización
             opt_map_mode = st.radio(
                 "Métrica de Distribución:",
                 ["Distribución Pacientes por Distrito (Únicos)", "Visitas por Distrito (Total)"],
                 horizontal=True,
                 index=0 if ver_por_pacientes else 1, # Si es modo 'Por Pacientes' fuerzalo visualmente a únicos por default (o 0 que es el orginal)
                 label_visibility="collapsed"
             )
             
             dist_chart_title = "Distribución Pacientes por Distrito"
             
             # Usamos 'DISTRITO' (ya normalizado en df_final si existe)
             col_dist_viz = "DISTRITO"
             col_p_viz = "PACIENTES"
             
             if col_dist_viz in df_final.columns:
                 data_dist = None
                 
                 # Si ver_por_pacientes global es true, forzamos vista únicos visualmente si así lo prefieres,
                 # O usamos la seleccion del radio botón pero con un default dinámico (hecho arriba).
                 if "Únicos" in opt_map_mode:
                     # Modo 1: Pacientes Únicos
                     if col_p_viz in df_final.columns:
                        # Agrupar por distrito y contar únicos
                        data_dist = df_final.groupby(col_dist_viz)[col_p_viz].nunique().reset_index(name='CANTIDAD')
                        data_dist = data_dist.sort_values('CANTIDAD', ascending=False)
                        dist_chart_title = "Distribución Pacientes por Distrito"
                 else:
                     # Modo 2: Visitas Totales (Original)
                     data_dist = df_final[col_dist_viz].value_counts().reset_index()
                     data_dist.columns = [col_dist_viz, 'CANTIDAD']
                     dist_chart_title = "Distribución por Distritos (Visitas Totales)"

                 if data_dist is not None and not data_dist.empty:
                     # Restaurar estilo original (Vertical + Rojo #FF4B4B)
                     # Eje X = Distritos, Eje Y = Cantidad
                     
                     col_x_name = data_dist.columns[0] # Distrito
                     
                     bars_dist = alt.Chart(data_dist).mark_bar(color="#FF4B4B").encode(
                        x=alt.X(col_x_name, sort='-y', title='Distrito'),
                        y=alt.Y('CANTIDAD', title='Total Pacientes'),
                        tooltip=[col_x_name, 'CANTIDAD']
                     ).properties(title=dist_chart_title)
                     
                     text_dist = bars_dist.mark_text(
                        align='center',
                        baseline='bottom',
                        dy=-5, # Encima de la barra
                        color='black',
                        fontWeight='bold',
                        fontSize=12,
                        clip=False # Evita que desaparezcan al borde
                     ).encode(
                        text=alt.Text('CANTIDAD', format='d')
                     )
                     
                     # Aumentamos height a 600 para que el eje sea "más alto"
                     # Agregamos config para que no desaparezcan etiquetas al solaparse (opcional)
                     final_dist = (bars_dist + text_dist).properties(height=600).interactive()
                     st.altair_chart(final_dist, use_container_width=True)
                 else:
                     st.info("No hay datos de distrito disponibles para graficar.")
             else:
                 st.warning("Columna DISTRITO no encontrada para generar gráfica.")

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
                    
                    # Agregar Pendientes al título
                    pend = r.get('PENDIENTES', 0)
                    # Intentar formatear a int si es posible
                    try: pend = int(pend)
                    except: pass
                    
                    l = f"{esp} (Inicio: {f_s}) | Pendientes: {pend}"
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
                    st.write(f"📍 **Distrito:** {p_data_found.get('DISTRITO', 'Sin Registro')}")
                    st.write(f"🏠 **Dirección:** {p_data_found.get('DIRECCION', 'Sin Registro')}")
                    
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
                        
                        # Reemplazamos scatter_chart por Altair explícito para controlar etiquetas en ESPAÑOL
                        # Usamos 'labelExpr' de Vega-Lite para forzar los meses en Español sin depender del Locale del servidor
                        spanish_months = "['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']"
                        # Expr: "15 de Enero del 2025"
                        axis_expr = f"date(datum.value) + ' de ' + {spanish_months}[month(datum.value)] + ' del ' + year(datum.value)"
                        
                        c_asist = alt.Chart(df_tl).mark_circle(size=120).encode( # Color por defecto (azul/theme)
                            x=alt.X('Fecha', title='Fecha de Asistencia', axis=alt.Axis(labelExpr=axis_expr)),
                            y=alt.Y('Ses', title='Sesión', sort=None), 
                            tooltip=[
                                alt.Tooltip('Fecha', title='Fecha', format='%d/%m/%Y'),
                                alt.Tooltip('Ses', title='Sesión')
                            ]
                        ).properties(
                            height=300
                        ).interactive()
                        
                        st.altair_chart(c_asist, use_container_width=True)
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
        st.info("ℹ️ Modo Lectura: La edición está desactivada en la versión pública.")
        
        
        # --- ULTIMA LIMPIEZA DE FORMATO (ID/DNI) ---
        # Aseguramos que los IDs se vean limpios sin .0 decimal y con ceros a la izquierda si aplica
        clean_cols = ['DNI', 'ID', 'DOCUMENTO', 'CODIGO']
        cols_to_pad = ['DNI', 'DOCUMENTO'] # Solo estos suelen necesitar padding a 8

        for c in clean_cols:
            if c in df_final.columns:
                # 1. Transformamos a string
                s_col = df_final[c].astype(str)
                # 2. Reemplazamos .0 al final
                s_col = s_col.str.replace(r'\.0+$', '', regex=True)
                
                # 3. PADDING (Solo para DNI/Documento y si son números)
                if c in cols_to_pad:
                    def smart_pad(val):
                        # Si es numérico puro y tiene menis de 8 digitos, rellenar (ej. 12345 -> 00012345)
                        if val.isdigit() and len(val) < 8 and len(val) > 4: # >4 evita padear IDs cortos como '1'
                            return val.zfill(8)
                        return val
                    s_col = s_col.map(smart_pad)
                
                df_final[c] = s_col

        # Configuración "Ejecutiva" para las columnas clave
        # Nota: Las columnas que no estén aquí se mostrarán por defecto (no se oculta nada)
        executive_config = {
            "PACIENTES": st.column_config.TextColumn("Paciente", width="medium", help="Nombre del paciente"),
            "ID": st.column_config.TextColumn("ID", width="small"),
            "DNI": st.column_config.TextColumn("Documento", width="small"),
            "TLF": st.column_config.TextColumn("Teléfono", width="small"),
            "DISTRITO": st.column_config.TextColumn("Distrito", width="small"),
            "DIRECCION": st.column_config.TextColumn("Dirección", width="medium"),
            "ESPECIALIDAD": st.column_config.TextColumn("Especialidad", width="medium"),
            "PROGRAMAS": st.column_config.TextColumn("Programa", width="medium"),
            "CANT.": st.column_config.NumberColumn("Cant.", help="Total de sesiones", format="%d"),
            "ESTADO": st.column_config.TextColumn("Estado Actual", width="small"),
            "CLINICA": st.column_config.TextColumn("Clínica", width="small"),
        }
        
        # --- ESTILO VISUAL (Pandas Styler) ---
        # Función para dar color de fondo según el estado (Estilo Semáforo Ejecutivo)
        def color_kpi_status(val):
            if not isinstance(val, str): return ''
            
            v = val.upper()
            # Verde (Positivo/Terminado)
            if 'TERMINMADO' in v or 'FINALIZADO' in v or 'ASISTI' in v or 'COMPLET' in v:
                return 'background-color: #d1e7dd; color: #0f5132; font-weight: 600;' 
            # Rojo/Rosado (Urgente/Pendiente)
            elif 'PENDIENTE' in v or 'ESPERA' in v or 'CANCEL' in v:
                return 'background-color: #f8d7da; color: #842029; font-weight: 600;'
            # Azul (En Proceso)
            elif 'PROCESO' in v or 'AGENDA' in v or 'INICIAD' in v:
                return 'background-color: #cff4fc; color: #055160; font-weight: 600;'
            
            return '' # Neutro

        # Aplicamos el estilo si existe la columna ESTADO
        if 'ESTADO' in df_final.columns:
            styled_df = df_final.style.map(color_kpi_status, subset=['ESTADO'])
        else:
            styled_df = df_final

        # Tabla de solo lectura - Respetando filtros y estilos
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            column_config=executive_config
        )

    
    with tab_downloads:
        st.header("📥 Descarga de Reporte Detallado")
        st.info("Este reporte desglosa cada sesión en una fila individual (Formato Vertical).")
        
        # Estado de autenticacion local para descargas
        is_auth_down = st.session_state.get("auth_downloads", False)
        should_auto_run = st.session_state.get("auto_gen_report", False)
        
        # --- Lógica de Autenticación con Popover (Más estable) ---
        if not is_auth_down:
            # Popover actúa como un botón que despliega un mini-modal flotante
            with st.popover("� Generar Reporte Detallado"):
                st.write("🔒 **Seguridad**")
                st.caption("Ingresa la clave de administrador (12345)")
                
                pwd_pop = st.text_input("Contraseña:", type="password", key="pwd_popover")
                
                if st.button("Desbloquear", key="btn_pop_unlock"):
                    if pwd_pop == "12345":
                        st.session_state["auth_downloads"] = True
                        st.session_state["auto_gen_report"] = True
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta")
        
        else:
            # Si YA está autenticado, mostramos mensaje y lógica
            st.success("🔓 Acceso concedido")
            
            # Lógica de "Explosión" (Unpivot/Melt inteligente)
            if should_auto_run or st.button("🚀 (Re) Generar Reporte Detallado", key="btn_gen_real"):
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
                            "DIRECCION": row.get('DIRECCION', ''), 
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
                        
                        st.success(f"✅ Reporte generado: {len(df_export)} filas individuales. (Sesión Autenticada)")
                        
                        # Botón de descarga real
                        st.download_button(
                            label="💾 DESCARGAR EXCEL (VERTICAL)",
                            data=buffer.getvalue(),
                            file_name="reporte_sesiones_vertical.xlsx",
                            mime="application/vnd.ms-excel"
                        )
                    else:
                        st.warning("No se encontraron datos para exportar.")
    if tab_map:
        with tab_map:
             # Pasamos df_final que ya tiene los filtros aplicados (Fechas/Pacientes)
             mapas.render_heatmap(df_final)

else:
    st.error(f"⚠️ No se pudieron cargar datos.")
    if error:
        st.code(error)
        
    st.info("� Intenta guardar tu Excel Online y espera 5 minutos para que baje a tu PC.")
    
# Lógica de Auto-refresco (al final)
if 'enable_autorefresh' in locals() and enable_autorefresh:
    time.sleep(locals().get('refresh_interval', 300))
    st.rerun()