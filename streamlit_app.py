import streamlit as st
import requests
import math

# KONFIGURACE
API_KEY = st.secrets.get("MAPY_API")
HEADERS = {"Referer": "https://206cestovne.streamlit.app/"}
START_ADDR = "Šátalská 469/1, Praha 4, 14100 Praha"

# VOZIDLA uživatele
VOZIDLA = {
    "6AB3517": {"model": "Hyundai i30", "spotreba": 5.9, "phm": "BA95"},
    "8AA1204": {"model": "Škoda Fabia", "spotreba": 4.5, "phm": "BA95"},
    "6SR7185": {"model": "MG HS", "spotreba": 7.6, "phm": "BA95"}
}

# SAZBY MPSV 2016-2026 (oficiální vyhlášky)
VYHLASKY = {
    2016: "385/2015 Sb.", 2017: "440/2016 Sb.", 2018: "463/2017 Sb.", 2019: "333/2018 Sb.",
    2020: "358/2019 Sb.", 2021: "589/2020 Sb.", 2022: "511/2021 Sb.", 2023: "467/2022 Sb.",
    2024: "398/2023 Sb.", 2025: "475/2024 Sb.", 2026: "573/2025 Sb."
}
SAZBY_KM = {
    2016: 3.80, 2017: 3.90, 2018: 4.00, 2019: 4.10, 2020: 4.20,
    2021: 4.40, 2022: 4.70, 2023: 5.20, 2024: 5.60, 2025: 5.80, 2026: 5.90
}

PHM_CENY = {  # BA95 benzín – průměrná cena dle MPSV vyhlášky (Kč/l)
    2016: 29.50, 2017: 29.50, 2018: 30.50, 2019: 33.10, 2020: 32.00,
    2021: 27.80, 2022: 37.10, 2023: 41.20, 2024: 38.20, 2025: 35.80, 2026: 34.70
}


def cz(cislo, des=2):
    """Formátuje číslo s českou desetinnou čárkou a mezerou jako oddělovačem tisíců."""
    formatted = f"{cislo:,.{des}f}"          # 1,234.56
    formatted = formatted.replace(",", " ")  # 1 234.56
    formatted = formatted.replace(".", ",")  # 1 234,56
    return formatted


def geocode(adresa, api_key):
    url = "https://api.mapy.cz/v1/geocode"
    params = {"apikey": api_key, "query": adresa, "limit": 1}
    r = requests.get(url, params=params, headers=HEADERS, timeout=10)
    data = r.json()
    item = data["items"][0]
    return item["position"]["lon"], item["position"]["lat"]


def get_route(start_addr, end_addr, api_key):
    slon, slat = geocode(start_addr, api_key)
    elon, elat = geocode(end_addr, api_key)
    url = "https://api.mapy.cz/v1/routing/route"
    params = {
        "apikey": api_key,
        "start": f"{slon},{slat}",
        "end": f"{elon},{elat}",
        "routeType": "car_fast",
        "lang": "cs"
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=10)
    data = r.json()
    km = data["length"] / 1000
    min_ = data["duration"] / 60
    return km, min_


def vygeneruj_pune(r):
    """Vygeneruje text PUNE věty z dict r (výsledky výpočtu)."""
    rok = r["rok"]
    adresa = r["adresa"]
    km = r["tam_zpet_km"]
    model = r["model"]
    spotreba = r["spotreba"]
    sazba = r["sazba"]
    phm_cena = r["phm_cena"]
    zakladni = r["zakladni"]
    phm_litr = r["phm_litr"]
    phm_nahrada = r["phm_nahrada"]
    hod = r["hod"]
    min_ = r["min_"]
    pracovnici = r["pracovnici"]
    vyhlaska = r["vyhlaska"]

    if pracovnici == 1:
        ucastnil = "Šetření se účastnil"
        prac_text = "jeden pracovník soudního exekutora"
    elif pracovnici == 2:
        ucastnil = "Šetření se účastnili"
        prac_text = "dva pracovníci soudního exekutora"
    else:
        ucastnil = "Šetření se účastnili"
        prac_text = "tři pracovníci soudního exekutora"
    prac_text2 = "1 pracovník" if pracovnici == 1 else ("2 pracovníci" if pracovnici == 2 else "3 pracovníci")

    if rok >= 2026:
        jednotky = r["pul_hodin"]
        sazba_casu = 150
        max_na_pracovnika = 1000
        jednotka_text = "půlhodin"
    else:
        jednotky = r["ctvrt_hodin"]
        sazba_casu = 50
        max_na_pracovnika = 500
        jednotka_text = "čtvrthodin"

    nahrada_na_pracovnika = min(jednotky * sazba_casu, max_na_pracovnika)
    nahrada_cas_celkem = nahrada_na_pracovnika * pracovnici

    if nahrada_na_pracovnika == max_na_pracovnika:
        vypocet_cas = (
            f"{prac_text2} × {jednotky} {jednotka_text} × {sazba_casu} Kč"
            f", omezeno na max. {cz(max_na_pracovnika, 0)} Kč/pracovník"
        )
    else:
        vypocet_cas = f"{prac_text2} × {jednotky} {jednotka_text} × {sazba_casu} Kč"

    veta = (
        f"V roce {rok} bylo provedeno místní šetření na adrese {adresa}. "
        f"Cesta ze sídla soudního exekutora a zpět činila {cz(km, 0)} km. "
        f"Při provedení výjezdu bylo využito osobní vozidlo {model}. "
        f"Dle technického průkazu činí kombinovaná spotřeba {cz(spotreba, 1)} l/100 km. "
        f"Pohonnou hmotou vozidla je Benzin 95. "
        f"S ohledem na výše uvedené má soudní exekutor nárok na základní náhradu ve výši "
        f"{cz(zakladni)} Kč ({cz(km, 0)} km × {cz(sazba, 2)} Kč) "
        f"a náhradu za spotřebované pohonné hmoty ve výši {cz(phm_nahrada)} Kč "
        f"({cz(km, 0)} km × {cz(spotreba, 1)} l/100 km × {cz(phm_cena, 2)} Kč). "
        f"Dle vyhlášky Ministerstva práce a sociálních věcí č. {vyhlaska} činí sazba základní náhrady "
        f"za 1 km jízdy {cz(sazba, 2)} Kč a výše průměrné ceny Benzinu 95 činí {cz(phm_cena, 2)} Kč. "
        f"Cesta trvala celkem {hod} hodin a {min_:02d} minut, "
        f"bylo tedy započato {jednotky} {jednotka_text}. "
        f"{ucastnil} {prac_text}. "
        f"Vzhledem k tomuto má soudní exekutor nárok na náhradu za ztrátu času, "
        f"která činí {cz(nahrada_cas_celkem, 0)} Kč ({vypocet_cas})."
    )
    return veta, nahrada_cas_celkem


# ─── STREAMLIT UI ────────────────────────────────────────────────────────────

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
            km_jedno, min_jedno = get_route(START_ADDR, adresa, API_KEY)
        except Exception as e:
            st.warning(f"🌐 API chyba: {str(e)[:80]}... Používám test data")
            km_jedno, min_jedno = 132.5, 160

        tam_zpet_km = km_jedno * 2
        tam_zpet_min = min_jedno * 2

        sazba = SAZBY_KM[rok]
        phm_cena = PHM_CENY[rok]
        spotreba = VOZIDLA[spz]["spotreba"]
        model = VOZIDLA[spz]["model"]

        zakladni = round(tam_zpet_km * sazba, 2)
        phm_litr = (tam_zpet_km / 100) * spotreba
        phm_nahrada = round(phm_litr * phm_cena, 2)
        celkem = math.ceil(zakladni + phm_nahrada)

        ctvrt_hodin = round(tam_zpet_min / 15) if rok < 2026 else None
        pul_hodin = round(tam_zpet_min / 30) if rok >= 2026 else None
        hod = int(tam_zpet_min // 60)
        min_ = int(tam_zpet_min % 60)

        st.session_state["vysledky"] = {
            "rok": rok,
            "adresa": adresa,
            "tam_zpet_km": tam_zpet_km,
            "model": model,
            "spotreba": spotreba,
            "sazba": sazba,
            "phm_cena": phm_cena,
            "zakladni": zakladni,
            "phm_litr": phm_litr,
            "phm_nahrada": phm_nahrada,
            "celkem": celkem,
            "ctvrt_hodin": ctvrt_hodin,
            "pul_hodin": pul_hodin,
            "hod": hod,
            "min_": min_,
            "pracovnici": st.session_state.get("pracovnici_radio", 1),
            "vyhlaska": VYHLASKY[rok],
        }

# ─── VÝSLEDKY + PUNE ─────────────────────────────────────────────────────────
if "vysledky" in st.session_state:
    r = st.session_state["vysledky"]

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📏 Vzdálenost tam + zpět", f"{cz(r['tam_zpet_km'], 0)} km")
        st.metric("⏱️ Doba jízdy", f"{r['hod']}:{r['min_']:02d} h")
        st.metric("💰 Náhrada km + PHM", f"{cz(r['celkem'], 0)} Kč")
    with col2:
        st.markdown("**Detail:**")
        st.write(f"*Základní:* **{cz(r['zakladni'])} Kč** ({cz(r['sazba'], 2)} Kč/km)")
        st.write(f"*PHM:* **{cz(r['phm_nahrada'])} Kč** ({cz(r['phm_litr'], 2)} l × {cz(r['phm_cena'], 2)} Kč/l)")
        if r["rok"] >= 2026:
            st.write(f"*Půlhodiny:* **{r['pul_hodin']}** × 150 Kč (max 1 000 Kč/pracovník)")
        else:
            st.write(f"*Čtvrthodiny:* **{r['ctvrt_hodin']}** × 50 Kč (max 500 Kč/pracovník)")

    st.warning("⚠️ **Exekuční limit: max 1 500 Kč/cestu**")

    # ─── PUNE VĚTA ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📄 Věta pro PUNE")

    pracovnici = st.radio(
        "Počet pracovníků soudního exekutora:",
        options=[1, 2, 3],
        format_func=lambda x: {1: "1 pracovník", 2: "2 pracovníci", 3: "3 pracovníci"}[x],
        horizontal=True,
        key="pracovnici_radio"
    )

    # Aktualizovat počet pracovníků v session_state a vygenerovat větu
    r["pracovnici"] = pracovnici
    veta, nahrada_cas = vygeneruj_pune(r)

    st.info(veta)
    st.caption(f"💼 Náhrada za ztrátu času celkem: **{cz(nahrada_cas, 0)} Kč**")
    st.markdown("*Zkopírujte text níže:*")
    st.code(veta, language=None)

# ─── INFO PANEL ──────────────────────────────────────────────────────────────
with st.expander("ℹ️ O aplikaci"):
    st.markdown("""
    **Funkce:**
    - Mapy.cz API routy (tam-zpět)
    - MPSV sazby 2016–2026
    - Vozidla: Fabia 4.5l, i30 5.9l, MG HS 7.6l
    - Čtvrthodiny (do 2025, max 500 Kč/prac.) + půlhodiny (od 2026, max 1 000 Kč/prac.)
    - Generátor věty pro PUNE s volbou počtu pracovníků

    **Deploy:** `pip install streamlit requests`, `streamlit run app.py`
    """)

st.caption("🎯 Exekutorský úřad Mgr. Jana Škarpy, Šátalská 469/1, Praha 4")
