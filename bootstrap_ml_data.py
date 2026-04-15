import pandas as pd
import random
from datetime import datetime, timedelta

def bootstrap_data():
    """Generates 150+ realistic training samples focusing on Disease vs Environmental Stress."""
    print("🌾 Bootstrapping 150+ enhanced farm observations...")
    
    stages = ["Vegetative", "Tillering", "Panicle Initiation", "Flowering/Grain Filling", "Ripening"]
    labels = ["Healthy", "Rice Blast (Fungal)", "Bacterial Leaf Blight", "BPH Infestation", "Water Stress/Drought"]
    plots = ["North Plot", "South Plot", "Canal Side", "Upper Patch", "Lowland Patch"]
    
    data = []
    base_date = datetime.now() - timedelta(days=90)
    
    for i in range(180):
        # Move forward in time
        obs_date = base_date + timedelta(days=i * 0.5)
        dat = (i // 2) % 120 # Cyclical DAT
        
        # Determine growth stage based on DAT
        if dat < 30: stage = stages[0]
        elif dat < 50: stage = stages[1]
        elif dat < 70: stage = stages[2]
        elif dat < 90: stage = stages[3]
        else: stage = stages[4]
        
        roll = random.random()
        
        if roll > 0.4:
            # 🟢 HEALTHY CASE
            label = "Healthy"
            ndvi = round(random.uniform(0.65, 0.85), 3)
            temp = round(random.uniform(24, 32), 1)
            hum = round(random.uniform(55, 75), 1)
        elif roll > 0.25:
            # 🍄 RICE BLAST (High Hum, Cool-ish Temp, Moderate NDVI)
            label = "Rice Blast (Fungal)"
            ndvi = round(random.uniform(0.35, 0.55), 3)
            temp = round(random.uniform(22, 26), 1)
            hum = round(random.uniform(85, 95), 1)
        elif roll > 0.15:
            # 🦠 BLIGHT (Saturated Hum, High Temp, Low-ish NDVI)
            label = "Bacterial Leaf Blight"
            ndvi = round(random.uniform(0.3, 0.5), 3)
            temp = round(random.uniform(28, 36), 1)
            hum = round(random.uniform(90, 98), 1)
        elif roll > 0.08:
            # 🦗 BPH (Dense Canopy, Warm, Humid)
            label = "BPH Infestation"
            ndvi = round(random.uniform(0.5, 0.7), 3)
            temp = round(random.uniform(26, 32), 1)
            hum = round(random.uniform(80, 92), 1)
        else:
            # 💧 WATER STRESS (Low Hum, High Temp, Very Low NDVI)
            # This is what the user encountered: low NDVI but also low humidity
            label = "Water Stress/Drought"
            ndvi = round(random.uniform(0.2, 0.35), 3)
            temp = round(random.uniform(30, 38), 1)
            hum = round(random.uniform(20, 45), 1)

        data.append({
            "timestamp": obs_date.isoformat(),
            "date": obs_date.strftime("%Y-%m-%d"),
            "plot": random.choice(plots),
            "ndvi": ndvi,
            "temp": temp,
            "humidity": hum,
            "rain_mm": round(random.uniform(0, 15), 1) if (hum > 85 and roll > 0.1) else 0,
            "growth_stage": stage,
            "days_after_transplant": dat,
            "label": label
        })
    
    df = pd.DataFrame(data)
    df.to_csv('training_dataset.csv', index=False)
    print(f"✅ Created training_dataset.csv with {len(df)} samples.")

if __name__ == "__main__":
    bootstrap_data()
