import streamlit as st
import requests
import pandas as pd

# KONFIGURACE
API_KEY = st.secrets.get("MAPY_API")
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
adresa = col1.text_input("Cílová adresa", "")
spz = col2.selectbox("SPZ vozidla", list(VOZIDLA.keys()))
rok = col3.selectbox("Rok", list(reversed(range(2016, 2027))))

if st.button("🧮 SPOČÍTAT", type="primary"):
    with st.spinner("Hledám optimální trasu..."):
        try:
            # Mapy.cz ROUTING API v1
            url = f"https://api.mapy.cz/v1/routing"
            params = {
                "key": API_KEY,
                "start": START_ADDR,
                "finish": adresa,
                "vehicle": "car"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "routes" in data and len(data["routes"]) > 0:
                    route = data["routes"][0]
                    km_jedno = route["distance"] / 1000
                    min_jedno = route["duration"] / 60
                else:
                    st.warning("🗺️ Trasa nenalezena, používám Boskovice (265 km)")
                    km_jedno, min_jedno = 132.5, 160
            else:
                st.warning(f"🌐 API chyba {response.status_code}, test data")
                km_jedno, min_jedno = 132.5, 160
                
        except Exception as e:
            st.info(f"🔧 API chyba: {str(e)[:50]}... Používám test data")
            km_jedno, min_jedno = 132.5, 160
        
        # TAM A ZPĚT
        tam_zpet_km = km_jedno * 2
        tam_zpet_min = min_jedno * 2
        
        # VÝPOČET
        sazba = SAZBY_KM[rok]
        phm_cena = PHM_CENY[rok]
        spotreba = VOZIDLA[spz]["spotreba"]
        
        
        zakladni = round(tam_zpet_km * sazba)
        phm_litr = round((tam_zpet_km / 100) * spotreba, 1)
        phm_nahrada = round(phm_litr * phm_cena)
        celkem = zakladni + phm_nahrada
        
        ctvrt_hodin = round(tam_zpet_min / 15)
        pul_hodin = round(tam_zpet_min / 30) if rok >= 2026 else None
        
        # VÝSLEDEK
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📏 Vzdálenost", f"{tam_zpet_km:.0f} km")
            st.metric("⏱️ Doba jízdy", f"{tam_zpet_min//60}:{tam_zpet_min%60:02d} h")
            st.metric("💰 Náhrada", f"{celkem:,} Kč")
        
        with col2:
            st.markdown("**Detail:**")
            st.write(f"*Základní:* **{zakladni:,} Kč** ({sazba} Kč/km)")
            st.write(f"*PHM:* **{phm_nahrada:,} Kč** ({phm_litr} l × {phm_cena} Kč/l)")
            st.write(f"*Čtvrthodiny:* **{ctvrt_hodin}**")
            if pul_hodin: st.write(f"*Půlhodiny:* **{pul_hodin}** (2026+)")
        
        st.warning("⚠️ **Exekuční limit: max 1 500 Kč/cestu**")

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
