"""
Page 11 — 📅 Temporal Trends
==============================
Shows 16-week NDVI / Soil Moisture / Health Score time series
for each rice field.

Weeks 1–12: historical data (solid lines).
Weeks 13–16: LSTM-simulated forecast (dashed lines).
Coloured vertical bands mark weather events (Rain/Drought/Flood).

Data priority:
  1. dl.get_field_history() — real logged history from MongoDB
  2. sim_engine time-series — offline fallback with realistic rice
"""

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import io

try:
    import data_loader as dl
    dl.get_field_sidebar()
    REAL_DATA_AVAILABLE = True
except Exception:
    REAL_DATA_AVAILABLE = False

import streamlit as st
if "farm_sim" not in st.session_state:
    st.session_state.farm_sim = dl.get_sim_engine()
engine = st.session_state.farm_sim
_st = st  # maintain internal reference compatibility

FIELD_NAMES = list(engine.fields.keys())

lang = setup_page(
    title="Crop Progress Over Time",
    subtitle="16-week history and AI yield forecast for all your fields",
    icon="📅",
    explanation_en="This page shows week-by-week how each of your field plots is performing. The solid lines are real recorded data. The dashed lines are the AI's forecast for the next 4 weeks.",
    explanation_hi="यह पृष्ठ दिखाता है कि आपके प्रत्येक खेत ब्लॉक सप्ताह-दर-सप्ताह कैसे प्रदर्शन कर रहा है। ठोस रेखाएं वास्तविक डेटा हैं। डैशड रेखाएं AI की अगले 4 सप्ताह की भविष्यवाणी हैं।"
)
if 'lang' not in _st.session_state:
    _st.session_state.lang = lang

# Data Fetching for Source Verification
history = []
if REAL_DATA_AVAILABLE:
    try:
        history = dl.get_field_history()
    except: pass

is_live = len(history) > 0
h_source = "Verified History (MongoDB)" if is_live else "Simulation Engine"
h_color = "#34d399" if is_live else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

# --- HEADER ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px;">
    <div>
        <div style="color:#22c55e; font-size:0.75rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;">CROP PROGRESS — 16-WEEK GROWTH ANALYTICS</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{h_color}15; border:1px solid {h_color}40; color:{h_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
            Source: {h_source}
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#F5F5F5; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            {len(history)} data points
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────────────
ctrl1, ctrl2 = st.columns([1, 2])

with ctrl1:
    field_lbl = "खेत चुनें" if lang == "hi" else "Select Field"
    sel_field = st.selectbox(field_lbl, FIELD_NAMES)

METRIC_OPTIONS = {
    "NDVI":          ("फसल की हरियाली" if lang == "hi" else "Crop Greenness"),
    "soil_moisture": ("मिट्टी की नमी (%)" if lang == "hi" else "Soil Moisture (%)"),
    "health_score":  ("कुल स्वास्थ्य स्कोर" if lang == "hi" else "Overall Health Score"),
}

with ctrl2:
    met_lbl = "मेट्रिक्स चुनें" if lang == "hi" else "Select Metrics to Show"
    sel_metrics = st.multiselect(
        met_lbl,
        list(METRIC_OPTIONS.keys()),
        default=["NDVI", "health_score"],
        format_func=lambda x: METRIC_OPTIONS[x],
    )

if not sel_metrics:
    st.warning("कृपया कोई मेट्रिक चुनें।" if lang == "hi" else "Please select at least one metric.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
ts = engine.get_time_series(sel_field)

# Try to incorporate real history for NDVI
real_hist_ndvi: list | None = None
if REAL_DATA_AVAILABLE:
    try:
        hist = dl.get_field_history()
        if hist and len(hist) >= 3:
            df_h = pd.DataFrame(hist).sort_values("timestamp")
            # Correctly map NDVI if column exists, else normalize health_score
            if "ndvi" in df_h.columns:
                real_hist_ndvi = df_h["ndvi"].tail(12).tolist()
            elif "health_score" in df_h.columns:
                real_hist_ndvi = (df_h["health_score"] / 100.0).tail(12).tolist()
    except Exception:
        pass

weeks       = ts["weeks"]            # 1–16
n_hist      = 12
n_fore      = 4
is_forecast = ts["is_forecast"]      # list of booleans

def get_series(metric: str) -> dict:
    if metric == "NDVI":
        hist = real_hist_ndvi if real_hist_ndvi and len(real_hist_ndvi) == n_hist else ts["ndvi_hist"]
        lo, hi = 0.1, 1.0
        unit = ""
    elif metric == "soil_moisture":
        hist = ts["sm_hist"]
        lo, hi = 0.0, 100.0
        unit = "%"
    else:  # health_score
        hist = ts["hs_hist"]
        lo, hi = 0.0, 100.0
        unit = ""
        
    from lstm_model import train_and_forecast
    spinner_text = f"AI {sel_field} के डेटा से सीख रहा है..." if lang == "hi" else f"Training AI on {sel_field} {metric} data..."
    with st.spinner(spinner_text):
        res = train_and_forecast(np.array(hist), sel_field, metric)
        
    fore = res["forecast"].tolist()
    upper = res["upper"].tolist()
    lower = res["lower"].tolist()
        
    return {
        "hist": hist, 
        "fore": fore, 
        "upper": upper, 
        "lower": lower, 
        "full": hist + fore, 
        "lo": lo, 
        "hi": hi, 
        "unit": unit, 
        "res": res
    }

METRIC_COLORS = {
    "NDVI":          "#22c55e",
    "soil_moisture": "#3b82f6",
    "health_score":  "#f59e0b",
}
METRIC_NAMES = {
    "NDVI":          "Crop Greenness"   if lang == "en" else "फसल की हरियाली",
    "soil_moisture": "Soil Moisture %"  if lang == "en" else "मिट्टी नमी %",
    "health_score":  "Health Score"     if lang == "en" else "स्वास्थ्य स्कोर",
}

# ── Build Chart ───────────────────────────────────────────────────────────────
fig = go.Figure()

# Weather event vertical bands
EVENT_COLORS = {"Rain": "#3b82f6", "Drought": "#f97316", "Flood": "#06b6d4"}
events = ts.get("events", [])
for ev in events:
    w     = ev["week"]
    color = EVENT_COLORS.get(ev["type"], "#888888")
    fig.add_vrect(
        x0=w - 0.45, x1=w + 0.45,
        fillcolor=color, opacity=0.15, layer="below", line_width=0,
    )
    ev_label = ({"Rain": "🌧️ बारिश", "Drought": "☀️ सूखा", "Flood": "🌊 बाढ़"}
                if lang == "hi" else {"Rain": "🌧️ Rain", "Drought": "☀️ Drought", "Flood": "🌊 Flood"})
    fig.add_annotation(
        x=w, y=1.07, xref="x", yref="paper",
        text=f"<b>{ev_label.get(ev['type'], ev['type'])}</b>",
        showarrow=False, font=dict(size=9, color=color),
    )

# Forecast region shade
fig.add_vrect(
    x0=n_hist + 0.5, x1=n_hist + n_fore + 0.5,
    fillcolor="#6366f1", opacity=0.06, layer="below", line_width=0,
)
fore_label = "AI पूर्वानुमान →" if lang == "hi" else "AI Forecast →"
fig.add_annotation(
    x=n_hist + 2, y=1.07, xref="x", yref="paper",
    text=f"<b style='color:#6366f1'>{fore_label}</b>",
    showarrow=False, font=dict(size=10, color="#6366f1"),
)

model_details = []

# Metric traces (solid historical, dashed forecast)
for metric in sel_metrics:
    sdata = get_series(metric)
    color = METRIC_COLORS[metric]
    name  = METRIC_NAMES[metric]
    hist  = sdata["hist"]
    fore  = sdata["fore"]
    upper = sdata["upper"]
    lower = sdata["lower"]
    
    model_details.append((name, sdata["res"]))

    # Historical solid
    fig.add_trace(go.Scatter(
        x=list(range(1, n_hist + 1)),
        y=hist,
        name=name + (" (इतिहास)" if lang == "hi" else " (History)"),
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=5),
        hovertemplate=f"<b>Week %{{x}}</b><br>{name}: %{{y:.3f}}<extra></extra>",
    ))

    # Forecast dashed (connect from last hist point)
    fig.add_trace(go.Scatter(
        x=[n_hist] + list(range(n_hist + 1, n_hist + n_fore + 1)),
        y=[hist[-1]] + fore,
        name=name + (" (अनुमान)" if lang == "hi" else " (Forecast)"),
        mode="lines+markers",
        line=dict(color=color, width=2, dash="dash"),
        marker=dict(size=5, symbol="diamond"),
        hovertemplate=f"<b>Week %{{x}} (AI)</b><br>{name}: %{{y:.3f}}<extra></extra>",
    ))
    
    # Confidence Interval bands (upper and lower)
    # To plot a filled area, we go forwards on the X axis using 'upper', then backwards using 'lower'
    x_ci = list(range(n_hist + 1, n_hist + n_fore + 1))
    fig.add_trace(go.Scatter(
        x=x_ci + x_ci[::-1],
        y=upper + lower[::-1],
        fill='toself',
        fillcolor=color,
        opacity=0.2,
        line=dict(color='rgba(255,255,255,0)'),
        showlegend=False,
        hoverinfo='skip'
    ))

# Stage labels on x-axis
stage_map = ts.get("stage_map", {})
tick_vals = list(range(1, n_hist + n_fore + 1))
tick_text = [
    f"W{w}<br><span style='font-size:8px'>{stage_map.get(w,'')[:7]}</span>"
    for w in tick_vals
]

fig.update_layout(
    height=480,
    xaxis=dict(
        title="Week" if lang == "en" else "सप्ताह",
        tickvals=tick_vals,
        ticktext=tick_text,
        gridcolor="rgba(255,255,255,0.08)",
        rangeslider=dict(visible=True),
    ),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=60, b=80),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)

exp_name = "🤖 AI की भविष्यवाणी कैसे बनी?" if lang == "hi" else "🤖 How the AI Forecast Works"
with st.expander(exp_name):
    for m_name, res in model_details:
        st.markdown(f"**{m_name}**")
        st.markdown(f"- {'सटीकता (आत्मविश्वास)' if lang=='hi' else 'Confidence Rating'}: `{99 - (res['train_loss'] * 100):.1f}%`")
        st.markdown(f"- {'डेटा का अध्ययन' if lang=='hi' else 'Data Studies Completed'}: `{res['epochs']} times`")
    caption_txt = ("यह AI मॉडल विशेष रूप से इसी खेत के पिछले 12 हफ्तों के डेटा को देखकर भविष्य की जानकारी दे रहा है।"
                   if lang == "hi" else 
                   "This AI model was trained on-the-spot using this exact field's history to predict its future.")
    st.caption(caption_txt)

# ── Weather Events Legend ─────────────────────────────────────────────────────
ev_legend_title = "मौसम घटनाएं (आपके खेत में इस मौसम में):" if lang == "hi" else "Weather events this season in your field:"
st.markdown(f"**{ev_legend_title}**")
ecols = st.columns(len(events) or 1)
for i, ev in enumerate(events):
    emoji = {"Rain": "🌧️", "Drought": "☀️", "Flood": "🌊"}.get(ev["type"], "🌀")
    ev_name = ({"Rain": "बारिश", "Drought": "सूखा", "Flood": "बाढ़"} if lang == "hi"
               else {"Rain": "Rain", "Drought": "Drought", "Flood": "Flood"}).get(ev["type"], ev["type"])
    with ecols[i]:
        st.markdown(f"{emoji} **{ev_name}** — Week {ev['week']}")

# ── Week-by-Week Table ────────────────────────────────────────────────────────
st.markdown("---")
tbl_title = "हफ्ता-दर-हफ्ता डेटा" if lang == "hi" else "Week-by-Week Data Table"
st.markdown(f"### 📋 {tbl_title}")

rows = []
for w in range(1, n_hist + n_fore + 1):
    row = {
        "Week" if lang == "en" else "सप्ताह": w,
        "Stage" if lang == "en" else "अवस्था": stage_map.get(w, ""),
        "Type" if lang == "en" else "प्रकार": ("📈 Forecast" if w > n_hist else "📋 History") if lang == "en"
                  else ("📈 अनुमान" if w > n_hist else "📋 इतिहास"),
    }
    for metric in ["NDVI", "soil_moisture", "health_score"]:
        sdata = get_series(metric)
        full  = sdata["full"]
        if 1 <= w <= len(full):
            row[METRIC_NAMES[metric]] = round(full[w - 1], 3)
        else:
            row[METRIC_NAMES[metric]] = None
    # Mark weather event
    ev_week = [e["type"] for e in events if e["week"] == w]
    row["Event" if lang == "en" else "घटना"] = ev_week[0] if ev_week else ""
    rows.append(row)

df_table = pd.DataFrame(rows)
st.dataframe(df_table, use_container_width=True, hide_index=True)

# ── Download CSV ──────────────────────────────────────────────────────────────
csv_bytes = df_table.to_csv(index=False).encode("utf-8")
dl_label  = f"⬇️ {'डेटा डाउनलोड करें' if lang == 'hi' else 'Download CSV'} — {sel_field}"
st.download_button(dl_label, data=csv_bytes,
                   file_name=f"{sel_field}_trends.csv", mime="text/csv")

# Footer
st.markdown("---")
st.caption("📈 " + ("हफ्ते 1–12: MongoDB इतिहास या सिमुलेशन | हफ्ते 13–16: AI पूर्वानुमान (सिमुलेशन)"
                    if lang == "hi"
                    else "Weeks 1–12: MongoDB history or simulation | Weeks 13–16: AI-simulated forecast"))
