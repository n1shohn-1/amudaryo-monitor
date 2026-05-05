import streamlit as st
import ee
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. SAHIFA SOZLAMALARI
st.set_page_config(
    page_title="Amudaryo AI-Monitor | Shaxriyor",
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

# --- 🎨 MODERN CYBER-UZBEK DIZAYNI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
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

# --- 🔐 XAVFSIZLIK TIZIMI ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    _, col_auth, _ = st.columns([1,1.2,1])
    with col_auth:
        st.markdown("<h2 style='text-align: center;'>TIZIMGA KIRISH</h2>", unsafe_allow_html=True)
        pw = st.text_input("MAXFIY KALIT:", type="password")
        if st.button("FAOL LASHTIRISH"):
            if pw == "Amudaryo_AI": st.session_state.auth = True; st.rerun()
            else: st.error("Xato kalit kiritildi!")
    st.stop()

# --- 🛰 BOSHQARUV PANELI ---
st.sidebar.image("https://img.icons8.com/fluency/96/river.png", width=80)
st.sidebar.markdown("### 🛠 TIZIM BOSHQARUVI")
locations = {"Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60], "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]}
selected_city = st.sidebar.selectbox("HUDUDNI TANLANG:", list(locations.keys()))
radius = st.sidebar.slider("TAHLIL RADIUSI (M):", 1000, 10000, 5000)

current_year = datetime.now().year
past_year = current_year - 10
future_year = current_year + 5

# --- 🧠 ASOSIY TAHLIL ALGORITMI (MUKAMMAL) ---
def analyze_river_advanced(coords, radius):
    try:
        point = ee.Geometry.Point(coords[1], coords[0])
        region = point.buffer(radius).bounds()
        
        def get_img(year_start):
            # Sentinel-2 ni qidiradi, topmasa Landsatga o'tadi
            coll = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region).filterDate(f'{year_start}-01-01', f'{year_start+1}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE')
            return coll.first()

        img_old = get_img(past_year - 1) # 2015-2016
        img_now = get_img(current_year - 1) # 2024-2025

        if not img_old or not img_now: return None

        # NDWI - Suvni aniqlash
        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.1)

        # Yemirilish va Chekinishni hisoblash
        erosion = mask_now.subtract(mask_old).gt(0).selfMask() # Yangi suv bosgan joy
        retreat = mask_old.subtract(mask_now).gt(0).selfMask() # Suv qochgan joy

        def get_area(mask):
            area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=10, maxPixels=1e9
            )
            return ee.Number(area.get('nd' if 'nd' in area.getInfo() else 'groups', 0)).divide(10000).round().getInfo()

        a_old, a_now = get_area(mask_old), get_area(mask_now)
        a_ero, a_ret = get_area(erosion), get_area(retreat)

        # Bashorat
        change_rate = (a_now - a_old) / 10
        a_fut = int(a_now + (change_rate * 5))
        
        # Vizualizatsiya
        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
        url_old = img_old.visualize(**vis).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})
        url_now = img_now.visualize(**vis).blend(erosion.visualize(palette=['#00f2ff'], opacity=0.7)).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})
        url_fut = img_now.visualize(**vis).getThumbURL({'dimensions': 800, 'region': region, 'format': 'jpg'})

        return url_old, url_now, url_fut, a_old, a_now, a_ero, a_ret, a_fut
    except:
        return None

# --- 🚀 NATIJALARNI CHIQARISH ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1: st.markdown(f"<h1>🌊 Amudaryo AI-DeformRisk Pro</h1>", unsafe_allow_html=True)
with col_h2: st.markdown(f"<div class='metric-card'><p>JORIY YIL</p><h3>{current_year}</h3></div>", unsafe_allow_html=True)

with st.spinner("🚀 Shaxriyor AI algoritmlari koinotdan ma'lumot olmoqda..."):
    results = analyze_river_advanced(locations[selected_city], radius)

if results:
    u1, u2, u3, a_old, a_now, a_ero, a_ret, a_fut = results
    
    st.subheader("🖼 Gidrologik O'zgarishlar Vizualizatsiyasi")
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"⏪ {past_year}-YIL"); st.image(u1, use_container_width=True); st.write(f"Maydon: {a_old} ga")
    with c2: st.success(f"📍 {current_year}-YIL (ANALIZ)"); st.image(u2, use_container_width=True); st.write(f"🔵 Yemirilish: {a_ero} ga | 🟡 Qurish: {a_ret} ga")
    with c3: st.error(f"⏩ {future_year}-YIL (BASHORAT)"); st.image(u3, use_container_width=True); st.write(f"Kutilmoqda: {a_fut} ga")

    # GRAFIK
    st.divider()
    chart_data = pd.DataFrame({'Yil': [past_year, current_year, future_year], 'Maydon (ga)': [a_old, a_now, a_fut]})
    fig = px.line(chart_data, x='Yil', y='Maydon (ga)', markers=True, title="Daryo Maydoni Dinamikasi", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # --- EKSPERT XULOSASI ---
    risk_level = "YUQORI" if a_ero > 40 else "O'RTA" if a_ero > 15 else "BARQAROR"
    st.markdown(f"""
    <div class="report-box-red">
        <h3 style='color: #ff4b4b;'>⚠️ AI ANALIZ XULOSASI: XAVF DARAJASI {risk_level}</h3>
        <p><b>Tahlil natijasi:</b> Oxirgi 10 yilda <b>{selected_city}</b> hududida <b>{a_ero} gektar</b> yer suv ostida qolgan (yemirilgan). 
        Daryo maydoni o'zgarishi yiliga o'rtacha <b>{round((a_now-a_old)/10, 2)} ga</b> tashkil qilmoqda.</p>
        <p><b>Bashorat:</b> Agar ushbu sur'at davom etsa, <b>{future_year}-yilga</b> borib suv maydoni <b>{a_fut} gektarga</b> yetishi mumkin.</p>
        <hr style='border: 0.5px solid #ff4b4b;'>
        <p><b>💡 SHAXRIYOR TAVSIYASI:</b> Ko'k bilan belgilangan (yemirilgan) hududlarda qirg'oqni mustahkamlash va damba qurish ishlarini rejalashtirish zarur.</p>
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-top: 10px;">
            <span>Tizim: Amudaryo AI Pro v2.0</span>
            <span>BOSH MUHANDIS: SHAXRIYOR</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ SENSOR XATOSI: Hududda bulutlilik yuqori. Iltimos, radiusni o'zgartirib qayta urinib ko'ring.")

if st.sidebar.button("🔌 TIZIMNI O'CHIRISH"):
    st.session_state.auth = False
    st.rerun()
