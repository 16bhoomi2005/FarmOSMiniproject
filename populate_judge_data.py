import pymongo
import datetime
import random
import os
from dotenv import load_dotenv

# Load MONGO_URI from .env
load_dotenv()
MONGO_URI = os.environ.get('MONGO_URI')

if not MONGO_URI:
    print("❌ MONGO_URI not found in .env file!")
    exit(1)

def seed_database():
    print("🚀 Starting Master Database Seeding (Judge-Ready v2)...")
    print("---------------------------------------")
    
    try:
        # Increase connection timeout for slow networks
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("\n📝 FIX: This is likely because your IP is not whitelisted in MongoDB Atlas.")
        print("Please run this script on your LOCAL machine for it to work.")
        return

    # 1. DATABASE: farm_intelligence
    db_intel = client.farm_intelligence
    
    # --- Collection: sensor_data ---
    print("🛰️  Seeding 'sensor_data' (30 days of telemetry)...")
    db_intel.sensor_data.delete_many({}) 
    
    fields = ["North", "South", "East", "West", "Center", "NW", "NE", "SW", "SE"]
    sensor_records = []
    now = datetime.datetime.now()
    
    for day in range(30, -1, -1):
        for hour in [8, 20]:
            timestamp = now - datetime.timedelta(days=day)
            timestamp = timestamp.replace(hour=hour, minute=random.randint(0,59))
            for f in fields:
                temp = 24 + random.uniform(2, 8)
                sensor_records.append({
                    "timestamp": timestamp.isoformat(),
                    "Temperature": round(temp, 2),
                    "Humidity": round(65 + random.uniform(-10, 15), 2),
                    "Soil_Moisture": round(60 + random.uniform(-15, 20), 2),
                    "Crop_Health": round(0.5 + random.uniform(0, 0.3), 3),
                    "Yield": round(2.5 + random.uniform(-0.5, 0.5), 2),
                    "Soil_pH": round(6.2 + random.uniform(-0.4, 0.4), 1),
                    "Field": f,
                    "Date": timestamp.strftime("%Y-%m-%d")
                })
    db_intel.sensor_data.insert_many(sensor_records)

    # --- Collection: alerts ---
    print("🚨 Seeding 'alerts' (Historical audit log)...")
    db_intel.alerts.delete_many({})
    alerts = [
        {"severity": "Critical", "field": "North", "message": "Critical Water Stress Detected via Satellite NDWI"},
        {"severity": "Warning", "field": "Center", "message": "Early signs of Brown Spot emerging"},
        {"severity": "Warning", "field": "East", "message": "Nitrogen levels dropping"},
        {"severity": "Critical", "field": "West", "message": "Night temperature drop detected (Risk of Blast)"},
    ]
    for a in alerts:
        a["timestamp"] = (now - datetime.timedelta(days=random.randint(1, 15))).isoformat()
    db_intel.alerts.insert_many(alerts)

    # --- Collection: market_prices ---
    print("📈 Seeding 'market_prices' (Historical Mandi trends)...")
    db_intel.market_prices.delete_many({})
    market_records = []
    for day in range(10, -1, -1):
        t = now - datetime.timedelta(days=day)
        market_records.append({
            "timestamp": t.isoformat(),
            "commodity": "Paddy (Dhan)",
            "market": "Bhandara Mandi",
            "modal_price": 2150 + random.randint(-50, 50)
        })
    db_intel.market_prices.insert_many(market_records)

    # 2. DATABASE: RiceFarmDB
    db_rice = client.RiceFarmDB
    
    # --- Collection: field_history ---
    print("⏳ Seeding 'field_history' (Timeline snapshots)...")
    db_rice.field_history.delete_many({})
    history_records = []
    for day in range(25, -1, -5):
        t = now - datetime.timedelta(days=day)
        history_records.append({
            "timestamp": t.isoformat(),
            "health_score": round(0.4 + (day/50), 2),
            "moisture_score": round(0.6 + random.uniform(-0.1, 0.2), 2),
            "event": "Regular Check"
        })
    db_rice.field_history.insert_many(history_records)

    # --- Collection: satellite_log ---
    print("🛰️  Seeding 'satellite_log' (Audit trail of GEE scans)...")
    db_rice.satellite_log.delete_many({})
    sat_records = []
    for i in range(5):
        t = now - datetime.timedelta(days=i*5)
        sat_records.append({
            "timestamp": t.isoformat(),
            "mission": "Sentinel-2 L2A",
            "avg_ndvi": round(0.65 + random.uniform(-0.1, 0.1), 3),
            "indices": ["NDVI", "EVI", "NDRE", "NDWI"]
        })
    db_rice.satellite_log.insert_many(sat_records)

    print("\n✨ DATABASE SEEDING COMPLETE! Your FarmOS is now 'Judge-Ready'.")

if __name__ == "__main__":
    seed_database()
