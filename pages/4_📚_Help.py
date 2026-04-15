import streamlit as st
import data_loader as dl
import time

st.set_page_config(page_title="Help", page_icon="📚", layout="wide")

# Apply Styles
dl.apply_custom_css()

# Sidebar
dl.get_field_sidebar()
lang = st.session_state.lang

st.title("📚 " + ("मदद और जांच" if lang == "hi" else "Help & Diagnosis"))
st.markdown("### " + ("AI को फोटो दिखाएं और बीमारी का पता लगाएं" if lang == "hi" else "Show the AI a photo of your sick crop."))

col1, col2 = st.columns([1, 1])

with col1:
    instruction = "📸 टेक फोटो या अपलोड" if lang == "hi" else "📸 Take a Photo or Upload"
    sub_text = "बीमार हिस्से को दिखाएं।" if lang == "hi" else "Focus on the sick part."
    
    st.markdown(f"""<div style="background-color: #f1f5f9; padding: 20px; border-radius: 15px; border: 2px dashed #cbd5e1; text-align: center;">
<h4 style="margin: 0; color: #475569;">{instruction}</h4>
<p style="font-size: 0.9rem; color: #64748b;">{sub_text}</p>
</div>""", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        
        with st.spinner(("AI जांच कर रहा है..." if lang == "hi" else "AI is analyzing...")):
            time.sleep(2)
            analysis = dl.get_vision_analysis(uploaded_file)
            
        st.success(("जांच पूरी हुई!" if lang == "hi" else "Analysis Complete!"))
        
        remedy_label = "👨‍🌾 तुरंत समाधान:" if lang == "hi" else "👨‍🌾 What to do Now:"
        symptoms_label = "📍 लक्षण:" if lang == "hi" else "📍 Signs:"
        precaution_label = "⚠️ सावधानी:" if lang == "hi" else "⚠️ Caution:"

        st.markdown(f"""<div style="background-color: #fff; padding: 25px; border-radius: 15px; border: 2px solid #2ecc71; margin-top: 20px;">
<h2 style="margin: 0; color: #166534;">{analysis['issue']}</h2>
<hr style="opacity: 0.2;">
<p style="font-size: 1.1rem;"><strong>{symptoms_label}</strong> {analysis['symptoms']}</p>
<div style="background-color: #f0fdf4; padding: 15px; border-radius: 10px; border-left: 5px solid #22c55e; margin-bottom: 10px;">
<p style="margin: 0; font-weight: bold; color: #166534;">{remedy_label}</p>
<p style="font-size: 1.1rem; margin: 5px 0 0 0; color: #14532d;">{analysis['remedy']}</p>
</div>
<div style="background-color: #fffbeb; padding: 15px; border-radius: 10px; border-left: 5px solid #f59e0b;">
<p style="margin: 0; font-weight: bold; color: #92400e;">{precaution_label}</p>
<p style="font-size: 1.1rem; margin: 5px 0 0 0; color: #78350f;">{analysis['precaution']}</p>
</div>
</div>""", unsafe_allow_html=True)

with col2:
    if uploaded_file and 'analysis' in locals():
        video_text = f"### 📽️ " + (f"{analysis['issue']} सुधारने का तरीका" if lang == "hi" else f"How to fix {analysis['issue']}")
        st.markdown(video_text)
        st.video(analysis['video'])
        st.caption("Official Agricultural Guide (YouTube)")
    else:
        st.markdown("### 💡 " + ("आज की सलाह" if lang == "hi" else "Farmer Tips"))
        tips = dl.get_farmer_tips(lang)
        for tip in tips:
            st.markdown(f"""<div class="farmer-tip" style="border-left-color: {tip['color']};">
<span style="font-size: 2rem;">{tip['icon']}</span>
<p style="margin: 0; font-size: 1rem; color: #1e293b;">{tip['text']}</p>
</div>""", unsafe_allow_html=True)
            
        st.info("💡 " + ("धूप में साफ फोटो लें!" if lang == "hi" else "Take a clear photo in sunlight!"))

# KB Section
with st.expander("📚 " + ("अक्सर पूछे जाने वाले सवाल" if lang == "hi" else "Common Questions")):
    st.write("1. Fertilizer Guide")
    st.write("2. Water Management")
