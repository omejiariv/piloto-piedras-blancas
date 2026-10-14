import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
import requests
import io
import os
import re
from datetime import datetime

# ==========================================
# 0. MOTORES MATEMÁTICOS Y CACHÉ DE DATOS
# ==========================================
def calcular_penman_monteith(tmax, tmin, rh, u2, rs, elev, lat, dia, albedo=0.08):
    """Motor Termodinámico Nativo (Reemplaza a PyETo)"""
    lat_rad = math.radians(lat)
    t_media = (tmax + tmin) / 2.0
    P = 101.3 * ((293 - 0.0065 * elev) / 293) ** 5.26
    gamma = 0.000665 * P
    delta = 4098 * (0.6108 * math.exp((17.27 * t_media) / (t_media + 237.3))) / ((t_media + 237.3) ** 2)
    es_tmax = 0.6108 * math.exp((17.27 * tmax) / (tmax + 237.3))
    es_tmin = 0.6108 * math.exp((17.27 * tmin) / (tmin + 237.3))
    es = (es_tmax + es_tmin) / 2.0
    ea = es * (rh / 100.0) 
    vpd = es - ea
    rns = (1 - albedo) * rs
    sol_dec = 0.409 * math.sin(((2 * math.pi) / 365) * dia - 1.39)
    sha = math.acos(-math.tan(lat_rad) * math.tan(sol_dec))
    ird = 1 + 0.033 * math.cos(((2 * math.pi) / 365) * dia)
    ra = (24 * 60 / math.pi) * 0.0820 * ird * (sha * math.sin(lat_rad) * math.sin(sol_dec) + math.cos(lat_rad) * math.cos(sol_dec) * math.sin(sha))
    rso = (0.75 + 2e-5 * elev) * ra
    rs_rso = min(rs / rso, 1.0) if rso > 0 else 0.5
    rnl = 4.903e-9 * (((tmax + 273.16)**4 + (tmin + 273.16)**4) / 2) * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * rs_rso - 0.35)
    rn = rns - rnl
    term_rad = (0.408 * delta * rn) / (delta + gamma)
    term_aero = (gamma * 2.626 * (1 + 0.536 * u2) * vpd) / (delta + gamma)
    
    return term_rad, term_aero, term_rad + term_aero, vpd, rn, P

@st.cache_data
def cargar_datos_embalses():
    try:
        url = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/sihcli_maestros/Area%20Volumen%20embalses%20Antioquia.xlsx"
        response = requests.get(url, verify=False)
        df = pd.read_excel(io.BytesIO(response.content))
        if 'Altura Promedio Cota Máx (msnm)' in df.columns:
            df['Altura Promedio Cota Máx (msnm)'] = df['Altura Promedio Cota Máx (msnm)'].apply(
                lambda x: x * 1000 if pd.notnull(x) and x < 10 else x
            )
        return df
    except Exception as e:
        return pd.DataFrame()

df_embalses = cargar_datos_embalses()

# Mapeo de Coordenadas Base
coords_embalses = {
    "Guatapé (El Peñol)": (6.26, -75.16), "Hidroituango": (7.13, -75.67), 
    "Jaguas": (6.31, -75.02), "La Fe": (6.11, -75.50), "Piedras Blancas": (6.29, -75.49), 
    "Playas": (6.27, -74.95), "Porce II": (6.75, -75.15), "Porce III": (6.80, -75.10), 
    "Riogrande II": (6.55, -75.45), "San Carlos": (6.21, -74.85)
}

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y CABEZOTE
# ==========================================
st.set_page_config(page_title="Seguridad Hídrica Medellín", page_icon="💧", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card { background-color: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 10px; }
    .metric-title { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;}
    .metric-value { color: #38bdf8; font-size: 1.8rem; font-weight: 800; margin: 5px 0;}
    .metric-sub { color: #cbd5e1; font-size: 0.75rem;}
</style>
""", unsafe_allow_html=True)

# Logos Institucionales
col_l1, col_l2, col_l3, col_spc = st.columns([0.5, 0.5, 0.5, 3])
with col_l1: st.image("https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/CuencaVerdeLogo_V1.JPG", use_container_width=True)
with col_l2: st.image("https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_epm.png", use_container_width=True)
with col_l3: st.image("https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_distritoMedellin.png", use_container_width=True)

st.markdown("""
<div style="background: linear-gradient(90deg, #0f172a, #1e293b); padding: 25px; border-radius: 15px; border-left: 5px solid #38bdf8; margin-top: 0px; margin-bottom: 25px;">
    <h4 style="color: #38bdf8; margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">🛡️ Proyecto Piloto de Adaptación Hidroclimática Inmediata</h4>
    <h1 style="color: white; margin: 5px 0 10px 0; font-size: 2.5rem;">Blindaje Evaporativo del Embalse Piedras Blancas ante El Niño (2026-2027)</h1>
    <p style="color: #cbd5e1; font-size: 1.1rem; margin: 0;">Estrategia proactiva para cosechar las lluvias de <b>octubre y noviembre de 2026</b> y sellar la lámina de agua mediante tecnologías flotantes, mitigando el riesgo de desabastecimiento en <b>diciembre de 2026 y el 1T de 2027</b>.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.markdown('<div class="metric-card"><div class="metric-title">Sistema Objetivo</div><div class="metric-value" style="color: white; font-size: 1.2rem;">Embalse Piedras Blancas</div><div class="metric-sub text-sky-400">Coord: 6.29° N, -75.49° W</div></div>', unsafe_allow_html=True)
c2.markdown('<div class="metric-card"><div class="metric-title">Capacidad de Reserva</div><div class="metric-value" style="color: #fbbf24;">0.50 Millones de m³</div><div class="metric-sub">Acueducto EPM (Oriente Medellín)</div></div>', unsafe_allow_html=True)
c3.markdown('<div class="metric-card"><div class="metric-title">Variable de Intervención</div><div class="metric-value" style="color: #34d399;">Control Evaporativo</div><div class="metric-sub">Impacto inmediato (50% - 85%)</div></div>', unsafe_allow_html=True)
c4.markdown('<div class="metric-card"><div class="metric-title">Ventana de Ejecución</div><div class="metric-value" style="color: #fb7185;">Oct - Nov 2026</div><div class="metric-sub">Previo al estiaje Dic 26 - Mar 27</div></div>', unsafe_allow_html=True)
st.write("")

# ==========================================
# 2. MEGA-NAVEGACIÓN (8 PESTAÑAS)
# ==========================================
tabs = st.tabs([
    "🌍 1. Diagnóstico", 
    "🔄 2. Ciclo Hidrológico", 
    "🔬 3. Física Evaporativa", 
    "💡 4. Tecnologías y Valor", 
    "📊 5. Base Maestra y Mapas", 
    "🎛️ 6. Simulador Piloto",
    "📡 7. Telemetría XM",
    "🚀 8. Ruta Crítica"
])

# -----------------------------------------
# TAB 1: DIAGNÓSTICO
# -----------------------------------------
with tabs[0]:
    st.header("Contexto Socio-Hidroclimático: La Vulnerabilidad de Piedras Blancas")
    col_diag1, col_diag2 = st.columns([1.2, 1])
    
    with col_diag1:
        st.subheader("Asimetría en el Sistema de Reservas (EPM)")
        st.markdown("A diferencia de los grandes embalses interconectados, **Piedras Blancas (0.5 Mm³)** abastece el oriente alto de Medellín y opera con un margen milimétrico.")
        df_vol = pd.DataFrame({"Embalse": ["Río Grande II", "La Fe", "Piedras Blancas"], "Volumen (Mm³)": [138.8, 11.1, 0.5], "Color": ["#38bdf8", "#34d399", "#fbbf24"]})
        fig_vol = px.bar(df_vol, y="Embalse", x="Volumen (Mm³)", text="Volumen (Mm³)", orientation='h')
        fig_vol.update_traces(marker_color=df_vol["Color"], textposition='outside')
        fig_vol.update_layout(height=220, margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(type='log', title="Volumen (Escala Logarítmica)"))
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_diag2:
        st.error("☀️ **1. Pérdida de la 'Manta Natural' bajo El Niño**\n\nUbicado a ~2,350 msnm. Con El Niño, se rompe la cobertura nubosa, aumentando la radiación solar (+15%), la temperatura y la 'sed' atmosférica.")
        st.warning("📐 **2. Efecto 'Bandeja'**\n\nSu ratio morfológico es muy bajo (≈ 0.025 Mm³/ha). Expone demasiada superficie térmica por cada metro cúbico almacenado.")
        st.info("🦠 **3. Riesgo de Eutrofización**\n\nEn el 1T 2027 aumenta la demanda, mientras que la radiación acelera la floración de cianobacterias que encarecen la potabilización.")

# -----------------------------------------
# TAB 2: CICLO HIDROLÓGICO
# -----------------------------------------
with tabs[1]:
    st.header("Gobernabilidad Real de las Variables del Ciclo")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.error("🌧️ 1. Precipitación (P) | CONTROL: ~0%")
        st.markdown("* **Mecanismo:** Fenómenos macroclimáticos.\n* **Maniobra:** Nula. No podemos hacer llover.\n* **Estrategia:** Retener al máximo las lluvias actuales.")
    with c2:
        st.warning("🌲 2. Caudales Base (Qb) | CONTROL: LARGO PLAZO")
        st.markdown("* **Mecanismo:** Recarga de bosques y suelos.\n* **Maniobra:** SbN y reforestación.\n* **Límite:** Toma de 5 a 15 años. No salva la crisis 2027.")
    with c3:
        st.success("☀️ 3. Evaporación (E) | CONTROL: INMEDIATO (85%)")
        st.markdown("* **Mecanismo:** Escape en el espejo de agua libre.\n* **Maniobra:** Directa. Aislar la interfaz agua-aire.\n* **Decisión:** Única palanca de ingeniería que responde en semanas.")

# -----------------------------------------
# TAB 3: FÍSICA EVAPORATIVA (LABORATORIO PyETo/Nativo)
# -----------------------------------------
with tabs[2]:
    st.header("Simulador Termodinámico: Ecuación de Penman-Monteith (Agua Libre)")
    st.markdown("Desde la perspectiva hidrológica, mientras que el flujo superficial es impulsado por la gravedad, la evaporación es traccionada por la **radiación solar** y el **déficit de presión de vapor (VPD)**.")
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        st.info("⚙️ **Parámetros Atmosféricos**")
        altitud = st.number_input("Altitud (msnm)", value=2350.0, step=50.0)
        latitud = st.number_input("Latitud (°)", value=6.29, step=0.1)
        dia_ano = st.slider("Día del año", min_value=1, max_value=365, value=345) # Diciembre
        t_max = st.slider("Temp. Máxima (°C)", 15.0, 40.0, 23.5)
        t_min = st.slider("Temp. Mínima (°C)", 5.0, 25.0, 11.5)
        rh_media = st.slider("Humedad Relativa (%)", 30.0, 100.0, 65.0)
        viento_2m = st.slider("Viento a 2m (m/s)", 0.0, 10.0, 2.8)
        rs = st.slider("Radiación Solar (MJ/m²/día)", 5.0, 30.0, 20.5)
        albedo_agua = st.number_input("Albedo del Agua", value=0.08, step=0.01, format="%.2f")

    with col_f2:
        # Cálculo Termodinámico Integrado
        t_rad, t_aero, e_total, vpd_val, rn_val, patm = calcular_penman_monteith(
            t_max, t_min, rh_media, viento_2m, rs, altitud, latitud, dia_ano, albedo_agua
        )
        
        st.subheader(f"Tasa de Evaporación Estimada: {e_total:.2f} mm/día")
        
        c_graf, c_met = st.columns([1.5, 1])
        with c_graf:
            fig_p = go.Figure(data=[go.Pie(
                labels=['Motor Radiativo (Solar)', 'Motor Aerodinámico (Viento/VPD)'],
                values=[max(0, t_rad), max(0, t_aero)], hole=.4, marker_colors=['#fbbf24', '#38bdf8']
            )])
            fig_p.update_layout(margin=dict(t=10, b=10, l=0, r=0), height=300, showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_p, use_container_width=True)
            
        with c_met:
            st.metric(label="Déficit de Presión de Vapor (VPD)", value=f"{vpd_val:.2f} kPa")
            st.metric(label="Radiación Neta (Rn)", value=f"{rn_val:.2f} MJ/m²/día")
            st.metric(label="Presión Atmosférica", value=f"{patm:.1f} kPa")

# -----------------------------------------
# TAB 4: TECNOLOGÍAS Y FOTOS
# -----------------------------------------
with tabs[3]:
    st.header("Intervenciones Físicas y Tecnológicas")
    st.markdown("Soluciones de ingeniería implementadas globalmente para reducir el estrés hídrico.")
    
    col_mtx, col_gal = st.columns([1.5, 1])
    with col_mtx:
        st.subheader("Matriz Tecnológica de Mitigación")
        df_tech = pd.DataFrame({
            "Tecnología": ["☀️ Solares Flotantes (FPV)", "⬡ Módulos Hexagonales", "🌑 Esferas de Sombra", "🧪 Monocapas Químicas"],
            "Reducción Evap.": ["60% - 70%", "80% - 90%", "80% - 85%", "15% - 30%"],
            "Costo": ["Alto (Inversión)", "Medio-Alto", "Medio", "Bajo (Operativo)"],
            "Caso de Éxito": ["Sirindhorn, Tailandia", "Acueductos", "Los Ángeles, EE.UU.", "Represas Agrícolas"]
        })
        st.dataframe(df_tech, use_container_width=True, hide_index=True)
        st.info("💡 **Sinergia Agua-Energía:** Los sistemas FPV no solo reducen la evaporación, sino que el cuerpo de agua enfría los paneles, aumentando su eficiencia fotovoltaica entre un 5% y 10%.")
    
    with col_gal:
        st.subheader("📸 Referencia Visual")
        try:
            ruta_fotos = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'Fotos'))
            if os.path.exists(ruta_fotos) and len(os.listdir(ruta_fotos)) > 0:
                archivos = [os.path.join(ruta_fotos, f) for f in os.listdir(ruta_fotos) if f.endswith(('.png', '.jpg', '.jpeg'))]
                if archivos:
                    st.image(archivos[0], use_container_width=True, caption="Tecnología Flotante")
            else:
                st.warning("Agrega fotos a la carpeta 'data/Fotos' en tu repositorio GitHub para visualizar la galería.")
        except Exception:
            st.caption("Galería visual no disponible en el despliegue actual.")

# -----------------------------------------
# TAB 5: BASE MAESTRA Y MAPA
# -----------------------------------------
with tabs[4]:
    st.header("Base Batimétrica y Explorador Satelital de Antioquia")
    col_df, col_map = st.columns([1, 1.2])
    
    with col_df:
        st.markdown("#### 📋 Matriz de Datos Crudos")
        if not df_embalses.empty:
            st.dataframe(df_embalses.astype(str), use_container_width=True, hide_index=True, height=350)
            st.info("💡 **Relación Volumen/Área:** Piedras Blancas y La Fe poseen morfologías expansivas que exponen gran superficie en relación a su volumen útil.")
        else:
            st.warning("Conectando a base de datos de Supabase...")

    with col_map:
        st.markdown("#### 🗺️ Ubicación Espacial")
        try:
            import folium
            import streamlit.components.v1 as components
            m = folium.Map(location=[6.5, -75.3], zoom_start=9)
            tile_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            folium.TileLayer(tiles=tile_url, attr='Esri', name='Satélite', overlay=False).add_to(m)
            
            if not df_embalses.empty:
                for _, row in df_embalses.iterrows():
                    nombre = row['Embalse']
                    if nombre in coords_embalses:
                        lat, lon = coords_embalses[nombre]
                        folium.Marker(
                            [lat, lon], 
                            tooltip=folium.Tooltip(nombre, permanent=True, direction='right', style="font-size: 11px; background-color: rgba(255,255,255,0.8);")
                        ).add_to(m)
            components.html(m._repr_html_(), height=400)
        except Exception as e:
            st.warning("Instala 'folium' en tu requirements.txt para habilitar el mapa interactivo.")

# -----------------------------------------
# TAB 6: SIMULADOR DEL PILOTO FINANCIERO
# -----------------------------------------
with tabs[5]:
    st.header("🎛️ Simulador Ejecutivo: Proyecto Piloto Piedras Blancas")
    
    c_s1, c_s2 = st.columns([1.2, 2])
    with c_s1:
        st.markdown("#### Parámetros de Intervención")
        area_ev = st.slider("Espejo de Agua Actual (ha):", 10.0, 28.0, 20.0, 1.0)
        pct_cb = st.slider("Cobertura del Piloto (%):", 10, 70, 40, 5)
        tech_sim = st.selectbox("Tecnología a evaluar:", ["⭐ Híbrido (50% FPV + 50% Hexa)", "☀️ 100% Paneles FPV", "⬡ 100% Módulos Hexagonales"])
        dias_crit = st.slider("Ventana Crítica (días):", 30, 180, 60, 15)
        consumo = st.slider("Dotación Neta (L/hab-día):", 50, 250, 50, 10)

    with c_s2:
        area_c = area_ev * (pct_cb / 100.0)
        ev_base = 4.35 # El Niño consolidado
        if "Híbrido" in tech_sim: ef_sim, mwp_s, cap_s, pay_s = 0.75, 0.625, 0.36, "3.8 Años"
        elif "Solares" in tech_sim: ef_sim, mwp_s, cap_s, pay_s = 0.65, 1.25, 0.56, "3.1 Años"
        else: ef_sim, mwp_s, cap_s, pay_s = 0.85, 0.0, 0.19, "7.5 Años"
            
        ahorro_m3_dia = (ev_base * area_ev * 10) * (pct_cb / 100.0) * ef_sim
        vol_salvado = ahorro_m3_dia * dias_crit
        habs = (ahorro_m3_dia * 60) / ((consumo / 1000.0) * dias_crit) # Lógica dinámica
        
        st.markdown("#### Impacto Físico y Financiero")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Agua Salvada", f"{vol_salvado:,.0f} m³", f"En {dias_crit} días")
        k2.metric("Abastecimiento", f"{habs:,.0f} Hab", f"Continuo a {consumo} L")
        k3.metric("Generación", f"{area_c*mwp_s:.1f} MWp", "Ley 1715" if mwp_s>0 else "Pasivo")
        k4.metric("CAPEX Est.", f"${area_c*cap_s:.2f}M USD", f"ROI: {pay_s}", delta_color="inverse")

# -----------------------------------------
# TAB 7: TELEMETRÍA XM
# -----------------------------------------
with tabs[6]:
    st.header("📡 Telemetría Operativa")
    st.markdown("Piedras Blancas y La Fe son embalses de uso exclusivo de acueducto y no reportan telemetría de energía a la base de datos de XM. Para conectar otros embalses de generación, se utiliza la API nativa de `pydataxm`.")
    if st.button("Probar Conexión PyDataXM (Embalse Guatapé)"):
        try:
            import datetime as dt
            from pydataxm import *
            api = pydataxm.ReadDB()
            df_cat = api.get_collections()
            if not df_cat.empty:
                st.success("✅ Conexión establecida con el servidor nacional de XM con éxito.")
        except Exception as e:
            st.error("Instala 'pydataxm' en tu archivo requirements.txt para habilitar esta función.")

# -----------------------------------------
# TAB 8: RUTA CRÍTICA
# -----------------------------------------
with tabs[7]:
    st.header("🚀 Ruta Crítica de Acción Proactiva")
    dias_fin_ano = (datetime(2026, 12, 31) - datetime.now()).days
    st.error(f"⚠️ **Sentido de Urgencia:** Quedan ~{max(0, dias_fin_ano)} días de lluvias antes del estiaje seco de fin de año. Si esperamos a febrero, el agua se habrá evaporado.")
    
    rt1, rt2, rt3, rt4 = st.columns(4)
    rt1.info("**PASO 1: Oct 2026**\n* Aprobación express (8 ha).\n* Regla de retención máxima.\n* Compra de módulos rápidos.")
    rt2.success("**PASO 2: Nov 2026**\n* Sellado temprano del espejo de agua al llegar a cota máxima.\n* Barreras de viento (Booms).")
    rt3.warning("**PASO 3: Dic 2026**\n* Defensa activa ante la alta radiación y vientos alisios.\n* Montaje FPV e interconexión.")
    rt4.error("**PASO 4: 1T 2027**\n* Superación del pico de El Niño sin racionamientos en Oriente.\n* Modelo listo para La Fe.")

st.markdown("---")
st.caption("Plataforma de Soporte a la Decisión Socio-Hidroclimática • Fondo de Agua CuencaVerde, EPM y Alcaldía de Medellín • 2026")
