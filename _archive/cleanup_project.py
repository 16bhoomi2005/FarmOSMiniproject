import os
import shutil

# Target directory
base_path = r"c:\CropSatelliteSensorMain\project"
pages_path = os.path.join(base_path, "pages")

# Files to KEEP in root
keep_root = {
    "Home.py",
    "data_loader.py",
    "weather_service.py",
    ".env.example",
    "bhandara_polygon.json",
    "active_alerts.json", # Metadata used by app
    "models", # Directory
    "Sentinel_Data", # Directory
    "data" # Directory
}

# Files to KEEP in pages
keep_pages = {
    "1_Field_Health_Map.py",
    "2_Sensor_Monitoring.py",
    "3_Smart_Prediction_Engine.py",
    "4_🚨_Alerts_&_Recommendations.py"
}

print("--- Starting Project Cleanup ---")

# Clean root
for item in os.listdir(base_path):
    item_path = os.path.join(base_path, item)
    if item in keep_root or item == "pages" or item == ".git" or item == "__pycache__":
        continue
    
    try:
        if os.path.isfile(item_path):
            os.remove(item_path)
            print(f"Deleted file: {item}")
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"Deleted dir: {item}")
    except Exception as e:
        print(f"Error deleting {item}: {e}")

# Clean pages
if os.path.exists(pages_path):
    for item in os.listdir(pages_path):
        if item in keep_pages:
            continue
        
        item_path = os.path.join(pages_path, item)
        try:
            os.remove(item_path)
            print(f"Deleted page: {item}")
        except Exception as e:
            print(f"Error deleting page {item}: {e}")

print("--- Cleanup Complete ---")
