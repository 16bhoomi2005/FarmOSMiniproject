import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import pandas as pd
from datetime import datetime
import data_loader as dl
from sim_engine import SmartFarmSimEngine
import plotly.express as px
import numpy as np

lang = setup_page(
    title="Season Report",
    subtitle="End-of-season summary with yield, income, and action plan",
    icon="📋",
    explanation_en="Generate a complete report of how your farm performed this season — health scores, pest threats, fertilizer needs, projected income, and a 4-week to-do plan.",
    explanation_hi="इस सीज़न आपका खेत कैसे प्रदर्शन किया इसकी पूरी रिपोर्ट तैयार करें — स्वास्थ्य स्कोर, कीट खतरे, खाद की ज़रूरत, अनुमानित आय और 4-सप्ताह की योजना।"
)
dl.get_field_sidebar()

# Fetch live state for source verification
weather = dl.load_current_weather()
is_live = "OpenWeather" in weather.get('source', '')
i_source = "Verified Intelligence" if is_live else "Simulation Engine"
i_color = "#34d399" if is_live else "#94a3b8"
last_updated = datetime.now().strftime("%H:%M")

from sim_engine import FIELD_NAMES

# Extract the mandi price logic from Finance Planner implicitly by querying API quickly or hardcoding today's approx value
# Real API check
import requests
@st.cache_data(ttl=3600)
def get_current_mandi_modal():
    try:
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?format=json&limit=50"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            df = pd.DataFrame(res.json()["records"])
            df = df[df['commodity'].str.contains('Paddy|Rice', case=False, na=False)]
            if not df.empty:
                return float(df['modal_price'].iloc[0]) * 10 # per ton
    except Exception:
        pass
    return 22000.0 # simulated fallback (per ton)

current_mandi_price = get_current_mandi_modal()

# ── 1. HEADER ──
st.title("📋 " + ("सीज़न रिपोर्ट जनरेटर" if lang == "hi" else "Season Report Generator"))
st.markdown("Generate a comprehensive end-of-season or mid-season agronomic report for all monitored fields.")

lbl_scope = "रिपोर्ट का दायरा" if lang == "hi" else "Report Scope"
opt_all   = "सभी खेत" if lang == "hi" else "All Fields"
report_scope = st.selectbox(lbl_scope, [opt_all, st.session_state.get("selected_field", "Center")])

lbl_gen = "📄 रिपोर्ट बनाएं" if lang == "hi" else "📄 Generate Report"
if st.button(lbl_gen, type="primary", use_container_width=True):
    
    name_map_rev = {
        "North":  ("उत्तर" if lang == "hi" else "North"),
        "South":  ("दक्षिण" if lang == "hi" else "South"),
        "East":   ("पूर्व" if lang == "hi" else "East"),
        "West":   ("पश्चिम" if lang == "hi" else "West"),
        "Center": ("केंद्र" if lang == "hi" else "Center"),
        "NW":     ("उत्तर-पश्चिम" if lang == "hi" else "North-West"),
        "NE":     ("उत्तर-पूर्व" if lang == "hi" else "North-East"),
        "SW":     ("दक्षिण-पश्चिम" if lang == "hi" else "South-West"),
        "SE":     ("दक्षिण-पूर्व" if lang == "hi" else "South-East")
    }
    
    fields_data = []
    total_yield = 0.0
    critical_issues = []
    pest_threats = []
    
    # Fetch real field analysis
    sectors = dl.get_sector_analysis()
    
    for f_key in FIELD_NAMES:
        mapped_name = name_map_rev.get(f_key, f_key)
        if report_scope != opt_all and mapped_name != report_scope:
            continue
            
        # Get live intelligence for this specific sector
        f_intel = dl.get_field_intelligence(lang=lang, sector_name=f_key)
        summary = f_intel["summary"]
        health = summary["ndvi"] * 100
        total_yield += f_intel["yield_estimate"]["estimate"]
        
        status = ("स्वस्थ" if lang == "hi" else "Healthy") if health >= 75 else ("मध्यम" if lang == "hi" else "Moderate") if health >= 50 else ("गंभीर" if lang == "hi" else "Critical")
        
        fields_data.append({
            "खेत" if lang == "hi" else "Field": mapped_name,
            "स्वास्थ्य स्कोर" if lang == "hi" else "Health Score": f"{health:.1f}",
            "हरियाली" if lang == "hi" else "Crop Greenness": f"{summary['ndvi']:.2f}",
            "उपज (टन/एकड़)" if lang == "hi" else "Yield (t/ac)": f"{f_intel['yield_estimate']['estimate']:.2f}",
            "सबसे बड़ा खतरा" if lang == "hi" else "Top Risk": f_intel["disease_risk"].get("threat", "None"),
            "स्थिति" if lang == "hi" else "Status": status
        })
        
        if health < 50:
            anomaly = "पानी की कमी" if summary["soil_moisture"] < 40 else "बीमारी का खतरा" if f_intel["disease_risk"]["score"] > 60 else "कम हरियाली"
            if lang == "en":
                anomaly = "Low Moisture" if summary["soil_moisture"] < 40 else "High Pest Risk" if f_intel["disease_risk"]["score"] > 60 else "Low Greenness"
                
            fix = ("सिंचाई करें" if lang == "hi" else "Irrigate field") if "पानी" in anomaly or "Moisture" in anomaly else \
                  (f"{f_intel['disease_risk']['threat']} उपचार" if lang == "hi" else f"Apply medicine for {f_intel['disease_risk']['threat']}") if "खतरा" in anomaly or "Pest" in anomaly else \
                  ("यूरिया खाद" if lang == "hi" else "Apply Urea")
                  
            critical_issues.append({"Field": mapped_name, "Anomaly": anomaly, "Fix": fix})
            
        pest_threats.append({
            "खेत" if lang == "hi" else "Field": mapped_name, 
            "खतरा" if lang == "hi" else "Threat": f_intel["disease_risk"].get("threat", "None"), 
            "जोखिम" if lang == "hi" else "Risk Level": f"{f_intel['disease_risk']['score']:.1f}/100", 
            "क्या करें" if lang == "hi" else "Action": f_intel["disease_risk"]["action_text"],
            "_raw_score": f_intel["disease_risk"]["score"]
        })
        
    df_summary = pd.DataFrame(fields_data)
    avg_health = np.mean([float(x.get("Health Score", x.get("स्वास्थ्य स्कोर", 0))) for x in fields_data]) if fields_data else 0.0
    n_critical = len([x for x in fields_data if x.get("Status", x.get("स्थिति")) in ("Critical", "गंभीर")])
    farm_name = "स्मार्ट फार्म" if lang == "hi" else "Smart Farm"
    
    # ── SECTION 1: EXECUTIVE SUMMARY ──
    farm_engine = st.session_state.farm_sim
    curr_week = farm_engine.current_week
    st.header("1. " + ("संक्षिप्त रिपोर्ट" if lang == "hi" else "Executive Summary"))
    if lang == "hi":
        summary_text = (f"सप्ताह {curr_week} तक, **{farm_name}** का औसत स्वास्थ्य **{avg_health:.1f}%** है। "
                        f"**{n_critical} खेतों** पर तुरंत ध्यान देने की आवश्यकता है। अनुमानित कुल उपज **{total_yield:.2f} टन** है।")
        txt_report = f"स्मार्ट फार्म सीज़न रिपोर्ट (सप्ताह {curr_week})\n"
        txt_report += "="*40 + "\n\n1. संक्षिप्त रिपोर्ट\n"
        txt_report += f"औसत स्वास्थ्य: {avg_health:.1f}%\nखतरे वाले खेत: {n_critical}\nकुल उपज अनुमान: {total_yield:.2f} टन\n\n"
    else:
        summary_text = (f"As of Week {curr_week}, Farm **{farm_name}** is performing at **{avg_health:.1f}% average health**. "
                        f"**{n_critical} fields** require immediate attention. The total projected yield is **{total_yield:.2f} tons**.")
        txt_report = f"SMART FARM SEASON REPORT (Week {curr_week})\n"
        txt_report += "="*40 + "\n\n1. EXECUTIVE SUMMARY\n"
        txt_report += f"Health: {avg_health:.1f}%\nCritical Fields: {n_critical}\nTotal Yield: {total_yield:.2f}t.\n\n"
        
    st.info(summary_text)
    
    # ── SECTION 2: FIELD-BY-FIELD SUMMARY ──
    st.header("2. " + ("सभी खेतों का विवरण" if lang == "hi" else "Field-by-Field Summary"))
    
    if df_summary.empty:
        st.warning("No data found for the selected report scope.")
    else:
        def color_status(val):
            color = '#22c55e' if val in ['Healthy', 'स्वस्थ'] else '#f59e0b' if val in ['Moderate', 'मध्यम'] else '#ef4444'
            return f'background-color: {color}; color: white; font-weight: bold;'
        
        col_status = 'स्थिति' if lang == 'hi' else 'Status'
        # Verification check to avoid KeyError if the column somehow didn't get added
        if col_status in df_summary.columns:
            st.dataframe(df_summary.style.map(color_status, subset=[col_status]), width='stretch')
        else:
            st.dataframe(df_summary, width='stretch')
    
    txt_report += ("2. खेतों का विवरण\n" if lang == "hi" else "2. FIELD SUMMARY\n")
    txt_report += df_summary.to_string(index=False) + ("\n\n" if not df_summary.empty else "No fields selected.\n\n")
    
    # ── SECTION 3: CRITICAL ISSUES ──
    st.header("3. " + ("गंभीर समस्याएं" if lang == "hi" else "Critical Issues"))
    if critical_issues:
        for c in critical_issues:
            warn = f"🔴 **{c['Field']}**: {c['Anomaly']} ➔ **{'सुझाव' if lang=='hi' else 'Fix'}**: {c['Fix']}"
            st.error(warn)
            txt_report += f"- {c['Field']}: {c['Anomaly']} -> {c['Fix']}\n"
    else:
        msg = "✅ कोई गंभीर समस्या नहीं है।" if lang == "hi" else "✅ No critical field issues detected."
        st.success(msg)
        txt_report += msg + "\n"
    txt_report += "\n"
    
    # ── SECTION 4: PEST & DISEASE SUMMARY ──
    st.header("4. " + ("बीमारी और कीट" if lang == "hi" else "Pest & Disease Summary"))
    pest_threats = sorted(pest_threats, key=lambda x: x["_raw_score"], reverse=True)[:3]
    df_pest = pd.DataFrame([{k:v for k,v in x.items() if not k.startswith('_')} for x in pest_threats])
    st.table(df_pest)
    
    txt_report += ("4. बीमारी और कीट (शीर्ष 3)\n" if lang == "hi" else "4. PEST SUMMARY (Top 3)\n")
    txt_report += df_pest.to_string(index=False) + "\n\n"
    
    # ── SECTION 5: 4-WEEK ACTION PLAN ──
    st.header("5. " + ("अगले 4 सप्ताह की योजना" if lang == "hi" else "4-Week Action Plan"))
    action_plan = []
    wk = curr_week
    global_tgt = ("सभी खेत" if lang == "hi" else "All Fields") if report_scope == opt_all else report_scope
    
    lang_wk, lang_act, lang_fld, lang_pri, lang_out = ("सप्ताह", "क्या करें", "खेत", "प्राथमिकता", "नतीजा") if lang == "hi" else ("Week", "Action", "Field", "Priority", "Expected Outcome")

    if lang == "hi":
        action_plan.append({lang_wk: wk + 1, lang_act: "कीट जांच और दवा",        lang_fld: global_tgt, lang_pri: "अधिक",  lang_out: "बीमारी का खतरा कम होगा"})
        action_plan.append({lang_wk: wk + 2, lang_act: "खेत की नमी जांचें",       lang_fld: global_tgt, lang_pri: "मध्यम", lang_out: "नमी बनी रहेगी"})
        action_plan.append({lang_wk: wk + 3, lang_act: "यूरिया खाद डालें",        lang_fld: global_tgt, lang_pri: "कम",    lang_out: "हरियाली और अच्छी फसल होगी"})
        action_plan.append({lang_wk: wk + 4, lang_act: "कटाई की तैयारी",          lang_fld: global_tgt, lang_pri: "मध्यम", lang_out: "फसल सुरक्षित कटेगी"})
    else:
        action_plan.append({lang_wk: wk + 1, lang_act: "Pest Check & Spray",      lang_fld: global_tgt, lang_pri: "High",   lang_out: "Reduce disease risk"})
        action_plan.append({lang_wk: wk + 2, lang_act: "Check Soil Moisture",     lang_fld: global_tgt, lang_pri: "Medium", lang_out: "Keep plants hydrated"})
        action_plan.append({lang_wk: wk + 3, lang_act: "Apply Fertilizer",        lang_fld: global_tgt, lang_pri: "Low",    lang_out: "Boost greenness and yield"})
        action_plan.append({lang_wk: wk + 4, lang_act: "Prepare for Harvest",     lang_fld: global_tgt, lang_pri: "Medium", lang_out: "Ready for cutting"})

    df_action = pd.DataFrame(action_plan)
    st.dataframe(df_action, hide_index=True, width='stretch')
    
    txt_report += ("5. योजना\n" if lang == "hi" else "5. ACTION PLAN\n")
    txt_report += df_action.to_string(index=False) + "\n\n"
    
    # ── SECTION 6: YIELD FORECAST ──
    st.header("6. " + ("उपज और आय का अनुमान" if lang == "hi" else "Yield Forecast & Income"))
    baseline_yield_per_field = 4.5
    baseline = baseline_yield_per_field * len(fields_data)
    diff_pct = ((total_yield / baseline) - 1) * 100 if baseline > 0 else 0
    
    est_rev = total_yield * current_mandi_price
    
    c1, c2, c3 = st.columns(3)
    t_proj = "कुल उपज अनुमान" if lang == "hi" else "Total Yield Projection"
    t_base = "सामान्य उपज" if lang == "hi" else "Normal Yield"
    t_rev  = "अनुमानित आय (रुपये)" if lang == "hi" else "Estimated Income (Rs)"
    v_base = "सामान्य से" if lang == "hi" else "vs normal"

    c1.metric(t_proj, f"{total_yield:.2f} tons", f"{diff_pct:+.1f}% {v_base}")
    c2.metric(t_base, f"{baseline:.2f} tons")
    c3.metric(t_rev, f"₹{est_rev:,.0f}")
    
    txt_report += ("6. उपज और आय\n" if lang == "hi" else "6. YIELD & INCOME\n")
    txt_report += f"{t_proj}: {total_yield:.2f} tons ({diff_pct:+.1f}%)\n"
    txt_report += f"{t_base}: {baseline:.2f} tons\n"
    txt_report += f"{t_rev}: Rs {est_rev:,.0f}\n\n"
    txt_report += "--- END OF REPORT ---\n"
    
    st.markdown("---")
    st.markdown("### 📤 " + ("रिपोर्ट डाउनलोड करें" if lang == "hi" else "Export Options"))
    ec1, ec2, ec3 = st.columns(3)
    
    with ec1:
        csv_data = df_summary.to_csv(index=False).encode('utf-8')
        st.download_button("📥 " + ("CSV डाउनलोड करें" if lang == "hi" else "Download CSV"), data=csv_data, file_name=f"Season_Report_Wk{curr_week}.csv", mime="text/csv", type="primary")
    with ec2:
        st.download_button("📄 " + ("टेक्स्ट (TXT) डाउनलोड करें" if lang == "hi" else "Download TXT"), data=txt_report, file_name=f"Season_Report_Wk{curr_week}.txt", mime="text/plain", type="primary")
    with ec3:
        btn_print = "🖨️ रिपोर्ट प्रिंट करें" if lang == "hi" else "🖨️ Print Report"
        html_btn = f"""
        <button onclick="window.print()" style="background-color:#4F46E5; color:white; border:none; padding:8px 24px; border-radius:8px; font-weight:600; cursor:pointer;">
            {btn_print}
        </button>
        """
        st.components.v1.html(html_btn, height=50)
