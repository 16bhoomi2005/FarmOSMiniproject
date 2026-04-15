# 🔌 Smart Farm Hardware & Wiring Guide

This guide provides the exact specifications and wiring instructions to connect your Bhandara Farm to the AI Dashboard using an Arduino.

## 🛒 Required Hardware
| Component | Description | Purpose |
| :--- | :--- | :--- |
| **Arduino Uno / Nano** | Main Microcontroller | Processes sensor signals |
| **DHT11 / DHT22** | Temp & Humidity Sensor | Records ambient climate |
| **Soil Moisture Sensor** | Analog Capacitive Sensor | Measures root-level hydration |
| **pH Sensor (Analog)** | Liquid pH Probe | Monitors soil acidity |
| **Jumper Wires** | M-M / M-F | Connections |
| **Breadboard** | Mini / Full | Layout sensors |

## 🛠️ Wiring Diagram (Pinout)

### 1. DHT11 (Climate)
- **VCC:** 5V (Arduino)
- **GND:** GND (Arduino)
- **Data (S / Out):** **Digital Pin 2**

### 2. Soil Moisture (Hydration)
- **VCC:** 3.3V or 5V
- **GND:** GND
- **Analog Output:** **Analog Pin A0**

### 3. pH Sensor (Soil Health)
- **VCC:** 5V
- **GND:** GND
- **Analog Output:** **Analog Pin A1**

## 💻 Software Setup
1. Open the [arduino_sketch.ino](file:///c:/CropSatelliteSensorMain/project/arduino_sketch.ino) in the Arduino IDE.
2. Select your board (Uno/Nano) and COM Port.
3. Click **Upload**.
4. Open the Serial Monitor with baud rate **115200** to verify readings.

## 📡 Syncing with Dashboard
Once the Arduino is plugged in via USB:
1. Open a terminal in the project folder.
2. Run: `python arduino_sensor_reader.py`
3. The dashboard will automatically update to **"100% REAL"** sensors.

---
> [!NOTE]
> For best results in large fields, use waterproof sensors and a long USB cable or a WiFi-enabled board like the ESP32.
