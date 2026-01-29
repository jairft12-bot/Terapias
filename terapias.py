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
            header {display: none !important;}
            footer {display: none !important;}
            .stDeployButton {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            [data-testid="stDecoration"] {display: none !important;}
            [data-testid="stHeader"] {display: none !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("📊 Visor de Terapias")

# URL PROPORCIONADA POR EL USUARIO (Nueva Versión)
# Appending &download=1 to force binary download from the sharing link
DATA_URL = "https://viva1aips-my.sharepoint.com/:x:/g/personal/gestorprocesos_viva1a_com_pe/IQBVCUVP2PrvRowbT35kUsq-AbGX0ndr7O2WukwjN-ucA0w?e=cPdRMs&download=1"
SHEET_NAME = "Seguimiento de terapias "
LOCAL_PATH = "data.xlsx"



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
    st.session_state.df_cache, _, _, _ = load_data(st.session_state.last_refresh)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # BOTÓN RECARGAR (Visible siempre, pero destacado)
    if st.button("🔄 RECARGAR AHORA", use_container_width=True):
        st.cache_data.clear()
        st.session_state.df_cache, error, ts, source = load_data(time.time())
        st.session_state.last_refresh = time.time()
        st.rerun()
        
    st.divider()
    
    # CONTROLES SOLO VISIBLES EN LOCAL
    enable_autorefresh = False # Default en nube: No auto-refresh agresivo UI
    if IS_LOCAL:
        st.caption("🛠️ Modo Local Activo")
        # Auto-refresh logic
        enable_autorefresh = st.checkbox("✅ Auto-escaneo activo", value=True)
        if enable_autorefresh:
            refresh_interval = st.select_slider(
                "Frecuencia (segundos):",
                options=[90, 120, 180, 240, 300, 600],
                value=90
            )
            # Solo ejecutamos el sleep/rerun si está habilitado
            if enable_autorefresh:
                 # Pequeña lógica de rerun (simplificada para no bloquear)
                 pass

# Carga de datos real
df, error, hora_lectura, data_source = load_data(st.session_state.last_refresh)

# Área Principal - Indicadores
# Solo mostramos la fuente de datos si estamos en local o si hay error
if error or IS_LOCAL:
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

if df is not None:
    # Definir 4 pestañas explícitamente para evitar errores
    tab_dashboard, tab_search, tab_main, tab_downloads = st.tabs([
        "📊 Dashboard ", 
        "🔍 Buscador de Pacientes", 
        "📋 Tabla Principal", 
        "📥 Descargas"
    ])
    
    with tab_dashboard:
        st.caption(f"Visualizando datos de: {data_source} | Actualizado: {hora_lectura}")
        
        # --- 1. KPIS (TARJETAS) ---
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        # KPI 1: Total Pacientes (Únicos)
        # Intentamos buscar la columna DNI de forma segura
        col_dni = 'DNI' if 'DNI' in df.columns else 'DNI '
        if col_dni not in df.columns:
             # Fallback: primera columna? No, mejor no arriesgar
             st.error(f"No encuentro la columna DNI. Columnas: {list(df.columns)}")
             total_pacientes = 0
        else:
             total_pacientes = df[col_dni].nunique()
             
        kpi1.metric("Pacientes Únicos", total_pacientes)
        
        # KPI Extra: Total Registros (Filas válidas)
        # Contamos solo si la columna PACIENTES tiene dato
        # Esto filtra filas vacías del final de excel
        total_filas = df['PACIENTES'].dropna().count() if 'PACIENTES' in df.columns else len(df)
        kpi2.metric("Terapias Ordenadas", total_filas, help="Número de terapias registradas (excluye filas vacías)")

        # KPI 3, 4, 5: Desglose de Estados
        try:
            df_kpi_valid = df[df['PACIENTES'].notna() & (df['PACIENTES'] != '')]
            total_validas = len(df_kpi_valid)
            
            # Buscar columna ESTADO flexiblemente
            col_estado_found = None
            for c in df.columns:
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
                    "Gestión Realizada", 
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
                # Solicitud: Primero % y abajo el número total
                
                total_sesiones_saldo = 0
                count_negativos = 0
                
                if 'PENDIENTES' in df.columns:
                     s_pend_col = pd.to_numeric(df['PENDIENTES'], errors='coerce').fillna(0)
                     # Saldo pendiente real (positivo)
                     total_sesiones_saldo = int(s_pend_col[s_pend_col > 0].sum())
                     count_negativos = int(s_pend_col[s_pend_col < 0].count())
                
                col_cant = 'CANT.' if 'CANT.' in df.columns else 'CANT'
                total_programado_kpi = 0
                if col_cant in df.columns:
                     total_programado_kpi = pd.to_numeric(df[col_cant], errors='coerce').fillna(0).sum()
                
                # CÁLCULO DE EJECUTADAS
                total_ejecutadas_kpi = total_programado_kpi - total_sesiones_saldo
                tasa_ejecucion = (total_ejecutadas_kpi / total_programado_kpi * 100) if total_programado_kpi > 0 else 0
                
                kpi5.metric(
                    "Sesiones Realizadas",
                    f"{tasa_ejecucion:.1f}%",
                    f"{total_ejecutadas_kpi} Ejecutadas",
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
            if 'ESPECIALIDAD' in df.columns:
                # 1. Preparar datos limpios
                df_sp = df[df['ESPECIALIDAD'].notna() & (df['ESPECIALIDAD'] != '')]
                
                # 2. Calcular estadisticas
                col_id = 'DNI' if 'DNI' in df.columns else 'PACIENTES'
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
                
                missing_sp = df[df['PACIENTES'].notna() & (df['ESPECIALIDAD'].isna() | (df['ESPECIALIDAD'] == ''))].shape[0]
                if missing_sp > 0:
                    st.warning(f"⚠️ Atención: Hay {missing_sp} filas con Especialidad vacía (No salen en la gráfica).")
            else:
                st.warning("Columna ESPECIALIDAD no encontrada")
                
        with c2:
            st.subheader("⏳ Sesiones de Terapia")
            
            # --- Lógica del Donut (Traída aquí) ---
            tot_prog_s = 0
            tot_pend_s = 0
            
            c_cant = 'CANT.' if 'CANT.' in df.columns else 'CANT'
            if c_cant in df.columns:
                 tot_prog_s = pd.to_numeric(df[c_cant], errors='coerce').fillna(0).sum()
            if 'PENDIENTES' in df.columns:
                 s_p = pd.to_numeric(df['PENDIENTES'], errors='coerce').fillna(0)
                 tot_pend_s = s_p[s_p > 0].sum()
            
            tot_ejec_s = tot_prog_s - tot_pend_s
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
            if 'ESTADO' in df.columns:
                df_st_valid = df[df['ESTADO'].notna() & (df['ESTADO'] != '')]
                
                total_counts = df_st_valid['ESTADO'].value_counts().reset_index()
                total_counts.columns = ['Estado', 'Total Terapias']
                
                col_id = 'DNI' if 'DNI' in df.columns else 'PACIENTES'
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
                
                missing_st = df[df['PACIENTES'].notna() & (df['ESTADO'].isna() | (df['ESTADO'] == ''))].shape[0]
                if missing_st > 0:
                    st.warning(f"⚠️ Atención: Hay {missing_st} filas con Estado vacío.")
            else:
                 st.warning("Columna ESTADO no encontrada")
        
        st.divider()
        
        # --- 3. GEOGRAFÍA ---
        st.subheader("🗺️ Mapa de Calor: Distritos")
        if 'DISTRITO' in df.columns:
             dist_data = df['DISTRITO'].value_counts().reset_index()
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
        # 1. Obtener lista de estados únicos
        lista_estados = ["Todos"] + sorted(df['ESTADO'].astype(str).unique().tolist())
        
        estado_filtro = st.selectbox(
            "📂 Filtrar por Estado (Opcional):",
            lista_estados,
            index=0,
            key="filtro_estado_global"
        )
        
        # 2. Filtrar lista de pacientes según el estado elegido
        if estado_filtro != "Todos":
            df_search = df[df['ESTADO'].astype(str) == estado_filtro]
        else:
            df_search = df
            
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
            # 1. Encontrar todas las filas de este paciente
            p_rows = df[df['PACIENTES'] == paciente_seleccionado].copy()
            
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