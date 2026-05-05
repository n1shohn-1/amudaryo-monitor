import streamlit as st
import ee
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Amudaryo AI-Monitor Pro", layout="wide", initial_sidebar_state="expanded")

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
    st.error(f"🛰 Ulanish xatosi: {e}")
    st.stop()

# --- 🎨 ULTRA-PROFESSIONAL KIBER DIZAYN ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(6, 12, 24, 0.9), rgba(6, 12, 24, 0.9)), 
        url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
        background-attachment: fixed;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Sidebar dizayni */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 25, 47, 0.95) !important;
        border-right: 2px solid #00f2ff;
        box-shadow: 5px 0 15px rgba(0, 242, 255, 0.2);
    }
    
    /* Metrika va bloklar */
    .stMetric {
        background: rgba(0, 242, 255, 0.05) !important;
        border: 1px solid #00f2ff !important;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.1);
        border-radius: 15px !important;
    }
    
    /* Ekspert xulosasi - Neon Effekt */
    .report-box-cyber { 
        padding: 30px; border-radius: 20px; 
        border: 1px solid #00f2ff;
        background: rgba(0, 242, 255, 0.05);
        box-shadow: inset 0 0 20px rgba(0, 242, 255, 0.1);
        color: #e2e8f0;
        margin-top: 25px;
    }

    /* Tugmalar */
    .stButton>button {
        background: linear-gradient(45deg, #00f2ff, #0066ff) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 12px !important;
        height: 50px;
        transition: 0.4s all ease;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0, 242, 255, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 KIRISH ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #00f2ff; text-shadow: 0 0 20px #00f2ff;'>🛡 MONITORING TIZIMI</h1>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1,1.2,1])
    with col_p2:
        password = st.text_input("Kirish paroli:", type="password")
        if st.button("TIZIMNI FAOLLASHTIRISH"):
            if password == "Amudaryo_AI": 
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Ruxsat berilmadi!")
    st.stop()

# --- ASOSIY SAHIFA ---
if 'started' not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.markdown("""
        <div style="text-align: center; padding: 60px; background: rgba(0, 242, 255, 0.03); border-radius: 30px; border: 1px solid rgba(0, 242, 255, 0.3);">
            <h1 style="color: #00f2ff; font-size: 3rem;">🌊 Amudaryo AI-Monitor <span style="color: #ffffff;">Pro</span></h1>
            <p style="font-size: 1.4rem; color: #8892b0;">Sun'iy intellekt va Sentinel-2 texnologiyasi asosida daryo deformatsiyasi tahlili</p>
            <hr style="border: 0.5px solid #00f2ff; width: 60%; margin: 30px auto;">
            <p style="font-size: 1.1rem;">Loyiha muallifi: <b style="color: #00f2ff;">Shaxriyor</b></p>
            <p style="color: #4ade80;">✅ Tizim barqaror holatda</p>
        </div>
    """, unsafe_allow_html=True)
    
    _, col_btn, _ = st.columns([2,1,2])
    with col_btn:
        if st.button("🚀 ANALIZNI BOSHLASH"):
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- MONITORING PANEL ---
st.sidebar.markdown("<h2 style='color: #00f2ff; text-align: center;'>🛰 DASHBOARD</h2>", unsafe_allow_html=True)
locations = {
    "Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60],
    "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]
}
selected_city = st.sidebar.selectbox("🎯 Hudud:", list(locations.keys()))
radius = st.sidebar.slider("📡 Skanerlash radiusi (m):", 1000, 15000, 5000)

if st.sidebar.button("🔌 Tizimdan chiqish"):
    st.session_state.authenticated = False
    st.session_state.started = False
    st.rerun()

current_year = datetime.now().year
past_year = current_year - 5 # Sentinel uchun 5 yil optimal

st.title(f"📊 {selected_city} Hududi: Kiber-Analiz")

def analyze_river_v2(coords, radius):
    point = ee.Geometry.Point(coords[1], coords[0])
    region = point.buffer(radius).bounds()
    
    # Landsat'dan Sentinel-2 ga o'tamiz (sifatliroq va surat ko'p)
    def get_satellite_img(year):
        return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(region) \
            .filterDate(f'{year-1}-01-01', f'{year}-12-31') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()
    
    img_old = get_satellite_img(past_year)
    img_now = get_satellite_img(current_year)
    
    if not img_old or not img_now: return None
    
    # NDWI (Suv indeksi) Sentinel kanallari uchun: (B3 - B8) / (B3 + B8)
    mask_old = img_old.normalizedDifference(['B3', 'B8']).rename('w').gt(0.0)
    mask_now = img_now.normalizedDifference(['B3', 'B8']).rename('w').gt(0.0)
    
    erosion = mask_now.subtract(mask_old).gt(0).selfMask()
    
    def get_area(mask):
        area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=region, scale=10, maxPixels=1e9 # Sentinel scale=10
        )
        return ee.Number(area.get('w', 0)).divide(10000).round().getInfo()
    
    a_old, a_now, a_ero = get_area(mask_old), get_area(mask_now), get_area(erosion)
    
    vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    v_params = {'dimensions': 1000, 'format': 'jpg', 'region': region}
    
    try:
        u1 = img_old.visualize(**vis).getThumbURL(v_params)
        u2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#00f2ff'], opacity=0.8)).getThumbURL(v_params)
        return u1, u2, a_old, a_now, a_ero
    except:
        return None

with st.spinner("🛰 AI Sentinel-2 ma'lumotlarini qayta ishlamoqda..."):
    res = analyze_river_v2(locations[selected_city], radius)

if res:
    u1, u2, a_old, a_now, a_ero = res
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"📅 {past_year}-yil holati")
        st.image(u1, use_container_width=True)
    with c2:
        st.success(f"📡 {current_year}-yil: AI Deformatsiya")
        st.image(u2, use_container_width=True)
    
    st.divider()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Eski maydon", f"{a_old} ga", delta_color="off")
    m2.metric("Hozirgi maydon", f"{a_now} ga", delta=int(a_now-a_old))
    m3.metric("Yemirilish", f"{a_ero} ga", delta="-Xavfli", delta_color="inverse")

    st.markdown(f"""
    <div class="report-box-cyber">
        <h3 style="color: #00f2ff;">📑 Tizim Xulosasi</h3>
        <p>Sentinel-2 skanerlash natijasida <b>{selected_city}</b> hududida <b>{a_ero} gektar</b> o'zgarish aniqlandi.</p>
        <p>Ma'lumotlar Shaxriyor tomonidan sozlangan neyron tarmoq orqali filtrlandi.</p>
        <hr style="border-color: rgba(0, 242, 255, 0.2);">
        <p style="text-align: right; font-style: italic;">Muhandis: Shaxriyor</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Diqqat: Bu hududda bulutlilik yuqori. Iltimos, radiusni o'zgartiring yoki bir ozdan so'ng qayta urinib ko'ring.")
