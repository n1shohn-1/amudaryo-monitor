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

# --- 🧠 SESSION STATE ---
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# --- 🎨 MODERN CYBER-UZBEK DIZAYNI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }
    [data-testid="stSidebar"] { background: rgba(10, 25, 47, 0.95) !important; border-right: 2px solid #00f2ff; }
    .metric-card {
        background: rgba(16, 33, 65, 0.8); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
    }
    .report-box-red { 
        padding: 30px; border-radius: 20px; border: 2px solid #ff4b4b; 
        background-color: rgba(255, 75, 75, 0.15); backdrop-filter: blur(10px); margin-top: 20px; border-left: 10px solid #ff4b4b;
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

# --- 🛰 BOSHQARUV ---
current_year = datetime.now().year
past_year = current_year - 7
future_year = current_year + 5

# --- 🧠 INTEGRATSIYALASHGAN ANALIZ ---
def analyze_full_spectrum(geometry):
    try:
        # Rasmni olish funksiyasi (Bulutlilikni kamaytirish va median olish orqali rasm chiqmaslik muammosini yechadi)
        def fetch_img(year):
            dataset = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(geometry) \
                .filterDate(f'{year}-03-01', f'{year}-10-31') \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
            # Agar rasm bo'sh bo'lsa, bulutlilik chegarasini oshiramiz
            if dataset.size().getInfo() == 0:
                dataset = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                    .filterBounds(geometry) \
                    .filterDate(f'{year}-01-01', f'{year}-12-31')
            
            return dataset.median().clip(geometry)

        img_old = fetch_img(past_year)
        img_now = fetch_img(current_year)

        # Suv maskalari (NDWI)
        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.1)

        # SARIQ: O'tmishda suv yo'q edi, hozir bor (Yuvilish) yoki aksincha
        # Sizning so'rovingizga ko'ra: o'tmishdagi quruqlik hozir suv bo'lsa - SARIQ
        erosion = mask_now.subtract(mask_old).gt(0).selfMask()

        # QIZIL: Kelajak xavfi (Hozirgi qirg'oqdan 500m bufer)
        future_buffer = mask_now.focal_max(radius=500, units='meters')
        future_risk = future_buffer.subtract(mask_now).gt(0).selfMask()

        def calc_area(m):
            area = m.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=geometry, scale=20, maxPixels=1e9
            )
            val = area.get('nd')
            return ee.Number(ee.Algorithms.If(val, val, 0)).divide(10000).round().getInfo()

        a_old, a_now = calc_area(mask_old), calc_area(mask_now)
        a_ero = calc_area(erosion)
        a_fut = int(a_now * 1.05) # Bashoratli o'sish

        # Vizualizatsiya
        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3500, 'gamma': 1.4}
        v_params = {'dimensions': 1200, 'region': geometry.bounds(), 'format': 'jpg'}
        
        url1 = img_old.visualize(**vis).getThumbURL(v_params)
        
        # 2-Rasm: Bugungi holat + SARIQ (Yuvilgan joylar)
        url2 = img_now.visualize(**vis).blend(
            erosion.visualize(palette=['#ffff00'], opacity=0.9)
        ).getThumbURL(v_params)
        
        # 3-Rasm: Bashorat + QIZIL (Xavfli zonalar)
        url3 = img_now.visualize(**vis).blend(
            future_risk.visualize(palette=['#ff0000'], opacity=0.7)
        ).getThumbURL(v_params)
        
        return url1, url2, url3, a_old, a_now, a_fut, a_ero
    except Exception as e:
        st.error(f"Analizda xato: {e}")
        return None

# --- 🚀 ASOSIY EKRAN ---
st.markdown("<h1>🌊 AMUDARYO AI-DEFORMRISK MONITOR PRO</h1>", unsafe_allow_html=True)
st.subheader("📍 Xaritadan to'rtburchak chizib hududni tanlang")

m = folium.Map(
    location=[41.5, 60.5], zoom_start=8, 
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", 
    attr="Google Satellite"
)
folium.plugins.Draw(
    export=False,
    draw_options={'polyline':False, 'polygon':False, 'circle':False, 'marker':False, 'circlemarker':False, 'rectangle':True}
).add_to(m)

map_output = st_folium(m, width="100%", height=450, key="amu_map_v2")

if map_output['last_active_drawing']:
    coords = map_output['last_active_drawing']['geometry']['coordinates'][0]
    selected_geometry = ee.Geometry.Polygon(coords)
    
    if st.button("🔍 SUN'IY YO'LDOSH TAHLILINI BOSHLASH"):
        with st.spinner("🛰 GEE koinot stansiyasidan ma'lumotlar olinmoqda..."):
            res = analyze_full_spectrum(selected_geometry)
            st.session_state.analysis_results = res

# --- NATIJALAR ---
if st.session_state.analysis_results:
    u1, u2, u3, a1, a2, af, aero = st.session_state.analysis_results
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<p style='text-align:center;'>📅 {past_year}-YIL</p>", unsafe_allow_html=True)
        st.image(u1, use_container_width=True, caption="Asl holat")
    with col2:
        st.markdown(f"<p style='text-align:center; color:#ffff00;'>📅 HOZIR (SARIQ: YUVILISH)</p>", unsafe_allow_html=True)
        st.image(u2, use_container_width=True, caption="Eroziya aniqlangan zonalar")
    with col3:
        st.markdown(f"<p style='text-align:center; color:#ff0000;'>📅 BASHORAT (QIZIL: XAVF)</p>", unsafe_allow_html=True)
        st.image(u3, use_container_width=True, caption="Kelajakdagi xavfli hududlar")

    st.markdown(f"""
        <div class="report-box-red">
            <h3 style='color: #ff4b4b;'>📑 FVV UCHUN TEZKOR MA'LUMOTNOMA</h3>
            <p>1. <b>ANIQLANGAN EROZIYA:</b> So'nggi yillarda daryo o'zani <b>{aero} gektar</b> maydonni yuvib ketgan (Sariq zonalar).<br>
            2. <b>XAVF MONITORINGI:</b> Qizil rang bilan belgilangan hududlarda qirg'oq mustahkamlash ishlarini olib borish tavsiya etiladi.</p>
        </div>
    """, unsafe_allow_html=True)
