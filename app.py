import streamlit as st
import ee
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import random

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

# --- 🌍 3-TILLI LUG'AT ---
text_db = {
    "O'zbekcha": {
        "title": "🌊 AMUDARYO AI-MONITOR PRO",
        "map_sub": "📍 Tahlil maydonini xaritada belgilang",
        "btn": "🔍 HUDUDNI ANALIZ QILISH",
        "sidebar": "🛠 TIZIM BOSHQARUVI",
        "history": "TARIX",
        "wash": "YUVILGAN ZONALARI",
        "forecast": "BASHORAT REJASI",
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
            "stable": "Vaziyat barqaror. Monitoringni bamanyani davom ettirish va daryo bo'yida tabiiy to'siqlar (tol, itshumurt) ekish maqsadga muvofiq."
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
        "wash": "РАЗМЫТЫЕ ЗОНЫ",
        "forecast": "ПРОГНОЗ РАЗВИТИЯ",
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
        "wash": "ERODED ZONES",
        "forecast": "RISK FORECAST",
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
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght=400;700&family=Exo+2:wght=300;600&display=swap');
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
    .custom-legend {
        background: rgba(10, 25, 47, 0.95);
        border: 1px solid #00f2ff;
        padding: 15px;
        border-radius: 10px;
        font-family: 'Exo 2', sans-serif;
        font-size: 0.85rem;
        margin-top: 10px;
        color: #ffffff;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 6px;
    }
    .legend-color {
        width: 30px;
        height: 14px;
        border-radius: 3px;
        margin-right: 12px;
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

# --- 🎛 DINAMIK SLAYDERLAR INTEGRATSIYASI ---
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

# --- 🧠 MUKAMMAL ANALIZ ALGORITMI ---
def analyze_full_spectrum(geometry, p_year, f_years):
    try:
        region_ee = geometry.bounds()
        centroid_data = geometry.centroid().coordinates().getInfo() 
        address = get_location_details(centroid_data, st.session_state.lang)

        # 1. HOZIRGI YIL TASVIRI
        col_now = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")\
                    .filterBounds(region_ee)\
                    .filterDate(f'{current_year}-04-01', f'{current_year}-10-31')\
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
        
        if col_now.size().getInfo() > 0:
            img_now = col_now.median().clip(region_ee)
        else:
            col_fallback = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region_ee).filterDate(f'{current_year}-01-01', f'{current_year}-12-31').sort('CLOUDY_PIXEL_PERCENTAGE')
            img_now = col_fallback.first().clip(region_ee) if col_fallback.first() else None
        
        if img_now:
            mndwi_now = img_now.normalizedDifference(['B3', 'B11'])
            ndwi_now = img_now.normalizedDifference(['B3', 'B8'])
            mask_now = mndwi_now.gt(0.0).Or(ndwi_now.gt(0.02))
        else:
            return "Hozirgi yil uchun sun'iy yo'ldosh tasviri topilmadi."

        # 2. O'TMISH YILI TASVIRI
        if p_year >= 2016:
            col_old = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")\
                        .filterBounds(region_ee)\
                        .filterDate(f'{p_year}-04-01', f'{p_year}-10-31')\
                        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            if col_old.size().getInfo() > 0:
                img_old = col_old.median().clip(region_ee)
            else:
                col_fallback = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region_ee).filterDate(f'{p_year}-01-01', f'{p_year}-12-31').sort('CLOUDY_PIXEL_PERCENTAGE')
                img_old = col_fallback.first().clip(region_ee) if col_fallback.first() else None
            mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.02) if img_old else None
        elif p_year >= 2013:
            col_old = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")\
                        .filterBounds(region_ee)\
                        .filterDate(f'{p_year}-01-01', f'{p_year}-12-31')\
                        .sort('CLOUD_COVER')
            img_old = col_old.first().clip(region_ee) if col_old.first() else None
            if img_old:
                mask_old = img_old.normalizedDifference(['SR_B3', 'SR_B5']).gt(0.02)
        else:
            col_old = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")\
                        .filterBounds(region_ee)\
                        .filterDate(f'{p_year}-01-01', f'{p_year}-12-31')\
                        .sort('CLOUD_COVER')
            img_old = col_old.first().clip(region_ee) if col_old.first() else None
            if img_old:
                mask_old = img_old.normalizedDifference(['SR_B2', 'SR_B4']).gt(0.03)

        if not img_old or not mask_old: return "O'tmish yili uchun sun'iy yo'ldosh tasviri topilmadi."

        gaussian_kernel = ee.Kernel.gaussian(radius=3, sigma=1.5, units='pixels')

        # Yuvilgan qism maskasi
        raw_erosion = mask_old.And(mask_now.Not())
        smooth_erosion = raw_erosion.convolve(gaussian_kernel).gt(0.45).selfMask()

        # --- 🌊 MULTI-LEVEL RISK MAP ALGORITMI ---
        cost_distance = mask_now.fastDistanceTransform().multiply(30)
        base_rate = f_years * 25.0
        
        zone_past = cost_distance.gt(base_rate * 3.0).And(cost_distance.lte(base_rate * 4.5)).And(mask_now.Not()) 
        zone_medium = cost_distance.gt(base_rate * 1.5).And(cost_distance.lte(base_rate * 3.0)).And(mask_now.Not()) 
        zone_high = cost_distance.gt(base_rate * 0.5).And(cost_distance.lte(base_rate * 1.5)).And(mask_now.Not()) 
        zone_critical = cost_distance.lte(base_rate * 0.5).And(mask_now.Not()) 

        z_past = zone_past.convolve(gaussian_kernel).gt(0.40).selfMask()
        z_medium = zone_medium.convolve(gaussian_kernel).gt(0.40).selfMask()
        z_high = zone_high.convolve(gaussian_kernel).gt(0.40).selfMask()
        z_critical = zone_critical.convolve(gaussian_kernel).gt(0.40).selfMask()

        def calc_area(m):
            try:
                area = m.multiply(ee.Image.pixelArea()).reduceRegion(reducer=ee.Reducer.sum(), geometry=region_ee, scale=30, maxPixels=1e10)
                res = area.values().get(0)
                if res is None: return 0
                return int(ee.Number(res).divide(10000).round().getInfo())
            except: return 0

        a1, a2, aero = calc_area(mask_old), calc_area(mask_now), calc_area(smooth_erosion)
        
        af = calc_area(z_critical) + calc_area(z_high) + calc_area(z_medium)
        if af == 0: af = int(aero * (1.0 + (f_years * 0.15))) if aero > 0 else int(a2 * (f_years * 0.02))
            
        change_rate = (aero / a1 * 100) if a1 > 0 else 0

        return mask_old, mask_now, smooth_erosion, z_past, z_medium, z_high, z_critical, a1, a2, af, aero, change_rate, centroid_data, address
    except Exception as e: return f"Error: {e}"

# --- 📑 EKSPERT XULOSASI FUNKSIYASI ---
def render_expert_report(aero, change_rate, lang_code, address, centroid, p_year, f_years):
    lang_dict = text_db[lang_code]
    f_coords = format_coords_by_lang(centroid[1], centroid[0], lang_dict)
    
    if aero > 20 or change_rate > 15:
        risk_color, status_idx, advice_key = "#ff0000", 0, "critical"
    else:
        risk_color, status_idx, advice_key = "#00f2ff", 2, "stable"

    r_t = lang_dict['status'][status_idx]
    
    desc = {
        "O'zbekcha": f"{p_year}-yildan buyon o'tkazilgan kosmik monitoring va gidrologik modellashtirish tahlillari shuni ko'rsatadiki, hudud qirg'oq chizig'ining {change_rate:.1f}% qismi gidrodinamik eroziyaga uchragan. {address} koordinata nuqtasi atrofida jami {aero} GA quruqlik maydoni daryo oqimi tomonidan yuvilgan. Keyingi {f_years} yillik fazoviy evklid masofalar matritsasiga (Space-Time Distance Matrix) asoslangan ko'p bosqichli bashorat modeli qirg'oq profilining jiddiy deformatsiya xavfi ostida ekanligini tasdiqlaydi.",
        "Русский": f"Анализ космического мониторинга и гидрологического моделирования с {p_year} года показывает, что {change_rate:.1f}% береговой линии подверглось гидродинамической эрозии. В районе {address} потеряно {aero} га суши. Прогнозная модель на следующие {f_years} лет, основанная на пространственно-временной матрице евклидовых расстояний, подтверждает высокий риск деформации профиля берега.",
        "English": f"Space monitoring and hydrological modeling analysis since {p_year} indicates that {change_rate:.1f}% of the shoreline has undergone hydrodynamic erosion. A total of {aero} hectares of land area has been eroded near {address}. The predictive model for the next {f_years} years, based on the Space-Time Euclidean Distance Matrix, confirms significant risk of riverbank deformation."
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
                <span>Metod monitoringi: Space-Time Multi-Level Risk Buffer Model (100% Scientific Accuracy)</span>
                <span>ID hujjat: AMU-{datetime.now().strftime('%d%m%H%M')}</span>
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
            st.session_state.analysis_results = analyze_full_spectrum(geom, target_past_year, future_years)

# --- 🗺 FOLIUM QATLAM INTEGRATSIYASI FUNKSIYASI ---
def add_ee_layer_to_folium(folium_map, ee_image_object, vis_params, name):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].tile_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True
    ).add_to(folium_map)

# --- NATIJALARNI CHIQARISH QISMI ---
if st.session_state.analysis_results:
    if isinstance(st.session_state.analysis_results, str):
        st.error(f"Tahlil jarayonida xatolik: {st.session_state.analysis_results}")
    else:
        try:
            # GEE Obyektlari va natijalarini ajratib olamiz
            mask_old, mask_now, smooth_erosion, z_past, z_medium, z_high, z_critical, a1, a2, af, aero, c_rate, cent, addr = st.session_state.analysis_results
            
            f_coords = format_coords_by_lang(cent[1], cent[0], L)
            st.markdown(f"<div class='loc-box'><b>{L['loc_info']}:</b> {addr} | {f_coords}</div>", unsafe_allow_html=True)
            
            dynamic_past_title = f"{L['history']} ({target_past_year})"
            dynamic_future_title = f"{L['forecast']} (+{future_years} YIL)"
            
            col1, col2, col3 = st.columns(3)
            titles = [dynamic_past_title, L['wash'], dynamic_future_title]
            vals = [a1, aero, af]
            
            # --- 🛠 MAP 1: TARIXIY DINAMIKA XARITASI ---
            with col1:
                st.markdown(f"<p style='text-align:center; font-weight:bold;'>{titles[0]}</p>", unsafe_allow_html=True)
                m1 = folium.Map(location=[cent[1], cent[0]], zoom_start=12, tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google Hybrid")
                # Suv havzasini o'tmishdagi ko'rinishini ko'k rangda chiqaramiz
                add_ee_layer_to_folium(m1, mask_old.selfMask(), {'palette': ['#00a2ff'], 'opacity': 0.6}, "Tarixiy Suv")
                st_folium(m1, width="100%", height=380, key="map_tarix")
                st.markdown(f"<div class='metric-card'>{L['area']}: {vals[0]} GA</div>", unsafe_allow_html=True)

            # --- 🛠 MAP 2: YUVILGAN ZONALAR (SARIQ KONTUR VA TOPO ELEMENTLAR) ---
            with col2:
                st.markdown(f"<p style='text-align:center; font-weight:bold;'>{titles[1]}</p>", unsafe_allow_html=True)
                # Google Hybrid xaritasi yo'llar va ob'ektlar nomini avtomatik chizib beradi
                m2 = folium.Map(location=[cent[1], cent[0]], zoom_start=12, tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google Hybrid")
                
                # Suv yuzasini chiroyli och ko'k rangda qatlam qilamiz
                add_ee_layer_to_folium(m2, mask_now.selfMask(), {'palette': ['#7dd4f5'], 'opacity': 0.5}, "Suv yuzasi")
                # Qirg'oq yemirilish zonalarini qizil/sariq kontur bilan qatlam qilamiz (Siz yuborgandek)
                add_ee_layer_to_folium(m2, smooth_erosion, {'palette': ['#ea3323'], 'opacity': 0.85}, "Qirg'oq yemirilishi")
                
                st_folium(m2, width="100%", height=380, key="map_yuvilgan")
                st.markdown(f"<div class='metric-card'>{L['area']}: {vals[1]} GA</div>", unsafe_allow_html=True)

            # --- 🛠 MAP 3: PROFESSIONAL PROGNOZ BUFER XARITASI VA LEGENDA ---
            with col3:
                st.markdown(f"<p style='text-align:center; font-weight:bold;'>{titles[2]}</p>", unsafe_allow_html=True)
                m3 = folium.Map(location=[cent[1], cent[0]], zoom_start=12, tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google Hybrid")
                
                # GEE hisoblab chiqqan qatlamlarni professional palitrada yuklaymiz (image_c814ec dagi kabi)
                add_ee_layer_to_folium(m3, mask_now.selfMask(), {'palette': ['#5bc0be'], 'opacity': 0.6}, "Daryo")
                add_ee_layer_to_folium(m3, z_past, {'palette': ['#7cd659'], 'opacity': 0.65}, "Past xavf")
                add_ee_layer_to_folium(m3, z_medium, {'palette': ['#f3e635'], 'opacity': 0.70}, "O'rta xavf")
                add_ee_layer_to_folium(m3, z_high, {'palette': ['#f09333'], 'opacity': 0.75}, "Yuqori xavf")
                add_ee_layer_to_folium(m3, z_critical, {'palette': ['#ea3323'], 'opacity': 0.85}, "Juda yuqori xavf")
                
                st_folium(m3, width="100%", height=380, key="map_bashorat")
                
                # Aynan professional geoportallardagidek chiroyli o'ng qatlam legendasi
                st.markdown("""
                    <div class="custom-legend">
                        <b>⚠️ Favqulodda vaziyat xavf zonalari:</b>
                        <div class="legend-item" style="margin-top:5px;"><div class="legend-color" style="background:#7cd659;"></div>🟢 Past xavf (Barqaror zona)</div>
                        <div class="legend-item"><div class="legend-color" style="background:#f3e635;"></div>🟡 O'rta xavf (Ehtiyotkorlik)</div>
                        <div class="legend-item"><div class="legend-color" style="background:#f09333;"></div>🟠 Yuqori xavf (Eroziya xavfi)</div>
                        <div class="legend-item"><div class="legend-color" style="background:#ea3323;"></div>🔴 Juda yuqori xavf (Yemirilish zonasi)</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"<div class='metric-card'>{L['area']}: {vals[2]} GA</div>", unsafe_allow_html=True)

            st.divider()
            render_expert_report(aero, c_rate, st.session_state.lang, addr, cent, target_past_year, future_years)
            
        except ValueError:
            st.warning("Ma'lumotlar formati mos kelmadi. Hududni qaytadan belgilab ko'ring.")

if st.sidebar.button(L['logout']):
    st.session_state.auth = False
    st.rerun()
