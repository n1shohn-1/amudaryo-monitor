import streamlit as st
import ee
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. SAHIFA SOZLAMALARI
st.set_page_config(
    page_title="Amudaryo AI-DeformRisk | Shaxriyor",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🛰 GOOGLE EARTH ENGINE ULANISHI ---
try:
    if "earth_engine" in st.secrets:
        ee_key_raw = st.secrets["earth_engine"]["json_key"]
        ee_key_dict = json.loads(ee_key_raw)
        credentials = ee.ServiceAccountCredentials(ee_key_dict['client_email'], key_data=ee_key_raw)
        ee.Initialize(credentials, project='ee-nusratullayev38')
    else:
        ee.Initialize(project='ee-nusratullayev38')
except Exception as e:
    st.error(f"🛰 Tizimga ulanishda xatolik: {e}")
    st.stop()

# --- 🎨 MODERN CYBER-UZBEK DIZAYNI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: rgba(10, 25, 47, 0.95) !important;
        border-right: 2px solid #00f2ff;
    }

    .metric-card {
        background: rgba(16, 33, 65, 0.8); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
    }

    .report-box {
        background: rgba(2, 12, 27, 0.85); padding: 30px; border-radius: 20px;
        border-left: 5px solid #ff4b4b; backdrop-filter: blur(10px); margin-top: 20px;
    }

    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; text-transform: uppercase; }

    .stButton>button {
        width: 100%; background: transparent !important; color: #00f2ff !important;
        border: 2px solid #00f2ff !important; font-family: 'Orbitron', sans-serif; transition: 0.4s;
    }
    .stButton>button:hover { background: #00f2ff !important; color: #000 !important; box-shadow: 0 0 20px #00f2ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 XAVFSIZLIK TIZIMI ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    _, col_auth, _ = st.columns([1,1.2,1])
    with col_auth:
        st.markdown("<h2 style='text-align: center;'>TIZIMGA KIRISH</h2>", unsafe_allow_html=True)
        pw = st.text_input("MAXFIY KALIT (Shahzod):", type="password")
        if st.button("FAOLLASHTIRISH"):
            if pw == "Amudaryo_AI":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Xato kalit kiritildi!")
    st.stop()

# --- 🛰 BOSHQARUV PANELI ---
st.sidebar.image("https://img.icons8.com/fluency/96/river.png", width=80)
st.sidebar.markdown("### 🛠 TIZIM BOSHQARUVI")
locations = {"Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60], "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]}
city = st.sidebar.selectbox("HUDUDNI TANLANG:", list(locations.keys()))
radius = st.sidebar.slider("SKANERLASH RADIUSI (M):", 1000, 15000, 5000)

current_year = datetime.now().year
past_year = current_year - 7 # 7 yillik tahlil

# --- 🧠 ASOSIY ANALIZ ALGORITMI ---
def analyze_deform(coords, rad):
    try:
        point = ee.Geometry.Point(coords[1], coords[0])
        region = point.buffer(rad).bounds()
        
        def fetch_img(year):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region) \
                .filterDate(f'{year}-01-01', f'{year}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE').first()

        img_old = fetch_img(past_year)
        img_now = fetch_img(current_year)

        if not img_old or not img_now: return None

        # NDWI - Suvni aniqlash
        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.1)

        # Eroziya va Qurishni aniqlash (Sizning 1-kodingizdagi mantiq)
        erosion = mask_now.subtract(mask_old).gt(0).selfMask() # Yangi suv (Yemirilish)
        retreat = mask_old.subtract(mask_now).gt(0).selfMask() # Suv chekinishi (Qurish)

        def calc_area(m):
            area = m.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=10, maxPixels=1e9
            )
            return ee.Number(area.get('nd', 0)).divide(10000).round().getInfo()

        a_old, a_now = calc_area(mask_old), calc_area(mask_now)
        a_ero, a_ret = calc_area(erosion), calc_area(retreat)
        
        # Vizualizatsiya
        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
        url1 = img_old.visualize(**vis).getThumbURL({'dimensions': 1000, 'region': region})
        # 2-rasmda: Ko'k - Yemirilish, Sariq - Qurish
        url2 = img_now.visualize(**vis) \
            .blend(erosion.visualize(palette=['#00f2ff'], opacity=0.7)) \
            .blend(retreat.visualize(palette=['#ffff00'], opacity=0.7)) \
            .getThumbURL({'dimensions': 1000, 'region': region})
        
        return url1, url2, a_old, a_now, a_ero, a_ret
    except: return None

# --- 🚀 NATIJALAR ---
st.markdown(f"<h1>🌊 AMUDARYO AI-DEFORMRISK MONITOR PRO</h1>", unsafe_allow_html=True)

with st.spinner("🛰 Sun'iy yo'ldosh bilan kvant aloqa o'rnatilmoqda..."):
    res = analyze_deform(locations[city], radius)

if res:
    u1, u2, a1, a2, a_ero, a_ret = res
    diff = a2 - a1
    
    # METRIKALAR
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-card'><p>{past_year} MAYDONI</p><h2>{a1} GA</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-card'><p>{current_year} MAYDONI</p><h2>{a2} GA</h2></div>", unsafe_allow_html=True)
    with m3: 
        status_color = "#00f2ff" if diff >= 0 else "#ff4b4b"
        st.markdown(f"<div class='metric-card'><p>DINAMIKA</p><h2 style='color:{status_color};'>{diff:+} GA</h2></div>", unsafe_allow_html=True)

    # RASMLAR
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<p style='text-align:center;'>📅 {past_year}-YILGI HOLAT</p>", unsafe_allow_html=True)
        st.image(u1, use_container_width=True)
    with c2:
        st.markdown(f"<p style='text-align:center; color:#00f2ff;'>📅 {current_year}-YIL (AI ANALIZ: 🔵Yemirilish 🟡Qurish)</p>", unsafe_allow_html=True)
        st.image(u2, use_container_width=True)

    # GRAFIK
    st.divider()
    df_chart = pd.DataFrame({'Yil': [str(past_year), str(current_year)], 'Maydon': [a1, a2]})
    fig = px.line(df_chart, x='Yil', y='Maydon', markers=True, title="Suv Havzasi Dinamikasi", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # EKSPERT XULOSASI
    st.markdown(f"""
        <div class="report-box">
            <h3 style='color: #ff4b4b;'>📑 EKSPERTIZANING RASMIY BAYONNOMASI</h3>
            <p style="font-size: 1.1rem;">
                <b>{city}</b> hududi bo'yicha o'tkazilgan AI-monitoring natijasida quyidagilar aniqlandi:<br>
                1. Oxirgi yillarda daryo o'zanining <b>{a_ero} gektar</b> qismi yemirilishga (eroziya) uchragan (ko'k zonalar).<br>
                2. <b>{a_ret} gektar</b> maydonda suv chekinishi va yangi quruqlik qatlamlari hosil bo'lgan (sariq zonalar).<br>
                3. Umumiy balans: Daryo maydoni {abs(diff)} gektarga {'ortgan' if diff > 0 else 'kamaygan'}.
            </p>
            <hr style="border-color: rgba(255, 75, 75, 0.2);">
            <div style="display: flex; justify-content: space-between; font-family: 'Orbitron'; font-size: 0.8rem;">
                <span>ID: AMU-AI-2026-{city.upper()}</span>
                <span style="color: #00f2ff;">BOSH MUHANDIS: SHAHZOD</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ SENSOR XATOSI: Hududda bulutlilik yuqori yoki GEE ruxsatida muammo. Radiusni o'zgartirib ko'ring.")

if st.sidebar.button("🔌 TIZIMNI O'CHIRISH"):
    st.session_state.auth = False
    st.rerun()
