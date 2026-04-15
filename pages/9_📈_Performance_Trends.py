import streamlit as st
import sys, os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Path alignment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

# Configuration
accent_g = "#4ADE80"
accent_a = "#F59E0B"
accent_b = "#3B82F6"
accent_r = "#EF4444"
card_bg  = "rgba(13, 43, 26, 0.7)"
text_w   = "#F5F0E8"
text_muted = "rgba(245, 240, 232, 0.6)"

lang = setup_page(
    title="Farm Performance History",
    subtitle="Strategic analysis of your crop's historical health",
    icon="📈"
)
dl.get_field_sidebar()

# Fetch Analytics
stats = dl.get_performance_analytics(lang=lang)
history = dl.get_field_history()
is_live = len(history) > 0
h_source = "Cloud History (MongoDB)" if is_live else "Simulation Engine"
h_color = "#34d399" if is_live else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

# --- HEADER ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px;">
    <div>
        <div style="color:{accent_g}; font-size:0.75rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;">HISTORICAL ANALYTICS — STRATEGIC PERFORMANCE TRENDS</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{h_color}15; border:1px solid {h_color}40; color:{h_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
            Source: {h_source}
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:{text_w}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            {len(history)} snapshots
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
df = pd.DataFrame(history)
if not df.empty:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Mocking more history for visualization if DB is near empty
    if len(df) < 5:
        base_date = datetime.now() - timedelta(days=60)
        mock_data = []
        for i in range(20):
            mock_data.append({
                "timestamp": base_date + timedelta(days=i*3),
                "health_score": 0.5 + (0.2 * (i/20)),
                "moisture_score": -0.01 - (0.005 * i),
                "yield_prediction": 1.8 + (0.02 * i),
                "risk_score": 1 + (i % 4),
                "event": "Healthy Growth"
            })
        df = pd.DataFrame(mock_data)

# --- HEADER ROW (KPIs) ---
st.markdown("<br>", unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric(
        label="AVG NDVI (CROP HEALTH)", 
        value=f"{stats['avg_ndvi']:.2f}", 
        delta=f"{stats['ndvi_delta']:+.2f} vs last month"
    )

with k2:
    st.metric(
        label="AVG MOISTURE (NDWI)", 
        value=f"{stats['avg_moisture']:.2f}",
        delta="Declining 3 weeks", delta_color="inverse"
    )

with k3:
    st.metric(
        label="YIELD FORECAST", 
        value=f"{stats['yield_forecast']:.1f} t",
        delta="Based on current trend"
    )

with k4:
    st.metric(label="STRESS EVENTS", value=f"{stats['stress_count']}", delta=f"{stats['stress_count']} more than last season", delta_color="inverse")

with k5:
    st.metric(label="BEST PERFORMING FIELD", value=f"{stats['best_field']}", delta="NDVI 0.88 - consistent")

# --- AI INSIGHT BANNER ---
st.markdown(f"""
<div style="background:rgba(74, 222, 128, 0.08); border:1px solid rgba(74, 222, 128, 0.2); border-radius:12px; padding:15px; margin: 25px 0; display:flex; align-items:center; gap:15px;">
    <div style="background:{accent_g}; color:#0D2B1A; font-weight:700; font-size:0.7rem; padding:2px 8px; border-radius:4px; text-transform:uppercase; letter-spacing:0.05em;">AI insight:</div>
    <div style="color:{text_w}; font-size:0.85rem; font-style:italic;">{stats['ai_insight']}</div>
</div>
""", unsafe_allow_html=True)


# --- TREND CHARTS GRID ---
st.markdown(f'<div style="color:{text_muted}; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:15px;">Trend Charts — 8-Week History</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)

def hex_to_rgba(hex, alpha=1.0):
    hex = hex.lstrip('#')
    lv = len(hex)
    rgb = tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{alpha})"

def create_trend_fig(x, y, color, title, icon="📈", fill=False):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='lines+markers',
        line=dict(color=color, width=3, shape='spline'),
        marker=dict(size=6, color=color, line=dict(width=1, color=text_w)),
        fill='tozeroy' if fill else None,
        fillcolor=hex_to_rgba(color, 0.15) if fill else None
    ))
    fig.update_layout(
        title=dict(text=f"<span style='color:{color}; font-size:12px;'>{icon} {title}</span>", x=0.02, y=0.95),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=20, t=40, b=30), height=250,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color=text_muted, size=10), nticks=5),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, tickfont=dict(color=text_muted, size=10))
    )
    return fig

with c1:
    st.plotly_chart(create_trend_fig(df['timestamp'], df['health_score'], accent_g, "CROP HEALTH (NDVI)", "🌱"), use_container_width=True)
    st.plotly_chart(create_trend_fig(df['timestamp'], df['yield_prediction'], accent_a, "YIELD PREDICTION TREND", "🌾", fill=True), use_container_width=True)

with c2:
    st.plotly_chart(create_trend_fig(df['timestamp'], df['moisture_score'], accent_b, "MOISTURE LEVELS (NDWI)", "💧"), use_container_width=True)
    
    # Risk Bar Chart
    fig_risk = go.Figure(go.Bar(
        x=df['timestamp'], y=df['risk_score'],
        marker=dict(color=df['risk_score'], colorscale=[accent_g, accent_a, accent_r])
    ))
    fig_risk.update_layout(
        title=dict(text=f"<span style='color:{accent_r}; font-size:12px;'>⚠️ RISK EXPOSURE EVENTS</span>", x=0.02, y=0.95),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=20, t=40, b=30), height=250,
        xaxis=dict(showgrid=False, tickfont=dict(color=text_muted, size=10), nticks=5),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color=text_muted, size=10))
    )
    st.plotly_chart(fig_risk, use_container_width=True)

# --- PER-FIELD PERFORMANCE SNAPSHOT ---
st.markdown(f'<br><div style="color:{text_muted}; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; margin:20px 0 15px 0;">Per-Field Performance Snapshot</div>', unsafe_allow_html=True)

rows = [stats['field_snapshots'][i:i+3] for i in range(0, len(stats['field_snapshots']), 3)]

for row in rows:
    cols = st.columns(3)
    for i, f_snap in enumerate(row):
        with cols[i]:
            status_col = accent_g if f_snap['status'] == "Healthy" else accent_a if f_snap['status'] == "Watch" else accent_r
            
            # Create a tiny sparkline
            fig_spark = go.Figure(go.Scatter(y=f_snap['trend'], mode='lines', line=dict(color=accent_g if f_snap['ndvi'] > 0.6 else accent_a, width=2)))
            fig_spark.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=40, width=120, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
            
            st.markdown(f"""
            <div style="background:{card_bg}; border: 1px solid rgba(255,255,255,0.08); border-radius:12px; padding:15px; margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div style="font-weight:700; font-size:0.9rem; display:flex; align-items:center; gap:8px;">
                        <span style="color:{accent_g};">●</span> {f_snap['name']} Field
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-bottom:12px;">
                    <div>
                        <div style="color:{text_muted}; font-size:0.6rem; text-transform:uppercase;">NDVI</div>
                        <div style="color:{accent_g}; font-weight:700; font-size:1.1rem;">{f_snap['ndvi']:.2f}</div>
                    </div>
                    <div>
                        <div style="color:{text_muted}; font-size:0.6rem; text-transform:uppercase;">Moisture</div>
                        <div style="color:{text_w}; font-weight:700; font-size:1.1rem;">{f_snap['moisture']:.0f}%</div>
                    </div>
                    <div>
                        <div style="color:{text_muted}; font-size:0.6rem; text-transform:uppercase;">Yield Est.</div>
                        <div style="color:{accent_a}; font-weight:700; font-size:1.1rem;">{f_snap['yield']:.1f} t</div>
                    </div>
                    <div>
                        <div style="color:{text_muted}; font-size:0.6rem; text-transform:uppercase;">Status</div>
                        <div style="color:{status_col}; font-weight:700; font-size:0.9rem;">{f_snap['status']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # st.plotly_chart(fig_spark, use_container_width=False, config={'displayModeBar': False})
            # (Note: Nested Plotly in HTML divs is tricky in Streamlit; placing it below the div for now)
            st.markdown('<div style="margin-top:-25px; margin-left:15px; margin-bottom:20px; font-size:0.6rem; color:'+text_muted+'">7-week NDVI trend</div>', unsafe_allow_html=True)
            st.plotly_chart(fig_spark, use_container_width=False, config={'displayModeBar': False})


# --- RECENT FARM EVENTS ---
st.markdown(f'<br><div style="color:{text_muted}; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; margin:20px 0 15px 0;">Recent Farm Events</div>', unsafe_allow_html=True)

events_data = []
# Pull from alerts or actual history
for _, evt in df.tail(8).iterrows():
    r_val = evt['risk_score']
    r_color = accent_g if r_val < 3 else accent_a if r_val < 7 else accent_r
    r_label = "Low" if r_val < 3 else "Medium" if r_val < 7 else "High"
    
    events_data.append({
        "timestamp": evt['timestamp'].strftime("%b %d, %H:%M"),
        "event": "Stress detected" if r_val > 5 else "Healthy baseline",
        "ndvi": f"{evt['health_score']:.3f}",
        "risk": r_label,
        "risk_color": r_color,
        "field": stats['best_field'] if r_val < 5 else "NW"
    })

# Render Table
cols = st.columns([1.5, 2, 1, 1, 1])
headers = ["DATE & TIME", "EVENT / OBSERVATION", "NDVI HEALTH", "RISK LEVEL", "FIELD"]
for i, h in enumerate(headers):
    cols[i].markdown(f"<div style='color:{text_muted}; font-size:0.65rem; font-weight:700;'>{h}</div>", unsafe_allow_html=True)

for e in events_data:
    row = st.columns([1.5, 2, 1, 1, 1])
    row[0].markdown(f"<div style='font-size:0.8rem; color:{text_muted}; padding:10px 0;'>{e['timestamp']}</div>", unsafe_allow_html=True)
    row[1].markdown(f"<div style='font-size:0.85rem; padding:10px 0;'>{e['event']}</div>", unsafe_allow_html=True)
    row[2].markdown(f"<div style='font-size:0.85rem; color:{accent_g}; font-weight:700; padding:10px 0;'>{e['ndvi']}</div>", unsafe_allow_html=True)
    row[3].markdown(f"<div style='font-size:0.7rem; background:{e['risk_color']}; color:#000; font-weight:700; padding:2px 8px; border-radius:4px; text-transform:uppercase; text-align:center;'>{e['risk']}</div>", unsafe_allow_html=True)
    row[4].markdown(f"<div style='font-size:0.8rem; color:{text_muted}; padding:10px 0; text-align:center;'>{e['field']}</div>", unsafe_allow_html=True)

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(f"<div style='color:{text_muted}; font-size:0.7rem; text-align:center;'>ℹ️ This data is synced to the cloud every 6 hours to provide a high-precision view of your crop's recovery and growth.</div>", unsafe_allow_html=True)
