import streamlit as st
import ee
import json
from datetime import datetime

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Amudaryo AI-Monitor | Shaxriyor", page_icon="🛰", layout="wide")

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
    st.error(f"🛰 Tizim xatosi: {e}")
    st.stop()

# --- 🎨 SHAXRIYOR KLASSIK CYBER DIZAYNI ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url('https://img.freepik.com/free-photo/view-earth-from-outer-space_23-2150692749.jpg');
        background-size: cover;
        color: #ffffff;
    }
    [data-testid="stSidebar"] { background: rgba(10, 25, 47, 0.9) !important; border-right: 2px solid #00f2ff; }
    .metric-card {
        background: rgba(16, 33, 65, 0.8);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #00f2ff;
        text-align: center;
    }
    .report-box {
        background: rgba(2, 12, 27, 0.9);
        padding: 30px;
        border-radius: 20px;
        border-left: 5px solid #00f2ff;
        margin-top: 20px;
    }
    h1, h2, h3 { color: #00f2ff !important; font-family: 'Arial Black'; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 KIRISH ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    _, col_auth, _ = st.columns([1,1,1])
    with col_auth:
        st.markdown("<h2 style='text-align:center;'>🛰 TERMINAL</h2>", unsafe_allow_html=True)
        pw = st.text_input("PASSWORD:", type="password")
        if st.button("KIRISH"):
            if pw == "Amudaryo_AI": st.session_state.auth = True; st.rerun()
    st.stop()

# --- 🛰 BOSHQARUV ---
st.sidebar.title("🛠 COMAND")
locations = {
    "Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60],
    "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]
}
city = st.sidebar.selectbox("HUDUD:", list(locations.keys()))
radius = st.sidebar.slider("RADIUS (M):", 5000, 15000, 8000)

# --- 🧠 ENG KUCHLI VA SODDA ANALIZ ---
def get_data(coords, rad):
    point = ee.Geometry.Point(coords[1], coords[0])
    region = point.buffer(rad).bounds()
    
    # Sentinel-2 tasvirlarini olish (Eng yangi va eng toza tasvir)
    def fetch_best(year):
        return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(region) \
            .filterDate(f'{year}-01-01', f'{year}-12-31') \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()

    img_old = fetch_best(2020)
    img_new = fetch_best(2024)

    # Agar Sentinel topilmasa, Landsat'ga o'tadi (BU JUDA MUHIM!)
    if not img_new:
        img_new = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(region) \
            .filterDate('2023-01-01', '2024-12-31') \
            .sort('CLOUD_COVER') \
            .first()

    # Suv maydoni (Oddiy va aniq algoritm)
    mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
    mask_new = img_new.normalizedDifference(['B3', 'B8']).gt(0.1)
    
    def area(m):
        a = m.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=region, scale=30, maxPixels=1e9
        )
        return ee.Number(a.get('nd', 0)).divide(10000).round().getInfo()

    a1, a2 = area(mask_old), area(mask_new)
    
    vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    u1 = img_old.visualize(**vis).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})
    u2 = img_new.visualize(**vis).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})
    
    return u1, u2, a1, a2

# --- NATIJA ---
st.title(f"📍 {city} Hududi Monitoringi")
with st.spinner("AI Ma'lumotlarni hisoblamoqda..."):
    res = get_data(locations[city], radius)

if res:
    u1, u2, a1, a2 = res
    c1, c2 = st.columns(2)
    with c1: st.image(u1, caption="2020-yil"); st.markdown(f"<div class='metric-card'>AVVALGI: {a1} GA</div>", unsafe_allow_html=True)
    with c2: st.image(u2, caption="2024-yil"); st.markdown(f"<div class='metric-card'>HOZIRGI: {a2} GA</div>", unsafe_allow_html=True)

    diff = a2 - a1
    st.markdown(f"""
        <div class="report-box">
            <h3>📑 SHAXRIYOR: AI XULOSASI</h3>
            <p>Hududda suv maydoni <b>{abs(diff)} gektarga</b> {'o\'sgan' if diff > 0 else 'kamaygan'}.</p>
            <p style="text-align:right;"><b>MUHANDIS: SHAXRIYOR</b></p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("Ma'lumot topilmadi. Radiusni o'zgartiring!")
