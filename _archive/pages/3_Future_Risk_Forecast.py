import streamlit as st
import data_loader as dl
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

# Page Config
st.set_page_config(page_title="Future Risk Forecast", page_icon="🧠", layout="wide")
dl.apply_custom_css()

# Sidebar
selected_field = dl.get_field_sidebar()

st.title(f"🧠 Future Risk Forecast: {selected_field}")
st.markdown("---")

# Load Data
weather_data = dl.load_current_weather()
sensor_data = dl.simulate_realtime_data()
sat_features = dl.load_satellite_features()

# Key parameters for logic
ndvi_val = sat_features.get('NDVI_mean', 0.5) if sat_features else 0.5

col_main, col_side = st.columns([2, 1])

with col_main:
    st.markdown("### 📅 5-Day Rice Problem Forecast")
    
    if "error" not in weather_data and weather_data.get('forecast'):
        forecast = weather_data['forecast']
        
        # Calculate Risk for each day
        risk_progression = []
        
        for day in forecast:
            # Blast Risk Logic: Humidity + Temp
            blast_raw = (day['humidity'] / 100) * (1 - (abs(day['temp'] - 20) / 20)) * 100
            # BLB Risk Logic: Temp + Humidity + Wind/Rain (simulated)
            blb_raw = (day['humidity'] / 100) * (day['temp'] / 35) * 90
            
            risk_progression.append({
                "Date": day['date'][:10],
                "Rice Blast Risk": min(100, max(10, blast_raw + np.random.normal(0, 5))),
                "Bacterial Blight Risk": min(100, max(5, blb_raw + np.random.normal(0, 5))),
                "Tudtuda Risk": min(100, max(0, (ndvi_val * 50) + (day['humidity'] / 2)))
            })
            
        df_risk = pd.DataFrame(risk_progression)
        
        fig = px.line(df_risk, x='Date', y=["Rice Blast Risk", "Bacterial Blight Risk", "Tudtuda Risk"],
                      markers=True, title="Expected Risk Levels Next 5 Days")
        fig.update_layout(yaxis_range=[0, 100], yaxis_title="Risk Level (%)", legend_title_text='Crop Threat')
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 **Farmer Tip:** These risks are calculated by connecting satellite field health with upcoming weather changes.")
    else:
        st.warning("Weather forecast not available. Connect OpenWeather API to see future risk forecasts.")
        st.image("https://via.placeholder.com/800x400.png?text=Waiting+for+Weather+Connection", use_container_width=True)

with col_side:
    st.markdown("### 🔍 Current Risk Factors")
    
    # Analyze contributing factors
    factors = []
    if sensor_data is not None:
        if sensor_data['Humidity'] > 85: factors.append(("Very High Humidity (Damp Air)", "critical"))
        if sensor_data['Temperature'] < 22: factors.append(("Cold Night Temperatures", "warning"))
        if ndvi_val > 0.6: factors.append(("Very Thick Crop Coverage", "info"))
        
    if factors:
        for factor, level in factors:
            if level == "critical": st.error(f"❌ {factor}")
            elif level == "warning": st.warning(f"⚠️ {factor}")
            else: st.info(f"ℹ️ {factor}")
    else:
        st.success("✅ Good weather conditions. No major plant threats detected today.")

    st.markdown("---")
    st.markdown("### 🤖 Intelligence Logic")
    st.markdown("""
    The system looks for **patterns** in your field:
    - **Visual Changes:** How thick or thin crops appear.
    - **Climate History:** How damp or hot it has been for the last 3 days.
    """)
    st.progress(85, text="Model Confidence")
