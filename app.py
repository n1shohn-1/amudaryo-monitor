import streamlit as st
import ee
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. SAHIFA SOZLAMALARI (ASL DIZAYN)
st.set_page_config(
    page_title="Amudaryo AI-Monitor | Shahzod",
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

# --- 🎨 ASL CYBER-UZBEK DIZAYNI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }
    [data-testid="stSidebar"] {
        background: rgba(10, 25, 47, 0.9) !important;
        border-right: 2px solid #00f2ff;
    }
    .metric-card {
        background: rgba(16, 33, 65, 0.8); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
    }
    .report-box-red { 
        padding: 25px; border-radius: 20px; border: 2px solid #ff4b4b; 
        background: rgba(255, 75, 75, 0.15); backdrop-filter: blur(10px); color: #ffffff;
    }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; text-transform: uppercase; }
    .stButton>button {
        width: 100%; background: transparent !important; color: #00f2ff !important;
        border: 2px solid #00f2ff !important; font-family: 'Orbitron', sans-serif; transition: 0.4s;
    }
    .stButton>button:hover { background: #00f2ff !important; color: #000 !important; box-shadow: 0 0 20px #00f2ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 🛰 BOSHQARUV PANELI ---
st.sidebar.image("https://img.icons8.com/fluency/96/river.png", width=80)
st.sidebar.markdown("### 🛠 TIZIM BOSHQARUVI")
locations = {"Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60], "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]}
selected_city = st.sidebar.selectbox("HUDUDNI TANLANG:", list(locations.keys()))
radius = st.sidebar.slider("TAHLIL RADIUSI (M):", 1000, 15000, 5000)

# --- 🧠 AQLLI TAHLIL (XATOLIKLARNI OLDINI OLUVCHI) ---
def analyze_river_system(coords, radius):
    try:
        point = ee.Geometry.Point(coords[1], coords[0])
        region = point.buffer(radius).bounds()
        
        # 2024-2025 yillar oralig'idagi eng toza tasvirni olish
        img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region) \
                .filterDate('2024-01-01', '2025-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE') \
                .first()

        if not img.getInfo(): return None

        # NDWI (Suv ko'rsatkichi)
        ndwi = img.normalizedDifference(['B3', 'B8']).gt(0.0)
        
        # Maydon hisobi
        area_px = ndwi.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=region, scale=30, maxPixels=1e9
        )
        area_ha = ee.Number(area_px.get('nd', 0)).divide(10000).round().getInfo()

        # Rasm URL (Thumbnail ruxsatini tekshirish bilan)
        try:
            vis_url = img.visualize(bands=['B4', 'B3', 'B2'], min=0, max=3000).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})
        except:
            vis_url = None # Rasm chiqmasa xato bermaydi

        return vis_url, area_ha
    except Exception as e:
        return str(e)

# --- 🚀 INTERFEYS ---
st.markdown(f"<h1>🌊 AMUDARYO AI-DEFORMRISK PRO</h1>", unsafe_allow_html=True)

with st.spinner("🛰 GEE serverlari bilan bog'lanilmoqda..."):
    results = analyze_river_system(locations[selected_city], radius)

if isinstance(results, tuple):
    vis_url, area_ha = results
    
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        if vis_url:
            st.image(vis_url, use_container_width=True, caption=f"Sun'iy yo'ldosh tasviri: {selected_city}")
        else:
            st.warning("⚠️ Rasm generatsiya qilishda ruxsat yetishmadi, lekin hisob-kitoblar tayyor.")
    
    with col_side:
        st.markdown(f"""
            <div class='metric-card'>
                <p>JORIY SUV MAYDONI</p>
                <h3>{area_ha} Gektar</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Grafik
        df = pd.DataFrame({'Ko'rsatkich': ['Suv Maydoni'], 'Qiymat': [area_ha]})
        fig = px.bar(df, x='Ko'rsatkich', y='Qiymat', color_discrete_sequence=['#00f2ff'], template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div class="report-box-red">
        <h3 style='color: #ff4b4b;'>⚠️ ANALIZ XULOSASI</h3>
        <p><b>{selected_city}</b> hududida sun'iy yo'ldosh tahlili muvaffaqiyatli yakunlandi. 
        Aniqlangan suv sathi maydoni: <b>{area_ha} ga</b>. Ruxsatlar to'liq faollashgach, grafik o'zgarishlar ham qo'shiladi.</p>
        <p style="font-size: 0.8rem; opacity: 0.7;">Tizim: Amudaryo AI v2.2 | Muallif: Shahzod</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Algoritm xatosi: {results}")
