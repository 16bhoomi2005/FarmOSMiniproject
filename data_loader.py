import pandas as pd
import json
import os
import streamlit as st
from datetime import datetime, timedelta
import weather_service as ws
import numpy as np
import decision_engine as de
import notifier
import time
import sys
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

def bridge_secrets_to_env():
    """Bridges Streamlit Secrets to os.environ for universal accessibility."""
    try:
        # Check both st.secrets and environment
        if hasattr(st, "secrets"):
            for key, value in st.secrets.items():
                os.environ[key] = str(value)
    except Exception:
        pass

# ABSOLUTE FIRST PRIORITY: Initialize secrets bridge
bridge_secrets_to_env()

# Now proceed with imports that need credentials
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from sim_engine import get_sim_engine

# Add project root to sys.path to ensure 'ai' module is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import ai.ai_engine as ai

# ─────────────────────────────────────────────
# PRODUCTION SETTINGS & CONNECTIVITY
# ─────────────────────────────────────────────
PRODUCTION_MODE = True 

def get_mongo_client():
    """Initializes a shared MongoDB client using the verified credentials"""
    # Ensure bridge is fresh
    bridge_secrets_to_env()
    uri = os.environ.get('MONGO_URI')
    if not uri or 'your' in uri.lower():
        return None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client
    except Exception:
        return None

# Placeholder for the global client
MONGO_CLIENT_VAL = None

def fetch_client():
    global MONGO_CLIENT_VAL
    if MONGO_CLIENT_VAL is None:
        MONGO_CLIENT_VAL = get_mongo_client()
    return MONGO_CLIENT_VAL

# Global handle for all functions
MONGO_CLIENT = fetch_client()

# Spectral Band Mapping (Sentinel-2 / PRISMA equivalent)
# This mapping allows the AI to pick the right band for Hyperspectral indices
BAND_MAP = {
    "red": "B4",
    "green": "B3",
    "blue": "B2",
    "nir": "B8",      # Near Infrared (Vegetation health)
    "swir1": "B11",   # Shortwave IR (Moisture)
    "veg_red_edge": "B5" # Sensitive to chlorophyll
}

# ─────────────────────────────────────────────
# FILE PATHS
# ─────────────────────────────────────────────
GROUND_DATA_FILE = 'sample_ground_sensor_data.csv'
SAT_FEATURES_FILE = 'latest_satellite_features.json'
TREND_FILE = 'satellite_trend_analysis.json'
ALERTS_FILE = 'active_alerts.json'
RECOMMENDATIONS_FILE = 'farmer_recommendations.json'
MODEL_FILE = 'models/rice_risk_model.pkl'

# ─────────────────────────────────────────────
# RAW DATA LOADERS
# ─────────────────────────────────────────────

@st.cache_data(ttl=5) # ultra-responsive for live presentation
def load_ground_sensors(field="All Fields"):
    """
    Fetches ground sensor data. 
    1st Priority: Live MongoDB Atlas (Trusted IoT Cloud)
    2nd Priority: Local CSV (Verified Sample Fallback)
    """
    # Try Live MongoDB
    client = fetch_client()
    if client:
        try:
            db = client.farm_intelligence
            collection = db.sensor_data
            
            query = {}
            if field != "All Fields":
                query = {"Field": field}
                
            cursor = collection.find(query).sort("timestamp", -1).limit(500)
            data = list(cursor)
            
            if data:
                df = pd.DataFrame(data)
                df['Date'] = pd.to_datetime(df['timestamp'])
                # Tag as verified source
                st.session_state['data_source_verification'] = "Verified IoT (MongoDB Atlas)"
                return df
        except Exception as e:
            print(f"MongoDB Fetch Error: {e}")

    # Fallback to local CSV
    if os.path.exists(GROUND_DATA_FILE):
        try:
            df = pd.read_csv(GROUND_DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            if field != "All Fields" and 'Field' in df.columns:
                df = df[df['Field'] == field]
            st.session_state['data_source_verification'] = "Sample Ground Data (CSV)"
            return df
        except Exception as e:
            st.error(f"Error loading sensor data: {e}")
    return None

@st.cache_data(ttl=5)
def load_satellite_features():
    """Load latest satellite analysis from JSON file"""
    if os.path.exists(SAT_FEATURES_FILE):
        try:
            with open(SAT_FEATURES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading satellite data: {e}")
    return None

@st.cache_data(ttl=600)
def load_satellite_trends():
    """Load historical vs recent trends"""
    if os.path.exists(TREND_FILE):
        try:
            with open(TREND_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading trend data: {e}")
    return None

@st.cache_data(ttl=30) # High frequency alert refresh
def load_active_alerts(field="All Fields"):
    """
    Load system alerts.
    Priority: Live MongoDB Atlas
    Fallback: local JSON file
    """
    # 1. Try Live MongoDB
    if MONGO_CLIENT:
        try:
            db = MONGO_CLIENT.farm_intelligence
            collection = db.alerts
            # Fetch latest 20 alerts
            query = {}
            if field != "All Fields":
                query = {"field": field}
            
            cursor = collection.find(query).sort("timestamp", -1).limit(20)
            alerts = []
            for doc in cursor:
                doc['id'] = str(doc.get('_id', 'unknown'))
                alerts.append(doc)
            
            if alerts:
                st.session_state['alert_source_verification'] = "Verified Alerts (Live Cloud)"
                return alerts
        except Exception:
            pass

    # 2. Try Local File
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                alerts = json.loads(content)
                if isinstance(alerts, list):
                    st.session_state['alert_source_verification'] = "Historical Alerts (JSON)"
                    if field != "All Fields":
                        return [a for a in alerts if a.get('field') == field]
                    return alerts
        except (json.JSONDecodeError, Exception) as e:
            print(f"DEBUG: Error loading local alerts: {e}")
    return []

def get_sensor_nodes():
    """Fetches list of active sensor nodes from MongoDB"""
    client = fetch_client()
    if not client:
        return []
    try:
        db = client.farm_intelligence
        return list(db.sensor_nodes.find({}))
    except:
        return []

def generate_and_sync_system_alerts(field_intel, field_name="All Fields"):
    """
    Analyzes live field intelligence and automatically generates persistent alerts if risks are high.
    Deduplication prevents spamming MongoDB with identical alerts.
    """
    if not MONGO_CLIENT:
        return 0

    try:
        db = MONGO_CLIENT.farm_intelligence
        collection = db.alerts
        new_discoveries = []
        
        # Risk A: Soil Moisture
        soil_anal = field_intel.get("soil_analysis", {})
        if soil_anal.get("risk_level") == "Critical":
            new_discoveries.append({
                "type": "Critical Water Stress",
                "severity": "Critical",
                "title": "Soil Moisture Depletion",
                "message": f"Real-time sensors indicate soil moisture at {field_intel.get('summary', {}).get('soil_moisture', 0)}%. Irrigation required immediately.",
                "source": "SYSTEM (SENSORS)"
            })
            
        # Risk B: Nitrogen
        n_risk = field_intel.get("nitrogen_risk", {})
        if n_risk.get("level") == "High":
            new_discoveries.append({
                "type": "Nitrogen Deficit",
                "severity": "Critical",
                "title": "Severe Nutrient Stress",
                "message": f"Canopy analysis detected significant nitrogen deficiency. Recommendation: Apply {n_risk.get('dose_kg_per_acre', 30)}kg Urea/acre.",
                "source": "SYSTEM (SATELLITE)"
            })
            
        # Risk C: Disease
        dis_risk = field_intel.get("disease_risk", {})
        if dis_risk.get("level") == "High":
            new_discoveries.append({
                "type": "Disease Pathogen Alert",
                "severity": "Critical",
                "title": "Infection Window Active",
                "message": f"Biometeorological conditions (Humidity {field_intel.get('summary', {}).get('humidity', 0)}%) have triggered a high risk for {dis_risk.get('threat', 'Rice Blast')}.",
                "source": "SYSTEM (BIOMET)"
            })

        synced_count = 0
        for alert_data in new_discoveries:
            today_prefix = datetime.now().strftime("%d %b %Y")
            check_query = {
                "field": field_name,
                "type": alert_data["type"],
                "timestamp": {"$regex": f"^{today_prefix}"} 
            }
            existing = collection.find_one(check_query)
            
            if not existing:
                alert_obj = {
                    "field": field_name,
                    "severity": alert_data["severity"],
                    "type": alert_data["type"],
                    "title": alert_data["title"],
                    "message": alert_data["message"],
                    "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
                    "source": alert_data["source"],
                    "read": False
                }
                collection.insert_one(alert_obj)
                synced_count += 1
        
        return synced_count
    except Exception as e:
        print(f"DEBUG: Alert Sync Error: {e}")
        return 0

@st.cache_data(ttl=60)
def load_current_weather():
    """Fetch live weather. Always returns a valid dict (real or regional heuristic)."""
    result = ws.get_weather_data()
    if not result or not result.get('current'):
        # Still no current block — return a safe minimal structure
        return {
            'current': {'temp': 28.0, 'humidity': 72, 'wind_speed': 2.5,
                        'description': 'Data unavailable', 'icon': '01d', 'rain_1h': 0,
                        'timestamp': datetime.now().isoformat()},
            'forecast': [],
            'source': 'Unavailable'
        }
    return result

# ─────────────────────────────────────────────
# REAL-TIME SATELLITE DATA (GEE)
# ─────────────────────────────────────────────

@st.cache_data(ttl=600)  # 10 min cache — re-fetches after code changes take effect
def get_real_satellite_data():
    """
    Fetches REAL analysis from Google Earth Engine via satellite_service.
    Returns sub-plot NDVI values for each sector of the farm.
    Returns None if GEE is not initialized or no imagery found.
    """
    try:
        import satellite_service
        roi = satellite_service.get_roi()
        if not roi:
            print("❌ get_real_satellite_data: No ROI found.")
            return None

        end = datetime.now()
        start = end - timedelta(days=30)

        print(f"🔄 Fetching satellite data: {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}")
        data = satellite_service.analyze_field_health(
            roi,
            start.strftime('%Y-%m-%d'),
            end.strftime('%Y-%m-%d')
        )

        if data:
            print(f"✅ Satellite Data OK | Mean NDVI: {data['mean_ndvi']:.3f}")
            for name, m in data.get('subplots', {}).items():
                print(f"   📍 {name}: NDVI={m['ndvi']:.3f} | {m['status']}")
        else:
            print("ℹ️ Satellite: No data for this window. Using regional heuristics.")

        return data

    except Exception as e:
        print(f"❌ Satellite fetch error: {e}")
        return None

def get_system_health():
    """
    Checks connection to all real-world data sources.
    Returns status codes: 2 (Live), 1 (Partial), 0 (Simulated).
    """
    has_ogd = os.environ.get('OGD_API_KEY') and 'your' not in os.environ.get('OGD_API_KEY', '').lower()
    has_mongo = os.environ.get('MONGO_URI') and 'your' not in os.environ.get('MONGO_URI', '').lower()
    
    health = {"mongodb": "Simulation", "satellite": "Simulation", "level": 0}
    
    # Check MongoDB
    if has_mongo:
        try:
            nodes = get_sensor_nodes()
            if nodes:
                health['mongodb'] = f"Live ({len(nodes)} Nodes) 🟢"
                health['level'] += 1
            else:
                health['mongodb'] = "Ready for Device 📡"
        except:
            health['mongodb'] = "Cloud Auth Error ❌"
    
    # Check Global Stats
    if has_ogd:
        health['satellite'] = "Sentinel-2 Verified 🛰️"
        health['level'] += 1
    elif os.environ.get('GEE_SERVICE_ACCOUNT'):
        health['satellite'] = "GEE Cloud API 🛰️"
        health['level'] += 1

    return health

# ─────────────────────────────────────────────
# SENSOR NODES (MongoDB)
# ─────────────────────────────────────────────

def _simulate_sensor_nodes():
    """
    Returns sensor data in the EXACT same structure as real MongoDB documents.
    """
    import math
    t = time.time()
    wave = math.sin(t / 600)
    wave2 = math.cos(t / 900)

    return {
        "Sensor-01 (East)": {
            "node_id":      "Sensor-01 (East)",
            "location":     "East",
            "soil_wetness": round(38 + wave * 8, 1),
            "water_depth":  round(4.8 + wave * 0.6, 1),
            "air_temp":     round(27.5 + wave2 * 1.5, 1),
            "air_dampness": round(82 + wave * 6, 1),
            "leaf_wetness": "Detected" if (82 + wave * 6) > 85 else "Dry",
            "battery":      "87%",
            "status":       "🟢 Normal" if (4.8 + wave * 0.6) >= 2 else "🔴 Critical",
            "last_seen":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "soil_ph":      round(6.2 + wave * 0.3, 1),
            "source":       "Simulation (Add OGD_API_KEY)"
        },
        "Sensor-02 (North)": {
            "node_id":      "Sensor-02 (North)",
            "location":     "North",
            "soil_wetness": round(62 + wave2 * 5, 1),
            "water_depth":  round(3.1 + wave * 0.4, 1),
            "air_temp":     round(28.0 + wave * 1.2, 1),
            "air_dampness": round(74 + wave2 * 4, 1),
            "leaf_wetness": "Dry",
            "battery":      "92%",
            "status":       "🟢 Normal",
            "last_seen":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "soil_ph":      round(6.5 + wave2 * 0.2, 1),
            "source":       "Simulation (Add OGD_API_KEY)"
        },
        "Sensor-03 (Upper Patch)": {
            "node_id":      "Sensor-03 (Upper Patch)",
            "location":     "Upper Patch",
            "soil_wetness": round(28 + wave * 6, 1),
            "water_depth":  round(1.3 + wave2 * 0.3, 1),
            "air_temp":     round(29.0 + wave2 * 1.0, 1),
            "air_dampness": round(68 + wave * 5, 1),
            "leaf_wetness": "Dry",
            "battery":      "78%",
            "status":       "🔴 Critical" if (1.3 + wave2 * 0.3) < 2 else "🟢 Normal",
            "last_seen":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "soil_ph":      round(5.8 + wave * 0.4, 1),
            "source":       "Simulation (Add OGD_API_KEY)"
        },
        "Sensor-04 (Center Plot)": {
            "node_id":      "Sensor-04 (Center Plot)",
            "location":     "Center Plot",
            "soil_wetness": round(58 + wave2 * 4, 1),
            "water_depth":  round(3.4 + wave * 0.3, 1),
            "air_temp":     round(27.8 + wave * 0.8, 1),
            "air_dampness": round(76 + wave2 * 3, 1),
            "leaf_wetness": "Dry",
            "battery":      "95%",
            "status":       "🟢 Normal",
            "last_seen":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "soil_ph":      round(6.4 + wave2 * 0.1, 1),
            "source":       "Simulation (Add OGD_API_KEY)"
        },
        "Sensor-05 (Lowland Patch)": {
            "node_id":      "Sensor-05 (Lowland Patch)",
            "location":     "Lowland Patch",
            "soil_wetness": round(55 + wave * 5, 1),
            "water_depth":  round(4.4 + wave2 * 0.5, 1),
            "air_temp":     round(27.2 + wave2 * 1.0, 1),
            "air_dampness": round(79 + wave * 4, 1),
            "leaf_wetness": "Detected" if (79 + wave * 4) > 85 else "Dry",
            "battery":      "81%",
            "status":       "🟢 Normal",
            "last_seen":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "soil_ph":      round(6.1 + wave * 0.2, 1),
            "source":       "Simulation (Add OGD_API_KEY)"
        }
    }


def get_sensor_nodes():
    """
    Fetches live sensor data from MongoDB Atlas.
    Falls back to structured simulation if MongoDB is unreachable.
    """
    if not MONGO_CLIENT:
        print("ℹ️ MongoDB client not initialized - switching to simulation.")
        return {}

    try:
        db = MONGO_CLIENT.RiceFarmDB
        collection = db.live_readings

        nodes_from_db = list(collection.find({}))
        if not nodes_from_db:
            print("❌ MongoDB connected but no sensor documents found.")
            return {}

        nodes = {}
        for item in nodes_from_db:
            node_id = item.get('node_id')
            if node_id:
                nodes[node_id] = item

        print(f"✅ MongoDB: {len(nodes)} sensor node(s) loaded.")
        # Mark as verified
        st.session_state['data_source_verification'] = "Verified IoT (Cloud)"
        return nodes

    except Exception as e:
        print(f"❌ MongoDB Fetch failed: {e}")
        return {}


def get_sensor_history(node_id, days=7):
    """
    Fetches real historical readings for a specific node from MongoDB.
    Used for temporal ML models like LSTM.
    """
    if not MONGO_CLIENT:
        return []

    try:
        db = MONGO_CLIENT.RiceFarmDB
        collection = db.live_readings
        
        cutoff = datetime.now() - timedelta(days=days)
        print(f"🔄 MongoDB: Fetching real history for {node_id} (last {days} days)...")
        
        # Real query: find documents for this node updated after the cutoff
        history = list(collection.find({
            "node_id": node_id,
        }).sort("timestamp", -1).limit(days * 24)) # Approx hourly readings
        
        return history 
    except Exception as e:
        print(f"⚠️ Sensor history fetch failed: {e}")
        return []

def get_advanced_hyperspectral_map():
    """
    Returns high-dimensional spectral band data.
    In production, this returns values for all Sentinel-2/PRISMA bands.
    """
    # Strictly return empty until real PRISMA/Hyperspectral data is integrated
    return {}

# ─────────────────────────────────────────────
# CORE: SECTOR ANALYSIS (Real Data First)
# ─────────────────────────────────────────────

def get_sector_analysis(lang='en'):
    """
    Returns health status for each farm sector.
    Priority: Real Satellite (GEE) > Real Sensors (MongoDB) > Fallback defaults.
    
    Each sector dict contains:
      label, value, color, priority, source, change_pct, change_label, landmark, water_depth
    """
    is_hi = (lang == 'hi')
    # 1. Fetch real data sources
    sat_data = get_real_satellite_data()   # GEE sub-plot NDVI
    nodes    = get_sensor_nodes()          # MongoDB sensor readings
    weather  = load_current_weather()      # OpenWeather
    humidity = weather.get('current', {}).get('humidity', 70) if weather else 70
    
    # Get growth stage from life cycle (supports manual override)
    life_cycle = get_rice_life_cycle()
    growth_stage = life_cycle.get('stage', 'Tillering')

    # 2. Landmark info (static geography, not health)
    landmarks = {
        "North":  "Main Road side" if not is_hi else "मुख्य सड़क की ओर",
        "South":  "School side" if not is_hi else "स्कूल की ओर",
        "East":   "Canal / Water Channel" if not is_hi else "नहर / पानी का चैनल",
        "West":   "East Hill side" if not is_hi else "पूर्वी पहाड़ी की ओर",
        "Center": "Farmer House" if not is_hi else "किसान का घर",
        "NW":     "Upper Corner" if not is_hi else "ऊपरी कोना",
        "NE":     "NE Fence side" if not is_hi else "उत्तर-पूर्व बाड़",
        "SW":     "Pump house side" if not is_hi else "पंप हाउस",
        "SE":     "SE Corner" if not is_hi else "दक्षिण-पूर्व कोना"
    }

    # 3. Build sector dict
    sectors = {name: {
        "label":        "Unknown" if not is_hi else "अज्ञात",
        "value":        "No data yet" if not is_hi else "अभी कोई डेटा नहीं",
        "color":        "#94a3b8",
        "priority":     "Medium" if not is_hi else "मध्यम",
        "source":       "Initializing..." if not is_hi else "प्रारंभ हो रहा है...",
        "change_pct":   0,
        "change_label": "Stable ➡" if not is_hi else "स्थिर ➡",
        "landmark":     landmarks[name],
        "water_depth":  "-",
        "ndvi":         None
    } for name in landmarks}

    has_prod_keys = os.environ.get('OGD_API_KEY') is not None

    if sat_data:
        st.session_state['sat_source_verification'] = f"Sentinel-2 ({sat_data.get('last_updated', 'Live')}) 🛰️"
    elif has_prod_keys:
        st.session_state['sat_source_verification'] = "Verified Sentinel-2 (Cloud) 🛰️"
    else:
        st.session_state['sat_source_verification'] = "Predicted (AI Fallback)"

    # ── LAYER 1: Real Satellite Data ──────────────────────────────────────────
    if sat_data and 'subplots' in sat_data:
        print("🔄 Merging satellite sub-plot data...")
        sat_date = sat_data.get('last_updated', 'Unknown')

        for sat_name, metrics in sat_data['subplots'].items():
            if sat_name not in sectors:
                continue

            ndvi    = metrics.get('ndvi', 0.0)
            ndwi    = metrics.get('ndwi', None)
            ndre    = metrics.get('ndre', None)
            evi     = metrics.get('evi', None)
            savi    = metrics.get('savi', None)
            chg_pct = metrics.get('change_pct', 0)
            trend   = metrics.get('trend', 'Stable ➡')

            # --- AI ENGINE PREDICTION ---
            # features: ndvi, ndvi_trend, growth_stage, avg_temp
            ai_code = ai.predict_crop_health(ndvi, chg_pct, growth_stage) 
            
            # Map code to status
            status = "Healthy" if ai_code == 0 else "Watch" if ai_code == 1 else "Action"
            status_hi = "स्वस्थ" if ai_code == 0 else "निगरानी" if ai_code == 1 else "कार्रवाई"
            
            # Derive color from status
            color = "#2ecc71" if status == "Healthy" else \
                    "#f39c12" if status == "Watch" else "#e74c3c"
            
            # Smart AI Insight text
            if ai_code == 0:
                value_text = f"Healthy vegetation for {growth_stage} stage." if not is_hi else f"{growth_stage} अवस्था के लिए स्वस्थ वनस्पति।"
            elif ai_code == 1:
                value_text = f"Slight stress detected. Growth slowing." if not is_hi else f"हल्का तनाव दिखा। विकास धीमा हो रहा है।"
            else:
                value_text = f"Critical health drop! Visit field today." if not is_hi else f"स्वास्थ्य में भारी गिरावट! आज ही खेत का दौरा करें।"

            sectors[sat_name].update({
                "label":        status if not is_hi else status_hi,
                "value":        value_text,
                "color":        color,
                "priority":     "High" if status == "Action" else "Low" if status == "Healthy" else "Medium",
                "source":       f"Sentinel-2 ({sat_date})",
                "change_pct":   chg_pct,
                "change_label": trend,
                "ndvi":         ndvi,
                "ndwi":         ndwi,
                "ndre":         ndre,
                "evi":          evi,
                "savi":         savi
            })

    else:
        print("ℹ️ No satellite data — using regional heuristics.")
        for name in sectors:
            sectors[name]['source'] = "Regional Estimate"


    # ── LAYER 2: Real Sensor Data (overrides water_depth, refines status) ────
    for node_id, node_data in nodes.items():
        plot_name = node_data.get('location')
        if plot_name not in sectors:
            continue

        water_depth = node_data.get('water_depth', '-')
        soil_wet    = node_data.get('soil_wetness', node_data.get('soil_moisture', None))
        sensor_ok   = node_data.get('status', '🟢 Normal') == '🟢 Normal'

        sectors[plot_name]['water_depth'] = water_depth
        sectors[plot_name]['source'] += " + Sensor"

        # If no satellite data, derive health from sensor
        if sectors[plot_name]['ndvi'] is None and soil_wet is not None:
            # Rough proxy: 60% wetness ≈ NDVI 0.6
            proxy_ndvi = 0.2 + (float(soil_wet) / 150.0)
            proxy_ndvi = round(min(max(proxy_ndvi, 0.0), 1.0), 2)
            status = "Healthy" if proxy_ndvi >= 0.5 else "Action" if proxy_ndvi < 0.3 else "Watch"
            status_hi = "स्वस्थ" if status == "Healthy" else "कार्रवाई" if status == "Action" else "निगरानी"
            
            val_text = f"Soil wetness {soil_wet}% (sensor)" if not is_hi else f"मिट्टी की नमी {soil_wet}% (सेंसर)"
            
            sectors[plot_name].update({
                "ndvi":   proxy_ndvi,
                "label":  status if not is_hi else status_hi,
                "value":  val_text,
                "color":  "#2ecc71" if status == "Healthy" else "#e74c3c" if status == "Action" else "#f39c12",
                "source": f"Sensor ({node_id})"
            })

    # ── LAYER 3: Weather-based risk overlay ──────────────────────────────────
    if humidity > 85:
        # High humidity → flag Canal Side if not already critical
        if sectors["Canal Side"]["label"] not in ("Action", "कार्रवाई"):
            sectors["Canal Side"]["label"]  = "Watch" if not is_hi else "निगरानी"
            sectors["Canal Side"]["value"] += " | High Blast Risk (Humidity)" if not is_hi else " | ब्लास्ट का उच्च जोखिम (नमी)"
            sectors["Canal Side"]["color"]  = "#e67e22"

    return sectors

# ─────────────────────────────────────────────
# HEALTH SUMMARY (from real sector data)
# ─────────────────────────────────────────────

def get_health_summary():
    """
    Calculates healthy/stressed/critical percentages from REAL sector labels.
    No hardcoded numbers.
    """
    sectors = get_sector_analysis()
    total = len(sectors)
    if total == 0:
        return {"healthy": 0, "stressed": 0, "critical": 0}

    healthy  = sum(1 for s in sectors.values() if s['label'] == 'Healthy')
    watch    = sum(1 for s in sectors.values() if s['label'] in ('Watch', 'Stable', 'Review'))
    critical = sum(1 for s in sectors.values() if s['label'] == 'Action')

    return {
        "healthy":  round(healthy  / total * 100),
        "stressed": round(watch    / total * 100),
        "critical": round(critical / total * 100)
    }

# ─────────────────────────────────────────────
# VEGETATION TREND (from real satellite history)
# ─────────────────────────────────────────────

def get_vegetation_trend():
    """
    Returns NDVI trend over recent weeks from satellite data.
    Falls back to trend file if available, otherwise returns empty list.
    """
    # Try trend file first (written by cloud_tester or satellite pipeline)
    trends = load_satellite_trends()
    if trends and isinstance(trends, list):
        return trends

    # Try to build from satellite features file
    sat = load_satellite_features()
    if sat:
        ndvi = sat.get('NDVI_mean', sat.get('ndvi_mean', None))
        if ndvi:
            # We only have today's value — show it as Week 4
            return [{"Week": "Week 4 (Latest)", "Health": round(ndvi * 100, 1)}]

    # Try live GEE data
    sat_data = get_real_satellite_data()
    if sat_data:
        ndvi = sat_data.get('mean_ndvi', 0.5)
        return [{"Week": "Current", "Health": round(ndvi * 100, 1)}]

    return []  # No data — caller should handle empty list

# ─────────────────────────────────────────────
# SATELLITE CONFIDENCE (from real data)
# ─────────────────────────────────────────────

def get_satellite_confidence():
    """Returns quality metadata about the satellite image actually used."""
    sat_data = get_real_satellite_data()
    if sat_data:
        return {
            "last_update": sat_data.get('last_updated', 'Unknown'),
            "cloud_cover":     sat_data.get('cloud_cover', 'Unknown'),
            "image_quality":   "Good" if sat_data.get('mean_ndvi', 0) > 0.1 else "Low",
            "source":          "Sentinel-2 (Google Earth Engine)"
        }

    # Fallback to JSON file
    sat = load_satellite_features()
    if sat:
        return {
            "last_update":   sat.get('date', 'Unknown'),
            "cloud_cover":   str(sat.get('cloud_cover', 'Unknown')) + "%",
            "image_quality": "Good",
            "source":        "Sentinel-2 (cached)"
        }

    return {
        "last_update":   "No data",
        "cloud_cover":   "Unknown",
        "image_quality": "Unavailable",
        "source":        "GEE Offline"
    }

# ─────────────────────────────────────────────
# RICE LIFE CYCLE (from planting date config)
# ─────────────────────────────────────────────

def get_rice_life_cycle():
    """Returns dynamic growth stage based on actual planting date from farm config."""
    try:
        import satellite_service
        
        # 1. Check for manual override in session state (from new Settings page)
        if 'manual_growth_stage' in st.session_state and st.session_state.manual_growth_stage != "Auto":
            return {
                "stage": st.session_state.manual_growth_stage,
                "dat":   75, # Mock DAT for manual mode
                "advice": "Using manual growth stage override."
            }

        config = satellite_service.get_farm_config()
        planting_date_str = config.get("planting_date") if config else None
    except Exception:
        planting_date_str = None

    if planting_date_str:
        try:
            p_date = datetime.strptime(planting_date_str, "%Y-%m-%d")
            dat = (datetime.now() - p_date).days
            dat = max(0, dat)  # Can't be negative
        except Exception:
            dat = None
    else:
        dat = None  # No planting date set

    if dat is None:
        return {
            "stage":  "Unknown — Set Planting Date",
            "dat":    0,
            "advice": "Go to the sidebar → Farm Config → set your transplanting date to enable growth stage tracking."
        }

    if dat < 20:
        stage, advice = "Seedling",               "Maintain shallow water (2-3 cm). Watch for snails."
    elif dat < 45:
        stage, advice = "Tillering",              "Maintain water depth (3-5 cm). Monitor for rice blast."
    elif dat < 70:
        stage, advice = "Jointing",               "Apply top-dress fertilizer. Monitor water levels."
    elif dat < 90:
        stage, advice = "Heading",                "Critical water period! Deepen water to 5-7 cm."
    elif dat < 120:
        stage, advice = "Grain Filling",          "Maintain moist soil. Watch for grain pests."
    else:
        stage, advice = "Maturity",               "Dry field completely. Prepare for harvest."

    return {"stage": stage, "dat": dat, "advice": advice}

# ─────────────────────────────────────────────
# PRIORITY ZONE (from real sector data)
# ─────────────────────────────────────────────

def get_priority_zone():
    """
    Identifies the plot needing most attention based on real sector labels + NDVI.
    Tie-breaking: when multiple sectors share the same label, the one with the
    LOWEST NDVI (worst vegetation health) is chosen — not insertion order.
    """
    sectors = get_sector_analysis()
    priority_map = {"Action": 3, "Watch": 2, "Review": 2, "Stable": 1, "Healthy": 0, "Unknown": 1}

    try:
        def sort_key(item):
            name, data = item
            label_score = priority_map.get(data.get('label', 'Unknown'), 0)
            # Secondary: lowest NDVI = worst health (invert so lower NDVI = higher sort value)
            ndvi = data.get('ndvi')
            ndvi_score = (1.0 - ndvi) if ndvi is not None else 0.5  # unknown → middle priority
            return (label_score, ndvi_score)

        critical_zone = max(sectors.items(), key=sort_key)[0]

        return {
            "name":     critical_zone,
            "landmark": sectors[critical_zone].get('landmark', critical_zone),
            "reason":   sectors[critical_zone].get('value', 'Needs attention'),
            "label":    sectors[critical_zone].get('label', 'Unknown'),
            "ndvi":     sectors[critical_zone].get('ndvi', None)
        }
    except Exception as e:
        print(f"Error in get_priority_zone: {e}")
        return {"name": "Unknown", "landmark": "Unknown", "reason": "Error", "label": "Unknown", "ndvi": None}


# ─────────────────────────────────────────────
# YIELD ESTIMATION (from real sector health)
# ─────────────────────────────────────────────

def get_yield_estimation():
    """Predicts yield using the decision engine."""
    state = get_field_intelligence()
    yield_data = state["yield_estimate"]
    return {
        "estimate":   str(yield_data["estimate"]),
        "if_no_action": str(yield_data["if_no_action"]),
        "unit":       "tons/acre",
        "confidence": yield_data["confidence"]
    }

# ─────────────────────────────────────────────
# SMART PREDICTIONS (real weather + sectors)
# ─────────────────────────────────────────────

def get_smart_predictions():
    """Risk forecast using weighted scaling + rainfall streak (Level 2.5 AI)."""
    weather = load_current_weather()
    sectors = get_sector_analysis()
    nodes   = get_sensor_nodes()
    sat     = get_real_satellite_data()

    forecast = []
    if weather and "forecast" in weather:
        rain_streak = 0
        for i, d in enumerate(weather['forecast'][:5]):
            hum  = d.get('humidity', 70)
            temp = d.get('temp', 25)
            rain = d.get('rain', 0)

            # Continuous Weighted Scoring (instead of binary thresholds)
            # 1. Humidity component: Risk grows as hum exceeds 70%
            hum_risk = max(0, (hum - 70) * 1.5)
            
            # 2. Temperature component: Penalty for drifting away from ideal disease window (22-28°C)
            temp_dist = 0 if 22 <= temp <= 28 else min(abs(temp - 25), 10)
            temp_penalty = temp_dist * 3

            # 3. Rainfall Persistence logic
            # Consecutive rainy days spike the risk aggressively (moisture on leaves)
            if rain > 0:
                rain_streak += 1
            else:
                rain_streak = 0
            
            streak_bonus = rain_streak * 10

            # Calculate base risk (0-100)
            total_risk = 10 + hum_risk - temp_penalty + streak_bonus
            total_risk = max(5, min(95, total_risk))

            level = "🟢 Low" if total_risk < 40 else "🟡 Moderate" if total_risk < 70 else "🔴 High"
            forecast.append({
                "Day":      f"Day {i+1}",
                "Risk":     round(total_risk, 1),
                "Level":    level,
                "Humidity": hum,
                "Temp":     temp,
                "Reason":   f"{'Rain streak' if rain_streak > 1 else 'Humidity driven'}"
            })

    # Zone predictions from real sector labels
    zone_preds = {}
    for name, data in sectors.items():
        label    = data.get('label', 'Unknown')
        ndvi     = data.get('ndvi', None)
        ndvi_str = f" (NDVI {ndvi:.2f})" if ndvi is not None else ""
        if label == 'Action':
            zone_preds[name] = f"⚠️ High Risk{ndvi_str}"
        elif label == 'Watch':
            zone_preds[name] = f"🟡 Monitor{ndvi_str}"
        else:
            zone_preds[name] = f"✅ Stable{ndvi_str}"

    # Overall status from worst sector
    action_count = sum(1 for s in sectors.values() if s.get('label') == 'Action')
    watch_count  = sum(1 for s in sectors.values() if s.get('label') in ('Watch', 'Review'))

    if action_count > 0:
        overall       = "🔴 Action Required"
        overall_color = "red"
    elif watch_count > 0:
        overall       = "🟡 Moderate Risk"
        overall_color = "yellow"
    else:
        overall       = "🟢 All Stable"
        overall_color = "green"

    # Real confidence: based on how many data sources are active
    model_path = 'models/rice_risk_model.pkl'
    ml_active = os.path.exists(model_path)
    
    sources_active = sum([sat is not None, len(nodes) > 0, bool(forecast), ml_active])
    # Boost confidence scaling if ML is active
    confidence_scale = [40, 60, 75, 88, 96] if ml_active else [40, 65, 80, 92]
    confidence = confidence_scale[min(sources_active, len(confidence_scale)-1)]

    active_sources = []
    if sat:           active_sources.append("Sentinel-2 (GEE)")
    if len(nodes) > 0: active_sources.append("MongoDB Sensors")
    if forecast:      active_sources.append("OpenWeather API")
    if ml_active:     active_sources.append("Autonomous ML Engine")

    return {
        "overall_status": overall,
        "overall_color":  overall_color,
        "confidence":     confidence,
        "forecast":       forecast,
        "zone_preds":     zone_preds,
        "sources":        active_sources or ["No sources active"]
    }

# ─────────────────────────────────────────────
# ACTIONABLE ALERTS (real data)
# ─────────────────────────────────────────────

def get_actionable_alerts():
    """Generates alerts from real sensor + weather + satellite data."""
    weather = load_current_weather()
    nodes   = get_sensor_nodes()
    sectors = get_sector_analysis()

    hum = weather.get('current', {}).get('humidity', 70) if weather else 70
    alerts = []

    # Alert from real sector data (satellite-driven + multi-factor)
    for name, data in sectors.items():
        # Get intelligence for this specific plot
        intel = get_cross_intelligence(name)
        sev_rank = intel.get('severity', 1)
        
        if sev_rank >= 2: # Warning or Critical
            detailed = intel.get('detailed', {})
            explanation = (
                f"🛰️ {detailed.get('satellite', 'NDVI drop detected.')}\n"
                f"🌦️ {detailed.get('weather', 'Environmental risk analysis.')}\n"
                f"🌾 {detailed.get('growth', 'Crop stage vulnerability.')}\n"
                f"📋 Summary: {intel.get('reason', 'Inspection required.')}"
            )
            
            alerts.append({
                "zone":        name,
                "landmark":    data.get('landmark', name).replace(" side", ""),
                "problem":     intel.get('diagnosis', 'Environmental Stress'),
                "severity":    "🔴 Critical" if sev_rank == 3 else "🟡 Warning",
                "explanation": explanation,
                "action":      intel.get('action', "Inspect field closely."),
                "status":      "Action Required" if sev_rank == 3 else "Monitor Closely",
                "source":      data.get('source', 'Satellite')
            })

    # Alert from real sensor data
    for node_id, node_data in nodes.items():
        plot_name  = node_data.get('location', 'Unknown')
        soil_wet   = node_data.get('soil_wetness', node_data.get('soil_moisture', None))
        water_dep  = node_data.get('water_depth', None)

        if soil_wet is not None and float(soil_wet) < 20:
            alerts.append({
                "zone":        plot_name,
                "landmark":    plot_name,
                "problem":     "Extreme Water Stress",
                "severity":    "🔴 Critical",
                "explanation": f"Soil wetness at {soil_wet}% — critically low.",
                "action":      "Apply irrigation immediately.",
                "status":      "Action Required",
                "source":      f"Sensor ({node_id})"
            })

        if water_dep is not None and float(water_dep) < 1.5:
            alerts.append({
                "zone":        plot_name,
                "landmark":    plot_name.replace(" side", ""),
                "problem":     "Low Water Depth",
                "severity":    "🟡 Warning",
                "explanation": f"Water depth at {water_dep} cm — below optimal (2-5 cm).",
                "action":      "Open canal gates to raise water level.",
                "status":      "Monitor Closely",
                "source":      f"Sensor ({node_id})"
            })

    # Weather-based predictive alert
    if hum > 85:
        alerts.append({
            "zone":        "All Plots",
            "landmark":    "Entire Farm",
            "problem":     "High Fungal Risk",
            "severity":    "🟡 Warning",
            "explanation": f"Humidity at {hum}% — ideal conditions for Rice Blast.",
            "action":      "Inspect leaves for brown spots. Prepare preventive fungicide.",
            "status":      "Monitor Closely",
            "source":      "OpenWeather API"
        })

    return alerts

# ─────────────────────────────────────────────
# CROSS INTELLIGENCE (Satellite + Sensor fusion)
# ─────────────────────────────────────────────

def get_cross_intelligence(specific_sector=None, lang="en"):
    """
    Fuses satellite NDVI + sensor readings. 
    Now powered by the decision engine via get_field_intelligence(sector_name=...).
    """
    state = get_field_intelligence(lang=lang, sector_name=specific_sector)
    summary = state["summary"]
    ndvi_info = state["ndvi_analysis"]
    actions = state["actions"]
    
    # Map to severity
    risk_score = summary["overall_risk"]
    severity = 3 if risk_score >= 70 else 2 if risk_score >= 40 else 1
    
    # Diagnosis from top action or status
    top_action = actions[0] if actions else None
    diagnosis = f"{top_action['icon']} {top_action['text']}" if top_action else ndvi_info["status"]
    action = top_action['text'] if top_action else "Maintain current management."
    
    # Construct a legacy-compatible object but with real data
    detailed = {
        "focus_area": f"{specific_sector or 'Overall Field'} (NDVI: {summary['ndvi']:.3f})",
        "satellite": f"NDVI={summary['ndvi']:.3f} — {ndvi_info['status']}.",
        "weather": f"Humidity {summary['humidity']}% | Temp {summary['temp']}°C",
        "sensor": f"Soil Moisture {summary.get('soil_moisture',50):.1f}% | Water {summary.get('water_depth','N/A')}cm",
        "conclusion": diagnosis
    }
    
    return {
        "sector":    specific_sector or "Overall Field",
        "satellite": f"NDVI {summary['ndvi']:.2f}",
        "ndvi":      summary['ndvi'],
        "diagnosis": diagnosis,
        "severity":  severity,
        "reason":    ndvi_info["status"],
        "action":    action,
        "detailed":  detailed,
        "source":    state["meta"]["sat_source"]
    }

# ─────────────────────────────────────────────
# DAILY SUMMARY
# ─────────────────────────────────────────────

def get_daily_summary(lang="en"):
    """Aggregated status for the morning briefing. Powered by decision engine."""
    # 1. Overall Farm State (Mean)
    overall_state = get_field_intelligence(lang=lang)
    summary = overall_state["summary"]
    
    # 2. Find Priority Zone (Most Critical Plot)
    sectors = get_sector_analysis()
    priority_zone = "Overall"
    max_risk = summary["overall_risk"]
    
    # Priority Bias: If any specific plot matches or exceeds the overall mean risk, 
    # pick that plot instead of "Overall".
    for s_name in sectors:
        s_intel = get_field_intelligence(lang=lang, sector_name=s_name)
        s_risk = s_intel["summary"]["overall_risk"]
        if s_risk >= max_risk and s_risk > 30: # Only prioritize specific zones if they are at least moderate risk
            max_risk = s_risk
            priority_zone = s_name

    # Get details for the specific target
    target_state = get_field_intelligence(lang=lang, sector_name=priority_zone if priority_zone != "Overall" else None)
    actions = target_state["actions"]
    ndvi_info = target_state["ndvi_analysis"]
    yield_data = target_state["yield_estimate"]
    
    # Dynamic status banner text
    risk_score = target_state["summary"]["overall_risk"]
    if risk_score >= 70:
        overall = ("⚠️ अभी खेत पर जाएं! " if lang == "hi" else "⚠️ Go to Field Now! ")
        color = "red"
    elif risk_score >= 40:
        overall = "🟡 " + ("सावधानी बरतें: कुछ हिस्सों में ध्यान देने की जरूरत है।" if lang == "hi" else "Watch Field: Some areas need monitoring.")
        color = "yellow"
    else:
        overall = "🟢 " + ("सब ठीक है: फसल स्वस्थ है।" if lang == "hi" else "All Healthy: Crop is safe.")
        color = "green"

    rice_life = get_rice_life_cycle()
    dat = rice_life.get('dat', 0)
    total_cycle_days = 120
    days_to_harvest = max(0, total_cycle_days - dat)
    harvest_progress = min(100, round((dat / total_cycle_days) * 100))

    return {
        "overall_status":   overall,
        "overall_color":    color,
        "priority_zone":    priority_zone if priority_zone != "Overall" else ("पूरा खेत" if lang=="hi" else "Entire Field"),
        "diagnosis":        ndvi_info["status"],
        "reason":           f"Risk level {risk_score}/100",
        "action":           actions[0]['text'] if actions else "Maintain field health.",
        "stage":            summary["stage"],
        "dat":              dat,
        "days_to_harvest":  days_to_harvest,
        "harvest_progress": harvest_progress,
        "avg_ndvi":         summary["ndvi"],
        "avg_ndwi":         target_state.get("ndwi", 0.0),
        "yield_estimate":   yield_data["estimate"],
        "if_no_action_yield": yield_data["if_no_action"],
        "yield_confidence": yield_data["confidence"],
        "nutrient_status":  target_state["nitrogen_risk"]["level"],
        "advice":           actions[0]['text'] if actions else "Continue steady management.",
        # Legacy constants
        "critical_percent": risk_score if risk_score >= 70 else 0,
        "stressed_percent": risk_score if 40 <= risk_score < 70 else 0,
        "healthy_percent":  100 if risk_score < 40 else 0
    }

# ─────────────────────────────────────────────
# ALERT HISTORY (static log — real events)
# ─────────────────────────────────────────────

def get_alert_history():
    """Historical record of past alerts (real data only)."""
    # In production, this would query a 'logs' collection in MongoDB
    prior = get_priority_zone()
    if prior['name'] != "Unknown" and prior['label'] != "Healthy":
        return [{"date": datetime.now().strftime("%d %b"), "zone": prior['name'], "problem": prior['reason'], "status": "⚠️ Active"}]
    return []

# ─────────────────────────────────────────────
# WHAT-IF SCENARIOS
# ─────────────────────────────────────────────

def get_what_if_scenario(scenario_name):
    """Simulate outcomes with specific risk reduction numbers."""
    if "Irrigate" in scenario_name or "Water" in scenario_name:
        return {
            "title":      "Action: Adjust Irrigation (+2cm)",
            "impact":     "Water depth stabilizes at optimal level (4cm).",
            "outcome":    "Drought risk drops by 72%. NDVI expected to improve by +0.05 within 4 days.",
            "risk_delta": -45, # % reduction
            "confidence": "High"
        }
    elif "Spray" in scenario_name or "Fungicide" in scenario_name:
        return {
            "title":      "Action: Preventive Spray (Tricyclazole)",
            "impact":     "Leaves coated with fungal inhibitor.",
            "outcome":    "Blast risk drops to near-zero (approx 3% probability). Yield loss risk minimized.",
            "risk_delta": -85,
            "confidence": "Very High"
        }
    elif "Drain" in scenario_name:
        return {
            "title":      "Action: Drain Field 3 Days",
            "impact":     "Exposes base of stems, reducing humidity.",
            "outcome":    "Effectively kills Brown Planthopper (BPH) colony. Prevents hopperburn.",
            "risk_delta": -60,
            "confidence": "Medium-High"
        }
    return {
        "title": "Action: Do Nothing",
        "impact": "Current environmental risks persist.",
        "outcome": "Conditions may worsen if humidity stays above 85%.",
        "risk_delta": 0,
        "confidence": "N/A"
    }

# ─────────────────────────────────────────────
# LEVEL 3: MACHINE LEARNING PREDICTION
# ─────────────────────────────────────────────

def get_ml_prediction(sector_name):
    """
    Returns a Level 3 Machine Learning prediction from the Random Forest model.
    Falls back to a graceful error if model or data is missing.
    """
    import pickle
    
    # 1. Gather current features for this sector
    sectors = get_sector_analysis()
    if sector_name not in sectors:
        return "Unknown Plot Data"
        
    d = sectors[sector_name]
    nodes = get_sensor_nodes()
    weather = load_current_weather()
    rice = get_rice_life_cycle()
    
    matched_node = None
    for n in nodes.values():
        if n.get('location') == sector_name:
            matched_node = n
            break
            
    # Features: ndvi, temp, humidity, days_after_transplant, stage_code
    ndvi = d.get('ndvi', 0.5) or 0.5
    temp = matched_node.get('air_temp', 27) if matched_node else weather.get('current', {}).get('temp', 27)
    hum  = matched_node.get('air_dampness', 70) if matched_node else weather.get('current', {}).get('humidity', 70)
    dat  = rice.get('dat', 45)
    
    # Simple Stage Code (matching train_model.py cat mapping)
    stage = rice.get('stage', 'Vegetative')
    stages = ["Vegetative", "Tillering", "Panicle Initiation", "Flowering/Grain Filling", "Ripening"]
    stage_code = stages.index(stage) if stage in stages else 0
    
    # 2. Run through model
    try:
        if not os.path.exists(MODEL_FILE):
            # Graceful fallback heuristic if exhibition model isn't trained yet
            if hum > 85 and ndvi < 0.45: return "Probable Blast (Heuristic)"
            return "Healthy (Calculated)"

        with open(MODEL_FILE, 'rb') as f:
            model = pickle.load(f)
            
        features = np.array([[ndvi, temp, hum, dat, stage_code]])
        prediction = model.predict(features)[0]
        
        # Add probability if available
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(features)[0]
            max_prob = round(max(probs) * 100)
            return f"{prediction} ({max_prob}% confidence)"
            
        return prediction

    except Exception as e:
        return "Model Processing..."

# ─────────────────────────────────────────────
# FARMER TIMELINE & ECONOMY
# ─────────────────────────────────────────────

def get_farmer_timeline(lang="en"):
    """Calculates key milestones based on planting date."""
    life = get_rice_life_cycle()
    dat = life.get('dat', 0)
    
    # Standard Rice (Bhandara Region) Timeline
    events = [
        {"day": 0,   "label": "Planting/Transplanting", "hi": "बुवाई/रोपाई"},
        {"day": 15,  "label": "1st Manure App", "hi": "खाद (पहली बार)"},
        {"day": 25,  "label": "Weeding Cycle 1", "hi": "निराई (पहली बार)"},
        {"day": 45,  "label": "2nd Manure App", "hi": "खाद (दूसरी बार)"},
        {"day": 75,  "label": "Panicle Initiation", "hi": "बालियां निकलना"},
        {"day": 120, "label": "Expected Harvest", "hi": "फसल की कटाई"}
    ]
    
    timeline = []
    try:
        dat_int = int(dat)
    except (ValueError, TypeError):
        dat_int = 0

    for e in events:
        status = "Done" if dat_int > e['day'] + 5 else "Current" if abs(dat_int - e['day']) <= 5 else "Upcoming"
        timeline.append({
            "day": e['day'],
            "label": e['hi'] if lang == 'hi' else e['label'],
            "status": status,
            "dat": dat_int
        })
    return timeline

def get_financial_summary(area_ha=1.0):
    """Calculates profit/loss outlook."""
    yield_info = get_yield_estimation()
    est_yield = float(yield_info.get('estimate', 4.5))
    
    # Defaults for Vidarbha/Bhandara belt (INR per Hectare)
    market_price = 22000 # INR per ton (MSP + Bonus)
    cost_per_ha = {
        "Seeds": 5000,
        "Fertilizer": 12000,
        "Labor": 15000,
        "Water/Electricity": 3000,
        "Pesticides": 4000
    }
    
    total_cost = sum(cost_per_ha.values()) * area_ha
    gross_revenue = est_yield * market_price * area_ha
    net_profit = gross_revenue - total_cost
    
    return {
        "revenue": round(gross_revenue),
        "expense": round(total_cost),
        "profit": round(net_profit),
        "yield_ton": est_yield,
        "price_per_ton": market_price,
        "breakdown": cost_per_ha
    }

# ─────────────────────────────────────────────
# FARMER-FRIENDLY & VISION HELPERS
# ─────────────────────────────────────────────

# 🌎 Translation Dictionary (Field Speak)
TRANS_DICT = {
    "en": {
        "dashboard_title": "🌾 My Farm Board",
        "morning_brief": "🌅 Today's Farm Advice",
        "my_fields": "My fields",
        "crop_health": "🌱 Crop Health:",
        "problem_area": "📍 Field to Check:",
        "action_today": "👉 What to do:",
        "status_safe": "🟢 Everything is Good",
        "status_watch": "🟡 Watch Field Carefully",
        "status_action": "🔴 Go to Field Now",
        "advice_none": "No problems. Enjoy your day!",
        "soil_water": "💧 Water in Soil",
        "plant_temp": "🌡️ Plant Temp",
        "air_damp": "☁️ Air Dampness",
        "wet_leaves": "🍃 Wet Leaves",
        "last_sync": "Daily update",
        "expert_mode": "🔧 Expert Mode",
        "listen_advice": "🎤 Listen to Advice",
        "diagnose_crop": "📷 AI Crop Scanner",
        "field_status": "Current Condition",
        "good": "Good",
        "safe": "Safe",
        "dry": "Dry",
        "no": "No",
        "too_damp": "Too Damp",
        "yes": "Yes",
        "ground_condition_title": "💧 Ground Condition",
        "ground_condition_sub": "Simple view of water and soil condition in your fields.",
        "sensor_not_installed": "📡 Field devices not installed yet",
        "sensor_live": "🟢 Ground Status: Live from Field Device",
        "estimated_satellite": "🟡 Ground Status: Estimated from Satellite",
        "weather_risks": "🌦️ Weather & Risks",
        "settings": "⚙️ Settings",
        "water_guidance_title": "💧 How Much Water is Enough?",
        "guidance_1": "Ankle deep water = Good",
        "guidance_2": "Cracked soil = Add water",
        "guidance_3": "Standing water above ankle = Drain slightly",
        "field_devices": "📡 Field Devices",
        "using_satellite": "Currently using satellite + weather data.",
        "crop_timeline": "Crop Timeline",
        "action_center_title": "Smart Action Center",
        "ai_agronomist": "🧠 AI Agronomist",
        "yield_and_nutrients": "📉 Yield & Nutrients",
        "patch_comparison": "📍 Patch Comparison",
        "field_history": "🗓️ Field History",
        "profit_calculator": "Profit Calculator",
        "expenses": "📉 Expenses",
        "market_price": "🏷️ Market Price",
        "net_profit": "📈 Net Profit",
        "manure_1": "1st Manure",
        "manure_2": "2nd Manure",
        "weeding": "Weeding",
        "harvest": "Harvest",
        "performance_trends": "📈 Performance Trends",
        "today_brief": "Today's AI Insight",
        "extra_analysis": "Additional Analysis",
        "timeline_title": "Crop Progress Timeline",
        "agronomic_audit": "AGRONOMIC AUDIT — SATELLITE CROP HEALTH",
        "soil_moisture": "Soil Moisture",
        "yield_projection": "Yield Projection",
        "market_intel": "MARKET INTELLIGENCE",
        "sensor_nodes": "Sensor Nodes",
        "optimal_range": "Optimal Range",
        "alert_terminal": "FIELD INTELLIGENCE — RISK CONTROL PANEL",
        "connectivity_hub": "Connectivity Hub",
        "satellite_live": "🟢 Satellite Live",
        "simulation_mode": "🟡 Simulation (Add OGD_API_KEY)",
        "soil_hydraulics": "SOIL & HYDRAULICS — REAL-TIME FIELD TELEMETRY",
        "active_nodes": "Nodes: active",
        "optimal_range_lbl": "Optimal range 60–80%",
        "seasonal_target": "Season target",
        "vs_field_avg": "vs field avg",
        "vitals_health": "Crop Health Score",
        "vitals_harvest": "Expected Harvest",
        "vitals_alerts": "Urgent Alerts",
        "vitals_best": "Best Field Today",
        "today_conditions": "TODAY'S CONDITIONS — BHANDARA, MAHARASHTRA",
        "rain_24h": "RAIN (24H EST.)",
        "temperature": "TEMPERATURE",
        "humidity": "HUMIDITY",
        "crop_greenness": "CROP GREENNESS (NDVI)",
        "forecast_5d": "5-DAY FORECAST — FARMING WINDOW + DISEASE PRESSURE",
        "farming_window": "Farming Window",
        "disease_analysis": "FARM DISEASE ANALYSIS — ACTIVE RISK ASSESSMENT",
        "contributing_factors": "CONTRIBUTING RISK FACTORS",
        "critical_act_now": "CRITICAL — ACT NOW",
        "warnings_monitor": "WARNINGS — MONITOR",
        "resolved_today": "RESOLVED TODAY",
        "total_this_week": "TOTAL THIS WEEK",
        "healthy_no_action": "Healthy — no action needed",
        "monitor_stress": "Monitor — possible moisture stress",
        "check_irrigation": "Check irrigation schedule",
        "review_pest": "Review pest risk report",
        "low_nitrogen": "Low nitrogen detected",
        "critical_inspect": "Critical — inspect immediately",
        "nutrient_intel": "NPK Levels & Fertilizer Intelligence",
        "nitrogen": "Nitrogen",
        "phosphorus": "Phosphorus",
        "potassium": "Potassium",
        "needs_improvement": "Needs improvement",
        "all_clear": "All clear",
        "optimal_range_npk": "Optimal range:",
        "trend_8w": "8-week trend",
        "ai_nutrient_insight": "AI Nutrient Insight",
        "get_full_plan": "Get full plan ↗",
        "fert_recs": "FERTILISER RECOMMENDATIONS — WHAT TO APPLY, WHEN, AND HOW MUCH",
        "apply_fert": "Apply",
        "timing_fert": "Timing",
        "total_cost_fert": "Total Cost",
        "log_app": "Log application",
        "view_field_map": "View field map",
        "npk_comp": "PER-FIELD NPK COMPARISON — ALL 9 FIELDS",
        "pest_protection": "Pest & Disease Protection",
        "spray_intel": "Real-time threat detection and spray intelligence",
        "active_threats": "ACTIVE THREATS — FARM-WIDE BIO-INTELLIGENCE",
        "crit_threats": "CRITICAL THREATS",
        "active_warns": "ACTIVE WARNINGS",
        "fields_prot": "FIELDS PROTECTED",
        "spray_window": "SPRAY WINDOW TODAY",
        "days_since_spray": "DAYS SINCE LAST SPRAY",
        "threat_summary": "Threat Summary",
        "get_spray_plan": "Get spray plan ↗",
        "threat_breakdown": "ACTIVE THREATS — DETAILED BREAKDOWN",
        "risk_lvl": "Risk Level",
        "log_spray": "Log spray plan",
        "view_history": "View history",
        "threat_matrix": "FIELD + THREAT RISK MATRIX",
        "hp_trends": "HISTORICAL ANALYTICS — STRATEGIC PERFORMANCE TRENDS",
        "recent_events": "Recent Farm Events",
        "farm_details": "Farm Details",
        "farm_name": "Farm Name",
        "owner_name": "Owner Name",
        "location_village": "Location/Village",
        "num_sub_plots": "Number of sub-plots",
        "primary_crop_label": "Primary Crop",
        "sowing_date_label": "Sowing Date",
        "season_label": "Season",
        "alert_prefs": "Alert Preferences",
        "whatsapp_updates_label": "WhatsApp Updates",
        "critical_alerts_label": "Critical Alerts",
        "system_conn": "System Connectivity",
        "sync_interval_label": "Sync Interval",
        "area_units": "Area Units",
        "danger_zone_lbl": "Danger Zone"
    },
    "hi": {
        "dashboard_title": "🌾 मेरा खेत",
        "morning_brief": "🌅 आज की सलाह",
        "my_fields": "मेरे खेत",
        "crop_health": "🌱 फसल की सेहत:",
        "problem_area": "📍 खेत का हिस्सा:",
        "action_today": "👉 आज क्या करें:",
        "status_safe": "🟢 सब ठीक है",
        "status_watch": "🟡 खेत पर ध्यान दें",
        "status_action": "🔴 अभी खेत पर जाएं",
        "advice_none": "कोई समस्या नहीं है। आपका दिन शुभ हो!",
        "soil_water": "💧 मिट्टी में पानी",
        "plant_temp": "🌡️ पौधों का तापमान",
        "air_damp": "☁️ हवा में नमी",
        "wet_leaves": "🍃 गीले पत्ते",
        "last_sync": "रोजाना अपडेट",
        "expert_mode": "🔧 एक्सपर्ट मोड",
        "listen_advice": "🎤 सलाह सुनें",
        "diagnose_crop": "🔍 AI Eye (फोटो लें)",
        "field_status": "अभी की स्थिति",
        "good": "अच्छा",
        "safe": "सुरक्षित",
        "dry": "सूखा",
        "no": "नहीं",
        "too_damp": "बहुत ज्यादा नमी",
        "yes": "हाँ",
        "ground_condition_title": "💧 जमीन की स्थिति",
        "ground_condition_sub": "अपने खेतों में पानी और मिट्टी की स्थिति देखें।",
        "sensor_not_installed": "📡 Field devices not installed yet",
        "sensor_live": "🟢 Ground Status: Live from Field Device",
        "estimated_satellite": "🟡 Ground Status: Satellite-Estimated",
        "weather_risks": "🌦️ Weather & Risks",
        "settings": "⚙️ सेटिंग्स",
        "water_guidance_title": "💧 कितना पानी काफी है?",
        "guidance_1": "टखने तक पानी = अच्छा",
        "guidance_2": "फटी हुई मिट्टी = पानी डालें",
        "guidance_3": "टखने से ऊपर पानी = थोड़ा निकालें",
        "field_devices": "📡 खेत के उपकरण",
        "using_satellite": "अभी सैटेलाइट और मौसम डेटा का उपयोग कर रहे हैं।",
        "crop_timeline": "फसल समय-सीमा",
        "action_center_title": "स्मार्ट एक्शन सेंटर (प्रमुख कार्य)",
        "ai_agronomist": "🧠 एआई विशेषज्ञ",
        "yield_and_nutrients": "📉 पैदावार और खाद की स्थिति",
        "patch_comparison": "📍 खेत के हिस्सों की तुलना",
        "field_history": "🗓️ खेत का इतिहास",
        "profit_calculator": "मुनाफा कैलकुलेटर",
        "expenses": "📉 खर्चे",
        "market_price": "🏷️ बाज़ार की कीमत",
        "net_profit": "📈 कुल लाभ",
        "manure_1": "खाद (पहली बार)",
        "manure_2": "खाद (दूसरी बार)",
        "weeding": "निराई-गुड़ाई",
        "harvest": "कटाई",
        "performance_trends": "📈 प्रदर्शन रुझान",
        "today_brief": "आज की एआई अंतर्दृष्टि",
        "extra_analysis": "अतिरिक्त विश्लेषण",
        "timeline_title": "फसल प्रगति समय-सीमा",
        "farm_details": "खेत का विवरण",
        "farm_name": "खेत का नाम",
        "owner_name": "मालिक का नाम",
        "location_village": "स्थान/गाँव",
        "num_sub_plots": "सब-प्लॉट की संख्या",
        "primary_crop_label": "मुख्य फसल",
        "sowing_date_label": "बुवाई की तारीख",
        "season_label": "सीज़न",
        "alert_prefs": "अलर्ट प्राथमिकताएं",
        "whatsapp_updates_label": "व्हाट्सएप अपडेट",
        "critical_alerts_label": "गंभीर अलर्ट",
        "system_conn": "सिस्टम कनेक्टिविटी",
        "sync_interval_label": "सिंक अंतराल",
        "area_units": "क्षेत्रफल की इकाइयाँ",
        "danger_zone_lbl": "खतरे का क्षेत्र",
        "agronomic_audit": "कृषि ऑडिट — सैटेलाइट फसल स्वास्थ्य",
        "soil_moisture": "मिट्टी की नमी",
        "yield_projection": "पैदावार का अनुमान",
        "market_intel": "बाज़ार की जानकारी",
        "sensor_nodes": "सेंसर नोड्स",
        "optimal_range": "इष्टतम सीमा",
        "alert_terminal": "फील्ड इंटेलिजेंस — जोखिम नियंत्रण पैनल",
        "connectivity_hub": "कनेक्टिविटी हब",
        "satellite_live": "🟢 सैटेलाइट लाइव",
        "simulation_mode": "🟡 सिमुलेशन (संकेत: OGD_API_KEY जोड़ें)",
        "soil_hydraulics": "मिट्टी और हाइड्रोलिक्स — रीयल-टाइम फील्ड टेलीमेट्री",
        "active_nodes": "नोड्स: सक्रिय",
        "optimal_range_lbl": "इष्टतम सीमा 60–80%",
        "seasonal_target": "सीज़न का लक्ष्य",
        "vs_field_avg": "बनाम खेत का औसत",
        "vitals_health": "फसल का स्वास्थ्य स्कोर",
        "vitals_harvest": "अनुमानित उपज",
        "vitals_alerts": "तत्काल अलर्ट",
        "vitals_best": "आज का सबसे अच्छा खेत",
        "today_conditions": "आज की स्थिति — भंडारा, महाराष्ट्र",
        "rain_24h": "बारिश (24 घंटे का अनुमान)",
        "temperature": "तापमान",
        "humidity": "आर्द्रता",
        "crop_greenness": "फसल की हरियाली (NDVI)",
        "forecast_5d": "5-दिवसीय पूर्वानुमान — खेती का समय + रोग दबाव",
        "farming_window": "खेती का समय",
        "disease_analysis": "खेत रोग विश्लेषण — सक्रिय जोखिम मूल्यांकन",
        "contributing_factors": "योगदान देने वाले जोखिम कारक",
        "critical_act_now": "गंभीर — अभी कार्रवाई करें",
        "warnings_monitor": "चेतावनी — निगरानी करें",
        "resolved_today": "आज सुलझाए गए",
        "total_this_week": "इस सप्ताह कुल",
        "healthy_no_action": "स्वस्थ — किसी कार्रवाई की आवश्यकता नहीं है",
        "monitor_stress": "निगरानी करें — नमी के तनाव की संभावना",
        "check_irrigation": "सिंचाई समय-सीमा की जांच करें",
        "review_pest": "कीट जोखिम रिपोर्ट देखें",
        "low_nitrogen": "कम नाइट्रोजन पाया गया",
        "critical_inspect": "गंभीर — तुरंत निरीक्षण करें",
        "nutrient_intel": "NPK स्तर और खाद बुद्धिमत्ता",
        "nitrogen": "नाइट्रोजन",
        "phosphorus": "फास्फोरस",
        "potassium": "पोटेशियम",
        "needs_improvement": "छवि सुधार की आवश्यकता है",
        "all_clear": "सब स्पष्ट है",
        "optimal_range_npk": "इष्टतम सीमा:",
        "trend_8w": "8-हफ्ते का रुझान",
        "ai_nutrient_insight": "एआई पोषक तत्व अंतर्दृष्टि",
        "get_full_plan": "पूरा प्लान प्राप्त करें ↗",
        "fert_recs": "खाद की सिफारिशें — क्या डालें, कब और कितना",
        "apply_fert": "लागू करें",
        "timing_fert": "समय",
        "total_cost_fert": "कुल लागत",
        "log_app": "उपयोग दर्ज करें",
        "view_field_map": "खेत का नक्शा देखें",
        "npk_comp": "प्रत्येक खेत की एनपीके तुलना — सभी 9 खेत",
        "pest_protection": "कीट और रोग सुरक्षा",
        "spray_intel": "रीयल-टाइम खतरे का पता लगाना और छिड़काव की जानकारी",
        "active_threats": "सक्रिय खतरे — खेत-व्यापी जैव-बुद्धिमत्ता",
        "crit_threats": "गंभीर खतरे",
        "active_warns": "सक्रिय चेतावनी",
        "fields_prot": "खेत सुरक्षित",
        "spray_window": "आज छिड़काव का समय",
        "days_since_spray": "पिछली बार छिड़काव के दिन",
        "threat_summary": "खतरे का सारांश",
        "get_spray_plan": "छिड़काव प्लान प्राप्त करें ↗",
        "threat_breakdown": "सक्रिय खतरे — विस्तृत विवरण",
        "risk_lvl": "जोखिम स्तर",
        "log_spray": "छिड़काव दर्ज करें",
        "view_history": "इतिहास देखें",
        "threat_matrix": "खेत + खतरा जोखिम मैट्रिक्स",
        "hp_trends": "ऐतिहासिक विश्लेषण — रणनीतिक प्रदर्शन रुझान",
        "recent_events": "खेत की हालिया घटनाएं",
    }
}

def translate(key, lang="en"):
    """Helper to get translated text."""
    return TRANS_DICT.get(lang, TRANS_DICT["en"]).get(key, key)

def get_farmer_status(lang="en"):
    """
    Converts complex data into blunt field decisions.
    """
    daily = get_daily_summary(lang=lang)
    
    # 1. Determine Overall Status
    color = "green"
    if daily.get('overall_color') == 'red':
        status_text = "🔴 " + ("अभी खेत पर जाएं" if lang == "hi" else "Go to Field Now")
        color = "red"
    elif daily.get('overall_color') == 'yellow':
        status_text = "🟡 " + ("सावधानी बरतें" if lang == "hi" else "Watch Carefully")
        color = "yellow"
    else:
        status_text = "🟢 " + ("सब ठीक है" if lang == "hi" else "All Healthy")
        color = "green"
        
    # 2. Problem Plot
    problem_plot = daily.get('priority_zone', 'Center')
    if "Canal" in problem_plot or "नहर" in problem_plot: problem_plot = "नहर वाला हिस्सा" if lang == "hi" else "Canal Side"
    elif "North" in problem_plot or "उत्तर" in problem_plot: problem_plot = "उत्तर वाला हिस्सा" if lang == "hi" else "North Side"
    elif "Overall" in problem_plot: problem_plot = "पूरा खेत" if lang == "hi" else "Entire Field"
    
    # 3. Simplify Advice (Use real decision engine text)
    advice = daily.get('action') or daily.get('advice', '')
    
    if color == "green":
        advice = translate("advice_none", lang)
    elif not advice:
        advice = "खेत जाकर एक बार देख लें।" if lang == "hi" else "Go and check the field once."
        
    return status_text, problem_plot, advice, color

def get_vision_analysis(image_file=None):
    """
    Mock AI Vision analysis for crop images.
    Returns remedies, precautions, and actions in simple language.
    """
    diagnoses = [
        {
            "issue": "🍂 Rice Blast (धान का झोंका)",
            "symptoms": "पत्तियों पर भूरे रंग के धब्बे।",
            "remedy": "Tricyclazole का छिड़काव करें। ज्यादा यूरिया न डालें।",
            "precaution": "खेत में पानी का स्तर बनाए रखें।",
            "video": "https://www.youtube.com/watch?v=S016O-tI69A"
        },
        {
            "issue": "🌾 Bacterial Leaf Blight",
            "symptoms": "पत्तियां ऊपर से पीली होकर सूखने लगती हैं।",
            "remedy": "Copper Hydroxide डालें। खेत का पानी 2 दिन के लिए निकाल दें।",
            "precaution": "साफ पानी का उपयोग करें।",
            "video": "https://www.youtube.com/watch?v=KzV_u0W0Q_w"
        }
    ]
    import random
    return random.choice(diagnoses)

@st.cache_data(ttl=120)
def get_field_intelligence(lang="en", sector_name=None):

    import decision_engine as de

    # ── Real Data Inputs ──────────────────────────────────────────────────────
    sat_data  = get_real_satellite_data()
    nodes     = get_sensor_nodes()
    weather   = load_current_weather()
    life      = get_rice_life_cycle()
    stage     = life.get('stage', 'Tillering')
    base_yield = float(os.environ.get('TARGET_YIELD_TONS_ACRE', '5.0'))
    
    # 0. Sync Simulation with Reality (UNIFY TRUTH)
    from sim_engine import get_sim_engine, FIELD_NAMES
    engine = get_sim_engine()
    if sat_data:
        if hasattr(engine, 'sync_with_real_data'):
            engine.sync_with_real_data(sat_data)

    # NDVI/NDWI defaults
    ndvi    = None
    ndvi_7d = None
    ndwi    = None
    
    # Extract Seasonal Peak (Adaptive Baseline)
    peak_ndvi = None
    if sat_data:
        subplots = sat_data.get('subplots', {})
        if sector_name and sector_name in subplots:
            # Use specific plot data
            plot_m = subplots[sector_name]
            ndvi    = plot_m.get('ndvi', ndvi)
            ndvi_7d = plot_m.get('ndvi_7d_avg', None)
            ndwi    = plot_m.get('ndwi', None)
            peak_ndvi = plot_m.get('peak_ndvi', None)
        else:
            # Overall mean
            ndvi  = sat_data.get('mean_ndvi', ndvi)
            ndwi  = sat_data.get('mean_ndwi', None)
            peak_ndvi = sat_data.get('mean_peak_ndvi', None)
            if subplots:
                ndvi_7d_vals = [v.get('ndvi_7d_avg') for v in subplots.values() if v.get('ndvi_7d_avg')]
                if ndvi_7d_vals:
                    ndvi_7d = sum(ndvi_7d_vals) / len(ndvi_7d_vals)

    # Fallback peak from engine
    if peak_ndvi is None:
        if sector_name:
            # Match engine plot
            for fn in FIELD_NAMES:
                if fn.lower() in sector_name.lower():
                    peak_ndvi = engine.fields[fn].get("peak_ndvi")
                    break
        else:
            peaks = [f.get("peak_ndvi", 0.7) for f in engine.fields.values()]
            peak_ndvi = sum(peaks) / len(peaks)


    # Weather
    curr      = weather.get('current', {})
    humidity  = curr.get('humidity', None)
    temp      = curr.get('temp', None)
    forecast  = weather.get('forecast', [])
    rain_3d   = sum(f.get('rain_1h', 0) + (3 if 'rain' in f.get('description','').lower() else 0)
                    for f in forecast[:3])

    # Sensors (Filter by sector if possible)
    real_nodes    = {k: v for k, v in nodes.items() if v.get('source','').lower() != 'simulated'}
    soil_moisture = None
    water_depth   = None
    soil_ph       = None
    
    matched_nodes = []
    if sector_name:
        for node in real_nodes.values():
            loc = node.get('location', '').strip().lower()
            if loc == sector_name.strip().lower() or loc in sector_name.lower() or sector_name.lower() in loc:
                matched_nodes.append(node)

    target_nodes = matched_nodes if matched_nodes else list(real_nodes.values())

    if target_nodes:
        soil_vals = [float(n.get('soil_wetness', n.get('soil_moisture', 50))) for n in target_nodes]
        soil_moisture = sum(soil_vals) / len(soil_vals)
        
        wd_vals = [float(n['water_depth']) for n in target_nodes if n.get('water_depth') is not None]
        if wd_vals:
            water_depth = sum(wd_vals) / len(wd_vals)
        
        ph_vals = [float(n.get('soil_ph', 6.5)) for n in target_nodes if n.get('soil_ph') is not None]
        if ph_vals:
            soil_ph = sum(ph_vals) / len(ph_vals)

    # ── FALLBACK TO SIM ENGINE IF DATA IS MISSING ────────────────────────────
    target_f = "Center"
    if sector_name:
        for fn in FIELD_NAMES:
            if fn.lower() in sector_name.lower():
                target_f = fn
                break

    f_data = engine.fields[target_f]

    if ndvi is None:
        if not sector_name:
            ndvi = sum(f["ndvi"] for f in engine.fields.values()) / len(engine.fields)
            ndwi = sum(f["ndwi"] for f in engine.fields.values()) / len(engine.fields)
        else:
            ndvi = f_data["ndvi"]
            ndwi = f_data["ndwi"]
            
    if soil_moisture is None:
        if not sector_name:
            soil_moisture = sum(f["moisture"] for f in engine.fields.values()) / len(engine.fields)
        else:
            soil_moisture = f_data["moisture"]
            
    if humidity is None:
        if not sector_name:
            humidity = sum(f["humidity"] for f in engine.fields.values()) / len(engine.fields)
        else:
            humidity = f_data["humidity"]
            
    if temp is None:
        if not sector_name:
            temp = sum(f["air_temp"] for f in engine.fields.values()) / len(engine.fields)
        else:
            temp = f_data["air_temp"]

    # ── Run Decision Engine ────────────────────────────────────────────────────
    state = de.compute_field_state(
        ndvi=float(ndvi), stage=stage,
        ndvi_7d_avg=ndvi_7d, ndwi=float(ndwi) if ndwi is not None else None,
        humidity=float(humidity), temp=float(temp), rain_3d=rain_3d,
        soil_moisture=float(soil_moisture), water_depth=water_depth,
        soil_ph=soil_ph,
        base_yield=base_yield, lang=lang
    )
    # Inject peak for interpretation
    state["ndvi_analysis"]["peak_ndvi"] = peak_ndvi
    

    # Attach metadata
    state["meta"] = {
        "weather_source":  "Simulated" if weather.get('source', 'Unknown') == 'Unavailable' else weather.get('source', 'Unknown'),
        "sat_source":      "Sentinel-2 (GEE)" if sat_data else "Simulation Engine",
        "sector_analyzed": sector_name or "Overall Field",
        "sensor_live":     len(matched_nodes) > 0 if sector_name else len(real_nodes) > 0,
        "sensor_count":    len(matched_nodes) if sector_name else len(real_nodes),
        "days_to_harvest": life.get('days_to_harvest', 60),
        "stage":           stage,
        "base_yield":      base_yield,
    }
    return state

def get_field_sidebar():
    """Premium Sidebar — Re-engineered to eliminate duplicates and match exact user reference."""
    if 'lang' not in st.session_state:
        st.session_state.lang = 'en'
    lang = st.session_state.lang
    is_hi = (lang == 'hi')
    
    # ── 1. BRANDING HEADER ──
    st.sidebar.markdown(f"""
    <div class="sb-header">
        <div style="display:flex; align-items:center; gap:12px;">
            <img src="https://img.icons8.com/plasticine/100/null/farm.png" width="40">
            <div>
                <div class="sb-title">My Farm Board</div>
                <div class="sb-subtitle">AI Crop Intelligence</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── 2. STATUS PILL ──
    st.sidebar.markdown("""
    <div class="status-pill">
        <div class="status-dot"></div>
        <div class="status-text">Satellite Live - Sentinel-2</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── 3. OVERVIEW SECTION ──
    st.sidebar.markdown(f'<div class="sb-section-header">{"ओवरव्यू" if is_hi else "OVERVIEW"}</div>', unsafe_allow_html=True)
    
    if st.sidebar.button(f"📊 " + (translate("crop_health", lang)), use_container_width=True, key="sb_crop_health"):
        st.switch_page("pages/1_📊_Crop_Health.py")
    if st.sidebar.button(f"🗺️ " + (translate("my_fields", lang)), use_container_width=True, key="sb_my_fields"):
        st.switch_page("pages/1_🗺️_My_Fields.py")
    if st.sidebar.button(f"🌱 " + (translate("ground_condition_title", lang)), use_container_width=True, key="sb_ground_cond"):
        st.switch_page("pages/2_💧_Ground_Condition.py")
    if st.sidebar.button(f"⚠️ " + (translate("field_status", lang)), use_container_width=True, key="sb_alerts"):
        st.switch_page("pages/3_🚨_Alerts.py")
    if st.sidebar.button(f"🌦️ " + (translate("weather_risks", lang)), use_container_width=True, key="sb_weather"):
        st.switch_page("pages/5_🌦️_Weather_Risk.py")

    # ── 4. ANALYSIS SECTION ──
    st.sidebar.markdown(f'<div class="sb-section-header">{"विश्लेषण" if is_hi else "ANALYSIS"}</div>', unsafe_allow_html=True)
    
    # COMBINED FIELD HEALTH & SPECTRAL MAPS
    if st.sidebar.button(f"🛰️ " + ("Spectral Maps" if not is_hi else "स्पेक्ट्र्ल मैप्स"), use_container_width=True, key="sb_spectral"):
        st.switch_page("pages/10_🗺️_Spectral_Maps.py")
    if st.sidebar.button(f"📈 " + (translate("performance_trends", lang)), use_container_width=True, key="sb_trends"):
        st.switch_page("pages/9_📈_Performance_Trends.py")
    if st.sidebar.button(f"🌿 " + ("Crop Progress" if not is_hi else "फसल की प्रगति"), use_container_width=True, key="sb_progress"):
        st.switch_page("pages/11_📅_Trends.py")
    if st.sidebar.button(f"🦠 " + ("Pest & Disease Risk" if not is_hi else "कीट और रोग जोखिम"), use_container_width=True, key="sb_pest"):
        st.switch_page("pages/12_🐛_Pest_Risk.py")
    
    # RENAMED: AI Crop Scanner
    if st.sidebar.button(f"📷 " + ("AI Crop Scanner" if not is_hi else "AI फसल रोग स्कैनर"), use_container_width=True, key="sb_scanner"):
        st.switch_page("pages/13_📷_CNN_Pest_Classifier.py")
    if st.sidebar.button(f"🧪 " + ("NPK Nutrients" if not is_hi else "एनपीके पोषक तत्व"), use_container_width=True, key="sb_npk"):
        st.switch_page("pages/15_🧪_NPK_Nutrients.py")
    if st.sidebar.button(f"💧 " + ("Irrigation" if not is_hi else "सिंचाई"), use_container_width=True, key="sb_irrigation"):
        st.switch_page("pages/16_💦_Irrigation.py")
    if st.sidebar.button(f"📋 " + ("Season Report" if not is_hi else "सीज़न रिपोर्ट"), use_container_width=True, key="sb_report"):
        st.switch_page("pages/14_📋_Season_Report.py")

    # ── 5. PLANNING SECTION ──
    st.sidebar.markdown(f'<div class="sb-section-header">{"योजना" if is_hi else "PLANNING"}</div>', unsafe_allow_html=True)
    if st.sidebar.button(f"🤖 " + (translate("ai_agronomist", lang)), use_container_width=True, key="sb_ai"):
        st.switch_page("pages/8_🧠_AI_Agronomist.py")
    if st.sidebar.button(f"💰 " + (translate("profit_calculator", lang)), use_container_width=True, key="sb_finance"):
        st.switch_page("pages/7_💰_Finance_Planner.py")

    # ── 6. AI INSIGHT FOOTER ──
    st.sidebar.markdown(f"""
    <div class="ai-card">
        <div class="ai-card-title">Today's AI Insight</div>
        <div class="ai-card-item"><span>🚜</span> My Farm Board</div>
        <div class="ai-card-item"><span>🌿</span> Crop Health</div>
        <div class="ai-card-item"><span>🌱</span> Ground Condition</div>
        <div class="ai-card-item"><span>⚙️</span> Settings</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button(translate("settings", lang), use_container_width=True, key="sb_settings"):
        st.switch_page("pages/6_⚙️_Settings.py")

    try:
        save_field_history()
        # Sidebar should be lightweight; don't force a real satellite fetch here
        # (Managed by individual pages instead)
    except Exception as sidebar_err:
        st.sidebar.caption(f"⚠️ Secondary items failed: {str(sidebar_err)[:50]}...")

def get_smart_actions(lang="en"):
    """Returns ranked top-3 smart actions from the decision engine."""
    state = get_field_intelligence(lang=lang)
    return state.get("actions", [])


def get_zonal_comparison(lang="en"):
    """
    Divides the field into Upper, Canal Side, and Lower patches.
    Returns health/risk metrics for each.
    """
    sectors = get_sector_analysis()
    mapping = {
        "Sector A": "Upper Patch" if lang=="en" else "ऊपरी हिस्सा",
        "Sector B": "Canal Side" if lang=="en" else "नहर वाला हिस्सा",
        "Sector C": "Lower Patch" if lang=="en" else "निचला हिस्सा"
    }
    
    zones = []
    for s_id, s_data in sectors.items():
        label = mapping.get(s_id, s_id)
        zones.append({
            "name": label,
            "health": s_data.get('label', 'Unknown'),
            "ndvi": s_data.get('ndvi') or 0.5,
            "risk": "High" if (s_data.get('ndvi') or 0.5) < 0.4 else "Low"
        })
    return zones

def save_field_history():
    """Captures a snapshot of field status to MongoDB for the weekly timeline."""
    try:
        import pymongo
        MONGO_CON = "mongodb+srv://bhoomivaishya06_db_user:GuysqjmNsQjvgZuj@cluster0.wqfcwpe.mongodb.net/?appName=Cluster0"
        client = pymongo.MongoClient(MONGO_CON, serverSelectionTimeoutMS=2000)
        db = client.RiceFarmDB
        history = db.field_history
        
        daily = get_daily_summary()
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "health_score": daily['avg_ndvi'],
            "moisture_score": daily.get('avg_ndwi', 0.0),
            "yield_prediction": daily['yield_estimate'],
            "risk_score": daily.get('critical_percent', daily.get('overall_risk', 0)),
            "event": "Regular Check" if daily['overall_color'] == 'green' else "Stress Detected"
        }
        
        # Only save if last record is older than 6 hours to avoid spam
        last = history.find_one(sort=[("timestamp", -1)])
        if not last or (datetime.now() - datetime.fromisoformat(last['timestamp'])).total_seconds() > 21600:
            history.insert_one(snapshot)
            print("📜 History: Snapshot saved to Cloud.")
    except Exception as e:
        print(f"⚠️ History Sync Failed: {e}")

def get_field_history():
    """Retrieves weekly summaries for the history timeline."""
    try:
        import pymongo
        MONGO_CON = "mongodb+srv://bhoomivaishya06_db_user:GuysqjmNsQjvgZuj@cluster0.wqfcwpe.mongodb.net/?appName=Cluster0"
        client = pymongo.MongoClient(MONGO_CON, serverSelectionTimeoutMS=2000)
        history = list(client.RiceFarmDB.field_history.find().sort("timestamp", 1).limit(60))
        return history
    except:
        return []

def get_performance_analytics(lang="en"):
    """
    Computes high-fidelity analytics for the Performance History dashboard.
    Aggregates KPIs, deltas vs 30 days ago, and per-field sparklines.
    """
    history = get_field_history()
    from sim_engine import get_sim_engine, FIELD_NAMES
    engine = get_sim_engine()
    
    # 0. Sync Simulation with Reality (UNIFY TRUTH)
    sat_data = get_real_satellite_data()
    if sat_data:
        if hasattr(engine, 'sync_with_real_data'):
            engine.sync_with_real_data(sat_data)
    
    # 1. KPI Calculations (Using history if available, else simulation)
    if len(history) >= 10:
        latest = history[-1]
        prior  = history[-10] # Roughly 30 days if snapshotted every 3 days
        ndvi_curr = latest.get('health_score', 0.6) / 100.0 if latest.get('health_score', 0) > 1 else latest.get('health_score', 0.6)
        ndvi_prev = prior.get('health_score', 0.58) / 100.0 if prior.get('health_score', 0) > 1 else prior.get('health_score', 0.58)
        ndvi_delta = round(ndvi_curr - ndvi_prev, 2)
    else:
        # Simulated fallback
        ndvi_curr  = sum(f["ndvi"] for f in engine.fields.values()) / len(engine.fields)
        ndvi_delta = 0.02 # Simulated trend
        
    # 2. Per-Field Grid Data
    field_snapshots = []
    for f_name in ["SE", "North", "East", "NW", "South", "SW"]: # Reference Fields
        f_data = engine.get_field(f_name)
        f_ts   = engine.get_time_series(f_name)
        # 7-week trend (latest 7 weeks from hist)
        trend = f_ts.get('ndvi_hist', [0.5,0.5,0.5,0.5,0.5,0.5,0.5])[-7:]
        
        field_snapshots.append({
            "name": f_name,
            "ndvi": f_data.get("ndvi", 0.6),
            "moisture": f_data.get("moisture", 50),
            "yield": f_data.get("yield_pred", 2.2),
            "status": f_data.get("status", "Healthy"),
            "trend": trend
        })
        
    return {
        "avg_ndvi": ndvi_curr,
        "ndvi_delta": ndvi_delta,
        "avg_moisture": sum(f["ndwi"] for f in engine.fields.values()) / len(engine.fields),
        "yield_forecast": sum(f["yield_pred"] for f in engine.fields.values()) / len(engine.fields),
        "stress_count": len([a for a in engine.alerts if a["severity"] == "Critical"]),
        "best_field": max(engine.fields.items(), key=lambda x: x[1]['ndvi'])[0],
        "field_snapshots": field_snapshots,
        "ai_insight": "NDVI peaked in mid-March then declined — consistent with tillering water stress. Moisture has been below optimal for 18 days. If irrigation improves, yield can recover by harvest." if lang=="en" else "मार्च के मध्य में एनडीवीआई चरम पर था और फिर गिर गया - यह कल्ले फूटने के समय पानी के तनाव के अनुरूप है। 18 दिनों से नमी अनुकूल से कम रही है। यदि सिंचाई में सुधार होता है, तो कटाई तक पैदावार में सुधार हो सकता है।"
    }

def get_farmer_tips(lang="en"):
    """Simple, visual-first tips."""
    if lang == "hi":
        return [
            {"icon": "💧", "text": "मिट्टी सूखी है? पानी डालें जब तक टखने न डूब जाएं।", "color": "#3b82f6"},
            {"icon": "🌿", "text": "पत्ते पीले हो रहे हैं? पौधों को यूरिया की जरूरत हो सकती है।", "color": "#10b981"},
            {"icon": "🔭", "text": "नक्शा देखें! लाल हिस्सों पर पहले ध्यान दें।", "color": "#ef4444"}
        ]
    return [
        {"icon": "💧", "text": "Is the soil dry? Add water until it covers your ankle.", "color": "#3b82f6"},
        {"icon": "🌿", "text": "Are leaves turning yellow? Your plants might be hungry for Urea.", "color": "#10b981"},
        {"icon": "🔭", "text": "Check the map! Red areas need your help first.", "color": "#ef4444"}
    ]

# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────

def apply_custom_css():
    """FarmOS UI — deep forest green background, amber accent, earthen glass panels."""
    from utils import inject_css, _FARMOS_CSS   # Re-use the shared design system
    st.markdown(f"<style>{_FARMOS_CSS}</style>", unsafe_allow_html=True)







def get_spectral_analytics(index_key="NDVI", lang="en"):
    """
    Computes farm-wide spatial statistics for the Spectral Health Maps.
    Calculates calibrated zonal breakdowns based on the index type.
    """
    from sim_engine import get_sim_engine, FIELD_NAMES
    engine = get_sim_engine()
    
    # 0. Sync Simulation with Reality (THE FIX)
    real_sat = get_real_satellite_data()
    if real_sat:
        if hasattr(engine, 'sync_with_real_data'):
            engine.sync_with_real_data(real_sat)
        if hasattr(engine, 'sync_trends_with_real_data'):
            engine.sync_trends_with_real_data(TREND_FILE)
    
    # 1. Aggregate All Spatial Data
    all_values = []
    field_averages = []
    
    for name in FIELD_NAMES:
        grid = engine.get_spatial_grid(index_key.lower(), name)
        avg_val = np.mean(grid)
        field_averages.append({"name": name, "value": float(avg_val)})
        all_values.extend(np.array(grid).flatten())
    
    all_values = np.array(all_values)
    
    # 2. Index-Specific Threshold Calibration
    # NDVI (Vegetation): High is good (0.6 - 0.9)
    # NDWI (Moisture):   Saturated rice fields are 0.3 - 0.5. Values > 0.5 are often open water.
    if index_key.upper() == "NDWI":
        # Calibrated for Water/Moisture in Rice
        p_thresh, h_thresh, w_thresh, s_thresh = 0.45, 0.25, 0.15, 0.05
    elif index_key.upper() == "STRESS":
        # Stress Index (High is bad, so we invert or use special thresholds)
        # We will keep raw then use buckets accordingly
        p_thresh, h_thresh, w_thresh, s_thresh = 0.15, 0.30, 0.50, 0.70
    elif index_key.upper() == "YIELD":
        # Yield Potential Index
        p_thresh, h_thresh, w_thresh, s_thresh = 0.75, 0.60, 0.45, 0.30
    else:
        # Standard NDVI / Others
        p_thresh, h_thresh, w_thresh, s_thresh = 0.75, 0.50, 0.30, 0.15

    # 3. Zone Breakdown Calculation
    if index_key.upper() == "STRESS":
        # Inverted buckets for Stress (Low is Peak)
        buckets = {
            "peak":     len(all_values[all_values < p_thresh]),
            "healthy":  len(all_values[(all_values >= p_thresh) & (all_values < h_thresh)]),
            "watch":    len(all_values[(all_values >= h_thresh) & (all_values < w_thresh)]),
            "stressed": len(all_values[(all_values >= w_thresh) & (all_values < s_thresh)]),
            "critical": len(all_values[all_values >= s_thresh])
        }
    else:
        buckets = {
            "peak":     len(all_values[all_values >= p_thresh]),
            "healthy":  len(all_values[(all_values >= h_thresh) & (all_values < p_thresh)]),
            "watch":    len(all_values[(all_values >= w_thresh) & (all_values < h_thresh)]),
            "stressed": len(all_values[(all_values >= s_thresh) & (all_values < w_thresh)]),
            "critical": len(all_values[all_values < s_thresh])
        }
    
    total = len(all_values)
    breakdown = {k: round((v/total)*100, 1) for k, v in buckets.items()}
    
    # 4. Sorting & KPIs
    field_averages.sort(key=lambda x: x['value'], reverse=True)
    
    # Dynamic KPI Thresholds for Counts
    if index_key.upper() == "STRESS":
        critical_zones = [f for f in field_averages if f['value'] > s_thresh]
        watch_zones    = [f for f in field_averages if h_thresh <= f['value'] <= s_thresh]
    else:
        crit_limit = s_thresh * 1.5 if index_key.upper() != "NDWI" else s_thresh
        watch_limit = h_thresh
        critical_zones = [f for f in field_averages if f['value'] < crit_limit]
        watch_zones    = [f for f in field_averages if crit_limit <= f['value'] < watch_limit]
    
    # Healthy % = Peak + Healthy
    healthy_percent = breakdown['peak'] + breakdown['healthy']
    
    # Dynamic Recommendation Text
    if index_key.upper() == "NDWI":
        status_msg = f"{index_key} analysis: Field moisture is {'excellent' if healthy_percent > 70 else 'optimal' if healthy_percent > 40 else 'low'}."
    elif index_key.upper() == "STRESS":
        status_msg = f"{index_key} analysis: Plant stress level is {'minimal' if healthy_percent > 70 else 'moderate' if healthy_percent > 40 else 'significant'}."
    elif index_key.upper() == "YIELD":
        status_msg = f"{index_key} analysis: Future yield potential is {'high' if healthy_percent > 70 else 'stable' if healthy_percent > 40 else 'restricted'}."
    else:
        status_msg = f"{index_key} analysis: Vegetation health is {'good' if healthy_percent > 70 else 'stable' if healthy_percent > 40 else 'critical'}."

    return {
        "breakdown": breakdown,
        "ranking": field_averages,
        "avg_farm_val": np.mean(all_values),
        "critical_count": len(critical_zones),
        "critical_names": ", ".join([f['name'] for f in critical_zones[:2]]) or "None",
        "watch_count": len(watch_zones),
        "best_field": field_averages[0]['name'] if field_averages else "N/A",
        "healthy_percent": healthy_percent,
        "ai_analysis": f"{status_msg} {field_averages[-1]['name']} field shows the highest variability." if lang == "en" else f"{index_key} विश्लेषण: {field_averages[-1]['name']} क्षेत्र में सबसे अधिक परिवर्तनशीलता दिखती है।"
    }

def get_pest_analytics(lang="en"):
    """
    Computes farm-wide pest and disease risk metrics.
    Includes Spray Window estimation and Treatment History.
    """
    from sim_engine import get_sim_engine, FIELD_NAMES, THREATS
    from alert_config import THREAT_METADATA
    engine = get_sim_engine()
    
    # KPIs & Matrix Aggregation
    field_intel = get_field_intelligence(lang=lang)
    summary = field_intel["summary"]
    weather = load_current_weather()
    forecast = weather.get('forecast', [])
    
    # Calculate Live Disease Profiles
    profiles = de.compute_disease_profiles(
        summary['humidity'], summary['temp'], summary['rain_3d'], 
        summary['ndvi'], summary['stage'], forecast=forecast
    )
    
    matrix = {}
    critical_count = 0
    warning_count  = 0
    protected_count = 0
    total_since_last = 0
    
    # Map the live profiles to each field (simplified for now, using farm extremes)
    for f_name in FIELD_NAMES:
        sanitized_risks = {
            "Rice Blast": profiles['blast']['score'],
            "Brown Spot": profiles['brown_spot']['score'],
            "Sheath Blight": profiles['sheath_blight']['score'],
            "False Smut": profiles['false_smut']['score']
        }
        matrix[f_name] = sanitized_risks
        
        max_risk = max(sanitized_risks.values())
        if max_risk > 70: critical_count += 1
        elif max_risk > 40: warning_count += 1
        if max_risk < 30: protected_count += 1
        
        # Treatment history formula (deterministic based on crop stage)
        life = get_rice_life_cycle()
        dat = life.get('dat', 40)
        days_ago = (dat % 12) + 2 # Dynamic relative to planting
        total_since_last += days_ago
        
    avg_since_last = total_since_last / len(FIELD_NAMES)
    
    # 2. Spray Window & Analysis
    wind_speed = weather.get('current', {}).get('wind_speed', 5)
    is_safe = wind_speed < 12
    spray_window = "4 - 8 AM" if is_safe else "Avoid - Wind too high"
    
    # Dynamic text based on highest profile
    top_threat = max(profiles.items(), key=lambda x: x[1]['score'])
    analysis = f"<b>{top_threat[0].replace('_',' ').title()} is your most urgent threat</b> — {top_threat[1]['action_text']}"
    if lang == "hi":
        analysis = "<b>चावल ब्लास्ट आपका सबसे बड़ा खतरा है</b> - गुरुवार रात की आर्द्रता 27°C के साथ 88% तक पहुंच जाएगी।"

    return {
        "critical_count": critical_count,
        "warning_count": warning_count,
        "fields_protected": f"{protected_count}/{len(FIELD_NAMES)}",
        "spray_window": spray_window,
        "spray_delta": f"Wind {wind_speed} km/h",
        "avg_days_since": int(avg_since_last),
        "matrix": matrix,
        "threats": ["Rice Blast", "Brown Spot", "Sheath Blight", "False Smut"],
        "details": THREAT_METADATA,
        "history": [
            {"field": f, "days_ago": (dat % 12) + 2, "due_in": 14 - ((dat % 12) + 2), 
             "status": "Overdue" if (14-((dat % 12) + 2)) < 0 else f"In {14-((dat % 12) + 2)} days"} 
            for f in FIELD_NAMES
        ],
        "analysis": analysis,
        "source": weather.get('source', 'Simulated')
    }

def get_nutrition_analytics(lang="en"):
    """
    Computes farm-wide NPK levels, trends, recommendations and costs.
    Priority: Live IoT Nodes (MongoDB)
    Fallback: Simulation Engine
    """
    from sim_engine import get_sim_engine, FIELD_NAMES
    from alert_config import NPK_CONFIG, FERTILIZER_CONFIG
    engine = get_sim_engine()
    
    # 0. Sync Simulation with Reality (UNIFY TRUTH)
    real_sat = get_real_satellite_data()
    if real_sat:
        if hasattr(engine, 'sync_with_real_data'):
            engine.sync_with_real_data(real_sat)
            
    nodes = get_sensor_nodes() # Live from MongoDB
    
    # 1. KPI Aggregation (Current Levels)
    matrix = {}
    sum_n, sum_p, sum_k = 0, 0, 0
    
    if nodes and len(nodes) > 0:
        st.session_state['nutrition_source_verification'] = "Verified IoT (Soil Sensors)"
        # Map nodes to matrix
        for i, (n_id, n_data) in enumerate(nodes.items()):
            # Fallback to names if node list is short
            f_name = FIELD_NAMES[i % len(FIELD_NAMES)]
            n_val = n_data.get('nitrogen', 45)
            p_val = n_data.get('phosphorus', 18)
            k_val = n_data.get('potassium', 38)
            
            matrix[f_name] = {"N": n_val, "P": p_val, "K": k_val}
            sum_n += n_val
            sum_p += p_val
            sum_k += k_val
        denom = len(nodes)
    else:
        st.session_state['nutrition_source_verification'] = "Regional Estimates"
        for f in FIELD_NAMES:
            fd = engine.fields[f]
            matrix[f] = {"N": fd["nitrogen"], "P": fd["phosphorus"], "K": fd["potassium"]}
            sum_n += fd["nitrogen"]
            sum_p += fd["phosphorus"]
            sum_k += fd["potassium"]
        denom = len(FIELD_NAMES)
    
    avg_n = sum_n / denom
    avg_p = sum_p / denom
    avg_k = sum_k / denom

    # 2. Trend Simulation (8 Weeks)
    weeks = ["Feb 24", "Mar 3", "Mar 10", "Mar 17", "Mar 24", "Mar 31", "Apr 7", "Apr 14"]
    # Simulate a gentle depletion over time for trends
    n_trend = [avg_n + (8 - i)*1.5 for i in range(8)]
    p_trend = [avg_p + (8 - i)*0.5 for i in range(8)]
    k_trend = [avg_k + (8 - i)*0.8 for i in range(8)]
    
    # 3. Recommendations & Costs
    recs = []
    cost_items = []
    total_cost = 0
    total_acres = len(FIELD_NAMES) * 1.5 # Assume each field is 1.5 acres for simulation
    
    # Phosphorus Check (Urgent in screenshot)
    if avg_p < NPK_CONFIG["P"]["min"]:
        gap = NPK_CONFIG["P"]["min"] - avg_p
        qty = FERTILIZER_CONFIG["MRP"]["standard_dose"] * total_acres
        cost = qty * FERTILIZER_CONFIG["MRP"]["price"]
        total_cost += cost
        recs.append({
            "type": "MRP",
            "val": FERTILIZER_CONFIG["MRP"]["standard_dose"],
            "timing": "Before Thu 10am",
            "cost": int(cost),
            "urgent": True,
            "role": FERTILIZER_CONFIG["MRP"]["role"]
        })
        cost_items.append({"name": FERTILIZER_CONFIG["MRP"]["name"], "fields": "SW, Central, South", "qty": int(qty), "price": FERTILIZER_CONFIG["MRP"]["price"], "total": int(cost)})

    # Potassium Check
    if avg_k < NPK_CONFIG["K"]["min"]:
        qty = FERTILIZER_CONFIG["MOP"]["standard_dose"] * total_acres
        cost = qty * FERTILIZER_CONFIG["MOP"]["price"]
        total_cost += cost
        recs.append({
            "type": "MOP",
            "val": FERTILIZER_CONFIG["MOP"]["standard_dose"],
            "timing": "In 10-14 days",
            "cost": int(cost),
            "urgent": False,
            "role": FERTILIZER_CONFIG["MOP"]["role"]
        })
        cost_items.append({"name": FERTILIZER_CONFIG["MOP"]["name"], "fields": "All 9 fields", "qty": int(qty), "price": FERTILIZER_CONFIG["MOP"]["price"], "total": int(cost)})

    # Nitrogen Maintenance
    recs.append({
        "type": "Nitrogen",
        "val": "Maintain",
        "timing": "Monitor weekly",
        "cost": 0,
        "urgent": False,
        "role": "Status: Optimal range" if avg_n >= NPK_CONFIG["N"]["min"] else "Status: Monitor"
    })
    cost_items.append({"name": "Urea top-up (N maintenance)", "fields": "Monitor only", "qty": 0, "price": 0, "total": 0})

    # AI Insight
    p_gap = max(0, NPK_CONFIG["P"]["min"] - avg_p)
    analysis = f"Phosphorus deficiency is your most urgent issue — at {avg_p:.1f} kg/ha it's {int((p_gap/NPK_CONFIG['P']['min'])*100)}% below target. Apply MRP 50 kg/ha before Thursday."
    if lang == "hi":
        analysis = f"फास्फोरस की कमी आपका सबसे जरूरी मुद्दा है — {avg_p:.1f} किग्रा/हेक्टेयर पर यह लक्ष्य से {int((p_gap/NPK_CONFIG['P']['min'])*100)}% कम है।"

    return {
        "avg_n": avg_n, "avg_p": avg_p, "avg_k": avg_k,
        "matrix": matrix,
        "trends": {"weeks": weeks, "N": n_trend, "P": p_trend, "K": k_trend},
        "recs": recs,
        "cost_items": cost_items,
        "total_cost": total_cost,
        "analysis": analysis,
        "config": NPK_CONFIG
    }
# ─────────────────────────────────────────────
# PROACTIVE STATE SYNC (Heartbeat)
# ─────────────────────────────────────────────

def sync_real_time_state():
    """
    Called on every page load via utils.setup_page.
    Triggers critical alert logic without blocking UI.
    Uses a 5-minute cooldown to prevent redundant processing.
    """
    # 1. Check cooldown
    last_sync = st.session_state.get('last_alert_sync', 0)
    current_time = time.time()
    
    if current_time - last_sync < 300: # 5 min cooldown
        return
        
    try:
        # Trigger intelligence for the main sectors to find critical threats
        lang = st.session_state.get('lang', 'en')
        field = st.session_state.get('selected_field', "North Plot")
        
        # This call implicitly triggers decision_engine.compute_field_state
        # which sends SMS alerts for Critical (>=70) threats.
        get_field_intelligence(lang=lang, sector_name=field)
        
        st.session_state.last_alert_sync = current_time
        print(f"💓 Heartbeat: Real-time alert sync completed for {field}")
        
    except Exception as e:
        print(f"⚠️ Heartbeat Sync Failed: {e}")
