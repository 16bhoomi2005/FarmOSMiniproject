import streamlit as st
import data_loader as dl
from datetime import datetime

# Page Config
st.set_page_config(page_title="Actionable Alerts", page_icon="🚨", layout="wide")
dl.apply_custom_css()

# Sidebar
selected_field = dl.get_field_sidebar()

st.title(f"🚨 Actionable Alerts: {selected_field}")
st.markdown("---")

# Load Data
sensor_data = dl.simulate_realtime_data()
sat_features = dl.load_satellite_features()

# Logic to generate Actionable Alerts
alerts_found = []

if sensor_data is not None:
    hum = sensor_data['Humidity']
    temp = sensor_data['Temperature']
    ndvi = sat_features.get('NDVI_mean', 0.5) if sat_features else 0.5
    
    # RICE BLAST
    if hum > 90 and temp < 24:
        alerts_found.append({
            "title": "High Rice Blast Risk",
            "condition": f"Air is very damp ({hum:.1f}%) and night is cool ({temp:.1f}°C)",
            "action": "Spray **Tricyclazole** immediately. This medicine protects against Blast. Repeat after 10 days if it stays cloudy.",
            "urgency": "DANGER",
            "color": "#ff4b4b"
        })
    elif hum > 85:
        alerts_found.append({
            "title": "Moderate Rice Blast Risk",
            "condition": "Air is getting damp. Fungus might grow.",
            "action": "Don't let too much water stand in the field. Watch for brown spots on leaves.",
            "urgency": "WARNING",
            "color": "#ffa500"
        })

    # BACTERIAL LEAF BLIGHT (BLB)
    if hum > 85 and temp > 30:
        alerts_found.append({
            "title": "Bacterial Leaf Blight Alert",
            "condition": "Weather is hot and very damp.",
            "action": "Remove water from field for 2 days. Use less Urea/Nitrogen. Apply **Copper medicine** if you see yellow streaks.",
            "urgency": "HIGH RISK",
            "color": "#ff8c00"
        })

    # TUDTUDA (LEAFHOPPER)
    if ndvi > 0.6 and hum > 80:
        alerts_found.append({
            "title": "Leafhoppers (Tudtuda) Warning",
            "condition": "Crops are very thick and air is damp.",
            "action": "Check the bottom of the rice plants. If you see many insects, apply **Pymetrozine** or **Dinotefuran**.",
            "urgency": "WARNING",
            "color": "#ffa500"
        })

# Display Alerts
if alerts_found:
    for alert in alerts_found:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 8px solid {alert['color']}; padding: 25px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <h3 style="margin-top: 0; color: #1e293b;">{alert['title']}</h3>
                <span style="background-color: {alert['color']}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;">
                    {alert['urgency']}
                </span>
            </div>
            <p style="margin: 10px 0; color: #475569;"><strong>Reason for Alert:</strong> {alert['condition']}</p>
            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px dashed #cbd5e1;">
                <p style="margin: 0; font-size: 1.1rem; color: #0f172a;"><strong>What to do now:</strong></p>
                <p style="margin: 5px 0 0 0;">{alert['action']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✅ **No critical alerts currently.** Your farm environment is stable. Continue regular monitoring.")

st.markdown("---")
st.markdown("### 📞 Local Help Desk")
st.info("Need immediate help? Call the District Agriculture Officer (Bhandara): **+91-XXXX-XXXXXX** or visit the Krishi Vigyan Kendra.")
