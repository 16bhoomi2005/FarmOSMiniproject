import streamlit as st
import sys, os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page
import data_loader as dl

lang = setup_page(
    title="Crop Health",
    subtitle="How your rice crop is growing right now",
    icon="📊",
    explanation_en="This page shows how strong and healthy your crop is across all plots. A score above 70 means you're in good shape. Below 45 means you need to act today.",
    explanation_hi="यह पृष्ठ दिखाता है कि आपकी फसल सभी क्षेत्रों में कितनी मजबूत और स्वस्थ है। 70 से ऊपर का स्कोर अच्छी स्थिति को दर्शाता है। 45 से नीचे का मतलब है आज कार्रवाई की ज़रूरत है।"
)
dl.get_field_sidebar()
is_hi = (lang == 'hi')

# Live Source Retrieval
sectors = dl.get_sector_analysis(lang=lang)

# Source Verification Badges
iot_source = st.session_state.get('data_source_verification', 'Simulated')
sat_source = st.session_state.get('sat_source_verification', 'Regional')
iot_color = "#34d399" if "Verified" in iot_source else "#94a3b8"
sat_color = "#34d399" if "Sentinel-2" in sat_source else "#E8A020"

# Calculate Metrics from LIVE sectors
if sectors and len(sectors) > 0:
    # Scale NDVI 0-1 to 0-100 for "score" if needed, or use existing labels
    field_scores = []
    for s_data in sectors.values():
        val = s_data.get('ndvi', 0.6) * 100
        field_scores.append(val)
        
    avg_h = sum(field_scores) / len(field_scores)
    fields_good = sum(1 for s in sectors.values() if s['label'] == 'Healthy')
    fields_caution = sum(1 for s in sectors.values() if s['label'] in ('Watch', 'Stable', 'Review'))
    fields_critical = sum(1 for s in sectors.values() if s['label'] == 'Action')
    total_fields = len(sectors)
else:
    # Fallback only
    farm_data = st.session_state.farm_sim.fields
    fields_good = sum(1 for f in farm_data.values() if f["health_score"] >= 70)
    fields_caution = sum(1 for f in farm_data.values() if 45 <= f["health_score"] < 70)
    fields_critical = sum(1 for f in farm_data.values() if f["health_score"] < 45)
    avg_h = sum(f["health_score"] for f in farm_data.values()) / len(farm_data)
    total_fields = len(farm_data)

now_str = datetime.now().strftime("%d %b, %H:%M")

# Translation mappings
t_title = "फसल स्वास्थ्य — धान 2026" if is_hi else "Crop Health — Rice 2026"
t_monitored = f"{total_fields} {'खेत की निगरानी' if is_hi else 'fields monitored'}"
t_attention = f"{fields_caution} {'को ध्यान देने की आवश्यकता है' if is_hi else 'need attention'}"
t_updated = f"{'अद्यतन' if is_hi else 'Updated'} {now_str}"

t_farm_score_lbl = "खेत का स्वास्थ्य स्कोर" if is_hi else "Farm health score"
t_good_lbl = "अच्छी स्थिति में खेत" if is_hi else "Fields in good shape"
t_action_lbl = "कार्यवाही आवश्यक खेत" if is_hi else "Fields need action"
t_crit_lbl = "गंभीर खेत" if is_hi else "Critical fields"

t_above_70 = "70 से ऊपर का स्कोर" if is_hi else "Score above 70"
t_mid_score = "स्कोर 45 – 70" if is_hi else "Score 45 – 70"
t_below_45 = "45 से नीचे का स्कोर" if is_hi else "Score below 45"

t_banner = f"⚠️ 70 से ऊपर = अच्छी स्थिति · 45 से नीचे = आज ही काम करें · इस हफ्ते {fields_caution} खेत सावधानी क्षेत्र में हैं" if is_hi else f"⚠️ Score above 70 = good shape · Below 45 = act today · {fields_caution} fields in the caution zone this week"
t_each_score = "प्रत्येक खेत का स्कोर" if is_hi else "Each field's score"

# COLORS
bg_dark = "#1C1A1A"  # Deep charcoal page bg
card_bg = "#262626"  # Card background
green_c = "#4ADE80"
green_fill = "#dcfce7"
amber_c = "#F59E0B"
amber_fill = "#fef3c7"
red_c = "#EF4444"
red_fill = "#fee2e2"
text_w = "#F5F5F5"
text_g = "#A3A3A3"

w_color = "#34d399" if "Sentinel-2" in sat_source else "#E8A020"
last_updated = datetime.now().strftime("%H:%M")

# --- HEADER strip ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:15px;">
    <div>
        <div style="color:#86A789; font-size:0.75rem; font-weight:700; letter-spacing:1px; text-transform:uppercase;">{dl.translate("agronomic_audit", lang)}</div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:{w_color}15; border:1px solid {w_color}40; color:{w_color}; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
            { ("साझा सूत्र: Sentinel-2" if is_hi else "Source: Sentinel-2") if "Sentinel" in sat_source else dl.translate("simulation_mode", lang) }
        </div>
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#F5F5F5; padding:4px 12px; border-radius:30px; font-size:0.75rem; font-weight:700;">
            { ("अद्यतित " if is_hi else "Updated ") + last_updated }
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4 METRIC CARDS ROW
st.markdown(f"""
<div style="display:flex; gap:15px; margin-bottom:20px; font-family:'Space Grotesk', sans-serif;">
    <!-- Metric 1 -->
    <div style="flex:1; background:{card_bg}; padding:20px; border-radius:12px; border:1px solid #333;">
        <div style="color:{text_g}; font-size:0.9rem; margin-bottom:10px;">{t_farm_score_lbl}</div>
        <div style="color:{green_c}; font-size:2.4rem; font-weight:700; line-height:1;">{avg_h:.0f}</div>
        <div style="color:{text_g}; font-size:0.85rem; margin-top:8px;">↑ 3 pts from last week</div>
    </div>
    <!-- Metric 2 -->
    <div style="flex:1; background:{card_bg}; padding:20px; border-radius:12px; border:1px solid #333;">
        <div style="color:{text_g}; font-size:0.9rem; margin-bottom:10px;">{t_good_lbl}</div>
        <div style="color:{green_c}; font-size:2.4rem; font-weight:700; line-height:1;">{fields_good}</div>
        <div style="color:{text_g}; font-size:0.85rem; margin-top:8px;">{t_above_70}</div>
    </div>
    <!-- Metric 3 -->
    <div style="flex:1; background:{card_bg}; padding:20px; border-radius:12px; border:1px solid #333;">
        <div style="color:{text_g}; font-size:0.9rem; margin-bottom:10px;">{t_action_lbl}</div>
        <div style="color:{amber_c}; font-size:2.4rem; font-weight:700; line-height:1;">{fields_caution}</div>
        <div style="color:{text_g}; font-size:0.85rem; margin-top:8px;">{t_mid_score}</div>
    </div>
    <!-- Metric 4 -->
    <div style="flex:1; background:{card_bg}; padding:20px; border-radius:12px; border:1px solid #333;">
        <div style="color:{text_g}; font-size:0.9rem; margin-bottom:10px;">{t_crit_lbl}</div>
        <div style="color:{text_w}; font-size:2.4rem; font-weight:700; line-height:1;">{fields_critical}</div>
        <div style="color:{text_g}; font-size:0.85rem; margin-top:8px;">{t_below_45}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# BANNER
st.markdown(f"""
<div style="background:#FFFBF0; border:1px solid #FDE68A; padding:12px 20px; border-radius:8px; color:#B45309; font-size:0.95rem; font-weight:500; margin-bottom:30px; font-family:'Space Grotesk', sans-serif;">
    {t_banner}
</div>
<div style="font-size:1.1rem; color:{text_w}; font-family:'Space Grotesk', sans-serif; margin-bottom:15px;">{t_each_score}</div>
""", unsafe_allow_html=True)

# 9 FIELD CARDS GRID
def get_field_ui_props(health_score):
    if health_score >= 70:
        return green_c, dl.translate("healthy_no_action", lang), green_fill, "#166534"
    elif health_score >= 64:
        return amber_c, dl.translate("monitor_stress", lang), amber_fill, "#92400e"
    elif health_score >= 56:
        return amber_c, dl.translate("check_irrigation", lang), amber_fill, "#92400e"
    elif health_score >= 50:
        return amber_c, dl.translate("review_pest", lang), amber_fill, "#92400e"
    elif health_score >= 45:
        return amber_c, dl.translate("low_nitrogen", lang), amber_fill, "#92400e"
    else:
        return red_c, dl.translate("critical_inspect", lang), red_fill, "#991b1b"

if sectors:
    # Map the live sectors directly to cards
    items = list(sectors.items())
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j, (name, s_data) in enumerate(items[i:i+3]):
            with cols[j]:
                score = s_data.get('ndvi', 0.6) * 100
                c_light, tag_text, tag_bg, tag_color = get_field_ui_props(score)
                # Override tag text with the actual live label from sector analysis if it's more descriptive
                if s_data.get('label'):
                    tag_text = s_data['label']
                    if s_data.get('value'):
                        tag_text += f": {s_data['value']}"
                
                scan_date = s_data.get('source', '').replace('Sentinel-2 (', '').replace(')', '') or datetime.now().strftime("%d %b")
                t_last_scan = f"अंतिम स्कैन: {scan_date}" if is_hi else f"Source: {scan_date}"
            
            # Simple smooth SVG sparkline that trends with the health score
            y_trend = 100 - score
            svg_path = f"M0 {y_trend} Q 20 {y_trend-5}, 40 {y_trend+2} T 80 {y_trend-2} T 120 {y_trend}"
            if score < 70:
                svg_path = f"M0 40 Q 20 40, 40 45 T 80 42 T 120 48"
            
            st.markdown(f"""
<div style="background:{card_bg}; border:2px solid #333; border-top:2px solid {c_light}; border-radius:12px; padding:20px; font-family:'Space Grotesk', sans-serif; position:relative;">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<div>
<div style="color:{text_w}; font-size:1.1rem; font-weight:600; margin-bottom:5px;">{name}</div>
<div style="color:{text_g}; font-size:0.8rem; margin-bottom:20px;">{t_last_scan}</div>
</div>
<!-- Circular Progress Ring -->
<div style="position:relative; width:46px; height:46px; border-radius:50%; background:conic-gradient({c_light} {score}%, #333 0); display:flex; align-items:center; justify-content:center;">
<div style="position:absolute; width:36px; height:36px; background:{card_bg}; border-radius:50%;"></div>
<div style="position:relative; color:{text_w}; font-size:0.9rem; font-weight:700;">{score:.0f}</div>
</div>
</div>
<div style="background:{tag_bg}; color:{tag_color}; padding:6px 12px; border-radius:4px; font-size:0.8rem; font-weight:600; display:inline-block; margin-bottom:25px;">
{tag_text}
</div>
<!-- Sparkline Graphic -->
<div style="position:absolute; bottom:20px; left:20px; width:calc(100% - 40px); height:15px;">
<svg viewBox="0 0 120 50" preserveAspectRatio="none" style="width:100%; height:100%;">
<path d="{svg_path}" fill="none" stroke="{c_light}" stroke-width="2" stroke-linecap="round"/>
</svg>
</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
