# 🌾 Connecting YOUR Real Farm Data

## Current Status
Your dashboard is currently displaying **sample/demo data** from `sample_ground_sensor_data.csv`. To see YOUR actual farm data, follow these steps:

## Step 1: Replace Sample Sensor Data with Your IoT Data

### Option A: Manual CSV Update
1. Open `sample_ground_sensor_data.csv`
2. Replace the sample data with your actual sensor readings
3. **Required columns:**
   - `Date` - Timestamp of reading
   - `Temperature` - Air temperature (°C)
   - `Humidity` - Relative humidity (%)
   - `Soil_Moisture` - Soil moisture (%)
   - `Crop_Health` - Health score (0-4 scale)
   - `Yield` - Yield estimate (tons/ha)
   - `Soil_pH` - Soil pH level
   - `Soil_Temperature` - Soil temperature (°C)
   - `Light_Intensity` - Light intensity (lux)

### Option B: Automated IoT Integration
Create a script to pull data from your IoT platform:

```python
# example_iot_connector.py
import pandas as pd
from your_iot_platform import get_sensor_data  # Replace with your platform

def update_sensor_data():
    # Fetch from your IoT platform
    data = get_sensor_data(device_ids=['sensor1', 'sensor2'])
    
    # Convert to required format
    df = pd.DataFrame({
        'Date': data['timestamps'],
        'Temperature': data['temp_readings'],
        'Humidity': data['humidity_readings'],
        # ... map all required columns
    })
    
    # Save to CSV
    df.to_csv('sample_ground_sensor_data.csv', index=False)
    print("✅ Sensor data updated!")

if __name__ == "__main__":
    update_sensor_data()
```

## Step 2: Process Your Sentinel-2 Satellite Data

1. **Download your field's Sentinel-2 imagery:**
   - Visit [Copernicus Open Access Hub](https://scihub.copernicus.eu/)
   - Search for your farm coordinates
   - Download `.SAFE` files for your area

2. **Place files in the correct location:**
   ```
   project/
   └── Sentinel_Data/
       └── S2A_MSIL2A_20240215T...SAFE/
   ```

3. **Run the processing script:**
   ```bash
   python enhanced_hybrid_system.py
   ```

4. **Verify output:**
   - Check for `latest_satellite_features.json`
   - This file contains real NDVI, EVI, GNDVI from YOUR fields

## Step 3: Generate Real Alerts

Run the alert system with your data:
```bash
python alert_config.py
```

This will analyze your sensor data and create `active_alerts.json` with field-specific alerts.

## Step 4: View Your Dashboard

```bash
streamlit run impactful_dashboard.py
```

Now you'll see:
- ✅ **Real sensor trends** from your IoT devices
- ✅ **Real satellite health scores** from your fields
- ✅ **Real alerts** based on your thresholds
- ✅ **Real yield predictions** from your data

## Troubleshooting

### "Unknown Field" in Alerts
- Ensure `active_alerts.json` has field names as keys
- Run `python alert_config.py` to regenerate

### "No satellite data found"
- Verify `.SAFE` files are in `Sentinel_Data/` folder
- Check file permissions
- Run `python enhanced_hybrid_system.py` with `-u` flag for unbuffered output

### Sensor Data Not Updating
- Check CSV file format matches exactly
- Ensure dates are in YYYY-MM-DD format
- Verify no missing values in required columns

## Next Steps

1. **Set up automated updates:** Schedule `example_iot_connector.py` to run hourly
2. **Configure alert thresholds:** Edit `alert_config.py` to match your crop types
3. **Add more fields:** Update `field_locations` in `alert_config.py`
4. **Deploy to production:** Host dashboard on a server for 24/7 access
