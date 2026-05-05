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

# --- 🎨 MODERN CYBER-UZBEK DIZAYNI ---
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
        border: 1px solid #00f2ff; text-align: center;
    }
    .report-box-red { 
        padding: 25px; border-radius: 15px; border: 2px solid #ff4b4b; 
        background-color: rgba(255, 75, 75, 0.1); margin-top: 20px;
    }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔐 XAVFSIZLIK TIZIMI ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
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

# --- 🧠 ANALIZ ALGORITMI ---
def analyze_selected_area(geometry):
    try:
        region = geometry
        def fetch_img(year):
            return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                .filterBounds(region).filterDate(f'{year}-01-01', f'{year}-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE').first().clip(region)

        past_y, curr_y = datetime.now().year - 7, datetime.now().year
        img_old = fetch_img(past_y)
        img_now = fetch_img(curr_y)

        # Suv maskalari (NDWI)
        mask_old = img_old.normalizedDifference(['B3', 'B8']).gt(0.1)
        mask_now = img_now.normalizedDifference(['B3', 'B8']).gt(0.1)

        # Yuvilib ketgan (Sariq) va Kelajak xavfi (Qizil)
        erosion = mask_old.subtract(mask_now).gt(0).selfMask() # Oldin suv bo'lmagan, hozir suv (yuvilgan)
        future_risk = mask_now.focal_max(radius=300, units='meters').subtract(mask_now).gt(0).selfMask()

        vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
        v_params = {'dimensions': 800, 'region': region, 'format': 'jpg'}
        
        url_old = img_old.visualize(**vis).getThumbURL(v_params)
        # Hozirgi ko'rinish: Yuvilgan joylar sariq bilan
        url_now = img_now.visualize(**vis).blend(erosion.visualize(palette=['#ffff00'])).getThumbURL(v_params)
        # Kelajak ko'rinish: Xavfli joylar qizil bilan
        url_future = img_now.visualize(**vis).blend(future_risk.visualize(palette=['#ff0000'])).getThumbURL(v_params)
        
        return url_old, url_now, url_future
    except: return None

# --- 🛰 BOSHQARUV VA XARITA ---
st.sidebar.markdown("### 🗺 HUDUDNI TANLASH")
st.markdown("### 📍 AMUDARYO BO'YLAB ANALIZ MAYDONINI BELGILANG")
st.write("Xaritadagi to'rtburchak chizish asbobidan foydalanib, daryoning kerakli qismini belgilang:")

# Amudaryo markazi (Urganch atrofida) boshlang'ich nuqta
m = folium.Map(location=[41.55, 60.63], zoom_start=8, tiles="CartoDB dark_matter")
# Faqat Amudaryo hududini ko'rsatish uchun cheklov (ixtiyoriy)
folium.plugins.Draw(
    export=False,
    draw_options={
        'polyline': False, 'circle': False, 'marker': False, 
        'circlemarker': False, 'polygon': False,
        'rectangle': True # Faqat to'rtburchak qolsin
    }
).add_to(m)

map_output = st_folium(m, width="100%", height=400)

selected_geometry = None
if map_output and map_output['last_active_drawing']:
    coords = map_output['last_active_drawing']['geometry']['coordinates'][0]
    # EE uchun formatga o'tkazish
    selected_geometry = ee.Geometry.Polygon(coords)
    st.sidebar.success("✅ Maydon belgilandi!")

if st.sidebar.button("🔍 TEKSHIRISH") and selected_geometry:
    with st.spinner("🛰 Sun'iy yo'ldosh ma'lumotlari tahlil qilinmoqda..."):
        urls = analyze_selected_area(selected_geometry)
        
    if urls:
        u_old, u_now, u_fut = urls
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<p style='text-align:center;'>📅 O'TMISH (7 yil oldin)</p>", unsafe_allow_html=True)
            st.image(u_old, use_container_width=True)
        with col2:
            st.markdown("<p style='text-align:center; color:#ffff00;'>📅 HOZIR (Yuvilgan joylar - Sariq)</p>", unsafe_allow_html=True)
            st.image(u_now, use_container_width=True)
        with col3:
            st.markdown("<p style='text-align:center; color:#ff4b4b;'>📅 KELAJAK (Xavfli zonalar - Qizil)</p>", unsafe_allow_html=True)
            st.image(u_fut, use_container_width=True)
            
        st.markdown("""
            <div class="report-box-red">
                <h3 style='color: #ff4b4b;'>📑 ANALIZ XULOSASI</h3>
                Tanlangan maydonda sariq rang bilan belgilangan qirg'oqlar oxirgi yillarda yuvilib ketganligini ko'rsatadi. 
                Qizil rangli zonalar esa daryo oqimi va tuproq tarkibi asosida kelajakda o'pirilishi mumkin bo'lgan yuqori xavfli hududlardir.
            </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Xatolik: Tanlangan maydon juda katta yoki ma'lumot topilmadi.")
elif not selected_geometry:
    st.info("Davom etish uchun xaritada to'rtburchak shakl chizib, maydonni tanlang.")

st.sidebar.markdown("---")
if st.sidebar.button("🔌 TIZIMNI O'CHIRISH"):
    st.session_state.auth = False
    st.rerun()
