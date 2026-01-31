
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

@st.cache_resource
def get_geolocator():
    # User agent único para cumplir políticas de Nominatim
    return Nominatim(user_agent="terapias_visor_app_v1")

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

def geocode_batch(direcciones, progress_bar=None):
    geolocator = get_geolocator()
    cache = load_cache()
    updated = False
    
    results = {}
    
    total = len(direcciones)
    for i, direccion in enumerate(direcciones):
        clean_addr = str(direccion).strip().upper()
        
        # 0. Si está vacío, saltar
        if not clean_addr or clean_addr == "NAN":
            continue

        # 1. Buscar en Caché
        if clean_addr in cache:
            results[clean_addr] = (cache[clean_addr]["LAT"], cache[clean_addr]["LON"])
        else:
            # 2. Consultar API
            try:
                # Intentar limpiar un poco y agregar contexto
                search_query = f"{clean_addr}{DEFAULT_CITY_COUNTRY}"
                location = geolocator.geocode(search_query, timeout=10)
                
                if location:
                    lat, lon = location.latitude, location.longitude
                    cache[clean_addr] = {"LAT": lat, "LON": lon}
                    results[clean_addr] = (lat, lon)
                    updated = True
                else:
                    # Intento 2: Sin "Lima" si falla (quizas tiene distrito explicito)
                    location = geolocator.geocode(f"{clean_addr}, Peru", timeout=10)
                    if location:
                        lat, lon = location.latitude, location.longitude
                        cache[clean_addr] = {"LAT": lat, "LON": lon}
                        results[clean_addr] = (lat, lon)
                        updated = True
                    else:
                        cache[clean_addr] = {"LAT": None, "LON": None} # Marcar como no encontrado para no reintentar siempre
            
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                st.warning(f"Error de conexión al geocodificar: {e}")
                time.sleep(2) # Pausa de seguridad
            
            # Respetar rate limit (1req/seg es politica de Nominatim)
            time.sleep(1.1)
        
        # Actualizar barra
        if progress_bar:
            progress_bar.progress((i + 1) / total, text=f"Geocodificando {i+1}/{total}: {clean_addr}")

    if updated:
        save_cache(cache)
        
    return results

def render_heatmap(df_main):
    st.header("🔥 Mapa de Calor de Pacientes")
    
    col_dir = None
    for c in df_main.columns:
        if "DIRECCION" in str(c).upper():
            col_dir = c
            break
            
    if not col_dir:
        st.error("❌ No se encontró una columna de 'DIRECCIÓN' en los datos.")
        return

    # Filtros únicos de dirección
    direcciones_unicas = df_main[col_dir].dropna().unique()
    
    if len(direcciones_unicas) == 0:
        st.warning("No hay direcciones para mostrar.")
        return

    # Botón para iniciar (porque es lento)
    if 'coords_ready' not in st.session_state:
        st.session_state.coords_ready = False

    col1, col2 = st.columns([1,3])
    with col1:
        st.info(f"📍 **{len(direcciones_unicas)}** direcciones únicas detectadas.")
        if st.button("🗺️ Generar/Actualizar Mapa"):
            st.session_state.coords_ready = False # Forzar reload
            
            # Barra progreso
            my_bar = st.progress(0, text="Iniciando geocodificación...")
            coords_map = geocode_batch(direcciones_unicas, progress_bar=my_bar)
            my_bar.empty()
            
            # Guardamos resultado en session para no recalcular en reruns simples
            st.session_state.cached_coords_map = coords_map
            st.session_state.coords_ready = True
            st.rerun()

    if st.session_state.get('coords_ready', False):
        coords_map = st.session_state.cached_coords_map
        
        # Preparar datos para Folium
        heat_data = [] # [Lat, Lon, Weight]
        marker_data = [] # [Lat, Lon, Popup]
        
        found_count = 0
        missing_count = 0
        
        for idx, row in df_main.iterrows():
            addr = str(row[col_dir]).strip().upper()
            if addr in coords_map and coords_map[addr] and coords_map[addr][0] is not None:
                lat, lon = coords_map[addr]
                heat_data.append([lat, lon, 1]) # Peso 1 por paciente
                
                # Datos para popup (Paciente)
                paciente = row['PACIENTES'] if 'PACIENTES' in df_main.columns else "Paciente"
                marker_data.append({'lat': lat, 'lon': lon, 'info': f"{paciente}: {addr}"})
                found_count += 1
            else:
                missing_count += 1

        # Métricas resultantes
        st.success(f"✅ Geolocalizados: {found_count} | ⚠️ No encontrados: {missing_count}")

        if heat_data:
            # Centro promedio
            avg_lat = sum([x[0] for x in heat_data]) / len(heat_data)
            avg_lon = sum([x[1] for x in heat_data]) / len(heat_data)
            
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
            
            # Capa de Calor
            HeatMap(heat_data, radius=15, blur=10).add_to(m)
            
            # Capa de Marcadores (Cluster) para ver detalles
            marker_cluster = MarkerCluster().add_to(m)
            for item in marker_data:
                folium.Marker(
                    location=[item['lat'], item['lon']],
                    popup=folium.Popup(item['info'], parse_html=True),
                    icon=folium.Icon(color="blue", icon="user")
                ).add_to(marker_cluster)

            st_folium(m, width=900, height=500)
        else:
            st.warning("No se pudieron obtener coordenadas válidas para generar el mapa.")
