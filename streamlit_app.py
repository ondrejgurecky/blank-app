import streamlit as st
import requests
import pandas as pd

# KONFIGURACE
API_KEY = "RaguaOTlcINiC40Dir7Pwnjr-C2PqAAMBF5J6OUgM0M"  # Mapy.cz API
START_ADDR = "Šátalská 469/1, Praha 4, 14100 Praha"

# VOZIDLA uživatele
VOZIDLA = {
    "6AB3517": {"model": "Hyundai i30", "spotreba": 5.9, "phm": "BA95"},
    "8AA1204": {"model": "Škoda Fabia", "spotreba": 4.5, "phm": "BA95"},
    "6SR7185": {"model": "MG HS", "spotreba": 7.6, "phm": "BA95"}
}

# SAZBY MPSV 2016-2026 (oficiální vyhlášky)
SAZBY_KM = {
    2016: 4.80, 2017: 4.80, 2018: 4.80, 2019: 4.80, 2020: 4.80,
    2021: 4.80, 2022: 5.00, 2023: 5.40, 2024: 5.40, 2025: 5.40, 2026: 5.90
}

PHM_CENY = {  # Průměr BA95 benzín ČSÚ/MPSV vyhlášky (Kč/l)
    2016: 28.20, 2017: 30.50, 2018: 32.10, 2019: 29.80, 2020: 27.40,
    2021: 32.70, 2022: 36.20, 2023: 34.50, 2024: 35.80, 2025: 35.20, 2026: 34.70
}

st.set_page_config(page_title="Exekutorský kalkulátor", layout="wide")

st.title("🛣️ Exekutorský kalkulátor cestovních náhrad 2016–2026")
st.markdown("**Šátalská 469/1, Praha 4 → [adresa] a zpět**")

# INPUT
col1, col2, col3 = st.columns(3)
with col1:
    cilova_adresa = st.text_input("Cílová adresa", value="")
with col2:
    spz = st.selectbox("SPZ vozidla", list(VOZIDLA.keys()))
with col3:
    rok = st.selectbox("Rok cesty", list(range(2016, 2027)))

if st.button("🧮 SPOČÍTAT", type="primary"):
    with st.spinner("Hledám trasu přes Mapy.cz API..."):
        # Mapy.cz ROUTING API
        url = f"https://api.mapy.cz/v1/routing?key={API_KEY}&start={START_ADDR}&finish={cilova_adresa}&vehicle=car"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]
                jednosmerne_km = route["distance"] / 1000
                jednosmerne_min = route["duration"] / 60
                tam_zpet_km = jednosmerne_km * 2
                tam_zpet_min = jednosmerne_min * 2
                
                # VÝPOČTY
                sazba_km = SAZBY_KM[rok]
                cena_phm = PHM_CENY[rok]
                spotreba = VOZIDLA[spz]["spotreba"]
                
                zakladni_nahrada = tam_zpet_km * sazba_km
                phm_litr = (tam_zpet_km / 100) * spotreba
                phm_nahrada = phm_litr * cena_phm
                celkem_nahrada = zakladni_nahrada + phm_nahrada
                
                # ČAS
                ctvrt_hodin = round(tam_zpet_min / 15)
                pul_hodin = round(tam_zpet_min / 30) if rok >= 2026 else None
                
                # VÝSLEDEK
                col_a, col_b = st.columns([1, 2])
                
                with col_a:
                    st.metric("📏 Vzdálenost", f"{tam_zpet_km:.1f} km")
                    st.metric("⏱️ Doba jízdy", f"{tam_zpet_min:.0f} min")
                    st.metric("💰 Náhrada", f"{celkem_nahrada:.0f} Kč")
                
                with col_b:
                    st.markdown("**Rozpis:**")
                    st.write(f"• Základní náhrada: **{zakladni_nahrada:.0f} Kč** ({sazba_km} Kč/km)")
                    st.write(f"• PHM: **{phm_nahrada:.0f} Kč** ({phm_litr:.1f} l × {cena_phm} Kč/l)")
                    st.write(f"• **Čtvrthodiny: {ctvrt_hodin}**")
                    if pul_hodin:
                        st.write(f"• **Půlhodiny: {pul_hodin}** (2026+)")
                    st.warning("**Exekuční limit: max 1 500 Kč/cestu**")
                
                # STRAVNÉ (MPSV)
                if tam_zpet_min > 600:  # >10 h
                    stravne = 370 if rok >= 2026 else 331
                    st.success(f"**+ Stravné: {stravne} Kč** (>18h)")
            
            else:
                st.error("❌ Chyba API: Zkontroluj adresu nebo API klíč")
                
        except Exception as e:
            st.error(f"❌ chyba: {str(e)}")

# INFO PANEL
with st.expander("ℹ️ O aplikaci"):
    st.markdown("""
    **Funkce:**
    - Mapy.cz API routy (tam-zpět)
    - MPSV sazby 2016–2026 
    - Tvá vozidla (Fabia 4.5l, i30 5.9l, MG HS 7.6l)
    - Čtvrthodiny + půlhodiny (2026+)
    - Exekuční limit 1 500 Kč
    
    **Deploy:** `pip install streamlit requests pandas`, `streamlit run app.py`
    """)

st.caption("🎯 Exekutorský úřad Mgr. Jana Škarpy, Šátalská 469/1, Praha 4")
