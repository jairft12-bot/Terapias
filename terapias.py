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
            
            /* RESET: Don't hide these, they kill the sidebar toggle */
            /* [data-testid="stToolbar"] {display: none !important;} */
            /* [data-testid="stDecoration"] {display: none !important;} */
            /* header {display: none !important;}  <-- ESTO OCULTABA EL SIDEBAR */
            /* [data-testid="stHeader"] {display: none !important;} <-- ESTO TAMBIEN */
            
            /* Custom Scrollbar for Sidebar */
            [data-testid="stSidebar"] ::-webkit-scrollbar {
                display: block !important;
                width: 12px !important;
                height: 12px !important;
            }
            [data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
                background-color: #888 !important; 
                border-radius: 6px !important;
            }
            [data-testid="stSidebar"] ::-webkit-scrollbar-track {
                background: #f1f1f1 !important; 
            }
            
            /* sidebar toggle button styling */
            [data-testid="stSidebarCollapsedControl"] {
                display: block !important;
                visibility: visible !important;
                color: #000 !important;
                background-color: rgba(255, 255, 255, 0.9) !important;
                border: 1px solid #ddd !important;
                border-radius: 50% !important;
                z-index: 1000000 !important;
                
                /* Position fallback if it's lost in the header */
                /* position: fixed !important; */
                /* top: 60px !important; */
                /* left: 10px !important; */
            }
            
            /* Ensure the toggle icon inside is visible */
            [data-testid="stSidebarCollapsedControl"] svg {
                fill: #000 !important;
                stroke: #000 !important;
            }

            /* --- SIDEBAR RESCUE --- */
            /* Keep strict scrolling enabled */
            section[data-testid="stSidebar"] > div {
                flex-shrink: 0 !important;
                height: 100vh !important;
                overflow-y: auto !important; 
                z-index: 999999 !important;
            }

            /* Ensure buttons inside sidebar are seen */
            [data-testid="stSidebar"] button {
                display: flex !important;
                visibility: visible !important;
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
    # Initial load attempt
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
                # pattern = r'(?:^|[\s\-\/])' + mes_txt + r'(?:$|[\s\-\/])' 
                # Simplificado: \b es boundary (pero ojo con guiones). 
                # Mejor explicit:
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
            
            # Si no es texto, intentar parser standard
            return pd.to_datetime(text)
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
        st.header("📅 Filtro de Tiempo")
        st.caption("Filtra por fecha de término (CANT)")
        
        filt_year = st.selectbox("Año:", opciones_anio, index=0)
        filt_month_name = st.selectbox("Mes:", opciones_mes, index=0)
        
        filt_month_num = None
        filter_active = False
        
        if filt_year != "Todos" or filt_month_name != "Todos":
             filter_active = True
             if filt_month_name != "Todos":
                 rev_map = {v:k for k,v in month_map.items()}
                 filt_month_num = rev_map[filt_month_name]



        # 3. CONTROLES LOCALES (Discretos abajo)
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
        "📊 Dashboard ", 
        "🔍 Buscador de Pacientes", 
        "📋 Tabla Principal", 
        "📥 Descargas"
    ])
    
    # --- FILTRADO STRICTO (GLOBAL) ---
    # Volvemos al filtrado estricto.
    if 'PACIENTES' in df.columns:
        df_base = df[df['PACIENTES'].notna() & (df['PACIENTES'].astype(str).str.strip() != '')].copy()
    else:
        df_base = df.copy()

    # --- APLICAR FILTRO DE FECHAS AL DF_CLEAN ---
    # --- APLICAR FILTRO DE FECHAS AL DF_CLEAN ---
    # Recalcular trigger para asegurar consistencia
    filter_active = False
    if filt_year != "Todos" or filt_month_name != "Todos":
        filter_active = True
        
    if filter_active:
        # Filtrar usando FECHA_CLAVE
        # Asegurar que df_base tenga esa columna
        if 'FECHA_CLAVE' not in df_base.columns:
            df_base['FECHA_CLAVE'] = df.loc[df_base.index, 'FECHA_CLAVE']
            
        # Aplicar condiciones
        mask = pd.Series([True]*len(df_base), index=df_base.index)
        
        if filt_year != "Todos":
             mask = mask & (df_base['FECHA_CLAVE'].apply(lambda x: str(x.year) if pd.notna(x) else '') == filt_year)
             
        if filt_month_name != "Todos":
             # Recalcular numero de mes localmente
             mes_map_local = {"Enero":1, "Febrero":2, "Marzo":3, "Abril":4, "Mayo":5, "Junio":6, 
                              "Julio":7, "Agosto":8, "Septiembre":9, "Octubre":10, "Noviembre":11, "Diciembre":12}
             f_num = mes_map_local.get(filt_month_name, -1)
             
             mask = mask & (df_base['FECHA_CLAVE'].apply(lambda x: x.month if pd.notna(x) else -1) == f_num)
             
        # Guardar el filtrado final
        df_clean = df_base[mask].copy()
    else:
        df_clean = df_base.copy() # Sin filtro de fecha

    with tab_dashboard:
        st.caption(f"Visualizando datos de: {data_source} | Actualizado: {hora_lectura}")
        
        # --- 1. KPIS (TARJETAS) ---
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        # KPI 1: Total Pacientes
        col_dni = 'DNI' if 'DNI' in df_clean.columns else 'DNI ' # Space matters?
        if col_dni not in df_clean.columns and 'DNI' in df_clean.columns: col_dni = 'DNI'
            
        if col_dni in df_clean.columns:
             total_pacientes = df_clean[col_dni].nunique()
        else:
             total_pacientes = len(df_clean) # Fallback count rows
             
        kpi1.metric("Pacientes", total_pacientes)
       
        # KPI 2: Total Terapias / Sesiones
        if filter_active:
            # Mostramos el total de FILAS que caen en ese mes de término
            total_filas = len(df_clean)
            label_kpi2 = f"Agendamiento {filt_month_name}" if filt_month_name != "Todos" else "Agendamiento Año"
            kpi2.metric(label_kpi2, total_filas, help="Pacientes agendados en este periodo (Según Columna I).")
        else:
            total_filas = len(df_clean)
            kpi2.metric("Terapias Ordenadas", total_filas)


        # KPI 3, 4, 5: Desglose de Estados - USANDO DF_CLEAN
        try:
            # Ya tenemos df_clean
            df_kpi_valid = df_clean
            total_validas = len(df_kpi_valid)
            
            # Buscar columna ESTADO flexiblemente
            col_estado_found = None
            for c in df_clean.columns:
                if "ESTADO" in str(c).upper().strip():
                    col_estado_found = c
                    break
            
            if col_estado_found:
                # Normalizar serie
                s_estado = df_kpi_valid[col_estado_found].astype(str).str.upper().str.strip()
                
                # --- KPI 3: Gestión Realizada (FINALIZADO + EN PROCESO) ---
                gestor_mask = s_estado.isin(['FINALIZADO', 'EN PROCESO'])
                count_gestion = s_estado[gestor_mask].shape[0]
                tasa_gestion = (count_gestion / total_validas * 100) if total_validas > 0 else 0
                
                kpi3.metric(
                    "Gestión De Agen Realizada", 
                    f"{tasa_gestion:.1f}%", 
                    f"{count_gestion} Fin/Proceso"
                )
                
                # --- KPI 4: Pendiente Agendamiento ---
                pend_ag_mask = s_estado.str.contains("AGENDAMIENTO", case=False, na=False)
                count_pend_ag = s_estado[pend_ag_mask].shape[0]
                tasa_pend_ag = (count_pend_ag / total_validas * 100) if total_validas > 0 else 0
                
                kpi4.metric(
                    "Pendiente Agendamiento",
                    f"{tasa_pend_ag:.1f}%",
                    f"{count_pend_ag} Por Agendar",
                    delta_color="inverse"
                )
                
                # --- KPI 5: Sesiones Realizadas (Avance) ---
                # Solicitud: Programado (K), Realizado (L), Pendientes (M)
                # Usamos df_clean para asegurar que no sumamos filas vacías
                
                total_sesiones_saldo = 0
                count_negativos = 0
                
                # Columna Pendientes (M usualmente)
                if 'PENDIENTES' in df_clean.columns:
                     s_pend_col = pd.to_numeric(df_clean['PENDIENTES'], errors='coerce').fillna(0)
                     total_sesiones_saldo = int(s_pend_col[s_pend_col > 0].sum())
                     count_negativos = int(s_pend_col[s_pend_col < 0].count())
                else:
                    s_pend_col = pd.Series([0]*len(df_clean))
                
                # Columna Programado/Cant (K usualmente)
                col_cant = 'CANT.' if 'CANT.' in df_clean.columns else 'CANT'
                total_programado_kpi = 0
                if col_cant in df_clean.columns:
                     total_programado_kpi = pd.to_numeric(df_clean[col_cant], errors='coerce').fillna(0).sum()
                
                # Columna Realizadas/Ejecutadas (L usualmente)
                col_realizadas = None
                for c in df_clean.columns:
                    if "REALIZADAS" in str(c) or "EJECUTADAS" in str(c):
                        col_realizadas = c
                        break
                
                total_ejecutadas_kpi = 0
                if col_realizadas:
                     total_ejecutadas_kpi = pd.to_numeric(df_clean[col_realizadas], errors='coerce').fillna(0).sum()
                else:
                     # Fallback seguro: Programado - Pendientes
                     total_ejecutadas_kpi = total_programado_kpi - s_pend_col.sum()
                
                tasa_ejecucion = (total_ejecutadas_kpi / total_programado_kpi * 100) if total_programado_kpi > 0 else 0
                
                kpi5.metric(
                    "Sesiones Realizadas",
                    f"{tasa_ejecucion:.1f}%",
                    f"{int(total_ejecutadas_kpi)} Ejecutadas",
                    delta_color="normal" # Verde por defecto si es positivo
                )
                
                if count_negativos > 0:
                    kpi5.caption(f"⚠️ {count_negativos} casos con exceso (negativos)")

            else:
                 kpi3.metric("Gestión", "N/A", "Sin Estado")
                 kpi4.metric("P. Agendamiento", "N/A", "Sin Estado")
                 kpi5.metric("P. Ejecución", "N/A", "Sin Estado")
                 
        except Exception as e:
            kpi3.metric("Error", "!!!", str(e))

        st.divider()

        # --- 2. GRÁFICOS ESTRATÉGICOS (Layout Ajustado: 3 Columnas) ---
        # Izquierda: Especialidad | Centro: Donut Balance | Derecha: Estado
        c1, c2, c3 = st.columns([1.2, 0.8, 1.2])
        
        with c1:
            st.subheader("📊 Terapias Solicitadas")
            if 'ESPECIALIDAD' in df_clean.columns:
                # 1. Preparar datos limpios (sobre df_clean)
                df_sp = df_clean[df_clean['ESPECIALIDAD'].notna() & (df_clean['ESPECIALIDAD'] != '')]
                
                # 2. Calcular estadisticas
                col_id = 'DNI' if 'DNI' in df_clean.columns else 'PACIENTES'
                sp_stats = df_sp.groupby('ESPECIALIDAD').agg(
                    Total_Terapias=('ESPECIALIDAD', 'count'),
                    Pacientes_Unicos=(col_id, 'nunique')
                ).reset_index().sort_values(by="Total_Terapias", ascending=False)
                
                # 3. Gráfico
                base = alt.Chart(sp_stats).encode(
                    x=alt.X('Total_Terapias', title='Total Ordenadas'),
                    y=alt.Y('ESPECIALIDAD', sort='-x', title=''),
                    tooltip=[
                        alt.Tooltip('ESPECIALIDAD', title='Especialidad'),
                        alt.Tooltip('Total_Terapias', title='Terapias Ordenadas'),
                        alt.Tooltip('Pacientes_Unicos', title='Pacientes Únicos')
                    ]
                )
                bars = base.mark_bar(color="#FF4B4B")
                text = base.mark_text(align='left', dx=3, color='black').encode(text='Total_Terapias')
                
                st.altair_chart((bars + text).properties(height=350), use_container_width=True)
                
                missing_sp = df_clean[df_clean['ESPECIALIDAD'].isna() | (df_clean['ESPECIALIDAD'] == '')].shape[0]
                if missing_sp > 0:
                    st.warning(f"⚠️ Atención: Hay {missing_sp} filas con Especialidad vacía (No salen en la gráfica).")
            else:
                st.warning("Columna ESPECIALIDAD no encontrada")
                
        with c2:
            st.subheader("⏳ Sesiones de Terapia")
            # USAMOS VARIABLES CALCULADAS ARRIBA (que ya usan df_clean)
            # para consistencia perfecta KPI vs Gráfica
            
            tot_prog_s = total_programado_kpi
            tot_ejec_s = total_ejecutadas_kpi
            # Pendientes para gráfica (solo positivos visualmente)
            tot_pend_s = 0
            if 'PENDIENTES' in df_clean.columns:
                 s_p = pd.to_numeric(df_clean['PENDIENTES'], errors='coerce').fillna(0)
                 tot_pend_s = s_p[s_p > 0].sum()
                 
            pct_av = (tot_ejec_s / tot_prog_s * 100) if tot_prog_s > 0 else 0
            
            # Gráfico Donut Compacto
            source_bal = pd.DataFrame({
                "Estado": ["Ejecutadas", "Pendientes"],
                "Valor": [tot_ejec_s, tot_pend_s],
                "Color": ["#2E8B57", "#E0E0E0"]
            })
            
            base_b = alt.Chart(source_bal).encode(
                theta=alt.Theta("Valor", stack=True)
            )
            pie_b = base_b.mark_arc(innerRadius=60, outerRadius=85).encode(
                color=alt.Color("Estado", scale=alt.Scale(domain=["Ejecutadas", "Pendientes"], range=["#2E8B57", "#E0E0E0"]), legend=None),
                tooltip=["Estado", "Valor"]
            )
            text_p = base_b.mark_text(radius=0, size=20, fontStyle="bold", color="#2E8B57").encode(
                text=alt.value(f"{pct_av:.0f}%")
            )
            st.altair_chart((pie_b + text_p).properties(height=250), use_container_width=True)
            
            # Métricas Centradas y Estilizadas (HTML/CSS)
            st.markdown(f"""
            <div style="display: flex; justify-content: center; gap: 20px; text-align: center; margin-top: -10px;">
                <div>
                    <span style="font-size: 14px; color: #555;">Programado</span><br>
                    <span style="font-size: 20px; font-weight: bold; color: #333;">{int(tot_prog_s)}</span>
                </div>
                <div style="border-left: 1px solid #ddd; height: 30px; margin-top: 5px;"></div>
                <div>
                    <span style="font-size: 14px; color: #555;">Pendientes</span><br>
                    <span style="font-size: 20px; font-weight: bold; color: #FF4B4B;">{int(tot_pend_s)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.subheader("📋 Estado Pacientes")
            if 'ESTADO' in df_clean.columns:
                df_st_valid = df_clean[df_clean['ESTADO'].notna() & (df_clean['ESTADO'] != '')]
                
                total_counts = df_st_valid['ESTADO'].value_counts().reset_index()
                total_counts.columns = ['Estado', 'Total Terapias']
                
                col_id = 'DNI' if 'DNI' in df_clean.columns else 'PACIENTES'
                unique_counts = df_st_valid.groupby('ESTADO')[col_id].nunique().reset_index()
                unique_counts.columns = ['Estado', 'Pacientes Únicos']
                final_stats = pd.merge(total_counts, unique_counts, on='Estado')
                
                base_st = alt.Chart(final_stats).encode(
                    x=alt.X('Total Terapias', title='Total'),
                    y=alt.Y('Estado', sort='-x', title=''),
                    tooltip=['Estado', 'Total Terapias', 'Pacientes Únicos']
                )
                bars_st = base_st.mark_bar(color="#FF4B4B")
                text_st = base_st.mark_text(align='left', dx=3, color='black').encode(text='Total Terapias')
                
                st.altair_chart((bars_st + text_st).properties(height=350), use_container_width=True)
                
                missing_st = df_clean[df_clean['PACIENTES'].notna() & (df_clean['ESTADO'].isna() | (df_clean['ESTADO'] == ''))].shape[0]
                if missing_st > 0:
                    st.warning(f"⚠️ Atención: Hay {missing_st} filas con Estado vacío.")
            else:
                 st.warning("Columna ESTADO no encontrada")
        
        st.divider()
        
        # --- 3. GEOGRAFÍA ---
        st.subheader("🗺️ Distribución por Distritos")
        if 'DISTRITO' in df_clean.columns:
             dist_data = df_clean['DISTRITO'].value_counts().reset_index()
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
        st.header("🔍 Buscador Avanzado")
        
        # --- FILTRO POR ESTADO (NUEVO) ---
        # 1. Obtener lista de estados únicos (USANDO df_clean)
        lista_estados = ["Todos"] + sorted(df_clean['ESTADO'].astype(str).unique().tolist())
        
        estado_filtro = st.selectbox(
            "📂 Filtrar por Estado (Opcional):",
            lista_estados,
            index=0,
            key="filtro_estado_global"
        )
        
        # 2. Filtrar lista de pacientes según el estado elegido (USANDO df_clean)
        if estado_filtro != "Todos":
            df_search = df_clean[df_clean['ESTADO'].astype(str) == estado_filtro]
        else:
            df_search = df_clean
            
        # Selector de pacientes sorted (filtrado)
        pacientes_lista = df_search['PACIENTES'].dropna().unique().tolist()
        pacientes_lista.sort()
        
        # Mostrar conteo detallado
        total_rows = len(df_search)
        st.caption(f"🔎 Resultado: {len(pacientes_lista)} Pacientes únicos | {total_rows} Terapias encontradas (Estado: {estado_filtro})")
        
        paciente_seleccionado = st.selectbox(
            "Escribe o selecciona un paciente:", 
            pacientes_lista, 
            index=None, 
            placeholder="Buscar paciente...",
            key="selector_paciente_principal" # key estable
        )
        
        if paciente_seleccionado:
            # 1. Encontrar todas las filas de este paciente (USANDO df_clean para respetar filtros)
            p_rows = df_clean[df_clean['PACIENTES'] == paciente_seleccionado].copy()
            
            # 2. Construir lista de opciones únicas (Combina Especialidad + Fecha OM)
            opciones_tratamiento = []
            
            # Map index to display label
            index_map = {} 
            
            for idx, row in p_rows.iterrows():
                esp = row['ESPECIALIDAD']
                f_om = row.get('FECHA OM', 'Sin Fecha')
                
                if isinstance(f_om, datetime.datetime):
                    f_om_str = f_om.strftime('%d/%m/%Y')
                else:
                    f_om_str = str(f_om)
                    
                label = f"{esp} (Inicio: {f_om_str})"
                
                # Check duplication
                original_label = label
                counter = 2
                while label in index_map:
                    label = f"{original_label} ({counter})"
                    counter += 1
                
                opciones_tratamiento.append(label)
                index_map[label] = idx
            
            # Use columns as fake pills so user can click
            tratamiento_sel = st.selectbox(
                "Selecciona la Terapia específica:", 
                opciones_tratamiento,
                key="selector_terapia_detalle" # key estable
            )
            
            p_data = None
            if tratamiento_sel:
                # Recuperar la fila exacta usando el índice
                real_idx = index_map[tratamiento_sel]
                p_data = df.loc[real_idx]
            
            if p_data is not None:
                # --- TARJETA DE PACIENTE ---
                st.markdown(f"### 👤 {paciente_seleccionado}")
                st.caption(f"Visualizando: {tratamiento_sel}")
                
                # Debug info
                with st.expander("📋 Ver Datos Crudos (Para revisión)"):
                    st.write("Esto es exactamente lo que se lee del Excel:")
                    st.json(p_data.to_dict())

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.info(f"**DNI:** {p_data.get('DNI', 'N/A')}")
                    st.write(f"**Teléfono:** {p_data.get('TLF', 'N/A')}")
                    
                with c2:
                    st.info(f"**Programa:** {p_data.get('PROGRAMAS', 'N/A')}")
                    
                    # FECHA OM formatting
                    fecha_om = p_data.get('FECHA OM', 'N/A')
                    if isinstance(fecha_om, datetime.datetime):
                        fecha_om = fecha_om.strftime('%d/%m/%Y')
                    st.write(f"**Inicio Terapia:** {fecha_om}")
                    
                with c3:
                    # LÓGICA DE ESTADO INTELIGENTE
                    raw_estado = p_data.get('ESTADO', 'N/A')
                    
                    # Protección contra "N" o estados corruptos
                    if isinstance(raw_estado, str) and len(raw_estado) < 2:
                        raw_estado = "DESCONOCIDO (Dato corrupto)"
                        
                    val_pend = p_data.get('PENDIENTES', 0)
                    if pd.isna(val_pend): val_pend = 0
                    val_pend = int(val_pend)
                    
                    # Si dice Finalizado pero hay pendientes, es un error del excel
                    estado_final = raw_estado
                    if raw_estado == "FINALIZADO" and val_pend > 0:
                        estado_final = "⚠️ PENDIENTE (Corregido)"
                        st.warning(f"Estado Excel: {raw_estado} | Realidad: Faltan {val_pend}")
                    elif raw_estado == "PENDIENTE":
                        st.warning(f"Estado: {raw_estado}")
                    else:
                        st.success(f"Estado: {estado_final}")
                    
                    # CANTIDAD Y PENDIENTES
                    val_cant = p_data.get('CANT.', 0)
                    if pd.isna(val_cant): val_cant = 0
                    if pd.isna(val_cant): val_cant = 0
                    
                    st.write(f"**Progreso:** {int(val_cant) - int(val_pend)}/{int(val_cant)}")
                    st.caption(f"Total: {int(val_cant)} | Pend: {int(val_pend)}")
                    
                st.divider()
                
                # --- LÍNEA DE TIEMPO (GRÁFICA) ---
                st.subheader("📅 Cronograma de Asistencia")
                
                timeline_data = []
                for i in range(1, 21):
                    # CONVERTIR A STRING PORQUE LAS COLUMNAS SON strings "1", "2"...
                    col_name = str(i)
                    
                    if col_name in p_data and pd.notna(p_data[col_name]):
                         val = p_data[col_name]
                         
                         fecha_obj = None
                         
                         if isinstance(val, datetime.datetime):
                             fecha_obj = val
                         else:
                             # Intentar parsear si es texto
                             try:
                                 fecha_obj = pd.to_datetime(val, dayfirst=True, errors='coerce')
                                 if pd.isna(fecha_obj): fecha_obj = None
                             except:
                                 pass
                                 
                         if fecha_obj:
                             timeline_data.append({
                                 "Sesión": f"S{i}",
                                 "Fecha": fecha_obj,
                                 "FechaStr": fecha_obj.strftime('%d/%m/%Y'),
                                 "Tipo": "Asistió"
                             })
                
                if timeline_data:
                    df_timeline = pd.DataFrame(timeline_data)
                    
                    # Gráfica de puntos/barras en el tiempo
                    # Error handling: 'Tipo' seems to fail, removing color mapped by column 
                    # and using simple static color or default
                    st.scatter_chart(
                        df_timeline,
                        x="Fecha",
                        y="Sesión",
                        size=100
                    )
                    
                    # Mostrar última fecha grande
                    ultima_fecha = df_timeline['Fecha'].max().strftime('%d/%m/%Y')
                    st.success(f"✅ **Última asistencia registrada:** {ultima_fecha}")
                    
                     # Tabla detallada
                    with st.expander("Ver Fechas Detalladas"):
                        st.dataframe(df_timeline[['Sesión', 'FechaStr']])
                else:
                    st.warning("⚠️ No se encontraron fechas válidas en las columnas de sesiones (1-20).")

    with tab_main:
        st.caption(f"Fuente de datos: {data_source}")
        st.info("� Modo Lectura: La edición está desactivada en la versión pública.")
        
        # Tabla de solo lectura
        st.dataframe(df, use_container_width=True)

    
    with tab_downloads:
        st.header("📥 Descarga de Reporte Detallado")
        st.info("Este reporte desglosa cada sesión en una fila individual (Formato Vertical).")
        
        # Lógica de "Explosión" (Unpivot/Melt inteligente)
        if st.button("🚀 Generar Reporte Detallado"):
            with st.spinner("Procesando todas las sesiones..."):
                exploded_data = []
                
                # Iterar por cada orden de terapia
                for idx, row in df.iterrows():
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