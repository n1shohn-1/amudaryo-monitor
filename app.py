import streamlit as st
import ee
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# 1. Sahifa dizayni va sozlamalar
st.set_page_config(page_title="Amudaryo AI-Monitor Pro", layout="wide", initial_sidebar_state="expanded")

# --- 🛰 GOOGLE EARTH ENGINE ULANISHI (Tuzatilgan versiya) ---
try:
    if "earth_engine" in st.secrets:
        # Secrets-dan JSON kalitni o'qiymiz
        ee_key_raw = st.secrets["earth_engine"]["json_key"]
        ee_key_dict = json.loads(ee_key_raw)
        
        # Servis akkaunt orqali autentifikatsiya
        credentials = ee.ServiceAccountCredentials(
            ee_key_dict['client_email'], 
            key_data=ee_key_raw
        )
        # LOYIHA ID-sini aniq ko'rsatish (Xatolikni oldini oladi)
        ee.Initialize(credentials, project='ee-nusratullayev38')
    else:
        # Mahalliy muhit yoki alternativ ulanish
        ee.Initialize(project='ee-nusratullayev38')
except Exception as e:
    st.error(f"Google Earth Engine autentifikatsiya xatosi: {e}")
    st.stop()

# --- 🎨 PROFESSIONAL DIZAYN VA FON (Custom CSS) ---
st.markdown("""
    <style>
    /* Asosiy fon uchun rasm va effekt */
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.8)), 
        url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
        background-attachment: fixed;
        color: #e2e8f0;
    }
    
    /* Bloklarni shaffof va chiroyli qilish */
    [data-testid="stSidebar"] {
        background-color: rgba(30, 41, 59, 0.95) !important;
    }
    
    .stMarkdown, .stMetric, div[data-testid="stBlock"] {
        color: white !important;
    }

    [data-testid="stMetric"] {
        background-color: rgba(255, 235, 59, 0.1) !important; 
        border: 1px solid #FFEB3B;
        padding: 15px; border-radius: 12px;
    }
    
    .report-box-red { 
        padding: 25px; border-radius: 15px; border: 2px solid #ef4444; 
        background-color: rgba(220, 38, 38, 0.2); color: #fecaca; margin-top: 20px;
    }
    
    /* Tugmalarni dasturchi uslubida qilish */
    .stButton>button {
        border-radius: 8px;
        background-color: #3b82f6;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        box-shadow: 0 0 15px #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 PAROL HIMOYASI ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br><h1 style='text-align: center; color: #60a5fa;'>🔐 Amudaryo AI-Monitor Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Tizim himoyalangan. Foydalanish uchun parolni kiriting.</p>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns([1,1,1])
    with col_p2:
        password = st.text_input("Parol:", type="password")
        if st.button("Tizimga kirish"):
            if password == "Amudaryo_AI": 
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Parol noto'g'ri!")
    st.stop()

# --- ASOSIY INTERFEYS ---
if 'started' not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.markdown("""
        <div style="text-align: center; padding: 50px; background: rgba(30, 58, 138, 0.4); border-radius: 20px; border: 1px solid #3b82f6;">
            <h1 style="color: #60a5fa;">🌊 Amudaryo AI-DeformRisk Monitor</h1>
            <p style="font-size: 1.2rem;">Kiber-texnologiyalar va sun'iy yo'ldosh tahlili asosida daryo monitoringi</p>
            <hr style="border: 0.1px solid #3b82f6; width: 50%; margin: auto;">
            <p>Loyiha Shahzod tomonidan ishlab chiqilgan va litsenziyalangan.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([2,1,2])
    with col_btn2:
        if st.button("🚀 Monitoringni boshlash", use_container_width=True):
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- SIDEBAR VA TAHLIL ---
st.sidebar.image("https://img.icons8.com/fluency/96/river.png", width=80)
st.sidebar.title("📍 Boshqaruv")
locations = {
    "Urganch": [41.55, 60.63], "Nukus": [42.45, 59.60],
    "Termiz": [37.22, 67.27], "Tuyamuyun": [41.22, 61.38]
}
selected_city = st.sidebar.selectbox("Hududni tanlang:", list(locations.keys()))
radius = st.sidebar.slider("Tahlil radiusi (m):", 1000, 10000, 4000)

if st.sidebar.button("🔄 Chiqish"):
    st.session_state.authenticated = False
    st.session_state.started = False
    st.rerun()

current_year = datetime.now().year
past_year = current_year - 10
future_year = current_year + 5

st.title(f"📊 {selected_city} hududi tahlili")
st.write(f"Hozirgi vaqt: {current_year}")

def analyze_river(coords, radius):
    point = ee.Geometry.Point(coords[1], coords[0])
    region = point.buffer(radius).bounds()
    def get_landsat(year):
        return ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(region).filterDate(f'{year}-01-01', f'{year}-12-31').sort('CLOUD_COVER').first()
    
    img_old = get_landsat(past_year)
    img_now = get_landsat(current_year)
    
    if not img_old or not img_now: return None
    
    mask_old = img_old.normalizedDifference(['SR_B3', 'SR_B5']).rename('w').gt(0.1)
    mask_now = img_now.normalizedDifference(['SR_B3', 'SR_B5']).rename('w').gt(0.1)
    
    erosion = mask_now.subtract(mask_old).gt(0).selfMask()
    retreat = mask_old.subtract(mask_now).gt(0).selfMask()
    
    def get_area(mask):
        area = mask.multiply(ee.Image.pixelArea()).reduceRegion(reducer=ee.Reducer.sum(), geometry=region, scale=30, maxPixels=1e9)
        return ee.Number(area.get('w', 0)).divide(10000).round().getInfo()
    
    area_old = get_area(mask_old)
    area_now = get_area(mask_now)
    area_ero = get_area(erosion)
    area_ret = get_area(retreat)
    
    change_rate = (area_now - area_old) / 10
    area_fut = int(area_now + (change_rate * 5))
    
    future_risk = erosion.focal_max(radius=350, units='meters').selfMask()
    
    vis = {'bands': ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 30000}
    v_params = {'dimensions': 800, 'format': 'jpg', 'region': region}
    
    u1 = img_old.visualize(**vis).getThumbURL(v_params)
    u2 = img_now.visualize(**vis).blend(erosion.visualize(palette=['#0000FF'], opacity=0.8)).blend(retreat.visualize(palette=['#FFFF00'], opacity=0.8)).getThumbURL(v_params)
    u3 = img_now.visualize(**vis).blend(future_risk.visualize(palette=['#FF00FF'], opacity=0.7)).getThumbURL(v_params)
    
    return u1, u2, u3, area_old, area_now, area_ero, area_ret, area_fut

with st.spinner("🛰 Tahlil qilinmoqda..."):
    results = analyze_river(locations[selected_city], radius)

if results:
    u1, u2, u3, a_old, a_now, a_ero, a_ret, a_fut = results
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"⏪ {past_year}-yil")
        st.image(u1, use_container_width=True)
    with col2:
        st.success(f"📍 {current_year}-yil")
        st.image(u2, use_container_width=True)
        st.write(f"🔵 Yemirilgan: **{a_ero} ga** | 🟡 Qurigan: **{a_ret} ga**")
    with col3:
        st.error(f"⏩ {future_year}-yil")
        st.image(u3, use_container_width=True)
    
    st.divider()
    chart_data = pd.DataFrame({'Yil': [past_year, current_year, future_year], 'Maydon (ga)': [a_old, a_now, a_fut], 'Holat': ["O'tmish", "Hozir", "Bashorat"]})
    fig = px.line(chart_data, x='Yil', y='Maydon (ga)', markers=True, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Yakuniy Ekspert Xulosasi")
    risk_level = "YUQORI" if a_ero > 40 else "O'RTA"
    st.markdown(f"""
    <div class="report-box-red">
        <h4>⚠️ Xavf darajasi: {risk_level}</h4>
        <p>Oxirgi 10 yilda <b>{a_ero} gektar</b> yer yemirilgan. Kelgusi 5 yilda AI bashorati bo'yicha yana <b>{abs(a_fut - a_now)} gektar</b> xavf ostida.</p>
        <p><b>💡 Tavsiya:</b> Qirg'oq mustahkamlash ishlarini jadallashtirish lozim.</p>
    </div>
    """, unsafe_allow_html=True)
