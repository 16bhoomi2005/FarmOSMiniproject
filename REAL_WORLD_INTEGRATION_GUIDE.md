# 🌾 Rice Impact: Zero-to-Hero Production Integration Guide

This guide is designed for beginners. It will take you from absolute zero (unboxing your Arduino) to a fully live, cloud-integrated Rice Farm Dashboard.

---

## 🛑 Phase 0: Status Check
**STATUS: INTEGRATED!** I have already updated `data_loader.py` and `arduino_bridge.py` with your connection string: `mongodb+srv://bhoomivaishya...`. 

The platform is currently in **"Real Data Only"** mode. If your database is empty, the dashboard will wait for your first sync.

---

## ☁️ Phase 1: Verify your Cloud Brain (MongoDB)
1.  **Database Name:** The system expects a database named `RiceFarmDB`.
2.  **Collection Name:** The system expects a collection named `live_readings`.
3.  **IP Whitelist (Crucial):** Go to MongoDB Atlas -> "Network Access" -> **"Allow Access from Anywhere"** (0.0.0.0/0).

---

## 🧪 Phase 2: Instant Connection Test (Do This Now!)
Before touching any wires, let's verify your cloud-to-dashboard link.
1. Run: `python cloud_tester.py`
2. This pushes a "fake" real packet to your MongoDB.
3. **Check Dashboard:** If the "Canal Side" health metrics change, your system is ready!

---

## 🛰️ Phase 3: Satellite Intelligence (The Eyes)
Activate the satellite maps that use Google Earth Engine (GEE).
1.  **Register:** [earthengine.google.com](https://earthengine.google.com/).
2.  **Authenticate:** Once approved, type `earthengine authenticate` in your terminal. This will open a browser window to link your account.

---

## 🛠️ Phase 4: Arduino & Hardware (The Heartbeat)
Now we build the physical system. 
### 1. Physical Wiring
```text
SENSORS WIRING GUIDE:
---------------------
[DHT22 (Temp)]   -> Data: Pin 2, VCC: 5V, GND: GND
[Ultrasonic]     -> Trig: Pin 3, Echo: Pin 4, VCC: 5V, GND: GND
[Soil Moisture]  -> Data: A0, VCC: 5V, GND: GND
```

### 2. The Code (`arduino_sketch.ino`)
Upload this to your Arduino using the Arduino IDE. Keep the Arduino plugged into your USB port!

---

## 🌉 Phase 5: The Python Serial Bridge
This final step links your Arduino to the internet.
1.  **Install:** `pip install pymongo dnspython pyserial`
2.  **Run:** `python arduino_bridge.py`
3.  **Monitor:** Check your terminal for "✅ Sync Successful" messages.

---

> [!IMPORTANT]
> **Plot Mapping:** The name in your Arduino code (`Canal Side`) must match the dashboard plot names exactly. 
