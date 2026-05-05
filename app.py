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

# --- 🎨 YANGILANGAN AI-BREND DIZAYNI ---
# Bu yerda orqa fon rasmi daryo va texnologiya uyg'unligiga o'zgartirildi
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.8)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: rgba(5, 15, 30, 0.9) !important;
        border-right: 2px solid #00f2ff;
    }

    .metric-card {
        background: rgba(0, 20, 40, 0.8); padding: 15px; border-radius: 12px;
        border: 1px solid #00f2ff; text-align: center;
    }

    .report-box-red { 
        padding: 25px; border-radius: 15px; 
        border-left: 10px solid #ff4b4b;
        background-color: rgba(255, 75, 75, 0.1); 
        backdrop-filter: blur(10px);
    }

    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; }

    .stButton>button {
        background: #00f2ff22 !important; color: #00f2ff !important;
        border: 1px solid #00f2ff !important; font-family: 'Orbitron';
    }
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
            else: st.error("Xato!")
    st.stop()

# --- 🧠 ANALIZ FUNKSIYASI (O'zgarishsiz qoldi) ---
def analyze_full_spectrum(lat, lon, rad):
    try:
        point = ee.Geometry.Point(lon, lat)
        region = point.buffer(rad).bounds()
        
        def fetch_img(year):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region).filterDate(f'{year}-01-01', f'{year}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE').first()

        past_year, current_year = datetime.now().year - 7, datetime.now().year
        img_old, img_now = fetch_img(past_year), fetch_img(current_year)
        
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
        
        return url1, url2, url3, a_old, a_now, a_fut, aero, aret
    except: return None

# --- 🗺 INTERAKTIV XARITA TIZIMI ---
st.sidebar.markdown("### 🗺 HUDUDNI TANLASH")
st.sidebar.info("Xaritadan tahlil qilmoqchi bo'lgan nuqtangizni ustiga bosing va 'TAHLILNI BOSHLASH' tugmasini bosing.")

# Xaritani yaratish (Amudaryo markazida)
m = folium.Map(location=[41.5, 60.5], zoom_start=7, tiles="CartoDB dark_matter")
# Foydalanuvchi tanlagan joyni ko'rsatish uchun "Click" hodisasi
m.add_child(folium.LatLngPopup())

# Xaritani Streamlit-da ko'rsatish
map_data = st_folium(m, width="100%", height=400)

selected_lat, selected_lon = None, None
if map_data and map_data['last_clicked']:
    selected_lat = map_data['last_clicked']['lat']
    selected_lon = map_data['last_clicked']['lng']
    st.sidebar.success(f"Tanlandi: {round(selected_lat, 4)}, {round(selected_lon, 4)}")

radius = st.sidebar.slider("SKANERLASH RADIUSI (M):", 1000, 10000, 3000)
start_analysis = st.sidebar.button("🚀 TAHLILNI BOSHLASH")

# --- 🚀 ASOSIY EKRAN ---
st.markdown("<h1>🌊 AMUDARYO AI-DEFORMRISK MONITOR PRO</h1>", unsafe_allow_html=True)

if start_analysis and selected_lat:
    with st.spinner("🛰 Sun'iy yo'ldosh ma'lumotlari qayta ishlanmoqda..."):
        res = analyze_full_spectrum(selected_lat, selected_lon, radius)
        
    if res:
        u1, u2, u3, a1, a2, af, aero, aret = res
        col1, col2, col3 = st.columns(3)
        with col1:
            st.image(u1, caption="Tarixiy Holat", use_container_width=True)
            st.markdown(f"<div class='metric-card'>Maydon: {a1} GA</div>", unsafe_allow_html=True)
        with col2:
            st.image(u2, caption="Hozirgi Dinamika", use_container_width=True)
            st.markdown(f"<div class='metric-card'>Eroziya: {aero} GA</div>", unsafe_allow_html=True)
        with col3:
            st.image(u3, caption="AI Bashorat", use_container_width=True)
            st.markdown(f"<div class='metric-card'>Kutilmoqda: {af} GA</div>", unsafe_allow_html=True)
            
        # Grafik va Hisobot qismi (oldindagidek)
        st.divider()
        st.markdown("<div class='report-box-red'><h3>📑 AI ANALITIK XULOSA</h3>"
                    f"Tanlangan koordinata: {selected_lat}, {selected_lon}<br>"
                    f"Kelajak 5 yil uchun daryo o'zani o'zgarish xavfi mavjud.</div>", unsafe_allow_html=True)
    else:
        st.error("Ushbu hudud uchun ma'lumot topilmadi.")
elif start_analysis and not selected_lat:
    st.warning("Iltimos, avval xaritadan biror nuqtani bosing!")
else:
    st.markdown("""
        <div style='text-align: center; padding: 50px; background: rgba(0,0,0,0.5); border-radius: 20px;'>
            <h3>Xaritadan Amudaryoning istalgan qismini tanlang</h3>
            <p>Sichqoncha bilan nuqta qo'ying va chap paneldagi tugmani bosing.</p>
        </div>
    """, unsafe_allow_html=True)
