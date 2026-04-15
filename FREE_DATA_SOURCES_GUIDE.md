# 🆓 Free Data Sources for Your Smart Farm System

This guide shows you how to get **100% FREE** satellite imagery and sensor data for your farm.

---

## 🛰️ Part 1: Free Satellite Data (Sentinel-2)

### What You Get
- **10-meter resolution** imagery of your farm
- **Updated every 5 days** (free!)
- **Multispectral bands** for NDVI, EVI, health analysis
- **Completely free** from European Space Agency

### Step-by-Step Instructions

#### Option A: Copernicus Browser (Easiest - No Account Needed)

1. **Visit:** https://browser.dataspace.copernicus.eu/

2. **Find Your Farm:**
   - Click the search icon (🔍)
   - Enter your farm's location (city name, coordinates, or address)
   - Zoom in until you can see your fields

3. **Search for Images:**
   - Click the calendar icon
   - Select date range (last 30 days recommended)
   - Click "Search"
   - Filter: Select "Sentinel-2" and "L2A" (atmospherically corrected)

4. **Download:**
   - Click on a cloud-free image over your farm
   - Click "Download" → Select "Full Product (.SAFE)"
   - Save to: `C:\CropSatelliteSensorMain\project\Sentinel_Data\`

#### Option B: Copernicus Data Space (Requires Free Account)

1. **Create Free Account:** https://dataspace.copernicus.eu/
2. **Login and Search:** Same as Option A
3. **Benefit:** Faster downloads, API access for automation

### What to Download

- **Product Type:** Sentinel-2 MSI Level-2A
- **Cloud Coverage:** < 10% (choose clearest day)
- **Frequency:** Download every 1-2 weeks for trend analysis

---

## 📱 Part 2: Free "IoT Sensors" (Manual Data Collection)

Since you don't have physical IoT sensors, you can collect data manually and still use the system!

### Method 1: Manual Measurements (Free!)

**Equipment Needed (Low Cost):**
- Soil pH meter: ₹500-1000 on Amazon
- Soil moisture meter: ₹300-500
- Digital thermometer: ₹200-400
- **Total:** ~₹1500 ($18 USD)

**How to Collect:**

1. **Daily Readings (5 minutes):**
   - Measure soil pH in 3 spots → average
   - Measure soil moisture in 3 spots → average
   - Record air temperature
   - Estimate crop health (0-4 scale: 0=poor, 4=excellent)

2. **Update CSV:**
   ```csv
   Date,Temperature,Humidity,Soil_Moisture,Crop_Health,Yield,Soil_pH,Soil_Temperature,Light_Intensity
   2026-02-15,28,65,55,3,60,6.5,22,800
   ```

3. **Add to `sample_ground_sensor_data.csv`** - Just append new rows!

### Method 2: Weather API (Automated & Free!)

Use free weather APIs to get temperature, humidity automatically:

**Create this script:** `auto_weather_update.py`

```python
import requests
import pandas as pd
from datetime import datetime

# Free API - No credit card needed!
API_KEY = "YOUR_FREE_KEY"  # Get from openweathermap.org
FARM_LAT = 28.6139  # Replace with your farm latitude
FARM_LON = 77.2090  # Replace with your farm longitude

def get_weather_data():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={FARM_LAT}&lon={FARM_LON}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    
    return {
        'Date': datetime.now().strftime('%Y-%m-%d'),
        'Temperature': data['main']['temp'],
        'Humidity': data['main']['humidity'],
        'Soil_Moisture': 50,  # Manual measurement needed
        'Crop_Health': 3,     # Manual assessment needed
        'Yield': 60,          # Estimate
        'Soil_pH': 6.5,       # Manual measurement needed
        'Soil_Temperature': data['main']['temp'] - 5,  # Approximation
        'Light_Intensity': 800  # Approximation
    }

def update_csv():
    new_data = get_weather_data()
    df = pd.read_csv('sample_ground_sensor_data.csv')
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv('sample_ground_sensor_data.csv', index=False)
    print("✅ Data updated!")

if __name__ == "__main__":
    update_csv()
```

**Get Free API Key:**
1. Go to: https://openweathermap.org/api
2. Sign up (free tier: 1000 calls/day)
3. Copy your API key
4. Replace `YOUR_FREE_KEY` in script

**Run daily:** `python auto_weather_update.py`

### Method 3: Smartphone Apps (Free!)

**For Android/iOS:**
- **Soil pH:** "Soil pH Meter" app (uses camera - less accurate but free)
- **Weather:** Built-in weather app for temp/humidity
- **Light:** "Light Meter" app (uses phone camera)

Record in a notebook → Update CSV weekly

---

## 🗺️ Part 3: Get Your Farm Coordinates (Free!)

### Method 1: Google Maps
1. Go to: https://www.google.com/maps
2. Find your farm
3. Right-click on your field
4. Click coordinates (e.g., "28.6139, 77.2090")
5. Copy and use for satellite data search

### Method 2: GPS on Phone
1. Stand in your field
2. Open Google Maps
3. Tap blue dot (your location)
4. Coordinates shown at bottom

---

## 📊 Part 4: Update Your System

### Step 1: Add Your Coordinates

Edit `alert_config.py`:

```python
def setup_field_locations(self):
    return {
        'North': {
            'coordinates': (YOUR_LAT, YOUR_LON),  # ← Add your coordinates
            'area_acres': 10,  # ← Your actual field size
            'crop_type': 'Wheat',  # ← Your crop
            'soil_type': 'Loamy'
        }
    }
```

### Step 2: Process Satellite Data

```bash
# After downloading .SAFE file to Sentinel_Data/
python enhanced_hybrid_system.py
```

### Step 3: Update Sensor Data

```bash
# Run weather script daily
python auto_weather_update.py

# OR manually edit sample_ground_sensor_data.csv
```

### Step 4: View Dashboard

```bash
streamlit run impactful_dashboard.py
```

---

## 💰 Cost Breakdown

| Item | Cost |
|------|------|
| Sentinel-2 Satellite Data | **FREE** ✅ |
| Weather API (OpenWeatherMap) | **FREE** ✅ (1000 calls/day) |
| Google Maps Coordinates | **FREE** ✅ |
| Basic Soil Meters (Optional) | ₹1500 (~$18) |
| **Total Monthly Cost** | **₹0 - ₹1500 one-time** |

---

## 🎯 Quick Start Checklist

- [ ] Get farm coordinates from Google Maps
- [ ] Create free account on Copernicus Data Space
- [ ] Download 1 Sentinel-2 image for your farm
- [ ] Place .SAFE file in `Sentinel_Data/` folder
- [ ] Sign up for free OpenWeatherMap API
- [ ] Create `auto_weather_update.py` script
- [ ] Run `python enhanced_hybrid_system.py`
- [ ] Run `python auto_weather_update.py`
- [ ] Launch dashboard: `streamlit run impactful_dashboard.py`
- [ ] See YOUR real farm data! 🎉

---

## 📞 Need Help?

**Common Issues:**

**Q: Sentinel download is slow**  
A: Files are 500MB-1GB. Use a download manager or try at night.

**Q: Can't find my farm on satellite**  
A: Make sure cloud coverage < 20%. Try different dates.

**Q: Weather API not working**  
A: Check API key is correct. Free tier has 60 calls/hour limit.

**Q: No .SAFE files found**  
A: Ensure folder structure: `Sentinel_Data/S2A_MSIL2A_...SAFE/`

---

## 🚀 Next Level (Still Free!)

Once comfortable, automate everything:

1. **Schedule satellite downloads** - Use Copernicus API
2. **Auto-run processing** - Windows Task Scheduler
3. **Daily weather updates** - Cron job for `auto_weather_update.py`
4. **Host dashboard online** - Streamlit Cloud (free tier)

**Result:** Fully automated smart farm system for ₹0/month! 🌾
