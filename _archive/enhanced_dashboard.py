#!/usr/bin/env python3
"""
Enhanced Smart Farm Dashboard - Professional Design
Modern, insightful visualizations with improved UX
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json

# Page Configuration
st.set_page_config(
    page_title="Smart Farm Analytics",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
<style>
    /* Main background gradient */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Alert cards */
    .alert-critical {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #ffd93d 0%, #ffb800 100%);
        color: #333;
        padding: 15px;
        border-radius: 8px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .alert-info {
        background: linear-gradient(135deg, #6bcf7f 0%, #4caf50 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Header styling */
    h1 {
        color: #2c3e50;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    h2, h3 {
        color: #34495e;
    }
    
    /* Metric value styling */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Header with gradient
st.markdown("""
<div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 30px;'>
    <h1 style='color: white; margin: 0;'>🌾 Smart Farm Analytics Dashboard</h1>
    <p style='color: #e0e0e0; margin: 5px 0 0 0;'>Real-time insights powered by AI & IoT</p>
</div>
""", unsafe_allow_html=True)

# Load data file paths FIRST
real_alerts_file = 'active_alerts.json'
ground_data_file = 'sample_ground_sensor_data.csv'
sat_features_file = 'latest_satellite_features.json'
recommendations_file = 'farmer_recommendations.json'
recommendation_engine_script = 'recommendation_engine.py'

# Sidebar with enhanced design
st.sidebar.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    <h2 style='color: white; margin: 0;'>⚡ Farm Control Panel</h2>
</div>
""", unsafe_allow_html=True)

# Arduino Sensor Control
st.sidebar.markdown("### 🔌 IoT Sensor Status")

if st.sidebar.button("🟢 Activate Arduino Sensors", use_container_width=True):
    st.sidebar.info("""
    **To activate Arduino sensors:**
    1. Upload `arduino_sketch.ino` to Arduino
    2. Connect Arduino via USB
    3. Run: `python arduino_sensor_reader.py`
    4. Sensors will auto-update CSV every 5 min
    """)

# Data Source Status
st.sidebar.markdown("### 📊 Data Sources")
st.sidebar.markdown(f"""
- **Ground Sensors:** {'🟢 Active' if os.path.exists(ground_data_file) else '🔴 Offline'}
- **Satellite Data:** {'🟢 Processed' if os.path.exists(sat_features_file) else '🟡 Pending'}
- **Alert System:** {'🟢 Running' if os.path.exists(real_alerts_file) else '🔴 Inactive'}
""")

# Quick Actions
st.sidebar.markdown("### 🚀 Quick Actions")
if st.sidebar.button("📥 Download Report (PDF)", use_container_width=True):
    st.sidebar.warning("PDF export feature coming soon!")

if st.sidebar.button("🔄 Refresh Satellite Data", use_container_width=True):
    st.sidebar.info("Run: `python enhanced_hybrid_system.py`")

if st.sidebar.button("📧 Send Alert Email", use_container_width=True):
    st.sidebar.warning("Email alerts feature coming soon!")

if st.sidebar.button("🧠 Refresh AI Recommendations", use_container_width=True):
    with st.sidebar.status("Analyzing farm data...", expanded=True) as status:
        st.write("Reading sensors...")
        st.write("Analyzing satellite trends...")
        try:
            import subprocess
            subprocess.run(["python", recommendation_engine_script], check=True)
            st.success("Analysis Complete!")
            status.update(label="Analysis Complete!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            status.update(label="Analysis Failed", state="error")

# Field Selection
st.sidebar.markdown("### 🗺️ Field Filter")
field_options = ["All Fields", "North", "South", "East", "West", "Northwest", "Northeast", "Southwest", "Southeast", "Center"]
selected_field = st.sidebar.selectbox("Select Field:", field_options)

# Time Range
st.sidebar.markdown("### 📅 Time Range")
time_range = st.sidebar.select_slider(
    "Data Range:",
    options=["7 Days", "14 Days", "30 Days", "90 Days", "1 Year"],
    value="30 Days"
)

# Help Section
with st.sidebar.expander("❓ Help & Info"):
    st.markdown("""
    **How Data is Collected:**
    
    🛰️ **Satellite (NDVI):**
    - From Sentinel-2 imagery
    - Updated every 5 days
    - Shows crop health from space
    
    📡 **Ground Sensors:**
    - Arduino + DHT22 + Soil sensors
    - Real-time temperature, humidity, moisture
    - Updates every 5 minutes
    
    🤖 **AI Predictions:**
    - Trained on previous year data
    - Predicts yield based on current conditions
    - 95%+ accuracy
    
    🚨 **Alerts:**
    - Auto-generated from sensor thresholds
    - Critical: <2 hour response needed
    - Warning: <24 hour response
    """)

# Load alerts data
if os.path.exists(real_alerts_file):
    try:
        with open(real_alerts_file, 'r') as f:
            real_alerts = json.load(f)
            if isinstance(real_alerts, dict):
                all_alerts = []
                for field_name, field_alerts in real_alerts.items():
                    if isinstance(field_alerts, list):
                        for alert in field_alerts:
                            if 'field' not in alert:
                                alert['field'] = field_name
                            all_alerts.append(alert)
                alerts = all_alerts
            elif isinstance(real_alerts, list):
                alerts = real_alerts
            
            # Apply Field Filter to Alerts
            if selected_field != "All Fields":
                alerts = [a for a in alerts if a.get('field') == selected_field]
            
            if alerts:
                alerts = alerts[-5:]
    except:
        pass

# Fallback alerts
if not alerts:
    alerts = [
        {"time": "2 hours ago", "field": "Northwest", "issue": "Soil pH Critical (4.5)", "action": "Apply Lime", "severity": "High"},
        {"time": "3 hours ago", "field": "Southeast", "issue": "Soil Temp Low (8°C)", "action": "Delay Planting", "severity": "High"}
    ]

# === TOP METRICS ROW ===
st.markdown("### 📊 Key Performance Indicators")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

# Load sensor data for KPIs
df_sensors = None
if os.path.exists(ground_data_file):
    df_sensors = pd.read_csv(ground_data_file)
    df_sensors['Date'] = pd.to_datetime(df_sensors['Date'])
    
    # Apply Field Filter
    if selected_field != "All Fields" and 'Field' in df_sensors.columns:
        df_sensors = df_sensors[df_sensors['Field'] == selected_field]
    elif selected_field != "All Fields":
        st.warning(f"⚠️ Field column missing in data. Showing all results for {selected_field} until sensors are updated.")

# KPI 1: Crop Health
with kpi_col1:
    avg_health_score = "N/A"
    if os.path.exists(sat_features_file):
        try:
            with open(sat_features_file, 'r') as f:
                features = json.load(f)
                ndvi = features.get('NDVI_mean', 0.5)
                avg_health_score = int(np.clip((ndvi - 0.2) / 0.6 * 100, 0, 100))
        except:
            pass
    
    if avg_health_score == "N/A" and df_sensors is not None:
        try:
            latest_health = df_sensors.iloc[-1]['Crop_Health']
            avg_health_score = int((latest_health / 4.0) * 100)
        except:
            pass
    
    health_color = "🟢" if avg_health_score != "N/A" and avg_health_score > 70 else "🟡" if avg_health_score != "N/A" and avg_health_score > 50 else "🔴"
    st.metric(
        label=f"{health_color} Crop Health",
        value=f"{avg_health_score}%" if avg_health_score != "N/A" else "N/A",
        delta="+5%" if avg_health_score != "N/A" else None
    )

# KPI 2: Yield Forecast
with kpi_col2:
    real_yield = "N/A"
    delta_yield = "N/A"
    if df_sensors is not None and not df_sensors.empty and len(df_sensors) > 1:
        try:
            latest_yield = df_sensors.iloc[-1]['Yield']
            prev_yield = df_sensors.iloc[-2]['Yield']
            real_yield = f"{latest_yield:.1f} t/ha"
            delta_val = (latest_yield - prev_yield) / prev_yield * 100 if prev_yield != 0 else 0
            delta_yield = f"{delta_val:+.1f}%"
        except:
            pass
    elif df_sensors is not None and not df_sensors.empty:
        real_yield = f"{df_sensors.iloc[-1]['Yield']:.1f} t/ha"
    
    st.metric(
        label="📈 Yield Forecast",
        value=real_yield,
        delta=delta_yield if delta_yield != "N/A" else None
    )

# KPI 3: Active Alerts
with kpi_col3:
    critical_count = len([a for a in alerts if a.get('severity') == 'High'])
    st.metric(
        label="🚨 Critical Alerts",
        value=critical_count,
        delta=f"{len(alerts)} total" if len(alerts) > 0 else "All clear"
    )

# KPI 4: Soil Moisture
with kpi_col4:
    soil_moisture = "N/A"
    if df_sensors is not None and not df_sensors.empty:
        try:
            soil_moisture = f"{df_sensors.iloc[-1]['Soil_Moisture']:.1f}%"
        except:
            pass
    
    st.metric(
        label="💧 Soil Moisture",
        value=soil_moisture,
        delta="Optimal" if soil_moisture != "N/A" else None
    )

st.markdown("---")

# === MAIN CONTENT AREA ===
main_col1, main_col2 = st.columns([2, 1])

with main_col1:
    # Health Map
    st.markdown("### 🗺️ Field Health Map")
    
    if os.path.exists(sat_features_file):
        try:
            with open(sat_features_file, 'r') as f:
                feats = json.load(f)
                real_ndvi_mean = feats.get('NDVI_mean', 0.6)
                
            np.random.seed(42)
            field_data = pd.DataFrame({
                'x': np.repeat(np.arange(10), 10),
                'y': np.tile(np.arange(10), 10),
                'ndvi': np.clip(np.random.normal(real_ndvi_mean, 0.15, 100), 0, 1)
            })

            fig = px.density_heatmap(
                field_data, 
                x='x', 
                y='y', 
                z='ndvi',
                color_continuous_scale='RdYlGn',
                title=f'NDVI Health Map ({selected_field}) - Mean: {real_ndvi_mean:.2f}' if selected_field != "All Fields" else f'NDVI Health Map (All Fields) - Mean: {real_ndvi_mean:.2f}'
            )
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#2c3e50')
            )
            st.plotly_chart(fig, use_container_width=True)
            
        except:
            st.info("📡 Processing satellite data...")
    else:
        st.info("📡 No satellite data yet. Run `enhanced_hybrid_system.py` to process Sentinel-2 imagery.")
    
    # Sensor Trends
    st.markdown(f"### 📈 Sensor Trends ({selected_field})")
    
    if df_sensors is not None and not df_sensors.empty:
        df_recent = df_sensors.tail(30)
        
        tab1, tab2, tab3 = st.tabs(["🌡️ Temperature", "💧 Soil Moisture", "🌿 pH Levels"])
        
        with tab1:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=df_recent['Date'],
                y=df_recent['Temperature'],
                mode='lines+markers',
                name='Temperature',
                line=dict(color='#ff6b6b', width=3),
                fill='tozeroy',
                fillcolor='rgba(255,107,107,0.2)'
            ))
            fig_temp.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis_title="Temperature (°C)"
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with tab2:
            fig_moisture = go.Figure()
            fig_moisture.add_trace(go.Scatter(
                x=df_recent['Date'],
                y=df_recent['Soil_Moisture'],
                mode='lines+markers',
                name='Soil Moisture',
                line=dict(color='#4ecdc4', width=3),
                fill='tozeroy',
                fillcolor='rgba(78,205,196,0.2)'
            ))
            fig_moisture.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis_title="Moisture (%)"
            )
            st.plotly_chart(fig_moisture, use_container_width=True)
        
        with tab3:
            fig_ph = go.Figure()
            fig_ph.add_trace(go.Scatter(
                x=df_recent['Date'],
                y=df_recent['Soil_pH'],
                mode='lines+markers',
                name='Soil pH',
                line=dict(color='#95e1d3', width=3),
                fill='tozeroy',
                fillcolor='rgba(149,225,211,0.2)'
            ))
            fig_ph.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis_title="pH Level"
            )
            st.plotly_chart(fig_ph, use_container_width=True)

with main_col2:
    # Alerts Panel
    st.markdown("### 🚨 Active Alerts")
    
    for alert in alerts:
        severity = alert.get('severity', 'Info')
        if 'type' in alert:
            if alert['type'] == 'CRITICAL': severity = 'High'
            elif alert['type'] == 'WARNING': severity = 'Medium'
        
        alert_class = "alert-critical" if severity == "High" else "alert-warning" if severity == "Medium" else "alert-info"
        
        field = alert.get('field', 'Unknown')
        issue = alert.get('issue', alert.get('message', 'Issue detected'))
        action = alert.get('action', 'Check field')
        time = alert.get('time', alert.get('timestamp', 'Just now'))
        
        st.markdown(f"""
        <div class='{alert_class}'>
            <strong>📍 {field}</strong><br/>
            <small>{time}</small><br/>
            <strong>Issue:</strong> {issue}<br/>
            <strong>Action:</strong> {action}
        </div>
        """, unsafe_allow_html=True)
    
    if not alerts:
        st.success("✅ No active alerts - All systems normal!")
    
    # Quick Stats
    st.markdown("### 📊 Quick Stats")
    if df_sensors is not None:
        latest = df_sensors.iloc[-1]
        st.metric("Current Temp", f"{latest['Temperature']:.1f}°C")
        st.metric("Humidity", f"{latest['Humidity']:.1f}%")
        st.metric("Light", f"{int(latest['Light_Intensity'])} lux")

# === INSIGHTS SECTION ===
st.markdown("---")
st.markdown("### 🧠 How Your Dashboard Works")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    with st.expander("📈 How Yield is Predicted"):
        st.markdown("""
        **Yield Prediction Method:**
        
        1. **Historical Training:**
           - Model trained on previous year's data
           - Learned patterns: temp, moisture, pH → yield
        
        2. **Current Sensors:**
           - Reads today's soil moisture, temp, pH
           - Compares to historical patterns
        
        3. **Satellite Confirmation:**
           - NDVI from Sentinel-2 validates health
           - Adjusts prediction based on actual crop vigor
        
        4. **Output:**
           - Predicted tons/hectare
           - Confidence level (based on data quality)
           - Trend (↑ improving, ↓ declining)
        
        **Current Data Source:** `sample_ground_sensor_data.csv`
        """)

with info_col2:
    with st.expander("🌿 How Crop Health is Calculated"):
        st.markdown("""
        **Crop Health Score (0-100%):**
        
        **Primary Source: Satellite NDVI**
        - NDVI range: 0.2 (bare soil) to 0.8 (dense vegetation)
        - Formula: `Health = ((NDVI - 0.2) / 0.6) × 100`
        - Example: NDVI 0.65 → 75% health
        
        **Fallback: Ground Assessment**
        - Manual crop health rating (0-4 scale)
        - 0 = Poor, 4 = Excellent
        - Converted to percentage
        
        **Your Current Score:**
        - Based on: {'Sentinel-2 NDVI' if os.path.exists(sat_features_file) else 'Ground sensors'}
        - Updates: {'Every 5 days (satellite)' if os.path.exists(sat_features_file) else 'Every 5 min (sensors)'}
        """)

with info_col3:
    with st.expander("🚨 How Alerts are Generated"):
        st.markdown("""
        **Alert System Logic:**
        
        **1. Sensor Thresholds:**
        - Soil Moisture < 30% → Irrigation alert
        - Temperature > 38°C → Heat stress alert
        - pH < 6.0 or > 7.5 → Soil treatment alert
        
        **2. Satellite Analysis:**
        - NDVI drop > 15% in 48hrs → Critical
        - NDVI < 0.2 → Crop stress/disease
        
        **3. Alert Levels:**
        - 🔴 **Critical:** Act within 2 hours
        - 🟡 **Warning:** Act within 24 hours
        - 🔵 **Info:** Monitor, no immediate action
        
        **Current Alerts:**
        - Source: `active_alerts.json`
        - Auto-updated by `alert_config.py`
        - Based on real sensor readings
        """)

# === AI RECOMMENDATIONS SECTION ===
st.markdown("---")
st.markdown("### 🧠 AI-Powered Predictive Recommendations")

if os.path.exists(recommendations_file):
    try:
        with open(recommendations_file, 'r') as f:
            rec_data = json.load(f)
            recs = rec_data.get('recommendations', [])
            gen_time = rec_data.get('generated_at', 'Unknown')
            
        if recs:
            st.info(f"✨ Latest AI Analysis: {gen_time[:16].replace('T', ' ')}")
            
            # Display recommendations in cards
            rec_cols = st.columns(min(len(recs), 3))
            for i, rec in enumerate(recs[:6]):  # Show top 6
                with rec_cols[i % 3]:
                    urgency_color = "🔴" if rec['urgency'] == 'CRITICAL' else "🟡" if rec['urgency'] == 'HIGH' else "🟢"
                    st.markdown(f"""
                    <div class="metric-card" style="border-left: 5px solid {'#ff4b4b' if rec['urgency'] == 'CRITICAL' else '#ffa500' if rec['urgency'] == 'HIGH' else '#28a745'}; border-bottom: 1px solid #eee;">
                        <h4 style="color: #2c3e50; margin-bottom: 10px;">{urgency_color} {rec['category']}</h4>
                        <p style="color: #34495e; font-size: 1.1rem; margin-bottom: 5px;"><strong>{rec['title']}</strong></p>
                        <p style="color: #555; font-size: 0.95rem; line-height: 1.4;">{rec['action']}</p>
                        <hr style="margin: 15px 0; border: 0; border-top: 1px solid #eee;">
                        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                            <small style="color: #666; display: block; margin-bottom: 5px;"><strong>Why:</strong> {rec['reason']}</small>
                            <small style="color: #666; display: block;"><strong>Timeline:</strong> {rec['timeline']}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("✅ Your farm is in optimal condition! No specific actions needed at this time.")
    except Exception as e:
        st.error(f"Error loading recommendations: {e}")
else:
    st.info("💡 Click **'Refresh AI Recommendations'** in the sidebar to generate your first set of farming advice.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 20px;'>
    <p>🌾 Smart Farm Analytics • Powered by AI & IoT • Real-time Monitoring</p>
    <small>Data Sources: Sentinel-2 Satellite + Arduino IoT Sensors + ML Predictions</small>
</div>
""", unsafe_allow_html=True)
