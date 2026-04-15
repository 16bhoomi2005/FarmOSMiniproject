import serial
import pymongo
import json
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

# --- CONFIGURATION ---
SERIAL_PORT = os.getenv('SERIAL_PORT', 'COM3')
BAUD_RATE   = int(os.getenv('BAUD_RATE', 9600))
MONGO_URI   = os.getenv('MONGO_URI', "mongodb+srv://bhoomivaishya06_db_user:GuysqjmNsQjvgZuj@cluster0.wqfcwpe.mongodb.net/?appName=Cluster0")

print("🌾 Rice Impact: Robust Arduino-to-Cloud Bridge")
print("---------------------------------------------")

def connect_to_mongo():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client.RiceFarmDB
        collection = db.live_readings
        print("✅ Connected to MongoDB Atlas")
        return collection
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        return None

def main():
    collection = connect_to_mongo()
    if not collection:
        return

    while True:
        ser = None
        try:
            # 1. Connect to Arduino
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            time.sleep(2) # Wait for Arduino to reset
            print(f"✅ Connected to Arduino on {SERIAL_PORT}")
            print("🚀 Listening for data... (Press Ctrl+C to stop)")

            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        try:
                            # Parse JSON from Arduino
                            data = json.loads(line)
                            
                            # Map JSON values (Calibration can be added here)
                            temp  = data.get('temp', 0.0)
                            hum   = data.get('humidity', 0.0)
                            moist = data.get('soil_moisture', 0.0)
                            depth = data.get('water_depth', 0.0) # Added depth
                            bat   = data.get('battery', '100%')
                            node  = data.get('node_id', 'Sensor-01')
                            
                            # Determine location (can be passed from Arduino or mapped here)
                            plot_name = data.get('location', "Canal Side") 

                            payload = {
                                "node_id": f"{node} ({plot_name})",
                                "location": plot_name,
                                "air_temp": temp,
                                "air_dampness": hum,
                                "soil_wetness": moist,
                                "water_depth": depth,
                                "timestamp": datetime.utcnow(),
                                "battery": bat,
                                "status": "Online",
                                "source": "Hardware"
                            }

                            # 3. Push to MongoDB
                            collection.update_one(
                                {"location": plot_name}, 
                                {"$set": payload}, 
                                upsert=True
                            )
                            
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Synced {node}: {temp}°C, {moist}% Moist, {depth}cm depth")
                            
                        except json.JSONDecodeError:
                            if "Ready" in line:
                                print(f"📡 Device Ready: {line}")
                        except Exception as e:
                            print(f"⚠️ Processing Error: {e}")
                
                time.sleep(0.1)

        except serial.SerialException:
            print(f"⚠️ Lost connection to {SERIAL_PORT}. Retrying in 5 seconds...")
            if ser:
                ser.close()
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Bridge stopped by user.")
            break
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
