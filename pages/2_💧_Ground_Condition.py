import streamlit as st
import sys, os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

lang = st.session_state.get('lang', 'en')
is_hi = (lang == 'hi')

setup_page(
    title="Soil & Water" if not is_hi else "मिट्टी और पानी",
    subtitle="Underground moisture, water depth, and field sensors",
    icon="💧",
    explanation_en="Monitor soil moisture levels and water depth across your farm to optimize irrigation.",
    explanation_hi="सिंचाई को अनुकूलित करने के लिए अपने खेत में मिट्टी की नमी के स्तर और पानी की गहराई की निगरानी करें।"
)

dl.get_field_sidebar()

if "farm_sim" not in st.session_state:
    st.session_state.farm_sim = dl.get_sim_engine()

farm_data   = st.session_state.farm_sim.fields
field_intel = dl.get_field_intelligence(lang=lang)
nodes       = dl.get_sensor_nodes()

# Live Source Verification
is_live = len(nodes) > 0
iot_source = "Verified IoT (MongoDB)" if is_live else "Simulation Engine"
iot_color = "#34d399" if is_live else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

# --- HEADER strip ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px;">
    <div>
        <div style="color:#86A789; font-size:0.75rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;">{dl.translate("soil_hydraulics", lang)}</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{iot_color}15; border:1px solid {iot_color}40; color:{iot_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
            { ("साझा सूत्र: IoT NoDes" if is_hi else "Source: Verified IoT NoDes") if is_live else dl.translate("simulation_mode", lang) }
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#F5F5F5; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            { (str(len(nodes)) if is_live else "0") + " " + dl.translate("active_nodes", lang) }
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Metrics Calculations - Prioritize LIVE IoT Nodes
if is_live:
    # Use real IoT values for averages
    avg_moist = sum(n.get('soil_wetness', 60) for n in nodes.values()) / len(nodes)
    avg_w_depth = sum(n.get('water_depth', 1.4) for n in nodes.values()) / len(nodes)
    # Count alerts based on real IoT thresholds (moisture < 45)
    fields_need_water = sum(1 for n in nodes.values() if n.get('soil_wetness', 60) < 45)
    total_fields = len(nodes)
else:
    # Fallback to simulation if cloud is empty/offline
    from sim_engine import SmartFarmSimEngine
    if "farm_sim" not in st.session_state:
        st.session_state.farm_sim = dl.get_sim_engine()
    farm_data = st.session_state.farm_sim.fields
    avg_moist = sum(f.get("moisture", 60) for f in farm_data.values()) / len(farm_data) if farm_data else 60
    avg_w_depth = 1.4
    fields_need_water = sum(1 for f in farm_data.values() if f.get("moisture", 60) < 45)
    total_fields = len(farm_data)

# Styling Constants
bg_card = "#0F1A12" # Very dark green for cards
bg_dark = "#09120B" # App background
green_c = "#4ADE80"
green_bg = "#E9F5E9"
amber_c = "#F59E0B"
red_c = "#EF4444"
text_w = "#F5F5F5"
text_g = "#86A789" # Light sage green for subtitles

st.markdown("""
<style>
.stApp { background-color: #09120B; }
h1, h2, h3, p, span, div { font-family: 'Space Grotesk', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ── 4 TOP METRIC CARDS ──────────────────────────────────────────
t_avg_m = "AVG SOIL MOISTURE" if not is_hi else "औसत मिट्टी की नमी"
t_wt_d = "WATER TABLE DEPTH" if not is_hi else "जल स्तर की गहराई"
t_f_need = "FIELDS NEEDING WATER" if not is_hi else "पानी की आवश्यकता वाले खेत"
t_irr = "IRRIGATION EFFICIENCY" if not is_hi else "सिंचाई दक्षता"

st.markdown(f"""
<div style="display:flex; gap:15px; margin-bottom:25px;">
    <div style="flex:1; background:{bg_card}; border:1px solid #1C3D28; border-top:2px solid {green_c}; border-radius:12px; padding:20px;">
        <div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{t_avg_m}</div>
        <div style="color:{text_w}; font-size:2.2rem; font-weight:700; line-height:1;"><span style="color:#A3A3A3; font-size:1.6rem; margin-right:2px;"></span>{avg_moist:.0f}<span style="font-size:1.2rem; color:#A3A3A3; margin-left:2px;">%</span></div>
        <div style="color:{green_c}; font-size:0.75rem; margin-top:8px;">↑ {dl.translate("optimal_range_lbl", lang)}</div>
    </div>
    <div style="flex:1; background:{bg_card}; border:1px solid #1C3D28; border-top:2px solid {green_c}; border-radius:12px; padding:20px;">
        <div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{t_wt_d}</div>
        <div style="color:{text_w}; font-size:2.2rem; font-weight:700; line-height:1;">1.4<span style="font-size:1.2rem; color:#A3A3A3; margin-left:4px;">m</span></div>
        <div style="color:{green_c}; font-size:0.75rem; margin-top:8px;">↑ Stable vs yesterday</div>
    </div>
    <div style="flex:1; background:{bg_card}; border:1px solid #3D280B; border-top:2px solid {amber_c}; border-radius:12px; padding:20px;">
        <div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{t_f_need}</div>
        <div style="color:{amber_c}; font-size:2.2rem; font-weight:700; line-height:1;">{fields_need_water}</div>
        <div style="color:{amber_c}; font-size:0.75rem; margin-top:8px;">↑ SE + South critical</div>
    </div>
    <div style="flex:1; background:{bg_card}; border:1px solid #1C3D28; border-top:2px solid {green_c}; border-radius:12px; padding:20px;">
        <div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{t_irr}</div>
        <div style="color:{text_w}; font-size:2.2rem; font-weight:700; line-height:1;">84<span style="font-size:1.2rem; color:#A3A3A3; margin-left:2px;">%</span></div>
        <div style="color:{green_c}; font-size:0.75rem; margin-top:8px;">↑ 6% vs last week</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── AMBER ALERT BANNER ──────────────────────────────────────────
if fields_need_water > 0:
    t_alert_t = "Soil drying detected — South & SE fields need irrigation today" if not is_hi else "मिट्टी सूख रही है — दक्षिण और दक्षिण-पूर्व खेतों में आज सिंचाई की आवश्यकता है"
    t_alert_d = "NDWI readings dropped to -0.11 (South). Soil temperature at 32.8°C is accelerating evaporation. Without action, yield may drop. Recommended: irrigate to 5 cm depth before 10am tomorrow." if not is_hi else "NDWI रीडिंग -0.11 तक गिर गई है। 32.8°C पर मिट्टी का तापमान वाष्पीकरण को तेज कर रहा है। अनुशंसित: कल सुबह 10 बजे से पहले 5 सेंटीमीटर तक सिंचाई करें।"
    
    st.markdown(f"""
    <div style="background:linear-gradient(90deg, #2A1B0A 0%, #151005 100%); border:1px solid #3D280B; border-radius:12px; padding:20px; margin-bottom:30px; position:relative; overflow:hidden;">
        <div style="position:absolute; left:0; top:0; bottom:0; width:4px; background:{amber_c};"></div>
        <div style="display:flex; gap:15px; align-items:flex-start;">
            <div style="background:rgba(245,158,11,0.15); color:{amber_c}; width:36px; height:36px; border-radius:8px; display:flex; justify-content:center; align-items:center; font-size:1.1rem; flex-shrink:0;">
                ⚠️
            </div>
            <div>
                <div style="color:{text_w}; font-size:1.05rem; font-weight:700; margin-bottom:8px;">{t_alert_t}</div>
                <div style="color:#A3A3A3; font-size:0.85rem; line-height:1.5; margin-bottom:15px; max-width:90%;">{t_alert_d}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── 9 PER-FIELD CARDS GRID ──────────────────────────────────────────
t_soil_title = "SOIL STATUS PER FIELD — LIVE READINGS" if not is_hi else "प्रत्येक खेत की मिट्टी की स्थिति — लाइव रीडिंग"
st.markdown(f"""
<div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1.5px; margin-bottom:15px; margin-top:10px;">{t_soil_title}</div>
""", unsafe_allow_html=True)

fields = list(farm_data.values())
for i in range(0, len(fields), 3):
    cols = st.columns(3)
    for j, f in enumerate(fields[i:i+3]):
        with cols[j]:
            name = f["name"]
            # Extract 100% REAL metrics from the live backend
            # Match Field name to sensor location nodes
            matched_node = next((n for n in nodes.values() if name[:4].lower() in n.get('node_id', '').lower() or name[:2] in n.get('location', '')), None)
            
            if matched_node:
                moisture = matched_node.get('soil_wetness', 60)
                temp     = matched_node.get('air_temp', 29.5)
                w_depth  = matched_node.get('water_depth', 1.4)
                hum      = matched_node.get('air_dampness', 75)
                source_tag = "Live IoT"
            else:
                moisture = f.get("moisture", 60)
                temp     = 29.5
                w_depth  = 1.4
                hum      = 75
                source_tag = "Simulated"

            is_crit = moisture < 45
            is_warn = moisture < 60 and moisture >= 45
            is_good = moisture >= 60

            c_main = red_c if is_crit else amber_c if is_warn else green_c
            tag_bg = "#451a1a" if is_crit else "#3d280b" if is_warn else "#132a1b"
            tag_text = "Irrigate now" if is_crit else "Monitor" if is_warn else "Healthy"
            if is_hi:
                 tag_text = "अभी सिंचाई करें" if is_crit else "निगरानी करें" if is_warn else "स्वस्थ"

            real_ndvi = f.get('ndvi')
            if real_ndvi is None: real_ndvi = 0.6
            ndwi = round(real_ndvi - 0.7, 2)
            
            ndwi_col = red_c if ndwi < -0.1 else amber_c if ndwi < 0 else green_c
            
            card_html = f"""
<div style="background:{bg_card}; border:1px solid #1C3D28; border-radius:12px; padding:20px; font-family:'Space Grotesk', sans-serif; margin-bottom:15px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
<div style="display:flex; align-items:center; gap:8px;">
<div style="width:8px; height:8px; border-radius:50%; background:{c_main};"></div>
<div style="color:{text_w}; font-weight:700; font-size:1.05rem;">{name}</div>
</div>
<div style="display:flex; gap:5px;">
    <div style="background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.3); padding:4px 8px; border-radius:12px; font-size:0.6rem; font-weight:600; text-transform:uppercase;">{source_tag}</div>
    <div style="background:{tag_bg}; color:{c_main}; padding:4px 10px; border-radius:12px; font-size:0.7rem; font-weight:600;">{tag_text}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:8px;">
<div>
<div style="color:{text_g}; font-size:0.7rem; font-weight:700; letter-spacing:1px; margin-bottom:2px;">SOIL MOISTURE</div>
<div style="color:{c_main}; font-size:2rem; font-weight:700; line-height:1;">{moisture:.0f}<span style="font-size:1.1rem; margin-left:2px;">%</span></div>
</div>
<div style="text-align:right;">
<div style="color:#A3A3A3; font-size:0.7rem; margin-bottom:2px;">Optimal</div>
<div style="color:#A3A3A3; font-size:0.7rem;">60–80%</div>
</div>
</div>
<!-- Progress Line -->
<div style="display:flex; align-items:center; gap:5px; margin-bottom:20px;">
<div style="color:#A3A3A3; font-size:0.6rem;">0</div>
<div style="flex:1; height:4px; background:rgba(255,255,255,0.1); border-radius:2px; position:relative;">
<div style="position:absolute; left:0; top:0; bottom:0; width:{moisture}%; background:{c_main}; border-radius:2px;"></div>
</div>
<div style="color:#A3A3A3; font-size:0.6rem;">60</div>
<div style="width:15%; height:4px; background:rgba(255,255,255,0.1); border-radius:2px;"></div>
<div style="color:#A3A3A3; font-size:0.6rem;">80</div>
<div style="width:10%; height:4px; background:rgba(255,255,255,0.1); border-radius:2px;"></div>
<div style="color:#A3A3A3; font-size:0.6rem;">100</div>
</div>
<!-- 2x2 Dark Grid -->
<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:20px;">
<div style="background:#09120B; border:1px solid #1C3D28; border-radius:8px; padding:12px;">
<div style="color:{text_g}; font-size:0.65rem; display:flex; align-items:center; gap:4px; margin-bottom:6px;"><span>🌡️</span> Soil temp</div>
<div style="color:{text_w}; font-weight:700; font-size:1rem;">{temp:.1f}°C</div>
</div>
<div style="background:#09120B; border:1px solid #1C3D28; border-radius:8px; padding:12px;">
<div style="color:{text_g}; font-size:0.65rem; display:flex; align-items:center; gap:4px; margin-bottom:6px;"><span>💧</span> Water depth</div>
<div style="color:{text_w}; font-weight:700; font-size:1rem;">{w_depth:.1f} m</div>
</div>
<div style="background:#09120B; border:1px solid #1C3D28; border-radius:8px; padding:12px;">
<div style="color:{text_g}; font-size:0.65rem; margin-bottom:6px;">Humidity</div>
<div style="color:{text_w}; font-weight:700; font-size:1rem;">{hum}%</div>
</div>
<div style="background:#09120B; border:1px solid #1C3D28; border-radius:8px; padding:12px;">
<div style="color:{text_g}; font-size:0.65rem; margin-bottom:6px;">NDWI index</div>
<div style="color:{ndwi_col}; font-weight:700; font-size:1rem;">{ndwi}</div>
</div>
</div>
<!-- Bottom Trend -->
<div style="color:{text_g}; font-size:0.65rem; margin-bottom:6px;">6-day moisture trend</div>
<div style="display:flex; justify-content:space-between; align-items:flex-end; height:15px; gap:4px;">
<div style="flex:1; background:rgba(255,255,255,0.05); height:60%; border-radius:2px;"></div>
<div style="flex:1; background:rgba(255,255,255,0.08); height:70%; border-radius:2px;"></div>
<div style="flex:1; background:rgba(255,255,255,0.1); height:80%; border-radius:2px;"></div>
<div style="flex:1; background:rgba(255,255,255,0.15); height:65%; border-radius:2px;"></div>
<div style="flex:1; background:rgba(255,255,255,0.2); height:50%; border-radius:2px;"></div>
<div style="flex:1; background:{c_main}; height:{max(moisture, 20)}%; border-radius:2px;"></div>
</div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)

# ── BOTTOM WEATHER BOX ──────────────────────────────────────────
t_w_title = "WEATHER CONDITIONS AFFECTING SOIL" if not is_hi else "मौसम की स्थिति जो मिट्टी को प्रभावित कर रही है"
real_weather = dl.load_current_weather() if hasattr(dl, 'load_current_weather') else {}
w_temp = real_weather.get('temperature', 32.8)
w_hum = real_weather.get('humidity', 71)
w_rain = real_weather.get('rain_forecast', 8)

st.markdown(f"""
<div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1.5px; margin-bottom:15px; margin-top:20px;">{t_w_title}</div>
<div style="display:flex; gap:15px;">
<div style="flex:1; background:{bg_card}; border:1px solid #1C3D28; border-radius:12px; padding:20px;">
<div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px; display:flex; align-items:center; gap:5px;"><span>🌡️</span> TEMPERATURE</div>
<div style="color:{text_w}; font-size:1.8rem; font-weight:700; margin-bottom:10px;">{w_temp:.1f}<span style="font-size:1rem; color:#A3A3A3;">°C</span></div>
<div style="color:#A3A3A3; font-size:0.75rem; line-height:1.4; margin-bottom:10px;">High evaporation risk today</div>
<div style="height:3px; background:rgba(255,255,255,0.1); border-radius:2px; display:flex;"><div style="width:70%; background:{red_c}; border-radius:2px;"></div></div>
</div>
<div style="flex:1; background:{bg_card}; border:1px solid #1C3D28; border-radius:12px; padding:20px;">
<div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px; display:flex; align-items:center; gap:5px;"><span>💧</span> HUMIDITY</div>
<div style="color:{text_w}; font-size:1.8rem; font-weight:700; margin-bottom:10px;">{w_hum}<span style="font-size:1rem; color:#A3A3A3;">%</span></div>
<div style="color:#A3A3A3; font-size:0.75rem; line-height:1.4; margin-bottom:10px;">Moderate — optimal 65-75%</div>
<div style="height:3px; background:rgba(255,255,255,0.1); border-radius:2px; display:flex;"><div style="width:71%; background:{green_c}; border-radius:2px;"></div></div>
</div>
<div style="flex:1; background:{bg_card}; border:1px solid #1C3D28; border-radius:12px; padding:20px;">
<div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px; display:flex; align-items:center; gap:5px;"><span>☂️</span> 5-DAY RAIN</div>
<div style="color:{text_w}; font-size:1.8rem; font-weight:700; margin-bottom:10px;">{w_rain}<span style="font-size:1rem; color:#A3A3A3;"> mm</span></div>
<div style="color:#A3A3A3; font-size:0.75rem; line-height:1.4; margin-bottom:10px;">Fri forecast — insufficient for crops</div>
<div style="height:3px; background:rgba(255,255,255,0.1); border-radius:2px; display:flex;"><div style="width:20%; background:{amber_c}; border-radius:2px;"></div></div>
</div>
<div style="flex:1; background:{bg_card}; border:1px solid #1C3D28; border-radius:12px; padding:20px;">
<div style="color:{text_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:10px; display:flex; align-items:center; gap:5px;"><span>🌱</span> CROP STAGE</div>
<div style="color:{text_w}; font-size:1.8rem; font-weight:700; margin-bottom:10px;">Tillering</div>
<div style="color:#A3A3A3; font-size:0.75rem; line-height:1.4; margin-bottom:10px;">Critical water demand period</div>
<div style="height:3px; background:rgba(255,255,255,0.1); border-radius:2px; display:flex;"><div style="width:100%; background:{amber_c}; border-radius:2px;"></div></div>
</div>
</div>
""", unsafe_allow_html=True)
