import streamlit as st

# --- Python-accessible Design Tokens (Midnight Eco) ---
accent_a = "#E8A020"    # Amber
accent_g = "#4CAF82"    # Green
accent_r = "#D95B3A"    # Red
text_w   = "#F5F0E8"    # White
text_muted = "rgba(245,240,232,0.68)"
card_bg  = "rgba(255,255,255,0.05)"

# ─────────────────────────────────────────────────────────────────
# FARMOS DESIGN SYSTEM — shared across all pages via inject_css()
# ─────────────────────────────────────────────────────────────────

_FARMOS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Serif+Display&display=swap');

/* Hide native Streamlit sidebar navigation to prevent duplicates */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* ═══ FARMOS DESIGN TOKENS ═══ */
:root {
  --farm-bg:          #0D2B1A;
  --farm-bg2:         #0A2114;
  --farm-bg3:         #0F3020;
  --farm-accent:      #E8A020;
  --farm-accent2:     #4CAF82;
  --farm-text:        #F5F0E8;
  --farm-text2:       rgba(245,240,232,0.68);
  --farm-text3:       rgba(245,240,232,0.40);
  --farm-alert:       #D95B3A;
  --farm-neutral:     #7B8FA1;
  --farm-card:        rgba(255,255,255,0.05);
  --farm-border:      rgba(232,160,32,0.18);
  --farm-border2:     rgba(255,255,255,0.07);
  --farm-shadow:      0 4px 24px rgba(0,0,0,0.40);
  --farm-radius:      16px;
}

/* ═══ GLOBAL BACKGROUND ═══ */
html, body, [data-testid="stAppViewContainer"] {
  background: linear-gradient(160deg, #0D2B1A 0%, #0A2114 55%, #0D2B1A 100%) !important;
  min-height: 100vh;
  font-family: 'Space Grotesk', sans-serif !important;
}
.main, [data-testid="stMain"], [data-testid="block-container"] {
  background: transparent !important;
}

/* ═══ PAGE MOOD STRIPE — Global Content Header Line ═══ */
.scan-line {
  width: 100%;
  height: 4px;
  background: rgba(255,255,255,0.05);
  position: relative;
  overflow: hidden;
  margin-bottom: 15px;
  border-radius: 2px;
}

.scan-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: -40%;
  width: 40%;
  height: 100%;
  background: linear-gradient(90deg, transparent, #4CAF82, #E8A020, #D95B3A, transparent);
  animation: slide-scan 2.5s linear infinite;
  box-shadow: 0 0 15px rgba(232, 160, 32, 0.4);
}

@keyframes slide-scan {
  0% { left: -40%; }
  100% { left: 100%; }
}

[data-testid="stMainBlockContainer"]::before {
  content: none !important;
}

/* ═══ STREAMLIT METRIC CARDS — Earthen Glass ═══ */
[data-testid="metric-container"] {
  background: rgba(255,255,255,0.05) !important;
  backdrop-filter: blur(12px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(12px) saturate(140%) !important;
  border: 1px solid rgba(232,160,32,0.18) !important;
  border-top: 3px solid #E8A020 !important;
  border-radius: 16px !important;
  padding: 20px 18px !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(232,160,32,0.30) !important;
  border-top-color: #F5B83A !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 26px !important;
  font-weight: 700 !important;
  color: #F5F0E8 !important;
}
[data-testid="stMetricLabel"] {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 11px !important;
  color: rgba(245,240,232,0.55) !important;
  font-weight: 600 !important;
  letter-spacing: 0.07em !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricDelta"] {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 11px !important;
  font-weight: 600 !important;
}

/* ═══ BUTTONS — Amber Glow ═══ */
.stButton > button {
  border-radius: 10px !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  background: rgba(232,160,32,0.12) !important;
  color: #E8A020 !important;
  border: 1px solid rgba(232,160,32,0.35) !important;
  transition: all 0.2s ease !important;
  letter-spacing: 0.02em !important;
  padding: 0.60rem 1.2rem !important;
}
.stButton > button:hover {
  background: rgba(232,160,32,0.25) !important;
  border-color: #E8A020 !important;
  color: #F5F0E8 !important;
  box-shadow: 0 0 18px rgba(232,160,32,0.40), 0 4px 14px rgba(0,0,0,0.30) !important;
  transform: translateY(-2px) !important;
}
.stButton > button:active {
  transform: translateY(0px) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #E8A020, #C47D10) !important;
  color: #0D2B1A !important;
  border-color: #E8A020 !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 16px rgba(232,160,32,0.30) !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #F5B83A, #D48D20) !important;
  box-shadow: 0 0 24px rgba(232,160,32,0.55), 0 4px 16px rgba(0,0,0,0.35) !important;
  color: #0A2114 !important;
}

/* ═══ SIDEBAR — Deep Forest & Structured ═══ */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #071A0D 0%, #0A2114 60%, #0D2B1A 100%) !important;
  border-right: 1px solid rgba(232,160,32,0.18) !important;
}
/* Re-allow natural spacing between items */
[data-testid="stSidebar"] .stVerticalBlock {
  gap: 1.25rem !important;
}
/* Font specifically for text elements, NOT icons */
[data-testid="stSidebar"] p, 
[data-testid="stSidebar"] span, 
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div:not([class*="material"]) {
  color: rgba(245,240,232,0.85) !important;
  font-family: 'Space Grotesk', sans-serif !important;
}

/* Sidebar Branding */
.sb-header {
  padding: 10px 0 20px 0;
}
.sb-title {
  color: #F5F0E8 !important;
  font-size: 1.15rem !important;
  font-weight: 700 !important;
  margin-bottom: 2px !important;
  font-family: 'Space Grotesk', sans-serif !important;
}
.sb-subtitle {
  color: rgba(245,240,232,0.5) !important;
  font-size: 0.7rem !important;
  font-weight: 500 !important;
}

/* Status Pill */
.status-pill {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  background: rgba(76, 175, 130, 0.08) !important;
  border: 1px solid rgba(76, 175, 130, 0.2) !important;
  padding: 6px 12px !important;
  border-radius: 50px !important;
  margin: 15px 0 !important;
  width: fit-content !important;
}
.status-dot {
  width: 8px;
  height: 8px;
  background: #4CAF50;
  border-radius: 50%;
  box-shadow: 0 0 8px #4CAF50;
}
.status-text {
  font-size: 0.7rem !important;
  font-weight: 600 !important;
  color: #4CAF50 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Section Headers */
.sb-section-header {
  color: rgba(245,240,232,0.25) !important;
  font-size: 0.62rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  margin: 28px 0 12px 0 !important;
  border-top: 1px solid rgba(255,255,255,0.03);
  padding-top: 20px;
}

/* Navigation Items (Buttons) */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  color: rgba(245,240,232,0.7) !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding: 10px 14px !important;
  margin-bottom: 2px !important;
  font-size: 0.88rem !important;
  width: 100% !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  border-radius: 10px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.06) !important;
  color: #F5F0E8 !important;
  transform: translateX(4px) !important;
}
/* Active state simulation */
.stButton-active > button {
  background: rgba(76, 175, 130, 0.15) !important;
  color: #4CAF82 !important;
  font-weight: 600 !important;
}

/* Timeline */
.timeline-list {
  list-style: none !important;
  padding: 0 !important;
  margin: 10px 0 !important;
}
.timeline-item {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  margin-bottom: 10px !important;
  font-size: 0.72rem !important;
  color: rgba(245,240,232,0.55) !important;
}
.timeline-dot {
  width: 6px;
  height: 6px;
  background: #4CAF82;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(76,175,130,0.4);
}

/* AI Insight Card (Footer) */
.ai-card {
  background: rgba(0, 0, 0, 0.22) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 14px !important;
  padding: 16px !important;
  margin-top: 25px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.ai-card-title {
  font-size: 0.62rem !important;
  font-weight: 800 !important;
  color: rgba(245,240,232,0.35) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em;
  margin-bottom: 16px !important;
}
.ai-card-item {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  padding: 10px 0 !important;
  font-size: 0.82rem !important;
  color: rgba(245,240,232,0.75) !important;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  transition: color 0.2s ease;
}
.ai-card-item:hover {
  color: #F5F0E8 !important;
}
.ai-card-item:last-child {
  border-bottom: none !important;
}

/* Sidebar toggle/collapse button */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
  background: rgba(232,160,32,0.1) !important;
  border: 1px solid rgba(232,160,32,0.2) !important;
  border-radius: 8px !important;
}


/* ═══ HEADINGS ═══ */
h1, h2, h3, h4, h5 {
  font-family: 'DM Serif Display', serif !important;
  color: #F5F0E8 !important;
}
h1 { font-size: 1.9rem !important; font-weight: 400 !important; }
h2 { font-size: 1.45rem !important; font-weight: 400 !important; }
h3 { font-size: 1.1rem !important; font-weight: 400 !important; }
p, span, label, li {
  font-family: 'Space Grotesk', sans-serif !important;
  color: rgba(245,240,232,0.88) !important;
}

/* ═══ ALERTS / INFO ═══ */
[data-testid="stAlert"] {
  background: rgba(232,160,32,0.06) !important;
  border: 1px solid rgba(232,160,32,0.20) !important;
  border-left: 4px solid #E8A020 !important;
  border-radius: 12px !important;
  color: rgba(245,240,232,0.90) !important;
}
[data-testid="stAlert"] p { color: rgba(245,240,232,0.90) !important; }

/* ═══ DIVIDERS ═══ */
/* ═══ DIVIDERS — Animated Glow Line ═══ */
hr {
  height: 2px !important;
  border: none !important;
  background: linear-gradient(90deg, 
      rgba(76, 175, 130, 0) 0%, 
      rgba(76, 175, 130, 0.8) 25%, 
      rgba(232, 160, 32, 0.9) 50%, 
      rgba(76, 175, 130, 0.8) 75%, 
      rgba(76, 175, 130, 0) 100%
  ) !important;
  background-size: 200% 100% !important;
  animation: glow-line-move 2.5s ease-in-out infinite alternate !important;
  box-shadow: 0 0 12px rgba(76, 175, 130, 0.4) !important;
  opacity: 0.85 !important;
  margin: 28px 0 !important;
}

@keyframes glow-line-move {
  0% { background-position: 0% 0; filter: hue-rotate(0deg) brightness(1); }
  100% { background-position: 100% 0; filter: hue-rotate(15deg) brightness(1.2); }
}

.glow-line {
  height: 1px;
  width: 100%;
  background: linear-gradient(90deg, transparent, #4CAF82, #E8A020, #4CAF82, transparent);
  background-size: 200% 100%;
  animation: glow-line-move 2.5s ease-in-out infinite alternate;
  box-shadow: 0 0 10px rgba(76, 175, 130, 0.3);
  margin: 15px 0;
}

/* ═══ EXPANDERS ═══ */
[data-testid="stExpander"] {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(232,160,32,0.12) !important;
  border-radius: 14px !important;
}
[data-testid="stExpander"] summary {
  color: rgba(245,240,232,0.88) !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 600 !important;
}

/* ═══ INPUTS / SELECTS ═══ */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stDateInput"] input,
textarea {
  background: rgba(0,0,0,0.30) !important;
  border: 1px solid rgba(232,160,32,0.20) !important;
  border-radius: 10px !important;
  color: #F5F0E8 !important;
  font-family: 'Space Grotesk', sans-serif !important;
}

/* ═══ PROGRESS BARS ═══ */
.stProgress > div > div {
  background: linear-gradient(90deg, #4CAF82, #E8A020) !important;
  border-radius: 99px !important;
}
.stProgress > div {
  background: rgba(255,255,255,0.10) !important;
  border-radius: 99px !important;
}

/* ═══ DATAFRAMES ═══ */
[data-testid="stDataFrame"] {
  border-radius: 14px !important;
  overflow: hidden !important;
  border: 1px solid rgba(232,160,32,0.12) !important;
  background: rgba(0,0,0,0.20) !important;
}

/* ═══ SCROLLBAR ═══ */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0A2114; }
::-webkit-scrollbar-thumb {
  background: rgba(232,160,32,0.30);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(232,160,32,0.55); }

/* ═══ UTILITY CLASSES ═══ */
.status-banner {
  padding: 22px; border-radius: 18px; color: #F5F0E8;
  text-align: center; margin-bottom: 28px;
  font-family: 'Space Grotesk', sans-serif;
  border: 1px solid rgba(232,160,32,0.15);
}
.farmer-tip {
  display: flex; align-items: center; gap: 14px;
  background: rgba(76,175,130,0.08);
  padding: 14px; border-radius: 12px;
  border-left: 3px solid #4CAF82;
  margin-bottom: 10px;
  color: rgba(245,240,232,0.90);
}
.glass-card {
  background: rgba(255,255,255,0.05) !important;
  backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(232,160,32,0.15) !important;
  border-radius: 18px !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.35) !important;
}
.telemetry-card {
  background: rgba(0,0,0,0.25);
  border-radius: 16px; padding: 18px;
  border: 1px solid rgba(56,189,248,0.20);
  border-left: 4px solid #38bdf8;
  color: #F5F0E8 !important;
}
.telemetry-card h2, .telemetry-card p, .telemetry-card b { color: #F5F0E8 !important; }

/* ═══ FARM PULSE ═══ */
@keyframes farm-breathe {
  0%, 100% { transform: scale(1);    opacity: 1; }
  50%       { transform: scale(1.18); opacity: 0.70; }
}
@keyframes farm-ripple {
  0%   { transform: scale(1);   opacity: 0.6; }
  100% { transform: scale(2.8); opacity: 0; }
}
.farm-pulse-dot {
  width: 12px; height: 12px; border-radius: 50%;
  display: inline-block; position: relative;
  animation: farm-breathe 2.8s ease-in-out infinite;
}
.farm-pulse-dot::after {
  content: ''; position: absolute; inset: 0; border-radius: 50%;
  animation: farm-ripple 2.8s ease-out infinite;
}
.farm-pulse-dot.healthy   { background: #4CAF82; }
.farm-pulse-dot.healthy::after   { background: rgba(76,175,130,0.45); }
.farm-pulse-dot.caution   { background: #E8A020; }
.farm-pulse-dot.caution::after   { background: rgba(232,160,32,0.45); }
.farm-pulse-dot.alert-red { background: #D95B3A; }
.farm-pulse-dot.alert-red::after { background: rgba(217,91,58,0.45); }

/* ═══ AMBER PULSE ANIMATIONS ═══ */
@keyframes pulse-amber {
  0%   { box-shadow: 0 0 0 0 rgba(232,160,32,0.7); }
  70%  { box-shadow: 0 0 0 14px rgba(232,160,32,0); }
  100% { box-shadow: 0 0 0 0 rgba(232,160,32,0); }
}
@keyframes pulse-alert-red {
  0%   { box-shadow: 0 0 0 0 rgba(217,91,58,0.7); }
  70%  { box-shadow: 0 0 0 14px rgba(217,91,58,0); }
  100% { box-shadow: 0 0 0 0 rgba(217,91,58,0); }
}
.pulse-card { animation: pulse-alert-red 2s infinite; }
.neon-status {
  display: inline-block; width: 9px; height: 9px; border-radius: 50%;
  margin-right: 8px; box-shadow: 0 0 9px currentColor;
  animation: blinker 1.5s linear infinite;
}
@keyframes blinker { 50% { opacity: 0.25; } }

/* ═══ MOBILE ADAPTIVE LAYER ═══ */
@media (max-width: 768px) {
  [data-testid="stMainBlockContainer"] {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
  }
  h1 { font-size: 1.5rem !important; }
  h2 { font-size: 1.25rem !important; }
  
  [data-testid="metric-container"] {
    padding: 12px !important;
  }
  [data-testid="stMetricValue"] {
    font-size: 20px !important;
  }
  
  /* Sidebar Branding on Mobile */
  .sb-header { padding-bottom: 10px; }
  .sb-title { font-size: 1rem !important; }
}

/* ═══ HIDE STREAMLIT CHROME (Except Sidebar Toggle) ═══ */
#MainMenu, footer { visibility: hidden !important; }
[data-testid="stToolbar"] { opacity: 0.1; transition: opacity 0.3s; }
[data-testid="stToolbar"]:hover { opacity: 1.0; }

[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: block !important;
    opacity: 1 !important;
}
"""

def inject_css():
    st.markdown(f"<style>{_FARMOS_CSS}</style>", unsafe_allow_html=True)
    st.markdown('<div class="scan-line"></div>', unsafe_allow_html=True)


def status_color(score, lang='en'):
    """Returns (color_name, label) based on 0-100 farm health score."""
    if score >= 70:
        return "green", "Healthy" if lang == 'en' else "स्वस्थ (Healthy)"
    if score >= 45:
        return "orange", "Needs Attention" if lang == 'en' else "ध्यान दें (Needs Attention)"
    return "red", "At Risk" if lang == 'en' else "खतरे में (At Risk)"


def severity_badge(severity):
    """Returns (fg_color, bg_color) for badge styling — FarmOS earth-tone palette."""
    colors = {
        "Critical": ("#FFBDAA", "rgba(217,91,58,0.18)"),
        "Warning":  ("#F5C76A", "rgba(232,160,32,0.16)"),
        "Info":     ("#99D4B4", "rgba(76,175,130,0.14)"),
    }
    return colors.get(severity, ("#C8D8C0", "rgba(255,255,255,0.06)"))


def render_badge(label, severity):
    fg, bg = severity_badge(severity)
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 12px;border-radius:10px;'
        f'font-weight:700;font-size:11px;display:inline-block;letter-spacing:0.05em;'
        f'border:1px solid {fg}44;font-family:\'Space Grotesk\',sans-serif;">{label}</span>'
    )


# ─────────────────────────────────────────────────────────────────
# SVG wheat-in-hexagon logo mark (inline, 32px)
# ─────────────────────────────────────────────────────────────────
_WHEAT_LOGO_SVG = """
<svg width="32" height="36" viewBox="0 0 32 36" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Hexagon outline -->
  <path d="M16 1L30 9V27L16 35L2 27V9L16 1Z"
        stroke="#E8A020" stroke-width="1.5" fill="rgba(232,160,32,0.08)"/>
  <!-- Wheat stalk (center vertical) -->
  <line x1="16" y1="28" x2="16" y2="10" stroke="#4CAF82" stroke-width="1.3"/>
  <!-- Wheat grains (left) -->
  <ellipse cx="13" cy="14" rx="2.5" ry="1.3" fill="#E8A020" transform="rotate(-30 13 14)"/>
  <ellipse cx="12.5" cy="18" rx="2.5" ry="1.3" fill="#E8A020" transform="rotate(-30 12.5 18)"/>
  <ellipse cx="13" cy="22" rx="2.5" ry="1.3" fill="#E8A020" transform="rotate(-30 13 22)"/>
  <!-- Wheat grains (right) -->
  <ellipse cx="19" cy="14" rx="2.5" ry="1.3" fill="#E8A020" transform="rotate(30 19 14)"/>
  <ellipse cx="19.5" cy="18" rx="2.5" ry="1.3" fill="#E8A020" transform="rotate(30 19.5 18)"/>
  <ellipse cx="19" cy="22" rx="2.5" ry="1.3" fill="#E8A020" transform="rotate(30 19 22)"/>
  <!-- Top grain -->
  <ellipse cx="16" cy="11" rx="2" ry="2.5" fill="#E8A020"/>
</svg>
"""


def page_header(title, subtitle, icon="🌾", lang='en'):
    """
    FarmOS branded page header — earthy glass panel with wheat SVG logo,
    amber accent border, and DM Serif Display title.
    """
    inject_css()
    st.markdown(
        f"""<div style="
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(14px) saturate(140%);
            -webkit-backdrop-filter: blur(14px) saturate(140%);
            border: 1px solid rgba(232,160,32,0.18);
            border-left: 4px solid #E8A020;
            border-radius: 16px;
            padding: 20px 26px;
            margin-bottom: 20px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.04);
            display: flex;
            align-items: center;
            gap: 16px;
        ">
          <div style="flex-shrink:0;">{_WHEAT_LOGO_SVG}</div>
          <div>
            <div style="font-size:0.68rem;font-weight:700;color:#E8A020;letter-spacing:0.12em;
                        text-transform:uppercase;font-family:'Space Grotesk',sans-serif;
                        margin-bottom:2px;">FarmOS</div>
            <h1 style="font-family:'DM Serif Display',serif;font-size:1.65rem;font-weight:400;
                       margin:0 0 2px;color:#F5F0E8;letter-spacing:0.01em;">
              {icon} {title}
            </h1>
            <p style="color:rgba(245,240,232,0.60);font-size:0.82rem;margin:0;
                      font-family:'Space Grotesk',sans-serif;">
              {subtitle}
            </p>
          </div>
        </div>""",
        unsafe_allow_html=True
    )


def setup_page(title, subtitle, icon="🌾", explanation_en="", explanation_hi=""):
    """
    Standardizes the very beginning of every script — initializes lang state
    and renders the FarmOS-branded page header + optional explanation.
    """
    if 'lang' not in st.session_state:
        st.session_state.lang = 'en'
    if 'expert_mode' not in st.session_state:
        st.session_state.expert_mode = False
        
    lang = st.session_state.lang
    page_header(title, subtitle, icon, lang)

    # 1. Trigger proactive alert sync (Heartbeat)
    try:
        import data_loader as dl
        dl.sync_real_time_state()
    except Exception:
        pass

    # 2. Render Real-Time Alert Toasts (Popup alerts)
    render_real_time_toasts()

    if explanation_en or explanation_hi:
        info_text = explanation_hi if lang == 'hi' else explanation_en
        label = "💡 **यह पेज मुझे क्या बताता है?**" if lang == 'hi' else "💡 **What does this page tell me?**"
        st.info(f"{label}\n\n{info_text}")

    return lang
def render_real_time_toasts():
    """
    Checks for new critical alerts and renders them as Streamlit Toasts.
    Tracks 'last_toasted_ids' in session state to prevent repeat popups.
    """
    if "alerts" not in st.session_state:
        return

    if "last_toasted_ids" not in st.session_state:
        st.session_state.last_toasted_ids = set()

    # Find unread critical alerts not yet toasted
    critical_alerts = [
        a for a in st.session_state.alerts 
        if a.get('severity') == 'Critical' 
        and not a.get('read', False)
        and a.get('id') not in st.session_state.last_toasted_ids
    ]

    for alert in critical_alerts[:2]: # Show max 2 at a time to prevent UI clutter
        emoji = "🚨" if alert.get('severity') == 'Critical' else "⚠️"
        msg = f"{emoji} **{alert.get('type','Alert')}** in {alert.get('field','Field')}: {alert.get('message','')}"
        st.toast(msg)
        st.session_state.last_toasted_ids.add(alert.get('id'))
