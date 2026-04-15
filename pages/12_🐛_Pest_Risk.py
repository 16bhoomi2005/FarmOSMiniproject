import streamlit as st
import sys, os
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import textwrap

# Path alignment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

# Configuration
accent_g = "#4ADE80"
accent_a = "#F59E0B"
accent_r = "#EF4444"
card_bg  = "rgba(13, 43, 26, 0.7)"
text_w   = "#F5F0E8"
text_muted = "rgba(245, 240, 232, 0.6)"

lang = setup_page(
    title=dl.translate("pest_protection", st.session_state.get('lang')),
    subtitle=dl.translate("spray_intel", st.session_state.get('lang')),
    icon="🐛"
)
dl.get_field_sidebar()
is_hi = (lang == 'hi')

# Fetch Data
stats = dl.get_pest_analytics(lang=lang)
p_source = stats.get('source', 'Simulated')
p_color = "#34d399" if "OpenWeather" in p_source else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

# --- HEADER ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px;">
    <div>
        <div style="color:{accent_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;">{dl.translate("active_threats", lang)}</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{p_color}15; border:1px solid {p_color}40; color:{p_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            { ("स्रोत: ओपनवेदर" if is_hi else "Source: OpenWeather") if "OpenWeather" in p_source else dl.translate("simulation_mode", lang) }
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:{text_w}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            { ("अद्यतित " if is_hi else "Updated ") + last_updated }
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric(label=dl.translate("crit_threats", lang), value=stats['critical_count'], delta="Rice Blast", delta_color="inverse")
with k2:
    st.metric(label=dl.translate("active_warns", lang), value=stats['warning_count'], delta="Brown Spot", delta_color="off")
with k3:
    st.metric(label=dl.translate("fields_prot", lang), value=stats['fields_protected'], delta="Last spray: 18d ago", delta_color="off")
with k4:
    st.metric(label=dl.translate("spray_window", lang), value=stats['spray_window'], delta=stats['spray_delta'])
with k5:
    st.metric(label=dl.translate("days_since_spray", lang), value=stats['avg_days_since'], delta="Interval exceeded (14d)", delta_color="inverse")

# --- AI THREAT SUMMARY ---
st.markdown("<br>", unsafe_allow_html=True)
sum_col, btn_col = st.columns([4, 1])

with sum_col:
    st.markdown(f"""
    <div style="background:rgba(245, 158, 11, 0.08); border:1px solid rgba(245, 158, 11, 0.2); border-radius:12px; padding:15px; display:flex; gap:15px; align-items:start;">
        <div style="color:{accent_a}; font-size:1.2rem; margin-top:2px;">●</div>
        <div>
            <div style="color:{accent_a}; font-weight:700; font-size:0.6rem; text-transform:uppercase; margin-bottom:4px;">{dl.translate("threat_summary", lang)}</div>
            <div style="color:{text_w}; font-size:0.85rem;">{stats['analysis']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with btn_col:
    if st.button(dl.translate("get_spray_plan", lang), use_container_width=True, type="primary"):
        st.toast("Calculating dosages..." if not is_hi else "खुराक की गणना की जा रही है...")
        st.info("🧴 **Spray Recommendation**\n- Product: Tricyclazole 75% WP\n- Dosage: 0.6g per liter of water\n- Targets: Rice Blast & Leaf Spot\n- Safety: Wear mask/gloves during application.")

# --- DETAILED BREAKDOWN GRID ---
st.markdown("<br>", unsafe_allow_html=True)
st.html(f'<div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:15px;">{dl.translate("threat_breakdown", lang)}</div>')

def render_threat_card(col_obj, name, risk_val, drivers, actions, idx):
    col = accent_r if risk_val > 75 else accent_a if risk_val > 50 else accent_g
    status = "CRITICAL" if risk_val > 75 else "WARNING" if risk_val > 50 else "LOW"
    dr_html = "".join([f'<div style="text-align:center;"><div style="color:{text_muted}; font-size:0.5rem; text-transform:uppercase;">{k}</div><div style="font-weight:700; font-size:0.8rem; color:{v_c if v_c else text_w};">{v}</div></div>' for k, v, v_c in drivers])
    
    card_html = (
        f'<div style="background:{card_bg}; border: 1px solid rgba(255,255,255,0.08); border-radius:12px; padding:15px; margin-bottom:10px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">'
        f'<div style="font-weight:700; font-size:1rem; color:{text_w};">{name}</div>'
        f'<div style="background:{col}20; color:{col}; font-size:0.5rem; font-weight:800; padding:2px 8px; border-radius:4px; border:1px solid {col}44;">{risk_val}% - {status}</div>'
        f'</div>'
        f'<div style="color:{text_muted}; font-size:0.65rem; margin-bottom:4px;">{dl.translate("risk_lvl", lang)}</div>'
        f'<div style="height:6px; background:rgba(255,255,255,0.05); border-radius:3px; margin-bottom:20px;">'
        f'<div style="height:100%; width:{risk_val}%; background:{col}; border-radius:3px;"></div>'
        f'</div>'
        f'<div style="display:flex; justify-content:space-between; margin-bottom:20px;">{dr_html}</div>'
        f'<div style="color:{text_muted}; font-size:0.65rem; line-height:1.4; margin-bottom:20px; height:45px; overflow:hidden;">'
        f'<span style="font-weight:700; color:{text_w};">Action:</span> {actions}</div>'
        f'</div>'
    )
    with col_obj:
        st.html(card_html)
        b1, b2 = st.columns(2)
        if b1.button(dl.translate("log_spray", lang), key=f"log_spray_{idx}", use_container_width=True):
            st.success("✅ Spray Logged!" if not is_hi else "✅ छिड़काव दर्ज किया गया!")
        if b2.button(dl.translate("view_history", lang), key=f"hist_{idx}", use_container_width=True):
            st.switch_page("pages/14_📋_Season_Report.py")

rows = [stats['threats'][i:i+3] for i in range(0, len(stats['threats']), 3)]
for idx_r, row in enumerate(rows):
    cols = st.columns(3)
    for i, t_name in enumerate(row):
        avg_risk = int(np.mean([stats['matrix'][f].get(t_name, 0) for f in stats['matrix']]))
        with cols[i]:
            detail = stats['details'].get(t_name, stats['details']['Leaf Folder'])
            color_map = {"critical": accent_r, "warning": accent_a, "safe": accent_g, "normal": None}
            processed_drivers = [(d[0], d[1], color_map.get(d[2])) for d in detail['drivers']]
            action_text = detail['action_hi'] if lang == "hi" else detail['action']
            render_threat_card(cols[i], t_name, avg_risk, processed_drivers, action_text, f"{idx_r}_{i}")

# --- FIELD + THREAT RISK MATRIX ---
st.html(f'<br><div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin:20px 0 15px 0;">{dl.translate("threat_matrix", lang)}</div>')

thead = "".join([f'<th style="padding:10px; font-size:0.6rem; color:{text_muted}; font-weight:400; text-align:center;">{t}</th>' for t in stats['threats']])
tbody = ""
for f_name, risks in stats['matrix'].items():
    row_cells = "".join([
        f'<td style="padding:8px;"><div style="background:{accent_r if risks.get(t,0)>75 else accent_a if risks.get(t,0)>50 else "transparent"}30; border:1px solid {accent_r if risks.get(t,0)>75 else accent_a if risks.get(t,0)>50 else "rgba(255,255,255,0.05)"}; border-radius:6px; height:36px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.75rem; color:{accent_r if risks.get(t,0)>75 else accent_a if risks.get(t,0)>50 else text_w};">{int(risks.get(t,0))}%</div></td>'
        for t in stats['threats']
    ])
    tbody += f'<tr><td style="padding:10px; font-size:0.75rem; font-weight:500; color:{text_muted};">{f_name}</td>{row_cells}</tr>'

st.html(f'<div style="background:{card_bg}; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:10px; overflow-x:auto;"><table style="width:100%; border-collapse:collapse;"><thead><tr><th></th>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>')

# --- LEGEND ---
st.markdown(f"""
<div style="display:flex; gap:20px; font-size:0.65rem; color:{text_muted}; margin-top:12px;">
    <div style="display:flex; align-items:center; gap:6px;"><span style="color:{accent_r}">■</span> Critical (>75%)</div>
    <div style="display:flex; align-items:center; gap:6px;"><span style="color:{accent_a}">■</span> Warning (50–75%)</div>
    <div style="display:flex; align-items:center; gap:6px;"><span style="color:{accent_g}">■</span> Monitor (30–50%)</div>
    <div style="display:flex; align-items:center; gap:6px;"><span style="color:{text_muted}">■</span> Safe (<30%)</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div style="color:{text_muted}; font-size:0.6rem; text-align:center; margin-top:15px;">Target treatment interval: 14 days. Critical fields highlighted for immediate inspection.</div>', unsafe_allow_html=True)
