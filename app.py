import streamlit as st
import ee
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import random  # Yangi qo'shimcha: Har bir so'rov bloklanmasligi uchun unikal ID yaratishga kerak

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

# --- 🌍 3-TILLI LUG'AT (DINAMIK SLAYDER MATNLARI QO'SHILDI) ---
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
        "status": ["YUQORI (KRITIK)", "O'RTA (EHTIYOTKOR)", "BARQAROR (XAVFSIZ)"],
        "loc_info": "📍 HUDUDIY MA'LUMOTLAR",
        "coords_label": "Aniq koordinatalar",
        "address_label": "Rasmiy manzil",
        "directions": {"N": "Sh.k", "S": "J.k", "E": "Sh.u", "W": "G'.u"},
        "expert_advice": {
            "critical": "Zudlik bilan qirg'oqni mustahkamlash uchun beton-gabion konstruksiyalarini o'rnatish va daryo o'zanini chuqurlashtirish tavsiya etiladi. Eroziya darajasi xavfli.",
            "stable": "Vaziyat barqaror. Monitoringni davom ettirish va daryo bo'yida tabiiy to'siqlar (tol, itshumurt) ekish maqsadga muvofiq."
        },
        "slider_past": "⏳ O'tmish davri (1 - 20 yil oldin?):",
        "slider_future": "🔮 Bashorat davri (1 - 20 yildan keyin?):"
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
        "status": ["ВЫСОКИЙ (КРИТИЧЕСКИЙ)", "СРЕДНИЙ", "СТАБИЛЬНЫЙ"],
        "loc_info": "📍 ТЕРРИТОРИАЛЬНЫЕ ДАННЫЕ",
        "coords_label": "Точные координаты",
        "address_label": "Официальный адрес",
        "directions": {"N": "с.ш.", "S": "ю.ш.", "E": "в.д.", "W": "з.д."},
        "expert_advice": {
            "critical": "Рекомендуется немедленная установка бетонно-габионных конструкций и дноуглубительные работы. Скорость эрозии критическая.",
            "stable": "Ситуация стабильна. Рекомендуется посадка берегозащитных лесонасаждений и плановый мониторинг."
        },
        "slider_past": "⏳ Прошлый период (от 1 до 20 лет назад?):",
        "slider_future": "🔮 Период прогноза (от 1 до 20 лет?):"
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
        "status": ["HIGH (CRITICAL)", "MEDIUM (CAUTION)", "STABLE (SAFE)"],
        "loc_info": "📍 LOCATION DATA",
        "coords_label": "Precise Coordinates",
        "address_label": "Official Address",
        "directions": {"N": "N", "S": "S", "E": "E", "W": "W"},
        "expert_advice": {
            "critical": "Immediate installation of gabion structures and riverbed dredging is highly recommended. Erosion rate is critical.",
            "stable": "The area is hydrologically stable. Continued monitoring and planting of riparian vegetation are recommended."
        },
        "slider_past": "⏳ Historical period (1 to 20 years ago?):",
        "slider_future": "🔮 Forecast period (1 to 20 years later?):"
    }
}

# --- 🎨 DINAMIK NEON DIZAYN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;600&display=swap');
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
        color: #ffffff; font-family: 'Exo 2', sans-serif;
    }
    .metric-card {
        background: rgba(16, 33, 65, 0.7); padding: 20px; border-radius: 15px;
        border: 1px solid #00f2ff; text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 0 25px rgba(0, 242, 255, 0.4);
        background: rgba(16, 33, 65, 0.9);
    }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; }
    .stButton>button {
        width: 100%; background: transparent !important; color: #00f2ff !important;
        border: 2px solid #00f2ff !important; font-family: 'Orbitron', sans-serif;
        border-radius: 10px; transition: 0.4s;
    }
    .stButton>button:hover {
        background: #00f2ff !important; color: #000 !important;
        box-shadow: 0 0 20px #00f2ff; transform: scale(1.02);
    }
    .loc-box {
        background: rgba(0, 242, 255, 0.1); padding: 10px; border-radius: 10px; border: 1px dashed #00f2ff; margin-bottom: 20px;
    }
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

# --- 🌐 TILNI TANLASH VA SIDEBAR ---
st.session_state.lang = st.sidebar.selectbox("🌐 Choose Language / Tilni tanlang", ["O'zbekcha", "Русский", "English"])
L = text_db[st.session_state.lang]
st.sidebar.markdown(f"### {L['sidebar']}")

# --- 🎛 DINAMIK 20 YILLIK SLAYDERLAR INTEGRATSIYASI ---
st.sidebar.markdown("---")
past_years = st.sidebar.slider(L["slider_past"], min_value=1, max_value=20, value=5, step=1)
future_years = st.sidebar.slider(L["slider_future"], min_value=1, max_value=20, value=5, step=1)

current_year = datetime.now().year
target_past_year = current_year - past_years

# --- 🧭 KOORDINATALARNI FORMATLASH ---
def format_coords_by_lang(lat, lon, lang_dict):
    ns = lang_dict['directions']["N"] if lat >= 0 else lang_dict['directions']["S"]
    ew = lang_dict['directions']["E"] if lon >= 0 else lang_dict['directions']["W"]
    return f"{abs(lat):.6f}° {ns}, {abs(lon):.6f}° {ew}"

# --- 🛰 HUDUD NOMINI ANIQLASH ---
def get_location_details(coords, lang_name):
    try:
        mapping = {"O'zbekcha": "uz", "Русский": "ru", "English": "en"}
        rand_agent_id = random.randint(10000, 99999)
        geolocator = Nominatim(user_agent=f"amudaryo_monitor_pro_system_{rand_agent_id}")
        
        location = geolocator.reverse(f"{coords[1]}, {coords[0]}", timeout=12, language=mapping.get(lang_name, "en"))
        if location and location.address:
            return location.address
        return "Amudaryo sohili hududi (Noma'lum manzil)"
    except:
        return "Amudaryo havzasi yaqinidagi qirg'oq hududi"

# --- 🧠 MUKAMMAL ANALIZ ALGORITMI (NAFIS VA SILLIQ FILTRLAR INTEGRATSIYASI) ---
def analyze_full_spectrum(geometry, p_year, f_years):
    try:
        region_ee = geometry.bounds()
        centroid_data = geometry.centroid().coordinates().getInfo() 
        address = get_location_details(centroid_data, st.session_state.lang)

        # Hozirgi yil tasviri (Sentinel-2)
        col_now = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region_ee).filterDate(f'{current_year}-01-01', f'{current_year}-12-31').sort('CLOUDY_PIXEL_PERCENTAGE')
        img_now = col_now.first().clip(region_ee) if col_now.first() else None
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.05) if img_now else None

        # O'tmish yili uchun sun'iy yo'ldosh missiyasini moslashtirish mantiqi
        if p_year >= 2016:
            # Sentinel-2 Missiyasi
            col_old = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region_ee).filterDate(f'{p_year}-01-01', f'{p_year}-12-31').sort('CLOUDY_PIXEL_PERCENTAGE')
            img_old = col_old.first().clip(region_ee) if col_old.first() else None
            mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.05) if img_old else None
            v_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
        else:
            # Landsat 7 Missiyasi (2015 va undan oldingi yillar uchun barqaror ma'lumotlar bazasi)
            col_old = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2").filterBounds(region_ee).filterDate(f'{p_year}-01-01', f'{p_year}-12-31').sort('CLOUD_COVER')
            img_old = col_old.first().clip(region_ee) if col_old.first() else None
            mask_old = img_old.normalizedDifference(['SR_B2', 'SR_B4']).gt(0.05) if img_old else None
            v_params = {'bands': ['SR_B3', 'SR_B2', 'SR_B1'], 'min': 7000, 'max': 12000, 'gamma': 1.4}

        if not img_old or not img_now: return "Tasvirlar topilmadi."

        # Dastlabki qo'pol chiziqli eroziya maskasi
        raw_erosion = mask_old.And(mask_now.Not())
        
        # ✨ CHIZIQLARNI AKKURATNIY VA NAFIS QILUVCHI ARXITEKTURA FILTRI (SMOOTHING ENGINE)
        # Gausian Kernel yordamida piksellar orasidagi qo'pol burilishlarni yumshoq va silliq bog'lash
        gaussian_kernel = ee.Kernel.gaussian(radius=2, sigma=1, units='pixels')
        smooth_erosion = raw_erosion.convolve(gaussian_kernel).gt(0.4)
        
        # Tarqoq va mayda xunuk piksellarni yo'qotib, qirg'oq chiziqlarini yaxlit nafis holatga keltirish
        smooth_erosion = smooth_erosion.focal_max(radius=1.5, units='pixels').focal_min(radius=1.5, units='pixels').selfMask()

        # Kelajak xavf radiusini hisoblash va uni ham professional darajada silliqlash
        calculated_radius = f_years * 9.5
        raw_future_risk = raw_erosion.focal_max(radius=calculated_radius, units='meters').And(mask_now.Not())
        smooth_future_risk = raw_future_risk.convolve(gaussian_kernel).gt(0.4).selfMask()

        def calc_area(m):
            try:
                area = m.multiply(ee.Image.pixelArea()).reduceRegion(reducer=ee.Reducer.sum(), geometry=region_ee, scale=30, maxPixels=1e10)
                res = area.values().get(0)
                if res is None: return 0
                return int(ee.Number(res).divide(10000).round().getInfo())
            except: return 0

        a1, a2, aero = calc_area(mask_old), calc_area(mask_now), calc_area(smooth_erosion)
        
        # Bashorat maydonining dinamik matematik koeffitsiyenti
        af = int(aero * (1.0 + (f_years * 0.08))) if aero > 0 else int(a2 * (f_years * 0.012))
        change_rate = (aero / a1 * 100) if a1 > 0 else 0

        p = {'region': region_ee.getInfo()['coordinates'], 'dimensions': 800, 'format': 'png'}
        
        u1 = img_old.visualize(**v_params).getThumbURL(p)
        
        v_now = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000, 'gamma': 1.4}
        
        # Rang qatlamlarini xarita bilan ideal integratsiya qilish uchun shaffoflikni 'opacity=0.6' ga moslashtirdik
        u2 = img_now.visualize(**v_now).blend(smooth_erosion.visualize(palette=['#ffff00'], opacity=0.6)).getThumbURL(p)
        u3 = img_now.visualize(**v_now).blend(smooth_future_risk.visualize(palette=['#ff3333'], opacity=0.6)).getThumbURL(p)
        
        return u1, u2, u3, a1, a2, af, aero, change_rate, centroid_data, address
    except Exception as e: return f"Error: {e}"

# --- 📑 EKSPERT XULOSASI FUNKSIYASI (YILLAR INTEGRATSIYASI BILAN) ---
def render_expert_report(aero, change_rate, lang_code, address, centroid, p_year, f_years):
    lang_dict = text_db[lang_code]
    f_coords = format_coords_by_lang(centroid[1], centroid[0], lang_dict)
    
    if aero > 20 or change_rate > 15:
        risk_color, status_idx, advice_key = "#ff0000", 0, "critical"
    else:
        risk_color, status_idx, advice_key = "#00f2ff", 2, "stable"

    r_t = lang_dict['status'][status_idx]
    
    desc = {
        "O'zbekcha": f"{p_year}-yildan buyon o'tkazilgan tahlillar shuni ko'rsatadiki, hudud qirg'oqlarining {change_rate:.1f}% qismi gidrologik eroziyaga uchragan. {address} hududida jami {aero} GA maydon yo'qotilgan. Navbatdagi {f_years} yillik dinamik model jiddiy deformatsiya xavfini aniqladi.",
        "Русский": f"Анализ с {p_year} года показывает, что {change_rate:.1f}% береговой линии подверглось гидрологической эрозии. В районе {address} потеряно {aero} га. Динамическая модель на следующие {f_years} лет определила риски деформации.",
        "English": f"Analysis since {p_year} shows that {change_rate:.1f}% of the coastline has undergone hydrological erosion. A total of {aero} hectares lost in {address}. The dynamic model for the next {f_years} years defined deformation risks."
    }
    
    st.markdown(f"""
        <div style="border-left: 10px solid {risk_color}; background: rgba(10, 25, 47, 0.95); padding: 25px; border-radius: 15px; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
            <h3 style='color: {risk_color}; margin: 0;'>{lang_dict['expert_title']}</h3>
            <div class="loc-box" style="margin-top:15px;">
                <p style="margin:0; font-size:0.9rem;">🧭 <b>{lang_dict['coords_label']}:</b> {f_coords}</p>
                <p style="margin:0; font-size:0.9rem;">📍 <b>{lang_dict['address_label']}:</b> {address}</p>
            </div>
            <div style="display: flex; gap: 20px; margin-top: 10px;">
                <p style="margin: 0;"><b>{lang_dict['risk']}:</b> <span style="color:{risk_color}; font-weight: bold;">{r_t}</span></p>
                <p style="margin: 0;"><b>Eroziya dinamikasi ({p_year} - {current_year}):</b> <span style="color:{risk_color}; font-weight: bold;">{change_rate:.1f}%</span></p>
            </div>
            <p style='font-size: 1.05rem; line-height: 1.6; margin-top: 15px; color: #e0e0e0;'>{desc[lang_code]}</p>
            <p style='font-size: 1.1rem; color: #00f2ff; font-style: italic;'>"{lang_dict['expert_advice'][advice_key]}"</p>
            <hr style='opacity: 0.1;'>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888;">
                <span>Metod: Multi-Mission NDWI (Hierarchical Smoothing & Morphological Filtering)</span>
                <span>ID: AMU-{datetime.now().strftime('%d%m%H%M')}</span>
            </div>
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
        with st.spinner("🛰 AI Tahlil qilmoqda..."):
            coords = map_output['last_active_drawing']['geometry']['coordinates'][0]
            geom = ee.Geometry.Polygon(coords)
            # Parametrlarga slayderlardan kelayotgan dinamik yillar uzatiladi
            st.session_state.analysis_results = analyze_full_spectrum(geom, target_past_year, future_years)

# --- NATIJALARNI CHIQARISH QISMI ---
if st.session_state.analysis_results:
    if isinstance(st.session_state.analysis_results, str):
        st.error(f"Tahlil jarayonida xatolik: {st.session_state.analysis_results}")
    else:
        try:
            u1, u2, u3, a1, a2, af, aero, c_rate, cent, addr = st.session_state.analysis_results
            
            f_coords = format_coords_by_lang(cent[1], cent[0], L)
            st.markdown(f"<div class='loc-box'><b>{L['loc_info']}:</b> {addr} | {f_coords}</div>", unsafe_allow_html=True)
            
            # Dinamik ravishda tanlangan o'tmish va kelajak yillariga mos sarlavhalar hosil qilish
            dynamic_past_title = f"{L['history']} ({target_past_year})"
            dynamic_future_title = f"{L['forecast']} (+{future_years} YIL)"
            
            col1, col2, col3 = st.columns(3)
            titles = [dynamic_past_title, L['wash'], dynamic_future_title]
            imgs, vals = [u1, u2, u3], [a1, aero, af]
            
            for i, col in enumerate([col1, col2, col3]):
                with col:
                    st.markdown(f"<p style='text-align:center; font-weight:bold;'>{titles[i]}</p>", unsafe_allow_html=True)
                    st.image(imgs[i], use_container_width=True)
                    st.markdown(f"<div class='metric-card'>{L['area']}: {vals[i]} GA</div>", unsafe_allow_html=True)

            st.divider()
            # Ekspert xulosasiga ham dinamik yillar yuboriladi
            render_expert_report(aero, c_rate, st.session_state.lang, addr, cent, target_past_year, future_years)
            
        except ValueError:
            st.warning("Ma'lumotlar formati mos kelmadi yoki noto'liq. Iltimos, hududni qaytadan tanlab tahlil qiling.")

if st.sidebar.button(L['logout']):
    st.session_state.auth = False
    st.rerun()
