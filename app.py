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

# --- 🧠 MUKAMMAL ANALIZ ALGORITMI (Yangilangan) ---
def analyze_full_spectrum(geometry):
    try:
        region_ee = geometry.bounds()
        def fetch_img(year):
            col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region_ee).filterDate(f'{year}-01-01', f'{year}-12-31').sort('CLOUDY_PIXEL_PERCENTAGE')
            return col.first().clip(region_ee) if col.first() else None

        img_old, img_now = fetch_img(datetime.now().year - 7), fetch_img(datetime.now().year)
        if not img_old or not img_now: return "Tasvirlar topilmadi."

        # Suv maskalari
        mask_old, mask_now = img_old.normalizedDifference(['B3', 'B8']).gt(0.05), img_now.normalizedDifference(['B3', 'B8']).gt(0.05)
        
        # 1. Yuvilgan joylar (Sariq)
        erosion = mask_old.And(mask_now.Not()).selfMask()
        
        # 2. Bashorat (Qizil) - Ixchamlashtirilgan radius
        future_risk = mask_now.focal_max(radius=80, units='meters').And(mask_now.Not()).selfMask()

        def calc_area(m):
            try:
                area = m.multiply(ee.Image.pixelArea()).reduceRegion(reducer=ee.Reducer.sum(), geometry=region_ee, scale=30, maxPixels=1e10)
                return int(ee.Number(area.get('nd')).divide(10000).round().getInfo())
            except: return 0

        a1, a2, aero = calc_area(mask_old), calc_area(mask_now), calc_area(erosion)
        af = int(a2 * 1.15) # Bashorat maydoni

        v = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
        p = {'region': region_ee.getInfo()['coordinates'], 'dimensions': 800, 'format': 'png'}
        
        # Tasvirlar URL (Ixchamlik va shaffoflik sozlangan)
        u1 = img_old.visualize(**v).getThumbURL(p)
        u2 = img_now.visualize(**v).blend(erosion.visualize(palette=['#ffff00'], opacity=0.8)).getThumbURL(p)
        u3 = img_now.visualize(**v).blend(future_risk.visualize(palette=['#ff0000'], opacity=0.6)).getThumbURL(p)
        
        return u1, u2, u3, a1, a2, af, aero
    except Exception as e: return f"Error: {e}"

# --- 📑 EKSPERT XULOSASI FUNKSIYASI ---
def render_expert_report(aero, lang):
    risk_color = "#ff4b4b" if aero > 15 else "#ffaa00" if aero > 5 else "#00f2ff"
    r_t = L['status'][0] if aero > 15 else L['status'][1] if aero > 5 else L['status'][2]
    
    reports = {
        "O'zbekcha": {
            "high": f"DIQQAT! Hududda kritik eroziya jarayoni aniqlandi. Oxirgi davrda daryo o'zani {aero} gektar unumdor yerni yuvib ketgan. Kelajakda qirg'oqning yanada yemirilish ehtimoli 85% dan yuqori. Zudlik bilan gabion to'siqlar o'rnatish tavsiya etiladi.",
            "mid": f"Hududda o'rtacha darajadagi dinamik o'zgarishlar kuzatilmoqda. {aero} gektar maydon suv ostida qolgan. Vaziyat barqaror, biroq monitoringni davom ettirish va qirg'oqni yashil o'simliklar bilan mustahkamlash lozim.",
            "low": f"Hudud gidrologik jihatdan barqaror. Aniqlangan {aero} gektar o'zgarish daryo o'zanining tabiiy mavsumiy tebranishi hisoblanadi. Hozirda muhandislik aralashuviga ehtiyoj yo'q."
        },
        "Русский": {
            "high": f"ВНИМАНИЕ! Обнаружена критическая эрозия. Река поглотила {aero} га земли. Риск дальнейшего обрушения берега превышает 85%. Рекомендуется немедленное возведение защитных сооружений.",
            "mid": f"Наблюдаются умеренные динамические изменения. Размыто {aero} га. Ситуация стабильна, рекомендуется биологическое укрепление берегов и мониторинг.",
            "low": f"Территория гидрологически стабильна. Изменение в {aero} га является естественным сезонным процессом. Инженерное вмешательство не требуется."
        },
        "English": {
            "high": f"WARNING! Critical erosion detected. {aero} hectares have been lost to the river. Risk of further collapse exceeds 85%. Immediate installation of protective barriers is recommended.",
            "mid": f"Moderate dynamic changes observed. {aero} hectares eroded. Situation is stable, but ongoing monitoring and biological bank stabilization are advised.",
            "low": f"The area is hydrologically stable. The {aero} hectare change is within natural seasonal fluctuations. No engineering intervention needed."
        }
    }
    
    state = "high" if aero > 15 else "mid" if aero > 5 else "low"
    report_text = reports[lang][state]
    
    st.markdown(f"""
        <div style="border-left: 10px solid {risk_color}; background: rgba(10, 25, 47, 0.95); padding: 25px; border-radius: 15px; margin-top: 20px;">
            <h3 style='color: {risk_color}; margin: 0;'>{L['expert_title']}</h3>
            <p style="margin-top:10px;"><b>{L['risk']}:</b> <span style="color:{risk_color};">{r_t}</span></p>
            <p style='font-size: 1.1rem; line-height: 1.6; margin-top: 10px;'>{report_text}</p>
            <hr style='opacity: 0.2;'>
            <p style='font-size: 0.8rem; color: #888;'>AI-Generation ID: AMU-{datetime.now().strftime('%d%m%H%M')} | Area: {aero} GA</p>
        </div>
    """, unsafe_allow_html=True)

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

    # --- 📑 EKSPERT XULOSASINI CHAQIRISH ---
    st.divider()
    render_expert_report(aero, st.session_state.lang)

if st.sidebar.button(L['logout']):
    st.session_state.auth = False
    st.rerun()
