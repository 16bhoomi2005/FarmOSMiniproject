"""
Smart Action Center: Ranking Engine
Prioritizes daily actions based on urgency and mission-critical agricultural data.
Hierarchy: Water Stress > Disease/Pest Risk > Nutrient Deficiency > Information Advice.
"""

def translate_phrase(phrase, lang="en"):
    """Helper for ad-hoc technical phrases."""
    if lang == "en": return phrase
    
    mapping = {
        "Maintain 3-5 cm water depth.": "3-5 सेंटीमीटर पानी की गहराई बनाए रखें।",
        "Maintain 5-10 cm water depth.": "5-10 सेंटीमीटर पानी की गहराई बनाए रखें।",
        "Heavy rain expected. Drain field immediately.": "भारी बारिश की संभावना। तुरंत जल निकासी करें।",
        "Fast evaporation! Increase depth to 5 cm.": "तेजी से वाष्पीकरण! गहराई बढ़ाकर 5 सेमी करें।",
        "Fast evaporation! Increase depth to 10 cm.": "तेजी से वाष्पीकरण! गहराई बढ़ाकर 10 सेमी करें।"
    }
    return mapping.get(phrase, phrase)

def rank_actions(data, lang="en"):
    """
    Ranks potential field actions based on multi-source sensor and satellite data.
    
    Args:
        data (dict): Dictionary containing keys like 'ndvi', 'ndvi_trend', 'weather', 
                    'soil_moisture', 'disease_risk', 'nutrient_signals'.
        lang (str): 'en' or 'hi'
    
    Returns:
        list: Top 3 prioritized actions [{ 'priority': 'red', 'text': str }]
    """
    potential_actions = []
    
    # --- 1. WATER & IRRIGATION (URGENT) ---
    soil_moisture = data.get('soil_moisture', 50)
    rain_forecast = data.get('rain_forecast', 0)
    irrig_advice = data.get('irrigation_advice', '')
    
    if "Drain" in irrig_advice or "immediately" in irrig_advice:
        potential_actions.append({
            "urgency": 100,
            "priority": "red",
            "en": irrig_advice,
            "hi": translate_phrase(irrig_advice, lang="hi") # Assuming helper
        })
    elif "Increase" in irrig_advice or "Maintain" in irrig_advice:
        potential_actions.append({
            "urgency": 65,
            "priority": "yellow",
            "en": irrig_advice,
            "hi": translate_phrase(irrig_advice, lang="hi")
        })
    
    if rain_forecast > 40:
        potential_actions.append({
            "urgency": 90,
            "priority": "red",
            "en": "Heavy rain forecast! – Ensure proper drainage in lower patch.",
            "hi": "भारी बारिश का अनुमान! - निचले हिस्से में जल निकासी सुनिश्चित करें।"
        })

    # --- 2. DISEASE & PEST RISK ---
    disease_status = data.get('disease_risk', 'Low')
    pest_risk = data.get('pest_risk', 'Low')
    
    if disease_status == 'High' or pest_risk == 'High':
        potential_actions.append({
            "urgency": 95,
            "priority": "red",
            "en": f"Critical {data.get('threat', 'Disease')} Risk – Inspect leaves for brown spots.",
            "hi": f"गंभीर {data.get('threat_hi', 'बीमारी')} का खतरा - पत्तों पर भूरे धब्बे देखें।"
        })
    elif disease_status == 'Moderate':
        potential_actions.append({
            "urgency": 60,
            "priority": "yellow",
            "en": "Moderate humidity – Watch for signs of rice blast.",
            "hi": "मध्यम उमस - ब्लास्ट (झोंका) के शुरुआती लक्षण देखें।"
        })

    # --- 3. CROP HEALTH & NUTRIENTS ---
    ndvi_trend = data.get('ndvi_trend', 0)
    nutrient_signal = data.get('nutrient_signal', 'Stable')
    
    if ndvi_trend < -15:
        potential_actions.append({
            "urgency": 85,
            "priority": "red",
            "en": "Rapid thinning detected! – Urgent Nitrogen (N) dose suggested.",
            "hi": "फसल तेजी से कमजोर हो रही है! - नाइट्रोजन (N) डालना आवश्यक।"
        })
    elif nutrient_signal == 'Deficient':
        potential_actions.append({
            "urgency": 65,
            "priority": "yellow",
            "en": "Yellow patches detected – Apply 25kg Urea/Acre.",
            "hi": "पीले धब्बे दिखे हैं - प्रति एकड़ 25 किलो यूरिया डालें।"
        })
        
    # --- 4. CALM ADVISOR (GREEN / LOW PRIORITY) ---
    if not potential_actions:
        potential_actions.append({
            "urgency": 10,
            "priority": "green",
            "en": "Crop looks stable. Continue regular monitoring.",
            "hi": "फसल स्वस्थ लग रही है। सामान्य देखभाल जारी रखें।"
        })
    
    # Sort by urgency and take top 3
    sorted_actions = sorted(potential_actions, key=lambda x: x['urgency'], reverse=True)[:3]
    
    # Format for UI
    result = []
    for action in sorted_actions:
        result.append({
            "priority": action['priority'],
            "text": action['hi'] if lang == 'hi' else action['en']
        })
        
    return result
