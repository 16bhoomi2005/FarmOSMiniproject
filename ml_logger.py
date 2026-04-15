import pandas as pd
import os
import json
from datetime import datetime
import data_loader as dl

TRAINING_DATA_FILE = 'training_dataset.csv'

def log_daily_snapshot(label="Unknown", plot_name="All"):
    """
    Captures current environmental features and saves them to a CSV for ML training.
    Features: NDVI, Hum, Temp, Soil Moisture, Rain Streak, Growth Stage.
    Target: Label (Healthy, Rice Blast, etc.)
    """
    try:
        weather = dl.load_current_weather()
        sectors = dl.get_sector_analysis()
        life_cycle = dl.get_rice_life_cycle()
        
        # Get mean NDVI or sector-specific NDVI
        if plot_name == "All":
            ndvi_vals = [s['ndvi'] for s in sectors.values() if s['ndvi'] is not None]
            ndvi = sum(ndvi_vals) / len(ndvi_vals) if ndvi_vals else 0.5
        else:
            ndvi = sectors.get(plot_name, {}).get('ndvi', 0.5)

        # Build feature dict
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "plot": plot_name,
            "ndvi": round(ndvi, 3),
            "temp": weather.get('current', {}).get('temp', 25),
            "humidity": weather.get('current', {}).get('humidity', 70),
            "rain_mm": 0, # Would ideally come from daily history
            "growth_stage": life_cycle.get('stage', 'Unknown'),
            "days_after_transplant": life_cycle.get('days_after_transplant', 0),
            "label": label  # The Ground Truth
        }

        df_new = pd.DataFrame([snapshot])

        if not os.path.exists(TRAINING_DATA_FILE):
            df_new.to_csv(TRAINING_DATA_FILE, index=False)
        else:
            df_new.to_csv(TRAINING_DATA_FILE, mode='a', header=False, index=False)
        
        print(f"✅ ML Snapshot Logged: {label} for {plot_name}")
        return True
    except Exception as e:
        print(f"❌ Error logging ML snapshot: {e}")
        return False

if __name__ == "__main__":
    # Test logging
    log_daily_snapshot("Healthy", "Center Plot")
