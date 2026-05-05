import streamlit as st
import ee
import json
from datetime import datetime

# 1. SAHIFA SOZLAMALARI
st.set_page_config(
    page_title="Amudaryo AI-Monitor | Shaxriyor",
    page_icon="🛰",
    layout="wide"
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
        background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
        color: #ffffff;
        font-family: 'Exo 2', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: rgba(10, 25, 47, 0.9) !important;
        border-right: 2px solid #00f2ff;
    }

    .metric-card {
        background: rgba(16, 33, 65, 0.7);
        padding: 25px;
        border-radius: 20px;
        border: 1px solid #00f2ff;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
        text-align: center;
    }

    .report-box {
        background: rgba(2, 12, 27, 0.85);
        padding: 35px;
        border-radius: 25px;
        border-left: 5px solid #00f2ff;
        backdrop-filter: blur(10px);
        margin-top: 30px;
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: #00f2ff !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .stButton>button {
        width: 100%;
        background: transparent !important;
        color: #00f2ff !important;
        border: 2px solid #00f2ff !important;
        font-family: 'Orbitron', sans-serif;
        transition: 0.4s;
    }

    .stButton>button:hover {
        background: #00f2ff !important;
        color: #000 !important;
        box-shadow: 0 0 20px #00f2ff;
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
        if st.button("FAOL LASHTIRISH"):
            if pw == "Amudaryo_AI":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Xato kalit kiritildi!")
    st.stop()

# --- 🛰 BOSHQARUV PANELİ ---
st.sidebar.markdown("### 🛠 TIZIM BOSHQARUVI")
locations = {
    "Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60],
    "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]
}
city = st.sidebar.selectbox("HUDUDNI TANLANG:", list(locations.keys()))
radius = st.sidebar.slider("SKANERLASH RADIUSI (M):", 5000, 20000, 10000)

# --- 🧠 ANALIZ ALGORITMI (BARQAROR) ---
def get_river_analysis(coords, rad):
    try:
        point = ee.Geometry.Point(coords[1], coords[0])
        region = point.buffer(rad).bounds()
        
        # Tasvirlarni olish (Sentinel-2)
        def fetch_img(start, end):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region) \
                .filterDate(start, end) \
                .sort('CLOUDY_PIXEL_PERCENTAGE').first()

        img_old = fetch_img('2019-01-01', '2019-12-31')
        img_new = fetch_img('2023-01-01', '2024-12-31')

        if not img_old or not img_new: return None

        # NDWI (Suv indeksi)
        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
        mask_new = img_new.normalizedDifference(['B3', 'B8']).gt(0.1)
        
        def calc_area(m):
            area = m.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=10, maxPixels=1e9
            )
            return ee.Number(area.get('nd', 0)).divide(10000).round().getInfo()

        a1, a2 = calc_area(mask_old), calc_area(mask_new)
        
        # Vizualizatsiya
        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
        url1 = img_old.visualize(**vis).getThumbURL({'dimensions': 1000, 'region': region, 'format': 'jpg'})
        url2 = img_new.visualize(**vis).getThumbURL({'dimensions': 1000, 'region': region, 'format': 'jpg'})
        
        return url1, url2, a1, a2
    except:
        return None

# --- 🚀 NATIJALAR ---
st.markdown(f"<h1>🛰 {city} Hududi Monitoringi</h1>", unsafe_allow_html=True)

with st.spinner("Sun'iy yo'ldosh bilan aloqa o'rnatilmoqda..."):
    data = get_river_analysis(locations[city], radius)

if data:
    u1, u2, a1, a2 = data
    diff = a2 - a1
    
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        st.markdown("<p style='text-align:center;'>📅 2019-YILGI HOLAT</p>", unsafe_allow_html=True)
        st.image(u1, use_container_width=True)
    with col_img2:
        st.markdown("<p style='text-align:center; color:#00f2ff;'>📅 HOZIRGI HOLAT (AI-ANALIZ)</p>", unsafe_allow_html=True)
        st.image(u2, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-card'><p>AVVALGI MAYDON</p><h2>{a1} GA</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-card'><p>HOZIRGI MAYDON</p><h2>{a2} GA</h2></div>", unsafe_allow_html=True)
    with m3: 
        color = "#00f2ff" if diff >= 0 else "#ff4b4b"
        st.markdown(f"<div class='metric-card'><p>O'ZGARISH</p><h2 style='color:{color};'>{diff} GA</h2></div>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="report-box">
            <h3>📑 TIZIMNING RASMIY XULOSASI</h3>
            <p style="font-size: 1.2rem;">
                Skanerlash natijasida <b>{city}</b> hududida gidrologik o'zgarishlar aniqlandi. 
                Daryo o'zani maydoni <b>{abs(diff)} gektarga</b> {'ko\'paygan' if diff > 0 else 'kamaygan'}. 
                Ushbu ma'lumotlar Sentinel-2 sun'iy yo'ldoshidan olingan va Shaxriyor tomonidan sozlangan AI algoritmida qayta ishlandi.
            </p>
            <hr style="border-color: rgba(0, 242, 255, 0.3);">
            <div style="display: flex; justify-content: space-between;">
                <span>Vaqt: {datetime.now().strftime('%d.%m.%Y | %H:%M')}</span>
                <span style="color: #00f2ff; font-weight: bold;">BOSH MUHANDIS: SHAXRIYOR</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ SENSOR XATOSI: Hudud ustida bulutlilik darajasi yuqori yoki GEE ulanishida uzilish. Iltimos, radiusni biroz o'zgartiring.")

if st.sidebar.button("🔌 TIZIMNI O'CHIRISH"):
    st.session_state.auth = False
    st.rerun()
