import pandas as pd
import random
import os

# Use absolute path to ensure we hit the right file
file_path = r'c:\CropSatelliteSensorMain\project\sample_ground_sensor_data.csv'

if os.path.exists(file_path):
    print(f"Reading {file_path}...")
    df = pd.read_csv(file_path)
    if 'Field' not in df.columns:
        fields = ['North', 'South', 'East', 'West', 'Northwest', 'Northeast', 'Southwest', 'Southeast', 'Center']
        df['Field'] = [random.choice(fields) for _ in range(len(df))]
        df.to_csv(file_path, index=False)
        print(f"✅ Successfully added 'Field' column to {len(df)} rows.")
    else:
        print("ℹ️ 'Field' column already exists.")
else:
    print(f"❌ File {file_path} not found.")
