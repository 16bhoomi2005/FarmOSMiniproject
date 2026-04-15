"""
AI Agronomist Chat Engine
==========================
Real LLM-powered responses with full field context injected into the system prompt.

Priority:
  1. Google Gemini API (if GEMINI_API_KEY set in .env)
  2. Formula-computed specific fallback (references REAL numbers — NOT generic text)

Design rules:
  - Answer ALWAYS cites real field numbers (NDVI, temp, humidity, growth rate)
  - Never says "I'm monitoring your field..." (generic)
  - Never says "check your action center" (evasive)
  - Max 4 sentences, direct, in farmer language
"""

import os
import sys

# Load .env manually
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip())

_load_env()


def _build_system_prompt(ctx: dict, lang: str) -> str:
    """Build a fully context-injected system prompt from real field data."""
    ndvi        = ctx.get("ndvi", 0.5)
    ndvi_7d     = ctx.get("ndvi_7d_avg")
    ndwi        = ctx.get("ndwi", 0.1)
    stage       = ctx.get("stage", "Tillering")
    temp        = ctx.get("temp", 28)
    humidity    = ctx.get("humidity", 72)
    rain_3d     = ctx.get("rain_3d", 5.0)
    soil        = ctx.get("soil_moisture", 50)
    yield_est   = ctx.get("yield_estimate", 4.5)
    yield_loss  = ctx.get("if_no_action_yield", yield_est)
    n_level     = ctx.get("nitrogen_level", "Unknown")
    n_score     = ctx.get("nitrogen_score", 0)
    n_dose      = ctx.get("nitrogen_dose_kg", 0)
    irr_score   = ctx.get("irrigation_score", 0)
    irr_depth   = ctx.get("recommended_depth", "2–5 cm")
    dis_level   = ctx.get("disease_level", "Low")
    dis_score   = ctx.get("disease_score", 0)
    dis_threat  = ctx.get("disease_threat", "None")
    days_harvest = ctx.get("days_to_harvest", 60)

    growth_rate_str = ""
    if ndvi_7d:
        gr = (ndvi - ndvi_7d) / 7.0
        growth_rate_str = f"NDVI 7-day trend: {gr:+.4f} ΔNDVI/day ({'declining' if gr < 0 else 'growing'})\n"

    lang_instruction = "Respond in simple Hindi (Devanagari script)." if lang == "hi" else "Respond in simple English."

    return f"""You are an expert rice agronomist advising a smallholder farmer in Bhandara, Vidarbha, India.

LIVE FIELD DATA (from Sentinel-2 satellite + IoT sensors + OpenWeather):
- Crop: Rice (Paddy) | Growth Stage: {stage} | Days to harvest: {days_harvest}
- NDVI (canopy health): {ndvi:.3f}
{growth_rate_str}- NDWI (water index): {ndwi:.3f}
- Air Temperature: {temp}°C | Humidity: {humidity}% | 3-day rain forecast: {rain_3d:.0f}mm
- Soil Moisture (sensor): {soil}%
- Nitrogen Risk: {n_level} ({n_score}/100){f' → suggest {n_dose} kg Urea/acre' if n_dose > 0 else ''}
- Irrigation Urgency: {irr_score}/100 → recommended depth: {irr_depth}
- Disease Risk: {dis_level} ({dis_score}/100) — Threat: {dis_threat}
- Estimated Yield: {yield_est} t/ac | If risks ignored: {yield_loss} t/ac

YOUR RULES:
1. Always cite the exact numbers above in your answer.
2. Be DIRECT and SPECIFIC — no vague advice like "monitor the field."
3. Give a clear YES/NO recommendation, then explain WHY using the data.
4. Max 4 sentences. Use simple words a farmer can understand.
5. {lang_instruction}
6. Never say "I am monitoring your field" — you are ANSWERING with specific data.
"""


def _formula_response(query: str, ctx: dict, lang: str) -> str:
    """
    Formula-computed specific response when Gemini API is unavailable.
    Uses real field numbers — never static template text.
    """
    q = query.lower()
    ndvi        = ctx.get("ndvi", 0.5)
    stage       = ctx.get("stage", "Tillering")
    temp        = ctx.get("temp", 28)
    humidity    = ctx.get("humidity", 72)
    rain_3d     = ctx.get("rain_3d", 5.0)
    soil        = ctx.get("soil_moisture", 50)
    yield_est   = ctx.get("yield_estimate", 4.5)
    yield_loss  = ctx.get("if_no_action_yield", yield_est)
    n_level     = ctx.get("nitrogen_level", "Low")
    n_dose      = ctx.get("nitrogen_dose_kg", 0)
    n_score     = ctx.get("nitrogen_score", 0)
    irr_score   = ctx.get("irrigation_score", 0)
    irr_depth   = ctx.get("recommended_depth", "2–5 cm")
    dis_level   = ctx.get("disease_level", "Low")
    dis_score   = ctx.get("disease_score", 0)
    dis_threat  = ctx.get("disease_threat", "None")
    days_harvest = ctx.get("days_to_harvest", 60)

    hi = lang == "hi"

    # ── Fertilizer / Nitrogen ───────────────────────────────────────────────
    if any(w in q for w in ["fertilizer", "urea", "nitrogen", "खाद", "यूरिया", "नाइट्रोजन"]):
        if n_level == "High":
            if hi:
                return f"हाँ, तुरंत खाद डालें। आपका NDVI {ndvi:.2f} है जो {stage} अवस्था के लिए कम है और {n_score}/100 नाइट्रोजन तनाव दर्शाता है। आज {n_dose} किलो यूरिया प्रति एकड़ डालें — शाम को, बारिश नहीं है तो। 5 दिन में न डाला तो पैदावार {yield_loss} टन/एकड़ रह सकती है।"
            return f"Yes — apply fertilizer now. Your NDVI is {ndvi:.2f}, below the healthy threshold for {stage} stage, with a nitrogen risk score of {n_score}/100. Apply {n_dose} kg Urea/acre today, preferably in the evening. Without action, yield could drop to {yield_loss} t/ac."
        elif n_level == "Moderate":
            if hi:
                return f"संभव है खाद जरूरी हो। NDVI {ndvi:.2f} थोड़ा कम है ({n_score}/100 नाइट्रोजन स्कोर)। 3 दिन पत्ते देखें — अगर पीले होने लगें तो {n_dose} किलो यूरिया डालें।"
            return f"Possibly — your NDVI {ndvi:.2f} is slightly below target with a nitrogen score of {n_score}/100. Watch leaves for yellowing over the next 3 days. If yellowing appears, apply {n_dose} kg Urea/acre immediately."
        else:
            if hi:
                return f"अभी खाद की जरूरत नहीं है। NDVI {ndvi:.2f} {stage} अवस्था के लिए ठीक है। नाइट्रोजन स्कोर सिर्फ {n_score}/100 है। सामान्य देखभाल जारी रखें।"
            return f"No fertilizer needed right now. Your NDVI {ndvi:.2f} is adequate for {stage} stage, with a nitrogen risk score of only {n_score}/100. Continue normal monitoring and apply if NDVI drops further."

    # ── Water / Irrigation ──────────────────────────────────────────────────
    if any(w in q for w in ["water", "irrigate", "irrigation", "पानी", "सिंचाई", "बारिश", "rain"]):
        if irr_score >= 70:
            if hi:
                return f"हाँ, तुरंत सिंचाई करें। मिट्टी नमी {soil}% और अगले 3 दिन सिर्फ {rain_3d:.0f}mm बारिश का अनुमान है — जड़ों के लिए पर्याप्त नहीं। लक्ष्य {irr_depth} जल स्तर बनाए रखें। आज न किया तो पैदावार {yield_loss} टन/एकड़ तक गिर सकती है।"
            return f"Yes — irrigate immediately. Soil moisture is {soil}% and only {rain_3d:.0f}mm of rain is forecast in 3 days, which is insufficient for paddy roots. Target {irr_depth} water depth. Delaying today risks yield dropping to {yield_loss} t/ac."
        elif irr_score >= 40:
            if hi:
                return f"24 घंटे में जांचें। नमी {soil}% पर ठीक है लेकिन {rain_3d:.0f}mm बारिश के साथ कल तक {irr_depth} स्तर से नीचे जा सकता है।"
            return f"Check within 24 hours. Soil moisture {soil}% is borderline with only {rain_3d:.0f}mm rain forecast. Maintain {irr_depth} water depth — top up if level drops below the minimum."
        elif rain_3d > 30:
            if hi:
                return f"{rain_3d:.0f}mm भारी बारिश का अनुमान है — खेत से पानी निकालने के लिए तैयार रहें। {irr_depth} से ज्यादा पानी जड़ों को नुकसान पहुंचा सकता है।"
            return f"Heavy rain forecast of {rain_3d:.0f}mm — prepare drainage, not irrigation. Keep water depth at {irr_depth} maximum to avoid root damage from waterlogging."
        else:
            if hi:
                return f"अभी सिंचाई की जरूरत नहीं है। मिट्टी नमी {soil}% और {rain_3d:.0f}mm बारिश का अनुमान है जो {stage} अवस्था के लिए पर्याप्त है।"
            return f"No irrigation needed right now. Soil moisture is {soil}% and {rain_3d:.0f}mm rain is forecast, which should be adequate for {stage} stage. Reassess in 2–3 days."

    # ── Disease / Spray ─────────────────────────────────────────────────────
    if any(w in q for w in ["disease", "blast", "fungal", "spray", "बीमारी", "ब्लास्ट", "स्प्रे", "धब्बे"]):
        if dis_level == "High":
            if hi:
                return f"हाँ, बहुत खतरा है — {dis_score}/100 रोग स्कोर। {humidity}% नमी और {temp}°C तापमान {dis_threat} के लिए अनुकूल है। आज पत्तों पर भूरे/ग्रे धब्बे जांचें और Tricyclazole 75WP @ 0.6g/L स्प्रे करें।"
            return f"Yes — high disease risk at {dis_score}/100. Humidity {humidity}% and temperature {temp}°C create ideal conditions for {dis_threat}. Inspect leaves today for gray/brown lesions and apply Tricyclazole 75WP @ 0.6g/L preventively."
        elif dis_level == "Moderate":
            if hi:
                return f"मध्यम बीमारी खतरा ({dis_score}/100)। {humidity}% नमी {dis_threat} को बढ़ावा दे सकती है। हर 2 दिन पत्ते जांचें — धब्बे दिखें तो 24 घंटे में स्प्रे करें।"
            return f"Moderate disease risk ({dis_score}/100). Humidity at {humidity}% can promote {dis_threat}. Check leaves every 2 days — spray within 24 hours if any spots appear."
        else:
            if hi:
                return f"अभी बीमारी का खतरा कम है ({dis_score}/100)। {humidity}% नमी और {temp}°C तापमान पर रोग फैलने की संभावना नहीं। नियमित नज़र रखें।"
            return f"Low disease risk right now ({dis_score}/100). Humidity {humidity}% and temp {temp}°C are not favorable for {dis_threat}. Continue routine monitoring."

    # ── Weak crop / Health ──────────────────────────────────────────────────
    if any(w in q for w in ["weak", "yellow", "pale", "कमजोर", "पीला", "health", "स्वास्थ्य"]):
        from decision_engine import NDVI_THRESHOLDS
        thr = NDVI_THRESHOLDS.get(stage, NDVI_THRESHOLDS["Tillering"])
        deficit = round(thr["healthy"] - ndvi, 3)
        if ndvi < thr["moderate"]:
            if hi:
                return f"हाँ, फसल कमजोर है। NDVI {ndvi:.2f} है जो {stage} अवस्था के लिए न्यूनतम {thr['moderate']:.2f} से भी कम है — यानी {deficit:.2f} की कमी। सबसे पहले {n_dose}kg यूरिया और {irr_depth} पानी सुनिश्चित करें।"
            return f"Yes, the crop is struggling. NDVI {ndvi:.2f} is below even the minimum {thr['moderate']:.2f} for {stage} stage — a deficit of {deficit:.2f}. Priority: apply {n_dose}kg Urea/acre and ensure {irr_depth} water depth immediately."
        elif ndvi < thr["healthy"]:
            if hi:
                return f"फसल थोड़ी कमजोर है — NDVI {ndvi:.2f} है, लक्ष्य {thr['healthy']:.2f}। {n_level} नाइट्रोजन जोखिम है। अगले 5 दिन ध्यान रखें और जरूरत पड़े तो खाद डालें।"
            return f"Crop is slightly below target — NDVI {ndvi:.2f} vs healthy {thr['healthy']:.2f} for {stage}. Nitrogen risk is {n_level}. Monitor over 5 days and apply {n_dose}kg Urea if NDVI continues falling."
        else:
            if hi:
                return f"फसल ठीक दिख रही है — NDVI {ndvi:.2f} {stage} अवस्था के लिए स्वस्थ सीमा में है। नाइट्रोजन और पानी दोनों ठीक हैं।"
            return f"Crop looks healthy — NDVI {ndvi:.2f} is within the healthy range for {stage} stage. Nitrogen and water levels appear adequate based on satellite data."

    # ── Harvest ─────────────────────────────────────────────────────────────
    if any(w in q for w in ["harvest", "कटाई", "ready", "yield", "पैदावार"]):
        if hi:
            return f"आप कटाई से लगभग {days_harvest} दिन दूर हैं। मौजूदा NDVI {ndvi:.2f} और जोखिम स्तर के अनुसार पैदावार {yield_est} टन/एकड़ अनुमानित है। {f'नाइट्रोजन और पानी की देखभाल जारी रखें — लापरवाही से {yield_loss} t/ac तक गिर सकती है।' if yield_loss < yield_est else 'सामान्य देखभाल जारी रखें।'}"
        return f"You are approximately {days_harvest} days from harvest. Based on current NDVI {ndvi:.2f} and risk levels, yield is estimated at {yield_est} t/ac. {'Address nitrogen and water risks now — ignoring them could reduce harvest to ' + str(yield_loss) + ' t/ac.' if yield_loss < yield_est else 'Maintain current management for best results.'}"

    # ── General / Unknown ───────────────────────────────────────────────────
    # Build a specific summary even for general questions
    top_concern = "nitrogen deficiency" if n_level == "High" else \
                  "irrigation" if irr_score >= 60 else \
                  "disease risk" if dis_level == "High" else \
                  "no critical issues"
    if hi:
        top_hi = "नाइट्रोजन की कमी" if n_level == "High" else \
                 "सिंचाई" if irr_score >= 60 else \
                 "रोग का खतरा" if dis_level == "High" else "कोई बड़ी समस्या नहीं"
        return f"अभी आपके खेत का NDVI {ndvi:.2f} है और तापमान {temp}°C, नमी {humidity}% है। सबसे बड़ी चिंता: {top_hi}। पैदावार अनुमान {yield_est} टन/एकड़ है — क्या आप कोई खास विषय पर सलाह चाहते हैं?"
    return f"Your field currently shows NDVI {ndvi:.2f}, temperature {temp}°C, humidity {humidity}%. The top concern is {top_concern}. Estimated yield is {yield_est} t/ac — ask me specifically about fertilizer, water, disease, or harvest for targeted advice."


def get_agronomist_response(query: str, ctx: dict, lang: str = "en") -> str:
    """
    Main entry point. Tries Gemini API first, falls back to formula response.
    
    ctx must have keys from decision_engine.compute_field_state() summary +
    nitrogen_risk, irrigation_risk, disease_risk, yield_estimate.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    if gemini_key and gemini_key not in ("", "your_gemini_key_here"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model    = genai.GenerativeModel("gemini-2.0-flash")
            sys_prompt = _build_system_prompt(ctx, lang)
            response = model.generate_content(
                f"{sys_prompt}\n\nFarmer's question: {query}"
            )
            answer = response.text.strip()
            if answer:
                return answer
        except Exception as e:
            print(f"⚠️ Gemini API error: {e}. Using formula fallback.")

    # Formula-computed specific fallback
    return _formula_response(query, ctx, lang)
