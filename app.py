import streamlit as st
import ee
import json
import pandas as pd
from datetime import datetime, timedelta

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
    st.error(f"🛰 Tizimga ulanishda xatolik: {e}")
    st.stop()

# --- 🎨 MODERN CYBER DIZAYN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed; color: #ffffff; font-family: 'Exo 2', sans-serif;
    }
    .metric-card {
        background: rgba(16, 33, 65, 0.7); padding: 20px; border-radius: 15px; border: 1px solid #00f2ff; text-align: center;
    }
    .report-box {
        background: rgba(2, 12, 27, 0.9); padding: 30px; border-radius: 20px; border-left: 5px solid #00f2ff; backdrop-filter: blur(10px); margin-top: 20px;
    }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 XAVFSIZLIK ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    _, col_auth, _ = st.columns([1,1.2,1])
    with col_auth:
        st.markdown("<h2 style='text-align: center;'>TIZIMGA KIRISH</h2>", unsafe_allow_html=True)
        pw = st.text_input("MAXFIY KALIT:", type="password")
        if st.button("FAOL LASHTIRISH"):
            if pw == "Amudaryo_AI": st.session_state.auth = True; st.rerun()
            else: st.error("Xato!")
    st.stop()

# --- 🛰 BOSHQARUV ---
st.sidebar.markdown("### 🛠 TIZIM BOSHQARUVI")
locations = {"Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60], "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]}
city = st.sidebar.selectbox("HUDUDNI TANLANG:", list(locations.keys()))
radius = st.sidebar.slider("SKANERLASH RADIUSI (M):", 5000, 20000, 10000)

# --- 🧠 AI ANALIZ VA BASHORAT (ADVANCED) ---
def get_advanced_analysis(coords, rad):
    try:
        point = ee.Geometry.Point(coords[1], coords[0])
        region = point.buffer(rad).bounds()
        current_year = datetime.now().year
        past_year = current_year - 10
        
        def fetch_cloud_free(year):
            # Sentinel-2 to'plami
            s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region) \
                .filterDate(f'{year}-01-01', f'{year}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE')
            
            # Agar Sentinel bo'sh bo'lsa Landsat-8 ga o'tish
            if s2.size().getInfo() == 0:
                img = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                    .filterBounds(region) \
                    .filterDate(f'{year}-01-01', f'{year}-12-31') \
                    .sort('CLOUD_COVER').first()
                # Landsat va Sentinel bandlari farq qiladi, shuning uchun NDWI ni moslashtiramiz
                ndwi = img.normalizedDifference(['SR_B3', 'SR_B5'])
            else:
                img = s2.first()
                ndwi = img.normalizedDifference(['B3', 'B8'])
                
            return img, ndwi

        img_past, ndwi_past = fetch_cloud_free(past_year)
        img_now, ndwi_now = fetch_cloud_free(current_year)

        def calc_area(ndwi_img):
            mask = ndwi_img.gt(0.1)
            area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=30, maxPixels=1e9
            )
            return ee.Number(area.get('nd', 0)).divide(10000).round().getInfo()

        area_past = calc_area(ndwi_past)
        area_now = calc_area(ndwi_now)
        
        # 📈 Bashorat Logikasi (Linear Trend AI)
        trend = (area_now - area_past) / 10
        area_future = round(area_now + (trend * 5))
        
        # Vizualizatsiya
        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000} # Sentinel uchun
        if 'SR_B4' in img_now.bandNames().getInfo(): # Landsat uchun vizualizatsiya
             vis = {'bands': ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 30000}

        u_past = img_past.visualize(**vis).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})
        u_now = img_now.visualize(**vis).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})
        
        return u_past, u_now, area_past, area_now, area_future, past_year, current_year
    except Exception as e:
        return None

# --- 🚀 OUTPUT ---
st.markdown(f"<h1>🛰 {city} Monitoring & Bashorat</h1>", unsafe_allow_html=True)

with st.spinner("AI Arxivlarni va koinotni skanerlamoqda..."):
    data = get_advanced_analysis(locations[city], radius)

if data:
    u_p, u_n, a_p, a_n, a_f, y_p, y_n = data
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<p style='text-align:center;'>📅 {y_p}-YIL (ARXIV)</p>", unsafe_allow_html=True)
        st.image(u_p, use_container_width=True)
    with c2:
        st.markdown(f"<p style='text-align:center; color:#00f2ff;'>📅 {y_n}-YIL (HOZIRGI HOLAT)</p>", unsafe_allow_html=True)
        st.image(u_n, use_container_width=True)

    # Grafika
    st.markdown("### 📊 GIDROLOGIK DINAMIKA VA AI BASHORAT (2031)")
    chart_data = pd.DataFrame({
        'Yil': [str(y_p), str(y_n), str(y_n + 5)],
        'Maydon (GA)': [a_p, a_n, a_f]
    })
    st.line_chart(chart_data.set_index('Yil'))

    # Metrikalar
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-card'><p>{y_p}-YIL</p><h2>{a_p} GA</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-card'><p>{y_n}-YIL (HOZIR)</p><h2>{a_n} GA</h2></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric-card' style='border-color:#ff9f43;'><p>2031-YIL (BASHORAT)</p><h2>{a_f} GA</h2></div>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="report-box">
            <h3>📑 SHAXRIYOR AI INTEGRATSIYA: XULOSA</h3>
            <p style="font-size: 1.1rem;">
                Tizim <b>{y_p}</b> va <b>{y_n}</b> yillar oralig'idagi trendni tahlil qildi. 
                Oxirgi 10 yilda daryo o'zani yillik o'rtacha <b>{round((a_n-a_p)/10, 2)} GA</b> tezlikda o'zgargan. 
                Ushbu dinamika saqlanib qolsa, <b>{y_n + 5}-yilga</b> borib maydon <b>{a_f} GA</b> bo'lishi kutilmoqda.
            </p>
            <hr style="border-color: rgba(0, 242, 255, 0.3);">
            <div style="display: flex; justify-content: space-between;">
                <span>ANALIZ VAQTI: {datetime.now().strftime('%d.%m.%Y | %H:%M')}</span>
                <span style="color: #00f2ff; font-weight: bold;">BOSH MUHANDIS: SHAXRIYOR</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("⚠️ TIZIM MA'LUMOT OLOLMADI. Sabab: Google Earth Engine serverlari band yoki hududda ekstremal bulutlilik. Iltimos, radiusni o'zgartirib qayta urinib ko'ring.")
