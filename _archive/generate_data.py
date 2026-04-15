import pandas as pd
import numpy as np

def create_sample_data():
    """Create enhanced sample ground sensor data"""
    np.random.seed(42)
    dates = pd.date_range('2023-03-01', periods=100, freq='D')
    
    data = {
        'Date': dates,
        'Temperature': np.random.normal(28, 5, 100),
        'Humidity': np.random.normal(65, 15, 100),
        'Soil_Moisture': np.random.normal(55, 10, 100),
        'Crop_Health': np.random.randint(0, 4, 100),
        'Yield': np.random.normal(60, 15, 100),
        # New Season 2 Sensors
        'Soil_pH': np.random.normal(6.5, 0.5, 100),
        'Soil_Temperature': np.random.normal(22, 5, 100),
        'Light_Intensity': np.random.normal(800, 100, 100)
    }
    
    df = pd.DataFrame(data)
    df['Temperature'] = np.clip(df['Temperature'], 15, 40)
    df['Humidity'] = np.clip(df['Humidity'], 30, 90)
    df['Soil_Moisture'] = np.clip(df['Soil_Moisture'], 10, 80)
    df['Yield'] = np.clip(df['Yield'], 20, 100)
    df['Soil_pH'] = np.clip(df['Soil_pH'], 5.0, 8.5)
    df['Soil_Temperature'] = np.clip(df['Soil_Temperature'], 10, 35)
    df['Light_Intensity'] = np.clip(df['Light_Intensity'], 200, 1200)
    
    df.to_csv('sample_ground_sensor_data.csv', index=False)
    print("✅ Enhanced sample ground sensor data saved to 'sample_ground_sensor_data.csv'")

if __name__ == "__main__":
    create_sample_data()
