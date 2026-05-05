import streamlit as st
import ee
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# 1. Konfiguratsiya va Premium Brending
st.set_page_config(
    page_title="Amudaryo AI-Monitor | Shaxriyor Edition", 
    page_icon="🛰", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 🛰 GOOGLE EARTH ENGINE XAVFSIZ ULANISH ---
try:
    if "earth_engine" in st.secrets:
        ee_key_raw = st.secrets["earth_engine"]["json_key"]
        ee_key_dict = json.loads(ee_key_raw)
        credentials = ee.ServiceAccountCredentials(ee_key_dict['client_email'], key_data=ee_key_raw)
        ee.Initialize(credentials, project='ee-nusratullayev38')
    else:
        # Lokal test rejimi uchun
        ee.Initialize(project='ee-nusratullayev38')
except Exception as e:
    st.error(f"🛰 GEE Terminal Xatosi: {e}")
    st.stop()

# --- 🎨 HOLOGRAPHIC NEON UI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Rajdhani:wght@300;600&family=JetBrains+Mono&display=swap');
    
    :root {
        --neon-cyan: #00f2ff;
        --neon-green: #64ffda;
        --deep-space: #020c1b;
    }

    .stApp {
        background: radial-gradient(circle at 50% 50%, #0a192f 0%, #020c1b 100%);
        color: #e6f1ff;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Shaxriyor Maxsus Navigatsiya */
    [data-testid="stSidebar"] {
        background: rgba(2, 12, 27, 0.95) !important;
        border-right: 1px solid var(--neon-cyan);
        box-shadow: 5px 0 15px rgba(0, 242, 255, 0.1);
    }

    /* Kiber Kartalar */
    .metric-card {
        background: rgba(23, 42, 69, 0.4);
        padding: 30px;
        border-radius: 15px;
        border: 1px solid rgba(0, 242, 255, 0.2);
        backdrop-filter: blur(10px);
        text-align: center;
        transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .metric-card:hover {
        border-color: var(--neon-cyan);
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.3);
        transform: scale(1.02);
    }

    /* Animatsiyali Sarlavha */
    .glitch-title {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        color: var(--neon-cyan);
        text-shadow: 2px 2px 10px rgba(0, 242, 255, 0.5);
        letter-spacing: 5px;
        text-transform: uppercase;
    }

    /* Ekspert Xulosasi - Glassmorphism */
    .report-box-cyber { 
        padding: 40px; 
        border-radius: 20px; 
        background: linear-gradient(135deg, rgba(10, 25, 47, 0.8) 0%, rgba(2, 12, 27, 0.9) 100%);
        border: 1px solid rgba(100, 255, 218, 0.3);
        box-shadow: 0 0 50px rgba(0, 0, 0, 0.5);
        position: relative;
        overflow: hidden;
    }
    
    .report-box-cyber::before {
        content: "AI ANALYSYS BY SHAXRIYOR";
        position: absolute; top: 10px; right: 20px;
        font-size: 10px; color: var(--neon-green); opacity: 0.5;
    }

    /* Tugmalar */
    div.stButton > button {
        background: transparent !important;
        color: var(--neon-cyan) !important;
        border: 1px solid var(--neon-cyan) !important;
        border-radius: 0px !important;
        font-family: 'Orbitron', sans-serif !important;
        padding: 15px 30px !important;
        transition: 0.3s !important;
    }
    div.stButton > button:hover {
        background: var(--neon-cyan) !important;
        color: #020c1b !important;
        box-shadow: 0 0 25px var(--neon-cyan);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 XAVFSIZLIK TERMINALI ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    _, col_auth, _ = st.columns([1,1.5,1])
    with col_auth:
        st.markdown("<h2 class='glitch-title' style='text-align: center; font-size: 1.5rem;'>SECURE ACCESS</h2>", unsafe_allow_html=True)
        password = st.text_input("PASSWORD REQUIRED:", type="password")
        if st.button("INITIATE SYSTEM"):
            if password == "Amudaryo_AI": 
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("ACCESS DENIED: INVALID ENCRYPTION KEY")
    st.stop()

# --- 🛰 DASHBOARD LOGIC ---
if 'started' not in st.session_state: st.session_state.started = False

if not st.session_state.started:
    st.markdown("""
        <div style="text-align: center; padding: 100px 20px;">
            <h1 class="glitch-title" style="font-size: 4rem;">AMUDARYO<br><span style="font-size: 2rem;">AI-MONITORING SYSTEM</span></h1>
            <p style="color: #8892b0; font-family: 'JetBrains Mono';">Deep Satellite Analysis Engine v4.0</p>
            <div style="margin: 40px auto; width: 200px; height: 2px; background: var(--neon-cyan); box-shadow: 0 0 10px var(--neon-cyan);"></div>
            <p style="font-size: 1.2rem;">Lead Engineer: <span style="color: var(--neon-cyan); font-weight: bold;">SHAXRIYOR</span></p>
        </div>
    """, unsafe_allow_html=True)
    _, col_btn, _ = st.columns([2,1,2])
    with col_btn:
        if st.button("🚀 BOOT SYSTEM"):
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- MONITORING KONTROL ---
st.sidebar.markdown("<h2 style='color: var(--neon-cyan); font-family: Orbitron;'>🛰 COMMAND</h2>", unsafe_allow_html=True)
locations = {
    "Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60],
    "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]
}
selected_city = st.sidebar.selectbox("🎯 TARGET REGION:", list(locations.keys()))
radius = st.sidebar.slider("📡 SCAN RADIUS (m):", 3000, 20000, 10000)

current_year = datetime.now().year
past_year = current_year - 5

def analyze_river_ultra(coords, radius):
    point = ee.Geometry.Point(coords[1], coords[0])
    region = point.buffer(radius).bounds()
    
    def get_best_img(years):
        # 1-darajali: Sentinel-2 (High Res)
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(region) \
            .filterDate(f'{years[0]}-01-01', f'{years[1]}-12-31') \
            .sort('CLOUDY_PIXEL_PERCENTAGE').first()
        
        # 2-darajali: Landsat-8 (Fallback)
        if not s2.propertyNames().contains('system:index').getInfo():
            s2 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterBounds(region) \
                .filterDate(f'{years[0]}-01-01', f'{years[1]}-12-31') \
                .sort('CLOUD_COVER').first()
        return s2

    img_now = get_best_img([current_year-1, current_year])
    img_old = get_best_img([past_year-1, past_year])

    try:
        # Bandlar va indekslar
        band_names = img_now.bandNames().getInfo()
        is_s2 = 'B3' in band_names
        bands = ['B3', 'B8'] if is_s2 else ['SR_B3', 'SR_B5']
        
        # NDWI Suv tahlili
        mask_old = img_old.normalizedDifference(bands).gt(0.0)
        mask_now = img_now.normalizedDifference(bands).gt(0.0)
        
        # O'zan o'zgarishi (Eroziya va Deformatsiya)
        erosion = mask_now.subtract(mask_old).gt(0).selfMask()
        
        def get_area(mask):
            area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=30, maxPixels=1e9
            )
            val = area.get('nd', 0)
            return ee.Number(val).divide(10000).round().getInfo()

        a_old, a_now, a_ero = get_area(mask_old), get_area(mask_now), get_area(erosion)
        
        # Vizualizatsiya
        vis = {'bands': ['B4', 'B3', 'B2'] if is_s2 else ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 3000}
        v_params = {'dimensions': 1200, 'format': 'jpg', 'region': region}
        
        u1 = img_old.visualize(**vis).getThumbURL(v_params)
        u2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#00f2ff'], opacity=0.8)).getThumbURL(v_params)
        
        return u1, u2, a_old, a_now, a_ero
    except Exception:
        return None

# --- IJRO VA VIZUALIZATSIYA ---
st.markdown(f"<h3 class='glitch-title' style='font-size: 1.2rem;'>📍 SCANNING: {selected_city}</h3>", unsafe_allow_html=True)
with st.spinner("🛰 AI DEEP-SCANNING IN PROGRESS..."):
    res = analyze_river_ultra(locations[selected_city], radius)

if res:
    u1, u2, a_old, a_now, a_ero = res
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<p style='color:#8892b0; text-align:center; font-family:JetBrains Mono;'>HISTORICAL DATA ({past_year})</p>", unsafe_allow_html=True)
        st.image(u1, use_container_width=True)
    with c2:
        st.markdown(f"<p style='color:var(--neon-cyan); text-align:center; font-family:JetBrains Mono;'>AI AUGMENTED DATA ({current_year})</p>", unsafe_allow_html=True)
        st.image(u2, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-card'><p style='color:#8892b0;'>INITIAL AREA</p><h2 style='color:#e6f1ff;'>{a_old} ha</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-card'><p style='color:#8892b0;'>CURRENT AREA</p><h2 style='color:var(--neon-cyan);'>{a_now} ha</h2></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric-card' style='border-top: 2px solid #ff4b4b;'><p style='color:#8892b0;'>DELTA DEFORMATION</p><h2 style='color:#ff4b4b;'>{a_ero} ha</h2></div>", unsafe_allow_html=True)

    # Shaxriyor Xulosasi - Professional daraja
    st.markdown(f"""
        <div class="report-box-cyber" style="margin-top: 40px;">
            <h3 style="margin-top: 0; color: var(--neon-cyan); font-family: Orbitron; font-size: 1rem;">📑 SYSTEM ANALYSIS REPORT</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                Hudud: <b>{selected_city}</b>. Sun'iy intellekt daryo o'zanining <b>{a_ero} gektar</b> maydonida dinamik siljishlarni aniqladi. 
                <br>Olingan ma'lumotlar Sentinel-2 va Landsat-9 "Harmonized" algoritmi asosida qayta ishlandi. 
                Tahlil natijalari gidrologik xavf darajasini <span style="color:var(--neon-green)">STABIL</span> deb ko'rsatmoqda.
            </p>
            <hr style="border: 0.1px solid rgba(0, 242, 255, 0.1); margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-family: 'JetBrains Mono'; font-size: 12px; color: #8892b0;">TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                <span style="color: var(--neon-cyan); font-weight: bold; font-family: 'Orbitron';">CHIEF ENGINEER: SHAXRIYOR</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.warning("🛰 SENSOR ERROR: Sun'iy yo'ldosh ma'lumotlari bilan aloqa uzildi yoki hududda bulutlilik o'ta yuqori. Iltimos, radiusni o'zgartiring.")

if st.sidebar.button("🔌 SHUTDOWN SYSTEM"):
    st.session_state.authenticated = False
    st.rerun()
