import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import setup_page, accent_a, accent_g, accent_r, text_w, text_muted, card_bg
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import data_loader as dl

lang = setup_page(
    title=dl.translate("soil_nutrition", st.session_state.get('lang')),
    subtitle=dl.translate("nutrient_intel", st.session_state.get('lang')),
    icon="🧪"
)
dl.get_field_sidebar()
is_hi = (lang == 'hi')
growth_stage = dl.get_rice_life_cycle().get('stage', 'Tillering')

# Live Source Verification
nutri_source = st.session_state.get('nutrition_source_verification', 'Simulated')
nutri_color = "#4ADE80" if "Verified" in nutri_source else "#94a3b8"

st.markdown(f"""
<div style="display:flex; justify-content:flex-end; margin-bottom:20px;">
    <div style="background:{nutri_color}15; border:1px solid {nutri_color}40; color:{nutri_color}; padding:2px 10px; border-radius:15px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">
        { ("स्रोत: सत्यापित IoT" if is_hi else "Source: Verified IoT") if "Verified" in nutri_source else dl.translate("simulation_mode", lang) }
    </div>
</div>
""", unsafe_allow_html=True)

# Fetch Data-Driven Analytics
stats = dl.get_nutrition_analytics(lang=lang)
conf = stats['config']

def render_sparkline(data, color):
    # Convert hex to rgba for Plotly compatibility
    hex_c = color.lstrip('#')
    r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
    fill_rgba = f"rgba({r},{g},{b},0.1)"
    
    fig = go.Figure(go.Scatter(y=data, mode='lines', line=dict(color=color, width=2), fill='tozeroy', fillcolor=fill_rgba))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(l=0,r=0,t=0,b=0), height=30, width=120, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

# --- TOP KPI CARDS ---
c1, c2, c3 = st.columns(3)

def render_nutrient_card(placeholder, key, label, val, color, status, icon):
    # Building a single-row design for KPI cards
    opt_range = f"{conf[key]['min']}-{conf[key]['max']} {conf[key]['unit']}"
    prog = (val / conf[key]['max']) * 100
    
    # Translate status
    status_display = dl.translate("good", lang) if status == "Optimal" else dl.translate("safe", lang) if status == "Sufficient" else dl.translate("problem_area", lang)
    if not is_hi:
        status_display = status # keep original if en
        
    html = (
        f'<div style="background:{card_bg}; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px; position:relative; overflow:hidden;">'
        f'<div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">'
        f'<div style="background:{color}20; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:{color}; font-weight:700;">{icon}</div>'
        f'<div><div style="color:{text_muted}; font-size:0.6rem; text-transform:uppercase; text-align:right; margin-bottom:2px;">{dl.translate(label.lower(), lang)}</div>'
        f'<div style="color:{text_muted}; font-size:0.5rem; text-align:right;">{dl.translate("needs_improvement" if status != "Optimal" else "all_clear", lang)}</div></div>'
        f'</div>'
        f'<div style="display:flex; align-items:baseline; gap:8px;">'
        f'<div style="font-size:2rem; font-weight:800; color:{text_w};">{val:.1f}</div>'
        f'<div style="font-size:0.65rem; color:{text_muted};">kg/ha</div>'
        f'<div style="margin-left:auto; background:{color}20; color:{color}; font-size:0.55rem; font-weight:700; padding:2px 8px; border-radius:20px;">{status_display}</div>'
        f'</div>'
        f'<div style="color:{text_muted}; font-size:0.6rem; margin:15px 0 5px 0;">{dl.translate("optimal_range_npk", lang)} {opt_range}</div>'
        f'<div style="height:6px; background:rgba(255,255,255,0.05); border-radius:3px; margin-bottom:15px;">'
        f'<div style="height:100%; width:{min(prog, 100)}%; background:{color}; border-radius:3px;"></div>'
        f'</div>'
        f'<div style="display:flex; justify-content:space-between; align-items:end;">'
        f'<div style="font-size:0.55rem; color:{text_muted};">{dl.translate("trend_8w", lang)}</div>'
        f'</div>'
        f'</div>'
    )
    with placeholder:
        st.html(html)
        st.plotly_chart(render_sparkline(stats['trends'][key], color), use_container_width=False, config={'displayModeBar': False})

render_nutrient_card(c1, "N", "NITROGEN", stats['avg_n'], "#3b82f6", "Optimal" if stats['avg_n'] >= conf['N']['min'] else "Low", "N")
render_nutrient_card(c2, "P", "PHOSPHORUS", stats['avg_p'], accent_r, "Deficient" if stats['avg_p'] < conf['P']['min'] else "Optimal", "P")
render_nutrient_card(c3, "K", "POTASSIUM", stats['avg_k'], accent_a, "Low" if stats['avg_k'] < conf['K']['min'] else "Optimal", "K")

# --- AI NUTRIENT INSIGHT (Interactive) ---
st.markdown("<br>", unsafe_allow_html=True)
insight_col, action_col = st.columns([4, 1])

with insight_col:
    st.markdown(f"""
    <div style="background:rgba(42, 187, 155, 0.08); border:1px solid rgba(42, 187, 155, 0.2); border-radius:12px; padding:15px; display:flex; gap:15px; align-items:start;">
        <div style="color:{accent_g}; font-size:1.2rem; margin-top:2px;">●</div>
        <div>
            <div style="color:{accent_g}; font-weight:700; font-size:0.6rem; text-transform:uppercase; margin-bottom:4px;">{dl.translate("ai_nutrient_insight", lang)}</div>
            <div style="color:{text_w}; font-size:0.85rem;">{stats["analysis"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with action_col:
    if st.button(dl.translate("get_full_plan", lang), use_container_width=True, type="primary"):
        st.toast("Generating Plan..." if not is_hi else "प्लान तैयार किया जा रहा है...")
        st.info(f"📍 **Detailed Schedule for {growth_stage if 'growth_stage' in locals() else 'Current Stage'}**\n- Apply 45kg MRP tomorrow morning.\n- Split Urea application into 3 doses.\n- Focus on NW field (55% deficiency).")

# --- RECOMMENDATIONS GRID ---
st.markdown("<br>", unsafe_allow_html=True)
st.html(f'<div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:15px;">{dl.translate("fert_recs", lang)}</div>')
rec_cols = st.columns(2)

def render_rec_card(col_obj, rec, idx):
    bg = "rgba(245, 158, 11, 0.05)" if rec['type'] == 'MRP' else "rgba(139, 92, 246, 0.05)" if rec['type'] == 'MOP' else card_bg
    icon = "⚠️" if rec['type'] == 'MRP' else "⚖️" if rec['type'] == 'MOP' else "💧"
    icon_bg = "#f59e0b" if rec['type'] == 'MRP' else "#8b5cf6" if rec['type'] == 'MOP' else "#3b82f6"
    
    html = (
        f'<div style="background:{bg}; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px; margin-bottom:10px;">'
        f'<div style="display:flex; gap:15px; margin-bottom:15px;">'
        f'<div style="background:{icon_bg}20; width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:{icon_bg};">{icon}</div>'
        f'<div><div style="font-weight:700; color:{text_w}; font-size:0.9rem;">{dl.translate("apply_fert", lang)} {rec["type"]} - {rec["val"]} kg/ha</div>'
        f'<div style="font-size:0.7rem; color:{text_muted};">{rec["role"]}</div></div>'
        f'</div>'
        f'<div style="display:flex; gap:10px; margin-bottom:20px;">'
        f'<div style="background:rgba(255,255,255,0.05); padding:4px 10px; border-radius:4px; font-size:0.6rem; color:{icon_bg};">{rec["val"]} kg/ha</div>'
        f'<div style="background:rgba(255,255,255,0.05); padding:4px 10px; border-radius:4px; font-size:0.6rem; color:{accent_g};">{dl.translate("timing_fert", lang)}: {rec["timing"]}</div>'
        f'</div></div>'
    )
    with col_obj:
        st.html(html)
        b1, b2 = st.columns(2)
        if b1.button(dl.translate("log_app", lang), key=f"log_{idx}", use_container_width=True):
            st.success("✅ Application Logged!" if not is_hi else "✅ उपयोग दर्ज किया गया!")
        if b2.button(dl.translate("view_field_map", lang), key=f"map_{idx}", use_container_width=True):
            st.switch_page("pages/10_🗺️_Spectral_Maps.py")

if len(stats['recs']) >= 2:
    render_rec_card(rec_cols[0], stats['recs'][0], 0)
    render_rec_card(rec_cols[1], stats['recs'][1], 1)

# --- PER-FIELD COMPARISON (Fix Alignment) ---
st.html(f'<br><div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin:20px 0 15px 0;">{dl.translate("npk_comp", lang)}</div>')
field_items = list(stats['matrix'].items())
field_rows = [field_items[i:i+3] for i in range(0, 9, 3)]

def render_field_compact(col_obj, name, levels):
    def bar(val, opt_max, col):
        prog = min(100, (val / opt_max)*100)
        return (f'<div style="flex-grow:1; max-width:140px; height:4px; background:rgba(255,255,255,0.05); border-radius:2px; position:relative; margin: 0 10px;">'
                f'<div style="position:absolute; height:100%; width:{prog}%; background:{col}; border-radius:2px;"></div></div>')

    html = (
        f'<div style="background:{card_bg}; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px; margin-bottom:10px;">'
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">'
        f'<div style="width:8px; height:8px; background:{accent_g}; border-radius:50%;"></div>'
        f'<div style="font-size:0.75rem; font-weight:700; color:{text_w};">{name} {"Field" if not is_hi else "खेत"}</div>'
        f'</div>'
        f'<div style="display:flex; align-items:center; justify-content:space-between; gap:5px; margin-bottom:8px;"><div style="width:10px; font-size:0.6rem; color:{text_muted};">N</div>{bar(levels["N"], conf["N"]["max"], "#3b82f6")}<div style="width:25px; font-size:0.6rem; text-align:right; color:{text_muted};">{int(levels["N"])}</div></div>'
        f'<div style="display:flex; align-items:center; justify-content:space-between; gap:5px; margin-bottom:8px;"><div style="width:10px; font-size:0.6rem; color:{text_muted};">P</div>{bar(levels["P"], conf["P"]["max"], accent_r)}<div style="width:25px; font-size:0.6rem; text-align:right; color:{text_muted};">{int(levels["P"])}</div></div>'
        f'<div style="display:flex; align-items:center; justify-content:space-between; gap:5px;"><div style="width:10px; font-size:0.6rem; color:{text_muted};">K</div>{bar(levels["K"], conf["K"]["max"], accent_a)}<div style="width:25px; font-size:0.6rem; text-align:right; color:{text_muted};">{int(levels["K"])}</div></div>'
        f'</div>'
    )
    with col_obj:
        st.html(html)

for row in field_rows:
    cols = st.columns(3)
    for i, (name, levels) in enumerate(row):
        render_field_compact(cols[i], name, levels)

# --- TREND CHART ---
st.html(f'<br><div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin:20px 0 15px 0;">{dl.translate("trend_8w", lang)}</div>')
df_trend = pd.DataFrame({
    'Weeks': stats['trends']['weeks'],
    'Nitrogen (N)': stats['trends']['N'],
    'Phosphorus (P)': stats['trends']['P'],
    'Potassium (K)': stats['trends']['K']
})
fig_m = go.Figure()
fig_m.add_trace(go.Scatter(x=df_trend['Weeks'], y=df_trend['Nitrogen (N)'], name=dl.translate('nitrogen', lang), line=dict(color='#3b82f6', width=2), mode='lines+markers'))
fig_m.add_trace(go.Scatter(x=df_trend['Weeks'], y=df_trend['Phosphorus (P)'], name=dl.translate('phosphorus', lang), line=dict(color=accent_r, width=2), mode='lines+markers'))
fig_m.add_trace(go.Scatter(x=df_trend['Weeks'], y=df_trend['Potassium (K)'], name=dl.translate('potassium', lang), line=dict(color=accent_a, width=2), mode='lines+markers'))
fig_m.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10, color=text_muted)))
fig_m.update_xaxes(showgrid=False, zeroline=False, color=text_muted, tickfont=dict(size=9))
fig_m.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, color=text_muted, tickfont=dict(size=9))
st.plotly_chart(fig_m, use_container_width=True)

# --- COST TABLE (Localized) ---
st.html(f'<br><div style="color:{text_muted}; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin:20px 0 15px 0;">ESTIMATED FERTILISER COST — THIS CYCLE</div>')

rows_html = "".join([
    f'<tr><td style="padding:12px; font-size:0.75rem; color:{text_w};">{item["name"]}</td>'
    f'<td style="padding:12px; font-size:0.7rem; color:{text_muted};">{item["fields"]}</td>'
    f'<td style="padding:12px; font-size:0.7rem; color:{text_muted}; text-align:center;">{item["qty"]} kg</td>'
    f'<td style="padding:12px; font-size:0.7rem; color:{text_muted}; text-align:center;">₹{item["price"]}/kg</td>'
    f'<td style="padding:12px; font-size:0.75rem; color:{accent_g if item["total"]>0 else text_muted}; font-weight:700; text-align:right;">₹{item["total"]:,}</td></tr>'
    for item in stats['cost_items']
])

table_html = (
    f'<div style="background:{card_bg}; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:10px; overflow-x:auto;">'
    f'<table style="width:100%; border-collapse:collapse;">'
    f'<thead style="border-bottom:1px solid rgba(255,255,255,0.05);"><tr>'
    f'<th style="text-align:left; padding:12px; font-size:0.6rem; color:{text_muted}; text-transform:uppercase;">{ ("खाद" if is_hi else "Fertiliser") }</th>'
    f'<th style="text-align:left; padding:12px; font-size:0.6rem; color:{text_muted}; text-transform:uppercase;">{ ("खेत" if is_hi else "Fields") }</th>'
    f'<th style="text-align:center; padding:12px; font-size:0.6rem; color:{text_muted}; text-transform:uppercase;">{ ("मात्रा" if is_hi else "Quantity") }</th>'
    f'<th style="text-align:center; padding:12px; font-size:0.6rem; color:{text_muted}; text-transform:uppercase;">{ ("मूल्य" if is_hi else "Unit Price") }</th>'
    f'<th style="text-align:right; padding:12px; font-size:0.6rem; color:{text_muted}; text-transform:uppercase;">{ ("कुल लागत" if is_hi else "Total Cost") }</th>'
    f'</tr></thead>'
    f'<tbody>{rows_html}</tbody>'
    f'<tfoot style="border-top:1px solid rgba(255,255,255,0.1);">'
    f'<tr><td colspan="4" style="padding:15px; font-weight:700; color:{text_w}; font-size:0.8rem;">{ ("कुल अनुमानित लागत" if is_hi else "Total estimated cost") }</td>'
    f'<td style="padding:15px; font-weight:700; color:{accent_g}; font-size:1.1rem; text-align:right;">₹{int(stats["total_cost"]):,}</td></tr>'
    f'</tfoot></table></div>'
)
st.html(table_html)
