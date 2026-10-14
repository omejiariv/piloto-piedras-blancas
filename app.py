import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(page_title="Piloto Piedras Blancas", page_icon="💧", layout="wide")

# URLs Públicas de los Logos en Supabase
LOGO_CUENCA = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/CuencaVerdeLogo_V1.JPG"
LOGO_EPM = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_epm.png"
LOGO_ALCALDIA = "https://ldunpssoxvifemoyeuac.supabase.co/storage/v1/object/public/imagenes/logo_distritoMedellin.png"

# Cabezote Institucional
col1, col2, col3, col_vacia = st.columns([1, 1, 1, 10])
with col1: st.image(LOGO_CUENCA, use_container_width=True)
with col2: st.image(LOGO_EPM, use_container_width=True)
with col3: st.image(LOGO_ALCALDIA, use_container_width=True)

st.markdown("---")
st.markdown("""
# 💧 Blindaje Evaporativo: Embalse Piedras Blancas
**Alianza por la Seguridad Hídrica Territorial (Octubre 2026 - Marzo 2027)**  
*Estrategia proactiva para cosechar lluvias y sellar la lámina de agua mitigando el estiaje del fenómeno de El Niño.*
""")

# ==========================================
# TABS DE NAVEGACIÓN
# ==========================================
tab_contexto, tab_simulador, tab_ruta = st.tabs([
    "🌍 1. Contexto y Tecnologías", 
    "🎛️ 2. Simulador Interactivo", 
    "🚀 3. Ruta Crítica"
])

# --- TAB 1: CONTEXTO ---
with tab_contexto:
    st.subheader("El Efecto 'Tijera' en Piedras Blancas")
    c1, c2, c3 = st.columns(3)
    c1.info("**Asimetría del Sistema:** Capacidad de solo 0.50 Mm³ frente a los grandes embalses, exigiendo operación milimétrica.")
    c2.warning("**Efecto Bandeja:** 20 hectáreas de espejo de agua para un volumen tan bajo disparan la pérdida relativa.")
    c3.error("**El Niño:** Rompimiento nuboso a 2,350 msnm aumenta radiación y la 'sed' atmosférica (Déficit de Presión de Vapor).")
    
    st.markdown("### ¿Qué variable del Ciclo Hidrológico podemos controlar hoy?")
    st.markdown("""
    * 🌧️ **Precipitación:** Control Humano 0%. No podemos hacer llover.
    * 🌲 **Caudales Base:** Control Largo Plazo. Toma de 5 a 15 años restaurar la cuenca boscosa.
    * ☀️ **Evaporación:** **Control Directo (50%-85%)**. Cubrir el espejo de agua frena el escape físico en semanas.
    """)

# --- TAB 2: SIMULADOR ---
with tab_simulador:
    st.subheader("Simulador del Piloto y Caso de Negocio")
    
    col_ctrl, col_kpi = st.columns([1.2, 2])
    
    with col_ctrl:
        st.markdown("#### 🎚️ Parámetros de Intervención")
        area_ha = st.slider("Espejo de Agua Actual (ha):", 10.0, 28.0, 20.0, 1.0)
        pct_cob = st.slider("Cobertura del Proyecto Piloto (%):", 10, 70, 40, 5)
        
        tech = st.selectbox("Tecnología del Piloto:", [
            "⭐ Piloto Híbrido Recomendado (50% FPV + 50% Hexa)",
            "☀️ 100% Paneles Solares Flotantes (FPV)",
            "⬡ 100% Módulos Hexagonales (Despliegue Rápido)",
            "🌑 100% Esferas de Sombra Confinadas"
        ])
        
        clima = st.selectbox("Escenario Climático (Dic 26 - Mar 27):", [
            "🔥 El Niño Consolidado (~4.35 mm/día)",
            "🚨 El Niño Crítico + Vientos (~5.10 mm/día)",
            "🌤️ Media Histórica (~3.40 mm/día)"
        ])
        
        consumo_hab = st.slider("Consumo Per Cápita (L/hab-día):", 50, 300, 50, 10)
        dias_criticos = st.slider("Temporalidad / Ventana Crítica (días):", 30, 180, 60, 15)

    with col_kpi:
        # Cálculos Matemáticos replicados del HTML
        area_cubierta = area_ha * (pct_cob / 100.0)
        evap_dia = 4.35
        if "Crítico" in clima: evap_dia = 5.10
        elif "Media" in clima: evap_dia = 3.40
            
        if "Híbrido" in tech: eff, mwp, capex, pay = 0.75, 0.625, 0.36, "3.8 Años"
        elif "Solares" in tech: eff, mwp, capex, pay = 0.65, 1.25, 0.56, "3.1 Años (Ley 1715)"
        elif "Hexagonales" in tech: eff, mwp, capex, pay = 0.85, 0.0, 0.19, "7.5 Años"
        else: eff, mwp, capex, pay = 0.82, 0.0, 0.13, "6.0 Años"
            
        perdida_base_dia = evap_dia * area_ha * 10
        ahorro_dia = perdida_base_dia * (pct_cob / 100.0) * eff
        
        # Proyección en la ventana crítica
        bolsa_seguridad = ahorro_dia * 60
        agua_salvada_total = ahorro_dia * dias_criticos
        piscinas = agua_salvada_total / 2500.0
        hab_abastecidos = bolsa_seguridad / ((consumo_hab / 1000.0) * dias_criticos)
        
        mwp_tot = area_cubierta * mwp
        gwh_ano = mwp_tot * 1.35
        capex_tot = area_cubierta * capex
        
        # Renderizado de KPIs
        st.markdown("#### 📊 Impacto Proyectado")
        k1, k2 = st.columns(2)
        k1.metric(f"Agua Salvada ({dias_criticos} días)", f"{agua_salvada_total:,.0f} m³", f"~ {piscinas:.1f} Piscinas")
        k2.metric("Abastecimiento Garantizado", f"{hab_abastecidos:,.0f} Hab", f"Suministro continuo")
        
        k3, k4 = st.columns(2)
        k3.metric("Energía Limpia", f"{mwp_tot:.1f} MWp", f"~ {gwh_ano:.1f} GWh/año" if mwp_tot>0 else "Pasivo")
        k4.metric("Inversión Est. (CAPEX)", f"${capex_tot:.2f}M USD", f"ROI: {pay}", delta_color="inverse")
        
        # Gráfico dinámico
        paso = dias_criticos / 8
        dias_x = [int(i * paso) for i in range(9)]
        acum_sin = [perdida_base_dia * d for d in dias_x]
        acum_con = [(perdida_base_dia - ahorro_dia) * d for d in dias_x]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dias_x, y=acum_sin, fill='tozeroy', name='Sin Piloto', line=dict(color='#ef4444')))
        fig.add_trace(go.Scatter(x=dias_x, y=acum_con, fill='tozeroy', name='Con Piloto', line=dict(color='#10b981')))
        fig.update_layout(title="Curva de Retención de Reserva en Estiaje", margin=dict(t=30, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: RUTA CRÍTICA ---
with tab_ruta:
    st.subheader("Hoja de Ruta: Llamado a la Acción Inmediata")
    
    hoy = datetime.now()
    meta = datetime(2026, 12, 31)
    dias_restantes = (meta - hoy).days
    
    st.error(f"⏳ **URGENTE: Quedan ~{max(0, dias_restantes)} días** para aprovechar las lluvias de fin de año antes del estiaje crítico.")
    
    st.markdown("""
    * **Fase 1 (Oct 2026):** Aprobación del Piloto y estructuración de compra de módulos rápidos.
    * **Fase 2 (Nov 2026):** Retención máxima de lluvias y despliegue del sello de agua temprano.
    * **Fase 3 (Dic 2026):** Activación del escudo físico ante vientos alisios e instalación solar.
    * **Fase 4 (1T 2027):** Superación de El Niño con la reserva preservada y escalado a La Fe.
    """)
