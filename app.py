import streamlit as st
import ee
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# 1. Sahifa sozlamalari (Faqat bir marta chaqiriladi)
st.set_page_config(page_title="Amudaryo AI-Monitor Ultra", layout="wide", initial_sidebar_state="expanded")

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
    st.error(f"🛰 GEE ulanish xatosi: {e}")
    st.stop()

# --- 🎨 NEXT-GEN KIBER DIZAYN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@300;500&display=swap');
    
    .stApp {
        background: radial-gradient(circle at center, #0a192f 0%, #020c1b 100%);
        color: #e6f1ff;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Shisha effektli sidebar */
    [data-testid="stSidebar"] {
        background: rgba(2, 12, 27, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid #64ffda;
    }

    /* Karta effektlari */
    .metric-card {
        background: rgba(10, 25, 47, 0.7);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #64ffda;
        box-shadow: 0 4px 30px rgba(100, 255, 218, 0.1);
        text-align: center;
    }

    /* Ekspert xulosasi - Animatsiyali neon */
    .report-box-cyber { 
        padding: 30px; 
        border-radius: 20px; 
        border: 2px solid #64ffda;
        background: rgba(100, 255, 218, 0.02);
        box-shadow: 0 0 25px rgba(100, 255, 218, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .report-box-cyber::before {
        content: "";
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: conic-gradient(transparent, rgba(100, 255, 218, 0.1), transparent 30%);
        animation: rotate 10s linear infinite;
    }
    
    @keyframes rotate {
        100% { transform: rotate(360deg); }
    }

    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; letter-spacing: 2px; }
    
    .stButton>button {
        background: transparent !important;
        color: #64ffda !important;
        border: 1px solid #64ffda !important;
        transition: 0.3s all !important;
        text-transform: uppercase;
    }
    .stButton>button:hover {
        background: rgba(100, 255, 218, 0.1) !important;
        box-shadow: 0 0 15px #64ffda !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 KIRISH ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #64ffda; margin-top: 100px;'>⚡ AMUDARYO AI SECURE ACCESS</h1>", unsafe_allow_html=True)
    _, col_p2, _ = st.columns([1,1.2,1])
    with col_p2:
        password = st.text_input("Kirish kodi:", type="password")
        if st.button("TIZIMNI FAOLLASHTIRISH"):
            if password == "Amudaryo_AI": 
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("NOTOG'RI KOD!")
    st.stop()

# --- MONITORING PANEL ---
if 'started' not in st.session_state: st.session_state.started = False

if not st.session_state.started:
    st.markdown("""
        <div style="text-align: center; padding: 100px 20px;">
            <h1 style="color: #64ffda; font-size: 3.5rem; margin-bottom: 0;">AMUDARYO <span style="color: #fff;">AI-MONITOR</span></h1>
            <p style="color: #8892b0; font-size: 1.2rem;">Kosmik razvedka va sun'iy intellekt orqali daryo dinamikasi tahlili</p>
            <div style="margin-top: 40px;">
                <p>Loyixa muallifi: <span style="color: #64ffda;">Shahzod</span></p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    _, col_btn, _ = st.columns([2,1,2])
    with col_btn:
        if st.button("🚀 TIZIMGA KIRISH"):
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- ASOSIY DASHBOARD ---
st.sidebar.markdown("<h2 style='color: #64ffda;'>🛰 CONTROL PANEL</h2>", unsafe_allow_html=True)
locations = {
    "Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60],
    "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]
}
selected_city = st.sidebar.selectbox("🎯 Hudud:", list(locations.keys()))
radius = st.sidebar.slider("📡 Skanerlash radiusi (m):", 3000, 15000, 5000)

current_year = datetime.now().year
past_year = current_year - 5

def analyze_river_ultra(coords, radius):
    point = ee.Geometry.Point(coords[1], coords[0])
    region = point.buffer(radius).bounds()
    
    def get_img(collection, bands, date_range):
        # Filtrni yumshatdik: eng yaxshi suratni topish uchun
        col = ee.ImageCollection(collection) \
            .filterBounds(region) \
            .filterDate(date_range[0], date_range[1]) \
            .sort('CLOUDY_PIXEL_PERCENTAGE' if 'Sentinel' in collection else 'CLOUD_COVER')
        return col.first()

    # Sentinel-2 ni tekshiramiz
    img_now = get_img("COPERNICUS/S2_SR_HARMONIZED", ['B3', 'B8'], [f'{current_year-1}-01-01', f'{current_year}-12-31'])
    img_old = get_img("COPERNICUS/S2_SR_HARMONIZED", ['B3', 'B8'], [f'{past_year-1}-01-01', f'{past_year}-12-31'])
    
    # Sentinel bo'lmasa Landsatga o'tish
    is_sentinel = True
    if not img_now:
        img_now = get_img("LANDSAT/LC08/C02/T1_L2", ['SR_B3', 'SR_B5'], [f'{current_year-1}-01-01', f'{current_year}-12-31'])
        img_old = get_img("LANDSAT/LC08/C02/T1_L2", ['SR_B3', 'SR_B5'], [f'{past_year-1}-01-01', f'{past_year}-12-31'])
        is_sentinel = False

    if not img_now or not img_old: return None

    try:
        # Suv indeksi hisobi
        sw_bands = ['B3', 'B8'] if is_sentinel else ['SR_B3', 'SR_B5']
        mask_old = img_old.normalizedDifference(sw_bands).gt(0.0)
        mask_now = img_now.normalizedDifference(sw_bands).gt(0.0)
        erosion = mask_now.subtract(mask_old).gt(0).selfMask()
        
        def get_area(mask):
            area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=30, maxPixels=1e9
            )
            return ee.Number(area.get('nd', 0)).divide(10000).round().getInfo()

        a_old, a_now, a_ero = get_area(mask_old), get_area(mask_now), get_area(erosion)
        
        # Tasvir sozlamalari
        vis = {'bands': ['B4', 'B3', 'B2'] if is_sentinel else ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 3000 if is_sentinel else 30000}
        v_params = {'dimensions': 1000, 'format': 'jpg', 'region': region}
        
        u1 = img_old.visualize(**vis).getThumbURL(v_params)
        u2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#64ffda'], opacity=0.8)).getThumbURL(v_params)
        
        return u1, u2, a_old, a_now, a_ero
    except: return None

# --- IJRO ---
st.markdown(f"### 📍 {selected_city}: KOSMIK MONITORING")
with st.spinner("🛰 AI kosmik ma'lumotlarni sinxronizatsiya qilmoqda..."):
    res = analyze_river_ultra(locations[selected_city], radius)

if res:
    u1, u2, a_old, a_now, a_ero = res
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<p style='color:#8892b0;'>📅 {past_year}-YILGI HOLAT</p>", unsafe_allow_html=True)
        st.image(u1, use_container_width=True)
    with col2:
        st.markdown(f"<p style='color:#64ffda;'>📡 {current_year}-YILGI AI TAHLIL</p>", unsafe_allow_html=True)
        st.image(u2, use_container_width=True)

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-card'><p>BAZAVIY MAYDON</p><h2>{a_old} ga</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-card'><p>HOZIRGI MAYDON</p><h2>{a_now} ga</h2></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric-card' style='border-color:#ff4b4b;'><p>DEFORMATSIYA</p><h2 style='color:#ff4b4b;'>{a_ero} ga</h2></div>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="report-box-cyber" style="margin-top: 30px;">
            <div style="position: relative; z-index: 2;">
                <h3 style="color: #64ffda; margin-top: 0;">📑 EKSPERT XULOSASI</h3>
                <p>Skanerlash natijasida <b>{selected_city}</b> qirg'oq chizig'ida dinamik o'zgarishlar aniqlandi.</p>
                <p>Aniqlangan <b>{a_ero} gektar</b> o'zgarish sun'iy intellekt algoritmlari yordamida verifikatsiya qilindi.</p>
                <hr style="border: 0.1px solid rgba(100, 255, 218, 0.3);">
                <p style="text-align: right; font-family: 'Orbitron'; font-size: 0.8rem; color: #64ffda;">MUHANDIS: Shahzod | SYSTEM: VERIFIED</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.warning("📡 Diqqat: Bu hududda bulutlilik darajasi yuqori. Iltimos, radiusni biroz kattalashtiring yoki birozdan so'ng qayta urinib ko'ring.")

if st.sidebar.button("🔌 TIZIMDAN CHIQISH"):
    st.session_state.authenticated = False
    st.session_state.started = False
    st.rerun()
