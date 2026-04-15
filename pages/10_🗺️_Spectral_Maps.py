import streamlit as st
import sys, os
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# Path alignment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

# Configuration
accent_g = "#4ADE80"
accent_a = "#F59E0B"
accent_r = "#EF4444"
accent_p = "#166534" # Peak 
card_bg  = "rgba(13, 43, 26, 0.7)"
text_w   = "#F5F0E8"
text_muted = "rgba(245, 240, 232, 0.6)"

lang = setup_page(
    title="Field Health Maps" if st.session_state.get('lang') != 'hi' else "खेत का स्वास्थ्य नक्शा",
    subtitle="Colour-coded satellite view of all 9 sub-plots" if st.session_state.get('lang') != 'hi' else "सभी 9 उप-प्लॉटों का रंग-कोडित सैटेलाइट व्यू",
    icon="🗺️"
)
dl.get_field_sidebar()
is_hi = (lang == 'hi')

# Live Source Verification
sat_source = st.session_state.get('sat_source_verification', 'Heuristic')
sat_color = "#34d399" if "Sentinel-2" in sat_source else "#E8A020"

# Map Selection with Source Tracking
c1, c2 = st.columns([2, 1])
with c1:
    map_types = [
        "Overall crop health (NDVI)" if not is_hi else "कुल फसल स्वास्थ्य (NDVI)",
        "Moisture (NDWI)" if not is_hi else "नमी (NDWI)",
        "Stress zones" if not is_hi else "तनाव क्षेत्र",
        "Yield potential" if not is_hi else "पैदावार की क्षमता"
    ]
    selected_map = st.radio("Select Analysis Layer", map_types, horizontal=True, label_visibility="collapsed")
with c2:
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; align-items:center;">
        <div style="background:{sat_color}20; color:{sat_color}; padding:4px 12px; border-radius:30px; font-size:0.7rem; font-weight:700; border:1px solid {sat_color}40; text-transform:uppercase;">
            SAT: {sat_source}
        </div>
    </div>
    """, unsafe_allow_html=True)

idx_key = "STRESS" if "Stress" in selected_map else "YIELD" if "Yield" in selected_map else "NDWI" if "Moisture" in selected_map else "NDVI"

# Fetch Data
stats = dl.get_spectral_analytics(index_key=idx_key, lang=lang)
from sim_engine import get_sim_engine
engine = get_sim_engine()

# --- HEADER (KPIs) ---
st.markdown("<br>", unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    h_percent = stats['healthy_percent']
    status_tag = ("कुल मिलाकर अच्छा" if is_hi else "Good overall") if h_percent > 70 else ("स्थिर" if is_hi else "Stable") if h_percent > 40 else ("आज कार्रवाई करें" if is_hi else "Act today")
    st.metric(label=("औसत खेत " if is_hi else "AVG FARM ") + idx_key, value=f"{stats['avg_farm_val']:.2f}", delta=status_tag)
with k2:
    st.metric(label=("गंभीर क्षेत्र" if is_hi else "CRITICAL ZONES"), value=stats['critical_count'], delta=stats['critical_names'], delta_color="inverse")
with k3:
    st.metric(label=("निगरानी क्षेत्र" if is_hi else "WATCH ZONES"), value=stats['watch_count'], delta=("विचलन पाया गया" if is_hi else "Variance detected"), delta_color="off")
with k4:
    st.metric(label=("सर्वश्रेष्ठ खेत" if is_hi else "BEST FIELD"), value=stats['best_field'], delta=("शिखर क्षेत्र" if is_hi else "Peak Area"))
with k5:
    st.metric(label=("स्वस्थ क्षेत्र" if is_hi else "HEALTHY AREA"), value=f"{stats['healthy_percent']:.0f}%", delta=f"{stats['healthy_percent']/11:.0f} of 9 fields" if not is_hi else f"9 में से {stats['healthy_percent']/11:.0f} खेत")

# Legend Color Bar
st.markdown(f"""
<div style="display:flex; justify-content:flex-end; align-items:center; gap:10px; margin: 10px 0;">
    <div style="font-size:0.6rem; color:{text_muted}; text-transform:uppercase;">{ ("गंभीर" if is_hi else "Critical") }</div>
    <div style="width:120px; height:8px; border-radius:4px; background:linear-gradient(90deg, {accent_r}, {accent_a}, {accent_g}, {accent_p});"></div>
    <div style="font-size:0.6rem; color:{text_muted}; text-transform:uppercase;">{ ("शिखर" if is_hi else "Peak") }</div>
</div>
""", unsafe_allow_html=True)

# --- GRID OF FIELDS ---
# Custom order for reference image: SE, North, East, NW, West, NE, South, SW, Central
order = ["SE", "North", "East", "NW", "West", "NE", "South", "SW", "Center"]

st.markdown(f'<div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:15px;">{ ("सभी 9 खेत — " if is_hi else "ALL 9 FIELDS — ") + idx_key + (" हीटमैप व्यू" if is_hi else " HEATMAP VIEW") }</div>', unsafe_allow_html=True)

rows = [order[i:i+3] for i in range(0, 9, 3)]
for row_names in rows:
    cols = st.columns(3)
    for i, f_name in enumerate(row_names):
        with cols[i]:
            f_data = engine.get_field(f_name)
            avg_val = f_data.get(idx_key.lower(), 0.5)
            if is_hi:
                status_lbl = "शिखर स्वास्थ्य" if avg_val > 0.75 else "स्वस्थ" if avg_val > 0.5 else "निगरानी करें" if avg_val > 0.4 else "जोखिम में" if avg_val > 0.2 else "गंभीर"
            else:
                status_lbl = "Peak health" if avg_val > 0.75 else "Healthy" if avg_val > 0.5 else "Monitor" if avg_val > 0.4 else "At risk" if avg_val > 0.2 else "Critical"
            status_col = accent_p if avg_val > 0.75 else accent_g if avg_val > 0.5 else accent_a if avg_val > 0.3 else accent_r
            
            # Map Canvas
            grid = engine.get_spatial_grid(idx_key, f_name)
            # Use a smaller slice for the 10x4 visual effect if desired, or full 10x10
            viz_grid = np.array(grid)[:6, :] # 6x10 grid for card aspect ratio
            
            fig = go.Figure(data=go.Heatmap(
                z=viz_grid, colorscale=[[0, accent_r], [0.3, accent_a], [0.6, accent_g], [1, accent_p]],
                showscale=False, hoverinfo='none'
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0), height=80, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(visible=False), yaxis=dict(visible=False)
            )
            
            st.markdown(f"""
            <div style="background:{card_bg}; border: 1px solid rgba(255,255,255,0.08); border-radius:12px; padding:12px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div style="font-weight:700; font-size:0.85rem; display:flex; align-items:center; gap:6px;">
                        <span style="color:{status_col};">●</span> {f_name} Field
                    </div>
                    <div style="background:{status_col}20; color:{status_col}; font-size:0.5rem; font-weight:700; padding:2px 6px; border-radius:4px; text-transform:uppercase;">{status_lbl}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(fig, width="stretch", config={'displayModeBar': False}, key=f"spectral_heatmap_{idx_key}_{f_name}")
            st.markdown(f"""
            <div style="background:{card_bg}; border: 1px solid rgba(255,255,255,0.08); border-top:none; border-radius:0 0 12px 12px; padding:8px 12px; margin-top:-14px; margin-bottom:15px; display:flex; justify-content:space-between;">
                <div><div style="color:{text_muted}; font-size:0.55rem;">{idx_key}</div><div style="font-weight:700; font-size:0.8rem; color:{status_col if idx_key=='NDVI' else text_w};">{avg_val:.2f}</div></div>
                <div><div style="color:{text_muted}; font-size:0.55rem;">MOISTURE</div><div style="font-weight:700; font-size:0.8rem;">{f_data['moisture']:.0f}%</div></div>
                <div><div style="color:{text_muted}; font-size:0.55rem;">YIELD EST.</div><div style="font-weight:700; font-size:0.8rem; color:{accent_a}">{f_data['yield_pred']:.1f} t</div></div>
            </div>
            """, unsafe_allow_html=True)

# --- AI FIELD ANALYSIS ---
st.markdown(f"""
<div style="background:rgba(74, 222, 128, 0.08); border:1px solid rgba(74, 222, 128, 0.2); border-radius:12px; padding:15px; margin: 15px 0; display:flex; justify-content:space-between; align-items:center; gap:20px;">
    <div style="display:flex; gap:15px; align-items:start;">
        <div style="color:{accent_g}; font-size:1.2rem; margin-top:2px;">●</div>
        <div>
            <div style="color:{accent_g}; font-weight:700; font-size:0.6rem; text-transform:uppercase; margin-bottom:4px;">AI Field Analysis</div>
            <div style="color:{text_w}; font-size:0.85rem;">{stats['ai_analysis']}</div>
        </div>
    </div>
    <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:8px 15px; font-size:0.75rem; color:{text_w}; cursor:pointer; white-space:nowrap;">Ask AI for plan ↗</div>
</div>
""", unsafe_allow_html=True)

# --- RANKING LEADERBOARD ---
st.markdown(f'<div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin:25px 0 15px 0;">{idx_key} FIELD RANKING — BEST TO WEAKEST</div>', unsafe_allow_html=True)

for i, rank in enumerate(stats['ranking']):
    progress = rank['value'] * 100
    rank_color = accent_g if progress > 70 else accent_a if progress > 40 else accent_r
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:20px; margin-bottom:12px;">
        <div style="width:20px; color:{text_muted}; font-size:0.8rem;">{i+1}</div>
        <div style="width:100px; font-size:0.8rem; font-weight:500;">{rank['name']} Field</div>
        <div style="width:40px; font-size:0.8rem; color:{rank_color}; font-weight:700;">{rank['value']:.2f}</div>
        <div style="flex-grow:1; height:8px; background:rgba(255,255,255,0.05); border-radius:4px; position:relative;">
            <div style="position:absolute; left:0; top:0; height:100%; width:{progress}%; background:{accent_g if progress > 70 else accent_a if progress > 40 else accent_r}; border-radius:4px; opacity:0.3;"></div>
            <div style="position:absolute; left:0; top:0; height:100%; width:{progress*0.8}%; border-right:2px solid {rank_color};"></div>
        </div>
        <div style="width:50px; text-align:right; font-size:0.8rem; color:{accent_g if i < 3 else accent_r};">+0.02</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style="display:flex; gap:20px; font-size:0.65rem; color:{text_muted}; margin-top:5px;">
    <div style="display:flex; align-items:center; gap:6px;"><span style="color:{accent_g}">■</span> Healthy > 0.75</div>
    <div style="display:flex; align-items:center; gap:6px;"><span style="color:{accent_a}">■</span> Watch 0.3–0.75</div>
    <div style="display:flex; align-items:center; gap:6px;"><span style="color:{accent_r}">■</span> Critical < 0.3</div>
</div>
""", unsafe_allow_html=True)

# --- ZONE BREAKDOWN FOOTER ---
if idx_key == "NDWI":
    labels = ["Saturated / Water", "Highly Moist", "Optimal Moisture", "Dry Soil", "Parched"]
    descs = ["NDRE > 0.45", "NDRE 0.25-0.45", "NDRE 0.15-0.25", "NDRE 0.05-0.15", "NDRE < 0.05"]
    h_desc = "Percentage in optimal or moist range"
else:
    labels = ["Peak health", "Healthy", "Watch closely", "Stressed", "Act now"]
    descs = ["NDVI 0.75-1.0", "NDVI 0.5-0.75", "NDVI 0.3-0.5", "NDVI 0.15-0.3", "NDVI < 0.15"]
    h_desc = "Percentage in healthy or peak range"

st.markdown(f'<br><div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin:20px 0 15px 0;">ZONE BREAKDOWN — WHAT DO THE COLOURS MEAN?</div>', unsafe_allow_html=True)

breakdown_items = [
    {"label": labels[0], "val": stats['breakdown']['peak'], "desc": descs[0], "color": accent_p},
    {"label": labels[1], "val": stats['breakdown']['healthy'], "desc": descs[1], "color": accent_g},
    {"label": labels[2], "val": stats['breakdown']['watch'], "desc": descs[2], "color": accent_a},
    {"label": labels[3], "val": stats['breakdown']['stressed'], "desc": descs[3], "color": "#D97706"},
    {"label": labels[4], "val": stats['breakdown']['critical'], "desc": descs[4], "color": accent_r},
    {"label": "Total farm coverage", "val": stats['healthy_percent'], "desc": h_desc, "color": accent_g}
]

rows = [breakdown_items[i:i+3] for i in range(0, 6, 3)]
for row in rows:
    cols = st.columns(3)
    for i, item in enumerate(row):
        with cols[i]:
            st.markdown(f"""
            <div style="border: 1px solid rgba(255,255,255,0.08); border-radius:12px; padding:15px; height:100%;">
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:10px;">
                    <div style="color:{text_w}; font-weight:500; font-size:0.8rem;">{item['label']}</div>
                    <div style="color:{item['color']}; font-weight:700; font-size:1.4rem;">{item['val']:.0f}%</div>
                </div>
                <div style="height:4px; background:rgba(255,255,255,0.05); border-radius:2px; margin-bottom:12px;">
                    <div style="height:100%; width:{item['val']}%; background:{item['color']}; border-radius:2px;"></div>
                </div>
                <div style="color:{text_muted}; font-size:0.65rem; line-height:1.4;">{item['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

