#!/usr/bin/env python3
"""
Arduino Sensor Data Reader
Reads DHT22 (temp/humidity) and Soil Moisture sensor data from Arduino via Serial
Automatically updates sample_ground_sensor_data.csv
"""

import serial
import pandas as pd
from datetime import datetime
import time
import json

class ArduinoSensorReader:
    def __init__(self, port='COM3', baudrate=9600):
        """
        Initialize Arduino connection
        
        Args:
            port: COM port (Windows: COM3, COM4, etc. | Linux: /dev/ttyUSB0, /dev/ttyACM0)
            baudrate: Must match Arduino sketch (default: 9600)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.csv_file = 'sample_ground_sensor_data.csv'
        self.field = 'Center Plot'  # Match dashboard sector name
        self.node_id = 'NODE_01'    # Primary field device ID
        
        # MongoDB Configuration
        self.mongo_uri = "mongodb+srv://bhoomivaishya06_db_user:GuysqjmNsQjvgZuj@cluster0.wqfcwpe.mongodb.net/?appName=Cluster0"
        self.db_name = "RiceFarmDB"
        self.collection_name = "live_readings"
        
    def connect_serial(self):
        """Establish serial connection to Arduino"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)  # Wait for Arduino to reset
            print(f"✅ Connected to Arduino on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            print(f"💡 Tip: Check if Arduino is plugged in and port is correct")
            return False
            
    def push_to_mongodb(self, sensor_data):
        """Push sensor readings to MongoDB Atlas Cloud"""
        try:
            import pymongo
            client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            db = client[self.db_name]
            collection = db[self.collection_name]
            
            # Prepare document format expected by dashboard
            document = {
                "node_id": self.node_id,
                "location": self.field,
                "air_temp": sensor_data['temp'],
                "air_dampness": sensor_data['humidity'],
                "soil_wetness": sensor_data['soil_moisture'],
                "timestamp": datetime.now().isoformat(),
                "status": "🟢 Normal",
                "water_depth": "5cm", # Default for field conditions
                "battery": "85%"
            }
            
            # Update existing node document or insert new
            collection.update_one(
                {"node_id": self.node_id},
                {"$set": document},
                upsert=True
            )
            print(f"☁️ Cloud Sync: Data pushed to MongoDB Atlas.")
            return True
        except Exception as e:
            print(f"⚠️ Cloud Sync Failed: {e}")
            return False
    
    def read_sensor_data(self):
        """
        Read one line of sensor data from Arduino
        
        Expected Arduino output format (JSON):
        {"temp": 28.5, "humidity": 65.2, "soil_moisture": 45.8}
        
        Returns:
            dict: Sensor readings or None if error
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("❌ Serial connection not open")
            return None
        
        try:
            # Read line from Arduino
            line = self.serial_conn.readline().decode('utf-8').strip()
            
            if not line:
                return None
            
            # Parse JSON data
            data = json.loads(line)
            
            # Validate required fields
            if 'temp' in data and 'humidity' in data and 'soil_moisture' in data:
                return data
            else:
                print(f"⚠️ Incomplete data from Arduino: {data}")
                return None
                
        except json.JSONDecodeError:
            if line: print(f"⚠️ Non-JSON data from Arduino: {line}")
            return None
        except Exception as e:
            print(f"❌ Error reading serial: {e}")
            return None
    
    def update_csv(self, sensor_data):
        """Append new sensor reading to CSV file (Local Backup)"""
        try:
            # Check if file exists, if not create with headers
            if not os.path.exists(self.csv_file):
                df = pd.DataFrame(columns=['Date', 'Temperature', 'Humidity', 'Soil_Moisture', 'Field'])
            else:
                df = pd.read_csv(self.csv_file)
            
            # Create new row
            new_row = {
                'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Temperature': sensor_data['temp'],
                'Humidity': sensor_data['humidity'],
                'Soil_Moisture': sensor_data['soil_moisture'],
                'Field': self.field
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(self.csv_file, index=False)
            print(f"💾 Local Backup: Data saved to {self.csv_file}")
            
        except Exception as e:
            print(f"❌ Error updating CSV: {e}")
    
    def run_continuous(self, interval_seconds=60):
        """
        Continuously read and log sensor data
        
        Args:
            interval_seconds: Time between readings (default: 60s)
        """
        if not self.connect_serial():
            return
        
        print(f"📊 MONITORING START: {self.node_id} at {self.field}")
        print(f"📡 Interval: {interval_seconds}s | Cloud: MongoDB Atlas | Local: CSV")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                data = self.read_sensor_data()
                
                if data:
                    print("-" * 30)
                    print(f"📍 {datetime.now().strftime('%H:%M:%S')} - New Hardware Reading")
                    self.update_csv(data)
                    self.push_to_mongodb(data)
                    print(f"⏰ Next cycle in {interval_seconds} seconds...")
                    time.sleep(interval_seconds)
                else:
                    # If no data, wait a bit and try again
                    time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        finally:
            if self.serial_conn:
                self.serial_conn.close()
                print("✅ Serial connection closed")
    
    def read_once(self):
        """Read sensor data once and update CSV"""
        if not self.connect():
            return False
        
        try:
            print("📡 Reading sensor data...")
            data = self.read_sensor_data()
            
            if data:
                self.update_csv(data)
                return True
            else:
                print("❌ No valid data received")
                return False
                
        finally:
            if self.serial_conn:
                self.serial_conn.close()

# Usage Examples
if __name__ == "__main__":
    # CONFIGURATION
    ARDUINO_PORT = 'COM3'  # ← CHANGE THIS to your Arduino port
    # Windows: COM3, COM4, etc.
    # Linux/Mac: /dev/ttyUSB0, /dev/ttyACM0, etc.
    
    reader = ArduinoSensorReader(port=ARDUINO_PORT, baudrate=9600)
    
    # Option 1: Read once
    # reader.read_once()
    
    # Option 2: Continuous monitoring (every 5 minutes)
    reader.run_continuous(interval_seconds=300)
