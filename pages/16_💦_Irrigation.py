import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import pandas as pd
from datetime import datetime
import data_loader as dl
from mqtt_controller import publish_command, publish_bulk, get_subscribe_code
from sim_engine import SmartFarmSimEngine

lang = setup_page(
    title="Irrigation Control",
    subtitle="Turn water on/off for any field remotely",
    icon="💦",
    explanation_en="This page controls the water pumps and irrigation valves for all your fields remotely over the internet. Commands are sent to your physical hardware (ESP32/Arduino) instantly.",
    explanation_hi="यह पृष्ठ इंटरनेट के माध्यम से आपके सभी खेतों के पानी के पंप और सिंचाई वाल्व को दूर से नियंत्रित करता है। आदेश तुरंत आपके भौतिक हार्डवेयर (ESP32/Arduino) को भेजे जाते हैं।"
)
dl.get_field_sidebar()

from mqtt_controller import PAHO_AVAILABLE
if not PAHO_AVAILABLE:
    st.error("⚠️ " + ("MQTT कनेक्शन के लिए `paho-mqtt` लाइब्रेरी आवश्यक है। टर्मिनल में चलाएं: `pip install paho-mqtt`" if lang=="hi" else "**System Offline:** MQTT requires `paho-mqtt`. Please run `pip install paho-mqtt` in your terminal and restart the server."))

if "irrigation_log" not in st.session_state:
    st.session_state.irrigation_log = []

def log_command(field, command, duration, result):
    st.session_state.irrigation_log.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "field": field,
        "command": command,
        "duration_min": duration,
        "success": result.get("success", False),
        "message_id": result.get("message_id", "N/A")
    })

# Fetch Live Data
nodes = dl.get_sensor_nodes()
is_live = len(nodes) > 0
i_source = "Verified IoT (MongoDB)" if is_live else "Simulation Engine"
i_color = "#34d399" if is_live else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

from sim_engine import FIELD_NAMES
fields = FIELD_NAMES

# --- HEADER ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px;">
    <div>
        <div style="color:{dl.text_g if hasattr(dl, 'text_g') else '#86A789'}; font-size:0.75rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;">REMOTE CONTROL — SMART PUMP & VALVE CLUSTER</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{i_color}15; border:1px solid {i_color}40; color:{i_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
            Source: {i_source}
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#F5F5F5; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            Nodes: {len(nodes) if is_live else 0} active
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.subheader("🎛️ " + ("खेत नियंत्रण" if lang=="hi" else "Field Controls"))
for i in range(0, len(fields), 3):
    cols = st.columns(3)
    for j, field in enumerate(fields[i:i+3]):
        with cols[j]:
            # Get value from live nodes or fallback to sim
            f_node = nodes.get(field, {}) if is_live else {}
            moisture = f_node.get("moisture", 45.0) # Default if no node
            needs_water = moisture < 40
            
            f_lbl = "खेत का हिस्सा" if lang == "hi" else "Sub-Plot"
            st.markdown(f"**{field} {f_lbl}**")
            
            m_lbl = "मिट्टी की नमी" if lang == "hi" else "Soil Moisture"
            d_bad = "कम (पानी दें!)" if lang == "hi" else "Low (Irrigate!)"
            d_good = "सही है" if lang == "hi" else "Optimal"
            st.metric(m_lbl, f"{moisture:.1f}%", delta=d_bad if needs_water else d_good, delta_color="inverse")
            
            dur_lbl = "समय (मिनट)" if lang == "hi" else "Duration (minutes)"
            duration = st.slider(dur_lbl, 5, 60, 20, key=f"dur_{field}", label_visibility="collapsed")
            
            c1, c2 = st.columns(2)
            with c1:
                btn_irr = "💦 सिंचाई करें" if lang == "hi" else "💦 Irrigate"
                if st.button(btn_irr, key=f"on_{field}", type="primary" if needs_water else "secondary", use_container_width=True):
                    with st.spinner("सिग्नल भेज रहे हैं..." if lang=="hi" else "Publishing..."):
                        r = publish_command(field, "ON", duration)
                        if r["success"]:
                            st.success("पंप शुरू!" if lang=="hi" else "Sent")
                            log_command(field, "ON", duration, r)
                        else:
                            st.error(r.get("error", "Error"))
            with c2:
                btn_stop = "⏹️ बंद करें" if lang == "hi" else "⏹️ Stop"
                if st.button(btn_stop, key=f"off_{field}", use_container_width=True):
                    with st.spinner("सिग्नल भेज रहे हैं..." if lang=="hi" else "Publishing..."):
                        r = publish_command(field, "OFF")
                        if r["success"]:
                            st.info("पंप बंद" if lang=="hi" else "Stopped")
                            log_command(field, "OFF", 0, r)

st.divider()
st.subheader("⚡ " + ("एक साथ सभी खेत चलाएं (Bulk Automation)" if lang == "hi" else "Bulk Routing & Automation"))
bcol1, bcol2, bcol3 = st.columns(3)

with bcol1:
    btn_all_on = "🌊 सूखे खेतों में एक साथ पानी दें" if lang == "hi" else "🌊 Force Irrigate ALL Dry Sub-Plots"
    if st.button(btn_all_on, type="primary", use_container_width=True):
        dry_fields = []
        for f in fields:
            m = nodes.get(f, {}).get("moisture", 45) if is_live else 45
            if m < 40: dry_fields.append(f)
        if dry_fields:
            with st.spinner("सबको सिग्नल भेज रहे हैं..." if lang=="hi" else "Broadcasting to cluster..."):
                results = publish_bulk(dry_fields, "ON")
                success_count = sum(1 for r in results if r["success"])
                for f, r in zip(dry_fields, results):
                    log_command(f, "ON", 20, r)
                msg_dis = f"{success_count}/{len(dry_fields)} खेतों को आदेश भेजा गया।" if lang=="hi" else f"Dispatched {success_count}/{len(dry_fields)} commands."
                st.success(msg_dis)
        else:
            st.info("अभी कोई खेत सूखा नहीं है।" if lang=="hi" else "No sub-plots are currently dry.")

with bcol2:
    btn_all_off = "🛑 सभी पंप तुरंत बंद करें" if lang == "hi" else "🛑 Emergency Stop ALL Irrigation"
    if st.button(btn_all_off, use_container_width=True):
        with st.spinner("सबको बंद करने का आदेश..." if lang=="hi" else "Broadcasting ABORT..."):
            results = publish_bulk(fields, "OFF")
            success_count = sum(1 for r in results if r["success"])
            for f, r in zip(fields, results):
                log_command(f, "OFF", 0, r)
            msg_stop = f"सभी {success_count} खेतों में पानी रोक दिया गया।" if lang=="hi" else f"Stop signal sent to all {success_count} fields."
            st.info(msg_stop)

with bcol3:
    btn_auto = "🤖 AI ऑटो-मोड (अपने आप पानी दें)" if lang == "hi" else "🤖 AI Auto-Watering"
    if st.button(btn_auto, use_container_width=True):
        msg_spin = "AI सभी खेतों में नमी की जांच कर रहा है..." if lang == "hi" else "AI is checking moisture levels across all fields..."
        with st.spinner(msg_spin):
            auto_fields = []
            for f in fields:
                state = dl.get_field_intelligence(lang="en", sector_name=f)
                if state["irrigation_risk"]["needed"]:
                    auto_fields.append(f)
            
            if auto_fields:
                results = publish_bulk(auto_fields, "AUTO")
                for f, r in zip(auto_fields, results):
                    log_command(f, "AUTO", 30, r)
                msg_suc = f"AI ने {len(auto_fields)} सूखे खेतों के लिए पानी चालू कर दिया।" if lang == "hi" else f"AI started pumps for {len(auto_fields)} dry fields."
                st.success(msg_suc)
            else:
                msg_no = "सभी खेतों में पर्याप्त पानी है। अभी किसी पंप की जरूरत नहीं।" if lang == "hi" else "All fields have enough water right now. Pumps stay off."
                st.success(msg_no)

st.divider()
head_log = "📜 पंप चालू/बंद होने का रिकॉर्ड" if lang == "hi" else "📜 Pump Run History"
st.subheader(head_log)

if st.session_state.irrigation_log:
    df = pd.DataFrame(st.session_state.irrigation_log)
    df.rename(columns={
        "timestamp": "Time" if lang=="en" else "समय",
        "field": "Field" if lang=="en" else "खेत",
        "command": "Action" if lang=="en" else "आदेश",
        "duration_min": "Mins" if lang=="en" else "मिनट",
        "success": "Success" if lang=="en" else "सफल",
        "message_id": "ID" if lang=="en" else "आईडी"
    }, inplace=True)
    st.dataframe(df, use_container_width=True)
    
    btn_dl = "📩 रिकॉर्ड डाउनलोड करें" if lang == "hi" else "📩 Download Pump History CSV"
    st.download_button(btn_dl, df.to_csv(index=False).encode('utf-8'), "pump_history.csv", "text/csv")
else:
    msg_empty = "अभी तक इस बार कोई पंप नहीं चलाया गया।" if lang == "hi" else "No pumps have been turned on/off yet."
    st.caption(msg_empty)

st.divider()
with st.expander("🛠️ Hardware Integration Guide (ESP32/Arduino)"):
    st.markdown("""
    **To physically control valves using a micro-controller:**
    1. Install `PubSubClient` and `WiFi` library in the Arduino IDE.
    2. Connect your ESP32 to the internet and copy the snippet below.
    3. The relay controlling your water pump/valve will perfectly instantly sync with this dashboard over the global internet.
    """)
    st.code(get_subscribe_code(), language="cpp")
    st.caption("Listening on: `smartfarm/irrigation/farm_001/+/cmd`")
