# 🔧 Arduino Deployment - Step-by-Step Guide

## 📦 **STEP 1: Shopping List**

### What to Buy (Total: ~₹2,500 / $35):

```
□ Arduino Uno R3          - ₹500  ($8)
□ DHT22 Sensor           - ₹350  ($5)
□ Soil Moisture Sensor   - ₹200  ($3)
□ Jumper Wires (M-M)     - ₹100  ($2)
□ Breadboard (optional)  - ₹150  ($2)
□ USB Cable (A to B)     - ₹200  ($3)
□ Weatherproof Box       - ₹500  ($8)
□ Power Bank (10000mAh)  - ₹800  ($12)
```

**Where to Buy in India:**
- Amazon.in
- Robu.in
- ElectronicComp.com
- Local electronics market

---

## 🔌 **STEP 2: Wiring (15 minutes)**

### DHT22 Temperature/Humidity Sensor:

```
DHT22 Pin 1 (VCC)  →  Arduino 5V
DHT22 Pin 2 (DATA) →  Arduino Pin 2
DHT22 Pin 3 (NC)   →  Not connected
DHT22 Pin 4 (GND)  →  Arduino GND
```

### Soil Moisture Sensor:

```
Sensor VCC  →  Arduino 5V
Sensor GND  →  Arduino GND
Sensor A0   →  Arduino A0
```

### Visual Diagram:

```
        Arduino Uno
    ┌─────────────────┐
    │                 │
    │  5V ────────────┼──→ DHT22 VCC
    │  Pin 2 ─────────┼──→ DHT22 DATA
    │  GND ───────────┼──→ DHT22 GND
    │                 │
    │  5V ────────────┼──→ Soil Sensor VCC
    │  A0 ────────────┼──→ Soil Sensor A0
    │  GND ───────────┼──→ Soil Sensor GND
    │                 │
    │  USB ───────────┼──→ Computer/Power Bank
    └─────────────────┘
```

---

## 💻 **STEP 3: Upload Arduino Code (10 minutes)**

### A. Install Arduino IDE:
1. Download from: https://www.arduino.cc/en/software
2. Install (Windows/Mac/Linux)
3. Open Arduino IDE

### B. Install DHT Library:
1. In Arduino IDE: `Tools` → `Manage Libraries`
2. Search: "DHT sensor library"
3. Install "DHT sensor library by Adafruit"
4. Also install "Adafruit Unified Sensor"

### C. Upload Sketch:
1. Open: `arduino_sketch.ino` (from your project)
2. Connect Arduino via USB
3. Select: `Tools` → `Board` → `Arduino Uno`
4. Select: `Tools` → `Port` → `COM3` (or your port)
5. Click: **Upload** button (→)
6. Wait for "Done uploading"

### D. Test:
1. Open: `Tools` → `Serial Monitor`
2. Set baud rate: `9600`
3. You should see JSON output every 5 seconds:
   ```json
   {"temp":25.3,"humidity":65.2,"soil_moisture":45}
   ```

---

## 🧪 **STEP 4: Calibrate Soil Sensor (5 minutes)**

### Find AIR_VALUE:
1. Keep sensor in open air
2. Note the reading (e.g., 850)
3. Update in `arduino_sketch.ino`:
   ```cpp
   #define AIR_VALUE 850
   ```

### Find WATER_VALUE:
1. Dip sensor in water (only the prongs!)
2. Note the reading (e.g., 400)
3. Update in `arduino_sketch.ino`:
   ```cpp
   #define WATER_VALUE 400
   ```

### Re-upload:
1. Click Upload again
2. Now moisture shows 0-100%

---

## 🐍 **STEP 5: Run Python Reader (2 minutes)**

### A. Find COM Port:
```bash
# Windows:
python -m serial.tools.list_ports

# Linux/Mac:
ls /dev/tty*
```

### B. Update Port in Code:
Open `arduino_sensor_reader.py`:
```python
# Line 25: Change to your port
self.port = 'COM3'  # Windows
# or
self.port = '/dev/ttyUSB0'  # Linux
```

### C. Run:
```bash
cd C:\CropSatelliteSensorMain\project
python arduino_sensor_reader.py
```

### D. You Should See:
```
🌾 Arduino Sensor Reader Started
📡 Connecting to COM3...
✅ Connected to Arduino

📊 Reading 1 (2026-02-15 17:15:30)
   Temperature: 25.3°C
   Humidity: 65.2%
   Soil Moisture: 45.0%
✅ CSV updated: sample_ground_sensor_data.csv

📊 Reading 2 (2026-02-15 17:20:30)
...
```

---

## 🏡 **STEP 6: Field Installation (30 minutes)**

### A. Prepare Weatherproof Box:
1. Drill holes for:
   - USB cable (power)
   - Sensor wires (DHT22 + soil)
2. Use silicone sealant around holes
3. Mount Arduino inside with double-sided tape

### B. Install in Field:
1. Choose location:
   - Representative of field
   - Near crop rows
   - Accessible for maintenance

2. Mount box:
   - 1-2 feet above ground (on pole/fence)
   - Facing north (avoid direct sun)

3. Place sensors:
   - DHT22: Inside box (air temp/humidity)
   - Soil sensor: Bury at root depth (6-8 inches)
   - Keep wires protected

### C. Power:
**Option 1: USB Power Bank**
- Connect Arduino to 10000mAh power bank
- Lasts 3-5 days
- Replace/recharge weekly

**Option 2: Solar (Recommended)**
- 5V solar panel (₹800)
- 18650 battery holder (₹300)
- Lasts indefinitely

### D. Connect to Computer:
**Option 1: Laptop in Field**
- Bring laptop to field
- Run Python script
- Leave running (impractical)

**Option 2: Raspberry Pi (Best)**
- Install Raspberry Pi in weatherproof box
- Auto-run Python script on boot
- Access dashboard remotely

**Option 3: WiFi Arduino (Advanced)**
- Use ESP32 instead of Arduino Uno
- Sends data over WiFi
- No computer needed in field

---

## 📊 **STEP 7: Verify Dashboard (5 minutes)**

### A. Check CSV:
```bash
# Open in Excel/Notepad
sample_ground_sensor_data.csv

# Should have new rows every 5 minutes:
Date,Temperature,Humidity,Soil_Moisture,...
2026-02-15,25.3,65.2,45.0,...
```

### B. Run Dashboard:
```bash
streamlit run Home.py
```

### C. Verify:
- ✅ "Ground Sensors: 🟢 Active" in sidebar
- ✅ Latest temp/humidity in "Quick Stats"
- ✅ Graphs updating with new data

---

## 🔧 **TROUBLESHOOTING**

### Arduino Not Detected:
```bash
# Install CH340 driver (for clone boards)
# Download from: sparks.gogo.co.nz/ch340.html
```

### Serial Port Error:
```python
# Try different baud rates
ser = serial.Serial('COM3', 9600)  # Try 115200 if 9600 fails
```

### No Data in CSV:
```bash
# Check file permissions
# Run Python as administrator (Windows)
# Check CSV path is correct
```

### Sensor Reading 0:
```
DHT22: Check wiring, wait 2 seconds between reads
Soil: Calibrate AIR_VALUE and WATER_VALUE
```

---

## 📱 **BONUS: Remote Access**

### Access Dashboard from Phone:

**If on Same WiFi:**
```
1. Find computer IP: ipconfig (Windows) or ifconfig (Linux)
2. On phone browser: http://192.168.1.X:8501
```

**If on Different Network:**
```
1. Deploy to Streamlit Cloud (free)
2. Access from anywhere: yourfarm.streamlit.app
```

---

## ✅ **SUCCESS CHECKLIST**

After completing all steps, you should have:

- [x] Arduino wired and powered
- [x] Sensors reading correct values
- [x] Python script running continuously
- [x] CSV updating every 5 minutes
- [x] Dashboard showing real-time data
- [x] Weatherproof installation in field

**Congratulations! Your Smart Farm is now LIVE!** 🎉

---

## 📞 **Need Help?**

**Common Issues:**
- Wiring wrong → Check diagram above
- Port not found → Install CH340 driver
- No readings → Calibrate sensors
- CSV not updating → Check file path

**Next Steps:**
1. Let it run for 1 week
2. Collect baseline data
3. Download recent satellite imagery
4. Compare sensor data with NDVI trends
5. Start making data-driven decisions!

**Your farm is now smarter than 99% of farms in India!** 🚀
