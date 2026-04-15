import streamlit as st
import sys, os, textwrap
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

lang = st.session_state.get('lang', 'en')
is_hi = (lang == 'hi')

# Mapping for Icons based on alert type
TYPE_ICONS = {
    "Irrigation": "💧",
    "Critical Water Stress": "💧",
    "Disease": "🦠",
    "Rice Blast": "🦠",
    "Nitrogen": "🍂",
    "Soil": "🌱",
    "Weather": "🌦️",
    "System": "⚙️",
    "Default": "📢"
}

# --- REAL-TIME LIVE SENSING ENGINE ---
# This generates alerts instantly from incoming IoT/Sat telemetry
field_intel = dl.get_field_intelligence(lang=lang)

# 🚀 SYSTEM GENERATION: Sense conditions and Push to MongoDB FIRST
# (Deduplication inside ensures we only record fresh discoveries)
dl.generate_and_sync_system_alerts(field_intel)

# Fetch live data (including newly synced system alerts)
alerts = dl.load_active_alerts()

# Live Source Verification
is_live = len(alerts) > 0
iot_source = "Verified IoT (MongoDB)" if is_live else "Simulation Engine"
iot_color = "#34d399" if is_live else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

setup_page(
    title="Alerts & Actions" if not is_hi else "अलर्ट और क्रियाएं",
    subtitle="Things that need your attention today — sorted by urgency" if not is_hi else "चीजें जिन पर आज आपके ध्यान की आवश्यकता है — तात्कालिकता के अनुसार क्रमबद्ध",
    icon="🚨"
)
dl.get_field_sidebar()

# --- HEADER strip ---
st.markdown(textwrap.dedent(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px;">
    <div>
        <div style="color:#86A789; font-size:0.75rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;">{dl.translate("alert_terminal", lang)}</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{iot_color}15; border:1px solid {iot_color}40; color:{iot_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
            { ("साझा सूत्र: IoT NoDes" if is_hi else "Source: Verified IoT NoDes") if is_live else dl.translate("simulation_mode", lang) }
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#F5F5F5; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            { ("अद्यतित " if is_hi else "Updated ") + last_updated }
        </div>
    </div>
</div>
""").strip(), unsafe_allow_html=True)

# --- Metrics Calculation ---
# Prioritize LIVE alerts for metrics
critical_count = sum(1 for a in alerts if a.get('severity') == "Critical" and not a.get("read", False))
warning_count = sum(1 for a in alerts if a.get('severity') == "Warning" and not a.get("read", False))
resolved_count = sum(1 for a in alerts if a.get("read", False))
total_week = len(alerts)

# --- Filter Logic ---
if "alert_filter" not in st.session_state:
    st.session_state.alert_filter = "All"

filter_options = ["All", "Critical", "Warning", "Resolved", "Disease", "Irrigation", "Soil", "Weather"]
if is_hi:
    filter_labels = ["सभी", "गंभीर", "चेतावनी", "सुलझा हुआ", "बीमारी", "सिंचाई", "मिट्टी", "मौसम"]
else:
    filter_labels = filter_options

# Header and Metric Strip
st.markdown(f"""
<style>
    .stApp {{ background-color: #09120B; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    
    /* Sleek Night-Eco Alert Buttons */
    .stButton > button[key^="act_"] {{
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #F5F5F5 !important;
        border-radius: 8px !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        padding: 4px 12px !important;
        transition: all 0.2s ease !important;
        margin-top: 5px !important;
    }}
    .stButton > button[key^="act_"]:hover {{
        background: rgba(255,255,255,0.15) !important;
        border-color: rgba(255,255,255,0.25) !important;
        transform: translateY(-1px) !important;
    }}
    
/* Mobile Overrides for Alerts */
@media (max-width: 768px) {{
    .metric-strip {{
        flex-direction: column !important;
        gap: 10px !important;
    }}
    .metric-card {{
        width: 100% !important;
    }}
    .alert-card-header {{
        flex-direction: column !important;
        align-items: flex-start !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

# Metric Strip Layout
st.markdown(textwrap.dedent(f"""
<div class="metric-strip" style="display:flex; gap:15px; margin-bottom:25px; margin-top:20px;">
    <div class="metric-card" style="flex:1; background:#0F1A12; border:1px solid #1C3D28; border-top:2px solid #EF4444; border-radius:12px; padding:15px;">
        <div style="color:#86A789; font-size:0.7rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{dl.translate("critical_act_now", lang)}</div>
        <div style="color:#EF4444; font-size:2rem; font-weight:700; line-height:1;">{critical_count}</div>
        <div style="color:#EF4444; font-size:0.7rem; margin-top:8px;">{ ("अनदेखा करने पर उपज को खतरा" if is_hi else "Risk to yield if ignored") }</div>
    </div>
    <div class="metric-card" style="flex:1; background:#0F1A12; border:1px solid #1C3D28; border-top:2px solid #F59E0B; border-radius:12px; padding:15px;">
        <div style="color:#86A789; font-size:0.7rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{dl.translate("warnings_monitor", lang)}</div>
        <div style="color:#F5F5F5; font-size:2rem; font-weight:700; line-height:1;">{warning_count}</div>
        <div style="color:#F59E0B; font-size:0.7rem; margin-top:8px;">{ ("24 घंटे के भीतर जांच करें" if is_hi else "Check within 24 hrs") }</div>
    </div>
    <div class="metric-card" style="flex:1; background:#0F1A12; border:1px solid #1C3D28; border-top:2px solid #4ADE80; border-radius:12px; padding:15px;">
        <div style="color:#86A789; font-size:0.7rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{dl.translate("resolved_today", lang)}</div>
        <div style="color:#4ADE80; font-size:2rem; font-weight:700; line-height:1;">{resolved_count}</div>
        <div style="color:#4ADE80; font-size:0.7rem; margin-top:8px;">{ ("आपके द्वारा पूर्ण मार्क किया गया" if is_hi else "Marked done by you") }</div>
    </div>
    <div class="metric-card" style="flex:1; background:#0F1A12; border:1px solid #1C3D28; border-top:2px solid #A3A3A3; border-radius:12px; padding:15px;">
        <div style="color:#86A789; font-size:0.7rem; font-weight:700; letter-spacing:1px; margin-bottom:10px;">{dl.translate("total_this_week", lang)}</div>
        <div style="color:#F5F5F5; font-size:2rem; font-weight:700; line-height:1;">{total_week}</div>
        <div style="color:#A3A3A3; font-size:0.7rem; margin-top:8px;">↓ 3 {dl.translate("vs last week", lang)}</div>
    </div>
</div>
""").strip(), unsafe_allow_html=True)

# Filter Pills
cols = st.columns(len(filter_options))
for i, (opt, lbl) in enumerate(zip(filter_options, filter_labels)):
    is_active = st.session_state.alert_filter == opt
    if cols[i].button(lbl, key=f"filter_{opt}", type="primary" if is_active else "secondary", use_container_width=True):
        st.session_state.alert_filter = opt
        st.rerun()

# SMS Toggle
t_sms_lbl = ("SMS अलर्ट सक्रिय" if is_hi else "SMS ALERTS ACTIVE")
st.markdown(f"""
<div style="display:flex; justify-content:flex-end; margin: 15px 0;">
    <div style="background:#132A1B; border:1px solid #1C3D28; color:#4ADE80; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:600; display:flex; align-items:center; gap:8px;">
        <div style="width:6px; height:6px; border-radius:50%; background:#4ADE80;"></div>
        {t_sms_lbl}
    </div>
</div>
""", unsafe_allow_html=True)

# --- Alert Rendering Function ---
def get_time_ago(ts):
    """Converts timestamp to human readable format."""
    try:
        if not ts or ts == "Just now": return "Just now"
        # Handle ISO format
        if 'T' in ts:
            past = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            now = datetime.now(past.tzinfo)
            diff = now - past
            if diff.days > 0: return f"{diff.days}d ago"
            hours = diff.seconds // 3600
            if hours > 0: return f"{hours}h ago"
            mins = (diff.seconds % 3600) // 60
            return f"{mins}m ago"
        return ts
    except:
        return ts

def render_alert_card(alert):
    a_id = alert.get('id', 'temp_id')
    severity = alert.get('severity', 'Warning')
    is_resolved = alert.get('read', False)
    is_live = alert.get('is_live_sensed', False)
    a_type = alert.get('type', 'Alert')
    message = alert.get('message', '')
    
    # Smart Title Derivation
    title = alert.get('title')
    if not title or title == "Field Update":
        if "Nitrogen" in message or "NPK" in message: title = "Nutrient Optimization"
        elif "Water" in message or "Moisture" in message: title = "Hydration Intelligence"
        elif "Blast" in message or "Spot" in message or "Pest" in message: title = "Pathogen Alert"
        elif "Weather" in message or "Rain" in message: title = "Atmospheric Risk"
        else: title = f"{a_type} Event"

    # Determine color scheme
    if is_resolved:
        border_c, accents_c, bg_c = "#333", "#A3A3A3", "#0F1A12"
        tag_bg, tag_txt = "#262626", "#A3A3A3"
    elif severity == "Critical":
        border_c, accents_c, bg_c = "#EF4444", "#EF4444", "#150909"
        tag_bg, tag_txt = "#451a1a", "#EF4444"
    else: # Warning
        border_c, accents_c, bg_c = "#F59E0B", "#F59E0B", "#16130B"
        tag_bg, tag_txt = "#3d2a08", "#F59E0B"

    # Action buttons mapping
    actions = []
    if any(k in a_type or k in message for k in ["Water", "Irr", "Soil", "Moisture"]):
        actions = [("Schedule irrigation", "pages/2_💧_Ground_Condition.py"), ("Live sensors", "pages/2_💧_Ground_Condition.py")]
    elif any(k in a_type or k in message for k in ["Disease", "Blast", "Pest", "Spot"]):
        actions = [("Log treatment", "pages/8_🧠_AI_Agronomist.py"), ("AI Diagnosis", "pages/13_📷_CNN_Pest_Classifier.py")]
    elif any(k in a_type or k in message for k in ["Nitrogen", "NPK", "Nutrient"]):
        actions = [("Apply Fertilizer", "pages/15_🧪_NPK_Nutrients.py"), ("NDRE Trends", "pages/10_🗺️_Spectral_Maps.py")]
    else:
        actions = [("Alert Details", "pages/4_📚_Help.py"), ("Full Forecast", "pages/5_🌦️_Weather_Risk.py")]

    time_display = get_time_ago(alert.get('timestamp'))

    # Render Card Top
    st.markdown(f"""<div style="background:{bg_c}; border-left:4px solid {border_c}; border-right:1px solid rgba(255,255,255,0.05); border-top:1px solid rgba(255,255,255,0.05); border-bottom:1px solid rgba(255,255,255,0.05); border-top-left-radius:12px; border-top-right-radius:12px; padding:20px 20px 5px 20px; position:relative;">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<div style="width: 100%;">
<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
<span style="background:{tag_bg}; color:{tag_txt}; font-size:0.65rem; font-weight:800; padding:2px 8px; border-radius:4px; text-transform:uppercase;">{severity}</span>
{f'<span style="background:#34d399; color:#064e3b; font-size:0.65rem; font-weight:800; padding:2px 8px; border-radius:4px; text-transform:uppercase;">LIVE SENSE</span>' if is_live else ''}
<span style="color:rgba(255,255,255,0.4); font-size:0.75rem;">{time_display}</span>
</div>
<div style="color:#F5F5F5; font-size:1.15rem; font-weight:700; margin-bottom:8px;">{TYPE_ICONS.get(alert.get('type','Default'), '📢')} {title}</div>
<div style="color:rgba(245,240,232,0.7); font-size:0.9rem; line-height:1.5; margin-bottom:10px; max-width:90%;">{message}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    # Real Interactive Buttons
    cols = st.columns([1,1,3])
    for i, (lbl, target) in enumerate(actions):
        if i < 2:
            if cols[i].button(lbl, key=f"act_{a_id}_{i}", use_container_width=True):
                st.switch_page(target)
    
    # Render Card Bottom
    st.markdown(f"""<div style="background:{bg_c}; border-left:4px solid {border_c}; border-right:1px solid rgba(255,255,255,0.05); border-bottom:1px solid rgba(255,255,255,0.05); border-bottom-left-radius:12px; border-bottom-right-radius:12px; padding:5px 20px 20px 20px; position:relative; margin-bottom:15px;">
<div style="color:rgba(255,255,255,0.3); font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; display:flex; justify-content:space-between; align-items:center;">
<span>Source: {alert.get('source', 'System')} • Cat: {alert.get('type', 'General')}</span>
<div style="display:flex; gap:10px;">
{"<span style='background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#4ADE80; padding:4px 10px; border-radius:6px;'>RESOLVED</span>" if is_resolved else ""}
</div>
</div>
</div>""", unsafe_allow_html=True)

    # Resolve Logic (Side by side for compact feel)
    if not is_resolved:
        c1, c2 = st.columns([5, 1])
        with c2:
            if st.button("✓ Done", key=f"done_{a_id}", use_container_width=True, help="Mark this alert as resolved"):
                dl.mark_alert_read(a_id)
                st.rerun()

# --- Alerts Feed Rendering ---
f_val = st.session_state.alert_filter

# Filter criteria
display_alerts = alerts
if f_val == "Critical":
    display_alerts = [a for a in alerts if a['severity'] == "Critical" and not a.get('read')]
elif f_val == "Warning":
    display_alerts = [a for a in alerts if a['severity'] == "Warning" and not a.get('read')]
elif f_val == "Resolved":
    display_alerts = [a for a in alerts if a.get('read')]
elif f_val != "All":
    # Filter by type/category matching
    display_alerts = [a for a in alerts if f_val in a.get('type', '') or f_val in a.get('message', '')]

# Rendering Sections
criticals = [a for a in display_alerts if a['severity'] == "Critical" and not a.get('read')]
warnings = [a for a in display_alerts if a['severity'] == "Warning" and not a.get('read')]
resolved = [a for a in display_alerts if a.get('read')]

if f_val in ["All", "Critical"] and criticals:
    st.markdown(f"<div style='color:#EF4444; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin:20px 0 15px;'>{ ("गंभीर — तत्काल कार्रवाई आवश्यक" if is_hi else "CRITICAL — IMMEDIATE ACTION REQUIRED") }</div>", unsafe_allow_html=True)
    for a in criticals:
        render_alert_card(a)

if f_val in ["All", "Warning"] and warnings:
    st.markdown(f"<div style='color:#F59E0B; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin:20px 0 15px;'>{ ("चेतावनी — 24 घंटों के भीतर जांचें" if is_hi else "WARNINGS — CHECK WITHIN 24 HOURS") }</div>", unsafe_allow_html=True)
    for a in warnings:
        render_alert_card(a)

if f_val in ["All", "Resolved"] and resolved:
    st.markdown(f"<div style='color:#4ADE80; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin:20px 0 15px;'>{ ("आज सुलझाए गए" if is_hi else "RESOLVED TODAY") }</div>", unsafe_allow_html=True)
    for a in resolved:
        render_alert_card(a)

if not display_alerts:
    st.info("No alerts found for this filter.")

# SMS Notification Settings Card
f_phone = st.session_state.get("farmer_phone") or st.secrets.get("FARMER_PHONE", "+91 00000 00000")
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(textwrap.dedent(f"""
<div style="background:rgba(74,222,128,0.05); border:1px solid rgba(74,222,128,0.2); border-radius:12px; padding:30px; display:flex; gap:30px; align-items:center;">
    <div style="flex:1;">
        <div style="color:#4ADE80; font-weight:700; font-size:0.9rem; margin-bottom:10px;">SMS notifications active</div>
        <div style="color:#A3A3A3; font-size:0.8rem; line-height:1.5;">Critical alerts are sent to your mobile instantly. Warning alerts are batched at 7am daily.</div>
    </div>
    <div style="flex:2; display:flex; gap:10px; align-items:center;">
        <div style="flex:3; background:#262626; border:1px solid #333; border-radius:8px; padding:12px; color:#F5F5F5; font-size:1.1rem; font-family:monospace;">{f_phone}</div>
    </div>
</div>
""").strip(), unsafe_allow_html=True)

# Actual Streamlit input for SMS logic
with st.expander("Update SMS Contact & Test"):
    c1, c2 = st.columns([2, 1])
    with c1:
        new_phone = st.text_input("Mobile Number", value=f_phone)
    with c2:
        if st.button("Save Number", use_container_width=True):
            st.session_state.farmer_phone = new_phone
            st.success("Saved!")
    
    st.markdown("---")
    import notifier
    if st.button("🚀 Send Test SMS to registered phone", use_container_width=True):
        if f_phone and f_phone != "+91 00000 00000":
            test_alert = {
                "field": "Demo Plot",
                "severity": "Info",
                "type": "System Test",
                "message": "Connection verified. Your SmartFarm integration is active.",
                "value": "100",
                "unit": "%",
                "timestamp": datetime.now().strftime('%H:%M')
            }
            res = notifier.send_sms_alert(test_alert, f_phone)
            if res.get("success"):
                st.balloons()
                st.success(f"Test SMS sent! SID: {res.get('sid')}")
            else:
                st.error(f"Failed to send: {res.get('error')}")
        else:
            st.warning("Please save a valid phone number first.")
