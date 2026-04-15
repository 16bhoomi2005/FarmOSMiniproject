import streamlit as st
import sys, os
from datetime import datetime, date
from dotenv import load_dotenv, set_key

# Path alignment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

# 1. Page Config & Localization
lang = setup_page(
    title=dl.translate("settings", st.session_state.get('lang')),
    subtitle="Configure your farm, language, and alerts",
    icon="⚙️"
)
dl.get_field_sidebar()
is_hi = (lang == 'hi')

# 2. Session State Initialization
if 'settings_tab' not in st.session_state:
    st.session_state.settings_tab = "Farm Profile"
if 'farmer_name' not in st.session_state:
    st.session_state.farmer_name = "Rajesh Kumar"
if 'farm_loc' not in st.session_state:
    st.session_state.farm_loc = "Bhandara, Maharashtra"
if 'total_area' not in st.session_state:
    st.session_state.total_area = 12.0
if 'area_unit' not in st.session_state:
    st.session_state.area_unit = "Acres"
if 'weight_unit' not in st.session_state:
    st.session_state.weight_unit = "Tons"
if 'sowing_date' not in st.session_state:
    st.session_state.sowing_date = date(2024, 7, 15)

# Load env variables for credentials
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# --- CSS: Midnight Eco Control Panel ---
st.markdown(f"""
<style>
    .stApp {{ background-color: #050A06 !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    
    /* Navigation Sidebar Style */
    .nav-btn {{
        background: transparent;
        border: none;
        color: #86A789;
        padding: 12px 20px;
        width: 100%;
        text-align: left;
        border-radius: 8px;
        margin-bottom: 5px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .nav-btn:hover {{ background: rgba(134, 167, 137, 0.1); color: #F5F5F5; }}
    .nav-btn-active {{ background: rgba(74, 222, 128, 0.1) !important; color: #4ADE80 !important; font-weight: 700; border-left: 3px solid #4ADE80; }}
    
    /* Settings Card */
    .settings-card {{
        background: rgba(13, 26, 18, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }}
    .section-header {{
        color: #4ADE80;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 10px;
        position: relative;
        padding-bottom: 12px;
    }}
    
    .section-header::after {{
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, 
            rgba(76, 175, 130, 0) 0%, 
            rgba(76, 175, 130, 0.8) 25%, 
            rgba(232, 160, 32, 0.9) 50%, 
            rgba(76, 175, 130, 0.8) 75%, 
            rgba(76, 175, 130, 0) 100%
        );
        background-size: 200% 100%;
        animation: glow-line-move 2.5s ease-in-out infinite alternate;
        box-shadow: 0 0 10px rgba(76, 175, 130, 0.4);
    }}

    @keyframes glow-line-move {{
        0% {{ background-position: 0% 0; filter: hue-rotate(0deg) brightness(1); }}
        100% {{ background-position: 100% 0; filter: hue-rotate(15deg) brightness(1.2); }}
    }}
    
    /* Inputs Styling Override */
    div[data-baseweb="input"] {{ background-color: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }}
    div[data-baseweb="select"] > div {{ background-color: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; }}
    
    /* Status Dots */
    .status-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }}
</style>
""", unsafe_allow_html=True)

# 3. Main Layout: Navigation + Content
nav_col, content_col = st.columns([1, 3.5])

# --- NAVIGATION PANEL ---
with nav_col:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:rgba(255,255,255,0.4); font-size:0.6rem; font-weight:800; text-transform:uppercase; margin-bottom:15px; padding-left:20px;'>{dl.translate('today_brief', lang)}</div>", unsafe_allow_html=True)
    
    tabs = [
        ("👤 Farm Profile", "Farm Profile"),
        ("🌾 Crop & Season", "Crop & Season"),
        ("🔔 Alerts & Preferences", "Alerts"),
        ("📡 IoT Sensors", "Connectivity"),
        ("🌍 Language", "Personalization"),
        ("🔗 Integrations", "Integrations"),
        ("⚠️ Danger Zone", "Danger")
    ]
    
    for label, tab_id in tabs:
        is_active = st.session_state.settings_tab == tab_id
        if st.button(label, key=f"nav_{tab_id}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.settings_tab = tab_id
            st.rerun()
    
    st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)
    if st.button("SAVE ALL CHANGES", use_container_width=True, type="primary"):
        st.toast("Settings Saved Hub-wide")

# --- CONTENT PANEL ---
with content_col:
    # --- HEADER ---
    st.markdown(f"""
    <div style="margin-bottom:30px;">
        <h1 style="color:#F5F5F5; font-size:2.2rem; margin-bottom:5px;">⚙️ {dl.translate('settings', lang)}</h1>
        <p style="color:#86A789; font-size:0.9rem;">Configure your farm, language, and alerts</p>
    </div>
    """, unsafe_allow_html=True)

    tab = st.session_state.settings_tab

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION: FARM PROFILE
    # ──────────────────────────────────────────────────────────────────────────
    if tab == "Farm Profile":
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">👤 {dl.translate("farm_details", lang)}</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.text_input(dl.translate("farm_name", lang), value=st.session_state.get('farm_name', "Rajesh Kumar's Farm"), key='farm_name')
            st.text_input(dl.translate("location_village", lang), value=st.session_state.farm_loc, key='farm_loc')
            st.selectbox(dl.translate("num_sub_plots", lang), options=[1, 3, 5, 9, 12], index=3, key='sub_plots')
        with c2:
            st.text_input(dl.translate("owner_name", lang), value=st.session_state.farmer_name, key='farmer_name')
            st.number_input(dl.translate("total_area", lang), value=st.session_state.total_area, key='total_area')
            st.selectbox(dl.translate("primary_crop_label", lang), options=["Paddy (Rice)", "Wheat", "Sugarcane", "Cotton"], key='primary_crop')
            
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION: CROP & SEASON
    # ──────────────────────────────────────────────────────────────────────────
    elif tab == "Crop & Season":
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">🌾 {dl.translate("field_status", lang)} & {dl.translate("yield_projection", lang)}</div>', unsafe_allow_html=True)
        
        st.info("💡 " + dl.translate("guidance_1", lang))
        
        c1, c2 = st.columns(2)
        with c1:
            stages = ["Auto", "Seedling", "Tillering", "Flowering", "Grain Filling", "Pre-Harvest"]
            current_stage_idx = stages.index(st.session_state.manual_growth_stage) if st.session_state.manual_growth_stage in stages else 0
            st.selectbox(dl.translate("field_status", lang), options=stages, index=current_stage_idx, key='manual_growth_stage')
            st.date_input(dl.translate("sowing_date_label", lang), value=st.session_state.sowing_date, key='sowing_date')
        with c2:
            st.selectbox(dl.translate("season_label", lang), options=["Kharif 2024", "Rabi 2024", "Zaid 2025"], key='season_name')
            st.slider(dl.translate("yield_projection", lang), min_value=1.0, max_value=15.0, value=float(st.session_state.target_yield), step=0.5, key='target_yield')
            
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION: ALERTS & PREFERENCES
    # ──────────────────────────────────────────────────────────────────────────
    elif tab == "Alerts":
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">🔔 {dl.translate("alert_prefs", lang)}</div>', unsafe_allow_html=True)
        
        st.toggle(dl.translate("critical_alerts_label", lang), value=True)
        st.toggle(dl.translate("whatsapp_updates_label", lang), value=True)
        st.toggle(dl.translate("vitals_alerts", lang), value=True, key='sms_toggle')
        st.toggle("Email weekly reports" if not is_hi else "ईमेल साप्ताहिक रिपोर्ट", value=True)
        st.toggle("AI advisor suggestions" if not is_hi else "एआई सलाहकार सुझाव", value=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.75rem; color:#86A789; margin-bottom:10px;'>{dl.translate('problem_area', lang)}:</div>", unsafe_allow_html=True)
        
        t_phone = st.text_input("Phone Number" if not is_hi else "फ़ोन नंबर", value=os.environ.get("FARMER_PHONE", ""), key='farmer_phone_input_ui')
        
        st.markdown("<br>", unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("🚀 " + (dl.translate("listen_advice", lang).replace(" सलाह सुनें", " टेस्ट एसएमएस") if is_hi else "Send test SMS alert")):
                st.toast("SMS Pipeline Tested")
        with bc2:
            st.button("💬 " + ("व्हाट्सएप कनेक्शन का परीक्षण करें" if is_hi else "Test WhatsApp Connection"))
            
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION: CONNECTIVITY (Hardware & Cloud)
    # ──────────────────────────────────────────────────────────────────────────
    elif tab == "Connectivity":
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">📡 {dl.translate("system_conn", lang)}</div>', unsafe_allow_html=True)
        
        health = dl.get_system_health()
        
        def status_row(label, status_text, is_ok):
            col = "#4ADE80" if is_ok else "#EF4444"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.03);">
                <div style="color:#F5F5F5; font-size:0.85rem; display:flex; align-items:center; gap:10px;">
                    <span style="background:{col}; width:6px; height:6px; border-radius:50%;"></span> {label}
                </div>
                <div style="color:{col}; font-size:0.75rem; font-weight:700;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)

        status_row(dl.translate("sensor_nodes", lang), health['mongodb'], "Live" in health['mongodb'])
        status_row("Satellite service (Sentinel-2)" if not is_hi else "सैटेलाइट सेवा (Sentinel-2)", health['satellite'], "Sentinel" in health['satellite'])
        status_row("Cloud data stream" if not is_hi else "क्लाउड डेटा स्ट्रीम", "Connected - 99.2% uptime", True)
        status_row(dl.translate("market_intel", lang), "Synced - 42 min ago", True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox(dl.translate("sync_interval_label", lang), options=["Every 30 minutes", "Every 60 minutes", "On Change"])
        with c2:
            st.selectbox("Satellite sync frequency" if not is_hi else "सैटेलाइट सिंक आवृत्ति", options=["Every 6 hours", "Daily", "Weekly"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("🔄 " + ("कनेक्शन का परीक्षण करें और रीफ्रेश करें" if is_hi else "Test & Refresh Connections"), use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION: PERSONALIZATION
    # ──────────────────────────────────────────────────────────────────────────
    elif tab == "Personalization":
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">🌍 {dl.translate("extra_analysis", lang)}</div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            opt = ["English", "हिंदी"]
            new_lang = st.selectbox("App language" if not is_hi else "ऐप की भाषा", options=opt, index=0 if lang == 'en' else 1)
            if (new_lang == "English" and lang != 'en') or (new_lang == "हिंदी" and lang != 'hi'):
                st.session_state.lang = 'en' if new_lang == "English" else 'hi'
                st.rerun()
        with c2:
            st.selectbox(dl.translate("area_units", lang), options=["Acres", "Hectares", "Bigha"], index=0)
        with c3:
            st.selectbox("Weight units" if not is_hi else "वजन की इकाइयाँ", options=["Tons", "Quintals", "kg"], index=0)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.toggle(dl.translate("listen_advice", lang), value=st.session_state.get('voice_enabled', False), key='voice_enabled')
        st.toggle(dl.translate("expert_mode", lang), value=st.session_state.expert_mode, key='expert_mode')
        st.toggle("AI personalized recommendations" if not is_hi else "एआई व्यक्तिगत सिफारिशें", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION: INTEGRATIONS
    # ──────────────────────────────────────────────────────────────────────────
    elif tab == "Integrations":
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">🔗 {"Third-party integrations" if not is_hi else "तृतीय-पक्ष एकीकरण"}</div>', unsafe_allow_html=True)
        
        integrations = [
            ("Sentinel-2 (ESA)", "Active", "Manage"),
            ("AgroConnect (Local prices)", "Connected", "Manage"),
            ("OpenWeather API", "Connected", "Manage"),
            ("WhatsApp Business", "Connected", "Manage"),
            ("RM-45 Data Portal", "Not connected", "Connect")
        ]
        
        for name, status, action in integrations:
            col = "#4ADE80" if "Connected" in status or "Active" in status else "#A3A3A3"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; padding:15px; background:rgba(255,255,255,0.02); border-radius:10px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="background:{col}20; width:32px; height:32px; border-radius:6px; display:flex; align-items:center; justify-content:center; color:{col}; font-size:0.8rem;">📦</div>
                    <div>
                        <div style="color:#F5F5F5; font-size:0.85rem; font-weight:700;">{name}</div>
                        <div style="color:#86A789; font-size:0.6rem;">{status}</div>
                    </div>
                </div>
                <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#F5F5F5; font-size:0.7rem; padding:4px 12px; border-radius:6px; cursor:pointer;">{action}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.button("+ Add integration" if not is_hi else "+ एकीकरण जोड़ें", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION: DANGER ZONE
    # ──────────────────────────────────────────────────────────────────────────
    elif tab == "Danger":
        st.markdown('<div class="settings-card" style="border-color:rgba(239, 68, 68, 0.2); background:rgba(239, 68, 68, 0.05);">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header" style="color:#EF4444;">⚠️ {dl.translate("danger_zone_lbl", lang)}</div>', unsafe_allow_html=True)
        
        st.warning("These actions are permanent. Use with caution." if not is_hi else "ये क्रियाएं स्थायी हैं। सावधानी से उपयोग करें।")
        
        if st.button("Reset all farm data" if not is_hi else "सभी फार्म डेटा रीसेट करें", use_container_width=True):
            st.toast("Data Reset (Simulated)")
        st.button("Delete account" if not is_hi else "खाता हटाएं", use_container_width=True, type="secondary")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- SAVE BAR ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center; color:#86A789; font-size:0.65rem; border-top:1px solid rgba(255,255,255,0.05); padding-top:20px;">
        FarmOS v2.0 • Data retention: 365 days • <span style="color:#4ADE80;">Privacy Policy</span>
    </div>
    """, unsafe_allow_html=True)
