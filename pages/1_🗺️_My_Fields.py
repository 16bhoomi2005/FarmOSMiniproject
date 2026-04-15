import streamlit as st
import sys, os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

lang = st.session_state.get('lang', 'en')
is_hi = (lang == 'hi')

setup_page(
    title="Field Map" if not is_hi else "खेत का नक्शा",
    subtitle="Visual breakdown of your farm zones",
    icon="🗺️",
    explanation_en="Select any zone on the map to see its specific condition and recommended actions without any complicated charts.",
    explanation_hi="किसी भी क्षेत्र की विशिष्ट स्थिति और सुझाई गई कार्रवाइयों को देखने के लिए मानचित्र पर उस क्षेत्र को चुनें।"
)
dl.get_field_sidebar()

# --- Design Tokens ---
accent_color = "#E8A020"
card_bg = "#0F1A12"
text_g = "#86A789"
text_w = "#F5F0E8"

# --- Live Data Fetching ---
field_intel = dl.get_field_intelligence(lang)
sectors = dl.get_sector_analysis()
nodes = dl.get_sensor_nodes()
iot_source = st.session_state.get('data_source_verification', 'Simulation Engine')
sat_source = st.session_state.get('sat_source_verification', 'Regional Heuristic')
is_live = "Verified" in iot_source or "Sentinel-2" in sat_source

i_source = "Verified Live Intelligence" if is_live else "Simulation Engine"
i_color = "#34d399" if is_live else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

from sim_engine import FIELD_NAMES
if "selected_field" not in st.session_state:
    st.session_state.selected_field = FIELD_NAMES[0]

# Metrics (Derived from live sectors or sim fallback)
fields_good = 0
fields_watch = 0
for f in FIELD_NAMES:
    s_data = sectors.get(f, {})
    ni = s_data.get('ndvi', 0.6)
    if ni >= 0.7: fields_good += 1
    elif ni >= 0.4: fields_watch += 1
total_f = len(FIELD_NAMES)
now_str = datetime.now().strftime("%d %b")

t_title = "Field Map" if not is_hi else "खेत का नक्शा"
t_f_total = f"{total_f} plots total · {now_str}" if not is_hi else f"{total_f} कुल खेत · {now_str}"
t_good = f"{fields_good} {'good' if not is_hi else 'सुरक्षित'}"
t_watch = f"{fields_watch} {'watch' if not is_hi else 'ध्यान दें'}"
t_select = "Select a plot" if not is_hi else "एक हिस्सा चुनें"

# Top Header Layout
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; border-bottom:1px solid #333; padding-bottom:15px; margin-bottom:20px; font-family:'Space Grotesk', sans-serif;">
    <div>
        <div style="font-size:1.8rem; color:#F5F5F5; font-weight:600;">{t_title}</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{i_color}15; border:1px solid {i_color}40; color:{i_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
            Source: {i_source}
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#F5F5F5; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            Updated {last_updated}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.3], gap="large")

# --- LEFT SIDE: THE GRID ---
with col_left:
    st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
<span style="color:#F5F5F5; font-size:1.1rem; font-family:'Space Grotesk', sans-serif;">{t_select}</span>
</div>
    """, unsafe_allow_html=True)
    
    # Grid configuration
    for i in range(0, len(FIELD_NAMES), 3):
        row_cols = st.columns(3)
        for j, name in enumerate(FIELD_NAMES[i:i+3]):
            s_data = sectors.get(name, {})
            score = s_data.get('ndvi', 0.6) * 100
            is_good = score >= 70
            is_crit = score < 45
            
            # Dynamic styling based on health
            dot_color = "#4ADE80" if is_good else "#F59E0B" if not is_crit else "#EF4444"
            status_text = "Good" if is_good else "Watch" if not is_crit else "Act"
            if is_hi:
                status_text = "सुरक्षित" if is_good else "ध्यान दें" if not is_crit else "खतरे में"
                
            is_selected = (st.session_state.selected_field == name)
            border_c = "#E8A020" if is_selected else "rgba(255,255,255,0.05)"
            bg_c = "rgba(232,160,32,0.08)" if is_selected else "#1A1A18"
            
            # Render interactive component
            with row_cols[j]:
                # Transparent overlay trick for interactive cards in pure Streamlit
                st.markdown(f"""
                <div style="background:{bg_c}; border:1px solid {border_c}; border-radius:12px; padding:15px; position:relative; min-height:110px; font-family:'Space Grotesk', sans-serif; transition: all 0.3s ease;">
                    <div style="position:absolute; top:12px; right:12px; width:10px; height:10px; border-radius:50%; background:{dot_color}; box-shadow: 0 0 10px {dot_color}50;"></div>
                    <div style="color:#86A789; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:1px;">{name}</div>
                    <div style="color:#F5F5F5; font-size:1.8rem; font-weight:800; line-height:1.2; margin-top:5px;">{score:.0f}</div>
                    <div style="color:{dot_color}; font-size:0.75rem; font-weight:600; text-transform:uppercase;">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Hidden/Integrated select button
                if st.button(f"S_{name}", key=f"sel_{name}", use_container_width=True, help=f"Select {name}"):
                    st.session_state.selected_field = name
                    st.rerun()

    st.markdown("""
<div style="margin-top:20px; display:flex; gap:15px; font-size:0.7rem; color:#86A789; font-family:'Space Grotesk', sans-serif; text-transform:uppercase; font-weight:700;">
<span style="display:flex; align-items:center; gap:6px;"><div style="width:8px; height:8px; border-radius:50%; background:#4ADE80;"></div> Good</span>
<span style="display:flex; align-items:center; gap:6px;"><div style="width:8px; height:8px; border-radius:50%; background:#F59E0B;"></div> Watch</span>
<span style="display:flex; align-items:center; gap:6px;"><div style="width:8px; height:8px; border-radius:50%; background:#EF4444;"></div> Alert</span>
</div>
    """, unsafe_allow_html=True)

# --- RIGHT SIDE: DETAILS PANEL ---
with col_right:
    sel_name = st.session_state.selected_field
    sel_sector = sectors.get(sel_name, {})
    sel_score = sel_sector.get('ndvi', 0.6) * 100
    real_ndvi = sel_sector.get('ndvi', 0.6)
    
    # Get dynamic node data if available
    matched_node = next((n for n in nodes.values() if sel_name[:2] in n.get('location', '')), list(nodes.values())[0] if nodes else {})
    soil_m = matched_node.get('soil_wetness', matched_node.get('soil_moist', 38.0))
    last_seen = matched_node.get('last_seen', 'Real-time')
    
    stages = dl.get_rice_life_cycle()
    crop_stage = stages.get('stage', 'Tillering')
    
    is_good = sel_score >= 70
    is_crit = sel_score < 45
    c_txt = "#4ADE80" if is_good else "#F59E0B" if not is_crit else "#EF4444"
    bg_tag = "#fef3c7" if not is_crit and not is_good else "#dcfce7" if is_good else "#fee2e2"
    txt_tag = "#92400e" if not is_crit and not is_good else "#166534" if is_good else "#991b1b"
    
    concern = field_intel.get('disease_risk', {}).get('threat', 'Unknown risk')
    if is_good: tag_str = "Healthy — routine care" if not is_hi else "स्वस्थ — कोई कार्रवाई आवश्यक नहीं"
    elif is_crit: tag_str = f"Critical — act on {concern}" if not is_hi else f"गंभीर — {concern} पर काम करें"
    else: tag_str = f"Watch — {concern}" if not is_hi else f"निगरानी — {concern}"
    
    field_acts = [a for a in field_intel.get('actions', []) if a.get('field', sel_name) == sel_name]
    if not field_acts:
        field_acts = [
            {"text": "Check nitrogen levels", "desc": "NDVI trend suggests possible N deficiency in next 5 days", "icon": "🧪"},
            {"text": f"Scout for {concern}", "desc": "Local intelligence model highlights elevated risk factors for this sector.", "icon": "🔍"}
        ]
        if not is_good:
            field_acts.insert(0, {"text": "Increase irrigation by 15%", "desc": "Soil moisture below optimal range for tillering stage", "icon": "💧"})
            
    t_ndvi_lbl = "वनस्पति सूचकांक" if is_hi else "NDVI index"
    t_soil_lbl = "मिट्टी की नमी" if is_hi else "Soil moisture"
    t_stage_lbl = "फसल अवस्था" if is_hi else "Crop stage"
    t_rec_lbl = "अनुशंसित क्रियाएं" if is_hi else "RECOMMENDED ACTIONS"
    
    act_html = ""
    for act in field_acts[:2]:
        act_text = act.get('hi', act['text']) if is_hi else act['text']
        act_desc = act.get('desc_hi', act.get('desc', '')) if is_hi else act.get('desc', '')
        icon = act.get('icon', '📌')
        act_html += f"""
<div style="background:#262626; border-radius:12px; padding:20px; display:flex; align-items:center; gap:20px; margin-bottom:15px; border:1px solid #333;">
<div style="background:#F5F5F5; width:45px; height:45px; border-radius:12px; display:flex; justify-content:center; align-items:center; font-size:1.4rem;">{icon}</div>
<div>
<div style="color:#F5F5F5; font-size:1.1rem; font-weight:600; font-family:'Space Grotesk', sans-serif;">{act_text}</div>
<div style="color:#A3A3A3; font-size:0.9rem; line-height:1.4; font-family:'Space Grotesk', sans-serif;">{act_desc}</div>
</div>
</div>
        """

    right_ui = f"""
<div style="background:#1C1C1A; border-radius:20px; padding:30px; height:100%; border-left:1px solid #333; margin-left: -5px;">
<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:30px;">
<div>
<div style="font-size:2.2rem; color:#F5F5F5; font-weight:600; font-family:'Space Grotesk', sans-serif; line-height:1.2;">{sel_name}</div>
<div style="background:{bg_tag}; color:{txt_tag}; padding:6px 14px; border-radius:24px; font-size:0.85rem; font-weight:600; display:inline-block; margin-top:10px; font-family:'Space Grotesk', sans-serif;">
{tag_str}
</div>
</div>
<div style="text-align:right;">
<div style="color:{c_txt}; font-size:4rem; font-weight:800; line-height:0.9; font-family:'Space Grotesk', sans-serif;">{sel_score:.0f}</div>
<div style="color:#A3A3A3; font-size:0.85rem; margin-top:5px; font-family:'Space Grotesk', sans-serif;">{'स्वास्थ्य स्कोर' if is_hi else 'Health score'}</div>
<div style="color:{text_g}; font-size:0.65rem; margin-top:10px; opacity:0.8;">Last Seen: {last_seen}</div>
</div>
</div>
<div style="display:flex; gap:15px; margin-bottom:40px;">
<div style="flex:1; background:#2A2A28; border-radius:12px; padding:15px; border:1px solid #333;">
<div style="color:#A3A3A3; font-size:0.8rem; margin-bottom:8px; font-family:'Space Grotesk', sans-serif;">{t_ndvi_lbl}</div>
<div style="color:#F5F5F5; font-size:1.4rem; font-weight:600; font-family:'Space Grotesk', sans-serif;">{real_ndvi:.2f}</div>
</div>
<div style="flex:1; background:#2A2A28; border-radius:12px; padding:15px; border:1px solid #333;">
<div style="color:#A3A3A3; font-size:0.8rem; margin-bottom:8px; font-family:'Space Grotesk', sans-serif;">{t_soil_lbl}</div>
<div style="color:#F5F5F5; font-size:1.4rem; font-weight:600; font-family:'Space Grotesk', sans-serif;">{soil_m:.0f}%</div>
</div>
<div style="flex:1; background:#2A2A28; border-radius:12px; padding:15px; border:1px solid #333;">
<div style="color:#A3A3A3; font-size:0.8rem; margin-bottom:8px; font-family:'Space Grotesk', sans-serif;">{t_stage_lbl}</div>
<div style="color:#F5F5F5; font-size:1.2rem; font-weight:600; font-family:'Space Grotesk', sans-serif;">{crop_stage}</div>
</div>
</div>
<div style="color:#A3A3A3; font-size:0.8rem; font-weight:600; letter-spacing:1px; margin-bottom:15px; font-family:'Space Grotesk', sans-serif;">{t_rec_lbl}</div>
{act_html}
</div>
    """
    
    st.markdown(right_ui, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    btn1, btn2 = st.columns(2)
    with btn1:
        st.button("Get action plan ↗" if not is_hi else "कार्य योजना प्राप्त करें ↗", use_container_width=True, type="secondary")
    with btn2:
        if st.button("View trend ↗" if not is_hi else "प्रवृत्ति देखें ↗", use_container_width=True, type="secondary"):
             st.switch_page("pages/9_📈_Performance_Trends.py")
