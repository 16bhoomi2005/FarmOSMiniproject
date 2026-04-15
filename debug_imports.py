import os

def log(msg):
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

if os.path.exists("debug.log"):
    os.remove("debug.log")

log("Starting imports...")

try:
    import streamlit as st
    log("✅ streamlit imports")
except Exception as e:
    log(f"❌ streamlit failed: {e}")

try:
    import data_loader as dl
    log("✅ data_loader imports")
except Exception as e:
    log(f"❌ data_loader failed: {e}")

try:
    import plotly.express as px
    log("✅ plotly.express imports")
except Exception as e:
    log(f"❌ plotly.express failed: {e}")

try:
    import satellite_service
    log("✅ satellite_service imports")
except Exception as e:
    log(f"❌ satellite_service failed: {e}")

log("🎉 Imports done!")
