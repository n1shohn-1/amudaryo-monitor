import streamlit as st
import ee
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

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

# --- 🎨 OPTIMALLASHTIRILGAN KIBER DIZAYN (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');

    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), 
                    url('https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: rgba(10, 25, 47, 0.98) !important;
        border-right: 2px solid #00f2ff;
    }

    .metric-card {
        background: rgba(16, 33, 65, 0.85); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center; box-shadow: 0 0 20px rgba(0, 242, 255, 0.15);
    }

    .report-box-red { 
        padding: 30px; border-radius: 20px; 
        border: 2px solid #ff4b4b; 
        background-color: rgba(255, 75, 75, 0.1); 
        backdrop-filter: blur(12px); margin-top: 20px;
        border-left: 10px solid #ff4b4b;
    }

    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; text-transform: uppercase; letter-spacing: 2px; }

    .stButton>button {
        width: 100%; background: transparent !important; color: #00f2ff !important;
        border: 2px solid #00f2ff !important; font-family: 'Orbitron', sans-serif; transition: 0.3s;
    }
    .stButton>button:hover { background: #00f2ff !important; color: #000 !important; box-shadow: 0 0 25px #00f2ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 XAVFSIZLIK TIZIMI ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    _, col_auth, _ = st.columns([1,1.2,1])
    with col_auth:
        st.markdown("<h2 style='text-align: center;'>SYSTEM ACCESS</h2>", unsafe_allow_html=True)
        pw = st.text_input("PASSWORD:", type="password")
        if st.button("AUTHENTICATE"):
            if pw == "Amudaryo_AI":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Access Denied!")
    st.stop()

# --- 🛰 BOSHQARUV PANELI ---
st.sidebar.image("https://img.icons8.com/fluency/96/satellite.png", width=80)
st.sidebar.markdown("### 🛠 CONTROL PANEL")
locations = {"Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60], "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]}
city = st.sidebar.selectbox("TARGET AREA:", list(locations.keys()))
radius = st.sidebar.slider("SCAN RADIUS (M):", 2000, 15000, 5000)

current_year = datetime.now().year
past_year = current_year - 7
future_year = current_year + 5

# --- 🧠 OPTIMALLASHTIRILGAN ANALIZ VA BASHORAT ---
def analyze_fast_spectrum(coords, rad):
    try:
        point = ee.Geometry.Point(coords[1], coords[0])
        region = point.buffer(rad).bounds()
        
        def fetch_img(year):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region).filterDate(f'{year}-01-01', f'{year}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE').first()

        img_old = fetch_img(past_year)
        img_now = fetch_img(current_year)
        if not img_old or not img_now: return None

        # NDWI (Suvni aniqlash)
        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.1)

        # Deformatsiyalar
        erosion = mask_now.subtract(mask_old).gt(0).selfMask()
        retreat = mask_old.subtract(mask_now).gt(0).selfMask()
        
        # Bashorat xavfi
        risk_zone = erosion.focal_max(radius=350, units='meters').selfMask()

        def calc_area(m):
            area = m.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(), geometry=region, scale=20, maxPixels=1e8
            )
            return ee.Number(area.get('nd', 0)).divide(10000).round().getInfo()

        a_old, a_now = calc_area(mask_old), calc_area(mask_now)
        a_ero, a_ret = calc_area(erosion), calc_area(retreat)
        
        # Bashorat
        change_rate = (a_now - a_old) / 7
        a_fut = int(a_now + (change_rate * 5))

        # Vizualizatsiya (Tezkor yuklash uchun scale sozlangan)
        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
        v_params = {'dimensions': 800, 'region': region, 'format': 'png'}
        
        url1 = img_old.visualize(**vis).getThumbURL(v_params)
        
        # Hozirgi holat: Ko'k va Sariq
        url2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#00f2ff'])) \
                                      .blend(retreat.visualize(palette=['#ffff00'])) \
                                      .getThumbURL(v_params)
        
        # Bashorat holati: Toza ko'rinishda xavf zonalari (Ko'k va Sariq bashorat bilan)
        url3 = img_now.visualize(**vis).blend(risk_zone.visualize(palette=['#00f2ff'], opacity=0.6)) \
                                      .getThumbURL(v_params)
        
        return url1, url2, url3, a_old, a_now, a_fut, a_ero, a_ret
    except: return None

# --- 🚀 ASOSIY EKRAN ---
st.markdown(f"<h1>🛰 AMUDARYO AI-MONITOR PRO</h1>", unsafe_allow_html=True)

with st.spinner("📡 SATELLITE CONNECTION ESTABLISHED... ANALYZING DATA..."):
    results = analyze_fast_spectrum(locations[city], radius)

if results:
    u1, u2, u3, a1, a2, af, aero, aret = results
    
    st.markdown("### 🗺 REAL-TIME SPECTRAL ANALYSIS")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"<p style='text-align:center;'>📅 {past_year}-YEAR (HISTORY)</p>", unsafe_allow_html=True)
        st.image(u1, use_container_width=True)
        st.markdown(f"<div class='metric-card'>AREA: {a1} GA</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"<p style='text-align:center; color:#00f2ff;'>📅 {current_year}-YEAR (CURRENT)</p>", unsafe_allow_html=True)
        st.image(u2, use_container_width=True)
        st.markdown(f"<div class='metric-card'>🔵 EROSION: {aero} GA | 🟡 RETREAT: {aret} GA</div>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"<p style='text-align:center; color:#00f2ff;'>📅 {future_year}-YEAR (PREDICTION)</p>", unsafe_allow_html=True)
        st.image(u3, use_container_width=True)
        st.markdown(f"<div class='metric-card'>PREDICTED AREA: {af} GA</div>", unsafe_allow_html=True)

    # GRAFIK
    st.divider()
    df_chart = pd.DataFrame({
        'Timeline': [str(past_year), "Current", f"Future ({future_year})"],
        'Area (GA)': [a1, a2, af]
    })
    fig = px.line(df_chart, x='Timeline', y='Area (GA)', markers=True, text='Area (GA)', 
                 template="plotly_dark", color_discrete_sequence=['#00f2ff'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    # EKSPERT XULOSASI (QIZIL)
    st.markdown(f"""
        <div class="report-box-red">
            <h3 style='color: #ff4b4b;'>📑 OFFICIAL AI RISK REPORT</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                <b>AREA ANALYSIS:</b> {city} sector shows active morphological shifts.<br>
                <b>DYNAMICS:</b> In the last cycle, <b>{aero} hectares</b> of land were eroded by river flow, while <b>{aret} hectares</b> saw water retreat.<br>
                <b>FORECAST:</b> By {future_year}, the system predicts a total water area of <b>{af} GA</b>. Blue zones indicate high-risk areas for infrastructure damage.
            </p>
            <hr style="border-color: rgba(255, 75, 75, 0.3);">
            <div style="display: flex; justify-content: space-between; font-family: 'Orbitron'; font-size: 0.85rem;">
                <span>REF_ID: AMU-AI-2026-PRO</span>
                <span style="color: #00f2ff; font-weight: bold;">CHIEF ENGINEER</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ DATA RETRIEVAL ERROR: High cloud coverage or connection timeout. Adjust radius.")

if st.sidebar.button("🔌 TERMINATE SESSION"):
    st.session_state.auth = False
    st.rerun()
