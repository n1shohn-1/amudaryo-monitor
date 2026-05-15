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

# --- 🧠 SESSION STATE (O'ZGARISHSIZ + TIL QO'SHILDI) ---
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'lang' not in st.session_state:
    st.session_state.lang = "O'zbekcha"

# --- 🌍 MULTILINGUAL DICTIONARY (3 TA TIL LUG'ATI) ---
text_db = {
    "O'zbekcha": {
        "title": "🌊 AMUDARYO AI-DEFORMRISK MONITOR PRO",
        "map_sub": "📍 Tahlil maydonini xaritada belgilang",
        "btn": "🔍 TANLANGAN HUDUDNI ANALIZ QILISH",
        "sidebar": "🛠 TIZIM BOSHQARUVI",
        "history": "TARIX",
        "current": "HOZIRGI",
        "forecast": "BASHORAT",
        "area_label": "Maydon",
        "wash_label": "Yuvilgan",
        "risk_label": "XAVF DARAJASI",
        "chart_title": "📊 HUDUDIY DINAMIKA VA KVANT PROGNOZ",
        "expert": "📑 EKSPERTIZANING RASMIY BAYONNOMASI",
        "auth_title": "TIZIMGA KIRISH",
        "auth_key": "MAXFIY KALIT:",
        "auth_btn": "FAOLLASHTIRISH",
        "logout": "🔌 TIZIMNI O'CHIRISH"
    },
    "Русский": {
        "title": "🌊 АМУДАРЬЯ AI-DEFORMRISK MONITOR PRO",
        "map_sub": "📍 Отметьте область анализа на карте",
        "btn": "🔍 АНАЛИЗИРОВАТЬ ВЫБРАННУЮ ОБЛАСТЬ",
        "sidebar": "🛠 УПРАВЛЕНИЕ СИСТЕМОЙ",
        "history": "ИСТОРИЯ",
        "current": "ТЕКУЩИЙ",
        "forecast": "ПРОГНОЗ",
        "area_label": "Площадь",
        "wash_label": "Размыто",
        "risk_label": "УРОВЕНЬ РИСКА",
        "chart_title": "📊 ТЕРРИТОРИАЛЬНАЯ ДИНАМИКА И КВАНТОВЫЙ ПРОГНОЗ",
        "expert": "📑 ОФИЦИАЛЬНЫЙ ОТЧЕТ ЭКСПЕРТИЗЫ",
        "auth_title": "ВХОД В СИСТЕМУ",
        "auth_key": "СЕКРЕТНЫЙ КЛЮЧ:",
        "auth_btn": "АКТИВИРОВАТЬ",
        "logout": "🔌 ВЫЙТИ ИЗ СИСТЕМЫ"
    },
    "English": {
        "title": "🌊 AMUDARYA AI-DEFORMRISK MONITOR PRO",
        "map_sub": "📍 Mark the analysis area on the map",
        "btn": "🔍 ANALYZE SELECTED AREA",
        "sidebar": "🛠 SYSTEM CONTROL",
        "history": "HISTORY",
        "current": "CURRENT",
        "forecast": "FORECAST",
        "area_label": "Area",
        "wash_label": "Eroded",
        "risk_label": "RISK LEVEL",
        "chart_title": "📊 REGIONAL DYNAMICS & QUANTUM FORECAST",
        "expert": "📑 OFFICIAL EXPERT REPORT",
        "auth_title": "SYSTEM LOGIN",
        "auth_key": "SECRET KEY:",
        "auth_btn": "ACTIVATE",
        "logout": "🔌 SHUTDOWN SYSTEM"
    }
}
L = text_db[st.session_state.lang]

# --- 🎨 JILVADOR MODERN CYBER DIZAYN (KODINGIZDAN YAXSHILANDI) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }}
    [data-testid="stSidebar"] {{ background: rgba(10, 25, 47, 0.95) !important; border-right: 2px solid #00f2ff; }}
    .metric-card {{
        background: rgba(16, 33, 65, 0.8); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
        transition: 0.3s;
    }}
    .metric-card:hover {{ transform: scale(1.05); box-shadow: 0 0 25px #00f2ff; }}
    h1, h2, h3 {{ font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; text-transform: uppercase; text-shadow: 0 0 10px #00f2ff; }}
    .stButton>button {{
        width: 100%; background: linear-gradient(45deg, #00f2ff, #0072ff) !important; color: white !important;
        border: none !important; font-family: 'Orbitron', sans-serif; transition: 0.4s; border-radius: 10px;
    }}
    .stButton>button:hover {{ box-shadow: 0 0 20px #00f2ff; transform: translateY(-2px); }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 XAVFSIZLIK TIZIMI ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    _, col_auth, _ = st.columns([1,1.2,1])
    with col_auth:
        st.markdown(f"<h2 style='text-align: center;'>{L['auth_title']}</h2>", unsafe_allow_html=True)
        pw = st.text_input(L['auth_key'], type="password")
        if st.button(L['auth_btn']):
            if pw == "Amudaryo_AI":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Xato kalit!")
    st.stop()

# --- 🛰 BOSHQARUV ---
st.sidebar.image("https://img.icons8.com/fluency/96/river.png", width=80)
st.session_state.lang = st.sidebar.selectbox("🌐 Language / Til", ["O'zbekcha", "Русский", "English"])
st.sidebar.markdown(f"### {L['sidebar']}")

current_year = datetime.now().year
past_year = current_year - 7
future_year = current_year + 5

# --- 🧠 MUKAMMAL ANALIZ ALGORITMI (ASL HOLIDA SAQLANDI) ---
def analyze_full_spectrum(geometry):
    try:
        region_ee = geometry.bounds()
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

        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.05)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.05)
        erosion = mask_old.And(mask_now.Not()).selfMask()
        future_risk = mask_now.focal_max(radius=300, units='meters').And(mask_now.Not()).selfMask()

        def calc_area(m):
            try:
                area = m.multiply(ee.Image.pixelArea()).reduceRegion(
                    reducer=ee.Reducer.sum(), geometry=region_ee, scale=calc_scale, maxPixels=1e10
                )
                val = area.get('nd')
                if val is None: return 0
                return int(ee.Number(val).divide(10000).round().getInfo())
            except: return 0

        a_old, a_now, a_ero = calc_area(mask_old), calc_area(mask_now), calc_area(erosion)
        a_fut = int(a_now * 1.1) 

        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
        v_params = {'region': region_ee.getInfo()['coordinates'], 'dimensions': 800, 'format': 'png'}
        
        url1 = img_old.visualize(**vis).getThumbURL(v_params)
        url2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#ffff00'], opacity=1.0)).getThumbURL(v_params)
        url3 = img_now.visualize(**vis).blend(future_risk.visualize(palette=['#ff0000'], opacity=0.8)).getThumbURL(v_params)
        
        return url1, url2, url3, a_old, a_now, a_fut, a_ero
    except Exception as e:
        return f"Tizim xatosi: {str(e)}"

# --- 🚀 ASOSIY EKRAN ---
st.markdown(f"<h1>{L['title']}</h1>", unsafe_allow_html=True)
st.subheader(L['map_sub'])

m = folium.Map(location=[41.5, 60.5], zoom_start=8, tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google Satellite")
folium.plugins.Draw(export=False, draw_options={'polyline':False, 'polygon':False, 'circle':False, 'marker':False, 'circlemarker':False, 'rectangle':True}).add_to(m)
map_output = st_folium(m, width="100%", height=400, key="amu_map")

if map_output['last_active_drawing']:
    if st.button(L['btn']):
        with st.spinner("🛰..."):
            coords = map_output['last_active_drawing']['geometry']['coordinates'][0]
            st.session_state.analysis_results = analyze_full_spectrum(ee.Geometry.Polygon(coords))

if st.session_state.analysis_results:
    res = st.session_state.analysis_results
    if isinstance(res, str): st.error(f"❌ {res}")
    else:
        u1, u2, u3, a1, a2, af, aero = res
        st.markdown(f"### 🛰 MULTI-SPEKTRAL MONITORING ({st.session_state.lang})")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<p style='text-align:center;'>📅 {past_year}-YIL ({L['history']})</p>", unsafe_allow_html=True)
            st.image(u1, use_container_width=True)
            st.markdown(f"<div class='metric-card'>{L['area_label']}: {a1} GA</div>", unsafe
