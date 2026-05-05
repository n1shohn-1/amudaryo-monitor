import streamlit as st
import ee
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. SAHIFA SOZLAMALARI
st.set_page_config(
    page_title="Amudaryo AI-Predictor Pro",
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

# --- 🎨 MODERN CYBER-UZBEK DIZAYNI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                    url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1920&q=80');
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

    .report-box-red { 
        padding: 30px; border-radius: 20px; 
        border: 2px solid #ff4b4b; 
        background-color: rgba(255, 75, 75, 0.15); 
        backdrop-filter: blur(10px); margin-top: 20px;
        border-left: 10px solid #ff4b4b;
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
        pw = st.text_input("MAXFIY KALIT:", type="password")
        if st.button("FAOLLASHTIRISH"):
            if pw == "Amudaryo_AI":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Xato kalit kiritildi!")
    st.stop()

# --- 🧠 ANALIZ ALGORITMI ---
def analyze_full_spectrum(lat, lon, rad):
    try:
        point = ee.Geometry.Point(lon, lat)
        region = point.buffer(rad).bounds()
        
        def fetch_img(year):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region).filterDate(f'{year}-01-01', f'{year}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE').first()

        past_year = datetime.now().year - 7
        current_year = datetime.now().year
        
        img_old = fetch_img(past_year)
        img_now = fetch_img(current_year)
        if not img_old or not img_now: return None

        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.1)

        erosion = mask_now.subtract(mask_old).gt(0).selfMask()
        retreat = mask_old.subtract(mask_now).gt(0).selfMask()
        future_risk = erosion.focal_max(radius=400, units='meters').selfMask()

        def calc_area(m):
            area = m.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=10, maxPixels=1e9
            )
            return ee.Number(area.get('nd', 0)).divide(10000).round().getInfo()

        a_old, a_now = calc_area(mask_old), calc_area(mask_now)
        a_ero, a_ret = calc_area(erosion), calc_area(retreat)
        a_fut = int(a_now + ((a_now - a_old) / 7 * 5))

        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
        v_params = {'dimensions': 800, 'region': region, 'format': 'jpg'}
        
        url1 = img_old.visualize(**vis).getThumbURL(v_params)
        url2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#00f2ff'])) \
                                      .blend(retreat.visualize(palette=['#ffff00'])) \
                                      .getThumbURL(v_params)
        url3 = img_now.visualize(**vis).blend(future_risk.visualize(palette=['#ff00ff'], opacity=0.7)) \
                                      .getThumbURL(v_params)
        
        return url1, url2, url3, a_old, a_now, a_fut, a_ero, a_ret
    except: return None

# --- 🛰 BOSHQARUV PANELI ---
st.sidebar.image("https://img.icons8.com/fluency/96/river.png", width=80)
st.sidebar.markdown("### 🛠 HUDUD VA XARITA")

locations = {
    "Urganch": [41.55, 60.63], 
    "Nukus": [42.45, 59.60], 
    "Termiz": [37.22, 67.27], 
    "Tuyamuyun": [41.22, 61.38],
    "Beruniy": [41.69, 60.75]
}
city = st.sidebar.selectbox("ASOSIY HUDUDNI TANLANG:", list(locations.keys()))
radius = st.sidebar.slider("SKANERLASH RADIUSI (M):", 1000, 10000, 3000)

# --- 🗺 INTERAKTIV AMUDARYO XARITASI ---
st.markdown("### 🗺 AMUDARYO INTERAKTIV MONITORI")
st.write("Xaritadan tahlil qilmoqchi bo'lgan aniq nuqtangizni ustiga bosing:")

# Xaritani tanlangan shaharga yo'naltirish
m = folium.Map(location=locations[city], zoom_start=12, tiles="OpenStreetMap")
folium.TileLayer('Stamen Terrain').add_to(m) # Daryo o'zani yaxshi ko'rinishi uchun
m.add_child(folium.LatLngPopup())

map_data = st_folium(m, width="100%", height=450)

selected_lat, selected_lon = locations[city][0], locations[city][1]
if map_data and map_data['last_clicked']:
    selected_lat = map_data['last_clicked']['lat']
    selected_lon = map_data['last_clicked']['lng']
    st.sidebar.success(f"📍 Tanlangan nuqta: {round(selected_lat, 4)}, {round(selected_lon, 4)}")

start_analysis = st.sidebar.button("🚀 TAHLILNI BOSHLASH")

# --- 🚀 ASOSIY EKRAN ---
st.markdown(f"<h1>🌊 AMUDARYO AI-DEFORMRISK MONITOR PRO</h1>", unsafe_allow_html=True)

if start_analysis:
    with st.spinner("🛰 Sun'iy yo'ldosh tahlili ketmoqda..."):
        results = analyze_full_spectrum(selected_lat, selected_lon, radius)

    if results:
        u1, u2, u3, a1, a2, af, aero, aret = results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<p style='text-align:center;'>📅 TARIX</p>", unsafe_allow_html=True)
            st.image(u1, use_container_width=True)
            st.markdown(f"<div class='metric-card'>Maydon: {a1} GA</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<p style='text-align:center; color:#00f2ff;'>📅 HOZIR</p>", unsafe_allow_html=True)
            st.image(u2, use_container_width=True)
            st.markdown(f"<div class='metric-card'>🔵Yemirilish: {aero} GA</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<p style='text-align:center; color:#ff00ff;'>📅 BASHORAT</p>", unsafe_allow_html=True)
            st.image(u3, use_container_width=True)
            st.markdown(f"<div class='metric-card'>Bashorat: {af} GA</div>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class="report-box-red">
                <h3>📑 EKSPERTIZA XULOSASI</h3>
                Tanlangan nuqta ({round(selected_lat, 4)}, {round(selected_lon, 4)}) bo'yicha tahlil yakunlandi. 
                Oxirgi 7 yilda daryo o'zani sezilarli o'zgargan. Kelajakda magenta rangli hududlarda xavf yuqori.
                <br><br><b>BOSH MUHANDIS</b>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Ushbu koordinatalar bo'yicha ma'lumot topilmadi.")
else:
    st.info("Chap paneldagi tugmani bosing yoki xaritadan boshqa nuqtani tanlang.")
