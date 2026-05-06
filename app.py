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

# --- 🎨 MODERN CYBER-UZBEK DIZAYNI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                    url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }
    [data-testid="stSidebar"] { background: rgba(10, 25, 47, 0.95) !important; border-right: 2px solid #00f2ff; }
    .metric-card {
        background: rgba(16, 33, 65, 0.8); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
    }
    .report-box-dynamic { 
        padding: 30px; border-radius: 20px; border: 2px solid #00f2ff; 
        background-color: rgba(10, 25, 47, 0.85); backdrop-filter: blur(10px); margin-top: 20px; border-left: 10px solid #00f2ff;
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
st.sidebar.image("https://img.icons8.com/fluency/96/river.png", width=80)
st.sidebar.markdown("### 🛠 TIZIM BOSHQARUVI")

current_year = datetime.now().year
past_year = current_year - 7
future_year = current_year + 5

# --- 🧠 MUKAMMAL ANALIZ ALGORITMI ---
def analyze_full_spectrum(geometry):
    try:
        region_ee = geometry
        area_km2 = geometry.area().divide(1e6).getInfo()
        calc_scale = 10 if area_km2 < 5 else 30

        def fetch_img(year):
            col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region_ee) \
                .filterDate(f'{year}-01-01', f'{year}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE')
            img = col.first()
            return img.clip(region_ee) if img else None

        img_old = fetch_img(past_year)
        img_now = fetch_img(current_year)
        
        if img_old is None or img_now is None:
            return "Tanlangan hudud uchun sun'iy yo'ldosh tasvirlari topilmadi."

        # Suv maskalari va tahlili
        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.05)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.05)
        erosion = mask_old.And(mask_now.Not()).selfMask()
        future_risk = mask_now.focal_max(radius=300, units='meters').And(mask_now.Not()).selfMask()

        def calc_area(m):
            try:
                area = m.multiply(ee.Image.pixelArea()).reduceRegion(
                    reducer=ee.Reducer.sum(), 
                    geometry=region_ee, 
                    scale=calc_scale, 
                    maxPixels=1e10
                )
                val = area.get('nd')
                return int(ee.Number(val or 0).divide(10000).round().getInfo())
            except: return 0

        a_old = calc_area(mask_old)
        a_now = calc_area(mask_now)
        a_ero = calc_area(erosion)
        a_fut = int(a_now * 1.15) 

        # VIZUALIZATSIYA
        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
        v_params = {'region': region_ee.bounds(), 'scale': 30, 'format': 'png'}
        
        url1 = img_old.visualize(**vis).getThumbURL(v_params)
        url2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#ffff00'], opacity=1.0)).getThumbURL(v_params)
        url3 = img_now.visualize(**vis).blend(future_risk.visualize(palette=['#ff0000'], opacity=0.8)).getThumbURL(v_params)
        
        return url1, url2, url3, a_old, a_now, a_fut, a_ero
            
    except Exception as e:
        return f"Tizim xatosi: {str(e)}"

# --- 🚀 ASOSIY EKRAN ---
st.markdown("<h1>🌊 AMUDARYO AI-DEFORMRISK MONITOR PRO</h1>", unsafe_allow_html=True)
st.subheader("📍 Tahlil maydonini xaritada belgilang")

m = folium.Map(location=[41.5, 60.5], zoom_start=8, tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google Satellite")
folium.plugins.Draw(export=False, draw_options={'polyline':False, 'polygon':False, 'circle':False, 'marker':False, 'circlemarker':False, 'rectangle':True}).add_to(m)
map_output = st_folium(m, width="100%", height=400, key="amu_map")

# --- 🔍 TAHLILNI ISHGA TUSHIRISH (TO'G'RILANGAN QISM) ---
if map_output['last_active_drawing']:
    if st.button("🔍 TANLANGAN HUDUDNI ANALIZ QILISH"):
        with st.spinner("🛰 Kvant serverlar tahlil o'tkazmoqda..."):
            try:
                # Koordinatalarni GEE Polygoniga aylantirish
                raw_coords = map_output['last_active_drawing']['geometry']['coordinates'][0]
                region_ee = ee.Geometry.Polygon(raw_coords)
                
                # Natijalarni tahlil qilish va session_state'ga saqlash
                res = analyze_full_spectrum(region_ee)
                st.session_state.analysis_results = res
                st.rerun() # Natijani ko'rsatish uchun sahifani yangilash
            except Exception as e:
                st.error(f"Tahlilni boshlashda xatolik: {e}")

# --- 📊 NATIJALARNI KO'RSATISH ---
if st.session_state.analysis_results:
    res = st.session_state.analysis_results
    if isinstance(res, str):
        st.error(f"❌ {res}")
    else:
        u1, u2, u3, a1, a2, af, aero = res
        
        st.markdown("### 🛰 MULTI-SPEKTRAL MONITORING")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<p style='text-align:center;'>📅 {past_year}-YIL (TARIX)</p>", unsafe_allow_html=True)
            st.image(u1, use_container_width=True)
            st.markdown(f"<div class='metric-card'>Maydon: {a1} GA</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<p style='text-align:center; color:#ffff00;'>📅 {current_year}-YIL (SARIQ: O'PIRILISH)</p>", unsafe_allow_html=True)
            st.image(u2, use_container_width=True)
            st.markdown(f"<div class='metric-card'>⚠️ Yuvilgan: {aero} GA</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<p style='text-align:center; color:#ff4b4b;'>📅 {future_year}-YIL (QIZIL: XAVF)</p>", unsafe_allow_html=True)
            st.image(u3, use_container_width=True)
            st.markdown(f"<div class='metric-card'>Bashorat: {af} GA</div>", unsafe_allow_html=True)

        st.divider()
        st.markdown("### 📈 DINAMIK O'ZGARISHLAR VA BASHORAT")

        df_chart = pd.DataFrame({
            'Davr': [f"{past_year}", f"{current_year}", f"{future_year}"],
            'Maydon (ga)': [a1, a2, af]
        })

        fig = px.area(df_chart, x='Davr', y='Maydon (ga)', text='Maydon (ga)', markers=True, template="plotly_dark")
        fig.update_traces(line_color='#00f2ff', fillcolor='rgba(0, 242, 255, 0.2)', marker=dict(size=12, color='#ffffff'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Orbitron", color="#00f2ff"))
        st.plotly_chart(fig, use_container_width=True)

        risk_color = "#ff4b4b" if aero > 15 else "#00f2ff"
        risk_text = "YUQORI" if aero > 15 else "O'RTA" if aero > 5 else "BARQAROR"
        advice = "Tezkor qirg'oqni mustahkamlash lozim." if aero > 15 else "Monitoringni davom ettirish tavsiya etiladi."

        st.markdown(f"""
            <div class="report-box-dynamic" style="border-left-color: {risk_color};">
                <h3 style='color: {risk_color};'>📑 EKSPERTIZANING RASMIY BAYONNOMASI</h3>
                <p style="font-size: 1.15rem;">
                    Tizim tahliliga ko'ra, xavf darajasi: <b style="color:{risk_color};">{risk_text}</b>. <br>
                    Oxirgi 7 yil ichida <b>{aero} gektar</b> qirg'oq yuvilgan.
                </p>
                <p style="font-size: 1.1rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                    <b>💡 Tavsiya:</b> {advice}
                </p>
            </div>
        """, unsafe_allow_html=True)

if st.sidebar.button("🔌 TIZIMNI O'CHIRISH"):
    st.session_state.auth = False
    st.session_state.analysis_results = None
    st.rerun()
