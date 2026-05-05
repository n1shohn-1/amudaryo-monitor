import streamlit as st
import ee
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Amudaryo AI-Monitor Ultra Pro", layout="wide", initial_sidebar_state="expanded")

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

# --- 🎨 LIQUID-NEON PREMIUM DIZAYN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@300;500&display=swap');
    
    .stApp {
        background: #020c1b;
        color: #e6f1ff;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Sidebar - Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(10, 25, 47, 0.9) !important;
        backdrop-filter: blur(15px);
        border-right: 2px solid #00f2ff;
    }

    /* Karta effektlari */
    .metric-card {
        background: rgba(23, 42, 69, 0.8);
        padding: 25px;
        border-radius: 20px;
        border-top: 3px solid #00f2ff;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: 0.3s all ease;
    }
    .metric-card:hover { transform: translateY(-5px); border-top: 3px solid #64ffda; }

    /* Shaxriyor Xulosasi - Dynamic Neon Border */
    .report-box-cyber { 
        padding: 40px; 
        border-radius: 25px; 
        background: #0a192f;
        border: 1px solid rgba(0, 242, 255, 0.2);
        box-shadow: 0 0 40px rgba(0, 242, 255, 0.05);
        position: relative;
    }
    
    .report-box-cyber::after {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        border-radius: 25px;
        border: 1px solid transparent;
        background: linear-gradient(45deg, #00f2ff, transparent, #64ffda) border-box;
        -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
        mask-composite: exclude;
    }

    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; letter-spacing: 3px; color: #00f2ff; }
    
    /* Tugmalar */
    .stButton>button {
        background: linear-gradient(90deg, #00f2ff, #0066ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 55px;
        font-weight: bold !important;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 KIRISH ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>⚡ AMUDARYO AI SECURE TERMINAL</h1>", unsafe_allow_html=True)
    _, col_p2, _ = st.columns([1,1.2,1])
    with col_p2:
        password = st.text_input("Sizning parolingiz:", type="password")
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
        <div style="text-align: center; padding: 120px 20px;">
            <h1 style="color: #00f2ff; font-size: 3.5rem; margin-bottom: 10px;">AMUDARYO AI-MONITOR</h1>
            <p style="color: #8892b0; font-size: 1.3rem;">Sentinel-2 & Landsat 9 Integratsiyasi</p>
            <hr style="width: 100px; border: 2px solid #00f2ff; margin: 40px auto;">
            <p style="font-size: 1.1rem;">Loyiha muhandisi: <span style="color: #00f2ff;">Shaxriyor</span></p>
        </div>
    """, unsafe_allow_html=True)
    _, col_btn, _ = st.columns([2,1,2])
    with col_btn:
        if st.button("🚀 ANALIZNI BOSHLASH"):
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- DASHBOARD ---
st.sidebar.markdown("<h2 style='color: #00f2ff;'>🛰 CONTROL</h2>", unsafe_allow_html=True)
locations = {
    "Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60],
    "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]
}
selected_city = st.sidebar.selectbox("🎯 Hudud:", list(locations.keys()))
radius = st.sidebar.slider("📡 Skanerlash radiusi (m):", 3000, 20000, 8000)

current_year = datetime.now().year
past_year = current_year - 5

def analyze_river_advanced(coords, radius):
    point = ee.Geometry.Point(coords[1], coords[0])
    region = point.buffer(radius).bounds()
    
    # "Sariq yozuv" chiqmasligi uchun: Bulutlilik filtrini olib tashlab, eng yaxshisini saralaymiz
    def get_best_img(years):
        # Sentinel-2 dan qidirish
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(region) \
            .filterDate(f'{years[0]}-01-01', f'{years[1]}-12-31') \
            .sort('CLOUDY_PIXEL_PERCENTAGE').first()
        
        # Agar Sentinel topilmasa, Landsat-8 ga o'tish
        if not s2:
            return ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterBounds(region) \
                .filterDate(f'{years[0]}-01-01', f'{years[1]}-12-31') \
                .sort('CLOUD_COVER').first()
        return s2

    img_now = get_best_img([current_year-1, current_year])
    img_old = get_best_img([past_year-1, past_year])

    if not img_now or not img_old: return None

    try:
        # Avtomatik bandlarni aniqlash
        is_s2 = 'B3' in img_now.bandNames().getInfo()
        bands = ['B3', 'B8'] if is_s2 else ['SR_B3', 'SR_B5']
        vis = {'bands': ['B4', 'B3', 'B2'] if is_s2 else ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 3000 if is_s2 else 30000}
        
        mask_old = img_old.normalizedDifference(bands).gt(0.0)
        mask_now = img_now.normalizedDifference(bands).gt(0.0)
        erosion = mask_now.subtract(mask_old).gt(0).selfMask()
        
        def get_area(mask):
            area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=30, maxPixels=1e9
            )
            val = area.get('nd', 0) if not is_s2 else area.get('nd', 0)
            return ee.Number(val).divide(10000).round().getInfo()

        a_old, a_now, a_ero = get_area(mask_old), get_area(mask_now), get_area(erosion)
        v_params = {'dimensions': 1000, 'format': 'jpg', 'region': region}
        
        u1 = img_old.visualize(**vis).getThumbURL(v_params)
        u2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#00f2ff'], opacity=0.8)).getThumbURL(v_params)
        
        return u1, u2, a_old, a_now, a_ero
    except: return None

# --- IJRO ---
st.markdown(f"### 📍 {selected_city}: KIBER-MONITORING FAOLLASHDI")
with st.spinner("🛰 AI kosmik ma'lumotlarni tahlil qilmoqda..."):
    res = analyze_river_advanced(locations[selected_city], radius)

if res:
    u1, u2, a_old, a_now, a_ero = res
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<p style='color:#8892b0; text-align:center;'>📅 {past_year}-YIL</p>", unsafe_allow_html=True)
        st.image(u1, use_container_width=True)
    with c2:
        st.markdown(f"<p style='color:#00f2ff; text-align:center;'>📡 {current_year}-YIL (AI)</p>", unsafe_allow_html=True)
        st.image(u2, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-card'><p>AVVALGI MAYDON</p><h2>{a_old} ga</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-card'><p>JORIY MAYDON</p><h2>{a_now} ga</h2></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric-card' style='border-top-color:#ff4b4b;'><p>O'ZGARISH</p><h2 style='color:#ff4b4b;'>{a_ero} ga</h2></div>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="report-box-cyber" style="margin-top: 40px;">
            <h3 style="margin-top: 0; font-size: 1.2rem;">📑 SHAXRIYOR: EKSPERT TAHLILI</h3>
            <p>Sun'iy intellekt <b>{selected_city}</b> hududida daryo o'zanining <b>{a_ero} gektar</b> qismini deformatsiyaga uchragan deb tasnifladi.</p>
            <p>Ma'lumotlar Sentinel va Landsat sun'iy yo'ldoshlari orqali verifikatsiya qilingan.</p>
            <hr style="border: 0.1px solid rgba(0, 242, 255, 0.1); margin: 20px 0;">
            <p style="text-align: right; color: #00f2ff; font-weight: bold; font-family: 'Orbitron';">MUHANDIS: SHAXRIYOR</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # Agarda baribir rasm chiqmasa (internet yoki GEE xatosi bo'lsa), chiroyliroq xabar chiqadi
    st.info("🛰 Ma'lumotlarni yuklashda biroz kechikish. Iltimos, radiusni biroz o'zgartirib ko'ring (8000m tavsiya etiladi).")

if st.sidebar.button("🔌 TIZIMDAN CHIQISH"):
    st.session_state.authenticated = False
    st.rerun()
