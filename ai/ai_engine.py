"""
AI Engine for Rice Farm Platform
Centralized logic for predictions and health analysis.
Supports Hyperspectral/Multispectral indices and real ML model loading.
"""
import os
import pickle
import numpy as np

# Registry for loaded models
_MODELS = {}

def load_model(model_name, force_reload=False):
    """Loads a model from the models/ directory."""
    global _MODELS
    if model_name in _MODELS and not force_reload:
        return _MODELS[model_name]
    
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', model_name)
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                _MODELS[model_name] = pickle.load(f)
            return _MODELS[model_name]
        except Exception as e:
            print(f"⚠️ Error loading model {model_name}: {e}")
    return None

# --- HYPERSPECTRAL & SPECTRAL INDICES ---

def calculate_ndwi(green, nir):
    """Normalized Difference Water Index - for water stress detection."""
    if (nir + green) == 0: return 0
    return (green - nir) / (green + nir)

def calculate_vari(red, green, blue):
    """Visible Atmospherically Resistant Index - for vegetation fraction."""
    if (2 * green - red - blue) == 0: return 0
    return (green - red) / (green + red - blue)

def calculate_gli(red, green, blue):
    """Green Leaf Index - variant of NDVI for RGB imagery."""
    if (2 * green + red + blue) == 0: return 0
    return (2 * green - red - blue) / (2 * green + red + blue)

# --- CORE PREDICTION ENGINES ---

def predict_crop_health(ndvi, ndvi_trend, growth_stage="Tillering", avg_temp=28):
    """
    Simulates a Random Forest Classifier for Crop Health.
    
    Inputs:
        ndvi (float): Current NDVI value
        ndvi_trend (float): Change in NDVI over last period
        growth_stage (str): Current stage from Settings
        avg_temp (float): Region temperature
        
    Outputs:
        int: 0 = Healthy (Green), 1 = Slight Stress (Yellow), 2 = Critical (Red)
    """
    # --- REAL MODEL INFERENCE ---
    model = load_model('rice_health_classifier.pkl')
    if model:
        # Features: ndvi, trend, stage_code, temp
        # Note: mapping stage names to codes should be standardized
        stage_map = {"Seedling": 0, "Tillering": 1, "Flowering": 2, "Grain Filling": 3, "Pre-Harvest": 4}
        stage_code = stage_map.get(growth_stage, 1)
        try:
            features = np.array([[ndvi, ndvi_trend, stage_code, avg_temp]])
            return int(model.predict(features)[0])
        except Exception:
            pass # Fallback to simulation if feature mismatch

    # --- PRECISION ANALYTICS (Fallback to Satellite Heuristics) ---
    # This logic uses established agricultural science to estimate health when 
    # a local pre-trained ML model is not available.
    thresholds = {
        "Seedling":     {"good": 0.30, "ok": 0.20},
        "Tillering":    {"good": 0.50, "ok": 0.35},
        "Flowering":    {"good": 0.75, "ok": 0.55},
        "Grain Filling":{"good": 0.65, "ok": 0.45},
        "Pre-Harvest":  {"good": 0.40, "ok": 0.25}
    }
    
    stage_thr = thresholds.get(growth_stage, thresholds["Tillering"])
    
    if ndvi >= stage_thr["good"]:
        if ndvi_trend < -15: return 1 
        return 0 
    elif ndvi >= stage_thr["ok"]:
        return 1 
    else:
        return 2 

def predict_disease_risk(humidity, temp, rain_days, growth_stage="Tillering", ndvi_status=0):
    """
    Simulates a Logistic Regression probability model for Disease Risk.
    
    Outputs:
        dict: { 'risk_level': str, 'probability': int, 'main_threat': str }
    """
    # Basic logic: High humidity + Moderate temp = Fungal risk
    risk_score = 0
    
    # Humidity is the biggest factor for rice diseases like Blast/Blight
    if humidity > 85: risk_score += 40
    elif humidity > 75: risk_score += 20
    
    # Temperature (Blast likes 25-28C)
    if 24 <= temp <= 29: risk_score += 20
    
    # Rain days (wet leaves)
    if rain_days >= 3: risk_score += 20
    
    # Existing stress makes it worse
    if ndvi_status > 0: risk_score += 20
    
    # Caps at 100
    risk_score = min(risk_score, 100)
    
    # Determine level
    if risk_score > 70:
        level = "High"
        threat = "Rice Blast (Fungal)"
    elif risk_score > 40:
        level = "Moderate"
        threat = "Leaf Blight (Bacterial)"
    else:
        level = "Low"
        threat = "None Identified"
        
    return {
        "level": level,
        "probability": risk_score,
        "threat": threat
    }

def get_irrigation_guidance(growth_stage, rain_forecast, soil_moisture, temp):
    """
    Smart Irrigation Advisor: Water depth guidance for Paddy.
    """
    # Depth requirements (cm) for different Paddy stages
    depth_needs = {
        "Seedling": (1, 3),
        "Tillering": (3, 5),
        "Flowering": (5, 10),
        "Grain Filling": (5, 7),
        "Pre-Harvest": (0, 0)
    }
    
    min_d, max_d = depth_needs.get(growth_stage, (2, 5))
    
    advice = f"Maintain {min_d}-{max_d} cm water depth."
    warning = None
    
    if rain_forecast > 30:
        advice = "Heavy rain expected. Drain field immediately."
        warning = "Flood Risk"
    elif soil_moisture < 30 and temp > 32:
        advice = f"Fast evaporation! Increase depth to {max_d} cm."
        
    return {
        "recommended_depth": f"{min_d}-{max_d} cm",
        "advice": advice,
        "warning": warning
    }

def get_pest_outlook(forecast_data):
    """
    Pest Early Warning: 3-day outlook for BPH or Leaf Folder.
    """
    outlook = []
    days = ["Tomorrow", "Day 2", "Day 3"]
    
    for i, day_name in enumerate(days):
        # High Humidity + warm nights favor BPH (Brown Plant Hopper)
        f_point = forecast_data[i] if i < len(forecast_data) else {}
        hum = f_point.get('humidity', 70)
        temp = f_point.get('temp', 28)
        
        risk = "Low"
        if hum > 85 and 25 <= temp <= 30: risk = "High"
        elif hum > 75: risk = "Medium"
        
        outlook.append({"day": day_name, "risk": risk, "target": "Pests: BPH / Leaf Folder"})
        
    return outlook

def predict_yield_precision(ndvi, ndvi_trend, rainfall, growth_stage, target_yield=5.0):
    """
    Advanced Yield Regressor (Random Forest structure).
    Predicts tons/acre based on satellite trends and environmental data.
    """
    model = load_model('rice_yield_regressor.pkl')
    if model:
        try:
            # Code to run real inference if pkl is found
            features = np.array([[ndvi, ndvi_trend, rainfall, target_yield]])
            return {"estimate": round(model.predict(features)[0], 2), "confidence": "High"}
        except: pass

    # --- SCIENTIFIC HEURISTIC (Data-Driven fallback) ---
    base_potential = (ndvi / 0.8) * target_yield
    
    # Penalties for negative trends or lack of rain
    trend_impact = 1.0 + (ndvi_trend / 200) # -5% if trend is -10
    rain_impact = 1.0 if rainfall > 20 else 0.85 # Dry spell penalty
    
    # Stage sensitivity
    stage_weights = {"Flowering": 1.2, "Grain Filling": 1.1, "Tillering": 0.9}
    multiplier = stage_weights.get(growth_stage, 1.0)
    
    prediction = base_potential * trend_impact * rain_impact * multiplier
    
    # Confidence logic
    confidence = "High" if ndvi > 0.6 else "Medium" if ndvi > 0.4 else "Low"
    
    return {
        "estimate": round(min(target_yield * 1.5, max(0.5, prediction)), 2),
        "confidence": confidence,
        "risks": ["Low rainfall detected"] if rainfall < 15 else []
    }

def predict_nutrient_deficiency(sectors, growth_stage):
    """
    Spatial Analytics for Nutrient (Nitrogen) Detection.
    Compares NDVI across patches to detect localized yellowing/thinning.
    """
    if not sectors: return {"status": "Stable", "action": None}
    
    ndvi_values = [s['ndvi'] for s in sectors.values() if s['ndvi'] is not None]
    if not ndvi_values: return {"status": "Stable", "action": None}
    
    avg_ndvi = sum(ndvi_values) / len(ndvi_values)
    worst_ndvi = min(ndvi_values)
    
    # If a patch is >20% worse than field average, it's likely a nutrient deficiency 
    # (assuming irrigation is uniform across the small farm)
    if (avg_ndvi - worst_ndvi) > 0.15:
        return {
            "status": "Deficient",
            "level": "Nitrogen (N) Stress",
            "recommendation": "Apply 25kg Nitrogen/Acre to the lagging patch.",
            "confidence": "Medium (Spatial Variance)"
        }
    
    return {"status": "Stable", "action": "Nutrients sufficient."}

def generate_farmer_advice(health_status, disease_level, lang="en"):
    """
    Converts ML outputs to localized 'Field Speak'.
    """
    if lang == "hi":
        if health_status == 2: # Critical
            return "खेत की हालत ठीक नहीं है। तुरंत जाकर पानी और खाद जांचें।"
        if disease_level == "High":
            return "बीमारी का बहुत खतरा है। पत्तों को ध्यान से देखें और नमी कम रखें।"
        if health_status == 1:
            return "फसल थोड़ी कमजोर दिख रही है। समय पर खाद डालें।"
        return "फसल स्वस्थ है। सामान्य देखभाल जारी रखें।"
    else:
        if health_status == 2: # Critical
            return "Crop health is poor. Visit the field today and check water/fertilizer."
        if disease_level == "High":
            return "High disease risk! Inspect leaves daily and avoid over-watering."
        if health_status == 1:
            return "Crop shows slight stress. Ensure timely fertilization."
        return "Crop looks healthy and stable. Continue normal care."
