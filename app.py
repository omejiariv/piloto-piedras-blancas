import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
import requests
import io
import os
from datetime import datetime

# ==========================================
# 0. MOTOR MATEMÁTICO Y EXTRACCIÓN DE DATOS
# ==========================================
def calcular_penman_monteith(tmax, tmin, rh, u2, rs, elev, lat, dia, albedo=0.08):
    """Motor Termodinámico Nativo de Evaporación"""
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
    except Exception:
        return pd.DataFrame()

df_embalses = cargar_datos_embalses()

# ==========================================
# 1. CONFIGURACIÓN GENERAL Y ESTILOS
# ==========================================
st.set_page_config(page_title="Piloto Piedras Blancas", page_icon="💧", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    
    .block-container {
        padding-top: 1.5rem !important; 
        padding-bottom: 2rem !important;
        max-width: 1300px;
    }

    .glass-card {
        background-color: #1e293b; 
        border: 1px solid rgba(148, 163, 184, 0.2); 
        border-radius: 12px; 
        padding: 24px; 
        color: #f8fafc;
        height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .kpi-box {
        background: #0f172a; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #334155;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .kpi-title { font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px; }
    .kpi-val { font-size: 2.5rem; font-weight: 800; line-height: 1.1; margin: 5px 0 10px 0; }
    .kpi-desc { font-size: 0.85rem; color: #cbd5e1; line-height: 1.4; }
    .kpi-foot { font-size: 0.75rem; font-weight: 700; margin-top: 15px; display: inline-block;}
    
    .border-top-sky { border-top: 4px solid #38bdf8; }
    .border-top-emerald { border-top: 4px solid #10b981; }
    .border-top-amber { border-top: 4px solid #f59e0b; }
    .border-top-purple { border-top: 4px solid #a855f7; }
    .border-top-rose { border-top: 4px solid #f43f5e; }
    
    .section-title { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin-bottom: 5px; }
    .section-subtitle { font-size: 1rem; color: #475569; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

LOGO_CUENCA = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/CuencaVerdeLogo_V1.JPG"
LOGO_EPM = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_epm.png"
LOGO_ALCALDIA = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_distritoMedellin.png"

# ==========================================
# 2. CABEZOTE EJECUTIVO
# ==========================================
col_l1, col_l2, col_l3, col_spc = st.columns([1, 1, 1, 15])
with col_l1: st.image(LOGO_CUENCA, use_container_width=True)
with col_l2: st.image(LOGO_EPM, use_container_width=True)
with col_l3: st.image(LOGO_ALCALDIA, use_container_width=True)

st.markdown("""
<div style="background: radial-gradient(circle at top right, #1e293b, #0f172a 70%); padding: 30px; border-radius: 15px; border-left: 5px solid #38bdf8; margin-top: 5px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);">
    <h4 style="color: #38bdf8; margin: 0 0 10px 0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">🛡️ Proyecto Piloto de Adaptación Hidroclimática Inmediata</h4>
    <h1 style="color: white; margin: 0 0 10px 0; font-size: 2.8rem; font-weight: 800; line-height: 1.1;">Blindaje Evaporativo del Embalse Piedras Blancas ante El Niño (2026-2027)</h1>
    <p style="color: #cbd5e1; font-size: 1.1rem; margin: 0; line-height: 1.5;">Estrategia proactiva para cosechar las lluvias de <b>octubre y noviembre de 2026</b> y sellar la lámina de agua mediante tecnologías flotantes, mitigando el riesgo de desabastecimiento en <b>diciembre de 2026 y el 1T de 2027</b>.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.markdown('<div class="kpi-box"><div class="kpi-title">Sistema Objetivo</div><div class="kpi-val" style="color: white; font-size: 1.3rem;">Embalse Piedras Blancas</div><div class="kpi-desc" style="color: #38bdf8; font-weight: 600;">Coord: 6.29° N, -75.49° W</div></div>', unsafe_allow_html=True)
c2.markdown('<div class="kpi-box"><div class="kpi-title">Capacidad de Reserva</div><div class="kpi-val" style="color: #fbbf24; font-size: 1.5rem;">0.50 Millones de m³</div><div class="kpi-desc">Acueducto EPM (Oriente Medellín)</div></div>', unsafe_allow_html=True)
c3.markdown('<div class="kpi-box"><div class="kpi-title">Variable de Intervención</div><div class="kpi-val" style="color: #34d399; font-size: 1.5rem;">Control Evaporativo</div><div class="kpi-desc">Impacto inmediato (50% - 85%)</div></div>', unsafe_allow_html=True)
c4.markdown('<div class="kpi-box"><div class="kpi-title">Ventana de Ejecución</div><div class="kpi-val" style="color: #fb7185; font-size: 1.5rem;">Oct - Nov 2026</div><div class="kpi-desc">Previo al estiaje Dic 26 - Mar 27</div></div>', unsafe_allow_html=True)

st.write("") 

# ==========================================
# 3. NAVEGACIÓN EN PESTAÑAS (7 TABS AHORA)
# ==========================================
tabs = st.tabs([
    "🌍 1. Diagnóstico", 
    "🔄 2. Gobernanza", 
    "🔬 3. Física Evaporativa", 
    "🛠️ 4. Tecnologías",
    "💡 5. Creación de Valor", 
    "🎛️ 6. Simulador Piloto", 
    "🚀 7. Ruta Crítica"
])

# ---------------------------------------------------------
# TAB 1: DIAGNÓSTICO TERRITORIAL
# ---------------------------------------------------------
with tabs[0]:
    st.markdown('<div class="section-title">Contexto Socio-Hidroclimático: La Vulnerabilidad de Piedras Blancas</div>', unsafe_allow_html=True)
    
    col_diag1, col_diag2 = st.columns([1.2, 1])
    with col_diag1:
        st.markdown('<div class="glass-card"><h3 style="margin-top:0;">Asimetría en el Sistema de Reservas (EPM)</h3><p style="color:#94a3b8; font-size:0.9rem;">A diferencia de los grandes embalses interconectados, Piedras Blancas posee una capacidad volumétrica reducida y opera con un margen de maniobra milimétrico.</p></div>', unsafe_allow_html=True)
        df_vol = pd.DataFrame({"Embalse": ["Río Grande II", "La Fe", "Piedras Blancas"], "Volumen (Mm³)": [138.8, 11.1, 0.5], "Color": ["#38bdf8", "#34d399", "#fbbf24"]})
        fig_vol = px.bar(df_vol, y="Embalse", x="Volumen (Mm³)", text="Volumen (Mm³)", orientation='h')
        fig_vol.update_traces(marker_color=df_vol["Color"], textposition='outside', textfont=dict(color='#0f172a', weight='bold'))
        fig_vol.update_layout(height=240, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#475569'), margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(type='log', title="Volumen (Escala Logarítmica)", showgrid=False))
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_diag2:
        st.markdown("""
        <div class="glass-card border-top-amber" style="margin-bottom: 15px;">
            <strong style="color: #fbbf24; font-size: 1.1rem;">☀️ 1. Pérdida de la "Manta Natural" bajo El Niño</strong><br>
            <span style="font-size: 0.9rem; color: #cbd5e1;">Ubicado a ~2,350 msnm. Con El Niño, se rompe la cobertura nubosa, aumentando la radiación solar directa, la temperatura (+2°C) y la "sed" atmosférica.</span>
        </div>
        <div class="glass-card border-top-sky" style="margin-bottom: 15px;">
            <strong style="color: #38bdf8; font-size: 1.1rem;">📐 2. Morfología Tipo "Bandeja"</strong><br>
            <span style="font-size: 0.9rem; color: #cbd5e1;">Con ~0.5 Mm³ en 20 hectáreas, su ratio morfológico es bajísimo. Expone una gran superficie térmica por cada metro cúbico almacenado.</span>
        </div>
        <div class="glass-card border-top-purple">
            <strong style="color: #a855f7; font-size: 1.1rem;">🦠 3. Riesgo de Eutrofización en Estiaje</strong><br>
            <span style="font-size: 0.9rem; color: #cbd5e1;">En el 1T de 2027 aumenta la demanda, mientras que la radiación acelera floraciones de algas que comprometen y encarecen la potabilización.</span>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: GOBERNANZA Y CICLO
# ---------------------------------------------------------
with tabs[1]:
    st.markdown('<div class="section-title">El Ciclo Hidrológico: ¿Qué Variable Podemos Controlar Realmente Hoy?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Para evitar la crisis de diciembre 2026 y el 1T de 2027, debemos concentrar la inversión donde existe gobernabilidad humana inmediata.</div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("""<div class="glass-card border-top-sky">
        <h3 style="color: white; margin-top:0;">🌧️ 1. Precipitación (P)</h3>
        <span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">CONTROL HUMANO: ~0%</span>
        <p style="font-size: 0.9rem; margin-top: 15px; color: #cbd5e1;">Depende de fenómenos a escala planetaria. No podemos fabricar lluvias en pleno fenómeno de El Niño. Su dependencia es pasiva.</p>
        <p style="font-size: 0.85rem; color: #38bdf8; font-weight: 600;">Estrategia: Cosechar las últimas lluvias en Oct-Nov.</p>
    </div>""", unsafe_allow_html=True)
    
    c2.markdown("""<div class="glass-card border-top-amber">
        <h3 style="color: white; margin-top:0;">🌲 2. Caudales Base (Qb)</h3>
        <span style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">CONTROL: LARGO PLAZO</span>
        <p style="font-size: 0.9rem; margin-top: 15px; color: #cbd5e1;">Recarga lenta del bosque altoandino (SbN). Toma de 5 a 15 años de maduración ecológica para generar impacto volumétrico real.</p>
        <p style="font-size: 0.85rem; color: #fbbf24; font-weight: 600;">Límite: No aportará litros nuevos para Enero 2027.</p>
    </div>""", unsafe_allow_html=True)
    
    c3.markdown("""<div class="glass-card border-top-emerald" style="background-color: rgba(16, 185, 129, 0.05); border-color: #10b981;">
        <h3 style="color: #10b981; margin-top:0;">☀️ 3. Evaporación (E)</h3>
        <span style="background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">CONTROL: 50% AL 85% (INMEDIATO)</span>
        <p style="font-size: 0.9rem; margin-top: 15px; color: #cbd5e1;">Ocurre en un polígono pequeño y accesible (~20 ha). Aislar físicamente la interfaz agua-aire frena la pérdida casi por completo en semanas.</p>
        <p style="font-size: 0.85rem; color: #10b981; font-weight: 600;">Decisión: Única variable que reacciona a tiempo.</p>
    </div>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 3: FÍSICA EVAPORATIVA Y GRÁFICO MENSUAL
# ---------------------------------------------------------
with tabs[2]:
    st.markdown('<div class="section-title">Mecanismos Físicos de la Evaporación: Radiación Solar y Viento</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tasa de Evaporación Mensual en Embalse — Descomposición del término radiativo (energía) y aerodinámico (viento)</div>', unsafe_allow_html=True)
    
    col_chart, col_exp = st.columns([2, 1])
    
    with col_chart:
        data_evap = [
            {"month":"Ene","rad":85,"wind":30,"total":115}, {"month":"Feb","rad":90,"wind":25,"total":115},
            {"month":"Mar","rad":95,"wind":20,"total":115}, {"month":"Abr","rad":80,"wind":15,"total":95},
            {"month":"May","rad":70,"wind":15,"total":85}, {"month":"Jun","rad":65,"wind":20,"total":85},
            {"month":"Jul","rad":75,"wind":35,"total":110}, {"month":"Ago","rad":85,"wind":40,"total":125},
            {"month":"Sep","rad":90,"wind":25,"total":115}, {"month":"Oct","rad":80,"wind":15,"total":95},
            {"month":"Nov","rad":75,"wind":20,"total":95}, {"month":"Dic","rad":80,"wind":25,"total":105}
        ]
        df_chart = pd.DataFrame(data_evap)
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_chart["month"], y=df_chart["total"], mode='lines+markers', name='Evaporación Total', line=dict(color='#0ea5e9', width=3), marker=dict(size=8, color='#ffffff', line=dict(width=2, color='#0ea5e9'))))
        fig_line.add_trace(go.Scatter(x=df_chart["month"], y=df_chart["rad"], mode='lines+markers', name='Radiación (Energía)', line=dict(color='#64748b', width=2.5), marker=dict(size=7, color='#ffffff', line=dict(width=2, color='#64748b'))))
        fig_line.add_trace(go.Scatter(x=df_chart["month"], y=df_chart["wind"], mode='lines+markers', name='Viento (Aerodinámico)', line=dict(color='#10b981', width=2.5), marker=dict(size=7, color='#ffffff', line=dict(width=2, color='#10b981'))))
        
        fig_line.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#475569', family='Inter'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            hovermode="x unified", height=420, margin=dict(t=20, b=10, l=10, r=10),
            yaxis=dict(title="Milímetros (mm)", showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False),
            xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("💡 **Balance energético:** Evalúa cómo la radiación solar conduce el mayor porcentaje de evaporación frente al transporte aerodinámico.")

    with col_exp:
        st.markdown("""
        <div class="glass-card border-top-amber" style="margin-bottom: 15px; padding: 20px;">
            <strong style="color: #fbbf24; font-size: 1.1rem;">☀️ 1. Motor Radiativo</strong><br>
            <span style="font-size: 0.9rem; color: #cbd5e1;">El agua libre refleja solo el 8% de la luz solar (Bajo Albedo) y absorbe el <b>92% de la energía radiante</b>, calentando la capa superficial e impulsando más del 68% de las pérdidas (línea gris).</span>
        </div>
        <div class="glass-card border-top-sky" style="padding: 20px;">
            <strong style="color: #38bdf8; font-size: 1.1rem;">💨 2. Motor Aerodinámico</strong><br>
            <span style="font-size: 0.9rem; color: #cbd5e1;">Gobernado por el <b>Déficit de Presión de Vapor (VPD)</b>. A 2,350 msnm, la menor presión barométrica y los vientos barren continuamente la cúpula de vapor, acelerando la fuga.</span>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 4: TECNOLOGÍAS DE MITIGACIÓN (NUEVA PESTAÑA)
# ---------------------------------------------------------
with tabs[3]:
    st.markdown('<div class="section-title">Tecnologías de Control y Viabilidad Financiera</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Desde barreras físicas tradicionales hasta infraestructuras de generación eléctrica que protegen el recurso hídrico.</div>', unsafe_allow_html=True)
    
    st.markdown("### 1. Espectro de Tecnologías Base")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("Cubiertas y Mantas Físicas")
        st.markdown("""
        Método altamente eficaz a pequeña y mediana escala al bloquear el contacto directo agua-aire.
        * **Mantas Térmicas (Burbujas):** Reducen la evaporación casi por completo y retienen el calor nocturno.
        * **Cubiertas Automáticas (Lamas):** Rígidas (PVC/policarbonato), duraderas y brindan seguridad física.
        * **Cubiertas Solares:** Filtran rayos solares para reducir la brecha térmica entre el agua y el ambiente.
        """)
        
        st.subheader("Cobertores Líquidos (Mantas Químicas)")
        st.markdown("""
        Productos biodegradables que crean una **capa monomolecular invisible**. Frenan la salida del vapor sin alterar la potabilidad. A pequeña escala son económicos, pero a gran escala requieren dosificación "upwind" constante, perdiendo viabilidad.
        """)
    with col_t2:
        st.subheader("Sistemas de Esferas Flotantes (Barrier Balls)")
        st.markdown("""
        Esferas de plástico con protección UV que cubren la superficie bloqueando más del 90% de la interfaz agua-aire. Minimizan la radiación directa, reducen el crecimiento de algas y se apartan fácilmente ante intrusiones físicas.
        """)
        
        st.subheader("⬡ Módulos Hexagonales Autoconectables")
        st.markdown("""
        Alternativa mecánica modular (HexaCovers). Paneles de plástico que flotan y se autoensamblan geométricamente. Se adaptan dinámicamente al nivel del agua; si el embalse baja, se apilan en las orillas sin sufrir daños.
        """)

    st.markdown("---")
    st.markdown("### 2. Análisis Financiero y Evaluación Comparativa Dinámica")
    st.markdown("Ajuste el tamaño del embalse y seleccione una tecnología para proyectar su viabilidad a escala industrial (Cálculo basado en una cobertura del 40% de la superficie).")

    col_area, col_tech = st.columns([1, 2])
    with col_area:
        area_eval_ha = st.number_input("📐 Área total del embalse a evaluar (Hectáreas):", min_value=1.0, value=20.0, step=5.0)
    with col_tech:
        tech_eval = st.selectbox("🔍 Seleccionar Tecnología a Evaluar:", [
            "☀️ Paneles Solares Flotantes (Floatovoltaics - FPV)",
            "⬡ Módulos Hexagonales Autoconectables",
            "🌑 Sistemas de Esferas Flotantes (Barrier Balls)",
            "🛡️ Cubiertas y Mantas Físicas (Burbujas, Lamas, Solares)"
        ])

    vista_fin_sin = st.radio("Seleccione la vista de análisis:", ["💰 Modelo Financiero y Viabilidad", "📊 Síntesis Comparativa Global"], horizontal=True, label_visibility="collapsed")

    if vista_fin_sin == "💰 Modelo Financiero y Viabilidad":
        col_info, col_galeria = st.columns([1.6, 1.4])
        
        def obtener_galeria(prefijos):
            ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'Fotos'))
            imgs = []
            if os.path.exists(ruta_base):
                for f in os.listdir(ruta_base):
                    if any(p.lower() in f.lower() for p in prefijos):
                        imgs.append(os.path.join(ruta_base, f))
            return sorted(imgs)
            
        with col_info:
            area_cubierta_m2 = area_eval_ha * 10000 * 0.40
            factor_escala = area_eval_ha / 20.0
            mwp_instalado = 10.0 * factor_escala
            
            if "Paneles Solares" in tech_eval:
                st.success("**Tecnología Líder en Costo-Efectividad a Gran Escala:** Genera sinergia Agua-Energía.")
                st.markdown(f"**Desglose Inversión:** El CAPEX solar flotante oscila entre **$0.55 y $0.80 USD por vatio**. Cubrir el 40% del embalse ({area_cubierta_m2:,.0f} m²) permite instalar unos **{mwp_instalado:,.1f} MWp**. Inversión bruta: **${(6.70 * factor_escala):,.2f}M a ${(8.05 * factor_escala):,.2f}M USD**.")
                df_capex = pd.DataFrame({
                    "Componente": ["Módulos Fotovoltaicos", "Flotadores HDPE y Pasarelas", "Inversores y Equipos", "Anclaje y Amarre", "BOP Eléctrico", "Ingeniería y Permisos"],
                    "Participación": ["35%", "22%", "16%", "12%", "8%", "7%"]
                })
                st.table(df_capex)
                
                st.markdown(f"""
                **Beneficios Fiscales (Leyes 1715 y 2099):** El desembolso se reduce a **${(4.5 * factor_escala):,.2f}M - ${(5.5 * factor_escala):,.2f}M USD**:
                * **Exclusión IVA (19%) y Exención Arancelaria** para equipos importados.
                * **Deducción de Renta:** Hasta el 50% de la inversión en 15 años.
                * **Depreciación Acelerada:** Amortización en 3 a 5 años.
                
                **Retorno (ROI):** Al generar {(13.5 * factor_escala):,.1f} GWh/año para autoconsumo en bombeo, desplazando tarifas de EPM ($700-$900 COP/kWh):
                * **Ahorro Bruto Anual:** ${(2.5 * factor_escala):,.2f} - ${(3.0 * factor_escala):,.2f} Millones USD.
                * **Payback:** **2.5 a 4 años**. Vida útil restante (20+ años) como flujo de caja positivo.
                """)

            elif "Hexagonales" in tech_eval:
                st.info("**Alternativa Mecánica de Alta Durabilidad:** Ideal si la interconexión eléctrica no es viable.")
                st.markdown(f"""
                * **CAPEX (Inversión Inicial):** Moderada-Alta. Cubrir {area_cubierta_m2:,.0f} m² (40% de {area_eval_ha} Ha) cuesta aprox. **${(1.2 * factor_escala):,.2f}M - ${(2.0 * factor_escala):,.2f}M USD** ($15 - $25 USD/m²).
                * **OPEX (Gasto Recurrente):** Casi nulo. No requieren limpieza constante ni consumen energía.
                * **Retorno Financiero:** Indirecto. Se amortiza en 7 a 10 años basándose exclusivamente en el valor del agua cruda salvada.
                * **Viabilidad Técnica:** Excelente en topografías complejas; soportan fluctuaciones severas de cota sin tensión estructural.
                """)

            elif "Esferas" in tech_eval:
                st.warning("**Control Dinámico:** Famosas por su uso en el Embalse de Los Ángeles.")
                st.markdown(f"""
                * **CAPEX (Inversión Inicial):** Moderada. Aprox. **${(800 * factor_escala):,.0f}k - ${(1.2 * factor_escala):,.2f}M USD** para {area_cubierta_m2:,.0f} m² ($10 - $15 USD/m²).
                * **OPEX (Gasto Recurrente):** Bajo, pero superior a los hexágonos. Las esferas pueden acumular biopelículas o ser expulsadas a las orillas.
                * **Retorno Financiero:** 5 a 8 años por retención hídrica. 
                * **Limitación en Antioquia:** En cañones con efecto Venturi, las esferas tienden a apilarse en un solo extremo del embalse, perdiendo efectividad de cobertura.
                """)

            elif "Mantas" in tech_eval:
                st.error("**Descarte a Gran Escala:** Eficaces en piscinas y acueductos veredales, inviables en embalses.")
                st.markdown(f"""
                * **Mantas de Burbujas / Solares:** Extremadamente vulnerables al desgarro por fatiga mecánica. Vida útil reducida a 1-2 años a la intemperie total.
                * **Cubiertas de Lamas:** Costo prohibitivo a escala industrial (supera los $100 USD/m²).
                * **Veredicto:** Su uso debe restringirse a tanques de almacenamiento, plantas de tratamiento (PTAP) o reservorios menores a 1 Hectárea.
                """)

        with col_galeria:
            st.markdown("#### 📸 Explorador Visual y Casos de Estudio")
            prefijos_busqueda = []
            if "Paneles Solares" in tech_eval:
                prefijos_busqueda = ["paneles_solares", "floating_solar"]
            elif "Hexagonales" in tech_eval:
                prefijos_busqueda = ["hexa-cover"]
            elif "Esferas" in tech_eval:
                prefijos_busqueda = ["esferas_flotantes"]
            elif "Mantas" in tech_eval:
                prefijos_busqueda = ["mantas_flotantes"]
            
            galeria = obtener_galeria(prefijos_busqueda)
            
            if galeria:
                if len(galeria) > 1:
                    idx = st.slider("Desliza para ver más fotografías:", 1, len(galeria), 1) - 1
                    st.image(galeria[idx], use_container_width=True, caption=f"Fotografía {idx+1} de {len(galeria)}")
                else:
                    st.image(galeria[0], use_container_width=True, caption="Fotografía de referencia")
            else:
                st.info("💡 Agrega imágenes con los prefijos correspondientes en la carpeta 'data/Fotos/' para visualizarlas aquí.")
            
            st.markdown("---")
            st.markdown("#### 🎬 Referencias Documentales")
            if "Esferas" in tech_eval:
                st.video("https://www.youtube.com/watch?v=x7GWPTZBJd0")
            elif "Hexagonales" in tech_eval:
                st.video("https://www.youtube.com/watch?v=37mrElHtc8E")
            elif "Paneles Solares" in tech_eval:
                st.info("📺 **Ver Documental:** [El Gran Proyecto Solar Hídrico](https://www.facebook.com/unboxfactory/videos/a-major-river-system-supplying-water-to-around-40-million-americans-is-now-testi/1475959924012973/)")
            else:
                st.caption("Selecciona 'Paneles Solares' o 'Sistemas de Esferas' para desbloquear videos documentales.")

    else:
        st.markdown("#### Matriz de Decisión: Costo-Efectividad para Embalses (Escala > 10 Hectáreas)")
        df_sintesis = pd.DataFrame({
            "Tecnología": [
                "Solares Flotantes (FPV)", "Módulos Hexagonales", "Barrier Balls (Esferas)", 
                "Mantas Físicas (Burbujas/Lamas)", "Cobertor Líquido (Químico)"
            ],
            "Inversión Inicial (CAPEX)": ["Muy Alta", "Moderada - Alta", "Moderada", "Alta (Lamas) / Baja (Burbujas)", "Muy Baja"],
            "Costo Operativo (OPEX)": ["Bajo (Mantenimiento eléctrico)", "Casi Nulo", "Bajo", "Alto (Reemplazos frecuentes)", "Muy Alto (Dosis perpetuas)"],
            "Retorno de Inversión": ["2.5 - 4 Años (Ahorro Agua, Genera Energía)", "7 - 10 Años (Ahorra Agua, Mejora Calidad)", "5 - 8 Años (Ahorra Agua)", "Inviable a gran escala", "No se amortiza (Gasto fijo)"],
            "Viabilidad en Antioquia": ["⭐⭐⭐⭐⭐ (Excelente)", "⭐⭐⭐⭐ (Muy Buena)", "⭐⭐ (Riesgo por vientos)", "⭐ (Útil en áreas pequeñas o crisis)", "⭐ (Áreas pequeñas o crisis)"]
        })
        st.dataframe(df_sintesis, use_container_width=True, hide_index=True)
        st.caption("Nota: La viabilidad en Antioquia considera la topografía de cañones (vientos fuertes) y la necesidad de mantener la potabilidad del agua libre de aditivos constantes.")

# ---------------------------------------------------------
# TAB 5: CREACIÓN DE VALOR PÚBLICO
# ---------------------------------------------------------
with tabs[4]:
    st.markdown('<div class="section-title">Co-Beneficios Estratégicos al Implementar el Piloto</div>', unsafe_allow_html=True)
    st.write("")
    
    b1, b2 = st.columns(2)
    b3, b4 = st.columns(2)
    b5, b6 = st.columns(2)
    
    b1.markdown("""<div class="glass-card" style="display:flex; align-items:flex-start; gap: 15px;">
        <div style="font-size: 2.5rem; color: #38bdf8;">🚰</div>
        <div><h3 style="color:white; margin:0 0 10px 0; font-size:1.2rem;">1. Mejora de Calidad del Agua y Control de Algas</h3>
        <p style="color:#cbd5e1; font-size:0.9rem;">Al sombrear la superficie y bajar la temperatura del agua en ~2.5°C, se inhibe la fotosíntesis de cianobacterias. Esto evita episodios de eutrofización y <b>reduce entre un 20% y 30% el consumo de químicos en la PTAP</b>.</p></div>
    </div>""", unsafe_allow_html=True)

    b2.markdown("""<div class="glass-card" style="display:flex; align-items:flex-start; gap: 15px;">
        <div style="font-size: 2.5rem; color: #10b981;">⚡</div>
        <div><h3 style="color:white; margin:0 0 10px 0; font-size:1.2rem;">2. Simbiosis Termo-Eléctrica (+10% Rendimiento)</h3>
        <p style="color:#cbd5e1; font-size:0.9rem;">Los paneles solares en tierra pierden eficiencia al sobrecalentarse. Sobre el espejo de agua frío (2,350 msnm), el enfriamiento convectivo incrementa la producción eléctrica entre un <b>8% y 12% adicional</b>.</p></div>
    </div>""", unsafe_allow_html=True)

    b3.markdown("""<div class="glass-card" style="display:flex; align-items:flex-start; gap: 15px; margin-top: 15px;">
        <div style="font-size: 2.5rem; color: #fbbf24;">🌲</div>
        <div><h3 style="color:white; margin:0 0 10px 0; font-size:1.2rem;">3. Cero Conflicto de Uso de Suelo (Parque Arví)</h3>
        <p style="color:#cbd5e1; font-size:0.9rem;">Instalar 4 MWp solares en tierra firme exigiría adquirir predios costosos o talar hectáreas. Usar la lámina de un embalse existente genera <b>impacto cero sobre el bosque nativo</b>.</p></div>
    </div>""", unsafe_allow_html=True)

    b4.markdown("""<div class="glass-card" style="display:flex; align-items:flex-start; gap: 15px; margin-top: 15px;">
        <div style="font-size: 2.5rem; color: #a855f7;">🔄</div>
        <div><h3 style="color:white; margin:0 0 10px 0; font-size:1.2rem;">4. Escalabilidad Hacia La Fe y Río Grande II</h3>
        <p style="color:#cbd5e1; font-size:0.9rem;">Por su escala manejable (~20 ha) y aguas tranquilas, Piedras Blancas es el <b>laboratorio vivo ideal</b> para calibrar anclajes y telemetría antes de escalar a La Fe (145 ha) y Río Grande II (1,100 ha).</p></div>
    </div>""", unsafe_allow_html=True)

    b5.markdown("""<div class="glass-card" style="display:flex; align-items:flex-start; gap: 15px; margin-top: 15px;">
        <div style="font-size: 2.5rem; color: #f43f5e;">📜</div>
        <div><h3 style="color:white; margin:0 0 10px 0; font-size:1.2rem;">5. Beneficios Fiscales (Leyes 1715 y 2099)</h3>
        <p style="color:#cbd5e1; font-size:0.9rem;">Bajo estas leyes, el desembolso se reduce a <b>4.50M - 5.50M USD</b> mediante: Exclusión de IVA (19%) y exención arancelaria, Deducción de Renta (50% en 15 años) y Depreciación Acelerada (3 a 5 años).</p></div>
    </div>""", unsafe_allow_html=True)

    b6.markdown("""<div class="glass-card" style="display:flex; align-items:flex-start; gap: 15px; margin-top: 15px;">
        <div style="font-size: 2.5rem; color: #10b981;">📈</div>
        <div><h3 style="color:white; margin:0 0 10px 0; font-size:1.2rem;">6. Retorno Financiero (ROI)</h3>
        <p style="color:#cbd5e1; font-size:0.9rem;">Al generar 13.5 GWh/año para autoconsumo, desplazando tarifas de EPM (700-900 COP/kWh), se logra un <b>Ahorro Bruto Anual de 2.50-3.00 Millones USD</b>. Payback de 2.5 a 4 años con más de 20 años de flujo positivo.</p></div>
    </div>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 6: SIMULADOR DEL PILOTO
# ---------------------------------------------------------
with tabs[5]:
    st.markdown('<div class="section-title">Proyecto Piloto: Números para la Toma de Decisiones</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Ajuste los parámetros para la ventana crítica (Dic 2026 - Mar 2027) bajo escenario de El Niño.</div>', unsafe_allow_html=True)
    
    col_ctrl, col_kpi = st.columns([1, 2.5])
    
    with col_ctrl:
        st.markdown('<h4 style="color: #0f172a; margin-bottom: 15px;">⚙️ Parámetros de Simulación</h4>', unsafe_allow_html=True)
        area_eval = st.slider("Espejo de Agua Actual (ha):", 10.0, 28.0, 20.0, 1.0)
        pct_cob = st.slider("Cobertura del Piloto (%):", 10, 70, 40, 5)
        tech_sim = st.selectbox("Tecnología del Piloto:", ["⭐ Híbrido (50% FPV + 50% Hexa)", "☀️ 100% Paneles FPV", "⬡ 100% Módulos Hexagonales"])
        dias_estiaje = st.slider("Ventana Crítica (días):", 30, 180, 120, 15)
        consumo_hab = st.slider("Consumo (L/hab-día):", 50, 300, 50, 10)

    with col_kpi:
        area_cub = area_eval * (pct_cob / 100.0)
        ev_dia = 4.35 
        if "Híbrido" in tech_sim: eff, mwp, cap, pay = 0.75, 0.625, 0.36, "Payback: 3.8 Años"
        elif "Solares" in tech_sim: eff, mwp, cap, pay = 0.65, 1.25, 0.56, "Payback: 3.1 Años"
        else: eff, mwp, cap, pay = 0.85, 0.0, 0.19, "Sólo ahorro de agua"
            
        perdida_base = ev_dia * area_eval * 10
        ahorro_diario = perdida_base * (pct_cob / 100.0) * eff
        agua_salv_total = ahorro_diario * dias_estiaje
        piscinas = agua_salv_total / 2500.0
        
        hab_abastecidos = (ahorro_diario * 60) / ((consumo_hab / 1000.0) * dias_estiaje)
        mwp_tot = area_cub * mwp
        gwh_ano = mwp_tot * 1.35
        cap_tot = area_cub * cap

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'''<div class="kpi-box border-top-sky"><div class="kpi-title">AGUA SALVADA ({dias_estiaje} DÍAS)</div>
            <div class="kpi-val" style="color: #38bdf8;">{agua_salv_total:,.0f} <span style="font-size:1.5rem">m³</span></div>
            <div class="kpi-desc">Equivalente a <b>{piscinas:.1f} Piscinas Olímpicas</b> retenidas en el vaso.</div>
            <div class="kpi-foot" style="color: #38bdf8;">Anualizado: ~{(ahorro_diario*365):,.0f} m³/año</div></div>''', unsafe_allow_html=True)
            
        k2.markdown(f'''<div class="kpi-box border-top-emerald"><div class="kpi-title">SEGURIDAD ABASTECIMIENTO</div>
            <div class="kpi-val" style="color: #34d399;">{hab_abastecidos:,.0f} <span style="font-size:1.5rem">Hab</span></div>
            <div class="kpi-desc">Población con suministro garantizado a {consumo_hab} L/día en estiaje.</div>
            <div class="kpi-foot" style="color: #34d399;">Evita carrotanques</div></div>''', unsafe_allow_html=True)
            
        txt_ener = f"{mwp_tot:.1f} MWp" if mwp_tot > 0 else "0.0 MWp"
        txt_ener_sub = f"Genera {gwh_ano:.1f} GWh/año para autoconsumo EPM." if mwp_tot > 0 else "Barrera mecánica pasiva."
        k3.markdown(f'''<div class="kpi-box border-top-amber"><div class="kpi-title">GENERACIÓN (FPV)</div>
            <div class="kpi-val" style="color: #fbbf24;">{txt_ener}</div>
            <div class="kpi-desc">{txt_ener_sub}</div>
            <div class="kpi-foot" style="color: #fbbf24;">Sinergia energética</div></div>''', unsafe_allow_html=True)
            
        k4.markdown(f'''<div class="kpi-box border-top-purple"><div class="kpi-title">INVERSIÓN (CAPEX NETO)</div>
            <div class="kpi-val" style="color: white;">${cap_tot:.1f}M <span style="font-size:1.3rem">USD</span></div>
            <div class="kpi-desc">CAPEX neto asumiendo Ley 1715.</div>
            <div class="kpi-foot" style="color: #fb7185;">{pay}</div></div>''', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 7: RUTA CRÍTICA
# ---------------------------------------------------------
with tabs[6]:
    st.markdown("""
    <div class="section-title" style="margin-bottom: 15px;">Ruta Crítica de Acción: Octubre 2026 – Primer Trimestre 2027</div>
    <div style="background: rgba(127, 29, 29, 0.1); border: 1px solid rgba(248, 113, 113, 0.4); padding: 20px; border-radius: 10px; margin-bottom: 25px;">
        <span style="color: #ef4444; font-weight: bold; font-size: 1.1rem;">⚠️ ¿Por qué decidir HOY en Octubre de 2026?</span> <span style="color: #334155; font-size: 1.05rem;"><br>No se puede tapar un embalse cuando ya se secó en febrero. Debemos aprovechar los <b>días lluviosos de octubre y noviembre</b> para llenar el vaso al 100%, e instalar la cobertura para que actúe como "tapa hermética" desde el 1 de diciembre.</span>
    </div>
    """, unsafe_allow_html=True)
    
    r1, r2, r3, r4 = st.columns(4)
    r1.markdown("""<div class="glass-card border-top-sky">
        <span style="color:#38bdf8; font-size:0.75rem; font-weight:700;">PASO 1 • OCTUBRE 2026</span>
        <h3 style="color:white; font-size:1.1rem; margin:10px 0;">Aprobación Express y Cosecha</h3>
        <ul style="color:#cbd5e1; font-size:0.85rem; padding-left:15px; margin-bottom: 20px;">
            <li style="margin-bottom: 8px;">Aprobación ejecutiva del Piloto (8 ha).</li>
            <li style="margin-bottom: 8px;">Regla de retención máxima de lluvias de octubre.</li>
            <li>Compra de módulos rápidos (Fase 1A).</li>
        </ul>
        <div style="font-size:0.75rem; font-weight:700; color:#38bdf8;">Hito: Compra lista al 31 Oct.</div>
    </div>""", unsafe_allow_html=True)
    
    r2.markdown("""<div class="glass-card border-top-emerald">
        <span style="color:#10b981; font-size:0.75rem; font-weight:700;">PASO 2 • NOVIEMBRE 2026</span>
        <h3 style="color:white; font-size:1.1rem; margin:10px 0;">Sellado Temprano</h3>
        <ul style="color:#cbd5e1; font-size:0.85rem; padding-left:15px; margin-bottom: 20px;">
            <li style="margin-bottom: 8px;">Captura de lluvias hasta cota máxima.</li>
            <li style="margin-bottom: 8px;">Instalación de barreras y despliegue modular.</li>
            <li>Encendido de boyas de telemetría.</li>
        </ul>
        <div style="font-size:0.75rem; font-weight:700; color:#10b981;">Hito: Sellado al 30 de Nov.</div>
    </div>""", unsafe_allow_html=True)
    
    r3.markdown("""<div class="glass-card border-top-amber">
        <span style="color:#fbbf24; font-size:0.75rem; font-weight:700;">PASO 3 • DICIEMBRE 2026</span>
        <h3 style="color:white; font-size:1.1rem; margin:10px 0;">Defensa Activa en Verano</h3>
        <ul style="color:#cbd5e1; font-size:0.85rem; padding-left:15px; margin-bottom: 20px;">
            <li style="margin-bottom: 8px;">Llegada de radiación y vientos alisios con escudo activo.</li>
            <li style="margin-bottom: 8px;">Ahorro inmediato de ~260 m³/día.</li>
            <li>Montaje e interconexión de Paneles FPV.</li>
        </ul>
        <div style="font-size:0.75rem; font-weight:700; color:#fbbf24;">Hito: Mitigación pico Dic.</div>
    </div>""", unsafe_allow_html=True)
    
    r4.markdown("""<div class="glass-card border-top-purple">
        <span style="color:#a855f7; font-size:0.75rem; font-weight:700;">PASO 4 • ENE - MAR 2027</span>
        <h3 style="color:white; font-size:1.1rem; margin:10px 0;">Superación y Escalado</h3>
        <ul style="color:#cbd5e1; font-size:0.85rem; padding-left:15px; margin-bottom: 20px;">
            <li style="margin-bottom: 8px;">Preservación de >31,000 m³ en el trimestre más seco.</li>
            <li style="margin-bottom: 8px;">Agua cruda sin proliferación de algas.</li>
            <li>Expediente técnico validado para La Fe.</li>
        </ul>
        <div style="font-size:0.75rem; font-weight:700; color:#a855f7;">Hito: Modelo listo para escalar.</div>
    </div>""", unsafe_allow_html=True)
