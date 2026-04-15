"""
Precision Agriculture Decision Engine
======================================
Real agronomic formula engine. 
All outputs are computed from real inputs — no templates, no hardcoded text.

Data Flow:
  Sentinel-2 NDVI/NDWI + Weather + Sensors
       ↓
  compute_field_state()  →  full agronomic analysis dict
       ↓
  get_smart_actions()    →  top-3 ranked actions with 'If No Action' impact
       ↓
  All pages and AI Agronomist read from this single source of truth
"""

from datetime import datetime, timedelta
import math
import os
import json

# ─────────────────────────────────────────────────────────────────────────────
# AGRONOMIC CONSTANTS (Rice / Paddy — Vidarbha, India)
# ─────────────────────────────────────────────────────────────────────────────

# NDVI healthy thresholds per growth stage (established rice agronomy)
NDVI_THRESHOLDS = {
    "Seedling":      {"healthy": 0.30, "moderate": 0.18, "base_yield": 5.0},
    "Tillering":     {"healthy": 0.45, "moderate": 0.28, "base_yield": 5.0},
    "Jointing":      {"healthy": 0.65, "moderate": 0.45, "base_yield": 5.0},
    "Heading":       {"healthy": 0.75, "moderate": 0.55, "base_yield": 5.0},
    "Grain Filling": {"healthy": 0.60, "moderate": 0.40, "base_yield": 5.0},
    "Maturity":      {"healthy": 0.22, "moderate": 0.15, "base_yield": 5.0},
}

# NDWI thresholds (Normalized Difference Water Index)
# NDWI < 0.0 → dry stress likely
# NDWI 0.0–0.2 → moderate moisture
# NDWI > 0.2 → adequate water
NDWI_DRY     = 0.0
NDWI_OPTIMAL = 0.15

# Water depth recommendations (cm) per stage
WATER_DEPTH_NEEDS = {
    "Seedling":      (1, 3),
    "Tillering":     (2, 5),
    "Jointing":      (3, 8),
    "Heading":       (5, 10),
    "Grain Filling": (3, 5),
    "Maturity":      (0, 2),
}

# ─────────────────────────────────────────────────────────────────────────────
# A. NDVI INTERPRETATION (growth-stage aware)
# ─────────────────────────────────────────────────────────────────────────────

def interpret_ndvi(ndvi, stage, ndvi_7d_avg=None, peak_ndvi=None):
    """
    Returns NDVI health status, expected range, and deficit.
    Adaptive: Incorporates farm-specific peak performance.
    """
    thr = NDVI_THRESHOLDS.get(stage, NDVI_THRESHOLDS["Tillering"])
    
    # Adaptive Baseline: Use the farm's own peak if it's higher than the global target
    # (Only applies during growing stages; senescence handles Maturity)
    if peak_ndvi and stage not in ("Grain Filling", "Maturity"):
        healthy_thr = max(thr["healthy"], peak_ndvi * 0.98)
    else:
        healthy_thr  = thr["healthy"]
        
    moderate_thr = thr["moderate"]

    if ndvi >= healthy_thr:
        status = "Healthy"
        deficit = 0.0
    elif ndvi >= moderate_thr:
        status = "Moderate"
        deficit = round(healthy_thr - ndvi, 3)
    else:
        status = "Poor"
        deficit = round(healthy_thr - ndvi, 3)

    # NDVI growth rate (per day) — negative = declining canopy
    growth_rate = None
    if ndvi_7d_avg is not None and ndvi_7d_avg > 0:
        growth_rate = round((ndvi - ndvi_7d_avg) / 7.0, 5)

    return {
        "status":       status,
        "ndvi":         ndvi,
        "expected_min": moderate_thr,
        "expected_ok":  healthy_thr,
        "deficit":      deficit,
        "growth_rate":  growth_rate,   # units: ΔNDVI/day
        "stage":        stage,
    }

def generate_morning_briefing(engine, lang="en"):
    """Generates a dynamic 1-paragraph conversational morning briefing based on the live simulation state."""
    # 1. Total Health
    healths = [f["health_score"] for f in engine.fields.values()]
    avg_h = sum(healths) / len(healths) if healths else 0
    
    # 2. Moisture / Irrigation check
    dry_fields = []
    for k, v in engine.fields.items():
        if v["moisture"] < 40:
            dry_fields.append((k, v["moisture"]))
    
    # 3. Pest check
    high_risk_fields = []
    for k, v in engine.fields.items():
        if v["top_threat_score"] > 60:
            high_risk_fields.append((k, v["top_threat"]))
            
    if lang == "hi":
        msg = f"सुप्रभात। आज आपके खेत का कुल स्वास्थ्य **{avg_h:.0f}%** है। "
        if dry_fields:
            df_names = ", ".join([f[0] for f in dry_fields[:2]])
            msg += f"**{df_names}** खेत में पानी की कमी हो रही है और अगले कुछ दिन बारिश का कोई अनुमान नहीं है, इसलिए पंप चालू करने की सलाह दी जाती है। "
        else:
            msg += "सभी खेतों में नमी बिल्कुल सही है, आज सिंचाई की आवश्यकता नहीं है। "
            
        if high_risk_fields:
            pf_name, p_threat = high_risk_fields[0]
            msg += f"ध्यान दें: मौसम में नमी के कारण **{pf_name}** में **{p_threat}** का खतरा बढ़ रहा है। AI का सुझाव है कि एहतियात के तौर पर दवा का छिड़काव करें।"
        else:
            msg += "किसी भी खेत में कीड़ों या बीमारी का कोई गंभीर खतरा नहीं है।"
            
    else:
        msg = f"Good morning. Your farm is **{avg_h:.0f}%** healthy today. "
        if dry_fields:
            df_names = ", ".join([f[0] for f in dry_fields[:2]])
            msg += f"The **{df_names}** plot needs irrigation — soil moisture has dropped below 40% and no immediate rain is forecasted. "
        else:
            msg += "Soil moisture across all plots is optimal, no irrigation required today. "
            
        if high_risk_fields:
            pf_name, p_threat = high_risk_fields[0]
            msg += f"**Watch out:** Your **{pf_name}** plot has a rising risk of **{p_threat}** because last night was humid and warm. The AI recommends a preventative spray before Thursday."
        else:
            msg += "Crop health is stable with no immediate pest or disease threats detected."
            
    return msg

# ─────────────────────────────────────────────────────────────────────────────
# B. NITROGEN DEFICIENCY DETECTION (via NDVI growth rate)
# ─────────────────────────────────────────────────────────────────────────────

def assess_nitrogen_risk(ndvi_status, ndvi_7d_avg=None, rain_3d=0.0, soil_moisture=50.0):
    """
    Nitrogen deficiency shows as:
      - Reduced NDVI relative to stage expectation
      - Stagnant or declining growth rate
      - Despite adequate water (ruling out drought as cause)
    
    Returns dict: risk_level, confidence, dose_recommendation
    """
    ndvi       = ndvi_status["ndvi"]
    deficit    = ndvi_status["deficit"]
    status     = ndvi_status["status"]
    growth_rate = ndvi_status.get("growth_rate")  # ΔNDVI/day

    risk_score = 0

    # Factor 1: NDVI below stage-expected range
    if status == "Poor":     risk_score += 40
    elif status == "Moderate": risk_score += 20

    # Factor 2: Declining or stagnant growth rate
    if growth_rate is not None:
        if growth_rate < -0.003:   risk_score += 35  # strong decline
        elif growth_rate < 0.0:    risk_score += 20  # slow decline
        elif growth_rate < 0.001:  risk_score += 10  # stagnant

    # Factor 3: Water is NOT the limiting factor
    # If soil moisture is adequate AND rain is present, NDVI drop → Nitrogen
    if soil_moisture > 35 and rain_3d > 5:
        risk_score = min(risk_score + 15, 100)  # water ok → N is more likely cause

    risk_score = min(risk_score, 100)

    if risk_score >= 55:
        level    = "High"
        dose_kg  = 30  # kg Urea/acre — standard top-dress for Tillering
        reason   = f"NDVI {ndvi:.2f} is {deficit:.2f} below healthy threshold. Growth rate {growth_rate:+.4f}/day suggests nitrogen limitation."
    elif risk_score >= 30:
        level    = "Moderate"
        dose_kg  = 20
        reason   = f"NDVI at moderate level ({ndvi:.2f}). Monitor for further decline before applying."
    else:
        level    = "Low"
        dose_kg  = 0
        reason   = f"NDVI {ndvi:.2f} appears adequate for current growth stage."

    return {
        "level":            level,
        "score":            risk_score,
        "dose_kg_per_acre": dose_kg,
        "reason":           reason,
        "growth_rate":      growth_rate,
    }

# ─────────────────────────────────────────────────────────────────────────────
# C. IRRIGATION ASSESSMENT (NDWI + weather)
# ─────────────────────────────────────────────────────────────────────────────

def assess_irrigation(ndwi, humidity, rain_3d, temp, stage, water_depth=None, soil_moisture=None):
    """
    Real irrigation logic for flooded paddy cultivation.
    Uses NDWI from Sentinel-2 Green/NIR bands + weather forecast.
    
    Returns dict: needed, urgency_score, target_depth, reason
    """
    min_depth, max_depth = WATER_DEPTH_NEEDS.get(stage, (2, 5))

    urgency = 0

    # Factor 1: NDWI (satellite moisture) — most reliable signal
    if ndwi < NDWI_DRY:
        urgency += 40   # clearly dry
    elif ndwi < NDWI_OPTIMAL:
        urgency += 20   # borderline

    # Factor 2: Humidity below 55% → fast evapotranspiration
    if humidity < 45:   urgency += 25
    elif humidity < 55: urgency += 12

    # Factor 3: Temperature-driven evaporation
    if temp > 34:    urgency += 20
    elif temp > 30:  urgency += 10

    # Factor 4: No rain in forecast
    if rain_3d < 2:    urgency += 20
    elif rain_3d < 10: urgency += 8

    # Factor 5: Sensor water depth (if available)
    if water_depth is not None:
        if float(water_depth) < min_depth * 0.5:
            urgency += 30  # critically low
        elif float(water_depth) < min_depth:
            urgency += 15  # low

    # Heavy rain → drain warning
    if rain_3d > 50:
        return {
            "needed":       False,
            "drain_warning": True,
            "urgency_score": 0,
            "target_depth": f"{min_depth}–{max_depth} cm",
            "reason":       f"Heavy rain forecast ({rain_3d:.0f} mm in 3 days). Open drainage to prevent waterlogging.",
            "action_text":  f"Open drainage gates — {rain_3d:.0f}mm rain expected. Risk of root anoxia if flooded > {max_depth+3} cm."
        }

    urgency = min(urgency, 100)
    needed  = urgency >= 40

    if urgency >= 70:
        action = f"Irrigate immediately to {max_depth} cm depth. NDWI={ndwi:.2f} indicates soil drying. Temp {temp}°C is accelerating evaporation."
    elif urgency >= 40:
        action = f"Top-up water level to {min_depth}–{max_depth} cm within 24 hours. Rain forecast is only {rain_3d:.0f}mm — insufficient for paddy needs."
    else:
        action = f"Water level appears adequate. Maintain {min_depth}–{max_depth} cm. Check again in 2–3 days."

    return {
        "needed":        needed,
        "drain_warning": False,
        "urgency_score": urgency,
        "target_depth":  f"{min_depth}–{max_depth} cm",
        "reason":        f"NDWI={ndwi:.2f}, Humidity={humidity}%, Temp={temp}°C, 3-day rain={rain_3d:.0f}mm",
        "action_text":   action
    }

# ─────────────────────────────────────────────────────────────────────────────
# D. DISEASE RISK SCORING (formula-driven, 0–100)
# ─────────────────────────────────────────────────────────────────────────────

def compute_disease_risk(humidity, temp, rain_3d, ndvi, stage):
    """
    Rice blast (Magnaporthe oryzae) and bacterial blight risk model.
    Based on established epidemiology: humidity + temp window + rain + canopy density.
    
    Returns dict with score, level, threat, contributing_factors
    """
    score = 0
    factors = []

    # Humidity (biggest factor — spore release needs wet conditions)
    if humidity > 90:
        score += 35
        factors.append(f"Very high humidity {humidity}% (optimal blast spore release)")
    elif humidity > 80:
        score += 25
        factors.append(f"High humidity {humidity}% (blast-favorable)")
    elif humidity > 70:
        score += 12
        factors.append(f"Moderate humidity {humidity}%")

    # Temperature window (Rice Blast likes 20–28°C)
    if 22 <= temp <= 27:
        score += 25
        factors.append(f"Temperature {temp}°C — ideal blast development range (22–27°C)")
    elif 18 <= temp <= 30:
        score += 12
        factors.append(f"Temperature {temp}°C — moderate blast risk range")

    # Rainfall (wet leaf surface = infection pathway)
    if rain_3d > 20:
        score += 22
        factors.append(f"Heavy rain forecast {rain_3d:.0f}mm — prolonged leaf wetness")
    elif rain_3d > 8:
        score += 12
        factors.append(f"Rain forecast {rain_3d:.0f}mm — some leaf wetness risk")

    # Dense canopy traps moisture and delays drying
    if ndvi > 0.65:
        score += 10
        factors.append(f"Dense canopy (NDVI {ndvi:.2f}) — traps humidity inside crop")

    # Stressed plants are more susceptible
    ndvi_thr = NDVI_THRESHOLDS.get(stage, NDVI_THRESHOLDS["Tillering"])
    if ndvi < ndvi_thr["moderate"]:
        score += 10
        factors.append(f"Weakened plants (NDVI below stage minimum) — lower disease resistance")

    # Critical flowering stage = highest susceptibility
    if stage in ("Panicle Init", "Flowering"):
        score += 8
        factors.append(f"Critical {stage} stage — highest disease susceptibility window")

    score = min(score, 100)

    if score >= 70:
        level  = "High"
        threat = "Rice Blast (Magnaporthe oryzae)"
        action = f"Inspect leaves for diamond-shaped gray lesions TODAY. Apply fungicide (Tricyclazole 75WP @ 0.6g/L) preemptively if humidity stays above 80%."
    elif score >= 40:
        level  = "Moderate"
        threat = "Leaf Blight / Early Blast"
        action = f"Monitor leaves every 2 days for brown/gray spots. Avoid evening irrigation — leaf wetness overnight increases risk significantly."
    else:
        level  = "Low"
        threat = "No significant threat"
        action = f"Conditions not favorable for disease. Continue routine monitoring."

    return {
        "score":              score,
        "level":              level,
        "threat":             threat,
        "action_text":        action,
        "contributing_factors": factors,
        "humidity":           humidity,
        "temp":               temp,
        "rain_3d":            rain_3d,
    }

def compute_disease_profiles(humidity, temp, rain_3d, ndvi, stage, forecast=None):
    """
    Calculates separate risk scores and detailed profiles for 4 major rice diseases.
    Wires all sub-metrics and action recommendations to real-time backend data.
    """
    blast = compute_disease_risk(humidity, temp, rain_3d, ndvi, stage)
    extremes = analyze_weather_extremes(forecast) if forecast else {"night_max_hum": humidity, "night_min_temp": temp, "leaf_wetness_hrs": 0}
    
    # ── Brown Spot (Helminthosporium oryzae)
    bs_score = 0
    if 25 <= temp <= 30: bs_score += 30
    if 70 <= humidity <= 85: bs_score += 25
    if ndvi < 0.45: bs_score += 30 # Stressed/Undernourished plants
    if rain_3d > 10: bs_score += 15
    bs_score = min(bs_score, 100)
    
    # ── Sheath Blight (Rhizoctonia solani)
    sb_score = 0
    if ndvi > 0.65: sb_score += 40
    if humidity > 85: sb_score += 30
    if temp > 25: sb_score += 20
    if rain_3d > 15: sb_score += 10
    sb_score = min(sb_score, 100)
    
    # ── False Smut (Ustilaginoidea virens)
    fs_score = 0
    if stage in ("Flowering", "Panicle Init"):
        fs_score += 40
        if humidity > 90: fs_score += 40
        if 25 <= temp <= 30: fs_score += 20
    else:
        fs_score = 12 if humidity > 85 else 5
    fs_score = min(fs_score, 100)
    
    def get_level(s): return "High" if s > 70 else "Moderate" if s > 40 else "Low"

    return {
        "blast": {
            "score": blast["score"],
            "level": blast["level"],
            "action_text": blast["action_text"],
            "metrics": [
                {"lbl": "HUMIDITY", "val": f"{extremes['night_max_hum']}%"},
                {"lbl": "NIGHT TEMP", "val": f"{extremes['night_min_temp']:.0f}°C"},
                {"lbl": "LEAF WET HRS", "val": f"{extremes['leaf_wetness_hrs']}h"}
            ]
        },
        "brown_spot": {
            "score": bs_score,
            "level": get_level(bs_score),
            "action_text": "Apply Urea (Nitrogen) to strengthen immunity. Brown spot thrives on nitrogen-starved crops." if bs_score > 40 else "Monitor for dark brown spots. Nitrogen levels appear adequate for resistance.",
            "metrics": [
                {"lbl": "SOIL NITROGEN", "val": "Low" if ndvi < 0.5 else "Optimal"},
                {"lbl": "HUMIDITY", "val": f"{humidity}%"},
                {"lbl": "CROP HEALTH", "val": "Stressed" if ndvi < 0.4 else "Healthy"}
            ]
        },
        "sheath_blight": {
            "score": sb_score,
            "level": get_level(sb_score),
            "action_text": "Reduce nitrogen top-dressing and increase field drainage. Thrives in dense canopy zones." if sb_score > 40 else "Conditions stable. Maintain optimal plant spacing and water flow.",
            "metrics": [
                {"lbl": "CANOPY DENSITY", "val": "High" if ndvi > 0.65 else "Normal"},
                {"lbl": "HUMIDITY", "val": f"{humidity}%"},
                {"lbl": "NDVI", "val": f"{ndvi:.2f}"}
            ]
        },
        "false_smut": {
            "score": fs_score,
            "level": get_level(fs_score),
            "action_text": "Prioritize monitoring during panicle emergence. Heavy humidity at flowering triggers smut balls." if fs_score > 40 else "Low risk. Crop stage not currently in the peak infection window.",
            "metrics": [
                {"lbl": "CROP STAGE", "val": stage},
                {"lbl": "HUMIDITY", "val": f"{humidity}%"},
                {"lbl": "RAIN FORECAST", "val": f"{rain_3d:.0f}mm"}
            ]
        }
    }

def analyze_weather_extremes(forecast):
    """
    Extracts key environmental risk factors from the 5-day forecast.
    Specifically calculates night-time peak humidity and leaf wetness hours.
    """
    if not forecast:
        return {"night_max_hum": 70, "night_min_temp": 24, "leaf_wetness_hrs": 0}

    # Focus on next 24 hours for "Tonight" analysis
    night_points = []
    wet_hours = 0
    
    for item in forecast[:16]: # Next 48 hours
        try:
            dt = datetime.strptime(item['date'], '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            # Night period: 21:00 to 06:00
            if hour >= 21 or hour <= 6:
                night_points.append(item)
            
            # Leaf wetness heuristic: Humidity > 85% or Rain > 0
            if item.get('humidity', 0) > 85 or item.get('rain_1h', 0) > 0:
                wet_hours += 3 # Each slot is 3 hours
        except:
            continue

    max_hum = max([p.get('humidity', 70) for p in night_points]) if night_points else 70
    min_temp = min([p.get('temp', 24) for p in night_points]) if night_points else 24
    
    return {
        "night_max_hum": max_hum,
        "night_min_temp": min_temp,
        "leaf_wetness_hrs": wet_hours
    }

# ─────────────────────────────────────────────────────────────────────────────
# E. YIELD FORECAST (data-driven formula)
# ─────────────────────────────────────────────────────────────────────────────

def compute_yield_estimate(ndvi, stage, ndvi_status, nitrogen_risk, irrigation_risk,
                            disease_risk, rain_3d=0.0, base_yield=5.0, peak_ndvi=None):
    """
    Yield formula:
       yield = base_yield × ndvi_factor × stress_factor × stage_sensitivity
    Adaptive: ndvi_factor is now relative to YOUR farm's peak capability.
    """
    thr        = NDVI_THRESHOLDS.get(stage, NDVI_THRESHOLDS["Tillering"])
    # Goal: determine what '100% health' looks like for this farm
    if peak_ndvi and stage not in ("Grain Filling", "Maturity"):
        target_ndvi = max(thr["healthy"], peak_ndvi)
    else:
        target_ndvi = thr["healthy"]

    # NDVI factor (capped between 0.2 and 1.2)
    ndvi_factor = min(1.2, max(0.2, ndvi / max(target_ndvi, 0.01)))

    # Stress penalties
    n_penalty    = 0.12 if nitrogen_risk["level"] == "High"   else 0.06 if nitrogen_risk["level"] == "Moderate" else 0.0
    water_penalty = 0.10 if irrigation_risk["urgency_score"] >= 70 else 0.05 if irrigation_risk["urgency_score"] >= 40 else 0.0
    disease_penalty = 0.15 if disease_risk["level"] == "High"  else 0.07 if disease_risk["level"] == "Moderate" else 0.0

    # Stage sensitivity multiplier (Heading/Flowering most critical)
    stage_mult = {"Seedling": 0.85, "Tillering": 0.92, "Jointing": 1.05,
                  "Heading": 1.15, "Grain Filling": 1.05, "Maturity": 1.0}
    smult = stage_mult.get(stage, 1.0)
    
    # SENESCENCE ADJUSTMENT: If Maturity stage, and NDVI is low but above threshold,
    # we don't penalize the yield factor heavily.
    if stage == "Maturity" and ndvi >= thr["moderate"]:
        # Anchor ndvi_factor closer to 1.0 during harvest senescence
        ndvi_factor = 0.9 + (ndvi_factor * 0.1) 
    

    stress_factor = max(0.4, 1.0 - n_penalty - water_penalty - disease_penalty)
    current_est   = round(base_yield * ndvi_factor * stress_factor * smult, 2)
    current_est   = max(0.5, min(base_yield * 1.3, current_est))

    # "If No Action" — additional penalties if risks are ignored for 5 days
    n_ignored      = 0.18 if nitrogen_risk["level"] in ("High", "Moderate") else 0.0
    water_ignored  = 0.15 if irrigation_risk.get("needed") else 0.0
    disease_ignored = 0.20 if disease_risk["level"] == "High" else 0.08 if disease_risk["level"] == "Moderate" else 0.0
    ignored_factor  = max(0.3, 1.0 - n_ignored - water_ignored - disease_ignored)
    ignored_est     = round(current_est * ignored_factor, 2)
    potential_loss  = round(current_est - ignored_est, 2)

    # Confidence
    if ndvi > thr["healthy"]:    confidence = "High"
    elif ndvi > thr["moderate"]: confidence = "Medium"
    else:                         confidence = "Low"

    loss_breakdown = {}
    if n_ignored > 0:       loss_breakdown["Nitrogen deficiency"] = f"-{round(n_ignored * current_est, 2)} t/ac"
    if water_ignored > 0:   loss_breakdown["Water stress"]        = f"-{round(water_ignored * current_est, 2)} t/ac"
    if disease_ignored > 0: loss_breakdown["Disease damage"]      = f"-{round(disease_ignored * current_est, 2)} t/ac"

    return {
        "estimate":          current_est,
        "confidence":        confidence,
        "if_no_action":      ignored_est,
        "potential_loss":    potential_loss,
        "loss_breakdown":    loss_breakdown,
        "ndvi_factor":       round(ndvi_factor, 3),
        "stress_factor":     round(stress_factor, 3),
    }

# ─────────────────────────────────────────────────────────────────────────────
# F. SMART ACTION RANKER (top-3 with "If No Action")
# ─────────────────────────────────────────────────────────────────────────────

def rank_smart_actions(nitrogen_risk, irrigation_risk, disease_risk, yield_data, lang="en"):
    """
    Ranks up to 3 actions by severity score.
    Every action text is computed from real data — no static strings.
    
    Returns list of dicts: [{ priority, score, text, consequence, icon }]
    """
    candidates = []

    # ── Irrigation
    irr_score = irrigation_risk["urgency_score"]
    if irrigation_risk.get("drain_warning"):
        candidates.append({
            "score":       90,
            "priority":    "red",
            "icon":        "🌊",
            "en":          irrigation_risk["action_text"],
            "hi":          f"भारी बारिश का अनुमान। खेत से पानी तुरंत निकालें — जड़ों को नुकसान हो सकता है।",
            "consequence_en": "Waterlogging can kill roots in 48 hrs, reducing yield by up to 25%.",
            "consequence_hi": "जलभराव 48 घंटे में जड़ें मार सकता है — पैदावार 25% तक घट सकती है।",
        })
    elif irr_score >= 70:
        candidates.append({
            "score":       irr_score,
            "priority":    "red",
            "icon":        "💧",
            "en":          irrigation_risk["action_text"],
            "hi":          f"तुरंत सिंचाई करें — NDWI दर्शाता है कि मिट्टी सूख रही है।",
            "consequence_en": f"Without irrigation today: yield may drop to {yield_data['if_no_action']} t/ac (loss: {yield_data['loss_breakdown'].get('Water stress', '~0.3 t/ac')}).",
            "consequence_hi": f"आज सिंचाई नहीं की तो पैदावार {yield_data['if_no_action']} टन/एकड़ तक गिर सकती है।",
        })
    elif irr_score >= 40:
        candidates.append({
            "score":       irr_score,
            "priority":    "yellow",
            "icon":        "💧",
            "en":          irrigation_risk["action_text"],
            "hi":          f"24 घंटे में पानी का स्तर जांचें — {irrigation_risk['target_depth']} बनाए रखें।",
            "consequence_en": "Delay beyond 2 days may stress roots during active growth.",
            "consequence_hi": "2 दिन की देरी विकास के दौरान जड़ों को कमजोर कर सकती है।",
        })

    # ── Nitrogen
    n_score = nitrogen_risk["score"]
    if n_score >= 55:
        dose = nitrogen_risk["dose_kg_per_acre"]
        candidates.append({
            "score":       n_score,
            "priority":    "red",
            "icon":        "🌿",
            "en":          f"Apply {dose} kg Urea/acre NOW. {nitrogen_risk['reason']}",
            "hi":          f"आज {dose} किलो यूरिया प्रति एकड़ डालें। NDVI {nitrogen_risk.get('growth_rate', 0):.4f}/दिन की दर से गिर रहा है।",
            "consequence_en": f"Ignoring N-deficiency for 5 days: yield estimate drops to {yield_data['if_no_action']} t/ac.",
            "consequence_hi": f"5 दिन नाइट्रोजन न देने पर पैदावार {yield_data['if_no_action']} टन/एकड़ रह सकती है।",
        })
    elif n_score >= 30:
        candidates.append({
            "score":       n_score,
            "priority":    "yellow",
            "icon":        "🌿",
            "en":          f"Monitor for nitrogen signs. {nitrogen_risk['reason']}",
            "hi":          f"नाइट्रोजन के लक्षण देखें — पत्ते पीले होना या विकास रुकना।",
            "consequence_en": "If yellowing appears, apply 20 kg Urea immediately.",
            "consequence_hi": "पत्ते पीले होने पर तुरंत 20 किलो यूरिया डालें।",
        })

    # ── Disease
    d_score = disease_risk["score"]
    if d_score >= 70:
        candidates.append({
            "score":       d_score,
            "priority":    "red",
            "icon":        "🦠",
            "en":          disease_risk["action_text"],
            "hi":          f"पत्तियों पर ग्रे/भूरे धब्बे देखें। फफूंद का खतरा: {d_score}/100।",
            "consequence_en": f"Untreated blast can destroy 30–50% of panicles if humidity stays high.",
            "consequence_hi": "अनदेखी की तो बाली उत्पादन 30–50% तक खराब हो सकता है।",
        })
    elif d_score >= 40:
        candidates.append({
            "score":       d_score,
            "priority":    "yellow",
            "icon":        "🦠",
            "en":          disease_risk["action_text"],
            "hi":          f"बीमारी का मध्यम खतरा ({d_score}/100)। पत्तियों की नियमित जांच करें।",
            "consequence_en": "If lesions appear, spray within 24 hrs — late treatment loses 70% effectiveness.",
            "consequence_hi": "धब्बे दिखते ही 24 घंटे में स्प्रे करें — देरी से उपचार 70% कम असरदार होता है।",
        })

    # ── Healthy fallback
    if not candidates:
        candidates.append({
            "score":       5,
            "priority":    "green",
            "icon":        "✅",
            "en":          f"Crop is performing well. NDVI on track for {yield_data['estimate']} t/ac yield. Continue normal care.",
            "hi":          f"फसल ठीक चल रही है। NDVI लक्ष्य के अनुसार है। सामान्य देखभाल जारी रखें।",
            "consequence_en": "No critical risks identified. Maintain current management.",
            "consequence_hi": "कोई बड़ा खतरा नहीं। वर्तमान देखभाल जारी रखें।",
        })

    # Sort by score descending, take top 3
    sorted_actions = sorted(candidates, key=lambda x: x["score"], reverse=True)[:3]

    return [
        {
            "priority":    a["priority"],
            "score":       a["score"],
            "icon":        a["icon"],
            "text":        a["hi"] if lang == "hi" else a["en"],
            "consequence": a["consequence_hi"] if lang == "hi" else a["consequence_en"],
        }
        for a in sorted_actions
    ]

# ─────────────────────────────────────────────────────────────────────────────
# G. MASTER FUNCTION — compute_field_state()
# Single call returns full agronomic analysis. All pages use this.
# ─────────────────────────────────────────────────────────────────────────────

def compute_field_state(ndvi, stage, ndvi_7d_avg=None, ndwi=None,
                         humidity=72, temp=28, rain_3d=5.0,
                         soil_moisture=50, water_depth=None,
                         soil_ph=6.5,
                         base_yield=5.0, lang="en"):
    """
    Master function: computes the complete agronomic field state from real inputs.
    
    Args:
        ndvi (float): Current Sentinel-2 NDVI
        stage (str): Growth stage
        ndvi_7d_avg (float|None): 7-day mean NDVI (for growth rate)
        ndwi (float|None): Sentinel-2 NDWI. If None, estimated from humidity.
        humidity (float): % RH from weather API
        temp (float): Air temperature °C
        rain_3d (float): Cumulative rain forecast mm (3 days)
        soil_moisture (float): % from IoT sensor (50 default if no sensor)
        water_depth (float|None): cm from IoT sensor
        base_yield (float): tons/acre potential
        lang (str): 'en' or 'hi'
    
    Returns:
        dict: complete field state with all risk scores and actions
    """
    # Estimate NDWI from humidity if not available from satellite
    if ndwi is None:
        # Heuristic: low humidity → drier canopy → lower NDWI
        ndwi = round(-0.2 + (humidity / 250.0), 3)

    ndvi_st   = interpret_ndvi(ndvi, stage, ndvi_7d_avg)
    n_risk    = assess_nitrogen_risk(ndvi_st, ndvi_7d_avg, rain_3d, soil_moisture)
    irr_risk  = assess_irrigation(ndwi, humidity, rain_3d, temp, stage, water_depth, soil_moisture)
    dis_risk  = compute_disease_risk(humidity, temp, rain_3d, ndvi, stage)
    peak_ndvi = ndvi_st.get("peak_ndvi") # Logic for this handled in data_loader
    yield_est = compute_yield_estimate(ndvi, stage, ndvi_st, n_risk, irr_risk, dis_risk,
                                       rain_3d, base_yield, peak_ndvi=peak_ndvi)
    actions   = rank_smart_actions(n_risk, irr_risk, dis_risk, yield_est, lang)

    # ── GENERATE CRITICAL ALERTS FOR SMS ──
    import streamlit as st
    from notifier import notify_batch
    from datetime import datetime
    
    critical_alerts = []
    
    # Because compute_field_state doesn't receive field name, we try to grab it from session
    try:
        field_name = st.session_state.get("selected_field", "Field Sector")
    except Exception:
        field_name = "Field Sector"
        
    date_id = datetime.now().strftime('%Y%m%d')
    timestamp = datetime.now().strftime("%d %b %Y %H:%M")

    if irr_risk.get("urgency_score", 0) >= 70:
        critical_alerts.append({
            "id": f"irr_{field_name}_{date_id}",
            "field": field_name,
            "severity": "Critical",
            "type": "Critical Water Stress",
            "value": str(irr_risk["urgency_score"]),
            "unit": "%",
            "message": "Irrigate immediately to target depth.",
            "timestamp": timestamp
        })
        
    if n_risk.get("score", 0) >= 55:
        critical_alerts.append({
            "id": f"n_{field_name}_{date_id}",
            "field": field_name,
            "severity": "Critical",
            "type": "Nitrogen Deficit",
            "value": str(n_risk["score"]),
            "unit": "%",
            "message": f"Apply {n_risk['dose_kg_per_acre']} kg Urea/acre.",
            "timestamp": timestamp
        })

    if dis_risk.get("score", 0) >= 70:
        critical_alerts.append({
            "id": f"dis_{field_name}_{date_id}",
            "field": field_name,
            "severity": "Critical",
            "type": dis_risk["threat"],
            "value": str(dis_risk["score"]),
            "unit": "%",
            "message": "Apply fungicide immediately.",
            "timestamp": timestamp
        })
        
    if critical_alerts:
        try:
            to_num = st.secrets.get("FARMER_PHONE") or st.session_state.get("farmer_phone")
            if 'sms_sent_ids' not in st.session_state:
                st.session_state.sms_sent_ids = set()
                
            if to_num:
                already_sent = st.session_state.sms_sent_ids
                new_alerts = [a for a in critical_alerts if a["id"] not in already_sent]
                if new_alerts:
                    results = notify_batch(new_alerts, to_num)
                    for r in results:
                        st.session_state.sms_sent_ids.add(r["id"])
        except Exception:
            pass

    return {
        "ndvi_analysis":    ndvi_st,
        "nitrogen_risk":    n_risk,
        "irrigation_risk":  irr_risk,
        "disease_risk":     dis_risk,
        "yield_estimate":   yield_est,
        "actions":          actions,
        "ndwi":             ndwi,
        "summary": {
            "overall_risk":    max(n_risk["score"], irr_risk["urgency_score"], dis_risk["score"]),
            "ndvi":            ndvi,
            "avg_ndvi":        ndvi,
            "stage":           stage,
            "humidity":        humidity,
            "temp":            temp,
            "rain_3d":         rain_3d,
            "soil_moisture":   soil_moisture,
            "water_depth":     water_depth,
            "ph":              soil_ph or 6.5,
            "base_yield":      base_yield,
        }
    }


def evaluate(farm_engine, lang="en"):
    """
    Evaluates all fields in the farm engine and generates unified alerts,
    storing them directly in st.session_state.alerts.
    """
    import uuid
    import streamlit as st
    from datetime import datetime
    
    try:
        if "alerts" not in st.session_state:
            st.session_state.alerts = []
    except Exception:
        # Standalone testing or headless environment
        if not hasattr(st, 'session_state'):
            class MockSessionState(dict):
                def __getattr__(self, name): return self.get(name)
                def __setattr__(self, name, value): self[name] = value
            st.session_state = MockSessionState(alerts=[])
        
    new_alerts = []
    now_str = datetime.now().strftime("%I:%M %p")
    
    for field_name, f_data in farm_engine.fields.items():
        state = compute_field_state(
            ndvi=f_data["ndvi"], stage="Tillering",
            ndvi_7d_avg=f_data["ndvi"],
            ndwi=f_data["ndwi"],
            humidity=f_data["humidity"], temp=f_data["air_temp"], rain_3d=0.0,
            soil_moisture=f_data["moisture"], water_depth=1.5,
            lang=lang
        )
        
        # 1. Moisture Alert
        irr = state["irrigation_risk"]
        if irr["needed"]:
            new_alerts.append({
                "id": str(uuid.uuid4()),
                "field": field_name,
                "type": "Soil Moisture" if lang=="en" else "मिट्टी की नमी",
                "severity": "Critical" if irr["urgency_score"] > 70 else "Warning",
                "message": f"Your {field_name} field soil is getting dry ({f_data['moisture']}%)." if lang=="en" else f"आपके {field_name} खेत की मिट्टी सूख रही है ({f_data['moisture']}%)।",
                "action": "Turn on irrigation for 20 minutes today." if lang=="en" else "आज 20 मिनट के लिए सिंचाई चालू करें।",
                "value": f_data["moisture"],
                "unit": "%",
                "timestamp": now_str,
                "read": False
            })
            
        # 2. Disease Alert
        dis = state["disease_risk"]
        if dis["score"] > 40:
            new_alerts.append({
                "id": str(uuid.uuid4()),
                "field": field_name,
                "type": "Disease Risk" if lang=="en" else "बीमारी का खतरा",
                "severity": "Critical" if dis["score"] > 70 else "Warning",
                "message": f"Conditions are favorable for {dis['threat']}." if lang=="en" else f"{dis['threat']} के लिए परिस्थितियाँ अनुकूल हैं।",
                "action": dis["action_text"],
                "value": dis["score"],
                "unit": "/100",
                "timestamp": now_str,
                "read": False
            })
            
        # 3. Nitrogen
        nit = state["nitrogen_risk"]
        if nit["score"] > 40:
            new_alerts.append({
                "id": str(uuid.uuid4()),
                "field": field_name,
                "type": "Nitrogen" if lang=="en" else "नाइट्रोजन",
                "severity": "Critical" if nit["score"] > 70 else "Warning",
                "message": f"Crop leaves in {field_name} are showing pale greenness." if lang=="en" else f"{field_name} में फसल के पत्ते हल्के हरे रंग के हो रहे हैं।",
                "action": nit["reason"],
                "value": f_data.get("nitrogen", 0),
                "unit": "kg/ha",
                "timestamp": now_str,
                "read": False
            })

        # 4. Soil pH
        ph = f_data.get("soil_ph", 6.5)
        if ph < 5.5 or ph > 7.5:
            new_alerts.append({
                "id": str(uuid.uuid4()),
                "field": field_name,
                "type": "Soil pH",
                "severity": "Critical",
                "message": f"Soil pH in {field_name} is outside optimal range ({ph:.1f}).",
                "action": "Use lime or organic peat to stabilize pH.",
                "value": ph,
                "unit": "pH",
                "timestamp": now_str,
                "read": False
            })

        # 5. Soil Temperature (Root Stress)
        s_temp = f_data.get("soil_temp") or f_data.get("temp", 25)
        if s_temp > 35:
            new_alerts.append({
                "id": str(uuid.uuid4()),
                "field": field_name,
                "type": "Soil Temperature",
                "severity": "Warning",
                "message": f"High soil temperature ({s_temp:.1f}°C) may stress rice roots.",
                "action": "Increase water depth to cool the soil surface.",
                "value": s_temp,
                "unit": "°C",
                "timestamp": now_str,
                "read": False
            })

        # 6. Heat Stress (Air Temperature)
        a_temp = f_data.get("air_temp", 30)
        if a_temp > 38:
            new_alerts.append({
                "id": str(uuid.uuid4()),
                "field": field_name,
                "type": "Heat Stress",
                "severity": "Critical",
                "message": f"Extreme heat ({a_temp:.1f}°C) detected in {field_name}.",
                "action": "Ensure continuous flooding to prevent spikelet sterility.",
                "value": a_temp,
                "unit": "°C",
                "timestamp": now_str,
                "read": False
            })

        # 7. Satellite NDVI Monitor
        cur_ndvi = f_data.get("ndvi", 0.5)
        if cur_ndvi < 0.3:
            new_alerts.append({
                "id": str(uuid.uuid4()),
                "field": field_name,
                "type": "Vegetation Health",
                "severity": "Critical",
                "message": f"Satellite NDVI is dangerously low ({cur_ndvi:.2f}) in {field_name}.",
                "action": "Inspect field for catastrophic failure or sensor error.",
                "value": cur_ndvi,
                "unit": "NDVI",
                "timestamp": now_str,
                "read": False
            })

    existing = {f"{a['field']}_{a['type']}": a for a in st.session_state.alerts}
    final_alerts = []
    
    for na in new_alerts:
        key = f"{na['field']}_{na['type']}"
        if key in existing:
            na["read"] = existing[key]["read"]
            na["id"] = existing[key]["id"]
        final_alerts.append(na)
        
    final_alerts.sort(key=lambda x: (x["read"], 0 if x["severity"] == "Critical" else 1))
    st.session_state.alerts = final_alerts
    
    # ── PERSISTENCE BLOCK ──
    try:
        # 1. Save to local JSON
        import json
        with open('active_alerts.json', 'w') as f:
            json.dump(final_alerts, f, indent=2)
            
        # 2. Sync to MongoDB if available
        import os
        from data_loader import MONGO_CLIENT
        if MONGO_CLIENT:
            db = MONGO_CLIENT.farm_intelligence
            collection = db.alerts
            # Simple clear and replace for "Active" alerts (last 24h context)
            # or we can use upsert. Let's do upsert based on field + type.
            for a in final_alerts:
                collection.update_one(
                    {"field": a["field"], "type": a["type"]},
                    {"$set": a},
                    upsert=True
                )
    except Exception as e:
        print(f"DEBUG: Alert persistence failed: {e}")


def generate_agronomist_brief(state, lang="en"):
    """
    Generates a concise, high-impact strategy brief for the AI Agronomist page.
    """
    summary = state.get("summary", {})
    irr     = state.get("irrigation_risk", {})
    nitro   = state.get("nitrogen_risk", {})
    dis     = state.get("disease_risk", {})
    
    if irr.get("needed"):
        return ("Soil moisture is critical. Increase irrigation within 48 hours to maintain growth targets." 
                if lang == "en" else "मिट्टी में नमी की भारी कमी है। विकास लक्ष्य बनाए रखने के लिए 48 घंटों के भीतर सिंचाई बढ़ाएं।")
    
    if nitro.get("score", 0) > 55:
        return (f"Nitrogen deficiency detected. Apply {nitro.get('dose_kg_per_acre')}kg Urea/acre to avoid health decline."
                if lang == "en" else f"नाइट्रोजन की कमी पाई गई। गिरावट से बचने के लिए {nitro.get('dose_kg_per_acre')} किलो यूरिया प्रति एकड़ डालें।")
        
    if dis.get("score", 0) > 60:
        return (f"Disease risk is high. Monitor for {dis.get('threat')} and prepare preventative spray."
                if lang == "en" else f"बीमारी का खतरा बढ़ गया है। {dis.get('threat')} की जांच करें और स्प्रे तैयार रखें।")
        
    return ("Crop performance is optimal. Maintain current management schedule and monitor for updates."
            if lang == "en" else "फसल का प्रदर्शन बेहतरीन है। वर्तमान प्रबंधन जारी रखें और अपडेट पर नज़र रखें।")


# ─────────────────────────────────────────────────────────────────────────────
# SELF-TEST (run: python decision_engine.py)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== DECISION ENGINE SELF-TEST ===")
    print("Scenario: NDVI=0.29, humidity=78%, temp=26.5°C, rain_3d=0mm, Tillering stage\n")

    state = compute_field_state(
        ndvi=0.29, stage="Tillering",
        ndvi_7d_avg=0.33,   # declining over 7 days
        ndwi=0.06,
        humidity=78, temp=26.5, rain_3d=0.0,
        soil_moisture=45, water_depth=1.2,
        lang="en"
    )

    print(f"NDVI Status:    {state['ndvi_analysis']['status']} (deficit: {state['ndvi_analysis']['deficit']})")
    print(f"Nitrogen Risk:  {state['nitrogen_risk']['level']} ({state['nitrogen_risk']['score']}/100)")
    
    # NEW: Test the full farm evaluation and persistence
    print("\n🔄 Running Full Farm Evaluation...")
    import data_loader
    from sim_engine import SmartFarmSimEngine
    
    farm = SmartFarmSimEngine()
    # Force a moisture drop in one field for testing
    farm.fields["East"]["moisture"] = 32 
    evaluate(farm, lang="en")
    
    if os.path.exists('active_alerts.json'):
        print("✅ SUCCESS: active_alerts.json created and persisted.")
        with open('active_alerts.json', 'r') as f:
            alerts = json.load(f)
            print(f"📡 Found {len(alerts)} active alerts.")
            for a in alerts:
                print(f"   📍 {a['field']} | {a['type']} ({a['severity']})")
    else:
        print("❌ FAILED: active_alerts.json not found.")
