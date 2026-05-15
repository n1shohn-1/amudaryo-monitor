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
if 'lang' not in st.session_state:
    st.session_state.lang = "O'zbekcha"
if "auth" not in st.session_state:
    st.session_state.auth = False

# --- 🌍 3-TILLI LUG'AT (TEXT_DB) ---
text_db = {
    "O'zbekcha": {
        "title": "🌊 AMUDARYO AI-MONITOR PRO",
        "map_sub": "📍 Tahlil maydonini xaritada belgilang",
        "btn": "🔍 HUDUDNI ANALIZ QILISH",
        "sidebar": "🛠 TIZIM BOSHQARUVI",
        "history": "TARIX",
        "wash": "YUVILGAN",
        "forecast": "BASHORAT",
        "area": "Maydon",
        "risk": "XAVF DARAJASI",
        "expert_title": "📑 EKSPERTIZANING RASMIY BAYONNOMASI",
        "auth_title": "TIZIMGA KIRISH",
        "auth_key": "MAXFIY KALIT:",
        "auth_btn": "FAOLLASHTIRISH",
        "logout": "🔌 TIZIMNI O'CHIRISH",
        "status": ["YUQORI (KRITIK)", "O'RTA (EHTIYOTKOR)", "BARQAROR (XAVFSIZ)"]
    },
    "Русский": {
        "title": "🌊 АМУДАРЬЯ AI-MONITOR PRO",
        "map_sub": "📍 Отметьте область на карте",
        "btn": "🔍 АНАЛИЗИРОВАТЬ ОБЛАСТЬ",
        "sidebar": "🛠 УПРАВЛЕНИЕ СИСТЕМОЙ",
        "history": "ИСТОРИЯ",
        "wash": "РАЗМЫТО",
        "forecast": "ПРОГНОЗ",
        "area": "Площадь",
        "risk": "УРОВЕНЬ РИСКА",
        "expert_title": "📑 ОФИЦИАЛЬНЫЙ ОТЧЕТ ЭКСПЕРТИЗЫ",
        "auth_title": "ВХОД В СИСТЕМУ",
        "auth_key": "СЕКРЕТНЫЙ КЛЮЧ:",
        "auth_btn": "АКТИВИРОВАТЬ",
        "logout": "🔌 ВЫЙТИ ИЗ СИСТЕМЫ",
        "status": ["ВЫСОКИЙ (КРИТИЧЕСКИЙ)", "СРЕДНИЙ", "СТАБИЛЬНЫЙ"]
    },
    "English": {
        "title": "🌊 AMUDARYA AI-MONITOR PRO",
        "map_sub": "📍 Mark the area on the map",
        "btn": "🔍 ANALYZE SELECTED AREA",
        "sidebar": "🛠 SYSTEM CONTROL",
        "history": "HISTORY",
        "wash": "ERODED",
        "forecast": "FORECAST",
        "area": "Area",
        "risk": "RISK LEVEL",
        "expert_title": "📑 OFFICIAL EXPERT REPORT",
        "auth_title": "SYSTEM LOGIN",
        "auth_key": "SECRET KEY:",
        "auth_btn": "ACTIVATE",
        "logout": "🔌 SHUTDOWN SYSTEM",
        "status": ["HIGH (CRITICAL)", "MEDIUM (CAUTION)", "STABLE (SAFE)"]
    }
}

# --- 🎨 DINAMIK NEON DIZAYN ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }}
    .metric-card {{
        background: rgba(16, 33, 65, 0.7); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 0 25px rgba(0, 242, 255, 0.4);
        background: rgba(16, 33, 65, 0.9);
    }}
    h1, h2, h3 {{ font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; }}
    .stButton>button {{
        width: 100%; background: transparent !important; color: #00f2ff !important;
        border: 2px solid #00f2ff !important; font-family: 'Orbitron', sans-serif;
        border-radius: 10px; transition: 0.4s;
    }}
    .stButton>button:hover {{
        background: #00f2ff !important; color: #000 !important;
        box-shadow: 0 0 20px #00f2ff; transform: scale(1.02);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 XAVFSIZLIK ---
if not st.session_state.auth:
    _, col_auth, _ = st.columns([1,1.2,1])
    with col_auth:
        L_auth = text_db[st.session_state.lang]
        st.markdown(f"<h2 style='text-align: center;'>{L_auth['auth_title']}</h2>", unsafe_allow_html=True)
        pw = st.text_input(L_auth['auth_key'], type="password")
        if st.button(L_auth['auth_btn']):
            if pw == "Amudaryo_AI":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Xato!")
    st.stop()

# --- 🌐 TILNI TANLASH ---
st.session_state.lang = st.sidebar.selectbox("🌐 Choose Language / Tilni tanlang", ["O'zbekcha", "Русский", "English"])
L = text_db[st.session_state.lang]
st.sidebar.markdown(f"### {L['sidebar']}")

# --- 🧠 EE ANALIZ ALGORITMI (O'ZGARISHSIZ) ---
def analyze_full_spectrum(geometry):
    try:
        region_ee = geometry.bounds()
        def fetch_img(year):
            col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region_ee).filterDate(f'{year}-01-01', f'{year}-12-31').sort('CLOUDY_PIXEL_PERCENTAGE')
            return col.first().clip(region_ee) if col.first() else None

        img_old, img_now = fetch_img(datetime.now().year - 7), fetch_img(datetime.now().year)
        if not img_old or not img_now: return "Tasvirlar topilmadi."

        mask_old, mask_now = img_old.normalizedDifference(['B3', 'B8']).gt(0.05), img_now.normalizedDifference(['B3', 'B8']).gt(0.05)
        erosion = mask_old.And(mask_now.Not()).selfMask()
        future_risk = mask_now.focal_max(radius=300, units='meters').And(mask_now.Not()).selfMask()

        def calc_area(m):
            try:
                area = m.multiply(ee.Image.pixelArea()).reduceRegion(reducer=ee.Reducer.sum(), geometry=region_ee, scale=30, maxPixels=1e10)
                return int(ee.Number(area.get('nd')).divide(10000).round().getInfo())
            except: return 0

        a1, a2, aero = calc_area(mask_old), calc_area(mask_now), calc_area(erosion)
        v = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
        p = {'region': region_ee.getInfo()['coordinates'], 'dimensions': 800, 'format': 'png'}
        
        return img_old.visualize(**v).getThumbURL(p), img_now.visualize(**v).blend(erosion.visualize(palette=['#ffff00'])).getThumbURL(p), img_now.visualize(**v).blend(future_risk.visualize(palette=['#ff0000'])).getThumbURL(p), a1, a2, int(a2*1.1), aero
    except Exception as e: return f"Error: {e}"

# --- 🚀 ASOSIY EKRAN ---
st.markdown(f"<h1>{L['title']}</h1>", unsafe_allow_html=True)
st.subheader(L['map_sub'])

m = folium.Map(location=[41.5, 60.5], zoom_start=8, tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google")
folium.plugins.Draw(export=False, draw_options={'polyline':False, 'polygon':False, 'circle':False, 'marker':False, 'rectangle':True}).add_to(m)
map_output = st_folium(m, width="100%", height=400)

if map_output['last_active_drawing']:
    if st.button(L['btn']):
        with st.spinner("🛰..."):
            st.session_state.analysis_results = analyze_full_spectrum(ee.Geometry.Polygon(map_output['last_active_drawing']['geometry']['coordinates'][0]))

if st.session_state.analysis_results and not isinstance(st.session_state.analysis_results, str):
    u1, u2, u3, a1, a2, af, aero = st.session_state.analysis_results
    col1, col2, col3 = st.columns(3)
    
    titles = [L['history'], L['wash'], L['forecast']]
    imgs = [u1, u2, u3]
    vals = [a1, aero, af]
    
    for i, col in enumerate([col1, col2, col3]):
        with col:
            st.markdown(f"<p style='text-align:center;'>{titles[i]}</p>", unsafe_allow_html=True)
            st.image(imgs[i], use_container_width=True)
            st.markdown(f"<div class='metric-card'>{L['area']}: {vals[i]} GA</div>", unsafe_allow_html=True)

    # --- 📑 EKSPERT XULOSASI (DINAMIK) ---
    st.divider()
    r_c = "#ff4b4b" if aero > 15 else "#ffaa00" if aero > 5 else "#00f2ff"
    r_t = L['status'][0] if aero > 15 else L['status'][1] if aero > 5 else L['status'][2]
    
    st.markdown(f"""
        <div style="border-left: 10px solid {r_c}; background: rgba(10, 25, 47, 0.9); padding: 25px; border-radius: 15px;">
            <h3 style='color: {r_c} !important;'>{L['expert_title']}</h3>
            <p><b>{L['risk']}:</b> <span style="color:{r_c};">{r_t}</span></p>
            <p><b>{L['area']} ({L['wash']}):</b> {aero} GA</p>
        </div>
    """, unsafe_allow_html=True)

if st.sidebar.button(L['logout']):
    st.session_state.auth = False
    st.rerun()
