import streamlit as st
import sys, os
import json
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl
import decision_engine as de

# --- Page Setup & Data ---
lang = setup_page(
    title="AI Agronomist" if st.session_state.get('lang') != 'hi' else "AI कृषि विशेषज्ञ",
    subtitle="Expert terminal for proactive crop management" if st.session_state.get('lang') != 'hi' else "सक्रिय फसल प्रबंधन के लिए विशेषज्ञ टर्मिनल",
    icon="🧠"
)
dl.get_field_sidebar()
is_hi = (lang == 'hi')

field_intel = dl.get_field_intelligence(lang=lang)
summary = field_intel["summary"]
yield_data = field_intel["yield_estimate"]
life_cycle = dl.get_rice_life_cycle()
cur_stage = life_cycle.get('stage', 'Tillering')
dat = life_cycle.get('dat', 45)

# Generate Agromet Brief
agromet_brief = de.generate_agronomist_brief(field_intel, lang=lang)

# --- Design Tokens ---
accent_g = "#4ADE80"
accent_a = "#E8A020"
card_bg = "#1A1A1A"
text_g = "#86A789"
text_w = "#F5F5F5"
text_muted = "#A3A3A3"

# --- Custom CSS ---
st.markdown(f"""
<style>
    .agro-card {{
        background: {card_bg};
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }}
    .agro-header {{
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 25px; padding-bottom: 10px; border-bottom: 1px solid #262626;
    }}
    .badge {{
        padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
        background: #262626; color: {text_w};
    }}
    .badge-green {{ background: #4ADE8020; color: #4ADE80; border: 1px solid #4ADE8040; }}
    .badge-blue {{ background: #38BDF820; color: #38BDF8; border: 1px solid #38BDF840; }}
    
    .recommend-card {{
        background: #1A1505; border: 1px solid #E8A02040; border-radius: 8px;
        padding: 20px; display: flex; gap: 15px; align-items: flex-start;
        margin-bottom: 25px;
    }}
    
    /* Timeline */
    .timeline-container {{
        display: flex; justify-content: space-between; align-items: center;
        position: relative; margin-top: 20px; padding: 0 10px;
    }}
    .timeline-line {{
        position: absolute; top: 8px; left: 0; right: 0;
        height: 2px; background: #262626; z-index: 0;
    }}
    .timeline-progress {{
        position: absolute; top: 8px; left: 0;
        height: 2px; background: {accent_g}; z-index: 1;
    }}
    .node {{
        width: 16px; height: 16px; border-radius: 50%; background: #262626;
        border: 2px solid #525252; z-index: 2; position: relative;
    }}
    .node-done {{ background: {accent_g}; border-color: {accent_g}; }}
    .node-active {{ 
        background: #FFF; border-color: {accent_g}; 
        box-shadow: 0 0 15px {accent_g}; 
    }}
    .node-lbl {{ 
        font-size: 0.65rem; color: #737373; margin-top: 25px; 
        position: absolute; text-align: center; width: 60px; left: -22px;
    }}
    .node-active-lbl {{ color: {accent_g}; font-weight: 700; }}
    
    /* Progress Bars */
    .driver-row {{ margin-bottom: 15px; }}
    .driver-lbl {{ display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 5px; }}
    .p-bar {{ height: 8px; background: #262626; border-radius: 4px; overflow: hidden; }}
    .p-fill {{ height: 100%; border-radius: 4px; }}
    
    /* Chat Sugestions */
    .sugg-box {{
        display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;
    }}
    .sugg-btn {{
        background: #1A1A1A; border: 1px solid #404040; border-radius: 20px;
        padding: 6px 15px; color: #D4D4D4; font-size: 0.75rem; cursor: pointer;
    }}
    .sugg-btn:hover {{ border-color: #737373; color: #FFF; }}
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown(f"""
<div class="agro-header">
    <div style="font-size:1.2rem; font-weight:700; color:{text_w};">AI Agronomist</div>
    <div style="display:flex; gap:10px;">
        <div class="badge">Rice · All fields</div>
        <div class="badge badge-blue">{cur_stage} stage</div>
        <div style="font-size:0.75rem; color:{text_muted};">{datetime.now().strftime('%d %b %Y · %H:%M')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Recommendation Card ---
st.markdown(f"""
<div class="recommend-card">
    <div style="font-size:1.4rem;">⚠️</div>
    <div>
        <div style="color:{accent_a}; font-weight:700; font-size:0.85rem; margin-bottom:4px; text-transform:uppercase;">Today's AI recommendation</div>
        <div style="color:{accent_a}; font-size:0.9rem; line-height:1.4;">{agromet_brief}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Growth Stage Terminal ---
with st.container():
    # Render entire timeline as a single block to avoid broken divs
    stages = ["Seedling", "Tillering", "Jointing", "Heading", "Grain Filling", "Maturity"]
    dats = [0, 20, 45, 70, 90, 120]
    
    active_idx = 2
    for i, s in enumerate(stages):
        if s.lower() in cur_stage.lower():
            active_idx = i
            break
            
    prog_width = (active_idx / (len(stages)-1)) * 100
    
    timeline_html = f'<div class="timeline-container"><div class="timeline-line"></div><div class="timeline-progress" style="width:{prog_width}%;"></div>'
    for i, s in enumerate(stages):
        is_done = i < active_idx
        is_active = i == active_idx
        cls = "node-active" if is_active else "node-done" if is_done else ""
        lbl_cls = "node-active-lbl" if is_active else ""
        now_lbl = f"<div style='font-size:0.6rem; color:{accent_g};'>Now · Day {dat}</div>" if is_active else f"<div style='font-size:0.6rem;'>~Day {dats[i]}</div>" if i > 0 else f"<div style='font-size:0.6rem;'>Day 0</div>"
        timeline_html += f'<div class="node {cls}"><div class="node-lbl {lbl_cls}">{s}<br>{now_lbl}</div></div>'
    timeline_html += "</div>"

    st.markdown(f"""
    <div class="agro-card">
        <div style='color:{text_muted}; font-size:0.65rem; font-weight:700; letter-spacing:1px; margin-bottom:20px; text-transform:uppercase;'>{ ("विकास का चरण" if is_hi else "GROWTH STAGE") }</div>
        {timeline_html}
        <br><br>
    </div>
    """, unsafe_allow_html=True)

# --- Telemetry Grid (Health vs Yield) ---
t1, t2 = st.columns(2)

with t1:
    drivers_html = ""
    drivers = [
        {"lbl": ("फसल की हरियाली" if is_hi else "Crop greenness"), "val": summary.get('ndvi', 0), "max": 1, "color": "#4ADE80"},
        {"lbl": ("कीट जोखिम" if is_hi else "Pest risk"), "val": field_intel.get('disease_risk', {}).get('score', 0), "max": 100, "color": "#FB923C", "inv": True},
        {"lbl": ("मिट्टी की नमी" if is_hi else "Soil moisture"), "val": summary.get('soil_moisture', 0), "max": 100, "color": "#FB923C"},
        {"lbl": ("मिट्टी का पीएच" if is_hi else "Soil pH"), "val": summary.get('ph', 6.5), "max": 14, "color": "#4ADE80"}
    ]
    
    for d in drivers:
        pct = (d['val'] / d['max']) * 100
        if d.get('inv'): pct = 100 - pct
        color = d['color']
        val_str = f"{d['val']:.2f}" if d['lbl'] == 'Crop greenness' else f"{d['val']}"
        drivers_html += (
            f'<div class="driver-row">'
            f'<div class="driver-lbl"><div style="color:{text_muted}">{d["lbl"]}</div>'
            f'<div style="color:{color}; font-weight:700;">{val_str}</div></div>'
            f'<div class="p-bar"><div class="p-fill" style="width:{pct}%; background:{color};"></div></div>'
            f'</div>'
        )

    st.markdown(f'<div class="agro-card" style="height:400px; margin-bottom:0;">'
                f'<div style="color:{text_muted}; font-size:0.65rem; font-weight:700; letter-spacing:1px; margin-bottom:25px; text-transform:uppercase;">{ ("स्वास्थ्य स्कोर को प्रभावित करने वाले कारक" if is_hi else "WHAT\'S AFFECTING HEALTH SCORE") }</div>'
                f'{drivers_html}'
                f'<div style="display:flex; gap:15px; margin-top:25px;">'
                f'<div style="display:flex; align-items:center; gap:5px; font-size:0.65rem; color:{text_muted};"><div style="width:8px; height:8px; background:#4ADE80; border-radius:2px;"></div> { ("सकारात्मक" if is_hi else "Positive") }</div>'
                f'<div style="display:flex; align-items:center; gap:5px; font-size:0.65rem; color:{text_muted};"><div style="width:8px; height:8px; background:#FB923C; border-radius:2px;"></div> { ("चेतावनी" if is_hi else "Warning") }</div>'
                f'</div></div>', unsafe_allow_html=True)

with t2:
    y_val = float(yield_data['estimate'])
    t_yield_lbl = dl.translate("yield_projection", lang)
    t_expected_lbl = ("कटाई पर अपेक्षित" if is_hi else "Expected at harvest")
    t_low = ("न्यूनतम" if is_hi else "LOW")
    t_exp = ("अपेक्षित" if is_hi else "EXP")
    t_high = ("अधिकतम" if is_hi else "HIGH")

    st.markdown(f'<div class="agro-card" style="height:400px; margin-bottom:0; display: flex; flex-direction: column;">'
                f'<div style="color:{text_muted}; font-size:0.65rem; font-weight:700; letter-spacing:1px; margin-bottom:10px; text-transform:uppercase;">{t_yield_lbl}</div>'
                f'<div style="color:{accent_g}; font-size:2.8rem; font-weight:800; margin-bottom:0;">{y_val:.2f} t/ac</div>'
                f'<div style="color:{text_muted}; font-size:0.75rem; margin-bottom:15px;">{t_expected_lbl} · ± {y_val*0.08:.2f} (90% conf)</div>'
                f'<div style="display:flex; justify-content:space-between; margin-bottom:15px;">'
                f'<div><div style="color:{text_muted}; font-size:0.6rem; font-weight:700;">{t_low}</div><div style="color:{text_w}; font-weight:700; font-size:0.8rem;">{y_val*0.92:.2f}</div></div>'
                f'<div><div style="color:{accent_g}; font-size:0.6rem; font-weight:700;">{t_exp}</div><div style="color:{accent_g}; font-weight:700; font-size:0.8rem;">{y_val:.2f}</div></div>'
                f'<div><div style="color:{text_w}; font-size:0.6rem; font-weight:700;">{t_high}</div><div style="color:{text_w}; font-weight:700; font-size:0.8rem;">{y_val*1.08:.2f}</div></div>'
                f'</div><div id="plotly-yield-container" style="flex-grow:1;"></div></div>', unsafe_allow_html=True)
    
    weeks = [f"W{i}" for i in range(1, 16, 2)]
    y_trail = [y_val * (0.8 + 0.015*i) for i in range(len(weeks))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weeks, y=y_trail, mode='lines', line=dict(color=accent_g, width=3), fill='tozeroy', fillcolor="rgba(74, 222, 128, 0.1)"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=5, b=5), height=140,
        xaxis=dict(showgrid=False, color="#525252", tickfont=dict(size=8)),
        yaxis=dict(showgrid=True, gridcolor="#262626", color="#525252", tickfont=dict(size=8), range=[y_val*0.7, y_val*1.1])
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- Ask AI Terminal ---
st.markdown("<br>", unsafe_allow_html=True)

# Custom CSS for Streamlit's native chat components to match the dashboard
st.markdown(f"""
<style>
    [data-testid="stChatMessage"] {{
        background: {card_bg};
        border: 1px solid #262626;
        border-radius: 8px;
        margin-bottom: 10px;
    }}
    /* Style Chat Input */
    .stChatInputContainer {{
        padding-bottom: 20px;
    }}
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown(f"""
    <div style="background:{card_bg}; border:1px solid #262626; border-radius:12px 12px 0 0; padding:20px; border-bottom:none;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.2rem;">🤖</span>
            <div style="color:{text_w}; font-weight:700; font-size:1rem;">Farm Terminal</div>
        </div>
        <div style="color:{text_muted}; font-size:0.75rem; margin-top:5px;">Expert agronomic intelligence specialized in rice.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Terminal Output Area (History)
    terminal_box = st.container()
    with terminal_box:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        for msg in st.session_state.chat_history:
            icon = "👤" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=icon):
                st.markdown(f'<div style="font-family: monospace; font-size:0.9rem;">{msg["content"]}</div>', unsafe_allow_html=True)

    # Suggestion Tray
    st.markdown('<div style="background:' + card_bg + '; padding: 0 20px 15px 20px; border-left:1px solid #262626; border-right:1px solid #262626;">', unsafe_allow_html=True)
    c1, c2, c3, _ = st.columns([1,1,1,2])
    with c1:
        if st.button("Irrigation?", key="sug1"): st.session_state.temp_prompt = "Irrigation status?"
    with c2:
        if st.button("Pest Risk", key="sug2"): st.session_state.temp_prompt = "Pest risk report"
    with c3:
        if st.button("Fertilizer", key="sug3"): st.session_state.temp_prompt = "Fertilizer plan"
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input Area
    st.markdown('<div style="background:'+card_bg+'; border: 1px solid #262626; border-top:none; border-radius: 0 0 12px 12px; padding: 0 10px 10px 10px;">', unsafe_allow_html=True)
    q_placeholder = "Query irrigation, fertilization, or pest risk..." if not is_hi else "सिंचाई, उर्वरक या कीट जोखिम के बारे में पूछें..."
    prompt = st.chat_input(q_placeholder)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get('temp_prompt'):
        prompt = st.session_state.pop('temp_prompt')
    
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with terminal_box:
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
        
        with terminal_box:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Processing..." if not is_hi else "विश्लेषण हो रहा है..."):
                    # Map field_intel to ctx for the chat engine
                    from ai.chat_engine import get_agronomist_response
                    
                    ctx = {
                        "ndvi": summary.get("ndvi", 0.5),
                        "stage": cur_stage,
                        "temp": summary.get("temp", 28),
                        "humidity": summary.get("humidity", 70),
                        "rain_3d": summary.get("rain_3d", 5.0),
                        "soil_moisture": summary.get("soil_moisture", 50),
                        "yield_estimate": yield_data.get("estimate", 4.5),
                        "if_no_action_yield": yield_data.get("if_no_action", 4.0),
                        "nitrogen_level": field_intel.get("nitrogen_risk", {}).get("level", "Unknown"),
                        "nitrogen_score": field_intel.get("nitrogen_risk", {}).get("score", 0),
                        "nitrogen_dose_kg": field_intel.get("nitrogen_risk", {}).get("dose_kg_per_acre", 0),
                        "irrigation_score": field_intel.get("irrigation_risk", {}).get("urgency_score", 0),
                        "recommended_depth": field_intel.get("irrigation_risk", {}).get("target_depth", "2-5 cm"),
                        "disease_level": field_intel.get("disease_risk", {}).get("level", "Low"),
                        "disease_score": field_intel.get("disease_risk", {}).get("score", 0),
                        "disease_threat": field_intel.get("disease_risk", {}).get("threat", "None"),
                    }
                    
                    reply = get_agronomist_response(prompt, ctx, lang=lang)
                    
                    # Ensure Terminal Analysis prefix
                    if not reply.startswith("**[TERMINAL ANALYSIS]**"):
                        reply = f"**[TERMINAL ANALYSIS]**\n\n{reply}"
                        
                    st.markdown(f'<div style="font-family: monospace; color: {accent_g};">{reply}</div>', unsafe_allow_html=True)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
