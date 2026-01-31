
import streamlit as st
import pandas as pd
import os
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import unidecode
import ssl
import certifi

# SSL Context Hack para entornos locales sin certificados completos
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

# Contexto para geocodificación (Mejora resultados)
DEFAULT_CITY_COUNTRY = ", Lima, Peru"
CACHE_FILE = "coordenadas_cache.csv"

# Coordenadas Fijas de Distritos de Lima (Para evitar errores de API/SSL)
LIMA_DISTRICTS = {
    "ANCON": (-11.773, -77.146),
    "ATE": (-12.025, -76.918),
    "BARRANCO": (-12.149, -77.021),
    "BREÑA": (-12.056, -77.054),
    "CARABAYLLO": (-11.890, -77.029),
    "CHACLACAYO": (-11.973, -76.766),
    "CHORRILLOS": (-12.179, -77.006),
    "CIENEGUILLA": (-12.113, -76.712),
    "COMAS": (-11.936, -77.049),
    "EL AGUSTINO": (-12.043, -76.992),
    "INDEPENDENCIA": (-11.996, -77.054),
    "JESUS MARIA": (-12.074, -77.049),
    "LA MOLINA": (-12.079, -76.918),
    "LA VICTORIA": (-12.083, -77.017),
    "LIMA": (-12.046, -77.043),
    "LINCE": (-12.086, -77.034),
    "LOS OLIVOS": (-11.967, -77.070),
    "LURIGANCHO": (-11.971, -76.702),
    "LURIN": (-12.274, -76.865),
    "MAGDALENA DEL MAR": (-12.091, -77.069),
    "MIRAFLORES": (-12.111, -77.031),
    "PACHACAMAC": (-12.228, -76.860),
    "PUCUSANA": (-12.480, -76.797),
    "PUEBLO LIBRE": (-12.076, -77.062),
    "PUENTE PIEDRA": (-11.866, -77.073),
    "PUNTA HERMOSA": (-12.333, -76.824),
    "PUNTA NEGRA": (-12.365, -76.795),
    "RIMAC": (-12.029, -77.027),
    "SAN BARTOLO": (-12.389, -76.782),
    "SAN BORJA": (-12.107, -77.003),
    "SAN ISIDRO": (-12.098, -77.035),
    "SAN JUAN DE LURIGANCHO": (-11.977, -77.009),
    "SAN JUAN DE MIRAFLORES": (-12.164, -76.964),
    "SAN LUIS": (-12.076, -76.995),
    "SAN MARTIN DE PORRES": (-11.990, -77.086),
    "SAN MIGUEL": (-12.084, -77.091),
    "SANTA ANITA": (-12.041, -76.953),
    "SANTA MARIA DEL MAR": (-12.407, -76.777),
    "SANTA ROSA": (-11.799, -77.165),
    "SANTIAGO DE SURCO": (-12.143, -76.993),
    "SURCO": (-12.143, -76.993), # Alias común
    "SURQUILLO": (-12.113, -77.012),
    "VILLA EL SALVADOR": (-12.213, -76.939),
    "VILLA MARIA DEL TRIUNFO": (-12.159, -76.924),
    "CALLAO": (-12.056, -77.118),
    "BELLAVISTA": (-12.062, -77.096),
    "CARMEN DE LA LEGUA": (-12.046, -77.088),
    "LA PERLA": (-12.066, -77.113),
    "LA PUNTA": (-12.072, -77.164),
    "VENTANILLA": (-11.874, -77.126)
}

@st.cache_resource
def get_geolocator():
    # User agent único para cumplir políticas de Nominatim
    # FIX SSL MAC: Contexto explícito
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return Nominatim(user_agent="terapias_visor_app_v1", ssl_context=ctx)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            return pd.read_csv(CACHE_FILE).set_index("DIRECCION")[["LAT", "LON"]].to_dict("index")
        except:
            return {}
    return {}

def save_cache(cache_dict):
    try:
        data = []
        for addr, coords in cache_dict.items():
            data.append({"DIRECCION": addr, "LAT": coords["LAT"], "LON": coords["LON"]})
        pd.DataFrame(data).to_csv(CACHE_FILE, index=False)
    except Exception as e:
        print(f"Error guardando caché: {e}")

import re

def clean_address(addr):
    """
    Limpia direcciones complejas cortando texto de referencia.
    Ej: "CALLE X 123 ALTURA DEL MERCADO..." -> "CALLE X 123"
    """
    if not addr or str(addr).upper() == "NAN":
        return None
        
    s = str(addr).strip().upper()
    
    # Palabras clave que indican referencia (corta todo lo que sigue)
    stop_words = [
        r"\s+ALT[\.\s]", r"\s+ALTURA\s", 
        r"\s+FTE[\.\s]", r"\s+FRENTE\s", 
        r"\s+ESQ[\.\s]", r"\s+ESQUINA\s",
        r"\s+REF[\.\s]", r"\s+REFERENCIA\s",
        r"\s+URB[\.\s]", r"\s+URBANIZACI[OÓ]N\s",
        r"\s+BARRIO\s", r"\s+CDRA[\.\s]", r"\s+CUADRA\s",
        r"\s+INTERIOR\s", r"\s+INT[\.\s]",
        r"\s+DPTO\s", r"\s+DEPARTAMENTO\s",
        r"\s+MZ\s", r"\s+MANZANA\s",
        r"\s+LOTE\s", r"\s+LT\s",
        r"\s+ESPALDA\s", r"\s+A LA ESPALDA\s", # Agregado a pedido
        r"\s+PUENTE\s", # Agregado a pedido
        r"\-", # A veces usan guion para separar referencia
        r"\(", # Paréntesis de referencia
    ]
    
    for pattern in stop_words:
        # Buscamos el patrón
        match = re.search(pattern, s)
        if match:
            # Cortamos el string justo antes del match
            candidate = s[:match.start()].strip()
            # Si nos quedamos con algo decente (> 3 chars), lo usamos
            # Bajamos limite a 3 por si es "AV A 123"
            if len(candidate) > 3:
                s = candidate
                break # Asumimos que el primer corte es el bueno
    
    return s

def geocode_batch(direcciones_dict, progress_bar=None):
    """
    Recibe un diccionario {Original_Address: Distrito} o una lista de tuplas.
    En este caso recibiremos: {Original_Address: Distrito}
    """
    geolocator = get_geolocator()
    cache = load_cache()
    updated = False
    
    results = {}
    
    total = len(direcciones_dict)
    
    # Convertimos a lista (Address, District)
    items = list(direcciones_dict.items())
    
    for i, (direccion, distrito) in enumerate(items):
        # Limpieza básica para cache key (original cleaned)
        raw_clean = str(direccion).strip().upper()
        
        # Limpieza inteligente para búsqueda
        smart_clean = clean_address(direccion)
        district_suffix = f", {distrito}" if distrito and str(distrito).upper() != "NAN" else ""
        
        # 0. Si está vacío, saltar
        if not smart_clean:
            continue
            
        if not smart_clean:
            continue
            
        # 1. Buscar en Caché (por la key original)
        if raw_clean in cache:
            results[raw_clean] = (cache[raw_clean]["LAT"], cache[raw_clean]["LON"])
        
        # 2. b) Buscar en Diccionario Estático (Distritos Lima)
        elif raw_clean in LIMA_DISTRICTS:
            lat, lon = LIMA_DISTRICTS[raw_clean]
            # Guardamos en caché también para consistencia
            cache[raw_clean] = {"LAT": lat, "LON": lon}
            results[raw_clean] = (lat, lon)
            updated = True
        
        else:
            # 3. Consultar API con SMART CLEAN + DISTRITO
            try:
                # Intento 1: Dirección + Distrito + Lima, Peru
                search_query = f"{smart_clean}{district_suffix}{DEFAULT_CITY_COUNTRY}"
                # st.write(f"Testing: {search_query}") # Debug
                
                location = geolocator.geocode(search_query, timeout=10)
                
                if location:
                    lat, lon = location.latitude, location.longitude
                    cache[raw_clean] = {"LAT": lat, "LON": lon}
                    results[raw_clean] = (lat, lon)
                    updated = True
                else:
                    # Intento 2: Sin Distrito (solo dirección + Peru)
                    location = geolocator.geocode(f"{smart_clean}, Peru", timeout=10)
                    if location:
                        lat, lon = location.latitude, location.longitude
                        cache[raw_clean] = {"LAT": lat, "LON": lon}
                        results[raw_clean] = (lat, lon)
                        updated = True
                    else:
                        cache[raw_clean] = {"LAT": None, "LON": None} 
            
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                # Solo warning suave, no bloqueante
                pass
            except Exception as e:
                # Capturamos SSL globalmente parcheado o errores raros
                print(f"Error geo: {e}")
                pass
            
            # Respetar rate limit
            time.sleep(1.1)
        
        # Actualizar barra
        if progress_bar:
            progress_bar.progress((i + 1) / total, text=f"Geocodificando {i+1}/{total}...")

    if updated:
        save_cache(cache)
        
    return results

def render_heatmap(df_main):
    st.header("🔥 Mapa de Densidad por Distrito")
    
    # 1. Identificar columnas clave (Distrito, Dirección, Paciente)
    col_dist = None
    col_dir = None
    for c in df_main.columns:
        cup = str(c).upper()
        if "DISTRITO" in cup: col_dist = c
        if "DIRECCION" in cup: col_dir = c
            
    if not col_dist:
        st.error("❌ No se encontró la columna 'DISTRITO'.")
        return

    # 2. Agrupar por Distrito (Pacientes Únicos)
    # Identificar columna paciente
    col_paciente = "PACIENTES"
    for c in df_main.columns:
        if "PACIENTE" in str(c).upper():
             col_paciente = c
             break
    
    # Normalizar Distrito para agrupar
    # Usamos una copia ligera para no afectar el df original
    df_temp = df_main[[col_dist, col_paciente]].copy()
    df_temp["DISTRITO_NORM"] = df_temp[col_dist].fillna("Desconocido").astype(str).str.strip().str.upper()
    
    # Contar PACIENTES ÚNICOS por distrito
    dist_counts = df_temp.groupby("DISTRITO_NORM")[col_paciente].nunique().sort_values(ascending=False)
    
    # Filtramos distritos validos (> 2 chars)
    valid_districts = [d for d in dist_counts.index if len(d) > 2 and d != "DESCONOCIDO"]
    
    total_unique = df_temp[col_paciente].nunique()
    
    col1, col2 = st.columns([1,3])
    with col1:
        st.info(f"📍 **{len(valid_districts)}** Distritos | 👤 **{total_unique}** Pacientes\n\n" + 
                "\n".join([f"- {d}: {dist_counts[d]}" for d in valid_districts[:5]]) + 
                (f"\n... y {len(valid_districts)-5} más." if len(valid_districts)>5 else ""))
        
        # Boton "Actualizar Mapa"
        if st.button("🗺️ Actualizar Mapa (Por Distritos)"):
             st.session_state.coords_ready = False
             
             # Preparamos lista para geocodificar: {Distrito: Distrito} (hack para usar geocode_batch)
             # geocode_batch espera un dict o lista. Le pasamos {Distrito: None} para que busque "Distrito, Lima, Peru"
             # O mejor, {Distrito: Distrito} para que use district suffix logic si hiciera falta, pero mejor pasarlo como key.
             
             targets = {d: "" for d in valid_districts} # Distrito limpio como key, sin suffix extra
             
             my_bar = st.progress(0, text="Localizando distritos...")
             coords_map = geocode_batch(targets, progress_bar=my_bar)
             my_bar.empty()
             
             st.session_state.cached_coords_map = coords_map
             st.session_state.coords_ready = True
             st.rerun()

    if st.session_state.get('coords_ready', False):
        coords_map = st.session_state.cached_coords_map
        
        m = folium.Map(location=[-12.0464, -77.0428], zoom_start=11) # Lima Center
        
        found_any = False
        
        for distrito in valid_districts:
            count = dist_counts[distrito]
            
            # coords_map devuelve tuplas (lat, lon)
            if distrito in coords_map and coords_map[distrito]:
                lat, lon = coords_map[distrito]
                
                if lat is not None and lon is not None:
                    found_any = True
                    
                    # Círculo proporcional a la cantidad
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=5 + (count * 0.5), # Base 5px + 0.5px por paciente
                        popup=f"<b>{distrito}</b><br>Pacientes: {count}",
                        color="#3186cc",
                        fill=True,
                        fill_color="#3186cc",
                        fill_opacity=0.6
                    ).add_to(m)
                
                # Marcador simple con tooltip
                # folium.Marker([lat, lon], tooltip=f"{distrito}: {count}").add_to(m)
        
        if found_any:
            # Layout de 2 columnas: Mapa (izq) y Tabla (der)
            c_map, c_table = st.columns([1, 1])
            
            with c_map:
                # Titulo para alinear con la tabla
                st.subheader("🗺️ Vista Geográfica")
                st_folium(m, height=500, width=None) 
            
            with c_table:
                st.subheader("📋 Listado de Pacientes")
                
                # Identificar columnas extras solicitadas
                col_id = None
                col_prog = None
                col_esp = None
                
                for c in df_main.columns:
                    cup = str(c).upper()
                    if not col_id and any(x in cup for x in ["ID", "HISTORIA", "HC", "DNI"]): col_id = c
                    if not col_prog and "PROG" in cup: col_prog = c
                    if not col_esp and any(x in cup for x in ["ESP", "TERAPIA", "SERVICIO"]): col_esp = c
                
                cols_to_show = []
                if col_id: cols_to_show.append(col_id)
                if col_paciente: cols_to_show.append(col_paciente)
                if col_prog: cols_to_show.append(col_prog)
                if col_esp: cols_to_show.append(col_esp)
                if col_dir: cols_to_show.append(col_dir)
                if col_dist: cols_to_show.append(col_dist)
                
                if col_paciente:
                     df_table = df_main[cols_to_show].drop_duplicates(subset=[col_paciente]).copy()
                else:
                     df_table = df_main[cols_to_show].drop_duplicates()
                
                # Usar todo el ancho disponible en la columna
                st.dataframe(df_table, hide_index=True, height=500, use_container_width=True)
                
            # Mensaje de éxito ocupando todo el ancho (fuera de columnas)
            st.success("✅ Mapa actualizado por distritos.")
                
        else:
            st.warning("⚠️ No se pudieron geolocalizar los distritos. Verifica tu conexión.")
