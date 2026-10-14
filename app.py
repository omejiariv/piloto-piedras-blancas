import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
from datetime import datetime

# ==========================================
# 0. MOTOR TERMODINÁMICO NATIVO (Reemplaza a PyETo)
# ==========================================
def calcular_penman_monteith(tmax, tmin, rh, u2, rs, elev, lat, dia, albedo=0.08):
    lat_rad = math.radians(lat)
    t_media = (tmax + tmin) / 2.0
    
    # Presión atmosférica y Constante psicrométrica (gamma)
    P = 101.3 * ((293 - 0.0065 * elev) / 293) ** 5.26
    gamma = 0.000665 * P
    
    # Pendiente curva presión vapor (delta)
    delta = 4098 * (0.6108 * math.exp((17.27 * t_media) / (t_media + 237.3))) / ((t_media + 237.3) ** 2)
    
    # Déficit de presión de vapor (VPD)
    es_tmax = 0.6108 * math.exp((17.27 * tmax) / (tmax + 237.3))
    es_tmin = 0.6108 * math.exp((17.27 * tmin) / (tmin + 237.3))
    es = (es_tmax + es_tmin) / 2.0
    ea = es * (rh / 100.0) 
    vpd = es - ea
    
    # Radiación Neta
    rns = (1 - albedo) * rs
    sol_dec = 0.409 * math.sin(((2 * math.pi) / 365) * dia - 1.39)
    sha = math.acos(-math.tan(lat_rad) * math.tan(sol_dec))
    ird = 1 + 0.033 * math.cos(((2 * math.pi) / 365) * dia)
    ra = (24 * 60 / math.pi) * 0.0820 * ird * (sha * math.sin(lat_rad) * math.sin(sol_dec) + math.cos(lat_rad) * math.cos(sol_dec) * math.sin(sha))
    rso = (0.75 + 2e-5 * elev) * ra
    
    # Radiación onda larga
    rs_rso = min(rs / rso, 1.0) if rso > 0 else 0.5
    rnl = 4.903e-9 * (((tmax + 273.16)**4 + (tmin + 273.16)**4) / 2) * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * rs_rso - 0.35)
    rn = rns - rnl
    
    # Términos Ecuación Penman
    term_rad = (0.408 * delta * rn) / (delta + gamma)
    term_aero = (gamma * 2.626 * (1 + 0.536 * u2) * vpd) / (delta + gamma)
    
    return term_rad, term_aero, term_rad + term_aero

# ==========================================
# 1. CONFIGURACIÓN GENERAL Y ESTILOS
# ==========================================
st.set_page_config(page_title="Piloto Piedras Blancas", page_icon="💧", layout="wide")

st.markdown("""
<style>
    /* Reducir el espacio superior por defecto de la página en Streamlit */
    .block-container {
        padding-top: 1.5rem;
    }
    .metric-card {
        background-color: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 10px;
    }
    .metric-title { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;}
    .metric-value { color: #38bdf8; font-size: 1.8rem; font-weight: 800; margin: 5px 0;}
    .metric-sub { color: #cbd5e1; font-size: 0.75rem;}
</style>
""", unsafe_allow_html=True)

# URLs de Logos (Desde Supabase)
LOGO_CUENCA = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/CuencaVerdeLogo_V1.JPG"
LOGO_EPM = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_epm.png"
LOGO_ALCALDIA = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_distritoMedellin.png"

# ==========================================
# 2. CABEZOTE EJECUTIVO
# ==========================================
col_l1, col_l2, col_l3, col_spc = st.columns([1, 1, 1, 1])
with col_l1: st.image(LOGO_CUENCA, use_container_width=True)
with col_l2: st.image(LOGO_EPM, use_container_width=True)
with col_l3: st.image(LOGO_ALCALDIA, use_container_width=True)

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

# ==========================================
# 3. NAVEGACIÓN EN PESTAÑAS (TABS)
# ==========================================
tabs = st.tabs([
    "🌍 1. Diagnóstico", 
    "🔄 2. Gobernanza y Ciclo", 
    "🔬 3. Física Evaporativa", 
    "💡 4. Tecnologías y Valor", 
    "🎛️ 5. Simulador del Piloto", 
    "🚀 6. Ruta Crítica"
])

# ---------------------------------------------------------
# TAB 1: DIAGNÓSTICO TERRITORIAL
# ---------------------------------------------------------
with tabs[0]:
    st.header("Contexto Socio-Hidroclimático: La Vulnerabilidad de Piedras Blancas")
    
    col_diag1, col_diag2 = st.columns([1.2, 1])
    
    with col_diag1:
        st.subheader("Asimetría en el Sistema de Reservas (EPM)")
        st.markdown("A diferencia de los grandes embalses del sistema interconectado y de acueducto metropolitano, **Piedras Blancas** posee una capacidad volumétrica reducida y una geometría altamente expuesta:")
        
        # Gráfico comparativo
        df_embalses = pd.DataFrame({
            "Embalse": ["Río Grande II", "La Fe", "Piedras Blancas"],
            "Volumen (Mm³)": [138.8, 11.1, 0.5],
            "Color": ["#38bdf8", "#34d399", "#fbbf24"]
        })
        fig_vol = px.bar(df_embalses, y="Embalse", x="Volumen (Mm³)", text="Volumen (Mm³)", orientation='h')
        fig_vol.update_traces(marker_color=df_embalses["Color"], textposition='outside')
        fig_vol.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(type='log', title="Volumen en Mm³ (Escala Logarítmica)"))
        st.plotly_chart(fig_vol, use_container_width=True)
        st.caption("*Piedras Blancas es de uso exclusivo para acueducto, exigiendo monitoreo hidrometeorológico de alta precisión.")

    with col_diag2:
        st.error("☀️ **1. Pérdida de la 'Manta Natural' bajo El Niño**\n\nUbicado en Bosque Muy Húmedo Montano Bajo (bmh-MB) a ~2,350 msnm. Con El Niño, se rompe la cobertura nubosa, aumentando la radiación solar directa, la temperatura (+2°C) y la 'sed' atmosférica.")
        st.warning("📐 **2. Morfología Tipo 'Bandeja'**\n\nCon ~0.5 Mm³ distribuidos en 20 hectáreas, su ratio morfológico es bajísimo (≈ 0.025 Mm³/ha). Expone demasiada superficie térmica por cada metro cúbico almacenado.")
        st.info("🦠 **3. Presión Social y Riesgo de Eutrofización**\n\nEn el 1T de 2027 aumenta la demanda en Santa Elena y el oriente de Medellín, mientras que la radiación acelera la floración de cianobacterias (algas) que encarecen la potabilización.")

# ---------------------------------------------------------
# TAB 2: CICLO HIDROLÓGICO
# ---------------------------------------------------------
with tabs[1]:
    st.header("El Ciclo Hidrológico: ¿Qué Variable Podemos Controlar Realmente Hoy?")
    st.markdown("Para evitar la crisis de diciembre 2026 y el 1T de 2027, debemos concentrar la inversión donde existe **gobernabilidad humana inmediata**.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.error("🌧️ 1. Precipitación (P) | CONTROL: ~0%")
        st.markdown("""
        * **Mecanismo:** Depende de fenómenos a escala planetaria (ENSO, ZCIT).
        * **Maniobra:** Nula. No podemos fabricar lluvias.
        * **Estrategia Oct-Nov:** Capturar y almacenar cada gota de los últimos aguaceros.
        """)
    with c2:
        st.warning("🌲 2. Caudales Base (Qb) | CONTROL: LARGO PLAZO")
        st.markdown("""
        * **Mecanismo:** Recarga subsuperficial desde el bosque altoandino.
        * **Maniobra:** Alta, pero lenta (Soluciones Basadas en la Naturaleza - SbN).
        * **Límite:** Toma de **5 a 15 años** de maduración ecológica. No aportará litros en 2027.
        """)
    with c3:
        st.success("☀️ 3. Evaporación (E) | CONTROL: 50% al 85% (INMEDIATO)")
        st.markdown("""
        * **Mecanismo:** Escape físico de vapor en un polígono pequeño y accesible (~20 ha).
        * **Maniobra:** **Máxima y Directa.** Aislar físicamente la interfaz agua-aire.
        * **Decisión Estratégica:** Única variable que reacciona en semanas. Conservar 1 m³ captado es más seguro que esperar lluvias.
        """)

# ---------------------------------------------------------
# TAB 3: FÍSICA Y MÉTODO NATIVO
# ---------------------------------------------------------
with tabs[2]:
    st.header("Mecanismos Físicos: Termodinámica Atmosférica (Penman-Monteith)")
    st.markdown("A diferencia de los bosques circundantes (que cierran sus estomas en sequía), el espejo de agua carece de defensas biológicas.")
    
    col_fis1, col_fis2 = st.columns([1, 1.2])
    
    with col_fis1:
        st.subheader("Los Dos Motores de la Evaporación")
        st.markdown("""
        **1. Motor Radiativo (Balance Energético):**
        * **Trampa de Bajo Albedo (α ≈ 0.08):** El agua libre absorbe el 92% de la energía radiante solar.
        * Fórmula: `E_rad = [ 0.408 * Δ * (Rns - Rnl) ] / [ Δ + γ ]`
        
        **2. Motor Aerodinámico (Viento y VPD):**
        * **Barrido y Altitud:** El viento arrastra la cúpula húmeda. A 2,350 msnm la presión barométrica es menor (~76.5 kPa), facilitando el escape molecular.
        * Fórmula: `E_aero = [ γ * 2.626 * (1 + 0.536 * u2) * VPD ] / [ Δ + γ ]`
        """)

    with col_fis2:
        st.subheader("🔬 Laboratorio Termodinámico: Piedras Blancas en Vivo")
        with st.expander("Ajustar Condiciones Climáticas (Simulación)", expanded=True):
            cc1, cc2 = st.columns(2)
            tmax = cc1.slider("Temp. Máxima (°C)", 15.0, 35.0, 23.5)
            tmin = cc1.slider("Temp. Mínima (°C)", 5.0, 20.0, 11.5)
            rh = cc2.slider("Humedad Relativa (%)", 40.0, 100.0, 65.0)
            u2 = cc2.slider("Viento a 2m (m/s)", 0.5, 6.0, 2.8)
            rs = st.slider("Radiación Solar (MJ/m²/día)", 10.0, 30.0, 20.5)

        # Usar la función matemática nativa en lugar de pyeto
        term_rad, term_aero, evap_total = calcular_penman_monteith(tmax, tmin, rh, u2, rs, elev=2350.0, lat=6.29, dia=345)

        fig_pie = go.Figure(data=[go.Pie(
            labels=['Motor Radiativo (Solar)', 'Motor Aerodinámico (Viento/VPD)'],
            values=[max(0, term_rad), max(0, term_aero)], hole=.4,
            marker_colors=['#fbbf24', '#38bdf8']
        )])
        fig_pie.update_layout(title_text=f"Flujo Evaporativo Total: {evap_total:.2f} mm/día", margin=dict(t=40, b=0, l=0, r=0), height=250)
        st.plotly_chart(fig_pie, use_container_width=True)

# ---------------------------------------------------------
# TAB 4: TECNOLOGÍAS Y VALOR PÚBLICO
# ---------------------------------------------------------
with tabs[3]:
    st.header("Ingeniería de Mitigación y Creación de Valor")
    
    st.subheader("1. Matriz Tecnológica Evaluada")
    df_tech = pd.DataFrame({
        "Tecnología": ["☀️ Paneles Solares Flotantes (FPV)", "⬡ Módulos Hexagonales", "🌑 Esferas de Sombra", "🧪 Cobertores Químicos"],
        "Reducción Evap.": ["60% - 70%", "80% - 90%", "80% - 85%", "15% - 30%"],
        "Retorno (ROI)": ["2.5 a 4.0 Años (Leyes 1715)", "7 a 10 Años", "5 a 8 Años", "No se amortiza (OPEX)"],
        "Viabilidad Piedras Blancas": ["⭐⭐⭐⭐⭐ Excelente (Sinergia)", "⭐⭐⭐⭐⭐ Excelente (Rápido)", "⭐⭐⭐ Media (Requiere Booms)", "⭐ Apoyo Táctico Breve"]
    })
    st.dataframe(df_tech, use_container_width=True, hide_index=True)
    
    st.subheader("2. Co-Beneficios Estratégicos (Valor Público y Ambiental)")
    b1, b2, b3, b4 = st.columns(4)
    b1.info("**🦠 Control de Algas:** Sombrear el agua reduce la temperatura y frena cianobacterias, ahorrando 30% en químicos PTAP.")
    b2.success("**⚡ Simbiosis Eléctrica:** El agua fría (2,350 msnm) refrigera los paneles FPV, elevando su eficiencia un +10%.")
    b3.warning("**🌲 Cero Conflicto Suelo:** Evita talar bosques en el Parque Arví al aprovechar el espejo artificial existente.")
    b4.error("**🚀 Escalabilidad Regional:** Piedras Blancas es el laboratorio perfecto antes de saltar a La Fe y Río Grande II.")

# ---------------------------------------------------------
# TAB 5: SIMULADOR DEL PILOTO
# ---------------------------------------------------------
with tabs[4]:
    st.header("🎛️ Simulador del Proyecto Piloto y Caso de Negocio")
    st.markdown("Evaluación interactiva para dimensionar el impacto físico y financiero del piloto en Piedras Blancas.")
    
    col_ctrl, col_kpi = st.columns([1.2, 2])
    
    with col_ctrl:
        st.markdown("#### Parámetros de Intervención")
        area_eval = st.slider("Espejo de Agua Actual (ha):", 10.0, 28.0, 20.0, 1.0)
        pct_cob = st.slider("Cobertura del Proyecto Piloto (%):", 10, 70, 40, 5)
        
        tech_sim = st.selectbox("Tecnología del Piloto:", [
            "⭐ Piloto Híbrido Recomendado (50% FPV + 50% Hexa)",
            "☀️ 100% Paneles Solares Flotantes (FPV)",
            "⬡ 100% Módulos Hexagonales (Despliegue Rápido)"
        ])
        
        clima_sim = st.selectbox("Escenario Climático:", [
            "🔥 El Niño Consolidado (~4.35 mm/día)",
            "🚨 El Niño Crítico + Vientos (~5.10 mm/día)",
            "🌤️ Media Histórica (~3.40 mm/día)"
        ])
        
        consumo_hab = st.slider("Consumo Per Cápita (L/hab-día):", 50, 300, 50, 10)
        dias_estiaje = st.slider("Ventana Crítica / Temporalidad (días):", 30, 180, 60, 15)

    with col_kpi:
        area_cub = area_eval * (pct_cob / 100.0)
        ev_dia = 4.35
        if "Crítico" in clima_sim: ev_dia = 5.10
        elif "Media" in clima_sim: ev_dia = 3.40
            
        if "Híbrido" in tech_sim: eff, mwp, cap, pay = 0.75, 0.625, 0.36, "3.8 Años"
        elif "Solares" in tech_sim: eff, mwp, cap, pay = 0.65, 1.25, 0.56, "3.1 Años"
        else: eff, mwp, cap, pay = 0.85, 0.0, 0.19, "7.5 Años"
            
        perdida_base = ev_dia * area_eval * 10
        ahorro_diario = perdida_base * (pct_cob / 100.0) * eff
        
        agua_salv_total = ahorro_diario * dias_estiaje
        bolsa_base_60 = ahorro_diario * 60 # Regla de diseño base
        
        piscinas = agua_salv_total / 2500.0
        hab_abastecidos = bolsa_base_60 / ((consumo_hab / 1000.0) * dias_estiaje)
        
        mwp_tot = area_cub * mwp
        gwh_ano = mwp_tot * 1.35
        cap_tot = area_cub * cap

        st.markdown("#### Resultados del Impacto Proyectado")
        k1, k2 = st.columns(2)
        k1.metric(f"Agua Salvada ({dias_estiaje} días)", f"{agua_salv_total:,.0f} m³", f"{piscinas:.1f} Piscinas Olímpicas")
        k2.metric("Abastecimiento Garantizado", f"{hab_abastecidos:,.0f} Hab", f"Continuo a {consumo_hab} L/día")
        
        k3, k4 = st.columns(2)
        k3.metric("Generación Eléctrica", f"{mwp_tot:.1f} MWp", f"~ {gwh_ano:.1f} GWh/año" if mwp_tot>0 else "Pasivo Térmico")
        k4.metric("Inversión Est. (CAPEX Neto)", f"${cap_tot:.2f}M USD", f"Payback: {pay}", delta_color="inverse")

        # Gráfico de Curva de Retención
        paso = dias_estiaje / 10
        dx = [int(i * paso) for i in range(11)]
        y_sin = [perdida_base * d for d in dx]
        y_con = [(perdida_base - ahorro_diario) * d for d in dx]
        
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=dx, y=y_sin, fill='tozeroy', name='Pérdida SIN Intervención', line=dict(color='#ef4444')))
        fig_sim.add_trace(go.Scatter(x=dx, y=y_con, fill='tozeroy', name='Pérdida CON Piloto', line=dict(color='#10b981')))
        fig_sim.update_layout(title="Curva de Retención de Reserva (Efecto Escudo Hídrico)", margin=dict(t=30, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_sim, use_container_width=True)

# ---------------------------------------------------------
# TAB 6: RUTA CRÍTICA
# ---------------------------------------------------------
with tabs[5]:
    st.header("Ruta Crítica de Acción: Octubre 2026 – Primer Trimestre 2027")
    
    hoy = datetime.now()
    meta = datetime(2026, 12, 31)
    dias_restantes = (meta - hoy).days
    
    st.error(f"⚠️ **¿Por qué decidir HOY? Quedan ~{max(0, dias_restantes)} días** de la ventana bimodal antes de fin de año. Si esperamos a que el embalse se seque en febrero, habremos perdido el agua. La estrategia es **cosechar en Oct-Nov y sellar inmediatamente** para el estiaje.")
    
    r1, r2, r3, r4 = st.columns(4)
    r1.info("**PASO 1: Octubre 2026**\n* Aprobación express del piloto (8 ha).\n* Regla de retención máxima de lluvias.\n* Compra de módulos flotantes rápidos (Hexa).")
    r2.success("**PASO 2: Noviembre 2026**\n* Sellado temprano del espejo de agua al alcanzar cota máxima.\n* Instalación de barreras (Booms).\n* Boya de telemetría.")
    r3.warning("**PASO 3: Diciembre 2026**\n* Defensa activa ante el inicio del verano y vientos alisios.\n* Montaje de islas solares (FPV) e interconexión a PTAP.")
    r4.error("**PASO 4: 1T 2027**\n* Superación del pico de El Niño con la reserva retenida.\n* Control de floraciones algales.\n* Expediente validado para escalar a La Fe.")

st.markdown("---")
st.caption("Plataforma de Soporte a la Decisión Socio-Hidroclimática • Corporación CuencaVerde, EPM y Alcaldía de Medellín • Octubre 2026")
