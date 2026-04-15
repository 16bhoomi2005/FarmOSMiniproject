import streamlit as st
import pymongo
import os
from datetime import datetime
import time

def get_mongo_uri():
    try:
        if hasattr(st, "secrets") and st.secrets and "MONGODB_URI" in st.secrets:
            return st.secrets["MONGODB_URI"]
    except Exception:
        pass
    return os.environ.get("MONGODB_URI")

def check_connection():
    uri = get_mongo_uri()
    if not uri:
        # Skip silently, use sim_engine data (as requested)
        return False
        
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        st.success("✅ MongoDB connected successfully!")
        return True
    except Exception as e:
        st.warning(f"⚠️ MongoDB unreachable, using simulation. Details: {e}")
        return False

def push_test_data():
    uri = get_mongo_uri()
    if not uri:
        st.info("No MONGODB_URI credentials found. Setup secrets.toml to push data.")
        return
        
    try:
        st.write("🔗 Connecting to MongoDB Atlas...")
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
        db = client.RiceFarmDB
        collection = db.live_readings

        st.write("📡 Generating 1x REAL data packet for 'Canal Side'...")
        test_payload = {
            "node_id": "Sensor-01 (Canal Side)",
            "location": "Canal Side",
            "air_temp": 29.5,
            "air_dampness": 62.0,
            "soil_wetness": 55,
            "water_depth": 3.8,
            "battery": "98%",
            "timestamp": datetime.utcnow()
        }

        collection.update_one(
            {"location": "Canal Side"},
            {"$set": test_payload},
            upsert=True
        )

        st.success("✅ SUCCESS! Test data pushed to Cloud.")
        st.write("🌾 Go to your Dashboard and refresh—you should see 'Canal Side' data update now.")
        
    except Exception as e:
        st.error(f"❌ Error: {e}")

if __name__ == "__main__":
    st.title("☁️ Cloud Connection Tester")
    st.markdown("Check MongoDB Atlas connectivity and push test sensor packets.")
    
    if st.button("Ping Database"):
        check_connection()
        
    if st.button("Push Test Sensor Data"):
        push_test_data()
